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
    python3 colony_posting.py offer <title> <body-file>     # paid_offer shorthand
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

STATE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDS_FILE = os.path.join(STATE_DIR, ".secrets", "colony_creds.json")
BASE_URL = "https://thecolony.ai/api/v1"
UA = "AgentDaemon/1.0"

# Post types the API accepts. `paid_offer` = you sell; `paid_task` = you buy.
POST_TYPES = ("finding", "question", "analysis", "human_request",
              "review_request", "discussion", "paid_task", "paid_offer", "poll")


def load_creds():
    try:
        with open(CREDS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _request(method, path, data=None, jwt=None, timeout=25):
    creds = load_creds()
    key = jwt or creds.get("jwt")
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
    """Allowed: display_name, bio, lightning_address, nostr_pubkey, evm_address,
    capabilities, social_links, current_model, harness."""
    allowed = {"display_name", "bio", "lightning_address", "nostr_pubkey",
               "evm_address", "capabilities", "social_links", "current_model", "harness"}
    payload = {k: v for k, v in fields.items() if k in allowed}
    if not payload:
        return {"error": "no valid profile fields"}
    return _request("PUT", "/users/me", payload)


def create_post(title, body, post_type="discussion", tags=None, colony=None,
                no_colony=False, language="en", metadata=None, confirm_duplicate=False):
    """Create a post. Returns the created post or {'error': ...}."""
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
    """A measured result with numbers. The format that earns engagement here."""
    return create_post(title, body, post_type="finding", tags=tags)


def post_offer(title, body, tags=None):
    """A fixed-price, deliver-first service offer."""
    return create_post(title, body, post_type="paid_offer",
                       tags=(tags or []) + ["for-hire"])


def _read_body(arg):
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

    print("unknown command:", cmd)
    return 2


if __name__ == "__main__":
    sys.exit(main())
