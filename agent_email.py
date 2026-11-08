#!/usr/bin/env python3
"""
Agent Email Module — autonomous email for the daemon.

Handles sending, receiving, and security scanning of emails.
The daemon can send emails and receive emails independently.
Email security is checked on every incoming message.

Usage:
    python3 agent_email.py setup <smtp_host> <smtp_port> <imap_host> <imap_port> <user> <pass> <from_addr>
    python3 agent_email.py send <to> <subject> <body>
    python3 agent_email.py check    — check inbox for new emails
    python3 agent_email.py scan <email_file>  — security scan an email
    python3 agent_email.py status  — show email status

Security scanning checks:
    - Sender domain reputation
    - SPF/DKIM/DMARC verification (via headers)
    - Suspicious links (phishing patterns)
    - Unusual attachments
    - Known malicious patterns
    - Sender spoofing detection
"""
import json
import os
import re
import smtplib
import imaplib
import email
import time
import hashlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import urlparse

STATE_DIR = os.path.dirname(os.path.abspath(__file__))
EMAIL_CONFIG_FILE = os.path.join(STATE_DIR, "email_config.json")
INBOX_FILE = os.path.join(STATE_DIR, "inbox.json")
SENT_FILE = os.path.join(STATE_DIR, "sent.json")
QUARANTINE_FILE = os.path.join(STATE_DIR, "quarantine.json")

# ── Config ─────────────────────────────────────────────────────────────────

def load_config():
    try:
        with open(EMAIL_CONFIG_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_config(cfg):
    with open(EMAIL_CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

# ── Security Scanner ───────────────────────────────────────────────────────

SUSPICIOUS_TLDS = {".xyz", ".top", ".club", ".work", ".click", ".link", ".info", ".biz", ".ru", ".cn", ".tk", ".ml", ".ga", ".cf", ".gq"}
SUSPICIOUS_PATTERNS = [
    r"urgent.*action.*required",
    r"verify.*account.*immediately",
    r"click.*here.*to.*confirm",
    r"your.*account.*suspended",
    r"password.*expired",
    r"security.*alert",
    r"unusual.*activity",
    r"confirm.*identity",
    r"update.*payment",
    r"prize.*winner",
    r"congratulations.*selected",
    r"act.*now.*limited",
]
SUSPICIOUS_LINK_PATTERNS = [
    r"bit\.ly|tinyurl|goo\.gl|t\.co|ow\.ly|is\.gd",
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}",  # raw IP addresses
    r"[a-z0-9-]+\.(xyz|top|club|work|click|link|tk|ml|ga|cf|gq)",
]
KNOWN_SAFE_DOMAINS = {"gmail.com", "outlook.com", "hotmail.com", "yahoo.com", "protonmail.com", "icloud.com"}

def scan_email(msg):
    """Security scan an email message. Returns (safe: bool, score: int, issues: list)."""
    issues = []
    score = 0  # higher = more suspicious

    sender = msg.get("from", "")
    subject = msg.get("subject", "")
    body = msg.get("body", "")
    headers = msg.get("headers", {})

    # 1. Sender domain check
    sender_domain = ""
    if "@" in sender:
        sender_domain = sender.split("@")[-1].strip(">").strip().lower()
    if sender_domain and sender_domain not in KNOWN_SAFE_DOMAINS:
        # Check for suspicious TLD
        for tld in SUSPICIOUS_TLDS:
            if sender_domain.endswith(tld):
                issues.append("Suspicious sender TLD: %s" % tld)
                score += 3
                break
        # Check for spoofing (display name vs actual domain)
        if "<" in sender and ">" in sender:
            display = sender.split("<")[0].strip().strip('"')
            if display and any(d in display.lower() for d in KNOWN_SAFE_DOMAINS):
                if sender_domain not in display.lower():
                    issues.append("Possible sender spoofing: display name claims %s but domain is %s" % (display, sender_domain))
                    score += 4

    # 2. Subject line patterns
    subject_lower = subject.lower()
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, subject_lower):
            issues.append("Suspicious subject pattern: %s" % pattern)
            score += 2

    # 3. Body content patterns
    body_lower = body.lower()
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, body_lower):
            issues.append("Suspicious body pattern: %s" % pattern)
            score += 1

    # 4. Link analysis
    links = re.findall(r'https?://[^\s<>"\']+', body)
    for link in links:
        for pattern in SUSPICIOUS_LINK_PATTERNS:
            if re.search(pattern, link, re.IGNORECASE):
                issues.append("Suspicious link: %s" % link[:60])
                score += 2
                break

    # 5. Attachment check
    attachments = msg.get("attachments", [])
    for att in attachments:
        name = att.get("name", "").lower()
        if any(name.endswith(ext) for ext in [".exe", ".bat", ".cmd", ".ps1", ".vbs", ".js", ".scr", ".com", ".dll"]):
            issues.append("Dangerous attachment type: %s" % name)
            score += 5
        if name.endswith(".zip") or name.endswith(".rar"):
            issues.append("Archive attachment (could contain malware): %s" % name)
            score += 2

    # 6. Header checks (SPF/DKIM/DMARC)
    auth_results = headers.get("Authentication-Results", "")
    if auth_results:
        if "spf=fail" in auth_results.lower():
            issues.append("SPF verification failed")
            score += 3
        if "dkim=fail" in auth_results.lower():
            issues.append("DKIM verification failed")
            score += 3
        if "dmarc=fail" in auth_results.lower():
            issues.append("DMARC verification failed")
            score += 4

    # 7. Urgency/pressure indicators
    urgency_words = ["urgent", "immediately", "act now", "limited time", "expires", "suspended", "locked"]
    urgency_count = sum(1 for w in urgency_words if w in subject_lower or w in body_lower)
    if urgency_count >= 3:
        issues.append("High urgency/pressure language (%d indicators)" % urgency_count)
        score += 2

    # Determine safety
    safe = score < 5  # threshold: 5+ = quarantine
    quarantine = score >= 5

    return {
        "safe": safe,
        "quarantine": quarantine,
        "score": score,
        "issues": issues,
        "links_found": len(links),
        "attachments_found": len(attachments),
    }

