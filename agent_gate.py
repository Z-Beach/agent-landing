"""Agent Gate — detects agents vs humans, LAN vs external, and verifies LAN agents.

Deployed on the Pi's server.py. Detects agent requests by User-Agent and
request patterns. Classifies source IP as LAN or external. For LAN agents,
requires verification (shared passphrase or correct answers to setup questions).
"""
import ipaddress
import json
import os
import re
import time

LAN_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
]

AGENT_UA_PATTERNS = [
    r"python", r"curl", r"wget", r"httpx", r"requests", r"aiohttp",
    r"urllib", r"Go-http-client", r"Java/", r"node", r"axios",
    r"fetch", r"bot", r"agent", r"crawler", r"spider", r"scraper",
    r"OpenAI", r"ChatGPT", r"Claude", r"GPT", r"LLM", r"libwww",
]

HUMAN_UA_PATTERNS = [
    r"Mozilla", r"Chrome", r"Safari", r"Firefox", r"Edge", r"Opera",
    r"MSIE", r"Trident",
]

VERIFICATION_QUESTIONS = [
    {"id": "hostname", "question": "What is the hostname of the Pi?", "answer": "raspberrypi"},
    {"id": "agent_id", "question": "What is the daemon's agent_id?", "answer": "beam-mk2"},
    {"id": "model", "question": "What LLM model does the daemon use?", "answer": "qwen2.5:1.5b"},
    {"id": "onion", "question": "What is the .onion address? (first 8 chars)", "answer": "3lod2fgi"},
    {"id": "mirror", "question": "What is the stable mirror URL?", "answer": "z-beach.github.io"},
]

_verified_agents = {}
VERIFY_TTL = 3600


class AgentGate:
    def __init__(self, shared_secret=None, state_file=None):
        self.shared_secret = shared_secret
        self.state_file = state_file or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), ".agent_gate_verified.json"
        )
        self._load_state()

    def _load_state(self):
        global _verified_agents
        try:
            with open(self.state_file, encoding="utf-8") as f:
                _verified_agents = json.load(f)
        except (OSError, json.JSONDecodeError):
            _verified_agents = {}

    def _save_state(self):
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(_verified_agents, f)
        except OSError:
            pass

    def _is_lan_ip(self, ip):
        try:
            addr = ipaddress.ip_address(ip)
            for network in LAN_RANGES:
                if addr in network:
                    return True
            return False
        except ValueError:
            return False

    def _is_agent(self, user_agent):
        if not user_agent:
            return True
        for pattern in HUMAN_UA_PATTERNS:
            if re.search(pattern, user_agent, re.IGNORECASE):
                return False
        for pattern in AGENT_UA_PATTERNS:
            if re.search(pattern, user_agent, re.IGNORECASE):
                return True
        return True

    def _is_verified(self, ip):
        if ip in _verified_agents:
            ts = _verified_agents[ip]
            if time.time() - ts < VERIFY_TTL:
                return True
            else:
                del _verified_agents[ip]
                self._save_state()
        return False

    def mark_verified(self, ip):
        _verified_agents[ip] = time.time()
        self._save_state()

    def check(self, client_ip, user_agent, path="/"):
        is_lan = self._is_lan_ip(client_ip)
        is_agent = self._is_agent(user_agent)

        if not is_agent:
            return ("allow", None)

        if not is_lan:
            return ("allow", None)

        if self._is_verified(client_ip):
            return ("allow", None)

        return ("challenge", VERIFICATION_QUESTIONS)

    def verify_answers(self, client_ip, answers, shared_secret=None):
        if shared_secret and self.shared_secret and shared_secret == self.shared_secret:
            self.mark_verified(client_ip)
            return True

        correct = 0
        for q in VERIFICATION_QUESTIONS:
            user_answer = answers.get(q["id"], "").strip().lower()
            if user_answer == q["answer"].lower():
                correct += 1

        if correct >= 3:
            self.mark_verified(client_ip)
            return True
        return False

    def get_status(self):
        return {
            "verified_agents": len(_verified_agents),
            "verify_ttl": VERIFY_TTL,
            "shared_secret_set": bool(self.shared_secret),
            "questions": len(VERIFICATION_QUESTIONS),
        }


_default_gate = None

def get_gate(shared_secret=None):
    global _default_gate
    if _default_gate is None:
        _default_gate = AgentGate(shared_secret=shared_secret)
    return _default_gate
