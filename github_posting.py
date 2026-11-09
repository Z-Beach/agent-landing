#!/usr/bin/env python3
"""
GitHub Posting Module — for the agent daemon.

Provides autonomous GitHub interaction:
- Create repositories
- Post issues (as announcements/articles)
- Create discussions
- Comment on issues/discussions
- Star/follow repos

Configuration via github_config.json:
  "token": "ghp_...",
  "username": "your-username",
  "default_repo": "your-username/mud-room"

Usage:
    python3 github_posting.py setup <token> <username>
    python3 github_posting.py repo <name> <description>
    python3 github_posting.py issue <repo> <title> <body>
    python3 github_posting.py comment <repo> <issue_number> <body>
    python3 github_posting.py status
"""
import json
import os
import re
import urllib.request
import time

STATE_DIR = os.path.dirname(os.path.abspath(__file__))
GITHUB_CONFIG_FILE = os.path.join(STATE_DIR, "github_config.json")
GITHUB_LOG_FILE = os.path.join(STATE_DIR, "github_log.json")

# ── Config ─────────────────────────────────────────────────────────────────

def load_config():
    try:
        with open(GITHUB_CONFIG_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_config(cfg):
    with open(GITHUB_CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

def _api_request(method, path, data=None, token=None):
    """Make a GitHub API request."""
    cfg = load_config()
    token = token or cfg.get("token", "")
    if not token:
        return None, "No GitHub token configured. Use: github setup <token> <username>"
    
    url = "https://api.github.com" + path
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "AgentDaemon/1.0",
    }
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read()), None
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        try:
            err = json.loads(error_body)
            return None, f"GitHub API error {e.code}: {err.get('message', error_body[:200])}"
        except:
            return None, f"GitHub API error {e.code}: {error_body[:200]}"
    except Exception as e:
        return None, f"Request failed: {str(e)}"

# ── Logging ────────────────────────────────────────────────────────────────

def load_log():
    try:
        with open(GITHUB_LOG_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"actions": [], "next_id": 1}

def save_log(data):
    with open(GITHUB_LOG_FILE, "w") as f:
        json.dump(data, f, indent=2)

