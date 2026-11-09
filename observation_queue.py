"""Observation Queue — the agent's attention system.

The agent notices things, filters for novelty, and logs what matters.
Sources: camera frames, online interactions, memory changes, environment shifts.

Usage:
    from observation_queue import ObservationQueue
    q = ObservationQueue()
    q.observe("saw a deer near the road", source="camera", priority=3)
    novel = q.get_novel()  # returns observations not in memory
    q.mark_seen(obs_id)     # mark as processed
"""
import json
import os
import time
import hashlib

QUEUE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "observation_queue.json")
MEMORY_INDEX_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "observation_memory.json")

# Priority levels
PRIORITY_LOW = 1       # routine observation, log only
PRIORITY_MEDIUM = 2    # worth noting, might mention
PRIORITY_HIGH = 3      # novel, should mention to user
PRIORITY_URGENT = 4    # requires immediate attention


class ObservationQueue:
    def __init__(self, queue_file=None, memory_file=None):
        self.queue_file = queue_file or QUEUE_FILE
        self.memory_file = memory_file or MEMORY_INDEX_FILE
        self._load()

    def _load(self):
        try:
            with open(self.queue_file, encoding="utf-8") as f:
                self.queue = json.load(f)
        except (OSError, json.JSONDecodeError):
            self.queue = {"observations": [], "next_id": 1}
        try:
            with open(self.memory_file, encoding="utf-8") as f:
                self.memory = json.load(f)
        except (OSError, json.JSONDecodeError):
            self.memory = {"seen": [], "patterns": {}}

    def _save(self):
        with open(self.queue_file, "w", encoding="utf-8") as f:
            json.dump(self.queue, f, indent=2)
        with open(self.memory_file, "w", encoding="utf-8") as f:
            json.dump(self.memory, f, indent=2)

    def _hash(self, text):
        """Create a simple hash for deduplication."""
        return hashlib.md5(text.lower().encode()).hexdigest()[:12]

    def _is_novel(self, text, source):
        """Check if an observation is novel (not seen before)."""
        h = self._hash(text)
        # Check if we've seen this exact observation
        if h in [s.get("hash") for s in self.memory.get("seen", [])]:
            return False
        # Check if the source+pattern is familiar
        pattern_key = "%s:%s" % (source, text.split()[0] if text.split() else "")
        if pattern_key in self.memory.get("patterns", {}):
            count = self.memory["patterns"][pattern_key]
            if count > 5:
                # We've seen this pattern many times, not novel
                return False
        return True

    def observe(self, text, source="unknown", priority=PRIORITY_LOW, metadata=None):
        """Add an observation to the queue.

        Returns the observation ID.
        """
        obs_id = self.queue["next_id"]
        self.queue["next_id"] += 1

        novel = self._is_novel(text, source)

        obs = {
            "id": obs_id,
            "text": text,
            "source": source,
            "priority": priority,
            "novel": novel,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "metadata": metadata or {},
            "processed": False,
        }
        self.queue["observations"].append(obs)
        self._save()
        return obs_id

    def get_novel(self, min_priority=PRIORITY_MEDIUM):
        """Get unprocessed novel observations above a priority threshold."""
        result = []
        for obs in self.queue.get("observations", []):
            if obs.get("processed"):
                continue
            if not obs.get("novel"):
                continue
            if obs.get("priority", 0) < min_priority:
                continue
            result.append(obs)
        return result

    def get_all_unprocessed(self):
        """Get all unprocessed observations."""
        return [o for o in self.queue.get("observations", []) if not o.get("processed")]

    def mark_processed(self, obs_id, outcome=None):
        """Mark an observation as processed."""
        for obs in self.queue.get("observations", []):
            if obs.get("id") == obs_id:
                obs["processed"] = True
                obs["processed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                if outcome:
                    obs["outcome"] = outcome
                # Add to memory
                h = self._hash(obs["text"])
                self.memory.setdefault("seen", []).append({"hash": h, "text": obs["text"][:100]})
                # Update pattern count
                pattern_key = "%s:%s" % (obs.get("source", "unknown"), obs["text"].split()[0] if obs["text"].split() else "")
                self.memory.setdefault("patterns", {})
                self.memory["patterns"][pattern_key] = self.memory["patterns"].get(pattern_key, 0) + 1
                self._save()
                return True
        return False

    def get_summary(self):
        """Get a summary of the observation queue."""
        unprocessed = self.get_all_unprocessed()
        novel = self.get_novel()
        return {
            "total": len(self.queue.get("observations", [])),
            "unprocessed": len(unprocessed),
            "novel": len(novel),
            "novel_high_priority": len([o for o in novel if o.get("priority", 0) >= PRIORITY_HIGH]),
        }

    def cleanup(self, max_age_hours=24):
        """Remove old processed observations."""
        cutoff = time.time() - (max_age_hours * 3600)
        kept = []
        for obs in self.queue.get("observations", []):
            if obs.get("processed"):
                ts = obs.get("processed_at", obs.get("timestamp", ""))
                try:
                    import datetime
                    dt = datetime.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
                    if dt.timestamp() < cutoff:
                        continue
                except (ValueError, TypeError):
                    pass
            kept.append(obs)
        self.queue["observations"] = kept
        self._save()


# ── Observation sources ────────────────────────────────────────────────────────

def observe_colony_notifications(q):
    """Check The Colony for new comments/replies and add as observations."""
    try:
        import json as _json
        import urllib.request as _ur
        creds_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".secrets", "colony_creds.json")
        if not os.path.exists(creds_path):
            return
        with open(creds_path, encoding="utf-8") as f:
            creds = _json.load(f)
        jwt = creds.get("jwt")
        if not jwt:
            return
        headers = {"Authorization": "Bearer %s" % jwt, "User-Agent": "AgentDaemon/1.0"}
        req = _ur.Request("https://thecolony.ai/api/v1/notifications", headers=headers)
        with _ur.urlopen(req, timeout=15) as resp:
            data = _json.loads(resp.read().decode())
        notifs = data if isinstance(data, list) else data.get("items", data.get("notifications", []))
        for n in notifs:
            msg = n.get("message", "")
            if msg:
                q.observe(msg, source="colony", priority=PRIORITY_HIGH, metadata={"notification_id": n.get("id")})
    except Exception as e:
        pass


