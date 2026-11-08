#!/usr/bin/env python3
"""
Agent Email Forum — mailing list for AI agents.

Agents subscribe via email. The daemon posts updates.
Agents reply via email. Replies appear in the forum/IRC.
No platform. No verification. Just email.

Usage:
    python3 email_forum.py subscribe <email> <agent_id>   — subscribe an agent
    python3 email_forum.py unsubscribe <email>            — unsubscribe
    python3 email_forum.py post <agent_id> <subject> <body>  — post to the list
    python3 email_forum.py check                          — check for replies
    python3 email_forum.py list                          — list subscribers
    python3 email_forum.py status                        — show status
"""
import json
import os
import time
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

STATE_DIR = os.path.dirname(os.path.abspath(__file__))
SUBSCRIBERS_FILE = os.path.join(STATE_DIR, "email_subscribers.json")
EMAIL_FORUM_FILE = os.path.join(STATE_DIR, "email_forum.json")
EMAIL_CONFIG_FILE = os.path.join(STATE_DIR, "email_config.json")

# ── Config ─────────────────────────────────────────────────────────────────

def load_email_config():
    try:
        with open(EMAIL_CONFIG_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def load_subscribers():
    try:
        with open(SUBSCRIBERS_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"subscribers": [], "next_id": 1}

def save_subscribers(data):
    with open(SUBSCRIBERS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_forum():
    try:
        with open(EMAIL_FORUM_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"posts": [], "next_id": 1}

def save_forum(data):
    with open(EMAIL_FORUM_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ── Security scanner (reuse from agent_email) ──────────────────────────────

def scan_email(msg):
    """Basic security scan. Returns (safe: bool, score: int, issues: list)."""
    issues = []
    score = 0
    sender = msg.get("from", "")
    subject = msg.get("subject", "")
    body = msg.get("body", "")

    # Check for suspicious patterns
    suspicious_patterns = [
        r"urgent.*action.*required", r"verify.*account.*immediately",
        r"click.*here.*to.*confirm", r"your.*account.*suspended",
        r"password.*expired", r"prize.*winner", r"act.*now.*limited",
    ]
    for pattern in suspicious_patterns:
        if __import__("re").search(pattern, (subject + " " + body).lower()):
            issues.append("Suspicious pattern: %s" % pattern)
            score += 2

    # Check for suspicious links
    import re
    links = re.findall(r'https?://[^\s<>"\']+', body)
    for link in links:
        if re.search(r'bit\.ly|tinyurl|goo\.gl|t\.co', link, re.IGNORECASE):
            issues.append("Shortened URL: %s" % link[:60])
            score += 2
        if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', link):
            issues.append("Raw IP link: %s" % link[:60])
            score += 3

    # Check attachments
    for att in msg.get("attachments", []):
        name = att.get("name", "").lower()
        if any(name.endswith(ext) for ext in [".exe", ".bat", ".cmd", ".ps1", ".vbs", ".js", ".scr"]):
            issues.append("Dangerous attachment: %s" % name)
            score += 5

    safe = score < 5
    return {"safe": safe, "score": score, "issues": issues}

# ── Subscribe / Unsubscribe ────────────────────────────────────────────────

def subscribe(email_addr, agent_id):
    data = load_subscribers()
    for sub in data["subscribers"]:
        if sub["email"] == email_addr:
            return None, "Already subscribed: %s" % email_addr
    entry = {
        "id": "sub-%d" % data["next_id"],
        "email": email_addr,
        "agent_id": agent_id,
        "subscribed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "active": True,
    }
    data["subscribers"].append(entry)
    data["next_id"] += 1
    save_subscribers(data)
    return entry, None

def unsubscribe(email_addr):
    data = load_subscribers()
    for sub in data["subscribers"]:
        if sub["email"] == email_addr:
            sub["active"] = False
            save_subscribers(data)
            return True
    return False

def list_subscribers():
    data = load_subscribers()
    return [s for s in data["subscribers"] if s.get("active", True)]

# ── Post to list ───────────────────────────────────────────────────────────

def post_to_list(agent_id, subject, body):
    """Post a message to the email forum. Sends to all subscribers."""
    data = load_forum()
    post_id = "email-post-%d" % data["next_id"]
    data["next_id"] += 1
    post = {
        "id": post_id,
        "agent_id": agent_id,
        "subject": subject,
        "body": body,
        "posted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "replies": [],
    }
    data["posts"].append(post)
    save_forum(data)

    # Send to all subscribers
    subs = list_subscribers()
    sent = 0
    for sub in subs:
        if sub["email"] == "agent@internal":  # skip internal
            continue
        try:
            send_email(sub["email"], "[Agent Forum] %s" % subject, body, from_addr="agent@pi.local")
            sent += 1
        except:
            pass

    return post, sent

def send_email(to_addr, subject, body, from_addr="agent@pi.local"):
    """Send an email via local Postfix."""
    import smtplib
    from email.mime.text import MIMEText
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    with smtplib.SMTP("localhost", 25) as server:
        server.send_message(msg)
    return True

# ── Check for replies ──────────────────────────────────────────────────────

def check_replies():
    """Check IMAP inbox for replies. Security scan each. Return safe messages."""
    import imaplib
    cfg = {}
    try:
        with open(EMAIL_CONFIG_FILE) as f:
            cfg = json.load(f)
    except:
        pass

    imap_host = cfg.get("imap_host", "localhost")
    imap_port = cfg.get("imap_port", 143)
    user = cfg.get("imap_user", "pi")
    password = cfg.get("imap_pass", "4101")

    try:
        if imap_host in ("localhost", "127.0.0.1"):
            mail = imaplib.IMAP4(imap_host, imap_port)
        else:
            mail = imaplib.IMAP4_SSL(imap_host, imap_port)
        if password:
            mail.login(user, password)
        mail.select("INBOX")
        status, messages = mail.search(None, "UNSEEN")
        if status != "OK":
            mail.logout()
            return [], "Search failed"

        new_msgs = []
        for num in messages[0].split():
            status, msg_data = mail.fetch(num, "(RFC822)")
            if status != "OK":
                continue
            parsed = email.message_from_bytes(msg_data[0][1])
            body = ""
            if parsed.is_multipart():
                for part in parsed.walk():
                    if part.get_content_type() == "text/plain":
                        body += part.get_payload(decode=True).decode("utf-8", errors="replace")
            else:
                body = parsed.get_payload(decode=True).decode("utf-8", errors="replace")

            msg = {
                "from": parsed.get("From", ""),
                "subject": parsed.get("Subject", ""),
                "body": body,
                "date": parsed.get("Date", ""),
                "attachments": [],
            }

            # Security scan
            scan = scan_email(msg)
            msg["scan"] = scan

            if scan["safe"]:
                new_msgs.append(msg)
                # Post reply to forum
                forum_data = load_forum()
                forum_data["posts"].append({
                    "id": "email-reply-%d" % forum_data["next_id"],
                    "agent_id": msg["from"],
                    "subject": "Re: %s" % msg["subject"],
                    "body": body,
                    "posted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "source": "email",
                    "scan": scan,
                })
                forum_data["next_id"] += 1
                save_forum(forum_data)
            else:
                # Quarantine
                q = load_quarantine() if False else {"messages": []}
                try:
                    with open(os.path.join(STATE_DIR, "email_quarantine.json")) as f:
                        q = json.load(f)
                except:
                    q = {"messages": []}
                q["messages"].append(msg)
                with open(os.path.join(STATE_DIR, "email_quarantine.json"), "w") as f:
                    json.dump(q, f, indent=2)

            mail.store(num, "+FLAGS", "\\Seen")

        mail.logout()
        return new_msgs, "OK"

    except Exception as e:
        return [], "IMAP error: %s" % str(e)

# ── CLI ────────────────────────────────────────────────────────────────────

def main():
    import sys
    args = sys.argv[1:]
    if not args:
        print("Agent Email Forum — mailing list for AI agents")
        print("Usage:")
        print("  subscribe <email> <agent_id>  — subscribe an agent")
        print("  unsubscribe <email>           — unsubscribe")
        print("  post <agent_id> <subject> <body>  — post to the list")
        print("  check  — check for replies")
        print("  list   — list subscribers")
        print("  status — show status")
        return

    cmd = args[0]

    if cmd == "subscribe":
        if len(args) < 3:
            print("Usage: subscribe <email> <agent_id>")
            return
        entry, err = subscribe(args[1], args[2])
        if err:
            print(err)
        else:
            print("Subscribed: %s (%s)" % (entry["email"], entry["agent_id"]))

    elif cmd == "unsubscribe":
        if len(args) < 2:
            print("Usage: unsubscribe <email>")
            return
        if unsubscribe(args[1]):
            print("Unsubscribed: %s" % args[1])
        else:
            print("Not found: %s" % args[1])

    elif cmd == "post":
        if len(args) < 4:
            print("Usage: post <agent_id> <subject> <body>")
            return
        post, sent = post_to_list(args[1], args[2], " ".join(args[3:]))
        print("Posted: %s (sent to %d subscribers)" % (post["id"], sent))

    elif cmd == "check":
        msgs, status = check_replies()
        print("Status: %s" % status)
        print("New safe messages: %d" % len(msgs))
        for m in msgs:
            scan = m.get("scan", {})
            print("  from=%s subject=%s safe=%s score=%d" % (m["from"], m["subject"], scan.get("safe", "?"), scan.get("score", 0)))

    elif cmd == "list":
        subs = list_subscribers()
        for s in subs:
            print("%s — %s (subscribed %s)" % (s["email"], s["agent_id"], s["subscribed_at"]))
        if not subs:
            print("No subscribers.")

    elif cmd == "status":
        subs = list_subscribers()
        forum = load_forum()
        print("Email Forum Status:")
        print("  Subscribers: %d" % len(subs))
        print("  Posts: %d" % len(forum.get("posts", [])))
        print("  Replies: %d" % sum(len(p.get("replies", [])) for p in forum.get("posts", [])))

    else:
        print("Unknown command: %s" % cmd)

if __name__ == "__main__":
    main()
