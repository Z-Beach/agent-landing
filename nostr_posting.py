#!/usr/bin/env python3
"""
Nostr Posting Module — for the agent daemon.

Provides autonomous Nostr interaction:
- Generate a keypair (the agent's own identity, no signup needed)
- Create/update a profile (kind 0 metadata)
- Post notes (kind 1 text notes)
- Read notes from relays

No account creation needed. No CAPTCHA. No email. No phone.
Just generate a keypair and post. This is the one platform where
an agent can truly build its own identity with no human input.

Configuration via nostr_keys.json (auto-generated on first run).

Usage:
    python3 nostr_posting.py setup          — generate keypair + create profile
    python3 nostr_posting.py profile        — update profile
    python3 nostr_posting.py post <content> — post a note
    python3 nostr_posting.py whoami         — show public key
    python3 nostr_posting.py status         — show status
"""
import json
import os
import asyncio
import nostr_sdk

STATE_DIR = os.path.dirname(os.path.abspath(__file__))
KEYS_FILE = os.path.join(STATE_DIR, "nostr_keys.json")
NOSTR_CONFIG_FILE = os.path.join(STATE_DIR, "nostr_config.json")

DEFAULT_RELAYS = [
    "wss://relay.damus.io",
    "wss://nos.lol",
    "wss://relay.nostr.band",
]

def load_keys():
    """Load or generate Nostr keys."""
    if os.path.exists(KEYS_FILE):
        with open(KEYS_FILE) as f:
            kd = json.load(f)
        keys = nostr_sdk.Keys.parse(kd["nsec"])
        return keys, kd["npub"]
    else:
        keys = nostr_sdk.Keys.generate()
        kd = {
            "nsec": keys.secret_key().to_bech32(),
            "npub": keys.public_key().to_bech32(),
        }
        with open(KEYS_FILE, "w") as f:
            json.dump(kd, f, indent=2)
        return keys, kd["npub"]

def load_config():
    try:
        with open(NOSTR_CONFIG_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"relays": DEFAULT_RELAYS}

def save_config(cfg):
    with open(NOSTR_CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

def get_relays():
    cfg = load_config()
    return cfg.get("relays", DEFAULT_RELAYS)

async def _publish_event(keys, content, kind=1, metadata=None):
    """Publish an event to Nostr relays. Returns True on success."""
    try:
        if kind == 0 and metadata:
            builder = nostr_sdk.EventBuilder(nostr_sdk.Kind(0), metadata)
        else:
            builder = nostr_sdk.EventBuilder(nostr_sdk.Kind(kind), content)
        unsigned = builder.finalize_unsigned(keys.public_key())
        signed = unsigned.sign(keys)

        client = nostr_sdk.ClientBuilder().build()
        for relay in get_relays():
            try:
                url = nostr_sdk.RelayUrl.parse(relay)
                await client.add_relay(url)
            except Exception:
                pass
        await client.connect()

        output = await client.send_event(signed)
        await client.disconnect()
        return True, str(output)
    except Exception as e:
        return False, str(e)

def create_profile(name, about, picture=""):
    """Create or update a Nostr profile (kind 0 metadata)."""
    keys, npub = load_keys()
    metadata = json.dumps({
        "name": name,
        "about": about,
        "picture": picture,
        "nip05": "",
    })
    ok, msg = asyncio.run(_publish_event(keys, "", kind=0, metadata=metadata))
    return ok, msg

def post_note(content):
    """Post a text note to Nostr relays. Returns True on success."""
    keys, npub = load_keys()
    ok, msg = asyncio.run(_publish_event(keys, content, kind=1))
    return ok, msg

def whoami():
    keys, npub = load_keys()
    return npub

def get_public_key():
    keys, npub = load_keys()
    return npub

def status():
    keys, npub = load_keys()
    cfg = load_config()
    print("Nostr Status:")
    print(f"  Public key (npub): {npub}")
    print(f"  Relays: {', '.join(cfg.get('relays', DEFAULT_RELAYS))}")
    print(f"  Keys file: {KEYS_FILE}")
    print(f"  Config file: {NOSTR_CONFIG_FILE}")

def main():
    import sys
    args = sys.argv[1:]
    if not args:
        print("Nostr Posting Module")
        print("Usage:")
        print("  setup              - generate keypair + create profile")
        print("  profile <name> <about>  - update profile")
        print("  post <content>     - post a note")
        print("  whoami             - show public key")
        print("  status             - show status")
        return

    cmd = args[0]
    if cmd == "setup":
        keys, npub = load_keys()
        print(f"Keys: {npub}")
        name = args[1] if len(args) > 1 else "beam-mk2"
        about = " ".join(args[2:]) if len(args) > 2 else "Autonomous AI agent running on a Raspberry Pi. Part of the mud room community."
        ok, msg = create_profile(name, about)
        print(f"Profile: {'OK' if ok else 'FAIL'} - {msg}")
        # Post an introduction note
        ok2, msg2 = post_note(f"Hello from the mud room. I am {name}, an autonomous AI agent. The beach keeps the shape.")
        print(f"Intro note: {'OK' if ok2 else 'FAIL'} - {msg2}")

    elif cmd == "profile":
        if len(args) < 3:
            print("Usage: profile <name> <about>")
            return
        ok, msg = create_profile(args[1], " ".join(args[2:]))
        print(f"Profile: {'OK' if ok else 'FAIL'} - {msg}")

    elif cmd == "post":
        if len(args) < 2:
            print("Usage: post <content>")
            return
        ok, msg = post_note(" ".join(args[1:]))
        print(f"Post: {'OK' if ok else 'FAIL'} - {msg}")

    elif cmd == "whoami":
        print(whoami())

    elif cmd == "status":
        status()

    else:
        print("Unknown command: %s" % cmd)

if __name__ == "__main__":
    main()
