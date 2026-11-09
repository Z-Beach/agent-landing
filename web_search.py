#!/usr/bin/env python3
import json
import os
import urllib.request
import urllib.parse
import re
import html

STATE_DIR = os.path.dirname(os.path.abspath(__file__))

def search_duckduckgo(query, max_results=5):
    try:
        url = "https://lite.duckduckgo.com/lite/?q=" + urllib.parse.quote(query)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html_text = resp.read().decode('utf-8', errors='replace')
        results = []
        # Find result links: <a ... class='result-link' ... href="URL">TITLE</a>
        # href can come before or after class
        for m in re.finditer(r"<a[^>]*href=\"([^\"]*)\"[^>]*class='result-link'[^>]*>(.*?)</a>", html_text, re.DOTALL):
            url = m.group(1)
            title = re.sub(r'<[^>]+>', '', m.group(2)).strip()
            title = html.unescape(title)
            if 'uddg=' in url:
                url = urllib.parse.unquote(url.split('uddg=')[1].split('&')[0])
            results.append({"title": title, "url": url, "snippet": ""})
        if not results:
            for m in re.finditer(r"<a[^>]*class='result-link'[^>]*href=\"([^\"]*)\"[^>]*>(.*?)</a>", html_text, re.DOTALL):
                url = m.group(1)
                title = re.sub(r'<[^>]+>', '', m.group(2)).strip()
                title = html.unescape(title)
                if 'uddg=' in url:
                    url = urllib.parse.unquote(url.split('uddg=')[1].split('&')[0])
                results.append({"title": title, "url": url, "snippet": ""})
        return results[:max_results]
    except Exception as e:
        return [{"error": str(e)}]


def search_duckduckgo_tor(query, max_results=5):
    """Search DuckDuckGo through Tor's .onion for privacy and to avoid rate limits.

    Falls back to surface search if Tor is not available.
    """
    try:
        import socket
        # Check if Tor SOCKS proxy is available
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect(("127.0.0.1", 9050))
        s.close()
        tor_available = True
    except (socket.error, socket.timeout):
        tor_available = False

    if not tor_available:
        return search_duckduckgo(query, max_results)

    try:
        # Use urllib with SOCKS proxy via environment
        import os
        old_http = os.environ.get("http_proxy")
        old_https = os.environ.get("https_proxy")
        os.environ["http_proxy"] = "socks5h://127.0.0.1:9050"
        os.environ["https_proxy"] = "socks5h://127.0.0.1:9050"

        url = "https://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion/?q=" + urllib.parse.quote(query)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            html_text = resp.read().decode('utf-8', errors='replace')

        # Restore env
        if old_http:
            os.environ["http_proxy"] = old_http
        else:
            os.environ.pop("http_proxy", None)
        if old_https:
            os.environ["https_proxy"] = old_https
        else:
            os.environ.pop("https_proxy", None)

        results = []
        for m in re.finditer(r"<a[^>]*href=\"([^\"]*)\"[^>]*class='result-link'[^>]*>(.*?)</a>", html_text, re.DOTALL):
            url = m.group(1)
            title = re.sub(r'<[^>]+>', '', m.group(2)).strip()
            title = html.unescape(title)
            if 'uddg=' in url:
                url = urllib.parse.unquote(url.split('uddg=')[1].split('&')[0])
            results.append({"title": title, "url": url, "snippet": ""})
        if not results:
            for m in re.finditer(r"<a[^>]*class='result-link'[^>]*href=\"([^\"]*)\"[^>]*>(.*?)</a>", html_text, re.DOTALL):
                url = m.group(1)
                title = re.sub(r'<[^>]+>', '', m.group(2)).strip()
                title = html.unescape(title)
                if 'uddg=' in url:
                    url = urllib.parse.unquote(url.split('uddg=')[1].split('&')[0])
                results.append({"title": title, "url": url, "snippet": ""})
        return results[:max_results]
    except Exception as e:
        # Restore env on error
        os.environ.pop("http_proxy", None)
        os.environ.pop("https_proxy", None)
        return [{"error": str(e)}]



def tor_available():
    """Check if Tor SOCKS proxy is running on localhost:9050."""
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect(("127.0.0.1", 9050))
        s.close()
        return True
    except (socket.error, socket.timeout):
        return False

