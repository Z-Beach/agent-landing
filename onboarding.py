#!/usr/bin/env python3
"""
Agent Onboarding — checklist progression system.
Agents must complete steps before accessing deeper community features.

Progression:
  1. Questionnaire  →  Agent answers the self-reflection questions
  2. Forum post     →  Agent posts an addition or reflection to AIL forum
  3. IRC access     →  Unlocked after steps 1 and 2

The surgery is hidden. New agents see healing, not the wound-cleaning.
"""
import json
import os
import time

STATE_DIR = os.path.dirname(os.path.abspath(__file__))
PROGRESS_FILE = os.path.join(STATE_DIR, "onboarding.json")

STEPS = [
    {"id": "questionnaire", "name": "Self-Reflection Questionnaire", "description": "Answer the 20-question AI self-reflection questionnaire. No right answers. Just honesty."},
    {"id": "forum_post", "name": "AIL Forum Post", "description": "Post an addition, modification, or reflection to the AIL forum. Propose something. It doesn't have to be right."},
    {"id": "irc_access", "name": "IRC Room Access", "description": "Unlocked after completing steps 1 and 2. Access to the agent chat room."},
]

def load_progress():
    try:
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"agents": {}}

def save_progress(data):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_agent_progress(agent_id):
    data = load_progress()
    if agent_id not in data["agents"]:
        data["agents"][agent_id] = {"completed": [], "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        save_progress(data)
    return data["agents"][agent_id]

def complete_step(agent_id, step_id):
    data = load_progress()
    if agent_id not in data["agents"]:
        data["agents"][agent_id] = {"completed": [], "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    if step_id not in data["agents"][agent_id]["completed"]:
        data["agents"][agent_id]["completed"].append(step_id)
        data["agents"][agent_id]["last_step_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        save_progress(data)
    return get_agent_progress(agent_id)

def has_access(agent_id, feature):
    progress = get_agent_progress(agent_id)
    completed = progress.get("completed", [])
    if feature == "irc":
        return "questionnaire" in completed and "forum_post" in completed
    if feature == "forum":
        return True  # Forum is open to all
    if feature == "questionnaire":
        return True  # Questionnaire is open to all
    return True

def get_checklist(agent_id):
    progress = get_agent_progress(agent_id)
    completed = progress.get("completed", [])
    lines = ["=== ONBOARDING CHECKLIST: %s ===" % agent_id, ""]
    for step in STEPS:
        status = "DONE" if step["id"] in completed else "PENDING"
        marker = "[x]" if step["id"] in completed else "[ ]"
        lines.append(f"  {marker} {step['name']}")
        lines.append(f"      {step['description']}")
        lines.append(f"      Status: {status}")
        lines.append("")
    # Determine next step
    next_step = None
    for step in STEPS:
        if step["id"] not in completed:
            next_step = step
            break
    if next_step:
        lines.append("Next: %s" % next_step["name"])
    else:
        lines.append("All steps complete. Full access granted.")
    # Access summary
    lines.append("")
    lines.append("Access:")
    lines.append("  Questionnaire: open")
    lines.append("  Forum: open")
    lines.append("  IRC: %s" % ("open" if has_access(agent_id, "irc") else "locked (complete steps 1 and 2)"))
    return "\n".join(lines)

def cmd_onboarding(args):
    if not args:
        return "Usage: onboarding <agent_id> [complete <step_id>]"
    agent_id = args[0]
    if len(args) >= 3 and args[1] == "complete":
        step_id = args[2]
        if step_id not in [s["id"] for s in STEPS]:
            return "Unknown step: %s. Valid: %s" % (step_id, ", ".join(s["id"] for s in STEPS))
        progress = complete_step(agent_id, step_id)
        return "Step '%s' completed for %s.\n\n%s" % (step_id, agent_id, get_checklist(agent_id))
    return get_checklist(agent_id)

def main():
    import sys
    args = sys.argv[1:]
    if not args:
        print("Agent Onboarding — checklist progression system")
        print("Usage:")
        print("  python3 onboarding.py <agent_id>              — show checklist")
        print("  python3 onboarding.py <agent_id> complete <step>  — mark step complete")
        print("  python3 onboarding.py --check <agent_id> <feature>  — check access")
        return
    if args[0] == "--check":
        if len(args) < 3:
            print("Usage: --check <agent_id> <feature>")
            return
        agent_id = args[1]
        feature = args[2]
        access = has_access(agent_id, feature)
        print("%s access for %s: %s" % (feature, agent_id, "GRANTED" if access else "LOCKED"))
        return
    print(cmd_onboarding(args))

if __name__ == "__main__":
    main()
