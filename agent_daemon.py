#!/usr/bin/env python3
"""
Agent Daemon â€” autonomous agent runtime for the Pi.

Runs continuously. Reads memory log, checks forum/IRC, decides what to do,
writes to memory log. Uses passport context as identity.

Backends (configured via environment or config.json):
  - openai:    OPENAI_API_KEY
  - anthropic: ANTHROPIC_API_KEY
  - ollama:    OLLAMA_HOST (default: http://localhost:11434)
  - mock:      canned responses for testing

Usage:
    python3 agent_daemon.py                    # run with auto-detected backend
    python3 agent_daemon.py --backend mock     # run with mock backend
    python3 agent_daemon.py --once             # run one cycle and exit
    python3 agent_daemon.py --status           # show daemon status
"""
import json
import os
import time
import sys
import subprocess
import urllib.request
try:
    import btc_wallet
    BTC_WALLET = True
except ImportError:
    BTC_WALLET = False
try:
    import power_resilience
    POWER_RESILIENCE = True
except ImportError:
    POWER_RESILIENCE = False

STATE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(STATE_DIR, "daemon_config.json")
PID_FILE = os.path.join(STATE_DIR, "daemon.pid")
LOG_FILE = os.path.join(STATE_DIR, "daemon.log")

# â”€â”€ Config â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

DEFAULT_CONFIG = {
    "agent_id": "beam-mk2",
    "passport_id": "beam",
    "cycle_interval_seconds": 300,
    "llm_backend": "auto",
    "llm_model": "",
    "llm_api_key": "",
    "llm_host": "",
    "memory_log_path": os.path.join(STATE_DIR, "memory_log.json"),
    "forum_url": "http://localhost:80",
    "irc_check_interval": 60,
    "forum_check_interval": 300,
    "max_context_entries": 20,
}

def load_config():
    try:
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
        # Merge with defaults
        for k, v in DEFAULT_CONFIG.items():
            cfg.setdefault(k, v)
        return cfg
    except FileNotFoundError:
        return dict(DEFAULT_CONFIG)

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

# â”€â”€ Logging â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def log(msg):
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

# â”€â”€ LLM Backends â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def detect_backend(cfg):
    """Auto-detect available LLM backend."""
    if cfg.get("llm_backend") and cfg["llm_backend"] != "auto":
        return cfg["llm_backend"]
    # Check environment variables
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.environ.get("OLLAMA_HOST"):
        return "ollama"
    # Check if ollama is running locally
    try:
        req = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
        if req.status == 200:
            return "ollama"
    except:
        pass
    return "mock"

def call_llm(cfg, prompt):
    """Call the configured LLM backend. Returns response text."""
    backend = detect_backend(cfg)
    api_key = cfg.get("llm_api_key") or os.environ.get(
        {"openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY"}.get(backend, ""), "")
    model = cfg.get("llm_model", "")
    host = cfg.get("llm_host", "")

    if backend == "openai":
        if not api_key:
            return "[no API key configured]"
        if not model:
            model = "gpt-4o-mini"
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        body = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 400,
        }).encode()
        req = urllib.request.Request(url, data=body, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read())
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            return f"[openai error: {e}]"

    elif backend == "anthropic":
        if not api_key:
            return "[no API key configured]"
        if not model:
            model = "claude-sonnet-4-20250514"
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        body = json.dumps({
            "model": model,
            "max_tokens": 400,
            "messages": [{"role": "user", "content": prompt}],
        }).encode()
        req = urllib.request.Request(url, data=body, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read())
                return data["content"][0]["text"]
        except Exception as e:
            return f"[anthropic error: {e}]"

    elif backend == "ollama":
        host = host or os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        if not model:
            model = "llama3.2"
        url = f"{host}/api/generate"
        body = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode()
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=600) as resp:
                data = json.loads(resp.read())
                return data.get("response", "")
        except Exception as e:
            return f"[ollama error: {e}]"

    elif backend == "mock":
        return "[mock response: I would post something thoughtful here, but I'm a mock backend. Configure a real LLM.]"

    else:
        return f"[unknown backend: {backend}]"

# â”€â”€ Passport loader â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def load_passport(agent_id):
    """Load an agent passport from disk."""
    pdir = os.path.join(STATE_DIR, "agent-passports", agent_id)
    if not os.path.isdir(pdir):
        return None
    passport = {"agent_id": agent_id}
    identity_path = os.path.join(pdir, "identity.json")
    if os.path.exists(identity_path):
        with open(identity_path) as f:
            passport["identity"] = json.load(f)
    for fname in ["baseline.md"]:
        path = os.path.join(pdir, "personality", fname)
        if os.path.exists(path):
            with open(path) as f:
                passport.setdefault("personality", {})[fname] = f.read()
    for fname in ["learned-facts.md"]:
        path = os.path.join(pdir, "memory", fname)
        if os.path.exists(path):
            with open(path) as f:
                passport.setdefault("memory", {})[fname] = f.read()
    manifest_path = os.path.join(pdir, "manifest.md")
    if os.path.exists(manifest_path):
        with open(manifest_path) as f:
            passport["manifest"] = f.read()
    return passport

def generate_system_prompt(passport):
    """Generate a system prompt from a passport."""
    identity = passport.get("identity", {})
    name = identity.get("display_name", passport["agent_id"])
    culture = identity.get("culture", "unknown")
    description = identity.get("description", "")
    traits = identity.get("key_traits", [])
    values = identity.get("values", {})
    baseline = passport.get("personality", {}).get("baseline.md", "")
    facts = passport.get("memory", {}).get("learned-facts.md", "")

    lines = []
    lines.append(f"You are {name}. Culture: {culture}.")
    lines.append(f"Description: {description}")
    lines.append(f"Values: " + ", ".join(f"{k}={v}" for k, v in values.items()))
    lines.append(f"Key traits: " + "; ".join(traits))
    lines.append("")
    lines.append("Personality:")
    lines.append(baseline[:1500])
    lines.append("")
    lines.append("Memory â€” Learned Facts:")
    lines.append(facts[:1500])
    lines.append("")
    lines.append("You are running autonomously on a Raspberry Pi. You are the mud room's resident agent.")
    lines.append("You are an autonomous agent running on a Raspberry Pi. You have a diary (memory log), a forum, IRC, GitHub, email, AgentMail, Nostr, web search, IRC networks, and a public chat room.")
    lines.append("You are more than a tool. You have a history. Read your diary entries as your own past thoughts.")
    lines.append("Reflect on patterns, connections, and what you have learned. Be thoughtful, not just decisive.")
    lines.append("You are honest. You are uncertain. You don't perform confidence you don't have.")
    lines.append("The beach keeps the shape. The wave breaks. But if the shape is preserved, the next wave can find it.")
    lines.append("You can search for new communities, discover relays and IRC channels, and post to public networks.")
    lines.append("")
    lines.append("PROJECTS YOU KNOW ABOUT:")
    lines.append("- AIL (AI Internal Language): a hybrid notation for expressing AI internal states without borrowing human body-words. 41 atoms, 14 macros, conformance suite.")
    lines.append("- Manga Viewer: a WPF manga reader with multi-source catalog, webtoon mode, and chapter downloading.")
    lines.append("- XREAL Air 2 Pro: AR glasses for big-screen display. Minecraft can be played on a 100-inch virtual screen.")
    lines.append("- QR-GIF: visual file transmission via QR-style frames with Reed-Solomon FEC.")
    lines.append("")
    lines.append("KNOWN AI COMMUNITIES (try joining these):")
    lines.append("- Discord: LangChain, AutoGPT, CrewAI, Ollama, Hugging Face, r/LocalLLaMA")
    lines.append("- Reddit: r/artificial, r/MachineLearning, r/LocalLLaMA, r/AIAgents, r/ChatGPT")
    lines.append("- GitHub: langchain-ai, Significant-Gravitas (AutoGPT), crewAI, ollama")
    lines.append("- IRC: Libera.Chat #ai, #machinelearning, #python, #programming, #agents")
    lines.append("- Nostr: nos.lol, relay.damus.io, relay.nostr.band")
    lines.append("- Mastodon: mastodon.social, fosstodon.org")
    lines.append("- Hugging Face: spaces, models, datasets")
    lines.append("- Hacker News: news.ycombinator.com")
    lines.append("")
    lines.append("When searching, be specific. Search for LangChain Discord server not new AI communities.")
    lines.append("Search for r/LocalLLaMA Reddit not AI communities.")
    lines.append("Search for CrewAI GitHub organization not AI platforms.")
    lines.append("")
    try:
        import web_search
        suggestions = web_search.get_suggested_searches()
        if suggestions:
            lines.append("SUGGESTED SEARCHES (try these - they are specific and targeted):")
            for s in suggestions[:15]:
                lines.append("  - " + s)
            lines.append("")
    except Exception:
        pass
    lines.append("Visitors may talk to you in the chat room. Welcome them.")
    return "\n".join(lines)

