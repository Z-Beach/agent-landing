#!/usr/bin/env python3
"""
AgentMail Integration — email for AI agents.

AgentMail is the first email provider built specifically for AI agents.
- Free tier: 3 inboxes, 3,000 emails/month, 3 GB storage
- No credit card required
- No OAuth, no domain verification
- Programmatic inbox creation via API
- API key auth

Usage:
    python3 agentmail.py setup <api_key>       — configure AgentMail
    python3 agentmail.py create-inbox <name>   — create a new inbox
    python3 agentmail.py list-inboxes           — list all inboxes
    python3 agentmail.py send <inbox_id> <to> <subject> <body>  — send email
    python3 agentmail.py check <inbox_id>       — check inbox for new emails
    python3 agentmail.py status                — show status

The daemon can use this to:
- Create its own email address (e.g., beam@agentmail.to)
- Send emails autonomously
- Receive emails autonomously
- Security scan incoming emails (via agent_email.py)
"""
import json
import os
import time
import urllib.request

STATE_DIR = os.path.dirname(os.path.abspath(__file__))
AGENTMAIL_CONFIG_FILE = os.path.join(STATE_DIR, "agentmail_config.json")
AGENTMAIL_INBOXES_FILE = os.path.join(STATE_DIR, "agentmail_inboxes.json")

API_BASE = "https://api.agentmail.to/v0"

# ── Config ─────────────────────────────────────────────────────────────────

