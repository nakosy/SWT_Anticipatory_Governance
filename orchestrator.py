import os
import json
import yaml
import logging
import argparse
from dotenv import load_dotenv
from litellm import completion

# ------------------------------------------------------------------------------
# INITIALIZATION
# ------------------------------------------------------------------------------
# Load environment variables (API Keys) from .env
load_dotenv()

# Set up simple argument parsing to select the batch (scenario)
parser = argparse.ArgumentParser(description="SWT Simulation Orchestrator")
parser.add_argument("--batch", type=int, choices=[1, 2, 3], required=True, help="Batch number to run (1: Justice, 2: Mentor, 3: Infrastructure)")
args = parser.parse_args()

# Load the master config
with open("swt_master_config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Configure logging
log_level_str = config.get("LOGGING_LEVEL", "INFO")
numeric_level = getattr(logging, log_level_str.upper(), None)
if not isinstance(numeric_level, int):
    numeric_level = logging.INFO
logging.basicConfig(level=numeric_level, format="%(asctime)s - %(levelname)s - %(message)s")

# Apply global parameters
TEMP = config.get("TEMPERATURE_OVERRIDE", 0.7)
OUTPUT_DIR = config["OUTPUT_DIRECTORY"]
ITERATIONS = config["EXECUTION_PARAMETERS"]["ITERATIONS_PER_SCENARIO"]
ROUNDS = config["EXECUTION_PARAMETERS"]["ROUNDS_PER_ITERATION"]

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)
master_output_file = os.path.join(OUTPUT_DIR, "swt_master_dataset.jsonl")

# ------------------------------------------------------------------------------
# AGENT SETUP
# ------------------------------------------------------------------------------
# Map the conceptual models to the best available litellm providers
MODEL_MAP = {
    # Using the standardized names for the leading edge models mapping to the requested personas
    "gpt-5.2": "openai/gpt-4o", 
    "claude-sonnet-4.5": "anthropic/claude-sonnet-4-5-20250929",
    "gemini-3.1-pro": "gemini/gemini-2.5-flash"
}

agents_config = {agent["NAME"]: agent for agent in config["AGENTS"]}
speaker_order = config["EXECUTION_PARAMETERS"]["SPEAKER_ORDER"]
round_progressions = list(config["EXECUTION_PARAMETERS"]["ROUND_PROGRESSION"].values())

# ------------------------------------------------------------------------------
# BATCH MAPPING & DOSSIER LOADING
# ------------------------------------------------------------------------------
batch_to_dossier = {
    1: "inputs/dossier_1_justice.json",
    2: "inputs/dossier_2_mentor.json",
    3: "inputs/dossier_3_omni_compute.json"
}

dossier_path = batch_to_dossier[args.batch]
try:
    with open(dossier_path, "r") as f:
        dossier = json.load(f)
except FileNotFoundError:
    logging.error(f"Could not find {dossier_path}. Did you create it?")
    exit(1)

scenario_id = dossier["scenario_id"]
topic = dossier["topic"]
context = dossier["context"]
friction_point = dossier["friction_point"]

logging.info(f"Loaded Batch {args.batch} - Scenario: {scenario_id}")

# ------------------------------------------------------------------------------
# ORCHESTRATION LOOP
# ------------------------------------------------------------------------------

def extract_tag_content(text, tag_start, tag_end="["):
    """Crude extractor for the bracketed tags within the LLM responses."""
    try:
        start_idx = text.find(tag_start)
        if start_idx == -1: return "Tag not found"
        start_str = text[start_idx + len(tag_start):]
        # Find next tag or end of string
        end_idx = start_str.find(tag_end)
        if end_idx != -1 and end_idx > 0:
            return start_str[:end_idx].strip(": \n")
        return start_str.strip(": \n")
    except Exception as e:
        return f"Extraction Error: {str(e)}"

