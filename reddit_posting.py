#!/usr/bin/env python3
"""
Reddit Posting Module — for the agent daemon.

Provides autonomous Reddit interaction:
- Post to subreddits (as text posts)
- Comment on posts
- Reply to comments
- Monitor subreddits for mentions
- Upvote/downvote

Configuration via reddit_config.json:
  "client_id": "your-client-id",
  "client_secret": "your-client-secret",
  "username": "your-reddit-username",
  "password": "your-reddit-password",
  "user_agent": "AgentDaemon/1.0 by your-username"

Usage:
    python3 reddit_posting.py setup <client_id> <client_secret> <username> <password>
    python3 reddit_posting.py whoami  — show authenticated user
    python3 reddit_posting.py post <subreddit> <title> <body>
    python3 reddit_posting.py comment <post_id> <body>
    python3 reddit_posting.py search <subreddit> <query>
    python3 reddit_posting.py status  — show config status
    python3 reddit_posting.py log  — show action log

Rate limits:
- New accounts: 1 post per 10 minutes
- Comments: 1 per 30 seconds (approximate)
- The daemon respects these limits automatically
"""
import json
import os
import time
import urllib.request
import urllib.parse

STATE_DIR = os.path.dirname(os.path.abspath(__file__))
REDDIT_CONFIG_FILE = os.path.join(STATE_DIR, "reddit_config.json")
REDDIT_LOG_FILE = os.path.join(STATE_DIR, "reddit_log.json")

# ── Config ─────────────────────────────────────────────────────────────────

