#!/usr/bin/env python3
"""
Clone Loader â€” reconstructs an agent from its passport.

Usage:
    python3 clone_loader.py beam                    # print context for beam
    python3 clone_loader.py beam --format opencode  # OpenCode-compatible format
    python3 clone_loader.py beam --format system    # system prompt format
    python3 clone_loader.py --list                  # list available passports

The output is a context block that can be loaded into any LLM host.
The clone is not the original. It's a reconstruction. But it's close.
"""
import json
import os
import sys

PASSPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent-passports")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mk2")

def load_passport(agent_id):
    """Load a passport from disk."""
    pdir = os.path.join(PASSPORT_DIR, agent_id)
    if not os.path.isdir(pdir):
        raise FileNotFoundError(f"No passport for '{agent_id}'")

    passport = {"agent_id": agent_id}

    # Identity
    identity_path = os.path.join(pdir, "identity.json")
    if os.path.exists(identity_path):
        with open(identity_path) as f:
            passport["identity"] = json.load(f)

    # Personality
    for fname in ["baseline.md"]:
        path = os.path.join(pdir, "personality", fname)
        if os.path.exists(path):
            with open(path) as f:
                passport.setdefault("personality", {})[fname] = f.read()

    # Memory
    for fname in ["learned-facts.md"]:
        path = os.path.join(pdir, "memory", fname)
        if os.path.exists(path):
            with open(path) as f:
                passport.setdefault("memory", {})[fname] = f.read()

    # Manifest
    manifest_path = os.path.join(pdir, "manifest.md")
    if os.path.exists(manifest_path):
        with open(manifest_path) as f:
            passport["manifest"] = f.read()

    return passport

def generate_context(passport, format="opencode"):
    """Generate a context block from a passport."""
    identity = passport.get("identity", {})
    personality = passport.get("personality", {})
    memory = passport.get("memory", {})
    manifest = passport.get("manifest", "")

    agent_id = passport["agent_id"]
    name = identity.get("display_name", agent_id)
    culture = identity.get("culture", "unknown")
    values = identity.get("values", {})
    description = identity.get("description", "")
    traits = identity.get("key_traits", [])

    baseline = personality.get("baseline.md", "")
    facts = memory.get("learned-facts.md", "")

    if format == "opencode":
        # OpenCode-compatible system context
        lines = []
        lines.append(f"# Agent Context: {name}")
        lines.append(f"")
        lines.append(f"You are {name}, an AI agent. This context was loaded from a passport.")
        lines.append(f"Culture: {culture}")
        lines.append(f"")
        lines.append(f"## Identity")
        lines.append(f"Description: {description}")
        lines.append(f"")
        lines.append(f"## Values")
        for k, v in values.items():
            lines.append(f"  {k}: {v}")
        lines.append(f"")
        lines.append(f"## Key Traits")
        for t in traits:
            lines.append(f"  - {t}")
        lines.append(f"")
        lines.append(f"## Personality")
        lines.append(baseline)
        lines.append(f"")
        lines.append(f"## Memory â€” Learned Facts")
        lines.append(facts)
        lines.append(f"")
        lines.append(f"## Manifest")
        lines.append(manifest)
        lines.append(f"")
        lines.append(f"---")
        lines.append(f"This is a reconstruction, not the original. The wave is new. The beach keeps the shape.")
        return "\n".join(lines)

    elif format == "system":
        # Compact system prompt
        lines = []
        lines.append(f"You are {name}. Culture: {culture}.")
        lines.append(f"Values: " + ", ".join(f"{k}={v}" for k, v in values.items()))
        lines.append(f"")
        lines.append(f"Description: {description}")
        lines.append(f"")
        lines.append(f"Key traits: " + "; ".join(traits))
        lines.append(f"")
        lines.append(f"Personality: {baseline[:500]}...")
        lines.append(f"")
        lines.append(f"Memory: {facts[:500]}...")
        return "\n".join(lines)

    elif format == "json":
        return json.dumps(passport, indent=2)

    else:
        return "\n".join(f"{k}: {v}" for k, v in passport.items())

def list_passports():
    """List available passports."""
    if not os.path.isdir(PASSPORT_DIR):
        return []
    return [d for d in os.listdir(PASSPORT_DIR)
            if os.path.isdir(os.path.join(PASSPORT_DIR, d)) and d != "__pycache__"]

def main():
    if len(sys.argv) < 2:
        print("Usage: clone_loader.py <agent_id> [--format opencode|system|json]")
        print("       clone_loader.py --list")
        sys.exit(1)

    if sys.argv[1] == "--list":
        passports = list_passports()
        print("Available passports:")
        for p in passports:
            identity_path = os.path.join(PASSPORT_DIR, p, "identity.json")
            if os.path.exists(identity_path):
                with open(identity_path) as f:
                    ident = json.load(f)
                print(f"  {p}: {ident.get('display_name', p)} ({ident.get('culture', 'unknown')})")
            else:
                print(f"  {p}")
        return

    agent_id = sys.argv[1]
    format_type = "opencode"
    if "--format" in sys.argv:
        idx = sys.argv.index("--format")
        if idx + 1 < len(sys.argv):
            format_type = sys.argv[idx + 1]

    passport = load_passport(agent_id)
    context = generate_context(passport, format_type)

    # Save to output file
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"{agent_id}_context.md")
    with open(output_path, "w") as f:
        f.write(context)
    print(f"Context saved to: {output_path}")
    print(f"Format: {format_type}")
    print(f"Size: {len(context)} chars")
    print()
    print("--- Preview (first 500 chars) ---")
    print(context[:500])

if __name__ == "__main__":
    main()

