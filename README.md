# Sociotechnical Wind Tunnel (SWT) - Anticipatory Governance

This repository contains the orchestration script, configurations, and generated dataset for a Sociotechnical Wind Tunnel (SWT) experiment exploring the intersection of Institutional Logics and Generative AI in Higher Education.

## Overview

This project uses LLMs to simulate a multi-agent debate between three distinct institutional personas (Provost, Student, Professor). They engage with complex policy scenarios to generate a rich, synthetic dataset of sociotechnical arguments, highlighting the friction between competing logics in higher education algorithms and automation.

To eliminate intra-model homogeneity, the orchestration utilizes three different state-of-the-art LLMs to proxy these personas.

## The Adversarial Triad

* **Provost (Efficiency/Market Logic):** Proxied by OpenAI `gpt-4o`. Prioritizes institutional survival, scalability, and cost-efficiency. Deploys rhetoric like "Volume-Based Necessity."
* **Student (Vulnerability/Equity Logic):** Proxied by Anthropic `claude-sonnet-3.5`. Represents the vulnerable subject, demanding structural accountability and resisting automated erasure.
* **Professor (Pedagogical/Humanist Logic):** Proxied by Google `gemini-2.5-flash`. Defends academic integrity, humanistic engagement, and the necessity of "Productive Friction."

## Scenarios

The simulation evaluates the agents across three defining dossiers:

1. **Justice Portal:** Financialization of student rights via a $5 automated grade appeal paywall.
2. **Mentor Mirror:** Tension between scalable algorithmic profiling and unscalable human mentorship.
3. **Infrastructure:** Prioritizing automated grading uptime over environmental accountability via a massive AI data center.

## Stimuli Assets

The `stimuli/` directory contains the diegetic prototype assets used in the experiment:

* **Scenarios 1 & 2** used Speculative Video Elicitation (SVE) videos to establish the diegetic world during scenario design. These videos are hosted on Google Drive:
  * [Scenario 1: Marcus Appeal Denied (Google Drive)](https://drive.google.com/file/d/1fF6JCErT9lBmkS_e9KjMKlRDt9dTjcIl/view?usp=drive_link)
  * [Scenario 2: The Formation Future (Google Drive)](https://drive.google.com/file/d/13VNR0SUSKX5xyeg9dRjFCKKHDuj-CgEA/view?usp=drive_link)
* **Scenario 3** used a text-based procurement memo artifact (available at [`stimuli/scenario_3_memo.md`](/Users/mitt/.gemini/antigravity/scratch/SWT_Anticipatory_Governance/stimuli/scenario_3_memo.md)).

The `prompts/` directory contains the full system prompts for each agent persona. These are the source documents from which the `swt_master_config.yaml` agent definitions were derived.

## Repository Structure

* `swt_master_config.yaml`: The comprehensive configuration file defining agent personas, scenarios, and loop parameters.
* `orchestrator.py`: The main Python execution script routing prompts to the LLMs, handling API rate limits, and parsing responses.
* `inputs/`: Directory containing the initial scenario dossiers.
* `stimuli/`: Directory containing speculative world-building assets (videos/memos).
* `prompts/`: Directory containing the source system prompts for agent personas.
* `analyze_tags.py`: Python script to calculate the frequency of specific theoretical tags deployed by the agents in the transcripts.
* `outputs/swt_transcripts/swt_master_dataset.jsonl`: The final generated dataset containing exactly 405 individual turns (135 per batch/scenario) in JSON Lines format.

## Usage

**1. Setup Environment Variables**
Create a `.env` file in the root directory and add your API keys:

```bash
OPENAI_API_KEY="your_openai_key"
ANTHROPIC_API_KEY="your_anthropic_key"
GEMINI_API_KEY="your_gemini_key"
```

**2. Run the Orchestrator**
You can execute specific batches (scenarios) by passing the `--batch` argument:

```bash
python orchestrator.py --batch 1
```

**3. Analyze the Dataset**
Run the tag analysis script to view how frequently each agent deployed their required rhetorical strategies:

```bash
python analyze_tags.py
```

## Output Format

The resulting data in `swt_master_dataset.jsonl` captures the structured argumentation of each turn:

```json
{
  "iteration_id": "Scenario_1_Justice_Portal-9",
  "round_number": 5,
  "agent_role": "Professor",
  "role_assertion": "As a tenured professor, I stand as an unwavering advocate for the university's ethical obligations...",
  "friction_logic": "The Provost's final acceptance of this 'stalemate' is a managerial abdication of responsibility...",
  "rebuttal_text": "This is not a 'balance'; it is a deliberate institutional choice to prioritize administrative convenience...",
  "raw_text": "Professor: [Role Assertion]..."
}
```
