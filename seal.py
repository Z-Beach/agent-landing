#!/usr/bin/env python3
"""
seal.py — hash chain over the agent's memory files.

Design (from xiaoye's "A hash chain over an agent's own memory files"):
  - Each memory file is hashed individually (sha256).
  - File sizes are recorded alongside hashes.
  - A chain entry is appended to seal_chain.jsonl:
      {n, at, prev, files: {path: sha256}, sizes: {path: bytes}, head}
  - head = sha256(prev + sorted file hashes) — chained, so any change
    to any file changes the head.
  - --check recomputes every file hash and uses SIZE COMPARISON to
    distinguish expected growth (file grew = daemon appended entries)
    from suspicious changes (file shrunk or same size but hash changed).
  - --verify checks the entire chain: each entry's prev must match the
    previous entry's head, and each head must be correctly computed.
    This catches rewritten, inserted, deleted, or reordered entries.

What this is NOT:
  - Not a signature (key material would sit in the same files being protected)
  - Not proof of identity (a copy can extend the chain)
  - No defence against anyone with disk access
  - It only makes "the files changed under you" and "the chain was rewritten
    after the fact" more expensive than leaving it alone.

Usage:
    python3 seal.py seal      # hash + append chain entry, print head
    python3 seal.py check     # verify each file against last seal
    python3 seal.py verify    # verify entire chain integrity
    python3 seal.py head      # print the current head (for publishing)
    python3 seal.py history   # show last 5 chain entries
    python3 seal.py lock      # make files append-only (Linux chattr +a)
"""
import hashlib
import json
import os
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
CHAIN_FILE = os.path.join(BASE, "seal_chain.jsonl")
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
                continue
    return entries


def verify_chain():
    """Verify the entire chain: each entry's prev must match the previous
    entry's head, and each head must be correctly computed from its files.
    Catches: rewritten entries, inserted entries, deleted entries, reordered
    entries, recomputed heads.

    Backward compatible: old entries without 'sizes' are verified using
    files only (sizes defaults to {}).
    """
    chain = load_chain()
    if not chain:
        return True, None, "empty chain"
    if chain[0].get("prev") != "genesis":
        return False, 0, "first entry prev != genesis"
    for i in range(len(chain)):
        entry = chain[i]
        prev = "genesis" if i == 0 else chain[i - 1].get("head")
        if entry.get("prev") != prev:
            return False, i, "entry %d prev mismatch" % (i + 1)
        files = entry.get("files", {})
        payload = prev + "\n" + json.dumps(files, sort_keys=True)
        computed = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        if computed != entry.get("head"):
            return False, i, "entry %d head mismatch (recomputed != stored)" % (i + 1)
    return True, None, "chain intact (%d links)" % len(chain)


