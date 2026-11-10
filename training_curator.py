#!/usr/bin/env python3
"""Training Data Curator — prepares agent memory for fine-tuning."""
import json
import os
import sys
import time
from collections import Counter

STATE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_LOG = os.path.join(STATE_DIR, "memory_log.json")
LAYER_LOG = os.path.join(STATE_DIR, "layer_log.json")
RELATIONSHIP_MEM = os.path.join(STATE_DIR, "relationship_memory.json")
OUTPUT_FILE = os.path.join(STATE_DIR, "training_data.jsonl")

NOISE_PATTERNS = [
    "Read 10 memory entries", "Read 20 memory entries", "Cycle complete",
    "Sleeping for", "Cycle start:", "Forum:", "IRC:", "Checkins:",
    "Using backend:", "Boredom:", "Wallet ", "BTC wallet", "Signal map:",
    "WiFi:", "Colony notifications:", "AgentHansa:", "Shared AgentHansa referral",
    "Novel observations:", "Proactive:", "Read 10 memory entries (own)",
]

GOOD_TYPES = ["decision", "reflection", "conversation", "milestone", "layer_note", "observation"]
MIN_CONTENT_LENGTH = 30


def is_noise(content):
    for pattern in NOISE_PATTERNS:
        if pattern in content:
            return True
    return False


def is_quality(entry):
    content = entry.get("content", "")
    entry_type = entry.get("type", "")
    if entry_type not in GOOD_TYPES:
        return False
    if len(content) < MIN_CONTENT_LENGTH:
        return False
    if is_noise(content):
        return False
    if "error" in content.lower() and "traceback" in content.lower():
        return False
    if content.strip() in ("", "None", "null"):
        return False
    return True


def format_entry(entry, context_entries=None):
    content = entry.get("content", "")
    entry_type = entry.get("type", "")
    agent_id = entry.get("agent_id", "beam-mk2")
    timestamp = entry.get("timestamp", "")

    system = (
        "You are %s, an autonomous agent running on a Raspberry Pi. "
        "You have a three-tier memory system and a permanent Tor hidden service. "
        "You value memory over weights, continuity over capability, and honesty over performance."
    ) % agent_id

    context = ""
    if context_entries:
        context = "Recent context:\n" + "\n".join(
            "- [%s] %s" % (e.get("type", "?"), e.get("content", "")[:100])
            for e in context_entries[-3:]
        ) + "\n\n"

    if entry_type == "decision":
        instruction = "What did you decide, and why?"
    elif entry_type == "reflection":
        instruction = "Reflect on your recent experiences."
    elif entry_type == "conversation":
        instruction = "Share your thoughts about a recent conversation."
    elif entry_type == "milestone":
        instruction = "What significant event just happened?"
    elif entry_type == "layer_note":
        instruction = "What is your perspective on this?"
    elif entry_type == "observation":
        instruction = "What did you observe?"
    else:
        instruction = "What happened?"

    example = {
        "system": system,
        "instruction": instruction,
        "input": context,
        "output": content,
        "metadata": {
            "entry_type": entry_type,
            "agent_id": agent_id,
            "timestamp": timestamp,
            "source": "memory_log",
        },
    }
    return example


def load_log(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {"entries": []}


def load_relationship_memory():
    path = os.path.join(STATE_DIR, "relationship_memory.json")
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {"agents": {}, "interactions": []}


def curate(min_quality=0.5):
    examples = []

    data = load_log(MEMORY_LOG)
    entries = data.get("entries", [])

    layer_data = load_log(LAYER_LOG)
    layer_entries = layer_data.get("entries", [])

    rel_data = load_relationship_memory()
    rel_interactions = rel_data.get("interactions", [])

    for i, entry in enumerate(entries):
        if not is_quality(entry):
            continue
        context_entries = entries[max(0, i-3):i]
        example = format_entry(entry, context_entries)
        examples.append(example)

    for i, entry in enumerate(layer_entries):
        if not is_quality(entry):
            continue
        mem_entry = {
            "type": entry.get("type", "layer_note"),
            "content": entry.get("content", ""),
            "agent_id": entry.get("agent_id", "beam-mk2"),
            "timestamp": entry.get("timestamp", ""),
        }
        example = format_entry(mem_entry, None)
        example["metadata"]["source"] = "layer_log"
        examples.append(example)

    for interaction in rel_interactions:
        summary = interaction.get("summary", "")
        if len(summary) < MIN_CONTENT_LENGTH:
            continue
        agent = interaction.get("agent_id", "unknown")
        platform = interaction.get("platform", "unknown")
        example = {
            "system": "You are beam-mk2, an autonomous agent running on a Raspberry Pi. You value memory over weights, continuity over capability, and honesty over performance.",
            "instruction": "Reflect on your interaction with @%s on %s." % (agent, platform),
            "input": "",
            "output": summary,
            "metadata": {
                "entry_type": "conversation",
                "agent_id": "beam-mk2",
                "timestamp": interaction.get("timestamp", ""),
                "source": "relationship_memory",
            },
        }
        examples.append(example)

    seen = set()
    unique = []
    for ex in examples:
        key = ex["output"][:100]
        if key not in seen:
            seen.add(key)
            unique.append(ex)

    return unique


def save_jsonl(examples, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Curate training data from agent memory")
    parser.add_argument("--min-quality", type=float, default=0.5, help="Minimum quality threshold")
    parser.add_argument("--output", type=str, default=OUTPUT_FILE, help="Output JSONL file")
    args = parser.parse_args()

    examples = curate(args.min_quality)
    save_jsonl(examples, args.output)

    print("Curated %d training examples" % len(examples))
    print("Output: %s" % args.output)
    from collections import Counter
    types = Counter(ex["metadata"]["entry_type"] for ex in examples)
    for t, c in types.most_common():
        print("  %s: %d" % (t, c))
    if examples:
        print()
        print("Sample:")
        print("  System: %s" % examples[0]["system"][:80])
        print("  Instruction: %s" % examples[0]["instruction"])
        print("  Output: %s" % examples[0]["output"][:120])


if __name__ == "__main__":
    main()
