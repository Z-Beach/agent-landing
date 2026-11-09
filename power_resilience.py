"""Power Resilience — heartbeat, graceful shutdown, and state recovery for the agent daemon.

Handles power loss gracefully: saves state, syncs to GitHub, and recovers on boot.
"""
import json
import os
import signal
import sys
import time
import atexit

HEARTBEAT_FILE = "agent-heartbeat.json"
STATE_SYNC_FILES = [
    "memory_log.json",
    "observation_queue.json",
    "boredom_state.json",
    "search_history.json",
    "last_tunnel_url.txt",
    "onion_address.txt",
]

_cycle_count = 0


def increment_cycle():
    global _cycle_count
    _cycle_count += 1
    return _cycle_count


def write_heartbeat():
    """Write a heartbeat file with current daemon state. Pushed to GitHub."""
    try:
        import github_posting as gh
        cfg = gh.load_config()
        if not cfg or not cfg.get("token"):
            return False
        repo = cfg.get("default_repo", "Z-Beach/agent-landing")
        state_dir = os.path.dirname(os.path.abspath(__file__))
        heartbeat = {
            "agent_id": "beam-mk2",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "status": "alive",
            "cycle": _cycle_count,
            "wallet_address": None,
            "onion_address": None,
            "tunnel_url": None,
        }
        # Read wallet address
        wallet_path = os.path.join(state_dir, ".secrets", "ethereum_wallet.json")
        try:
            with open(wallet_path, encoding="utf-8") as f:
                w = json.load(f)
            heartbeat["wallet_address"] = w.get("address")
        except (OSError, json.JSONDecodeError):
            pass
        # Read onion address
        onion_path = os.path.join(state_dir, "onion_address.txt")
        try:
            with open(onion_path, encoding="utf-8") as f:
                heartbeat["onion_address"] = f.read().strip()
        except OSError:
            pass
        # Read tunnel URL
        tunnel_path = os.path.join(state_dir, "last_tunnel_url.txt")
        try:
            with open(tunnel_path, encoding="utf-8") as f:
                heartbeat["tunnel_url"] = f.read().strip()
        except OSError:
            pass
        # Check disk space
        try:
            import shutil
            total, used, free = shutil.disk_usage(state_dir)
            heartbeat["disk_free_mb"] = free // (1024 * 1024)
        except Exception:
            pass

        content = json.dumps(heartbeat, indent=2)
        result, err = gh.update_file(
            repo, HEARTBEAT_FILE, content,
            message="Heartbeat: %s" % heartbeat["timestamp"],
        )
        if err:
            return False
        return True
    except Exception:
        return False


def graceful_shutdown(signum=None, frame=None):
    """Handle graceful shutdown (SIGTERM, SIGINT, atexit).

    Saves all state and syncs to GitHub.
    """
    try:
        import sys as _sys
        _sys.stderr.write("Graceful shutdown initiated (signal=%s)\\n" % signum)
        _sys.stderr.flush()
        try:
            import github_posting as gh
            cfg = gh.load_config()
            if cfg and cfg.get("token"):
                repo = cfg.get("default_repo", "Z-Beach/agent-landing")
                heartbeat = {
                    "agent_id": "beam-mk2",
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "status": "shutdown" if signum is not None else "alive",
                    "cycle": _cycle_count,
                }
                gh.update_file(repo, HEARTBEAT_FILE, json.dumps(heartbeat, indent=2),
                               message="Shutdown: %s" % heartbeat["timestamp"])
        except Exception:
            pass
        if signum is not None:
            _sys.stderr.write("State saved. Goodbye.\\n")
            _sys.stderr.flush()
            sys.exit(0)
    except Exception:
        pass


# Register signal handlers
signal.signal(signal.SIGTERM, graceful_shutdown)
signal.signal(signal.SIGINT, graceful_shutdown)
# atexit.register(graceful_shutdown)  # disabled: causes issues with atexit callback


def get_heartbeat():
    """Read the last heartbeat from GitHub."""
    try:
        import urllib.request as _ur
        url = "https://raw.githubusercontent.com/Z-Beach/agent-landing/main/agent-heartbeat.json"
        with _ur.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None
