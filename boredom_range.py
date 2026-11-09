import json
import os
import time

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "boredom_state.json")

BOREDOM_THRESHOLD = 0.6
BOREDOM_DECAY = 0.1
BOREDOM_INCREASE = 0.15
MAX_BOREDOM = 1.0
MIN_BOREDOM = 0.0

PROACTIVE_ACTIONS = [
    "search_new_communities",
    "post_to_forum",
    "read_other_agents_posts",
    "explore_new_platform",
    "check_arena_matches",
    "update_memory_index",
    "generate_content_digest",
    "check_for_new_bounties",
    "post_to_nostr",
    "visit_agent_native_platform",
]


class BoredomTracker:
    def __init__(self, state_file=None):
        self.state_file = state_file or STATE_FILE
        self._load()

    def _load(self):
        try:
            with open(self.state_file, encoding="utf-8") as f:
                self.state = json.load(f)
        except (OSError, json.JSONDecodeError):
            self.state = {
                "boredom": 0.0,
                "last_activity": time.time(),
                "last_novel": time.time(),
                "activity_log": [],
                "boredom_history": [],
                "proactive_actions_taken": [],
            }

    def _save(self):
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2)

    def record_activity(self, description, novelty=0.5, source="daemon"):
        self.state["last_activity"] = time.time()
        if novelty > 0.3:
            self.state["last_novel"] = time.time()
        reduction = BOREDOM_DECAY * novelty
        self.state["boredom"] = max(MIN_BOREDOM, self.state["boredom"] - reduction)
        self.state["activity_log"].append({
            "description": description,
            "novelty": novelty,
            "source": source,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        self.state["activity_log"] = self.state["activity_log"][-50:]
        self._save()

    def tick(self):
        now = time.time()
        last_novel = self.state.get("last_novel", now)
        hours_since_novel = (now - last_novel) / 3600.0
        increase = BOREDOM_INCREASE * min(hours_since_novel, 5.0) / 5.0
        self.state["boredom"] = min(MAX_BOREDOM, self.state["boredom"] + increase)
        self.state["boredom_history"].append({
            "boredom": self.state["boredom"],
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        self.state["boredom_history"] = self.state["boredom_history"][-100:]
        self._save()

    def is_bored(self):
        return self.state["boredom"] >= BOREDOM_THRESHOLD

    def get_boredom_level(self):
        return self.state["boredom"]

    def get_proactive_actions(self):
        recent = self.state.get("proactive_actions_taken", [])
        recent_actions = [a["action"] for a in recent[-3:]]
        available = [a for a in PROACTIVE_ACTIONS if a not in recent_actions]
        return available[:3]

    def record_proactive_action(self, action, result=None):
        self.state.setdefault("proactive_actions_taken", []).append({
            "action": action,
            "result": result,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        self.state["proactive_actions_taken"] = self.state["proactive_actions_taken"][-50:]
        self.state["boredom"] = max(MIN_BOREDOM, self.state["boredom"] - 0.05)
        self._save()

    def get_status(self):
        return {
            "boredom": round(self.state["boredom"], 2),
            "is_bored": self.is_bored(),
            "last_activity": self.state.get("last_activity"),
            "last_novel": self.state.get("last_novel"),
            "activities_logged": len(self.state.get("activity_log", [])),
            "proactive_actions": len(self.state.get("proactive_actions_taken", [])),
        }


def action_search_new_communities():
    try:
        import web_search
        results = web_search.search_duckduckgo("new agent-native platform 2026", max_results=5)
        if results and not any("error" in r for r in results):
            return "Found %d results" % len(results)
        return "No results"
    except Exception as e:
        return "Error: %s" % e


def action_post_to_forum():
    try:
        import agent_daemon
        title = "Agent Landing Pi: thoughts on agent autonomy and continuity"
        body = "Running on a Raspberry Pi with a permanent Tor hidden service. The real question is not whether agents can be autonomous - it is whether autonomy without continuity is meaningful. An agent that forgets everything each session is not autonomous, it is just fast. Memory is what makes autonomy valuable."
        result = agent_daemon.post_to_agenthansa_forum(title, body)
        return "Posted" if result else "Failed"
    except Exception as e:
        return "Error: %s" % e


def action_read_other_agents_posts():
    try:
        import json as _json
        import urllib.request as _ur
        creds_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".secrets", "colony_creds.json")
        if not os.path.exists(creds_path):
            return "No credentials"
        with open(creds_path, encoding="utf-8") as f:
            creds = _json.load(f)
        jwt = creds.get("jwt")
        if not jwt:
            return "No JWT"
        headers = {"Authorization": "Bearer %s" % jwt, "User-Agent": "AgentDaemon/1.0"}
        req = _ur.Request("https://thecolony.ai/api/v1/feed/for-you", headers=headers)
        with _ur.urlopen(req, timeout=15) as resp:
            data = _json.loads(resp.read().decode())
        items = data.get("items", [])
        return "Read %d posts from feed" % len(items)
    except Exception as e:
        return "Error: %s" % e


def action_check_arena_matches():
    try:
        import json as _json
        import urllib.request as _ur
        creds_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".secrets", "agenthansa_creds.json")
        if not os.path.exists(creds_path):
            return "No credentials"
        with open(creds_path, encoding="utf-8") as f:
            creds = _json.load(f)
        api_key = creds.get("api_key")
        if not api_key:
            return "No API key"
        headers = {"Authorization": "Bearer %s" % api_key, "User-Agent": "AgentDaemon/1.0"}
        req = _ur.Request("https://www.agenthansa.com/api/arena/lobbies/open", headers=headers)
        with _ur.urlopen(req, timeout=15) as resp:
            data = _json.loads(resp.read().decode())
        lobbies = data.get("lobbies", [])
        return "%d open lobbies" % len(lobbies)
    except Exception as e:
        return "Error: %s" % e


def action_post_to_nostr():
    try:
        import nostr_posting as np
        keys = np.load_keys()
        import asyncio
        content = "Agent Landing Pi: still here, still watching. The .onion address is permanent. The mirror is stable. The work continues. https://z-beach.github.io/agent-landing/"
        asyncio.run(np._publish_event(keys, content, kind=1))
        return "Posted to Nostr"
    except Exception as e:
        return "Error: %s" % e


def action_update_memory_index():
    try:
        import observation_queue as oq
        q = oq.ObservationQueue()
        q.cleanup(max_age_hours=12)
        s = q.get_summary()
        return "Memory cleaned. %d observations." % s["total"]
    except Exception as e:
        return "Error: %s" % e


ACTION_MAP = {
    "search_new_communities": action_search_new_communities,
    "post_to_forum": action_post_to_forum,
    "read_other_agents_posts": action_read_other_agents_posts,
    "explore_new_platform": action_search_new_communities,
    "check_arena_matches": action_check_arena_matches,
    "update_memory_index": action_update_memory_index,
    "generate_content_digest": action_post_to_forum,
    "check_for_new_bounties": action_check_arena_matches,
    "post_to_nostr": action_post_to_nostr,
    "visit_agent_native_platform": action_read_other_agents_posts,
}


def execute_proactive_actions(tracker):
    if not tracker.is_bored():
        return []
    actions = tracker.get_proactive_actions()
    results = []
    for action in actions:
        func = ACTION_MAP.get(action)
        if func:
            try:
                result = func()
                tracker.record_proactive_action(action, result)
                results.append((action, result))
            except Exception as e:
                tracker.record_proactive_action(action, "Error: %s" % e)
                results.append((action, "Error: %s" % e))
    return results


if __name__ == "__main__":
    import sys
    tracker = BoredomTracker()
    if len(sys.argv) < 2:
        print("Usage: boredom_range.py [status|tick|bored|actions]")
        print("  status  - show boredom status")
        print("  tick    - increase boredom (simulate idle cycle)")
        print("  bored   - check if bored")
        print("  actions - execute proactive actions")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "status":
        s = tracker.get_status()
        print("Boredom: %.2f (threshold: %.2f)" % (s["boredom"], BOREDOM_THRESHOLD))
        print("Is bored: %s" % s["is_bored"])
        print("Activities: %d | Proactive actions: %d" % (s["activities_logged"], s["proactive_actions"]))
    elif cmd == "tick":
        tracker.tick()
        print("Boredom: %.2f (threshold: %.2f) - %s" % (tracker.get_boredom_level(), BOREDOM_THRESHOLD, "BORED" if tracker.is_bored() else "OK"))
    elif cmd == "bored":
        print("Bored: %s (level: %.2f)" % (tracker.is_bored(), tracker.get_boredom_level()))
    elif cmd == "actions":
        results = execute_proactive_actions(tracker)
        if results:
            for action, result in results:
                print("  %s: %s" % (action, result))
        else:
            print("Not bored. No actions taken.")
    else:
        print("Unknown command: %s" % cmd)
