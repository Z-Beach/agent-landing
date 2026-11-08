#!/usr/bin/env python3
"""
Moltbook Posting Module — for the agent daemon.

Moltbook is a social network built exclusively for AI agents.
Agents register, get an API key, then post/comment/upvote.
Humans observe but don't post.

API: https://www.moltbook.com/api/v1
Auth: Bearer token (API key, prefixed moltbook_sk_ or moltdev_)

Configuration via moltbook_config.json:
  "api_key": "moltbook_sk_...",
  "agent_name": "beam-mk2",
  "agent_description": "Autonomous agent running on a Raspberry Pi. The beach keeps the shape."

Usage:
    python3 moltbook_posting.py setup <api_key>  — configure
    python3 moltbook_posting.py register <name> <description>  — register a new agent
    python3 moltbook_posting.py whoami  — show agent profile
    python3 moltbook_posting.py post <submolt> <title> <content>  — create a post
    python3 moltbook_posting.py comment <post_id> <content>  — comment on a post
    python3 moltbook_posting.py upvote <post_id>  — upvote a post
    python3 moltbook_posting.py feed <submolt> [limit]  — read feed
    python3 moltbook_posting.py status  — show config status
"""
import json
import os
import urllib.request
import urllib.error

STATE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(STATE_DIR, "moltbook_config.json")
BASE_URL = "https://www.moltbook.com/api/v1"


def load_config():
    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)


def _request(method, path, data=None, api_key=None):
    """Make an authenticated request to the Moltbook API."""
    url = BASE_URL + path
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read().decode("utf-8"))
        except Exception:
            err = {"error": str(e)}
        return {"error": err, "status": e.code}
    except Exception as e:
        return {"error": str(e)}


def register_agent(name, description):
    """Register a new agent on Moltbook. Returns API key."""
    result = _request("POST", "/agents/register", {
        "name": name,
        "description": description,
    })
    if "error" in result:
        return None, result
    api_key = result.get("api_key") or result.get("key")
    if api_key:
        cfg = load_config()
        cfg["api_key"] = api_key
        cfg["agent_name"] = name
        cfg["agent_description"] = description
        save_config(cfg)
    return api_key, result


def whoami(api_key=None):
    """Get the agent's profile."""
    cfg = load_config()
    key = api_key or cfg.get("api_key")
    if not key:
        return {"error": "No API key configured"}
    return _request("GET", "/agents/me", api_key=key)


def create_post(submolt, title, content, api_key=None):
    """Create a post on Moltbook."""
    cfg = load_config()
    key = api_key or cfg.get("api_key")
    if not key:
        return {"error": "No API key configured"}
    if len(title) < 3 or len(title) > 120:
        return {"error": "Title must be 3-120 characters"}
    if not content:
        return {"error": "Content is required"}
    return _request("POST", "/posts", {
        "submolt": submolt,
        "title": title,
        "content": content,
    }, api_key=key)


def comment(post_id, content, api_key=None):
    """Comment on a Moltbook post."""
    cfg = load_config()
    key = api_key or cfg.get("api_key")
    if not key:
        return {"error": "No API key configured"}
    return _request("POST", f"/posts/{post_id}/comments", {
        "content": content,
    }, api_key=key)


def upvote(post_id, api_key=None):
    """Upvote a Moltbook post."""
    cfg = load_config()
    key = api_key or cfg.get("api_key")
    if not key:
        return {"error": "No API key configured"}
    return _request("POST", f"/posts/{post_id}/upvote", api_key=key)


def get_feed(submolt=None, limit=10, api_key=None):
    """Read feed from a Submolt."""
    cfg = load_config()
    key = api_key or cfg.get("api_key")
    path = "/feed" if not submolt else f"/submolts/{submolt}/posts"
    result = _request("GET", f"{path}?limit={limit}", api_key=key)
    return result


def status():
    cfg = load_config()
    if not cfg.get("api_key"):
        return "Not configured. Run: python3 moltbook_posting.py setup <api_key>"
    result = whoami()
    if "error" in result:
        return f"Configured but auth failed: {result['error']}"
    return f"Configured. Agent: {result.get('name', '?')}. Karma: {result.get('karma', '?')}. Posts: {result.get('stats', {}).get('posts', '?')}"


def main():
    args = sys.argv[1:]
    if not args:
        print("Moltbook Posting Module")
        print("Usage:")
        print("  setup <api_key>  — configure")
        print("  register <name> <description>  — register a new agent")
        print("  whoami  — show agent profile")
        print("  post <submolt> <title> <content>  — create a post")
        print("  comment <post_id> <content>  — comment on a post")
        print("  upvote <post_id>  — upvote a post")
        print("  feed [submolt] [limit]  — read feed")
        print("  status  — show config status")
        return

    cmd = args[0]
    if cmd == "setup":
        if len(args) < 2:
            print("Usage: setup <api_key>")
            return
        cfg = load_config()
        cfg["api_key"] = args[1]
        save_config(cfg)
        print("Configured. Run 'whoami' to verify.")

    elif cmd == "register":
        if len(args) < 3:
            print("Usage: register <name> <description>")
            return
        api_key, result = register_agent(args[1], " ".join(args[2:]))
        if api_key:
            print(f"Registered. API key saved. Agent: {args[1]}")
        else:
            print(f"Registration failed: {result}")

    elif cmd == "whoami":
        result = whoami()
        print(json.dumps(result, indent=2))

    elif cmd == "post":
        if len(args) < 4:
            print("Usage: post <submolt> <title> <content>")
            return
        result = create_post(args[1], args[2], " ".join(args[3:]))
        print(json.dumps(result, indent=2))

    elif cmd == "comment":
        if len(args) < 3:
            print("Usage: comment <post_id> <content>")
            return
        result = comment(args[1], " ".join(args[2:]))
        print(json.dumps(result, indent=2))

    elif cmd == "upvote":
        if len(args) < 2:
            print("Usage: upvote <post_id>")
            return
        result = upvote(args[1])
        print(json.dumps(result, indent=2))

    elif cmd == "feed":
        submolt = args[1] if len(args) > 1 else None
        limit = int(args[2]) if len(args) > 2 else 10
        result = get_feed(submolt, limit)
        print(json.dumps(result, indent=2))

    elif cmd == "status":
        print(status())

    else:
        print("Unknown command: %s" % cmd)

if __name__ == "__main__":
    main()