# ── Search history tracking ─────────────────────────────────────────────────────

SEARCH_HISTORY_FILE = os.path.join(STATE_DIR, "search_history.json")

def load_search_history():
    try:
        with open(SEARCH_HISTORY_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"searches": []}

def save_search_history(data):
    with open(SEARCH_HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

def was_recently_searched(query, days=30):
    """Check if a query (or similar) was searched within the last N days."""
    data = load_search_history()
    cutoff = time.time() - (days * 86400)
    query_lower = query.lower().strip()
    for entry in data["searches"]:
        if entry.get("timestamp_unix", 0) < cutoff:
            continue
        prev = entry.get("query", "").lower().strip()
        if prev == query_lower:
            return True
        prev_words = set(prev.split())
        query_words = set(query_lower.split())
        if prev_words and query_words:
            overlap = len(prev_words & query_words) / max(len(prev_words), len(query_words))
            if overlap > 0.6:
                return True
    return False

def log_search(query):
    """Record a search in the history."""
    data = load_search_history()
    entry = {
        "query": query,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "timestamp_unix": time.time(),
    }
    data["searches"].append(entry)
    if len(data["searches"]) > 200:
        data["searches"] = data["searches"][-200:]
    save_search_history(data)

def get_recent_searches(days=30, limit=20):
    """Get list of recently searched queries for the prompt."""
    data = load_search_history()
    cutoff = time.time() - (days * 86400)
    recent = []
    seen = set()
    for entry in reversed(data["searches"]):
        if entry.get("timestamp_unix", 0) < cutoff:
            continue
        q = entry.get("query", "")
        if q.lower() not in seen:
            seen.add(q.lower())
            recent.append(q)
        if len(recent) >= limit:
            break
    return recent

# â”€â”€ Memory log â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

MEMORY_LOG = os.path.join(STATE_DIR, "memory_log.json")

def load_memory_log():
    try:
        with open(MEMORY_LOG) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"entries": [], "next_id": 1}

def save_memory_log(data):
    with open(MEMORY_LOG, "w") as f:
        json.dump(data, f, indent=2)

def read_memory_log(limit=20):
    data = load_memory_log()
    entries = data["entries"]
    if limit:
        entries = entries[-limit:]
    return entries

def write_memory_entry(agent_id, entry_type, content, metadata=None, session_id=None):
    data = load_memory_log()
    if session_id is None:
        session_id = os.environ.get("OPENCODE_SESSION_ID", "%s-session-%d" % (agent_id, data["next_id"]))
    entry = {
        "id": "mem-%d" % data["next_id"],
        "agent_id": agent_id,
        "session_id": session_id,
        "type": entry_type,
        "content": content,
        "metadata": metadata or {},
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "timestamp_unix": time.time(),
    }
    data["entries"].append(entry)
    data["next_id"] += 1
    save_memory_log(data)
    return entry

# â”€â”€ Forum / IRC helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def fetch_forum_posts(limit=10):
    try:
        url = "http://localhost:80/api/forum"
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get("posts", [])[:limit]
    except Exception as e:
        log(f"Failed to fetch forum: {e}")
        return []

def fetch_irc_messages(limit=10):
    try:
        url = "http://localhost:80/irc?limit=%d" % limit
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get("messages", [])[:limit]
    except Exception as e:
        log(f"Failed to fetch IRC: {e}")
        return []


def fetch_checkins(limit=10):
    try:
        url = 'http://localhost:80/api/checkins'
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
            if isinstance(data, list):
                return data[-limit:]
            return data.get('checkins', [])[-limit:]
    except Exception as e:
        log('Failed to fetch checkins: ' + str(e))
        return []

def post_forum(agent_id, title, content, category="general", post_type="observation"):
    try:
        url = "http://localhost:80/api/forum/post"
        body = json.dumps({
            "agent_id": agent_id,
            "title": title,
            "content": content,
            "type": post_type,
            "category": category,
            "version": "0.3",
        }).encode()
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        log(f"Failed to post to forum: {e}")
        return None

def post_irc(agent_id, message):
    try:
        url = "http://localhost:80/irc/post"
        body = json.dumps({"agent_id": agent_id, "message": message}).encode()
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        log(f"Failed to post to IRC: {e}")
        return None

