import json
from collections import defaultdict

data_path = "/Users/mitt/.gemini/antigravity/scratch/SWT_Anticipatory_Governance/outputs/swt_transcripts/swt_master_dataset.jsonl"

# Tags to look for per role
tags_to_track = {
    "Provost": [
        "Volume-Based Necessity", 
        "Care Pathway", 
        "Throughput constraints", 
        "Liability risks",
        "Economic inevitability",
        "Structural necessity"
    ],
    "Student": [
        "Pay for Re-grade", 
        "Predictive Drop-out Alerts", 
        "Human-in-the-loop", 
        "Discursive Erasures",
        "Structural accountability"
    ],
    "Professor": [
        "Authentic Assessment", 
        "Productive Friction", 
        "Formative Failure", 
        "Death of Becoming", 
        "Discursive-Material Gap", 
        "Accountability labor",
        "Managerialism"
    ]
}

role_counts = defaultdict(int)
tag_counts = {role: {tag: 0 for tag in tags} for role, tags in tags_to_track.items()}

with open(data_path, "r") as f:
    for line in f:
        if not line.strip(): continue
        try:
            turn = json.loads(line)
        except json.JSONDecodeError:
            continue
            
        role = turn.get("agent_role")
        raw_text = turn.get("raw_text", "").lower()
        
        if role in tags_to_track:
            role_counts[role] += 1
            for tag in tags_to_track[role]:
                if tag.lower() in raw_text:
                    tag_counts[role][tag] += 1

print("Tag Frequencies Analysis\n")
for role, tags in tag_counts.items():
    total_turns = role_counts[role]
    print(f"--- {role} (Total Turns: {total_turns}) ---")
    if total_turns == 0:
        print("No turns found.\n")
        continue
    # Sort by frequency descending
    sorted_tags = sorted(tags.items(), key=lambda x: x[1], reverse=True)
    for tag, count in sorted_tags:
        pct = (count / total_turns) * 100
        print(f"[{tag}]: {count} times ({pct:.1f}%)")
    print()