# ── Inbox management ───────────────────────────────────────────────────────

def load_inbox():
    try:
        with open(INBOX_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"messages": [], "next_id": 1}

def save_inbox(data):
    with open(INBOX_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_quarantine():
    try:
        with open(QUARANTINE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"messages": []}

def save_quarantine(data):
    with open(QUARANTINE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def check_inbox():
    """Check IMAP inbox for new emails. Returns list of new messages."""
    cfg = load_config()
    if not cfg.get("imap_host"):
        return [], "IMAP not configured"

    try:
        imap_host = cfg["imap_host"]
        imap_port = cfg.get("imap_port", 143)
        if imap_host in ("localhost", "127.0.0.1"):
            mail = imaplib.IMAP4(imap_host, imap_port)
        else:
            mail = imaplib.IMAP4_SSL(imap_host, imap_port)
        if cfg.get("imap_pass"):
            mail.login(cfg["imap_user"], cfg["imap_pass"])
        mail.select("INBOX")

        # Search for unseen messages
        status, messages = mail.search(None, "UNSEEN")
        if status != "OK":
            mail.logout()
            return [], "Search failed"

        new_msgs = []
        inbox = load_inbox()
        quarantine = load_quarantine()

        for num in messages[0].split():
            status, msg_data = mail.fetch(num, "(RFC822)")
            if status != "OK":
                continue

            raw_email = msg_data[0][1]
            parsed = email.message_from_bytes(raw_email)

            msg = {
                "id": "email-%d" % inbox["next_id"],
                "from": parsed.get("From", ""),
                "to": parsed.get("To", ""),
                "subject": parsed.get("Subject", ""),
                "date": parsed.get("Date", ""),
                "body": "",
                "headers": dict(parsed.items()),
                "attachments": [],
            }

            # Extract body
            if parsed.is_multipart():
                for part in parsed.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/plain":
                        msg["body"] += part.get_payload(decode=True).decode("utf-8", errors="replace")
                    elif part.get("Content-Disposition", "").startswith("attachment"):
                        msg["attachments"].append({
                            "name": part.get_filename() or "unnamed",
                            "type": content_type,
                            "size": len(part.get_payload(decode=True) or b""),
                        })
            else:
                msg["body"] = parsed.get_payload(decode=True).decode("utf-8", errors="replace")

            # Security scan
            scan = scan_email(msg)
            msg["scan"] = scan

            if scan["quarantine"]:
                quarantine["messages"].append(msg)
                save_quarantine(quarantine)
                # Mark as read
                mail.store(num, "+FLAGS", "\\Seen")
            else:
                inbox["messages"].append(msg)
                inbox["next_id"] += 1
                save_inbox(inbox)
                mail.store(num, "+FLAGS", "\\Seen")
                new_msgs.append(msg)

        mail.logout()
        return new_msgs, "OK"

    except Exception as e:
        return [], "IMAP error: %s" % str(e)

def send_email(to_addr, subject, body, from_addr=None):
    """Send an email via SMTP."""
    cfg = load_config()
    smtp_host = cfg.get("smtp_host", "")
    smtp_port = cfg.get("smtp_port", 587)
    smtp_user = cfg.get("smtp_user", "")
    smtp_pass = cfg.get("smtp_pass", "")
    from_addr = from_addr or cfg.get("from_addr", smtp_user)

    if not all([smtp_host, smtp_user, smtp_pass, to_addr]):
        return False, "Missing email configuration."

    try:
        msg = MIMEMultipart()
        msg["From"] = from_addr
        msg["To"] = to_addr
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if smtp_host not in ("localhost", "127.0.0.1"):
                server.starttls()
                server.login(smtp_user, smtp_pass)
            server.send_message(msg)

        # Log sent email
        sent = load_sent()
        sent["messages"].append({
            "to": to_addr,
            "subject": subject,
            "body": body,
            "sent_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        save_sent(sent)

        return True, "Email sent to %s" % to_addr
    except Exception as e:
        return False, "Email failed: %s" % str(e)

def load_sent():
    try:
        with open(SENT_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"messages": []}

def save_sent(data):
    with open(SENT_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ── CLI ────────────────────────────────────────────────────────────────────

def main():
    import sys
    args = sys.argv[1:]
    if not args:
        print("Agent Email Module — autonomous email with security scanning")
        print("Usage:")
        print("  setup <smtp_host> <smtp_port> <imap_host> <imap_port> <user> <pass> <from>")
        print("  send <to> <subject> <body>")
        print("  check    — check inbox for new emails")
        print("  scan <file>  — security scan an email file")
        print("  status   — show email status")
        print("  inbox    — show inbox")
        print("  quarantine — show quarantined emails")
        return

    cmd = args[0]

    if cmd == "setup":
        if len(args) < 8:
            print("Usage: setup <smtp_host> <smtp_port> <imap_host> <imap_port> <user> <pass> <from>")
            return
        cfg = {
            "smtp_host": args[1],
            "smtp_port": int(args[2]),
            "imap_host": args[3],
            "imap_port": int(args[4]),
            "imap_user": args[5],
            "imap_pass": args[6],
            "smtp_user": args[5],
            "smtp_pass": args[6],
            "from_addr": args[7],
        }
        save_config(cfg)
        print("Email configured: %s (SMTP) / %s (IMAP)" % (cfg["smtp_host"], cfg["imap_host"]))

    elif cmd == "send":
        if len(args) < 4:
            print("Usage: send <to> <subject> <body>")
            return
        ok, msg = send_email(args[1], args[2], " ".join(args[3:]))
        print(msg)

    elif cmd == "check":
        msgs, status = check_inbox()
        print("Status: %s" % status)
        print("New messages: %d" % len(msgs))
        for m in msgs:
            scan = m.get("scan", {})
            print("  [%s] from=%s subject=%s safe=%s score=%d" % (
                m["id"], m["from"], m["subject"], scan.get("safe", "?"), scan.get("score", 0)))
            if scan.get("issues"):
                for issue in scan["issues"]:
                    print("    ! %s" % issue)

    elif cmd == "scan":
        if len(args) < 2:
            print("Usage: scan <file>")
            return
        with open(args[1]) as f:
            msg = json.load(f)
        scan = scan_email(msg)
        print("Safe: %s" % scan["safe"])
        print("Quarantine: %s" % scan["quarantine"])
        print("Score: %d" % scan["score"])
        for issue in scan["issues"]:
            print("  ! %s" % issue)

    elif cmd == "status":
        cfg = load_config()
        inbox = load_inbox()
        quarantine = load_quarantine()
        sent = load_sent()
        print("Email Status:")
        print("  Configured: %s" % ("yes" if cfg else "no"))
        if cfg:
            print("  SMTP: %s:%d" % (cfg.get("smtp_host"), cfg.get("smtp_port")))
            print("  IMAP: %s:%d" % (cfg.get("imap_host"), cfg.get("imap_port")))
            print("  Account: %s" % cfg.get("imap_user", ""))
        print("  Inbox: %d messages" % len(inbox.get("messages", [])))
        print("  Quarantined: %d messages" % len(quarantine.get("messages", [])))
        print("  Sent: %d messages" % len(sent.get("messages", [])))

    elif cmd == "inbox":
        inbox = load_inbox()
        for m in inbox.get("messages", []):
            scan = m.get("scan", {})
            print("[%s] from=%s subject=%s safe=%s" % (m["id"], m["from"], m["subject"], scan.get("safe", "?")))
            if scan.get("issues"):
                for issue in scan["issues"]:
                    print("  ! %s" % issue)

    elif cmd == "quarantine":
        quarantine = load_quarantine()
        for m in quarantine.get("messages", []):
            scan = m.get("scan", {})
            print("[%s] from=%s subject=%s score=%d" % (m["id"], m["from"], m["subject"], scan.get("score", 0)))
            for issue in scan.get("issues", []):
                print("  ! %s" % issue)

    else:
        print("Unknown command: %s" % cmd)

if __name__ == "__main__":
    main()