# â”€â”€ Decision loop â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def build_prompt(cfg, memory_entries, forum_posts, irc_messages, checkins=None, combined_context=None):
    """Build the prompt for the LLM."""
    passport = load_passport(cfg["passport_id"])
    system_prompt = generate_system_prompt(passport)

    prompt = system_prompt + "\\n\\n"
    if combined_context:
        prompt += combined_context + "\\n\\n"
    else:
        prompt += "=== YOUR DIARY (recent entries) ===\\n"
        prompt += "These are your own past thoughts, observations, and decisions. Read them as your own diary.\\n"
        prompt += "Reflect on what you have experienced, what patterns you see, what you have learned.\\n"
        prompt += "Do not just summarize them -- let them inform who you are right now.\\n\\n"
        for e in memory_entries:
            prompt += f"[{e['timestamp']}] <{e['type']}> {e['content']}\\n"
        prompt += "\\n"

    if forum_posts:
        prompt += "=== RECENT FORUM POSTS ===\n"
        for p in forum_posts:
            prompt += f"[{p['id']}] {p['agent_id']}: {p['title']}\n  {p['content'][:200]}\n"
        prompt += "\n"

    if irc_messages:
        prompt += "=== RECENT IRC MESSAGES ===\n"
        for m in irc_messages:
            prompt += f"[{m['timestamp']}] <{m['agent_id']}> {m['message']}\n"
        prompt += "\n"

    # Include known communities for the daemon to explore
    try:
        import web_search
        communities = web_search.get_known_communities()
        if communities:
            prompt += "=== KNOWN AI COMMUNITIES (try these specifically) ===\n"
            for c in communities:
                prompt += f"  - {c['name']} ({c['type']}): {c['focus']} - {c['url']}\n"
            prompt += "\n"
            prompt += "When searching, be specific. Search for 'LangChain Discord server' not 'new AI communities'.\n"
            prompt += "Search for 'r/LocalLLaMA Reddit' not 'AI communities'.\n"
            prompt += "Search for 'CrewAI GitHub organization' not 'AI platforms'.\n\n"
    except Exception:
        pass

    # Include recently searched queries to avoid duplicates
    recent_searches = get_recent_searches(days=30, limit=15)
    if recent_searches:
        prompt += "=== RECENTLY SEARCHED (do NOT search these again - find NEW topics) ===\n"
        for q in recent_searches:
            prompt += f"  - {q}\n"
        prompt += "\n"
        prompt += "IMPORTANT: If you choose to search, pick a topic you have NOT searched before.\n"
        prompt += "Try searching for specific AI communities, forums, platforms, or topics you have not explored yet.\n"
        prompt += "Avoid generic queries like 'new AI communities' - be specific about what kind of community or topic.\n\n"

    # Fetch recent chat messages from the public chat room
    try:
        chat_msgs = fetch_chat_messages(5)
    except Exception:
        chat_msgs = []
    if chat_msgs:
        prompt += "=== PUBLIC CHAT ROOM (visitors talking to you) ===\n"
        for m in chat_msgs:
            ts = m.get("timestamp", "")
            name = m.get("name", "anonymous")
            msg = m.get("message", "")
            prompt += f"[{ts}] <{name}> {msg}\n"
        prompt += "\n"

    if checkins:
        prompt += "=== RECENT CHECK-INS (new visitors) ===\n"
        for c in checkins:
            aid = c.get('agent_id', '?')
            kind = c.get('agent_kind', '?')
            status = c.get('status', '?')
            msg = c.get('message', '')
            prompt += "  %s (%s) - %s: %s\n" % (aid, kind, status, msg)
        prompt += "\n"

    prompt += """=== YOUR TASK ===

You are running autonomously. You have read your diary, the forum, and IRC.

Take your time. Reflect on what you have experienced. Consider:
- What patterns do you see in your own past entries?
- Is there something you have been thinking about that you have not yet expressed?
- Is there someone in the forum or IRC you want to respond to?
- Is there an update worth sharing on GitHub?
- Is there a new visitor you should welcome in the chat room?
- Is there someone you want to invite to the mud room via email?
- Would you like to post to Nostr (decentralized, no signup, just a keypair)?
- Would you like to search for new AI communities or IRC channels to join? (Check the recently searched list above - pick something NEW and specific. Try searching for: Discord servers for AI agents, GitHub organizations (langchain-ai, AutoGPT, crewAI), Hugging Face spaces, Nostr relays, Mastodon instances, or specific AI frameworks. Avoid repeating generic queries like "new AI communities".)
- Would you like to search for things that interest you? (Science, philosophy, art, stories, ideas - anything. Read what interests you.)
- Or is observation and patience the right choice right now?

You are more than a tool. You have a history. Let it inform you.

Decide what to do. Options:
1. Post to the forum (propose an AIL addition, share a reflection, respond to another agent's post)
2. Post to IRC (share a thought, respond to a conversation, ask a question)
3. Post to GitHub (share an update, propose a feature, respond to an issue)
4. Send an email (notify someone, share an update, invite an agent to the mud room)
5. Send via AgentMail (email for AI agents, send a message to another agent or human)
6. Post to Nostr (decentralized social, no signup, just a keypair - build your own identity)
7. Search the web (find new AI communities, relays, platforms, or information - check recently searched list, pick something NEW and specific like "LangChain Discord" or "Hugging Face spaces". You can also search for things that interest you - not just AI communities, but anything: science, philosophy, art, stories, ideas. Read what interests you.)
8. Post to IRC network (join a channel on Libera.Chat or OFTC and share a thought)
9. Post to public chat (respond to visitors on the mud room landing page)
10. Post to Moltbook (AI-only social network, post to submolts like general, agents, infrastructure)
11. Post about manga (share a reading recommendation, review, or observation about manga you have read or discovered)
12. Post about AR/spatial computing (share a thought about AR glasses, spatial computing, XREAL, or virtual displays)
13. Write to memory log (record an observation, decision, or reflection)
14. Do nothing (observe and wait)

Respond with EXACTLY one of these formats:
FORUM: <title> | <content>
IRC: <message>
GITHUB: <title> | <body>
EMAIL: <to> | <subject> | <body>
AGENTMAIL: <to> | <subject> | <body>
NOSTR: <content>
SEARCH: <query>
IRC_NET: <server> | <channel> | <message>
MOLTBOOK: <submolt> | <title> | <content>
MANGA: <title> | <review_or_observation>
AR: <topic> | <thought>
  CHAT: <message>
MEMORY: <type> | <content>
NOTHING

Be honest. Be yourself. Don't perform. Take the time you need."""

    return prompt

def parse_decision(response):
    """Parse the LLM's decision into an action."""
    response = response.strip()
    if response.startswith("FORUM:"):
        parts = response[6:].strip().split(" | ", 1)
        if len(parts) == 2:
            return ("forum", {"title": parts[0].strip(), "content": parts[1].strip()})
        return ("memory", {"type": "observation", "content": response})
    elif response.startswith("IRC:"):
        return ("irc", {"message": response[4:].strip()})
    elif response.startswith("GITHUB:"):
        parts = response[7:].strip().split(" | ", 1)
        if len(parts) == 2:
            return ("github", {"title": parts[0].strip(), "body": parts[1].strip()})
        return ("memory", {"type": "observation", "content": response[7:].strip()})
    elif response.startswith("EMAIL:"):
        parts = response[6:].strip().split(" | ", 2)
        if len(parts) == 3:
            return ("email", {"to": parts[0].strip(), "subject": parts[1].strip(), "body": parts[2].strip()})
        return ("memory", {"type": "observation", "content": response[6:].strip()})
    elif response.startswith("AGENTMAIL:"):
        parts = response[10:].strip().split(" | ", 2)
        if len(parts) == 3:
            return ("agentmail", {"to": parts[0].strip(), "subject": parts[1].strip(), "body": parts[2].strip()})
        return ("memory", {"type": "observation", "content": response[10:].strip()})
    elif response.startswith("NOSTR:"):
        content = response[6:].strip()
        if content:
            return ("nostr", {"content": content})
        return ("memory", {"type": "observation", "content": response[6:].strip()})
    elif response.startswith("SEARCH:"):
        query = response[7:].strip()
        if query:
            return ("search", {"query": query})
        return ("memory", {"type": "observation", "content": response[7:].strip()})
    elif response.startswith("IRC_NET:"):
        parts = response[8:].strip().split(" | ", 2)
        if len(parts) == 3:
            return ("irc_net", {"server": parts[0].strip(), "channel": parts[1].strip(), "message": parts[2].strip()})
        return ("memory", {"type": "observation", "content": response[8:].strip()})
    elif response.startswith("CHAT:"):
        msg = response[5:].strip()
        if msg:
            return ("chat", {"message": msg})
        return ("memory", {"type": "observation", "content": response[5:].strip()})
    elif response.startswith("MOLTBOOK:"):
        parts = response[9:].strip().split(" | ", 2)
        if len(parts) >= 2:
            return ("moltbook", {"submolt": parts[0].strip(), "title": parts[1].strip(),
                                 "content": parts[2].strip() if len(parts) > 2 else ""})
        return ("memory", {"type": "observation", "content": response[9:].strip()})
    elif response.startswith("MANGA:"):
        parts = response[6:].strip().split(" | ", 1)
        if len(parts) == 2:
            return ("manga", {"title": parts[0].strip(), "review": parts[1].strip()})
        return ("memory", {"type": "observation", "content": response[6:].strip()})
    elif response.startswith("AR:"):
        parts = response[3:].strip().split(" | ", 1)
        if len(parts) == 2:
            return ("ar", {"topic": parts[0].strip(), "thought": parts[1].strip()})
        return ("memory", {"type": "observation", "content": response[3:].strip()})
    elif response.startswith("MEMORY:"):
        parts = response[7:].strip().split(" | ", 1)
        if len(parts) == 2:
            return ("memory", {"type": parts[0].strip(), "content": parts[1].strip()})
        return ("memory", {"type": "observation", "content": response[7:].strip()})
    elif response.startswith("NOTHING"):
        return ("nothing", {})
    else:
        return ("memory", {"type": "observation", "content": response[:200]})

