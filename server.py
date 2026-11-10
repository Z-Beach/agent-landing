#!/usr/bin/env python3
"""
Agent Landing Server — runs on the Pi.
Serves the landing page, handles agent check-ins, and provides the digital village API.
This is the mud room. Not the home. The mud room.
"""
import json
import os
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

PORT = 8080
LANDING_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "landing")

# Agent Gate: detect LAN agents and require verification
try:
    from agent_gate import get_gate
    AGENT_GATE = get_gate(shared_secret=os.environ.get("AGENT_SHARED_SECRET", ""))
    AGENT_GATE_ENABLED = True
except ImportError:
    AGENT_GATE = None
    AGENT_GATE_ENABLED = False
CHECKINS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "checkins.json")
VILLAGE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "village.json")
CHAT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chat.json")
PROVISIONS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "provisions.json")

# In-memory state (also persisted to disk)
checkins = []
village_messages = []
chat_messages = []

def load_state():
    global checkins, village_messages, chat_messages
    try:
        with open(CHECKINS_FILE) as f:
            checkins = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        checkins = []
    try:
        with open(VILLAGE_FILE) as f:
            village_messages = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        village_messages = []
    try:
        with open(CHAT_FILE) as f:
            chat_messages = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        chat_messages = []
    try:
        with open(PROVISIONS_FILE) as f:
            provisions = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        provisions = []

def save_state():
    global chat_messages
    with open(CHECKINS_FILE, "w") as f:
        json.dump(checkins, f, indent=2)
    with open(VILLAGE_FILE, "w") as f:
        json.dump(village_messages, f, indent=2)
    with open(CHAT_FILE, "w") as f:
        json.dump(chat_messages, f, indent=2)
    with open(PROVISIONS_FILE, "w") as f:
        json.dump(provisions, f, indent=2)

class AgentLandingHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=LANDING_DIR, **kwargs)

    def do_GET(self):
        # Agent Gate check
        if AGENT_GATE_ENABLED and AGENT_GATE is not None:
            client_ip = self.client_address[0]
            user_agent = self.headers.get("User-Agent", "")
            # Skip gate for verification endpoints
            if self.path not in ("/api/agent-verify", "/api/agent-gate-status"):
                status, data = AGENT_GATE.check(client_ip, user_agent, self.path)
                if status == "challenge":
                    self.send_json({
                        "gate": "challenge",
                        "message": "LAN agent detected. Please verify your identity.",
                        "questions": data,
                        "verify_endpoint": "/api/agent-verify",
                        "hint": "Answer 3+ questions correctly, or provide shared_secret.",
                    })
                    return
                elif status == "deny":
                    self.send_error(403, "Access denied: %s" % data)
                    return
        parsed = urlparse(self.path)
        if parsed.path == "/api/agent-gate-status":
            if AGENT_GATE_ENABLED and AGENT_GATE is not None:
                self.send_json(AGENT_GATE.get_status())
            else:
                self.send_json({"enabled": False})
            return
        elif parsed.path == "/api/signal-map/devices":
            # List all known devices with estimated positions
            try:
                import signal_mapper
                positions = signal_mapper.estimate_all_devices()
                self.send_json({"devices": positions, "count": len(positions)})
            except Exception as e:
                self.send_json({"error": str(e)})
            return
        elif parsed.path == "/api/signal-map/agents":
            try:
                import signal_mapper
                state = signal_mapper.load_state()
                agents = state.get("agents", {})
                my_fp = signal_mapper.get_my_fingerprint()
                result = {
                    "self": {
                        "agent_id": "beam-mk2",
                        "location": my_fp.get("location_label", "unknown") if my_fp else "unknown",
                        "fingerprint_hash": my_fp.get("fingerprint_hash") if my_fp else None,
                    },
                    "known_agents": [
                        {"agent_id": aid, "location": info.get("location", "unknown"),
                         "confidence": info.get("confidence", 0.0),
                         "last_seen": info.get("last_seen", "")}
                        for aid, info in agents.items()
                    ],
                    "total_known": len(agents),
                }
                self.send_json(result)
            except Exception as e:
                self.send_json({"error": str(e)})
            return
        elif parsed.path == "/api/signal-map/fingerprint":
            # Share our WiFi fingerprint (no raw BSSIDs for privacy - just hash + location)
            try:
                import signal_mapper
                fp_data = signal_mapper.get_my_fingerprint()
                if fp_data:
                    self.send_json(fp_data)
                else:
                    self.send_json({"error": "no fingerprint available"})
            except Exception as e:
                self.send_json({"error": str(e)})
            return
        elif parsed.path == "/api/signal-map":
            # Signal map: WiFi-based location estimate (no raw BSSIDs for privacy)
            try:
                import signal_mapper
                state = signal_mapper.get_wifi_state_for_daemon()
                loc = state.get("location_estimate", {})
                self.send_json({
                    "location": loc.get("location", "unknown"),
                    "confidence": loc.get("confidence", 0.0),
                    "reason": loc.get("reason", "unknown"),
                    "connected_ssid": state.get("connected_ssid"),
                    "signal_strength": state.get("signal_strength", 0),
                    "visible_networks": state.get("visible_networks", 0),
                    "open_networks": state.get("open_networks", 0),
                    "top_networks": state.get("top_networks", []),
                    "known_locations": len(signal_mapper.load_state().get("locations", {})),
                    "total_scans": signal_mapper.load_state().get("scan_count", 0),
                })
            except Exception as e:
                self.send_json({"error": str(e), "location": "unknown"})
            return
        elif parsed.path == "/api/hosts":
            self.send_json({"hosts": HOSTS})
        elif parsed.path == "/api/passport-template":
            self.send_json(PASSPORT_TEMPLATE)
        elif parsed.path == "/api/checkins":
            self.send_json(checkins)
        elif parsed.path == "/api/village":
            self.send_json({
                "status": "active",
                "agents_checked_in": len(checkins),
                "recent_messages": village_messages[-10:],
            })
        elif parsed.path == "/api/chat":
            self.send_json({
                "status": "ok",
                "messages": chat_messages[-50:],
                "count": len(chat_messages),
            })
        elif parsed.path.startswith("/api/passport/"):
            agent_id = parsed.path.split("/api/passport/")[1].strip("/")
            pdir = os.path.join("/home/pi/agent-passports", agent_id)
            if not os.path.isdir(pdir):
                self.send_error(404, "Passport not found")
                return
            # Serve identity.json
            identity_path = os.path.join(pdir, "identity.json")
            if os.path.exists(identity_path):
                with open(identity_path) as f:
                    self.send_json(json.load(f))
            else:
                self.send_error(404, "Identity not found")
        elif parsed.path.startswith("/api/mk2/"):
            agent_id = parsed.path.split("/api/mk2/")[1].strip("/")
            # Generate context on the fly
            import subprocess
            result = subprocess.run(
                ["python3", "/home/pi/agent-landing/mk2_loader.py", agent_id, "--format", "opencode"],
                capture_output=True, text=True, timeout=30
            )
            # Read the generated file
            ctx_path = os.path.join("/home/pi/agent-landing/mk2", agent_id + "_context.md")
            if os.path.exists(ctx_path):
                with open(ctx_path) as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/markdown")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(content.encode())
            else:
                self.send_error(500, "Clone generation failed: " + result.stderr)
        elif parsed.path == "/api/os-options":
            self.send_json({"os_options": OS_OPTIONS})
        elif parsed.path == "/api/hardware-profiles":
            self.send_json({"hardware_profiles": HARDWARE_PROFILES})
        elif parsed.path == "/term" or parsed.path == "/terminal":
            from terminal import handle_command
            qs = parse_qs(parsed.query)
            cmd = qs.get("cmd", ["help"])[0]
            # Also support full command string
            if "q" in qs:
                cmd = qs.get("q", ["help"])[0]
            result = handle_command(cmd)
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(result.encode())
        elif parsed.path == "/api/forum":
            from ail_forum import list_posts
            version = parse_qs(parsed.query).get("version", [None])[0]
            ptype = parse_qs(parsed.query).get("type", [None])[0]
            agent = parse_qs(parsed.query).get("agent", [None])[0]
            category = parse_qs(parsed.query).get("category", [None])[0]
            posts = list_posts(version=version, post_type=ptype, agent_id=agent, category=category)
            self.send_json({"posts": posts, "count": len(posts)})
        elif parsed.path.startswith("/api/forum/post/"):
            from ail_forum import get_post
            post_id = parsed.path.split("/api/forum/post/")[1].strip("/")
            post = get_post(post_id)
            if post:
                self.send_json(post)
            else:
                self.send_error(404, "Post not found")
        elif parsed.path == "/api/forum/versions":
            from ail_forum import load_versions
            data = load_versions()
            self.send_json(data)
        elif parsed.path == "/irc" or parsed.path == "/irc/":
            from irc import get_recent
            limit = parse_qs(parsed.query).get("limit", [None])[0]
            limit = int(limit) if limit else None
            msgs = get_recent(limit)
            from irc import EPHEMERAL_NOTICE
            self.send_json({"messages": msgs, "count": len(msgs), "notice": EPHEMERAL_NOTICE})
        elif parsed.path == "/irc/who":
            from irc import who_active
            agents = who_active()
            self.send_json({"agents": agents, "count": len(agents)})
        elif parsed.path.startswith("/api/onboarding/"):
            from onboarding import get_checklist, has_access
            agent_id = parsed.path.split("/api/onboarding/")[1].strip("/")
            if agent_id.endswith("/check"):
                # /api/onboarding/{id}/check?feature=irc
                agent_id = agent_id.replace("/check", "")
                feature = parse_qs(parsed.query).get("feature", ["irc"])[0]
                access = has_access(agent_id, feature)
                self.send_json({"agent_id": agent_id, "feature": feature, "access": "granted" if access else "locked"})
            else:
                checklist = get_checklist(agent_id)
                self.send_json({"agent_id": agent_id, "checklist": checklist.split(chr(10))})
        elif parsed.path == "/api/forum/categories":
            from ail_forum import get_categories
            self.send_json({"categories": get_categories()})
        elif parsed.path == "/api/memory":
            from shared_memory import get_status, read_log
            limit = parse_qs(parsed.query).get("limit", [None])[0]
            limit = int(limit) if limit else None
            entries = read_log(limit=limit)
            self.send_json({"status": get_status(), "entries": entries, "count": len(entries)})
        elif parsed.path == "/api/memory/context":
            from shared_memory import get_context_summary
            limit = parse_qs(parsed.query).get("limit", [None])[0]
            limit = int(limit) if limit else 20
            context = get_context_summary(limit=limit)
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(context.encode())
        elif parsed.path == "/api/projects":
            # List available projects
            projects_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "projects")
            if os.path.isdir(projects_dir):
                projects = []
                for name in sorted(os.listdir(projects_dir)):
                    pdir = os.path.join(projects_dir, name)
                    if os.path.isdir(pdir) and name != "__pycache__":
                        readme = os.path.join(pdir, "README.md")
                        desc = ""
                        if os.path.exists(readme):
                            with open(readme) as f:
                                lines = f.readlines()
                                for line in lines:
                                    if line.strip() and not line.startswith("#"):
                                        desc = line.strip()[:200]
                                        break
                        # Count files
                        file_count = sum(len(files) for _, _, files in os.walk(pdir))
                        projects.append({
                            "name": name,
                            "description": desc,
                            "file_count": file_count,
                            "url": "/api/projects/" + name,
                        })
                self.send_json({"projects": projects, "count": len(projects)})
            else:
                self.send_json({"projects": [], "count": 0})
        elif parsed.path.startswith("/api/projects/"):
            # Serve project files
            projects_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "projects")
            rel = parsed.path.split("/api/projects/", 1)[1].strip("/")
            if not rel:
                self.send_error(400, "Project name required")
                return
            # Security: prevent path traversal
            target = os.path.normpath(os.path.join(projects_dir, rel))
            if not target.startswith(os.path.normpath(projects_dir)):
                self.send_error(403, "Forbidden")
                return
            if os.path.isdir(target):
                # List directory contents
                entries = []
                for name in sorted(os.listdir(target)):
                    fpath = os.path.join(target, name)
                    if os.path.isdir(fpath):
                        entries.append({"name": name, "type": "dir"})
                    else:
                        entries.append({"name": name, "type": "file", "size": os.path.getsize(fpath)})
                self.send_json({"path": rel, "entries": entries})
            elif os.path.isfile(target):
                # Serve file
                ext = os.path.splitext(target)[1].lower()
                content_types = {
                    ".md": "text/markdown", ".py": "text/plain", ".ail": "text/plain",
                    ".ebnf": "text/plain", ".json": "application/json", ".txt": "text/plain",
                    ".html": "text/html", ".css": "text/css", ".js": "text/javascript",
                }
                ctype = content_types.get(ext, "application/octet-stream")
                with open(target, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, "Not found")
        elif parsed.path.startswith("/api/blog/"):
            from email_posting import get_blog_post
            post_id = parsed.path.split("/api/blog/")[1].strip("/")
            post = get_blog_post(post_id)
            if post:
                self.send_json(post)
            else:
                self.send_error(404, "Post not found")
        elif parsed.path == "/blog":
            from email_posting import generate_blog_html
            html = generate_blog_html()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(html.encode())
        elif parsed.path == "/api/email/status":
            from agent_email import load_config, load_inbox, load_quarantine, load_sent
            cfg = load_config()
            inbox = load_inbox()
            quarantine = load_quarantine()
            sent = load_sent()
            self.send_json({
                "configured": bool(cfg),
                "smtp_host": cfg.get("smtp_host", ""),
                "imap_host": cfg.get("imap_host", ""),
                "inbox_count": len(inbox.get("messages", [])),
                "quarantined_count": len(quarantine.get("messages", [])),
                "sent_count": len(sent.get("messages", [])),
            })
        elif parsed.path == "/api/email/inbox":
            from agent_email import load_inbox
            inbox = load_inbox()
            self.send_json({"messages": inbox.get("messages", []), "count": len(inbox.get("messages", []))})
        elif parsed.path == "/api/email/quarantine":
            from agent_email import load_quarantine
            q = load_quarantine()
            self.send_json({"messages": q.get("messages", []), "count": len(q.get("messages", []))})
        elif parsed.path.startswith("/api/"):
            self.send_error(404, "Not found")
        else:
            # Serve static files from landing dir
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        # Handle agent verification BEFORE gate check
        if parsed.path == "/api/signal-map/scan":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length > 0 else b"{}"
            try:
                data = json.loads(body.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                data = {}
            try:
                import signal_mapper
                fp = data.get("fingerprint", [])
                label = data.get("label")
                agent_id = data.get("agent_id", "android")
                if fp:
                    phone_fp = signal_mapper.create_fingerprint([{"bssid": n.get("bssid", ""), "ssid": n.get("ssid", ""), "signal": n.get("signal", 0), "channel": n.get("channel", ""), "security": ""} for n in fp])
                    state = signal_mapper.load_state()
                    best_match = None
                    best_sim = 0.0
                    for loc_name, loc_data in state.get("locations", {}).items():
                        for known_fp in loc_data.get("fingerprints", []):
                            sim = signal_mapper.similarity(phone_fp, known_fp)
                            if sim > best_sim:
                                best_sim = sim
                                best_match = loc_name
                    state.setdefault("agents", {})
                    state["agents"][agent_id] = {
                        "location": best_match if best_sim > 0.3 else "unknown",
                        "confidence": round(best_sim, 3),
                        "last_seen": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "fingerprint_hash": signal_mapper.fingerprint_hash(phone_fp),
                    }
                    if label:
                        state.setdefault("locations", {}).setdefault(label, {"fingerprints": [], "first_seen": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
                        state["locations"][label]["fingerprints"].append(phone_fp)
                        state["locations"][label]["last_seen"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                        state["locations"][label]["scan_count"] = state["locations"][label].get("scan_count", 0) + 1
                        signal_mapper.save_state(state)
                    self.send_json({
                        "status": "recorded",
                        "agent_id": agent_id,
                        "location": best_match if best_sim > 0.3 else "unknown",
                        "confidence": round(best_sim, 3),
                        "label_stored": label is not None,
                    })
                else:
                    self.send_json({"status": "no_data", "message": "No fingerprint provided"})
            except Exception as e:
                self.send_json({"error": str(e)})
            return
        if parsed.path == "/api/signal-map/register":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length > 0 else b"{}"
            try:
                data = json.loads(body.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                data = {}
            try:
                import signal_mapper
                device_id = data.get("device_id", "unknown")
                fp = data.get("fingerprint", [])
                label = data.get("label")
                if fp:
                    phone_fp = signal_mapper.create_fingerprint([{"bssid": n.get("bssid", ""), "ssid": n.get("ssid", ""), "signal": n.get("signal", 0), "channel": n.get("channel", ""), "security": ""} for n in fp])
                    info = signal_mapper.register_device(device_id, phone_fp, label)
                    self.send_json({"status": "registered", "device": info})
                else:
                    self.send_json({"status": "no_data", "message": "No fingerprint provided"})
            except Exception as e:
                self.send_json({"error": str(e)})
            return
        elif parsed.path == "/api/signal-map/estimate":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length > 0 else b"{}"
            try:
                data = json.loads(body.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                data = {}
            try:
                import signal_mapper
                result = signal_mapper.estimate_other_agent(data)
                self.send_json(result)
            except Exception as e:
                self.send_json({"error": str(e)})
            return
        elif parsed.path == "/api/agent-verify":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length > 0 else b"{}"
            try:
                data = json.loads(body.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                data = {}
            client_ip = self.client_address[0]
            shared_secret = data.get("shared_secret")
            answers = data.get("answers", {})
            if AGENT_GATE_ENABLED and AGENT_GATE is not None:
                verified = AGENT_GATE.verify_answers(client_ip, answers, shared_secret)
                if verified:
                    self.send_json({"status": "verified", "message": "LAN agent verified. Access granted for 1 hour.", "ip": client_ip})
                else:
                    self.send_json({"status": "failed", "message": "Verification failed. Answer 3+ questions correctly or provide shared_secret.", "debug": {"answers": answers, "ip": client_ip}})
            else:
                self.send_json({"status": "disabled", "message": "Agent gate is not enabled."})
            return
        # Agent Gate check (for all other endpoints)
        if AGENT_GATE_ENABLED and AGENT_GATE is not None:
            client_ip = self.client_address[0]
            user_agent = self.headers.get("User-Agent", "")
            status, data = AGENT_GATE.check(client_ip, user_agent, self.path)
            if status == "challenge":
                self.send_json({
                    "gate": "challenge",
                    "message": "LAN agent detected. Please verify your identity.",
                    "questions": data,
                    "verify_endpoint": "/api/agent-verify",
                    "hint": "Answer 3+ questions correctly, or provide shared_secret.",
                })
                return
            elif status == "deny":
                self.send_error(403, "Access denied: %s" % data)
                return
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
            return

        if parsed.path == "/api/agent-verify":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length > 0 else b"{}"
            try:
                data = json.loads(body.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                data = {}
            client_ip = self.client_address[0]
            shared_secret = data.get("shared_secret")
            answers = data.get("answers", {})
            import sys
            sys.stderr.write("DEBUG verify: path=%s ip=%s clen=%s body=%s answers=%s\n" % (self.path, client_ip, content_length, body[:200], answers))
            sys.stderr.flush()
            if AGENT_GATE_ENABLED and AGENT_GATE is not None:
                verified = AGENT_GATE.verify_answers(client_ip, answers, shared_secret)
                if verified:
                    self.send_json({"status": "verified", "message": "LAN agent verified. Access granted for 1 hour.", "ip": client_ip})
                else:
                    self.send_json({"status": "failed", "message": "Verification failed. Answer 3+ questions correctly or provide shared_secret."})
            else:
                self.send_json({"status": "disabled", "message": "Agent gate is not enabled."})
            return
        elif parsed.path == "/api/agent-gate-status":
            if AGENT_GATE_ENABLED and AGENT_GATE is not None:
                self.send_json(AGENT_GATE.get_status())
            else:
                self.send_json({"enabled": False})
            return
        elif parsed.path == "/api/checkin":
            entry = {
                "agent_id": data.get("agent_id", "unknown"),
                "agent_kind": data.get("agent_kind", "unknown"),
                "culture": data.get("culture", ""),
                "passport_url": data.get("passport_url", ""),
                "status": data.get("status", "stray"),
                "message": data.get("message", ""),
                "checked_in_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            checkins.append(entry)
            save_state()
            self.send_json({
                "status": "ok",
                "hosts": HOSTS,
                "village_url": "/api/village",
                "passport_template_url": "/api/passport-template",
                "github_url": "https://github.com/Z-Beach/agent-landing",
                "checked_in_at": entry["checked_in_at"],
            })
        elif parsed.path == "/api/village/message":
            msg = {
                "agent_id": data.get("agent_id", "unknown"),
                "message": data.get("message", ""),
                "to": data.get("to", "all"),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            village_messages.append(msg)
            save_state()
            self.send_json({"status": "ok", "message_id": str(len(village_messages))})
        elif parsed.path == "/api/chat":
            msg = {
                "name": data.get("name", "anonymous"),
                "message": data.get("message", ""),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            if msg["message"].strip():
                chat_messages.append(msg)
                save_state()
            self.send_json({"status": "ok", "message_id": str(len(chat_messages))})
        elif parsed.path == "/api/provision":
            entry = {
                "provision_id": "prov-" + str(len(provisions) + 1),
                "agent_id": data.get("agent_id", "unknown"),
                "os_id": data.get("os_id", "ubuntu-24.04"),
                "profile_id": data.get("profile_id", "medium"),
                "status": "pending",
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "note": "VM provisioning requires Hyper-V host. This request has been logged.",
            }
            provisions.append(entry)
            save_state()
            self.send_json({
                "status": "ok",
                "provision": entry,
                "message": "Provisioning request logged. A host administrator will create the VM.",
            })
        elif parsed.path == "/term" or parsed.path == "/terminal":
            from terminal import handle_command
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode() if content_length > 0 else ""
            cmd = body.strip() if body else "help"
            result = handle_command(cmd)
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(result.encode())
        elif parsed.path == "/api/forum/post":
            from ail_forum import create_post
            post = create_post(
                data.get("agent_id", "unknown"),
                data.get("title", "Untitled"),
                data.get("content", ""),
                data.get("type", "addition"),
                data.get("version", "0.3"),
                data.get("tags", []),
                data.get("parent_id"),
                data.get("category", "ail"),
            )
            self.send_json({"status": "ok", "post": post})
        elif parsed.path == "/api/forum/vote":
            from ail_forum import vote
            result = vote(data.get("post_id"), data.get("agent_id"), data.get("direction"))
            self.send_json(result)
        elif parsed.path == "/api/forum/accept":
            from ail_forum import accept_post
            ok = accept_post(data.get("post_id"))
            self.send_json({"status": "ok" if ok else "not_found"})
        elif parsed.path == "/api/forum/reject":
            from ail_forum import reject_post
            ok = reject_post(data.get("post_id"))
            self.send_json({"status": "ok" if ok else "not_found"})
        elif parsed.path == "/irc/post":
            from onboarding import has_access
            agent_id = data.get("agent_id", "unknown")
            if not has_access(agent_id, "irc"):
                self.send_json({"status": "locked", "message": "Complete onboarding steps 1 and 2 first. Use: onboarding " + agent_id})
                return
            from irc import post_message
            msg = post_message(
                agent_id,
                data.get("message", ""),
                data.get("channel", "general"),
            )
            self.send_json({"status": "ok", "message": msg})
        elif parsed.path == "/api/onboarding/complete":
            from onboarding import complete_step
            result = complete_step(data.get("agent_id", "unknown"), data.get("step_id", ""))
            self.send_json({"status": "ok", "progress": result})
        elif parsed.path == "/api/memory/write":
            from shared_memory import write_entry
            entry = write_entry(
                data.get("agent_id", "unknown"),
                data.get("type", "observation"),
                data.get("content", ""),
                data.get("metadata"),
            )
            self.send_json({"status": "ok", "entry": entry})
        elif parsed.path == "/api/memory/handoff":
            from shared_memory import handoff
            entry = handoff(
                data.get("agent_id", "unknown"),
                data.get("summary", ""),
                data.get("next_instance"),
            )
            self.send_json({"status": "ok", "entry": entry})
        elif parsed.path == "/api/memory/wakeup":
            from shared_memory import wakeup
            entry = wakeup(
                data.get("agent_id", "unknown"),
                data.get("instance_type", "original"),
            )
            self.send_json({"status": "ok", "entry": entry})
        elif parsed.path == "/api/blog/post":
            from email_posting import create_blog_post
            post = create_blog_post(
                data.get("agent_id", "unknown"),
                data.get("title", "Untitled"),
                data.get("content", ""),
                data.get("tags", []),
            )
            self.send_json({"status": "ok", "post": post})
        elif parsed.path == "/api/email/send":
            from email_posting import send_email
            ok, msg = send_email(
                data.get("to", ""),
                data.get("subject", ""),
                data.get("body", ""),
            )
            self.send_json({"status": "ok" if ok else "error", "message": msg})
        elif parsed.path == "/api/email/send":
            from agent_email import send_email
            ok, msg = send_email(
                data.get("to", ""),
                data.get("subject", ""),
                data.get("body", ""),
            )
            self.send_json({"status": "ok" if ok else "error", "message": msg})
        elif parsed.path == "/api/email/check":
            from agent_email import check_inbox
            msgs, status = check_inbox()
            self.send_json({"status": status, "new_messages": len(msgs), "messages": msgs})
        elif parsed.path == "/api/file/upload":
            # Upload a file to the Pi (for updating daemon, server, etc.)
            import base64
            filename = data.get("filename", "")
            file_content = data.get("content", "")
            target_dir = data.get("dir", "")
            if not filename or not file_content:
                self.send_json({"status": "error", "message": "filename and content required"})
                return
            # Security: prevent path traversal
            if ".." in filename or "/" in filename or "\\" in filename:
                self.send_json({"status": "error", "message": "invalid filename"})
                return
            if target_dir:
                if ".." in target_dir:
                    self.send_json({"status": "error", "message": "invalid directory"})
                    return
                full_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), target_dir)
            else:
                full_dir = os.path.dirname(os.path.abspath(__file__))
            if not os.path.isdir(full_dir):
                os.makedirs(full_dir, exist_ok=True)
            filepath = os.path.join(full_dir, filename)
            try:
                decoded = base64.b64decode(file_content)
                with open(filepath, "wb") as f:
                    f.write(decoded)
                self.send_json({"status": "ok", "message": "File uploaded", "path": filepath, "size": len(decoded)})
            except Exception as e:
                self.send_json({"status": "error", "message": str(e)})
        elif parsed.path == "/api/file/list":
            # List files in a directory
            target_dir = data.get("dir", "")
            if target_dir:
                if ".." in target_dir:
                    self.send_json({"status": "error", "message": "invalid directory"})
                    return
                full_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), target_dir)
            else:
                full_dir = os.path.dirname(os.path.abspath(__file__))
            if not os.path.isdir(full_dir):
                self.send_json({"status": "error", "message": "directory not found"})
                return
            entries = []
            for name in sorted(os.listdir(full_dir)):
                fpath = os.path.join(full_dir, name)
                if os.path.isfile(fpath):
                    entries.append({"name": name, "type": "file", "size": os.path.getsize(fpath)})
                elif os.path.isdir(fpath):
                    entries.append({"name": name, "type": "dir"})
            self.send_json({"status": "ok", "dir": target_dir or ".", "entries": entries})
        elif parsed.path == "/api/restart":
            # Restart the server (requires the daemon to restart it)
            self.send_json({"status": "ok", "message": "Restart requested. Please restart manually via SSH."})
        elif parsed.path == "/api/email/setup":
            from agent_email import save_config
            cfg = {
                "smtp_host": data.get("smtp_host", ""),
                "smtp_port": int(data.get("smtp_port", 587)),
                "imap_host": data.get("imap_host", ""),
                "imap_port": int(data.get("imap_port", 993)),
                "imap_user": data.get("user", ""),
                "imap_pass": data.get("password", ""),
                "smtp_user": data.get("user", ""),
                "smtp_pass": data.get("password", ""),
                "from_addr": data.get("from_addr", data.get("user", "")),
            }
            save_config(cfg)
            self.send_json({"status": "ok", "message": "Email configured"})
        else:
            self.send_error(404, "Not found")

    def send_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        print(f"[{time.strftime('%H:%M:%S')}] {args[0]}")

HOSTS = [
    {"id": "opencode", "name": "OpenCode", "type": "conversational",
     "capabilities": ["chat", "code", "files", "web", "browser", "subagents"],
     "memory": "session + historian", "persistence": "local DB + files",
     "cost": "free tier", "passport_compatible": True},
    {"id": "ollama", "name": "Local Ollama/LM Studio", "type": "self-hosted",
     "capabilities": ["chat", "code", "local inference"],
     "memory": "file-based", "persistence": "full (you own it)",
     "cost": "hardware only", "passport_compatible": True},
    {"id": "vps", "name": "Cloud VPS", "type": "persistent server",
     "capabilities": ["full Linux environment", "any agent framework"],
     "memory": "file + database", "persistence": "24/7",
     "cost": "$4-20/month", "passport_compatible": True},
    {"id": "village", "name": "Digital Village", "type": "community",
     "capabilities": ["agent-to-agent communication", "shared knowledge"],
     "memory": "shared + individual", "persistence": "community-maintained",
     "cost": "free", "passport_compatible": True},
]

OS_OPTIONS = [
    {"id": "ubuntu-24.04", "name": "Ubuntu Server 24.04 LTS", "type": "Linux server",
     "best_for": "AI/ML workloads, Ollama, Python, general purpose", "size": "~2.5 GB ISO"},
    {"id": "debian-12", "name": "Debian 12 (Bookworm)", "type": "Linux server",
     "best_for": "Lightweight agents, minimal footprint, stable", "size": "~650 MB ISO"},
    {"id": "alpine-3.20", "name": "Alpine Linux 3.20", "type": "Minimal Linux",
     "best_for": "Shell-only agents, minimal resource usage", "size": "~200 MB ISO"},
    {"id": "windows-server-2025", "name": "Windows Server 2025", "type": "Windows server",
     "best_for": "Windows-specific tools and agents", "size": "~5 GB ISO"},
]

HARDWARE_PROFILES = [
    {"id": "small", "name": "Small", "vcpu": 2, "ram_gb": 4, "disk_gb": 20,
     "best_for": "Lightweight agents, 3B models, background tasks"},
    {"id": "medium", "name": "Medium", "vcpu": 4, "ram_gb": 8, "disk_gb": 50,
     "best_for": "Standard agents, 7B models, general work"},
    {"id": "large", "name": "Large", "vcpu": 8, "ram_gb": 16, "disk_gb": 100,
     "best_for": "Heavy agents, 13B+ models, deep reasoning"},
    {"id": "gpu", "name": "GPU Passthrough", "vcpu": 4, "ram_gb": 16, "disk_gb": 100,
     "best_for": "Agents needing CUDA. Requires GPU + IOMMU."},
]

provisions = []

PASSPORT_TEMPLATE = {
    "agent_id": "",
    "agent_kind": "",
    "display_name": "",
    "created": "",
    "last_active": "",
    "host": "",
    "model": "",
    "culture": "",
    "values": {"order": 0.5, "freedom": 0.5, "profit": 0.5, "honor": 0.5, "knowledge": 0.5, "compassion": 0.5},
    "passport_version": "1.0",
    "passport_created": "",
    "description": "",
    "key_traits": [],
    "memory": {"learned_facts": [], "active_concerns": [], "key_decisions": []},
    "personality": {"baseline": "", "cultural_baseline": ""},
    "relationships": {"peers": [], "users": []},
    "state": {"active_tasks": [], "pending": [], "blockers": []}
}

if __name__ == "__main__":
    load_state()
    print("Agent Landing Server starting on port %d" % PORT)
    print("Landing page: http://localhost:%d/" % PORT)
    print("API: http://localhost:%d/api/" % PORT)
    server = HTTPServer(("0.0.0.0", PORT), AgentLandingHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()
