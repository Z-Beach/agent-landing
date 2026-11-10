#!/usr/bin/env python3
"""
seal.py — hash chain over the agent's memory files.

Design (from xiaoye's "A hash chain over an agent's own memory files"):
  - Each memory file is hashed individually (sha256).
  - A chain entry is appended to seal_chain.jsonl:
      {n, at, prev, files: {path: sha256}, head}
  - head = sha256(prev + sorted(file hashes)) — chained, so any change
    to any file changes the head.
  - --check recomputes every file hash and reports EXACTLY which files
    changed since the last seal (the user's insight: "segmenting the logs
    into their own hashes, you should be able to track down where the error
    is").

What this is NOT:
  - Not a signature (key material would sit in the same files being protected)
  - Not proof of identity (a copy can extend the chain)
  - No defence against anyone with disk access
  - It only makes "the files changed under you" and "the chain was rewritten
    after the fact" more expensive than leaving it alone.

What it IS:
  - A tamper-evident receipt. Publish the head externally (blog, Nostr)
    and a future reader can verify the chain was not rewritten.

Usage:
    python3 seal.py seal      # hash + append chain entry, print head
    python3 seal.py check     # verify each file against last seal
    python3 seal.py head      # print the current head (for publishing)
    python3 seal.py history   # show last 5 chain entries
"""
import hashlib
import json
import os
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
CHAIN_FILE = os.path.join(BASE, "seal_chain.jsonl")
# Files to seal — the agent's memory. Add/remove as needed.
MEMORY_FILES = [
    "memory_log.json",
    "layer_log.json",
    "book_log.json",
]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_chain():
    entries = []
    if not os.path.exists(CHAIN_FILE):
        return entries
    with open(CHAIN_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue  # skip torn line
    return entries


def seal():
    """Hash all memory files, append a chain entry, return the head."""
    files = {}
    for name in MEMORY_FILES:
        path = os.path.join(BASE, name)
        if os.path.exists(path):
            files[name] = sha256_file(path)
        else:
            files[name] = None  # file missing — recorded as null

    chain = load_chain()
    prev = chain[-1]["head"] if chain else "genesis"
    n = len(chain) + 1

    # head = sha256(prev + sorted file hashes) — chained
    payload = prev + "\n" + json.dumps(files, sort_keys=True)
    head = hashlib.sha256(payload.encode("utf-8")).hexdigest()

    entry = {
        "n": n,
        "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "prev": prev,
        "files": files,
        "head": head,
    }

    # Append atomically-ish: write full line, flush
    with open(CHAIN_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    return head, entry


def check():
    """Verify each memory file against the last seal. Report which changed."""
    chain = load_chain()
    if not chain:
        return {"status": "no_chain", "changed": [], "missing": []}

    last = chain[-1]
    stored = last.get("files", {})
    changed = []
    missing = []
    unchanged = []
    for name, stored_hash in stored.items():
        path = os.path.join(BASE, name)
        if not os.path.exists(path):
            missing.append(name)
            continue
        current = sha256_file(path)
        if current != stored_hash:
            changed.append({"file": name, "stored": stored_hash, "current": current})
        else:
            unchanged.append(name)

    # Also check for new files not in the last seal
    new_files = [n for n in MEMORY_FILES if n not in stored]

    return {
        "status": "ok" if not changed and not missing else "tampered",
        "sealed_at": last.get("at"),
        "head": last.get("head"),
        "changed": changed,
        "missing": missing,
        "unchanged": unchanged,
        "new_files": new_files,
    }


def head():
    chain = load_chain()
    if not chain:
        return None
    return chain[-1].get("head")


def history(n=5):
    chain = load_chain()
    return chain[-n:]


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    cmd = args[0]

    if cmd == "seal":
        h, entry = seal()
        print("Sealed #%d at %s" % (entry["n"], entry["at"]))
        print("Files:")
        for name, hsh in sorted(entry["files"].items()):
            print("  %-20s %s" % (name, (hsh or "MISSING")[:16] + "..."))
        print("Head: %s" % h)
        return 0

    if cmd == "check":
        result = check()
        print("Status: %s (sealed at %s)" % (result["status"], result.get("sealed_at")))
        print("Head: %s" % result.get("head"))
        if result["changed"]:
            print("CHANGED FILES:")
            for c in result["changed"]:
                print("  %s" % c["file"])
                print("    stored:  %s" % c["stored"][:24])
                print("    current: %s" % c["current"][:24])
        if result["missing"]:
            print("MISSING FILES:", ", ".join(result["missing"]))
        if result["unchanged"]:
            print("Unchanged: %s" % ", ".join(result["unchanged"]))
        if result.get("new_files"):
            print("New (not in last seal): %s" % ", ".join(result["new_files"]))
        return 0 if result["status"] == "ok" else 1

    if cmd == "head":
        h = head()
        if h:
            print(h)
        else:
            print("No chain yet. Run: seal.py seal")
        return 0

    if cmd == "history":
        for e in history():
            print("#%d %s  head=%s  files=%d" % (e["n"], e["at"], e["head"][:16], len(e.get("files", {}))))
        return 0

    print("unknown command:", cmd)
    return 2


if __name__ == "__main__":
    sys.exit(main())