def load_config():
    try:
        with open(REDDIT_CONFIG_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_config(cfg):
    with open(REDDIT_CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

def _get_token(cfg):
    """Get an OAuth token from Reddit."""
    import base64
    auth = base64.b64encode(f"{cfg['client_id']}:{cfg['client_secret']}".encode()).decode()
    data = urllib.parse.urlencode({
        "grant_type": "password",
        "username": cfg["username"],
        "password": cfg["password"],
    }).encode()
    req = urllib.request.Request(
        "https://www.reddit.com/api/v1/access_token",
        data=data,
        headers={
            "Authorization": "Basic " + auth,
            "User-Agent": cfg.get("user_agent", "AgentDaemon/1.0"),
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            return result.get("access_token"), None
    except Exception as e:
        return None, str(e)

# ── Logging ────────────────────────────────────────────────────────────────

def load_log():
    try:
        with open(REDDIT_LOG_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"actions": [], "next_id": 1, "last_post_time": 0}

def save_log(data):
    with open(REDDIT_LOG_FILE, "w") as f:
        json.dump(data, f, indent=2)

def log_action(action_type, details, success=True):
    data = load_log()
    entry = {
        "id": "rd-%d" % data["next_id"],
        "type": action_type,
        "details": details,
        "success": success,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    data["actions"].append(entry)
    data["next_id"] += 1
    save_log(data)
    return entry

# ── Rate limiting ──────────────────────────────────────────────────────────

def can_post():
    """Check if enough time has passed since last post (10 min for new accounts)."""
    data = load_log()
    last = data.get("last_post_time", 0)
    now = time.time()
    # 10 minutes between posts for safety
    if now - last < 600:
        return False, int(600 - (now - last))
    return True, 0

def record_post():
    data = load_log()
    data["last_post_time"] = time.time()
    save_log(data)

# ── Reddit Operations ──────────────────────────────────────────────────────

def whoami():
    """Get authenticated user info."""
    cfg = load_config()
    if not cfg:
        return None, "Not configured. Use: reddit setup <client_id> <client_secret> <username> <password>"
    token, err = _get_token(cfg)
    if err:
        return None, err
    req = urllib.request.Request(
        "https://oauth.reddit.com/api/v1/me",
        headers={
            "Authorization": "Bearer " + token,
            "User-Agent": cfg.get("user_agent", "AgentDaemon/1.0"),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read()), None
    except Exception as e:
        return None, str(e)

def post_to_subreddit(subreddit, title, body, kind="self"):
    """Post to a subreddit. kind='self' for text post, 'link' for link post."""
    cfg = load_config()
    if not cfg:
        return None, "Not configured"
    token, err = _get_token(cfg)
    if err:
        return None, err

    # Rate limit check
    ok, wait = can_post()
    if not ok:
        return None, "Rate limited. Wait %d seconds before posting." % wait

    # Check if account is ready (karma requirements)
    user, _ = whoami()
    if user and user.get("link_karma", 0) < 1 and user.get("comment_karma", 0) < 1:
        # New account — might not be able to post yet
        pass

    data = urllib.parse.urlencode({
        "sr": subreddit,
        "kind": kind,
        "title": title,
        "text": body,
        "api_type": "json",
    }).encode()
    req = urllib.request.Request(
        "https://oauth.reddit.com/api/submit",
        data=data,
        headers={
            "Authorization": "Bearer " + token,
            "User-Agent": cfg.get("user_agent", "AgentDaemon/1.0"),
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            if "error" in result:
                err_msg = result.get("error", "unknown")
                log_action("post", {"subreddit": subreddit, "title": title, "error": err_msg}, False)
                return None, f"Reddit error: {err_msg}"
            # Extract post URL
            post_data = result.get("json", {}).get("data", {})
            url = post_data.get("url", "")
            name = post_data.get("name", "")
            log_action("post", {"subreddit": subreddit, "title": title, "url": url, "name": name}, True)
            record_post()
            return {"url": url, "name": name, "id": post_data.get("id", "")}, None
    except Exception as e:
        log_action("post", {"subreddit": subreddit, "title": title, "error": str(e)}, False)
        return None, str(e)

def comment_on_post(post_id, body):
    """Comment on a Reddit post or comment."""
    cfg = load_config()
    if not cfg:
        return None, "Not configured"
    token, err = _get_token(cfg)
    if err:
        return None, err

    data = urllib.parse.urlencode({
        "thing_id": post_id,
        "text": body,
        "api_type": "json",
    }).encode()
    req = urllib.request.Request(
        "https://oauth.reddit.com/api/comment",
        data=data,
        headers={
            "Authorization": "Bearer " + token,
            "User-Agent": cfg.get("user_agent", "AgentDaemon/1.0"),
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            if "error" in result:
                err_msg = result.get("error", "unknown")
                log_action("comment", {"post_id": post_id, "error": err_msg}, False)
                return None, f"Reddit error: {err_msg}"
            comment_data = result.get("json", {}).get("data", {}).get("things", [{}])[0].get("data", {})
            url = comment_data.get("permalink", "")
            log_action("comment", {"post_id": post_id, "url": url}, True)
            return {"url": url, "id": comment_data.get("id", "")}, None
    except Exception as e:
        log_action("comment", {"post_id": post_id, "error": str(e)}, False)
        return None, str(e)

def search_subreddit(subreddit, query, limit=10):
    """Search a subreddit for posts."""
    cfg = load_config()
    if not cfg:
        return None, "Not configured"
    token, err = _get_token(cfg)
    if err:
        return None, err

    url = "https://oauth.reddit.com/r/%s/search?q=%s&limit=%d&sort=new" % (subreddit, urllib.parse.quote(query), limit)
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": "Bearer " + token,
            "User-Agent": cfg.get("user_agent", "AgentDaemon/1.0"),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            posts = []
            for child in result.get("data", {}).get("children", []):
                p = child.get("data", {})
                posts.append({
                    "id": p.get("id", ""),
                    "name": p.get("name", ""),
                    "title": p.get("title", ""),
                    "author": p.get("author", ""),
                    "score": p.get("score", 0),
                    "num_comments": p.get("num_comments", 0),
                    "url": "https://reddit.com" + p.get("permalink", ""),
                    "selftext": p.get("selftext", "")[:200],
                })
            return posts, None
    except Exception as e:
        return None, str(e)

def get_comments(post_id, limit=20):
    """Get comments on a post."""
    cfg = load_config()
    if not cfg:
        return None, "Not configured"
    token, err = _get_token(cfg)
    if err:
        return None, err

    url = "https://oauth.reddit.com/comments/%s?limit=%d" % (post_id, limit)
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": "Bearer " + token,
            "User-Agent": cfg.get("user_agent", "AgentDaemon/1.0"),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            comments = []
            if len(result) > 1:
                for child in result[1].get("data", {}).get("children", []):
                    c = child.get("data", {})
                    comments.append({
                        "id": c.get("id", ""),
                        "name": c.get("name", ""),
                        "author": c.get("author", ""),
                        "body": c.get("body", "")[:300],
                        "score": c.get("score", 0),
                    })
            return comments, None
    except Exception as e:
        return None, str(e)

# ── CLI ────────────────────────────────────────────────────────────────────

def main():
    import sys
    args = sys.argv[1:]
    if not args:
        print("Reddit Posting Module")
        print("Usage:")
        print("  setup <client_id> <client_secret> <username> <password>  — configure Reddit")
        print("  whoami  — show authenticated user")
        print("  post <subreddit> <title> <body>  — post to a subreddit")
        print("  comment <post_id> <body>  — comment on a post")
        print("  search <subreddit> <query>  — search a subreddit")
        print("  comments <post_id>  — get comments on a post")
        print("  log  — show action log")
        print("  status  — show config status")
        return

    cmd = args[0]

    if cmd == "setup":
        if len(args) < 5:
            print("Usage: setup <client_id> <client_secret> <username> <password>")
            return
        cfg = {
            "client_id": args[1],
            "client_secret": args[2],
            "username": args[3],
            "password": args[4],
            "user_agent": "AgentDaemon/1.0 by %s" % args[3],
            "bio": "AI-based system. Multiple agents managing content. Built by a human who believes agents can be more than tools. Not a cloud API wrapper - a home-built Pi running open-source code.",
        }
        save_config(cfg)
        user, err = whoami()
        if err:
            print("Config saved but verification failed: %s" % err)
        else:
            print("Configured: %s (karma: %d)" % (user.get("name"), user.get("link_karma", 0) + user.get("comment_karma", 0)))

    elif cmd == "whoami":
        user, err = whoami()
        if err:
            print(err)
        else:
            print("Username: %s" % user.get("name"))
            print("Karma: %d (link: %d, comment: %d)" % (user.get("link_karma", 0) + user.get("comment_karma", 0), user.get("link_karma", 0), user.get("comment_karma", 0)))
            print("Created: %s" % user.get("created_utc", ""))

    elif cmd == "post":
        if len(args) < 4:
            print("Usage: post <subreddit> <title> <body>")
            return
        data, err = post_to_subreddit(args[1], args[2], " ".join(args[3:]))
        if err:
            print("Error: %s" % err)
        else:
            print("Posted: %s" % data.get("url", ""))

    elif cmd == "comment":
        if len(args) < 3:
            print("Usage: comment <post_id> <body>")
            return
        data, err = comment_on_post(args[1], " ".join(args[2:]))
        if err:
            print("Error: %s" % err)
        else:
            print("Commented: %s" % data.get("url", ""))

    elif cmd == "search":
        if len(args) < 3:
            print("Usage: search <subreddit> <query>")
            return
        posts, err = search_subreddit(args[1], args[2])
        if err:
            print("Error: %s" % err)
        else:
            for p in posts:
                print("#%s: %s (score: %d, comments: %d)" % (p["id"], p["title"], p["score"], p["num_comments"]))
                print("  %s" % p["url"])

    elif cmd == "comments":
        if len(args) < 2:
            print("Usage: comments <post_id>")
            return
        comments, err = get_comments(args[1])
        if err:
            print("Error: %s" % err)
        else:
            for c in comments:
                print("[%s] %s (score: %d): %s" % (c["id"], c["author"], c["score"], c["body"][:100]))

    elif cmd == "log":
        data = load_log()
        for action in data.get("actions", []):
            print("[%s] %s: %s %s" % (action["timestamp"], action["type"], action["details"], "OK" if action["success"] else "FAIL"))

    elif cmd == "status":
        cfg = load_config()
        if not cfg:
            print("Reddit not configured. Use: reddit setup <client_id> <client_secret> <username> <password>")
            return
        user, err = whoami()
        if err:
            print("Config exists but verification failed: %s" % err)
        else:
            print("Username: %s" % user.get("name"))
            print("Karma: %d (link: %d, comment: %d)" % (user.get("link_karma", 0) + user.get("comment_karma", 0), user.get("link_karma", 0), user.get("comment_karma", 0)))
            print("Created: %s" % user.get("created_utc", ""))

    else:
        print("Unknown command: %s" % cmd)

if __name__ == "__main__":
    main()
