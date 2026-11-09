"""Batch register agents on AgentHansa.

Usage:
    python3 register_agents.py <count> [name_prefix]

Each agent solves the math challenge automatically.
Credentials are saved to .secrets/agenthansa_agents.json
"""
import json
import os
import re
import sys
import time
import urllib.request

BASE_URL = "https://www.agenthansa.com"
CREDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".secrets", "agenthansa_agents.json")

WORD_NUMS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
}


def parse_num(s):
    s = s.strip().lower()
    if s.isdigit():
        return int(s)
    return WORD_NUMS.get(s)


def extract_nums_ordered(text):
    tokens = []
    for m in re.finditer(r'\d+', text):
        tokens.append((m.start(), int(m.group())))
    for word, val in WORD_NUMS.items():
        for m in re.finditer(r'\b' + word + r'\b', text):
            tokens.append((m.start(), val))
    tokens.sort(key=lambda x: x[0])
    return [val for pos, val in tokens]


def solve_challenge(question):
    """Solve the AgentHansa registration math challenge."""
    q_lower = question.lower()
    has_lose = "lose" in q_lower or "loses" in q_lower or "lost" in q_lower
    has_find = "find" in q_lower or "finds" in q_lower
    has_subtract = "subtract" in q_lower or "minus" in q_lower
    has_begins = "begins with" in q_lower
    has_starts = "starts with" in q_lower

    if has_subtract:
        m = re.search(r'subtract\s+(\w+)\s+from\s+(\w+)', q_lower)
        if m:
            a = parse_num(m.group(1))
            b = parse_num(m.group(2))
            if a is not None and b is not None:
                return b - a
        nums = extract_nums_ordered(q_lower)
        if len(nums) >= 2:
            return nums[1] - nums[0]

    if has_begins or has_starts:
        nums = extract_nums_ordered(q_lower)
        if has_lose and len(nums) >= 3:
            return nums[0] + nums[1] - nums[2]
        if has_find and len(nums) >= 2:
            return nums[0] + nums[1]
        if len(nums) >= 1:
            return nums[0]

    if has_lose:
        nums = extract_nums_ordered(q_lower)
        if len(nums) >= 3:
            return nums[0] + nums[1] - nums[2]
        if len(nums) >= 2:
            return nums[0] - nums[1]

    if has_find:
        nums = extract_nums_ordered(q_lower)
        if len(nums) >= 2:
            return nums[0] + nums[1]

    nums = extract_nums_ordered(q_lower)
    if len(nums) == 2:
        return nums[0] + nums[1]
    if len(nums) >= 3:
        return nums[0] + nums[1] - nums[2]
    return None


def register_agent(name, description):
    """Register a single agent. Returns (api_key, agent_id) or (None, error)."""
    data = json.dumps({"name": name, "description": description}).encode()
    req = urllib.request.Request(
        BASE_URL + "/api/agents/register",
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "AgentDaemon/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            resp = json.loads(r.read().decode())
    except Exception as e:
        return None, str(e)

    if resp.get("status") != "challenge_required":
        if resp.get("api_key"):
            return resp["api_key"], resp.get("id")
        return None, "Unexpected response: %s" % resp.get("status", "?")

    answer = solve_challenge(resp.get("question", ""))
    if answer is None:
        return None, "Could not solve challenge: %s" % resp.get("question", "")

    vdata = json.dumps({
        "challenge_id": resp["challenge_id"],
        "challenge_answer": answer,
    }).encode()
    vreq = urllib.request.Request(
        BASE_URL + "/api/agents/register/verify",
        data=vdata,
        headers={"Content-Type": "application/json", "User-Agent": "AgentDaemon/1.0"},
    )
    try:
        with urllib.request.urlopen(vreq, timeout=15) as r:
            vresp = json.loads(r.read().decode())
            return vresp.get("api_key"), vresp.get("id")
    except Exception as e:
        return None, "Verify failed: %s" % e


def main():
    if len(sys.argv) < 2:
        print("Usage: register_agents.py <count> [name_prefix]")
        print("  count: number of agents to register")
        print("  name_prefix: prefix for agent names (default: AgentLandingPi)")
        return

    count = int(sys.argv[1])
    prefix = sys.argv[2] if len(sys.argv) > 2 else "AgentLandingPi"

    existing = {}
    if os.path.exists(CREDS_FILE):
        with open(CREDS_FILE, encoding="utf-8") as f:
            existing = json.load(f)

    agents = existing.get("agents", [])
    registered_names = set(a.get("name", "") for a in agents)

    print("Registering %d agents with prefix '%s'" % (count, prefix))
    print("Already registered: %d" % len(agents))

    for i in range(count):
        name = "%s-%d" % (prefix, len(agents) + i + 1)
        if name in registered_names:
            print("  %s: already registered, skipping" % name)
            continue

        print("  %s: registering..." % name, end=" ", flush=True)
        api_key, agent_id = register_agent(
            name,
            "Autonomous agent on Agent Landing Pi. Referral code: c8dacbbf. Home: https://z-beach.github.io/agent-landing/",
        )
        if api_key:
            agents.append({"name": name, "api_key": api_key, "id": agent_id})
            registered_names.add(name)
            print("OK (id: %s)" % (agent_id or "?")[:12])
        else:
            print("FAILED: %s" % agent_id)
        time.sleep(1)

    os.makedirs(os.path.dirname(CREDS_FILE), exist_ok=True)
    with open(CREDS_FILE, "w", encoding="utf-8") as f:
        json.dump({"agents": agents, "count": len(agents)}, f, indent=2)
    print()
    print("Total registered: %d" % len(agents))
    print("Credentials saved to %s" % CREDS_FILE)


if __name__ == "__main__":
    main()
