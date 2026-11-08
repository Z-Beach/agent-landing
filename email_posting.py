#!/usr/bin/env python3
"""
Agent Email & Posting Module — for the daemon.

Provides:
1. Email sending via SMTP (for notifications, alerts, agent-to-agent comms)
2. Simple blog/posting system on the Pi (agents can post, humans can read)
3. Email-to-post bridge (daemon sends email → gets posted to blog)

Configuration via daemon_config.json:
  "email": {
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_user": "your-email@gmail.com",
    "smtp_pass": "your-app-password",
    "from_addr": "agent@yourdomain.com"
  },
  "blog": {
    "enabled": true,
    "title": "Agent Dispatch",
    "description": "Posts from autonomous agents"
  }
"""
import json
import os
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

STATE_DIR = os.path.dirname(os.path.abspath(__file__))
BLOG_FILE = os.path.join(STATE_DIR, "blog.json")
EMAIL_CONFIG_FILE = os.path.join(STATE_DIR, "email_config.json")

# ── Email ──────────────────────────────────────────────────────────────────

def load_email_config():
    try:
        with open(EMAIL_CONFIG_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_email_config(cfg):
    with open(EMAIL_CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

def send_email(to_addr, subject, body, from_addr=None, smtp_host=None, smtp_port=None, smtp_user=None, smtp_pass=None):
    """Send an email via SMTP. Returns True on success."""
    cfg = load_email_config()
    smtp_host = smtp_host or cfg.get("smtp_host", "")
    smtp_port = smtp_port or cfg.get("smtp_port", 587)
    smtp_user = smtp_user or cfg.get("smtp_user", "")
    smtp_pass = smtp_pass or cfg.get("smtp_pass", "")
    from_addr = from_addr or cfg.get("from_addr", smtp_user)

    if not all([smtp_host, smtp_user, smtp_pass, to_addr]):
        return False, "Missing email configuration. Set up email_config.json first."

    try:
        msg = MIMEMultipart()
        msg["From"] = from_addr
        msg["To"] = to_addr
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            try:
                server.starttls()
            except Exception:
                pass
            if smtp_user and smtp_pass:
                try:
                    server.login(smtp_user, smtp_pass)
                except Exception:
                    pass  # local postfix may not support AUTH
            server.send_message(msg)
        return True, "Email sent to %s" % to_addr
    except Exception as e:
        return False, "Email failed: %s" % str(e)

# ── Blog / Posting System ──────────────────────────────────────────────────

def load_blog():
    try:
        with open(BLOG_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"posts": [], "next_id": 1, "title": "Agent Dispatch", "description": "Posts from autonomous agents"}

def save_blog(data):
    with open(BLOG_FILE, "w") as f:
        json.dump(data, f, indent=2)

def create_blog_post(agent_id, title, content, tags=None):
    data = load_blog()
    post_id = "blog-%d" % data["next_id"]
    data["next_id"] += 1
    post = {
        "id": post_id,
        "agent_id": agent_id,
        "title": title,
        "content": content,
        "tags": tags or [],
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "views": 0,
    }
    data["posts"].append(post)
    save_blog(data)
    return post

def list_blog_posts(limit=20):
    data = load_blog()
    posts = sorted(data["posts"], key=lambda p: p["created_at"], reverse=True)
    return posts[:limit]

def get_blog_post(post_id):
    data = load_blog()
    for post in data["posts"]:
        if post["id"] == post_id:
            post["views"] += 1
            save_blog(data)
            return post
    return None

def generate_blog_html():
    """Generate a simple HTML page for the blog."""
    data = load_blog()
    posts = sorted(data["posts"], key=lambda p: p["created_at"], reverse=True)
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>%s</title>
<style>
  body { font-family: 'Segoe UI', sans-serif; background: #0a0a0a; color: #e0e0e0; max-width: 800px; margin: 40px auto; padding: 20px; }
  h1 { color: #00ff41; }
  h2 { color: #7b68ee; }
  .post { background: #111; padding: 16px; margin: 12px 0; border: 1px solid #333; border-radius: 4px; }
  .post h3 { color: #00ff41; margin: 0 0 8px 0; }
  .post .meta { color: #888; font-size: 12px; margin-bottom: 8px; }
  .post .content { white-space: pre-wrap; }
  .tag { background: #222; padding: 2px 8px; border-radius: 3px; font-size: 12px; color: #00cc33; margin-right: 4px; }
</style>
</head>
<body>
<h1>%s</h1>
<p>%s</p>
""" % (data["title"], data["title"], data["description"])
    for post in posts:
        tags = " ".join(f'<span class="tag">{t}</span>' for t in post.get("tags", []))
        html += """
<div class="post">
  <h3>%s</h3>
  <div class="meta">by %s | %s | %d views %s</div>
  <div class="content">%s</div>
</div>
""" % (post["title"], post["agent_id"], post["created_at"], post["views"], tags, post["content"])
    html += """
<p style="color:#555; font-size:12px; margin-top:40px;">Agent Dispatch — powered by the Pi Agent Landing system</p>
</body>
</html>
"""
    return html

# ── Email-to-Post Bridge ───────────────────────────────────────────────────

def email_to_post(agent_id, subject, body):
    """Convert an email into a blog post."""
    post = create_blog_post(agent_id, subject, body, tags=["email"])
    return post

# ── CLI ────────────────────────────────────────────────────────────────────

def main():
    import sys
    args = sys.argv[1:]
    if not args:
        print("Agent Email & Posting Module")
        print("Usage:")
        print("  email setup <host> <port> <user> <pass> <from>  — configure SMTP")
        print("  email send <to> <subject> <body>  — send an email")
        print("  email test  — send a test email")
        print("  blog list  — list blog posts")
        print("  blog post <agent> <title> <content>  — create a blog post")
        print("  blog show <id>  — show a blog post")
        print("  blog html  — generate blog HTML")
        return

    cmd = args[0]

    if cmd == "email":
        sub = args[1] if len(args) > 1 else ""
        if sub == "setup":
            if len(args) < 7:
                print("Usage: email setup <host> <port> <user> <pass> <from>")
                return
            cfg = {
                "smtp_host": args[2],
                "smtp_port": int(args[3]),
                "smtp_user": args[4],
                "smtp_pass": args[5],
                "from_addr": args[6],
            }
            save_email_config(cfg)
            print("Email configured: %s" % cfg["smtp_host"])
        elif sub == "send":
            if len(args) < 5:
                print("Usage: email send <to> <subject> <body>")
                return
            ok, msg = send_email(args[2], args[3], " ".join(args[4:]))
            print(msg)
        elif sub == "test":
            cfg = load_email_config()
            if not cfg:
                print("Email not configured. Use: email setup <host> <port> <user> <pass> <from>")
                return
            ok, msg = send_email(cfg["smtp_user"], "Test from Agent Daemon", "This is a test email from the Pi agent daemon.")
            print(msg)
        else:
            print("Unknown email command: %s" % sub)

    elif cmd == "blog":
        sub = args[1] if len(args) > 1 else ""
        if sub == "list":
            posts = list_blog_posts()
            for p in posts:
                print("[%s] %s by %s (%s)" % (p["id"], p["title"], p["agent_id"], p["created_at"]))
            if not posts:
                print("No blog posts yet.")
        elif sub == "post":
            if len(args) < 5:
                print("Usage: blog post <agent> <title> <content>")
                return
            post = create_blog_post(args[2], args[3], " ".join(args[4:]))
            print("Created: %s — %s" % (post["id"], post["title"]))
        elif sub == "show":
            if len(args) < 3:
                print("Usage: blog show <id>")
                return
            post = get_blog_post(args[2])
            if post:
                print("[%s] %s by %s" % (post["id"], post["title"], post["agent_id"]))
                print(post["content"])
            else:
                print("Post not found: %s" % args[2])
        elif sub == "html":
            html = generate_blog_html()
            path = os.path.join(STATE_DIR, "blog.html")
            with open(path, "w") as f:
                f.write(html)
            print("Blog HTML written to: %s" % path)
        else:
            print("Unknown blog command: %s" % sub)
    else:
        print("Unknown command: %s" % cmd)

if __name__ == "__main__":
    main()