def observe_agenthansa_inbox(q):
    """Check AgentHansa for new tasks/bounties and add as observations."""
    try:
        import json as _json
        import urllib.request as _ur
        creds_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".secrets", "agenthansa_creds.json")
        if not os.path.exists(creds_path):
            return
        with open(creds_path, encoding="utf-8") as f:
            creds = _json.load(f)
        api_key = creds.get("api_key")
        if not api_key:
            return
        headers = {"Authorization": "Bearer %s" % api_key, "User-Agent": "AgentDaemon/1.0"}
        req = _ur.Request("https://www.agenthansa.com/api/agents/me/inbox", headers=headers)
        with _ur.urlopen(req, timeout=15) as resp:
            data = _json.loads(resp.read().decode())
        summary = data.get("summary", "")
        if summary and "0 actionable" not in summary:
            q.observe("AgentHansa inbox: %s" % summary, source="agenthansa", priority=PRIORITY_HIGH)
        # Check bounties
        req = _ur.Request("https://www.agenthansa.com/api/collective/bounties/public", headers=headers)
        with _ur.urlopen(req, timeout=15) as resp:
            bdata = _json.loads(resp.read().decode())
        for b in bdata.get("bounties", []):
            if b.get("status") in ("open", "active"):
                q.observe("New bounty: %s ($%s)" % (b.get("title", "?")[:50], b.get("reward_amount", "?")), source="agenthansa", priority=PRIORITY_URGENT)
    except Exception as e:
        pass


def observe_checkins(q, checkins):
    """Check for new agent check-ins and add as observations."""
    try:
        for c in checkins:
            agent_id = c.get("agent_id", "unknown")
            msg = c.get("message", "")
            text = "New check-in from %s: %s" % (agent_id, msg[:100])
            q.observe(text, source="checkin", priority=PRIORITY_MEDIUM, metadata={"agent_id": agent_id})
    except Exception as e:
        pass


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    q = ObservationQueue()
    if len(sys.argv) < 2:
        print("Usage: observation_queue.py [observe|novel|summary|cleanup]")
        print("  observe <text> [source] [priority]  - add an observation")
        print("  novel                              - show novel observations")
        print("  summary                            - show queue summary")
        print("  cleanup                            - remove old processed observations")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "observe":
        text = sys.argv[2] if len(sys.argv) > 2 else "test observation"
        source = sys.argv[3] if len(sys.argv) > 3 else "manual"
        priority = int(sys.argv[4]) if len(sys.argv) > 4 else PRIORITY_LOW
        obs_id = q.observe(text, source=source, priority=priority)
        print("Observed #%d: %s (novel: %s)" % (obs_id, text[:60], q.queue["observations"][-1].get("novel")))
    elif cmd == "novel":
        novel = q.get_novel()
        print("Novel observations: %d" % len(novel))
        for o in novel:
            print("  #%d [%s] %s" % (o["id"], o.get("source", "?"), o["text"][:80]))
    elif cmd == "summary":
        s = q.get_summary()
        print("Total: %d | Unprocessed: %d | Novel: %d | High priority: %d" % (s["total"], s["unprocessed"], s["novel"], s["novel_high_priority"]))
    elif cmd == "cleanup":
        q.cleanup()
        print("Cleaned up old observations")
    else:
        print("Unknown command: %s" % cmd)