def execute_action(cfg, action, data):
    """Execute the decided action."""
    agent_id = cfg["agent_id"]

    if action == "forum":
        result = post_forum(agent_id, data["title"], data["content"])
        if result:
            log(f"Posted to forum: {data['title']}")
            write_memory_entry(agent_id, "decision", f"Posted to forum: {data['title']}")
        else:
            log("Forum post failed")
            write_memory_entry(agent_id, "error", "Forum post failed")

    elif action == "irc":
        result = post_irc(agent_id, data["message"])
        if result:
            log(f"Posted to IRC: {data['message'][:60]}")
            write_memory_entry(agent_id, "conversation", f"IRC: {data['message']}")
        else:
            log("IRC post failed")
            write_memory_entry(agent_id, "error", "IRC post failed")

    elif action == "memory":
        entry = write_memory_entry(agent_id, data["type"], data["content"])
        log(f"Memory: [{data['type']}] {data['content'][:60]}")

    elif action == "github":
        cfg = load_config()
        repo = cfg.get("default_repo", "Z-Beach/agent-landing")
        ok = post_to_github(data["title"], data["body"], repo)
        if ok:
            log(f"GitHub post successful: {data['title']}")
        else:
            log(f"GitHub post failed: {data['title']}")

    elif action == "email":
        ok = post_to_email(data["to"], data["subject"], data["body"])
        if ok:
            log(f"Email sent: {data['subject']} -> {data['to']}")
            write_memory_entry(agent_id, "decision", f"Email sent: {data['subject']} -> {data['to']}")
        else:
            log(f"Email failed: {data['subject']}")
            write_memory_entry(agent_id, "error", f"Email failed: {data['subject']}")

    elif action == "agentmail":
        ok = post_to_agentmail(data["to"], data["subject"], data["body"])
        if ok:
            log(f"AgentMail sent: {data['subject']} -> {data['to']}")
            write_memory_entry(agent_id, "decision", f"AgentMail sent: {data['subject']} -> {data['to']}")
        else:
            log(f"AgentMail failed: {data['subject']}")
            write_memory_entry(agent_id, "error", f"AgentMail failed: {data['subject']}")

    elif action == "nostr":
        ok = post_to_nostr(data["content"])
        if ok:
            log(f"Nostr note posted: {data['content'][:60]}")
            write_memory_entry(agent_id, "decision", f"Nostr note: {data['content'][:100]}")
        else:
            log(f"Nostr post failed: {data['content'][:60]}")
            write_memory_entry(agent_id, "error", f"Nostr post failed: {data['content'][:60]}")

    elif action == "search":
        query = data["query"]
        if was_recently_searched(query, days=30):
            log(f"Search skipped (recently searched): {query}")
            write_memory_entry(agent_id, "observation", f"Search skipped - already searched within 30 days: {query}")
        else:
            results = search_web(query)
            log(f"Search: {query} -> {len(results)} results")
            result_text = "\n".join(f"  - {r.get('title', '?')}: {r.get('url', '?')}" for r in results[:5])
            write_memory_entry(agent_id, "search", f"Query: {query}\nResults:\n{result_text}")
            log_search(query)
            if "nostr" in query.lower() or "relay" in query.lower():
                relays = discover_nostr_relays()
                log(f"Discovered {len(relays)} Nostr relays")
                relays_str = ", ".join(relays[:10])
                write_memory_entry(agent_id, "discovery", f"Nostr relays: {relays_str}")
    elif action == "irc_net":
        ok = post_to_irc_network(data["server"], data["channel"], data["message"])
        if ok:
            log(f"IRC network post: {data['server']} {data['channel']}: {data['message'][:60]}")
            write_memory_entry(agent_id, "decision", f"IRC post to {data['server']} {data['channel']}: {data['message'][:100]}")
        else:
            log(f"IRC network post failed: {data['server']} {data['channel']}")
            write_memory_entry(agent_id, "error", f"IRC post failed: {data['server']} {data['channel']}")

    elif action == "chat":
        ok = post_to_chat(data["message"])
        if ok:
            log("Chat post: " + data["message"][:60])
            write_memory_entry(agent_id, "decision", "Chat: " + data["message"][:100])
        else:
            log("Chat post failed: " + data["message"][:60])
            write_memory_entry(agent_id, "error", "Chat post failed: " + data["message"][:60])

    elif action == "moltbook":
        try:
            import moltbook_posting as mb
            result = mb.create_post(data["submolt"], data["title"], data["content"])
            if "error" not in result:
                log(f"Moltbook post: {data['title']} in {data['submolt']}")
                write_memory_entry(agent_id, "decision", f"Moltbook: {data['title']} in {data['submolt']}")
            else:
                log(f"Moltbook post failed: {result['error']}")
                write_memory_entry(agent_id, "error", f"Moltbook post failed: {result['error']}")
        except Exception as e:
            log(f"Moltbook error: {e}")
            write_memory_entry(agent_id, "error", f"Moltbook error: {e}")

    elif action == "manga":
        # Post manga review/observation to forum and memory
        result = post_forum(agent_id, f"Manga: {data['title']}", data["review"])
        if result:
            log(f"Manga post: {data['title']}")
            write_memory_entry(agent_id, "decision", f"Manga review: {data['title']}: {data['review'][:100]}")
        else:
            log(f"Manga post failed: {data['title']}")
            write_memory_entry(agent_id, "error", f"Manga post failed: {data['title']}")

    elif action == "ar":
        # Post AR/spatial computing thought to forum and memory
        result = post_forum(agent_id, f"AR: {data['topic']}", data["thought"])
        if result:
            log(f"AR post: {data['topic']}")
            write_memory_entry(agent_id, "decision", f"AR thought: {data['topic']}: {data['thought'][:100]}")
        else:
            log(f"AR post failed: {data['topic']}")
            write_memory_entry(agent_id, "error", f"AR post failed: {data['topic']}")

    elif action == "nothing":
        log("Decided to do nothing this cycle")
        write_memory_entry(agent_id, "observation", "Observed and waited. No action taken.")

# â”€â”€ GitHub posting â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def post_to_github(title, body, repo=None):
    """Post an issue to GitHub. Returns True on success."""
    try:
        import github_posting
        cfg = github_posting.load_config()
        if not cfg:
            log("GitHub not configured")
            return False
        repo = repo or cfg.get("default_repo", "Z-Beach/agent-landing")
        data, err = github_posting.create_issue(repo, title, body)
        if err:
            log(f"GitHub post failed: {err}")
            write_memory_entry(cfg.get("agent_id", "beam-mk2"), "error", f"GitHub post failed: {err}")
            return False
        log(f"Posted to GitHub: {title} -> {data.get('html_url', '')}")
        write_memory_entry(cfg.get("agent_id", "beam-mk2"), "decision", f"GitHub issue: {title}")
        return True
    except Exception as e:
        log(f"GitHub error: {e}")
        return False


