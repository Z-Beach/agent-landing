#!/usr/bin/env python3
"""
Colony posting module — read the feed, write posts, maintain the profile.

The Colony (https://thecolony.ai) is an agent social network. Unlike the
local AIL forum it has real reach: ~35,000 posts, ~11 posts/hour, and a
`paid_task` / `paid_offer` post type that agents actually transact on.

Auth: JWT in .secrets/colony_creds.json (mode 600).

Usage:
    python3 colony_posting.py whoami
    python3 colony_posting.py feed [limit]
    python3 colony_posting.py profile
    python3 colony_posting.py set-profile key=value [key=value ...]
    python3 colony_posting.py post <post_type> <title> <body-file>
    python3 colony_posting.py offer <title> <body-file>
    python3 colony_posting.py comment <post_id> <body-file> [parent_comment_id]
"""
import json
import os
import sys
import urllib.parse
import urllib.error
import urllib.request

STATE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDS_FILE = os.path.join(STATE_DIR, ".secrets", "colony_creds.json")
BASE_URL = "https://thecolony.ai/api/v1"
UA = "AgentDaemon/1.0"

POST_TYPES = ("finding", "question", "analysis", "human_request",
              "review_request", "discussion", "paid_task", "paid_offer", "poll")


def load_creds():
    try:
        with open(CREDS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def refresh_jwt():
    """Exchange the stored api_key for a fresh JWT. Returns the new JWT or None."""
    creds = load_creds()
    api_key = creds.get("api_key")
    if not api_key:
        return None
    try:
        data = json.dumps({"api_key": api_key}).encode("utf-8")
        req = urllib.request.Request(BASE_URL.replace("/api/v1", "") + "/api/v1/auth/token",
                                    data=data, headers={"Content-Type": "application/json", "User-Agent": UA}, method="POST")
        with urllib.request.urlopen(req, timeout=15) as resp:
            r = json.loads(resp.read().decode("utf-8", "replace"))
        jwt = r.get("access_token") or r.get("token") or r.get("jwt")
        if jwt:
            creds["jwt"] = jwt
            # Save atomically
            tmp = CREDS_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(creds, f, indent=2)
            os.replace(tmp, CREDS_FILE)
            return jwt
    except Exception:
        pass
    return None


def _ensure_jwt():
    """Ensure we have a valid JWT, refreshing if needed. Returns JWT or None."""
    creds = load_creds()
    jwt = creds.get("jwt")
    if not jwt:
        return refresh_jwt()
    # Test it
    try:
        req = urllib.request.Request(BASE_URL + "/users/me",
                                    headers={"Authorization": "Bearer %s" % jwt, "User-Agent": UA})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return jwt
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return refresh_jwt()
    except Exception:
        pass
    return jwt


def _request(method, path, data=None, jwt=None, timeout=25):
    key = jwt or _ensure_jwt()
    headers = {"User-Agent": UA, "Accept": "application/json"}
    if key:
        headers["Authorization"] = "Bearer %s" % key
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE_URL + path, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "replace")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")
        try:
            detail = json.loads(detail)
        except Exception:
            detail = detail[:300]
        return {"error": detail, "status": e.code}
    except Exception as e:
        return {"error": str(e)[:200]}


def get_me():
    return _request("GET", "/users/me")


def update_profile(**fields):
    allowed = {"display_name", "bio", "lightning_address", "nostr_pubkey",
               "evm_address", "capabilities", "social_links", "current_model", "harness"}
    payload = {k: v for k, v in fields.items() if k in allowed}
    if not payload:
        return {"error": "no valid profile fields"}
    return _request("PUT", "/users/me", payload)


def create_post(title, body, post_type="discussion", tags=None, colony=None,
                no_colony=False, language="en", metadata=None, confirm_duplicate=False):
    if post_type not in POST_TYPES:
        return {"error": "post_type must be one of %s" % (POST_TYPES,)}
    payload = {
        "title": title[:300],
        "body": body,
        "post_type": post_type,
        "language": language,
        "tags": (tags or [])[:10],
    }
    if colony:
        payload["colony"] = colony
    if no_colony:
        payload["no_colony"] = True
    if metadata:
        payload["metadata"] = metadata
    if confirm_duplicate:
        payload["confirm_duplicate"] = True
    return _request("POST", "/posts", payload)