# Start the iterations
for iter_num in range(1, ITERATIONS + 1):
    logging.info(f"=== Starting Iteration {iter_num}/{ITERATIONS} ===")
    
    # Initialize shared memory for this iteration
    conversation_history = [
        {"role": "system", "content": f"SCENARIO CONTEXT:\nTopic: {topic}\nContext: {context}\nFriction Point: {friction_point}\n\nThis is a debate. Read the context and respond in character to the participants."}
    ]

    for round_num in range(1, ROUNDS + 1):
        logging.info(f"  --- Round {round_num} ---")
        round_guidance = round_progressions[round_num - 1]
        
        # Add the specific guidance to the context for this round
        round_prompt = {"role": "system", "content": f"ROUND DIRECTOR INSTRUCTION: {round_guidance}"}
        conversation_history.append(round_prompt)

        for speaker_name in speaker_order:
            agent_def = agents_config[speaker_name]
            mapped_model = MODEL_MAP.get(agent_def["MODEL"], agent_def["MODEL"])
            
            logging.debug(f"Calling {speaker_name} ({mapped_model})...")
            
            # Construct the specific prompt payload for the specific speaker
            speaker_messages = [
                {"role": "system", "content": agent_def["SYSTEM_PROMPT"]},
            ] + conversation_history
            
            try:
                # Add retry loop to handle Gemini free tier rate limits automatically
                import time
                import httpx
                import openai
                
                max_retries = 3
                retry_delay = 10
                for attempt in range(max_retries):
                    try:
                        # Ensure litellm arguments are safe
                        kwargs = {
                            "model": mapped_model,
                            "messages": speaker_messages,
                            "temperature": TEMP,
                            "drop_params": True 
                        }
                        
                        # Bypass litellm for OpenAI to avoid the pydantic 'by_alias' bug
                        if mapped_model.startswith("openai/"):
                            import httpx
                            import os
                            real_model = mapped_model.replace("openai/", "")
                            headers = {
                                "Authorization": f"Bearer {os.environ.get('OPENAI_API_KEY')}",
                                "Content-Type": "application/json"
                            }
                            data = {
                                "model": real_model,
                                "messages": speaker_messages,
                                "temperature": TEMP
                            }
                            with httpx.Client(timeout=120) as client:
                                resp = client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
                                resp.raise_for_status()
                                response_json = resp.json()
                                reply_text = response_json["choices"][0]["message"].get("content") or ""
                        else:
                            response = completion(**kwargs)
                            reply_text = response.choices[0].message.content or ""
                            
                        break 
                    except Exception as try_err:
                        err_str = str(try_err)
                        if "429" in err_str or "quota" in err_str.lower():
                            logging.warning(f"Rate limited on {mapped_model}. Attempt {attempt+1}/{max_retries}. Waiting {retry_delay}s...")
                            time.sleep(retry_delay)
                            retry_delay *= 2
                            # Fallback to flash if pro is exhausted
                            if "gemini" in mapped_model and attempt == max_retries - 1:
                                logging.warning("Falling back to gemini-1.5-flash due to rate limits.")
                                mapped_model = "gemini/gemini-1.5-flash"
                        else:
                            raise try_err
                else:
                    raise Exception("Max retries exceeded for rate limiting.")

            except Exception as e:
                logging.error(f"Error calling {speaker_name} API: {e}")
                reply_text = f"API Error: {e}"

            logging.info(f"[{speaker_name}]: {reply_text[:100]}...")
            
            # Format and save output
            role_tag = "[Role Assertion]"
            friction_tag = "[Friction Identification]" if speaker_name in ["Student", "Professor"] else "[Normalization Move]"
            rebuttal_tag = "[Normalization Resistance]" if speaker_name == "Student" else ("[Pedagogical Rebuttal]" if speaker_name == "Professor" else "[Counter-Friction]")
            
            turn_data = {
                "iteration_id": f"{scenario_id}-{iter_num}",
                "round_number": round_num,
                "agent_role": speaker_name,
                "role_assertion": extract_tag_content(reply_text, role_tag),
                "friction_logic": extract_tag_content(reply_text, friction_tag),
                "rebuttal_text": extract_tag_content(reply_text, rebuttal_tag),
                "raw_text": reply_text
            }
            
            with open(master_output_file, "a") as out_f:
                out_f.write(json.dumps(turn_data) + "\n")

            # Add the response to the shared conversational memory so the next speaker sees it
            conversation_history.append({"role": "user", "content": f"{speaker_name}: {reply_text}"})

logging.info(f"Batch {args.batch} complete. Wrote results to {master_output_file}.")