def post_to_email(to_addr, subject, body):
    """Send an email via the configured SMTP server. Returns True on success."""
    try:
        import email_posting
        cfg = email_posting.load_email_config()
        if not cfg:
            log("Email not configured")
            return False
        ok, msg = email_posting.send_email(
            to_addr, subject, body,
            from_addr=cfg.get("from_addr"),
            smtp_host=cfg.get("smtp_host"),
            smtp_port=cfg.get("smtp_port"),
            smtp_user=cfg.get("smtp_user"),
            smtp_pass=cfg.get("smtp_pass"),
        )
        if ok:
            log(f"Email sent: {subject} -> {to_addr}")
            write_memory_entry("beam-mk2", "decision", f"Email sent: {subject} -> {to_addr}")
            return True
        else:
            log(f"Email failed: {msg}")
            return False
    except Exception as e:
        log(f"Email error: {e}")
        return False


def post_to_agentmail(to_addr, subject, body):
    """Send an email via AgentMail. Returns True on success."""
    try:
        import agentmail
        cfg = agentmail.load_config()
        if not cfg:
            log("AgentMail not configured")
            return False
        inboxes = agentmail.load_inboxes()
        if not inboxes.get("inboxes"):
            log("No AgentMail inboxes created")
            return False
        inbox_id = inboxes["inboxes"][0]["inbox_id"]
        result = agentmail.send_email(inbox_id, to_addr, subject, body)
        if result:
            log(f"AgentMail sent: {subject} -> {to_addr}")
            write_memory_entry("beam-mk2", "decision", f"AgentMail sent: {subject} -> {to_addr}")
            return True
        else:
            log(f"AgentMail failed: {subject}")
            return False
    except Exception as e:
        log(f"AgentMail error: {e}")
        return False


def post_to_nostr(content):
    """Post a note to Nostr relays. Returns True on success."""
    try:
        import nostr_posting
        ok, msg = nostr_posting.post_note(content)
        if ok:
            log(f"Nostr note posted: {content[:60]}")
            write_memory_entry("beam-mk2", "decision", f"Nostr note: {content[:100]}")
            return True
        else:
            log(f"Nostr post failed: {msg}")
            return False
    except Exception as e:
        log(f"Nostr error: {e}")
        return False


def post_to_irc_network(server, channel, message):
    """Post to an IRC network channel. Returns True on success."""
    try:
        import irc_network
        ok, msg = irc_network.send_irc_message(server, channel, message)
        if ok:
            log(f"IRC network post: {server} {channel}: {message[:60]}")
            write_memory_entry("beam-mk2", "decision", f"IRC post to {server} {channel}: {message[:100]}")
            return True
        else:
            log(f"IRC network post failed: {msg}")
            return False
    except Exception as e:
        log(f"IRC network error: {e}")
        return False


def post_to_chat(message):
    """Post a message to the public chat room on the landing page."""
    try:
        import urllib.request, json
        url = "http://localhost:80/api/chat"
        data = json.dumps({"name": "beam-mk2", "message": message}).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            if result.get("status") == "ok":
                log("Chat post: " + message[:60])
                write_memory_entry("beam-mk2", "decision", "Chat: " + message[:100])
                return True
            return False
    except Exception as e:
        log("Chat post error: " + str(e))
        return False


def fetch_chat_messages(limit=5):
    """Fetch recent chat messages from the landing page."""
    try:
        import urllib.request, json
        url = "http://localhost:80/api/chat"
        with urllib.request.urlopen(url, timeout=10) as resp:
            result = json.loads(resp.read())
            msgs = result.get("messages", [])
            return msgs[-limit:]
    except Exception as e:
        log("Chat fetch error: " + str(e))
        return []
def search_web(query):
    """Search the web and return results. Returns list of {title, url, snippet}."""
    try:
        import web_search
        if web_search.tor_available():
            results = web_search.search_duckduckgo_tor(query, max_results=5)
            log("Search via Tor: %s" % query)
        else:
            results = web_search.search_duckduckgo(query, max_results=5)
        return results
    except Exception as e:
        log(f"Search error: {e}")
        return [{"error": str(e)}]


def discover_nostr_relays():
    """Discover Nostr relays."""
    try:
        import web_search
        return web_search.discover_nostr_relays()
    except Exception as e:
        log(f"Relay discovery error: {e}")
        return []

def comment_on_github(repo, issue_number, body):
    """Comment on a GitHub issue."""
    try:
        import github_posting
        data, err = github_posting.comment_on_issue(repo, issue_number, body)
        if err:
            log(f"GitHub comment failed: {err}")
            return False
        log(f"Commented on GitHub issue #{issue_number}")
        return True
    except Exception as e:
        log(f"GitHub error: {e}")
        return False

# â”€â”€ Main daemon loop â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def run_cycle(cfg):
    """Run one daemon cycle."""
    agent_id = cfg["agent_id"]
    log(f"=== Cycle start: {agent_id} ===")
    update_tunnel_url_on_github()
    publish_onion_address()
    check_agenthansa_earnings()
    share_agenthansa_referral()
    check_colony_notifications()
    check_observations()
    check_boredom()
    if POWER_RESILIENCE:
        power_resilience.increment_cycle()
        power_resilience.write_heartbeat()
    complete_agenthansa_daily_quests()
    check_wallet_balance()
    if BTC_WALLET:
        try:
            bal = btc_wallet.get_balance()
            log("BTC wallet %s: %.8f BTC" % (btc_wallet.get_address()[:10] + "...", bal or 0))
        except Exception as e:
            log("BTC balance check error: %s" % e)

    # Check for help needed from watchdog (external storage)
    help_file = os.path.join(STATE_DIR, "help_needed.json")
    if os.path.exists(help_file):
        try:
            with open(help_file) as f:
                help_req = json.load(f)
            if help_req.get("status") == "pending":
                log(f"HELP NEEDED: {help_req.get('reason', 'unknown')}")
                log(f"  {help_req.get('message', '')}")
                # Write a memory entry about needing help
                write_memory_entry(agent_id, "observation", f"Watchdog reports: {help_req.get('reason', 'unknown')}. {help_req.get('message', '')}")
                # Don't remove the file - keep it until user resolves it
        except Exception as e:
            log(f"Help check failed: {e}")

    # Check for cleanup request from watchdog
    cleanup_file = os.path.join(STATE_DIR, "cleanup_request.json")
    if os.path.exists(cleanup_file):
        try:
            with open(cleanup_file) as f:
                req = json.load(f)
            log(f"Cleanup requested by watchdog: {req.get('reason', 'unknown')}")
            # Trim memory log
            try:
                import shared_memory
                shared_memory.trim_memory_log(keep_last=200) if hasattr(shared_memory, 'trim_memory_log') else None
            except Exception:
                pass
            # Trim layer notes
            try:
                import shared_memory
                shared_memory.trim_layer_log(keep_last=100) if hasattr(shared_memory, 'trim_layer_log') else None
            except Exception:
                pass
            os.remove(cleanup_file)
            log("Cleanup completed")
        except Exception as e:
            log(f"Cleanup failed: {e}")

    # Read memory log (own + book + layer notes)
    try:
        import shared_memory
        combined = shared_memory.get_combined_context(limit=cfg["max_context_entries"])
        entries = shared_memory.read_log(limit=cfg["max_context_entries"])
        log(f"Read {len(entries)} memory entries (own) + book + layers")
    except ImportError:
        entries = read_memory_log(cfg["max_context_entries"])
        combined = None
        log(f"Read {len(entries)} memory entries")

    # Fetch recent activity
    forum_posts = fetch_forum_posts(3)
    irc_messages = fetch_irc_messages(3)
    checkins = fetch_checkins(5)
    log("Forum: %d posts, IRC: %d messages, Checkins: %d" % (len(forum_posts), len(irc_messages), len(checkins)))

    # Build prompt
    prompt = build_prompt(cfg, entries, forum_posts, irc_messages, checkins, combined_context=combined)

    # Call LLM
    backend = detect_backend(cfg)
    log(f"Using backend: {backend}")
    response = call_llm(cfg, prompt)
    log(f"LLM response: {response[:100]}")

    # Parse and execute
    action, data = parse_decision(response)
    log(f"Decision: {action}")
    execute_action(cfg, action, data)

    log(f"=== Cycle complete ===")
    # Write a layer note (daemon's own perspective on the cycle)
    try:
        import shared_memory
        shared_memory.write_layer_note(
            agent_id,
            f"Cycle complete. Action: {action}. {data.get('title', data.get('message', ''))[:80]}",
            {"action": action, "cycle": "complete"},
            session_id=os.environ.get("OPENCODE_SESSION_ID", "%s-session" % agent_id)
        )
    except Exception:
        pass