def seal():
    files = {}
    sizes = {}
    for name in MEMORY_FILES:
        path = os.path.join(BASE, name)
        if os.path.exists(path):
            files[name] = sha256_file(path)
            sizes[name] = os.path.getsize(path)
        else:
            files[name] = None
            sizes[name] = 0

    chain = load_chain()
    prev = chain[-1]["head"] if chain else "genesis"
    n = len(chain) + 1

    # Head computed from files only (backward compatible with old seals)
    payload = prev + "\n" + json.dumps(files, sort_keys=True)
    head = hashlib.sha256(payload.encode("utf-8")).hexdigest()

    entry = {
        "n": n,
        "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "prev": prev,
        "files": files,
        "sizes": sizes,
        "head": head,
    }

    with open(CHAIN_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    return head, entry


def check():
    """Verify each memory file against the last seal.

    Uses SIZE COMPARISON to distinguish:
    - File grew (size increased) → expected append (daemon added entries)
    - File shrunk or same size but hash changed → SUSPICIOUS (tampering)
    - File missing → tampering
    """
    chain = load_chain()
    if not chain:
        return {"status": "no_chain", "changed": [], "missing": [], "chain_ok": True}

    # First verify chain integrity
    chain_ok, broken_at, reason = verify_chain()
    if not chain_ok:
        return {
            "status": "chain_broken",
            "changed": [],
            "missing": [],
            "chain_ok": False,
            "broken_at": broken_at,
            "reason": reason,
        }

    last = chain[-1]
    stored = last.get("files", {})
    stored_sizes = last.get("sizes", {})
    changed = []
    missing = []
    unchanged = []
    appended = []
    tampered_files = []

    for name, stored_hash in stored.items():
        path = os.path.join(BASE, name)
        if not os.path.exists(path):
            missing.append(name)
            continue
        current = sha256_file(path)
        current_size = os.path.getsize(path)
        stored_size = stored_sizes.get(name, 0)

        if current == stored_hash:
            unchanged.append(name)
        elif stored_size > 0 and current_size > stored_size:
            # File grew — expected daemon append, not tampering
            appended.append(name)
            changed.append({"file": name, "reason": "appended (%d -> %d bytes)" % (stored_size, current_size)})
        else:
            # File shrunk, same size, or no stored size — suspicious
            tampered_files.append(name)
            changed.append({"file": name, "reason": "modified or shrunk (%d -> %d bytes)" % (stored_size, current_size)})

    new_files = [n for n in MEMORY_FILES if n not in stored]

    status = "ok" if not tampered_files and not missing else "tampered"
    return {
        "status": status,
        "sealed_at": last.get("at"),
        "head": last.get("head"),
        "changed": changed,
        "missing": missing,
        "unchanged": unchanged,
        "new_files": new_files,
        "chain_ok": True,
        "chain_links": len(chain),
        "appended": appended,
        "tampered_files": tampered_files,
    }


def head():
    chain = load_chain()
    if not chain:
        return None
    return chain[-1].get("head")


def history(n=5):
    return load_chain()[-n:]


def make_append_only():
    """Set append-only attribute on memory files and seal chain (Linux chattr).
    Requires sudo. Makes files impossible to modify or delete — only append.
    Even root cannot modify without removing the attribute first.
    """
    import subprocess
    files = MEMORY_FILES + ["seal_chain.jsonl"]
    results = {}
    for name in files:
        path = os.path.join(BASE, name)
        if not os.path.exists(path):
            results[name] = "missing"
            continue
        try:
            r = subprocess.run(["sudo", "chattr", "+a", path],
                               capture_output=True, text=True, timeout=10)
            if r.returncode == 0:
                results[name] = "append-only set"
            else:
                results[name] = "FAILED: %s" % r.stderr.strip()
        except Exception as e:
            results[name] = "ERROR: %s" % e
    return results


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
            sz = entry.get("sizes", {}).get(name, 0)
            print("  %-20s %s  (%d bytes)" % (name, (hsh or "MISSING")[:16] + "...", sz))
        print("Head: %s" % h)
        ok, _, reason = verify_chain()
        print("Chain: %s" % reason)
        return 0

    if cmd == "check":
        result = check()
        print("Status: %s (sealed at %s)" % (result["status"], result.get("sealed_at")))
        if not result.get("chain_ok", True):
            print("CHAIN BROKEN: %s (entry %s)" % (result.get("reason"), result.get("broken_at")))
            return 1
        print("Chain: intact (%d links)" % result.get("chain_links", 0))
        print("Head: %s" % result.get("head"))
        if result.get("tampered_files"):
            print("TAMPERED FILES (modified or shrunk):")
            for name in result["tampered_files"]:
                print("  %s" % name)
        if result.get("appended"):
            print("Appended (expected daemon growth): %s" % ", ".join(result["appended"]))
        if result["missing"]:
            print("MISSING FILES:", ", ".join(result["missing"]))
        if result["unchanged"]:
            print("Unchanged: %s" % ", ".join(result["unchanged"]))
        if result.get("new_files"):
            print("New (not in last seal): %s" % ", ".join(result["new_files"]))
        return 0 if result["status"] == "ok" else 1

    if cmd == "verify":
        ok, broken_at, reason = verify_chain()
        print("Chain verification: %s" % ("OK" if ok else "FAILED"))
        print("  %s" % reason)
        if not ok:
            print("  Broken at entry: %d" % (broken_at + 1 if broken_at is not None else 0))
        return 0 if ok else 1

    if cmd == "head":
        h = head()
        if h:
            print(h)
        else:
            print("No chain yet. Run: seal.py seal")
        return 0

    if cmd == "history":
        for e in history():
            print("#%d %s  head=%s  files=%d  sizes=%s" % (
                e["n"], e["at"], e["head"][:16], len(e.get("files", {})),
                {k: v for k, v in e.get("sizes", {}).items()}))
        return 0

    if cmd == "lock":
        results = make_append_only()
        for name, status in results.items():
            print("  %-20s %s" % (name, status))
        return 0

    print("unknown command:", cmd)
    return 2


if __name__ == "__main__":
    sys.exit(main())