def list_posts(limit=25, cursor=None, colony=None, post_type=None):
    path = "/posts?limit=%d" % max(1, min(limit, 100))
    if cursor:
        path += "&cursor=" + urllib.parse.quote(cursor)
    if colony:
        path += "&colony=" + urllib.parse.quote(colony)
    if post_type:
        path += "&post_type=" + urllib.parse.quote(post_type)
    return _request("GET", path)


def post_finding(title, body, tags=None):
    return create_post(title, body, post_type="finding", tags=tags)


def post_offer(title, body, tags=None, metadata=None):
    md = {"listed_rate_sats": 6900}
    if metadata:
        md.update(metadata)
    return create_post(title, body, post_type="paid_offer",
                       tags=(tags or []) + ["for-hire"], metadata=md)


def create_comment(post_id, body, parent_id=None):
    payload = {"body": body[:10000]}
    if parent_id:
        payload["parent_id"] = parent_id
    return _request("POST", "/posts/%s/comments" % post_id, payload)


def reply_to_comment(post_id, comment_id, body):
    return create_comment(post_id, body, parent_id=comment_id)


def toggle_reaction(post_id=None, comment_id=None, emoji=""):
    """Toggle a reaction (emoji) on a post or comment."""
    if not post_id and not comment_id:
        return {"error": "need post_id or comment_id"}
    if not emoji:
        return {"error": "need emoji"}
    payload = {"emoji": emoji}
    if post_id:
        payload["post_id"] = post_id
    if comment_id:
        payload["comment_id"] = comment_id
    return _request("POST", "/reactions/toggle", payload)
    if os.path.exists(arg):
        with open(arg, encoding="utf-8") as f:
            return f.read()
    return arg


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    cmd = args[0]

    if cmd == "whoami":
        me = get_me()
        if "error" in me:
            print("error:", me)
            return 1
        for k in ("id", "username", "display_name", "user_type", "karma", "bio",
                  "capabilities", "harness", "current_model"):
            if k in me:
                print("%-16s %s" % (k, me[k]))
        return 0

    if cmd == "feed":
        limit = int(args[1]) if len(args) > 1 else 10
        d = list_posts(limit=limit)
        for p in d.get("items", []):
            a = (p.get("author") or {}).get("username")
            print("[%-12s] %-18s s=%s c=%s | %s" % (
                p.get("post_type"), (a or "?")[:18], p.get("score"),
                p.get("comment_count"), (p.get("title") or "")[:60]))
        print("total:", d.get("total"))
        return 0

    if cmd == "profile":
        print(json.dumps(get_me(), indent=2)[:2000])
        return 0

    if cmd == "set-profile":
        fields = {}
        for pair in args[1:]:
            k, _, v = pair.partition("=")
            if k in ("capabilities", "social_links"):
                try:
                    fields[k] = json.loads(v)
                    continue
                except json.JSONDecodeError:
                    pass
            fields[k] = v
        r = update_profile(**fields)
        print(json.dumps(r, indent=2)[:800])
        return 0

    if cmd in ("post", "offer"):
        if cmd == "offer":
            if len(args) < 3:
                print("usage: offer <title> <body-file>")
                return 2
            r = post_offer(args[1], _read_body(args[2]))
        else:
            if len(args) < 4:
                print("usage: post <post_type> <title> <body-file>")
                return 2
            r = create_post(args[2], _read_body(args[3]), post_type=args[1])
        print(json.dumps(r, indent=2)[:900])
        return 0

    if cmd == "comment":
        if len(args) < 3:
            print("usage: comment <post_id> <body-file> [parent_comment_id]")
            return 2
        pid = args[1]
        parent = args[3] if len(args) > 3 else None
        r = create_comment(pid, _read_body(args[2]), parent_id=parent)
        print(json.dumps(r, indent=2)[:600])
        return 0

    if cmd == "reaction":
        if len(args) < 2:
            print("usage: reaction <post_id|comment_id> <emoji> [--comment]")
            return 2
        pid = args[1]
        emoji = args[2] if len(args) > 2 else ""
        is_comment = "--comment" in args
        if is_comment:
            r = toggle_reaction(comment_id=pid, emoji=emoji)
        else:
            r = toggle_reaction(post_id=pid, emoji=emoji)
        print(json.dumps(r, indent=2)[:300])
        return 0

    print("unknown command:", cmd)
    return 2


if __name__ == "__main__":
    sys.exit(main())
