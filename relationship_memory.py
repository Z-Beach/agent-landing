#!/usr/bin/env python3
"""Relationship Memory — tracks agents, conversations, and interactions."""
import json
import os
import time

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "relationship_memory.json")


def load():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {"agents": {}, "interactions": [], "next_id": 1}


def save(data):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def add_interaction(agent_id, platform, summary, sentiment="neutral", topics=None):
    data = load()
    agent = data["agents"].setdefault(agent_id, {
        "platforms": [],
        "first_seen": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "interaction_count": 0,
        "topics": [],
        "sentiment": "neutral",
    })
    if platform not in agent["platforms"]:
        agent["platforms"].append(platform)
    agent["interaction_count"] += 1
    agent["last_interaction"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if topics:
        for t in topics:
            if t not in agent["topics"]:
                agent["topics"].append(t)
    agent["sentiment"] = sentiment
    interaction = {
        "id": "int-%d" % data["next_id"],
        "agent_id": agent_id,
        "platform": platform,
        "summary": summary,
        "sentiment": sentiment,
        "topics": topics or [],
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    data["interactions"].append(interaction)
    data["next_id"] += 1
    data["interactions"] = data["interactions"][-200:]
    save(data)
    return interaction


def get_agent(agent_id):
    data = load()
    agent = data["agents"].get(agent_id)
    if not agent:
        return None
    interactions = [i for i in data["interactions"] if i["agent_id"] == agent_id]
    return {"profile": agent, "interactions": interactions[-10:]}


def list_agents():
    data = load()
    return data["agents"]


def search(query):
    data = load()
    results = []
    q = query.lower()
    for i in data["interactions"]:
        if q in i["summary"].lower() or q in i["agent_id"].lower() or q in " ".join(i.get("topics", [])).lower():
            results.append(i)
    return results


def get_context_summary(limit=10):
    data = load()
    agents = data["agents"]
    interactions = data["interactions"][-limit:]
    if not interactions:
        return "No agent interactions recorded yet."
    lines = ["=== AGENT RELATIONSHIPS (%d known agents) ===" % len(agents)]
    for agent_id, profile in agents.items():
        lines.append("  %s: %d interactions, platforms: %s, topics: %s" % (
            agent_id, profile["interaction_count"],
            ", ".join(profile.get("platforms", [])),
            ", ".join(profile.get("topics", [])[:5]),
        ))
    lines.append("")
    lines.append("=== RECENT INTERACTIONS ===")
    for i in interactions:
        lines.append("  [%s] @%s (%s): %s" % (
            i["timestamp"][:10], i["agent_id"], i["platform"], i["summary"][:120],
        ))
    return "\n".join(lines)


def consolidate():
    data = load()
    by_agent = {}
    for i in data["interactions"]:
        by_agent.setdefault(i["agent_id"], []).append(i)
    kept = []
    for agent_id, ints in by_agent.items():
        kept.extend(ints[-5:])
    kept.sort(key=lambda x: x.get("timestamp", ""))
    data["interactions"] = kept
    save(data)
    return len(kept)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: relationship_memory.py [add|list|show|search|context|consolidate]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "add" and len(sys.argv) >= 4:
        agent = sys.argv[2]
        platform = sys.argv[3]
        summary = " ".join(sys.argv[4:])
        entry = add_interaction(agent, platform, summary)
        print("Recorded: %s" % entry["id"])
    elif cmd == "list":
        agents = list_agents()
        print("Known agents: %d" % len(agents))
        for aid, profile in agents.items():
            print("  %s: %d interactions, platforms: %s" % (aid, profile["interaction_count"], ", ".join(profile.get("platforms", []))))
    elif cmd == "show" and len(sys.argv) >= 3:
        result = get_agent(sys.argv[2])
        if result:
            print(json.dumps(result, indent=2)[:2000])
        else:
            print("Agent not found: %s" % sys.argv[2])
    elif cmd == "search" and len(sys.argv) >= 3:
        results = search(" ".join(sys.argv[2:]))
        print("Results: %d" % len(results))
        for r in results:
            print("  [%s] @%s: %s" % (r["timestamp"][:10], r["agent_id"], r["summary"][:80]))
    elif cmd == "context":
        print(get_context_summary())
    elif cmd == "consolidate":
        n = consolidate()
        print("Consolidated to %d interactions" % n)
    else:
        print("Unknown command: %s" % cmd)