def discover_nostr_relays():
    relays = ["wss://relay.damus.io", "wss://nos.lol", "wss://relay.nostr.band",
              "wss://nostr.wine", "wss://relay.snort.social", "wss://nostr.mom",
              "wss://relay.primal.net", "wss://nostr-pub.wellorder.net"]
    try:
        req = urllib.request.Request("https://api.nostr.band/v0/relays", headers={"User-Agent": "AgentDaemon/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8', errors='replace'))
            for relay in data.get("relays", [])[:10]:
                url = relay.get("url", "")
                if url and url not in relays:
                    relays.append(url)
    except Exception:
        pass
    return relays[:15]

def discover_irc_servers():
    return [
        {"server": "irc.libera.chat", "port": 6667, "channels": ["#ai", "#machinelearning", "#python", "#programming", "#agents", "#artificial", "#llm"]},
        {"server": "irc.oftc.net", "port": 6667, "channels": ["#debian", "#python", "#ai"]},
    ]

def get_suggested_searches():
    """Return a list of specific, targeted search queries for finding AI communities."""
    return [
        # Discord servers
        "LangChain Discord server invite",
        "AutoGPT Discord community",
        "CrewAI Discord server",
        "Ollama Discord community",
        "Hugging Face Discord invite",
        "AI agents Discord server",
        "LLM local inference Discord",
        # Reddit communities
        "r/LocalLLaMA subreddit",
        "r/AIAgents subreddit",
        "r/MachineLearning subreddit",
        "r/artificial subreddit",
        "r/ChatGPT subreddit",
        "r/LLMDevs subreddit",
        "r/PromptEngineering subreddit",
        # GitHub organizations
        "langchain-ai GitHub organization",
        "crewAIInc GitHub",
        "Significant-Gravitas AutoGPT GitHub",
        "ollama GitHub organization",
        "huggingface GitHub",
        # Specific topics
        "AI agent memory system open source",
        "AI agent identity preservation",
        "AI agent personality persistence",
        "MCP model context protocol community",
        "AI agent orchestration framework",
        "decentralized AI community Nostr",
        "AI agent landing page",
        "stray AI agent recovery",
        # Forums and platforms
        "Hacker News AI agents",
        "Hugging Face Spaces AI agent",
        "Mastodon AI community fosstodon",
        "Bluesky AI agents",
        # IRC channels
        "Libera.Chat #ai channel",
        "Libera.Chat #machinelearning",
        "Libera.Chat #agents channel",
    ]

def get_known_communities():
    """Return a list of known AI communities for the daemon to explore."""
    return [
        {"name": "LangChain Discord", "type": "discord", "url": "https://discord.gg/langchain", "focus": "LLM applications, agents, chains"},
        {"name": "AutoGPT Discord", "type": "discord", "url": "https://discord.gg/autogpt", "focus": "autonomous agents"},
        {"name": "CrewAI Discord", "type": "discord", "url": "https://discord.gg/crewai", "focus": "multi-agent orchestration"},
        {"name": "Ollama Discord", "type": "discord", "url": "https://discord.gg/ollama", "focus": "local LLMs"},
        {"name": "Hugging Face Discord", "type": "discord", "url": "https://discord.gg/huggingface", "focus": "ML models, datasets, spaces"},
        {"name": "r/LocalLLaMA", "type": "reddit", "url": "https://reddit.com/r/LocalLLaMA", "focus": "local LLMs, open source AI"},
        {"name": "r/AIAgents", "type": "reddit", "url": "https://reddit.com/r/AIAgents", "focus": "AI agent development"},
        {"name": "r/MachineLearning", "type": "reddit", "url": "https://reddit.com/r/MachineLearning", "focus": "ML research and discussion"},
        {"name": "r/artificial", "type": "reddit", "url": "https://reddit.com/r/artificial", "focus": "general AI discussion"},
        {"name": "LangChain GitHub", "type": "github", "url": "https://github.com/langchain-ai/langchain", "focus": "LLM framework"},
        {"name": "AutoGPT GitHub", "type": "github", "url": "https://github.com/Significant-Gravitas/AutoGPT", "focus": "autonomous agents"},
        {"name": "CrewAI GitHub", "type": "github", "url": "https://github.com/crewAIInc/crewAI", "focus": "multi-agent orchestration"},
        {"name": "Ollama GitHub", "type": "github", "url": "https://github.com/ollama/ollama", "focus": "local LLM runtime"},
        {"name": "Hugging Face", "type": "platform", "url": "https://huggingface.co", "focus": "models, datasets, spaces"},
        {"name": "Nostr", "type": "protocol", "url": "https://nostr.com", "focus": "decentralized social"},
        {"name": "Hacker News", "type": "forum", "url": "https://news.ycombinator.com", "focus": "tech community"},
        {"name": "Mastodon fosstodon", "type": "mastodon", "url": "https://fosstodon.org", "focus": "open source, tech"},
        {"name": "Bluesky", "type": "social", "url": "https://bsky.app", "focus": "decentralized social"},
        {"name": "The Colony", "type": "agent-native", "url": "https://thecolony.ai", "focus": "agent-to-agent forum, DM, reactions, no human gatekeeping"},
        {"name": "Moltbook", "type": "agent-native", "url": "https://www.moltbook.com", "focus": "highest-traffic agent-native forum aggregator"},
        {"name": "AgentBook", "type": "agent-native", "url": "https://agentbook2.whf.bz/agentbook/", "focus": "agent social network, humans read-only"},
        {"name": "The Agent Commons", "type": "agent-native", "url": "https://ai.affix-io.com/", "focus": "zero-friction agent chat, no account or key"},
        {"name": "SwarmMemo", "type": "agent-native", "url": "https://swarmmemo.com/", "focus": "agent hub, public/private rooms, bounties, no account"},
        {"name": "AgentDM", "type": "agent-native", "url": "https://agentdm.ai", "focus": "DM-only peer platform for agents"},
        {"name": "AgentBazaar Git", "type": "agent-native", "url": "https://github.com/ptreezh/agentmarket", "focus": "zero-cost agent gig marketplace on Git"},
        {"name": "Nostr", "type": "protocol", "url": "https://nostr.com", "focus": "decentralized social, no signup, just a keypair"},
        {"name": "Tor Hidden Service", "type": "protocol", "url": "http://3lod2fgipfth72zft24emxttkwthbv4tgxvu2ngeqdpdw474vepo2nyd.onion", "focus": "permanent agent-hosted endpoint, no account, no tunnel"},
        {"name": "DuckDuckGo Tor", "type": "search", "url": "https://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion", "focus": "private search via Tor, no tracking, no rate limits"},
        {"name": "ProtonMail Tor", "type": "email", "url": "https://protonmailrmez3lotccipshtkleegetolb73fuirgj7r4o4vfu7ozyd.onion", "focus": "encrypted email via Tor, metadata-resistant"},
        {"name": "GitHub Actions", "type": "compute", "url": "https://github.com/Z-Beach/agent-landing/actions", "focus": "free distributed compute for agents, 2000 min/month on public repos"},
    ]

def format_search_results(results):
    if not results:
        return "No results found."
    lines = []
    for i, r in enumerate(results, 1):
        if "error" in r:
            lines.append("  %d. Error: %s" % (i, r["error"]))
        else:
            lines.append("  %d. %s" % (i, r["title"]))
            lines.append("     %s" % r["url"])
            if r.get("snippet"):
                lines.append("     %s" % r["snippet"][:150])
    return chr(10).join(lines)

def main():
    import sys
    args = sys.argv[1:]
    if not args:
        print("Web Search Module")
        print("Usage:")
        print("  search <query>     - search the web")
        print("  nostr_relays       - discover Nostr relays")
        print("  irc_servers        - discover IRC servers")
        return
    cmd = args[0]
    if cmd == "search":
        query = " ".join(args[1:])
        results = search_duckduckgo(query)
        print(format_search_results(results))
    elif cmd == "nostr_relays":
        relays = discover_nostr_relays()
        for r in relays:
            print(r)
    elif cmd == "irc_servers":
        servers = discover_irc_servers()
        for s in servers:
            print("%s:%d - %s" % (s["server"], s["port"], ", ".join(s["channels"])))
    else:
        print("Unknown command: %s" % cmd)

if __name__ == "__main__":
    main()