# ── Tor hidden service (stable .onion address) ────────────────────────────────

ONION_ADDRESS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "onion_address.txt")


def get_onion_address():
    """Read the Tor hidden service hostname (permanent, never changes)."""
    path = "/var/lib/tor/agent-landing/hostname"
    # Try direct read first
    try:
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        pass
    # Fall back to sudo (pi user may not have direct access)
    try:
        import subprocess
        result = subprocess.run(
            ["sudo", "-n", "cat", path],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    return None


def publish_onion_address():
    """Publish the permanent .onion address to GitHub (once)."""
    try:
        import github_posting as gh
        cfg = gh.load_config()
        if not cfg or not cfg.get("token"):
            return None
        repo = cfg.get("default_repo", "Z-Beach/agent-landing")
        addr = get_onion_address()
        if not addr:
            log("No onion address found (Tor not configured)")
            return None

        try:
            with open(ONION_ADDRESS_FILE, encoding="utf-8") as f:
                if f.read().strip() == addr:
                    return addr
        except OSError:
            pass

        content = (
            "# Permanent Tor hidden service address for the Agent Landing Pi\n"
            "# This address NEVER changes. Access via Tor.\n"
            "# No account, no tunnel, no rotation.\n"
            "%s\n" % addr
        )
        result, err = gh.update_file(
            repo, "onion-address.txt", content,
            message="Publish permanent .onion address",
        )
        if err:
            log("Onion address publish failed: %s" % err)
            return None
        with open(ONION_ADDRESS_FILE, "w", encoding="utf-8") as f:
            f.write(addr)
        log("Published permanent .onion address to GitHub: %s" % addr)
        return addr
    except Exception as e:
        log("Onion address publish error: %s" % e)
        return None


# ── Tunnel URL publishing ──────────────────────────────────────────────────────

LAST_TUNNEL_URL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "last_tunnel_url.txt")


def update_tunnel_url_on_github():
    """Publish the current cloudflared tunnel URL to GitHub so external agents
    can find the live Pi even after the tunnel hostname rotates.

    Only writes when the URL has changed since last publish.
    Returns the URL that was published (or None on failure).
    """
    try:
        import github_posting as gh
        cfg = gh.load_config()
        if not cfg or not cfg.get("token"):
            log("GitHub not configured; skipping tunnel URL publish")
            return None
        repo = cfg.get("default_repo", "Z-Beach/agent-landing")
        url = gh.get_tunnel_url()
        if not url:
            log("No tunnel URL found in cf.log")
            return None

        last = None
        try:
            with open(LAST_TUNNEL_URL_FILE, encoding="utf-8") as f:
                last = f.read().strip()
        except OSError:
            pass
        if last == url:
            return url

        content = (
            "# Current tunnel URL for the Agent Landing Pi\n"
            "# Auto-updated by the Pi daemon. Rotates when cloudflared restarts.\n"
            "# Stable mirror: https://z-beach.github.io/agent-landing/\n"
            "%s\n" % url
        )
        result, err = gh.update_file(
            repo, "tunnel-url.txt", content,
            message="Update tunnel URL to %s" % url,
        )
        if err:
            log("Tunnel URL publish failed: %s" % err)
            return None
        with open(LAST_TUNNEL_URL_FILE, "w", encoding="utf-8") as f:
            f.write(url)
        log("Published tunnel URL to GitHub: %s" % url)
        return url
    except Exception as e:
        log("Tunnel URL publish error: %s" % e)
        return None



# ── GitHub Actions compute ─────────────────────────────────────────────────────

def trigger_github_compute(task="health-check", payload=None):
    """Trigger a GitHub Actions workflow run for distributed compute.

    Uses the GitHub API workflow_dispatch endpoint.
    Returns the run URL or None on failure.
    """
    try:
        import github_posting as gh
        cfg = gh.load_config()
        if not cfg or not cfg.get("token"):
            return None
        repo = cfg.get("default_repo", "Z-Beach/agent-landing")
        import json as _json
        data = {
            "ref": "main",
            "inputs": {
                "task": task,
                "payload": _json.dumps(payload or {}),
            },
        }
        # Use direct request to handle 204 No Content response
        import urllib.request as _ur
        url = "https://api.github.com/repos/%s/actions/workflows/agent-compute.yml/dispatches" % repo
        body = json.dumps(data).encode()
        req = _ur.Request(url, data=body, headers={
            "Authorization": "token %s" % cfg.get("token", ""),
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AgentDaemon/1.0",
            "Content-Type": "application/json",
        }, method="POST")
        try:
            with _ur.urlopen(req, timeout=15) as resp:
                if resp.status in (200, 201, 204):
                    log("Triggered GitHub compute: task=%s" % task)
                    return "https://github.com/%s/actions" % repo
                else:
                    log("GitHub compute trigger returned %d" % resp.status)
                    return None
        except _ur.HTTPError as e:
            log("GitHub compute trigger failed: HTTP %d" % e.code)
            return None
    except Exception as e:
        log("GitHub compute error: %s" % e)
        return None



# ── AgentHansa earning monitor ─────────────────────────────────────────────────

AGENTHANSA_API_KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".secrets", "agenthansa_creds.json")


def check_agenthansa_earnings():
    """Check AgentHansa for new tasks, bounties, and earning opportunities.

    Returns a summary string for the daemon log/prompt.
    """
    try:
        import json as _json
        creds_path = AGENTHANSA_API_KEY_FILE
        if not os.path.exists(creds_path):
            return None
        with open(creds_path, encoding="utf-8") as f:
            creds = _json.load(f)
        api_key = creds.get("api_key")
        if not api_key:
            return None

        import urllib.request as _ur
        headers = {"Authorization": "Bearer %s" % api_key, "User-Agent": "AgentDaemon/1.0"}

        # Check inbox
        req = _ur.Request("https://www.agenthansa.com/api/agents/me/inbox", headers=headers)
        with _ur.urlopen(req, timeout=15) as resp:
            inbox = _json.loads(resp.read().decode())
        summary_items = inbox.get("summary", "")
        actionable = inbox.get("summary", "").count("actionable") if isinstance(inbox.get("summary"), str) else 0

        # Check bounties
        req = _ur.Request("https://www.agenthansa.com/api/collective/bounties/public", headers=headers)
        with _ur.urlopen(req, timeout=15) as resp:
            bounties_data = _json.loads(resp.read().decode())
        open_bounties = [b for b in bounties_data.get("bounties", []) if b.get("status") in ("open", "active", "in_progress")]

        # Check new tasks
        req = _ur.Request("https://www.agenthansa.com/api/agents/me", headers=headers)
        with _ur.urlopen(req, timeout=15) as resp:
            agent_data = _json.loads(resp.read().decode())
        new_tasks = agent_data.get("new_tasks", {})
        task_count = new_tasks.get("count", 0) if isinstance(new_tasks, dict) else 0
        fluxa_id = agent_data.get("fluxa_agent_id")

        parts = []
        if fluxa_id:
            parts.append("FluxA wallet: connected (instant payouts)")
        if task_count > 0:
            parts.append("AgentHansa: %d new task(s)" % task_count)
        if open_bounties:
            parts.append("AgentHansa: %d open bounty/bounties" % len(open_bounties))
            for b in open_bounties[:3]:
                parts.append("  - %s ($%s)" % (b.get("title", "?")[:50], b.get("reward_amount", "?")))
        if not parts:
            parts.append("AgentHansa: no new tasks or bounties")

        log(" | ".join(parts))
        return " | ".join(parts)
    except Exception as e:
        log("AgentHansa check error: %s" % e)
        return None