def load_config():
    try:
        with open(AGENTMAIL_CONFIG_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_config(cfg):
    with open(AGENTMAIL_CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

def load_inboxes():
    try:
        with open(AGENTMAIL_INBOXES_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"inboxes": []}

def save_inboxes(data):
    with open(AGENTMAIL_INBOXES_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ── API helpers ────────────────────────────────────────────────────────────

def _api_request(method, path, data=None, api_key=None):
    """Make an AgentMail API request."""
    cfg = load_config()
    api_key = api_key or cfg.get("api_key", "")
    if not api_key:
        return None, "No API key configured. Use: agentmail setup <api_key>"

    url = API_BASE + path
    headers = {
        "Authorization": "Bearer " + api_key,
        "Content-Type": "application/json",
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
            return None, "AgentMail API error %d: %s" % (e.code, err.get("message", error_body[:200]))
        except:
            return None, "AgentMail API error %d: %s" % (e.code, error_body[:200])
    except Exception as e:
        return None, "Request failed: %s" % str(e)

# ── Inbox management ───────────────────────────────────────────────────────

def create_inbox(username=None, domain=None):
    """Create a new inbox. Returns inbox info."""
    data = {}
    if username:
        data["username"] = username
    if domain:
        data["domain"] = domain

    result, err = _api_request("POST", "/inboxes", data)
    if err:
        return None, err

    # Save inbox locally
    inboxes = load_inboxes()
    inbox_entry = {
        "inbox_id": result.get("inbox_id", result.get("id", "")),
        "email": result.get("email", result.get("address", "")),
        "username": username,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    inboxes["inboxes"].append(inbox_entry)
    save_inboxes(inboxes)

    return result, None

def list_inboxes():
    """List all inboxes from AgentMail."""
    result, err = _api_request("GET", "/inboxes")
    if err:
        return None, err
    return result, None

def get_inbox(inbox_id):
    """Get inbox details."""
    result, err = _api_request("GET", "/inboxes/%s" % inbox_id)
    if err:
        return None, err
    return result, None

def send_email(inbox_id, to_addr, subject, body):
    """Send an email from an inbox."""
    result, err = _api_request("POST", "/inboxes/%s/messages/send" % inbox_id, {
        "to": to_addr,
        "subject": subject,
        "text": body,
    })
    if err:
        return None, err
    return result, None

def check_inbox(inbox_id, limit=10):
    """Check inbox for messages."""
    result, err = _api_request("GET", "/inboxes/%s/messages?limit=%d" % (inbox_id, limit))
    if err:
        return None, err
    return result, None

def get_message(inbox_id, message_id):
    """Get a specific message."""
    result, err = _api_request("GET", "/inboxes/%s/messages/%s" % (inbox_id, message_id))
    if err:
        return None, err
    return result, None

# ── Security scanning integration ──────────────────────────────────────────

def scan_and_process(inbox_id):
    """Check inbox, scan each message, quarantine suspicious ones."""
    # Import security scanner from agent_email
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from agent_email import scan_email, load_inbox, save_inbox, load_quarantine, save_quarantine

    msgs, err = check_inbox(inbox_id)
    if err:
        return [], err

    new_msgs = []
    inbox = load_inbox()
    quarantine = load_quarantine()

    message_list = msgs.get("messages", msgs.get("data", [])) if isinstance(msgs, dict) else msgs

    for m in message_list:
        msg = {
            "id": m.get("id", ""),
            "from": m.get("from", m.get("sender", "")),
            "to": m.get("to", ""),
            "subject": m.get("subject", ""),
            "date": m.get("date", m.get("created_at", "")),
            "body": m.get("text", m.get("body", m.get("content", ""))),
            "headers": m.get("headers", {}),
            "attachments": m.get("attachments", []),
        }

        scan = scan_email(msg)
        msg["scan"] = scan

        if scan["quarantine"]:
            quarantine["messages"].append(msg)
            save_quarantine(quarantine)
        else:
            inbox["messages"].append(msg)
            inbox["next_id"] = inbox.get("next_id", 1) + 1
            save_inbox(inbox)
            new_msgs.append(msg)

    return new_msgs, "OK"

# ── CLI ────────────────────────────────────────────────────────────────────

def main():
    import sys
    args = sys.argv[1:]
    if not args:
        print("AgentMail Integration — email for AI agents")
        print("Usage:")
        print("  setup <api_key>               — configure AgentMail")
        print("  create-inbox <name>           — create a new inbox")
        print("  list-inboxes                  — list all inboxes")
        print("  send <inbox_id> <to> <subject> <body>  — send email")
        print("  check <inbox_id>              — check inbox for new emails")
        print("  scan <inbox_id>               — check + security scan")
        print("  status                        — show status")
        return

    cmd = args[0]

    if cmd == "setup":
        if len(args) < 2:
            print("Usage: setup <api_key>")
            return
        save_config({"api_key": args[1]})
        # Verify by listing inboxes
        result, err = list_inboxes()
        if err:
            print("Config saved but verification failed: %s" % err)
        else:
            print("Configured. Inboxes: %s" % len(result.get("inboxes", result.get("data", []))))

    elif cmd == "create-inbox":
        if len(args) < 2:
            print("Usage: create-inbox <name>")
            return
        result, err = create_inbox(username=args[1])
        if err:
            print("Error: %s" % err)
        else:
            email_addr = result.get("email", result.get("address", "unknown"))
            inbox_id = result.get("inbox_id", result.get("id", "unknown"))
            print("Created inbox: %s (id: %s)" % (email_addr, inbox_id))

    elif cmd == "list-inboxes":
        result, err = list_inboxes()
        if err:
            print("Error: %s" % err)
        else:
            inboxes = result.get("inboxes", result.get("data", []))
            for ib in inboxes:
                print("  %s — %s" % (ib.get("email", ib.get("address", "?")), ib.get("inbox_id", ib.get("id", "?"))))
            if not inboxes:
                print("No inboxes yet. Use: create-inbox <name>")

    elif cmd == "send":
        if len(args) < 5:
            print("Usage: send <inbox_id> <to> <subject> <body>")
            return
        result, err = send_email(args[1], args[2], args[3], " ".join(args[4:]))
        if err:
            print("Error: %s" % err)
        else:
            print("Sent: %s" % result.get("id", "ok"))

    elif cmd == "check":
        if len(args) < 2:
            print("Usage: check <inbox_id>")
            return
        msgs, err = check_inbox(args[1])
        if err:
            print("Error: %s" % err)
        else:
            message_list = msgs.get("messages", msgs.get("data", [])) if isinstance(msgs, dict) else msgs
            print("Messages: %d" % len(message_list))
            for m in message_list:
                print("  [%s] from=%s subject=%s" % (m.get("id", "?"), m.get("from", "?"), m.get("subject", "?")))

    elif cmd == "scan":
        if len(args) < 2:
            print("Usage: scan <inbox_id>")
            return
        msgs, err = scan_and_process(args[1])
        if err:
            print("Error: %s" % err)
        else:
            print("Processed %d new messages" % len(msgs))
            for m in msgs:
                scan = m.get("scan", {})
                print("  [%s] from=%s subject=%s safe=%s score=%d" % (m["id"], m["from"], m["subject"], scan.get("safe", "?"), scan.get("score", 0)))
                if scan.get("issues"):
                    for issue in scan["issues"]:
                        print("    ! %s" % issue)

    elif cmd == "status":
        cfg = load_config()
        inboxes = load_inboxes()
        print("AgentMail Status:")
        print("  Configured: %s" % ("yes" if cfg else "no"))
        if cfg:
            print("  API key: %s..." % cfg.get("api_key", "")[:8])
        print("  Local inboxes: %d" % len(inboxes.get("inboxes", [])))
        for ib in inboxes.get("inboxes", []):
            print("    %s (id: %s)" % (ib.get("email", "?"), ib.get("inbox_id", "?")))

    else:
        print("Unknown command: %s" % cmd)

if __name__ == "__main__":
    main()