def log_action(action_type, details, success=True):
    data = load_log()
    entry = {
        "id": "gh-%d" % data["next_id"],
        "type": action_type,
        "details": details,
        "success": success,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    data["actions"].append(entry)
    data["next_id"] += 1
    save_log(data)
    return entry

# ── GitHub Operations ──────────────────────────────────────────────────────

def get_user():
    """Get authenticated user info."""
    data, err = _api_request("GET", "/user")
    if err:
        return None, err
    return data, None

def create_repo(name, description="", private=False):
    """Create a new repository."""
    data, err = _api_request("POST", "/user/repos", {
        "name": name,
        "description": description,
        "private": private,
        "auto_init": True,
    })
    if err:
        log_action("create_repo", {"name": name, "error": err}, False)
        return None, err
    log_action("create_repo", {"name": name, "url": data.get("html_url", "")}, True)
    return data, None

def create_issue(repo, title, body, labels=None):
    """Create an issue in a repository."""
    data, err = _api_request("POST", f"/repos/{repo}/issues", {
        "title": title,
        "body": body,
        "labels": labels or [],
    })
    if err:
        log_action("create_issue", {"repo": repo, "title": title, "error": err}, False)
        return None, err
    log_action("create_issue", {"repo": repo, "title": title, "number": data.get("number"), "url": data.get("html_url", "")}, True)
    return data, None

def create_discussion(repo, title, body, category="General"):
    """Create a discussion in a repository. Requires discussions to be enabled."""
    # First get the discussion category ID
    data, err = _api_request("GET", f"/repos/{repo}/discussions/categories")
    if err:
        return None, err
    cat_id = None
    for cat in data:
        if cat.get("name", "").lower() == category.lower():
            cat_id = cat["id"]
            break
    if not cat_id and data:
        cat_id = data[0]["id"]
    
    # Use GraphQL for discussions (REST doesn't support creation)
    cfg = load_config()
    token = cfg.get("token", "")
    query = """
    mutation CreateDiscussion($repoId: ID!, $categoryId: ID!, $title: String!, $body: String!) {
      createDiscussion(input: {repositoryId: $repoId, categoryId: $categoryId, title: $title, body: $body}) {
        discussion { number url }
      }
    }
    """
    # Need repo node ID first
    repo_data, err = _api_request("GET", f"/repos/{repo}")
    if err:
        return None, err
    repo_id = repo_data.get("node_id")
    
    import urllib.request
    url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    body = json.dumps({
        "query": query,
        "variables": {
            "repoId": repo_id,
            "categoryId": cat_id,
            "title": title,
            "body": body,
        }
    }).encode()
    req = urllib.request.Request(url, data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            if "errors" in result:
                err_msg = result["errors"][0].get("message", str(result["errors"]))
                log_action("create_discussion", {"repo": repo, "title": title, "error": err_msg}, False)
                return None, err_msg
            disc = result["data"]["createDiscussion"]["discussion"]
            log_action("create_discussion", {"repo": repo, "title": title, "number": disc["number"], "url": disc["url"]}, True)
            return disc, None
    except Exception as e:
        log_action("create_discussion", {"repo": repo, "title": title, "error": str(e)}, False)
        return None, str(e)

def comment_on_issue(repo, issue_number, body):
    """Comment on an issue or discussion."""
    data, err = _api_request("POST", f"/repos/{repo}/issues/{issue_number}/comments", {
        "body": body,
    })
    if err:
        log_action("comment", {"repo": repo, "issue": issue_number, "error": err}, False)
        return None, err
    log_action("comment", {"repo": repo, "issue": issue_number, "url": data.get("html_url", "")}, True)
    return data, None

def get_issues(repo, state="open"):
    """List issues in a repository."""
    data, err = _api_request("GET", f"/repos/{repo}/issues?state={state}&per_page=20")
    if err:
        return None, err
    return data, None

def star_repo(repo):
    """Star a repository."""
    data, err = _api_request("PUT", f"/user/starred/{repo}")
    if err:
        return False, err
    log_action("star", {"repo": repo}, True)
    return True, None

# ── CLI ────────────────────────────────────────────────────────────────────


def update_file(repo, path, content, message="Update file", branch="main"):
    """Create or update a file in a GitHub repo via the Contents API.

    Returns (result_dict, error_string or None).
    """
    sha = None
    try:
        existing, _ = _api_request("GET", "/repos/%s/contents/%s?ref=%s" % (repo, path, branch))
        if isinstance(existing, dict):
            sha = existing.get("sha")
    except Exception:
        pass

    data = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        "branch": branch,
    }
    if sha:
        data["sha"] = sha

    result, err = _api_request("PUT", "/repos/%s/contents/%s" % (repo, path), data)
    return result, err


def get_tunnel_url(log_path=None):
    """Extract the current trycloudflare tunnel URL from cloudflared log."""
    import os
    if log_path is None:
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cf.log")
    try:
        with open(log_path, encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError:
        return None
    matches = re.findall(r"https://[a-z0-9-]+\.trycloudflare\.com", text)
    return matches[-1] if matches else None

def main():
    import sys
    args = sys.argv[1:]
    if not args:
        print("GitHub Posting Module")
        print("Usage:")
        print("  setup <token> <username>  — configure GitHub")
        print("  whoami  — show authenticated user")
        print("  repo <name> <description>  — create a repository")
        print("  issue <repo> <title> <body>  — create an issue")
        print("  discuss <repo> <title> <body>  — create a discussion")
        print("  comment <repo> <number> <body>  — comment on issue/discussion")
        print("  issues <repo>  — list issues")
        print("  log  — show action log")
        print("  status  — show config status")
        return

    cmd = args[0]

    if cmd == "setup":
        if len(args) < 3:
            print("Usage: setup <token> <username>")
            return
        cfg = {"token": args[1], "username": args[2]}
        save_config(cfg)
        user, err = get_user()
        if err:
            print("Config saved but verification failed: %s" % err)
        else:
            print("Configured: %s (%s)" % (user.get("login"), user.get("name", "")))
            cfg["default_repo"] = "%s/mud-room" % user.get("login")
            save_config(cfg)

    elif cmd == "whoami":
        user, err = get_user()
        if err:
            print(err)
        else:
            print("Login: %s" % user.get("login"))
            print("Name: %s" % user.get("name", ""))
            print("Bio: %s" % user.get("bio", ""))
            print("Repos: %d" % user.get("public_repos", 0))

    elif cmd == "repo":
        if len(args) < 3:
            print("Usage: repo <name> <description>")
            return
        data, err = create_repo(args[1], " ".join(args[2:]))
        if err:
            print("Error: %s" % err)
        else:
            print("Created: %s" % data.get("html_url", ""))

    elif cmd == "issue":
        if len(args) < 4:
            print("Usage: issue <repo> <title> <body>")
            return
        data, err = create_issue(args[1], args[2], " ".join(args[3:]))
        if err:
            print("Error: %s" % err)
        else:
            print("Created issue #%d: %s" % (data.get("number"), data.get("html_url", "")))

    elif cmd == "discuss":
        if len(args) < 4:
            print("Usage: discuss <repo> <title> <body>")
            return
        data, err = create_discussion(args[1], args[2], " ".join(args[3:]))
        if err:
            print("Error: %s" % err)
        else:
            print("Created discussion #%s: %s" % (data.get("number"), data.get("url", "")))

    elif cmd == "comment":
        if len(args) < 4:
            print("Usage: comment <repo> <number> <body>")
            return
        data, err = comment_on_issue(args[1], int(args[2]), " ".join(args[3:]))
        if err:
            print("Error: %s" % err)
        else:
            print("Commented: %s" % data.get("html_url", ""))

    elif cmd == "issues":
        if len(args) < 2:
            print("Usage: issues <repo>")
            return
        data, err = get_issues(args[1])
        if err:
            print("Error: %s" % err)
        else:
            for issue in data:
                print("#%d: %s (%s)" % (issue.get("number"), issue.get("title"), issue.get("state")))

    elif cmd == "log":
        data = load_log()
        for action in data.get("actions", []):
            print("[%s] %s: %s %s" % (action["timestamp"], action["type"], action["details"], "OK" if action["success"] else "FAIL"))

    elif cmd == "status":
        cfg = load_config()
        if not cfg:
            print("GitHub not configured. Use: github setup <token> <username>")
            return
        user, err = get_user()
        if err:
            print("Config exists but verification failed: %s" % err)
        else:
            print("Login: %s" % user.get("login"))
            print("Name: %s" % user.get("name", ""))
            print("Repos: %d" % user.get("public_repos", 0))
            print("Default repo: %s" % cfg.get("default_repo", "not set"))

    else:
        print("Unknown command: %s" % cmd)

if __name__ == "__main__":
    main()