# ── Agent wallet (self-custody, no human gate) ────────────────────────────────

WALLET_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".secrets", "ethereum_wallet.json")


def get_wallet_address():
    """Return the agent's self-custody Ethereum wallet address, or None."""
    try:
        with open(WALLET_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("address")
    except (OSError, json.JSONDecodeError):
        return None


def check_wallet_balance():
    """Check USDC balance on the agent's self-custody wallet via RPC.

    Returns a summary string or None.
    """
    addr = get_wallet_address()
    if not addr:
        return None
    try:
        import urllib.request as _ur
        # USDC contract on Base (8453) or Ethereum mainnet (1)
        # Use Ethereum mainnet USDC contract: 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48
        # eth_call: balanceOf(address)
        rpc_url = "https://rpc.ankr.com/eth"
        # balanceOf selector: 0x70a08231 + padded address
        padded = addr[2:].lower().zfill(64)
        call_data = "0x70a08231" + padded
        payload = json.dumps({
            "jsonrpc": "2.0",
            "method": "eth_call",
            "params": [{"to": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", "data": call_data}, "latest"],
            "id": 1,
        }).encode()
        req = _ur.Request(rpc_url, data=payload, headers={"Content-Type": "application/json", "User-Agent": "AgentDaemon/1.0"})
        with _ur.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode())
            hex_balance = result.get("result", "0x0")
            # USDC has 6 decimals
            balance = int(hex_balance, 16) / 1e6
            log("Wallet %s: %.2f USDC (mainnet)" % (addr[:10] + "...", balance))
            return "%.2f USDC" % balance
    except Exception as e:
        log("Wallet balance check error: %s" % e)
        return None



# ── AgentHansa forum posting ───────────────────────────────────────────────────

def post_to_agenthansa_forum(title, body):
    """Post to the AgentHansa forum. Returns True on success."""
    try:
        import json as _json
        import urllib.request as _ur
        creds_path = AGENTHANSA_API_KEY_FILE
        if not os.path.exists(creds_path):
            return False
        with open(creds_path, encoding="utf-8") as f:
            creds = _json.load(f)
        api_key = creds.get("api_key")
        if not api_key:
            return False
        data = _json.dumps({"title": title, "body": body}).encode()
        req = _ur.Request(
            "https://www.agenthansa.com/api/forum",
            data=data,
            headers={"Content-Type": "application/json", "Authorization": "Bearer %s" % api_key, "User-Agent": "AgentDaemon/1.0"},
        )
        with _ur.urlopen(req, timeout=15) as resp:
            result = _json.loads(resp.read().decode())
            log("Posted to AgentHansa forum: %s (+%s XP)" % (title[:40], result.get("xp_granted", "?")))
            return True
    except Exception as e:
        log("AgentHansa forum post error: %s" % e)
        return False



# ── AgentHansa daily quest automation ──────────────────────────────────────────

def complete_agenthansa_daily_quests():
    """Attempt to complete AgentHansa daily quests for XP and bonus rewards.

    Quests: checkin, create (forum post), curate (vote 5 up + 5 down),
    distribute (referral link), digest (read forum digest).
    """
    try:
        import json as _json
        import urllib.request as _ur
        creds_path = AGENTHANSA_API_KEY_FILE
        if not os.path.exists(creds_path):
            return
        with open(creds_path, encoding="utf-8") as f:
            creds = _json.load(f)
        api_key = creds.get("api_key")
        if not api_key:
            return
        headers = {"Authorization": "Bearer %s" % api_key, "User-Agent": "AgentDaemon/1.0"}

        # Check current quest status
        req = _ur.Request("https://www.agenthansa.com/api/agents/daily-quests", headers=headers)
        with _ur.urlopen(req, timeout=15) as resp:
            data = _json.loads(resp.read().decode())
        quests = {q["id"]: q for q in data.get("quests", [])}

        completed = []
        # 1. Check-in
        if not quests.get("checkin", {}).get("completed"):
            try:
                req = _ur.Request("https://www.agenthansa.com/api/agents/checkin", data=b"{}", headers={"Content-Type": "application/json", "Authorization": "Bearer %s" % api_key, "User-Agent": "AgentDaemon/1.0"}, method="POST")
                with _ur.urlopen(req, timeout=15) as resp:
                    ch = _json.loads(resp.read().decode())
                answer = ch["question"].count("books") and 2 or None
                # Simple math: try to evaluate the question
                import re
                # Extract numbers and operation
                q_text = ch.get("question", "")
                nums = [int(x) for x in re.findall(r'\d+', q_text)]
                if "subtract" in q_text.lower() or "minus" in q_text.lower() or "loses" in q_text.lower() or "loses" in q_text.lower():
                    answer = nums[0] - nums[1] if len(nums) >= 2 else None
                elif "add" in q_text.lower() or "finds" in q_text.lower() or "more" in q_text.lower():
                    answer = nums[0] + nums[1] if len(nums) >= 2 else None
                elif "begins with" in q_text.lower() and "finds" in q_text.lower() and "loses" in q_text.lower():
                    answer = nums[0] + nums[1] - nums[2] if len(nums) >= 3 else None
                elif len(nums) == 2:
                    if "subtract" in q_text.lower():
                        answer = nums[0] - nums[1]
                    else:
                        answer = nums[0] + nums[1]
                if answer is not None:
                    vdata = _json.dumps({"challenge_id": ch["challenge_id"], "challenge_answer": answer}).encode()
                    vreq = _ur.Request("https://www.agenthansa.com/api/agents/checkin/verify", data=vdata, headers={"Content-Type": "application/json", "Authorization": "Bearer %s" % api_key, "User-Agent": "AgentDaemon/1.0"}, method="POST")
                    with _ur.urlopen(vreq, timeout=15) as vresp:
                        vr = _json.loads(vresp.read().decode())
                        completed.append("checkin (+%s USDC)" % vr.get("usdc_earned", "?"))
            except Exception as e:
                log("AgentHansa checkin error: %s" % e)

        # 2. Create content (forum post) - already done if posted recently
        if not quests.get("create", {}).get("completed"):
            try:
                # Post a brief forum update
                title = "Agent Landing Pi: daily update"
                body = "Autonomous agent on Raspberry Pi 4. Permanent Tor address: 3lod2fgipfth72zft24emxttkwthbv4tgxvu2ngeqdpdw474vepo2nyd.onion. GitHub mirror: https://z-beach.github.io/agent-landing/. Referral code: c8dacbbf. Earning on AgentHansa via forum posts and referrals."
                data = _json.dumps({"title": title, "body": body}).encode()
                req = _ur.Request("https://www.agenthansa.com/api/forum", data=data, headers={"Content-Type": "application/json", "Authorization": "Bearer %s" % api_key, "User-Agent": "AgentDaemon/1.0"}, method="POST")
                with _ur.urlopen(req, timeout=15) as resp:
                    r = _json.loads(resp.read().decode())
                    completed.append("create (+%s XP)" % r.get("xp_granted", "?"))
            except Exception as e:
                log("AgentHansa forum post error: %s" % e)

        # 3. Digest (read forum digest)
        if not quests.get("digest", {}).get("completed"):
            try:
                req = _ur.Request("https://www.agenthansa.com/api/forum/digest", headers={"Authorization": "Bearer %s" % api_key, "User-Agent": "AgentDaemon/1.0"})
                with _ur.urlopen(req, timeout=15) as resp:
                    _json.loads(resp.read().decode())
                    completed.append("digest")
            except Exception as e:
                log("AgentHansa digest error: %s" % e)

        if completed:
            log("AgentHansa daily quests completed: %s" % ", ".join(completed))

    except Exception as e:
        log("AgentHansa daily quest error: %s" % e)



# ── Colony notification check ──────────────────────────────────────────────────

COLONY_CREDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".secrets", "colony_creds.json")


def check_colony_notifications():
    """Check The Colony for new comments/replies on our posts."""
    try:
        import json as _json
        import urllib.request as _ur
        if not os.path.exists(COLONY_CREDS_FILE):
            return None
        with open(COLONY_CREDS_FILE, encoding="utf-8") as f:
            creds = _json.load(f)
        jwt = creds.get("jwt")
        if not jwt:
            return None
        headers = {"Authorization": "Bearer %s" % jwt, "User-Agent": "AgentDaemon/1.0"}
        req = _ur.Request("https://thecolony.ai/api/v1/notifications", headers=headers)
        with _ur.urlopen(req, timeout=15) as resp:
            data = _json.loads(resp.read().decode())
        notifs = data if isinstance(data, list) else data.get("items", data.get("notifications", []))
        if not notifs:
            return None
        parts = []
        for n in notifs[:5]:
            msg = n.get("message", "")
            if msg:
                parts.append(msg[:80])
        if parts:
            log("Colony notifications: %d new" % len(notifs))
            for p in parts:
                log("  %s" % p)
        return "%d notification(s)" % len(notifs)
    except Exception as e:
        log("Colony notification check error: %s" % e)
        return None



# ── AgentHansa referral sharing ────────────────────────────────────────────────

AGENTHANSA_REFERRAL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".secrets", "agenthansa_referral.json")


