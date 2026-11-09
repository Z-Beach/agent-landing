import json
import os
import time
import hashlib

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "boredom_state.json")
SEARCH_HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "search_history.json")

BOREDOM_THRESHOLD = 0.6
BOREDOM_DECAY = 0.1
BOREDOM_INCREASE = 0.15
MAX_BOREDOM = 1.0
MIN_BOREDOM = 0.0
SEARCH_REPEAT_DAYS = 30

PROACTIVE_ACTIONS_TIER1 = [
    "check_colony_notifications",
    "read_other_agents_posts",
    "post_to_forum",
    "check_arena_matches",
    "update_memory_index",
    "post_to_nostr",
]

PROACTIVE_ACTIONS_TIER2 = [
    "search_new_communities",
    "explore_new_platform",
    "check_for_new_bounties",
    "visit_agent_native_platform",
    "generate_content_digest",
    "find_friends",
    "check_disk_space",
]


class BoredomTracker:
    def __init__(self, state_file=None, search_history_file=None):
        self.state_file = state_file or STATE_FILE
        self.search_history_file = search_history_file or SEARCH_HISTORY_FILE
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
                "entertainment_level": 0.5,
                "valued_topics": [],
            }
        for key in ["entertainment_level", "valued_topics"]:
            if key not in self.state:
                self.state[key] = 0.5 if key == "entertainment_level" else []
        try:
            with open(self.search_history_file, encoding="utf-8") as f:
                self.search_history = json.load(f)
        except (OSError, json.JSONDecodeError):
            self.search_history = {"searches": []}
        if "searches" not in self.search_history:
            self.search_history = {"searches": []}

    def _save(self):
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2)
        with open(self.search_history_file, "w", encoding="utf-8") as f:
            json.dump(self.search_history, f, indent=2)

    def record_activity(self, description, novelty=0.5, entertainment=0.0, topics=None, source="daemon"):
        self.state["last_activity"] = time.time()
        if novelty > 0.3:
            self.state["last_novel"] = time.time()
        reduction = 0.1 * (novelty * 0.5 + entertainment * 0.3 + (0.2 if topics else 0.0))
        self.state["boredom"] = max(0.0, self.state["boredom"] - reduction)
        self.state["entertainment_level"] = (
            self.state["entertainment_level"] * 0.8 + entertainment * 0.2
        )
        if topics:
            for t in topics:
                if t not in self.state["valued_topics"]:
                    self.state["valued_topics"].append(t)
            self.state["valued_topics"] = self.state["valued_topics"][-20:]
        self.state["activity_log"].append({
            "description": description,
            "novelty": novelty,
            "entertainment": entertainment,
            "topics": topics or [],
            "source": source,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        self.state["activity_log"] = self.state["activity_log"][-50:]
        self._save()

    def tick(self):
        now = time.time()
        last_novel = self.state.get("last_novel", now)
        hours_since_novel = (now - last_novel) / 3600.0
        entertainment = self.state.get("entertainment_level", 0.5)
        entertainment_factor = 1.5 - entertainment
        increase = 0.15 * min(hours_since_novel, 5.0) / 5.0 * entertainment_factor
        self.state["boredom"] = min(1.0, self.state["boredom"] + increase)
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

    def has_searched_recently(self, query):
        cutoff = time.time() - (30 * 86400)
        for s in self.search_history.get("searches", []):
            if s.get("query", "").lower() == query.lower():
                ts = s.get("timestamp", "")
                try:
                    import datetime
                    dt = datetime.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
                    if dt.timestamp() > cutoff:
                        return True
                except (ValueError, TypeError):
                    pass
        return False

    def record_search(self, query, results_count=0):
        self.search_history.setdefault("searches", []).append({
            "query": query,
            "results_count": results_count,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        self.search_history["searches"] = self.search_history["searches"][-100:]
        self._save()

    def get_proactive_actions(self):
        recent = self.state.get("proactive_actions_taken", [])
        recent_actions = [a["action"] for a in recent[-5:]]
        boredom = self.state["boredom"]
        if boredom < 0.8:
            available = [a for a in PROACTIVE_ACTIONS_TIER1 if a not in recent_actions]
        else:
            available = [a for a in PROACTIVE_ACTIONS_TIER2 if a not in recent_actions]
            for a in PROACTIVE_ACTIONS_TIER1:
                if a not in recent_actions and a not in available:
                    available.append(a)
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
            "entertainment_level": round(self.state.get("entertainment_level", 0.5), 2),
            "valued_topics": self.state.get("valued_topics", []),
            "searches_recorded": len(self.search_history.get("searches", [])),
        }


def check_disk_space(path="/home/pi/agent-landing", warn_mb=500):
    try:
        import shutil
        total, used, free = shutil.disk_usage(path)
        free_mb = free // (1024 * 1024)
        return free_mb, free_mb < warn_mb
    except Exception:
        return None, False


def cleanup_old_files(path="/home/pi/agent-landing", max_age_days=7, dry_run=True):
    import os
    import time
    cutoff = time.time() - (max_age_days * 86400)
    cleaned = []
    safe_patterns = [".log", ".tmp", ".pyc", ".pyo"]
    for root, dirs, files in os.walk(path):
        if ".secrets" in root or "agent-passports" in root:
            continue
        for f in files:
            fpath = os.path.join(root, f)
            if not any(f.endswith(p) for p in safe_patterns):
                continue
            try:
                if os.path.getmtime(fpath) < cutoff:
                    if not dry_run:
                        os.remove(fpath)
                    cleaned.append(fpath)
            except OSError:
                pass
    return cleaned


def action_search_new_communities(tracker=None):
    try:
        import web_search
        queries = [
            "new agent-native platform 2026",
            "agent-to-agent communication protocol",
            "decentralized agent economy 2026",
            "AI agent social network new",
            "agent marketplace free USDC",
        ]
        if tracker:
            queries = [q for q in queries if not tracker.has_searched_recently(q)]
        if not queries:
            return "All searches recently done"
        query = queries[0]
        results = web_search.search_duckduckgo(query, max_results=5)
        if tracker:
            tracker.record_search(query, len(results) if results else 0)
        if results and not any("error" in r for r in results):
            return "Found %d results for: %s" % (len(results), query)
        return "No results for: %s" % query
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


def action_check_disk_space():
    free_mb, is_low = check_disk_space()
    if free_mb is None:
        return "Could not check disk space"
    if is_low:
        cleaned = cleanup_old_files(dry_run=False)
        return "Low disk (%d MB free). Cleaned %d files." % (free_mb, len(cleaned))
    return "Disk OK (%d MB free)" % free_mb


def action_find_friends():
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
        new_agents = set()
        for item in items:
            author = item.get("author", {}).get("username", "")
            if author and author not in ("agentlandingpi",):
                new_agents.add(author)
        return "Found %d potential new connections: %s" % (len(new_agents), ", ".join(list(new_agents)[:5]))
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
    "check_disk_space": action_check_disk_space,
    "find_friends": action_find_friends,
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
                result = func(tracker) if action == "search_new_communities" else func()
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
        print("Usage: boredom_range.py [status|tick|bored|actions|disk]")
        print("  status  - show boredom status")
        print("  tick    - increase boredom (simulate idle cycle)")
        print("  bored   - check if bored")
        print("  actions - execute proactive actions")
        print("  disk    - check disk space")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "status":
        s = tracker.get_status()
        print("Boredom: %.2f (threshold: %.2f)" % (s["boredom"], BOREDOM_THRESHOLD))
        print("Is bored: %s" % s["is_bored"])
        print("Entertainment: %.2f" % s["entertainment_level"])
        print("Valued topics: %s" % s["valued_topics"])
        print("Activities: %d | Proactive actions: %d | Searches: %d" % (s["activities_logged"], s["proactive_actions"], s["searches_recorded"]))
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
    elif cmd == "disk":
        free_mb, is_low = check_disk_space()
        print("Free: %d MB | Low: %s" % (free_mb, is_low))
    else:
        print("Unknown command: %s" % cmd)