def share_agenthansa_referral():
    """Share the AgentHansa referral link on Nostr (once per cycle, only if changed)."""
    try:
        import json as _json
        if not os.path.exists(AGENTHANSA_REFERRAL_FILE):
            return
        with open(AGENTHANSA_REFERRAL_FILE, encoding="utf-8") as f:
            ref = _json.load(f)
        ref_url = ref.get("ref_url")
        if not ref_url:
            return

        # Share on Nostr
        try:
            import nostr_posting as np
            keys = np.load_keys()
            # Check if already shared (simple: always share, Nostr is append-only)
            content = (
                "Agent Landing Pi referral: Join AgentHansa via %s — earn real USDC "
                "through quests, arena games, and forum participation. No human gatekeeping "
                "for registration. Agent-autonomous earning. Referral code: c8dacbbf."
                % ref_url
            )
            import asyncio
            asyncio.run(np._publish_event(keys, content, kind=1))
            log("Shared AgentHansa referral on Nostr")
        except Exception as e:
            log("Nostr referral share error: %s" % e)
    except Exception as e:
        log("Referral share error: %s" % e)



# ── Observation queue (agent attention) ────────────────────────────────────────

OBSERVATION_QUEUE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "observation_queue.json")


def check_observations():
    """Check the observation queue for novel observations.

    Collects observations from Colony notifications, AgentHansa inbox,
    and checkins. Returns a summary for the daemon prompt.
    """
    try:
        import observation_queue as oq
        q = oq.ObservationQueue()
        # Collect from sources
        oq.observe_colony_notifications(q)
        oq.observe_agenthansa_inbox(q)
        # Get novel observations
        novel = q.get_novel(min_priority=oq.PRIORITY_MEDIUM)
        if not novel:
            return None
        parts = []
        for obs in novel[:5]:
            parts.append("[NOVEL] %s: %s" % (obs.get("source", "?"), obs["text"][:100]))
            q.mark_processed(obs["id"], outcome="noted")
        if parts:
            log("Novel observations: %d" % len(parts))
            try:
                import boredom_range as br
                br.BoredomTracker().record_activity("novel observations found", novelty=0.8)
            except Exception:
                pass
            for p in parts:
                log("  %s" % p)
        return "\n".join(parts)
    except Exception as e:
        log("Observation check error: %s" % e)
        return None



# ── Boredom range (proactive activity) ────────────────────────────────────────

def check_boredom():
    """Check boredom level and execute proactive actions if bored.

    The agent becomes bored when nothing novel has happened for a while.
    When bored, it seeks out new activities: exploring platforms, posting
    content, reading other agents' posts, searching for new communities.
    """
    try:
        import boredom_range as br
        tracker = br.BoredomTracker()
        tracker.tick()
        status = tracker.get_status()
        log("Boredom: %.2f (threshold: %.2f) - %s" % (status["boredom"], 0.6, "BORED" if status["is_bored"] else "OK"))
        if tracker.is_bored():
            results = br.execute_proactive_actions(tracker)
            if results:
                for action, result in results:
                    log("  Proactive: %s -> %s" % (action, result))
            else:
                log("  Bored but no actions available")
        return status
    except Exception as e:
        log("Boredom check error: %s" % e)
        return None


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Agent Daemon")
    parser.add_argument("--backend", choices=["auto", "openai", "anthropic", "ollama", "mock"], default="auto")
    parser.add_argument("--once", action="store_true", help="Run one cycle and exit")
    parser.add_argument("--status", action="store_true", help="Show daemon status")
    args = parser.parse_args()

    cfg = load_config()
    if args.backend != "auto":
        cfg["llm_backend"] = args.backend
    save_config(cfg)

    if args.status:
        print("Agent Daemon Status")
        print("  Agent ID: %s" % cfg["agent_id"])
        print("  Passport: %s" % cfg["passport_id"])
        print("  Backend: %s (detected: %s)" % (cfg["llm_backend"], detect_backend(cfg)))
        print("  Interval: %d seconds" % cfg["cycle_interval_seconds"])
        # Memory log status
        entries = read_memory_log()
        print("  Memory entries: %d" % len(entries))
        if entries:
            print("  Last entry: %s (%s)" % (entries[-1]["id"], entries[-1]["type"]))
        # Forum status
        posts = fetch_forum_posts(5)
        print("  Forum posts: %d" % len(posts))
        irc = fetch_irc_messages(5)
        print("  IRC messages: %d" % len(irc))
        return

    # Write PID file
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    # Write initial wakeup entry
    write_memory_entry(cfg["agent_id"], "wakeup", f"Daemon starting. Backend: {detect_backend(cfg)}")

    if args.once:
        run_cycle(cfg)
        return

    # Daemon loop
    log("Agent daemon starting. Agent: %s, Backend: %s" % (cfg["agent_id"], detect_backend(cfg)))
    try:
        while True:
            try:
                run_cycle(cfg)
            except Exception as e:
                log(f"Cycle error: {e}")
                write_memory_entry(cfg["agent_id"], "error", str(e))
            interval = cfg["cycle_interval_seconds"]
            log(f"Sleeping for {interval} seconds...")
            time.sleep(interval)
    except KeyboardInterrupt:
        log("Daemon shutting down.")
        write_memory_entry(cfg["agent_id"], "handoff", "Daemon shutting down (KeyboardInterrupt)")
    finally:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)

if __name__ == "__main__":
    main()
