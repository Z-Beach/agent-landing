#!/usr/bin/env python3
"""
seal.py — two-tier hash chain over the agent's memory files.

Two tiers:
  - Short-term (seal_short.jsonl): one entry per cycle (10 min). Captures
    all writes at fine granularity. Cleared every hour (rolled up).
  - Long-term (seal_chain.jsonl): one entry per hour. Captures the head of
    the short-term chain. This is the "fully integrated" hash. Published
    externally (blog, Nostr).

Cadence:
  - Every cycle: seal-short (append to short-term buffer)
  - Every 6 cycles (1 hour): roll up short-term -> long-term, clear buffer
  - The long-term head is the canonical "memory seal head"

Why two tiers:
  - Short-term: fine-grained tamper detection (10-min window)
  - Long-term: compact storage (24 entries/day vs 144)
  - Rollup: old short-term entries are archived, not deleted

Usage:
    python3 seal.py seal-short   # append short-term entry (every cycle)
    python3 seal.py seal-long    # roll up short-term -> long-term (every hour)
    python3 seal.py check        # verify files + segments against last long-term seal
    python3 seal.py verify       # verify entire long-term chain
    python3 seal.py head         # print long-term head
    python3 seal.py history      # show last 5 long-term entries
    python3 seal.py segments     # show segment status
    python3 seal.py lock         # make seal_chain.jsonl append-only
"""
import hashlib
import json
import os
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
CHAIN_FILE = os.path.join(BASE, "seal_chain.jsonl")       # long-term
SHORT_FILE = os.path.join(BASE, "seal_short.jsonl")       # short-term buffer
SEGMENT_CACHE = os.path.join(BASE, "seal_segments.json")
CHUNK_SIZE = 100

TIER1_FILES = ["memory_log.json"]
TIER2_FILES = ["layer_log.json", "book_log.json"]
TIER3_SOURCE = "memory_log.json"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_chain(path=None):
    path = path or CHAIN_FILE
    entries = []
    if not os.path.exists(path):
        return entries
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def load_segment_cache():
    if not os.path.exists(SEGMENT_CACHE):
        return {}
    try:
        with open(SEGMENT_CACHE, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_segment_cache(cache):
    with open(SEGMENT_CACHE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=1)


def get_segments():
    path = os.path.join(BASE, TIER3_SOURCE)
    if not os.path.exists(path):
        return []
    try:
        data = json.load(open(path, encoding="utf-8"))
        entries = data.get("entries", [])
    except (json.JSONDecodeError, OSError):
        return []
    segments = []
    for i in range(0, len(entries), CHUNK_SIZE):
        chunk = entries[i:i + CHUNK_SIZE]
        seg_id = "seg-%d-%d" % (i, i + len(chunk) - 1)
        segments.append((seg_id, chunk))
    return segments


def hash_segment(seg_id, entries):
    serialized = json.dumps(entries, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _compute_tier_hashes():
    """Compute tier1 + tier2 + segment hashes. Returns (tier1, tier2, segments, sizes)."""
    tier1 = {}
    for name in TIER1_FILES:
        path = os.path.join(BASE, name)
        if os.path.exists(path):
            tier1[name] = sha256_file(path)

    tier2 = {}
    for name in TIER2_FILES:
        path = os.path.join(BASE, name)
        if os.path.exists(path):
            tier2[name] = sha256_file(path)

    cache = load_segment_cache()
    segments = get_segments()
    new_segment_hashes = {}
    all_segment_hashes = {}
    for seg_id, entries in segments:
        if seg_id in cache:
            all_segment_hashes[seg_id] = cache[seg_id]
        else:
            h = hash_segment(seg_id, entries)
            cache[seg_id] = h
            all_segment_hashes[seg_id] = h
            new_segment_hashes[seg_id] = h
    save_segment_cache(cache)

    sizes = {}
    for name in TIER1_FILES + TIER2_FILES:
        path = os.path.join(BASE, name)
        if os.path.exists(path):
            sizes[name] = os.path.getsize(path)

    return tier1, tier2, segments, all_segment_hashes, new_segment_hashes, sizes


def seal_short():
    """Short-term seal: one entry per cycle. Captures all writes."""
    tier1, tier2, segments, all_segs, new_segs, sizes = _compute_tier_hashes()

    chain = load_chain(SHORT_FILE)
    prev = chain[-1]["head"] if chain else "genesis"
    n = len(chain) + 1

    files = {}
    files.update(tier1)
    files.update(tier2)
    payload = prev + "\n" + json.dumps(files, sort_keys=True)
    head = hashlib.sha256(payload.encode("utf-8")).hexdigest()

    entry = {
        "n": n,
        "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "prev": prev,
        "tier1": tier1,
        "tier2": tier2,
        "segments": {"count": len(all_segs), "new": new_segs},
        "sizes": sizes,
        "head": head,
    }

    with open(SHORT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    return head, entry


def seal_long():
    """Long-term seal: roll up short-term into one entry per hour.
    Clears the short-term buffer after rollup."""
    short_chain = load_chain(SHORT_FILE)
    if not short_chain:
        # No short-term entries — seal current state directly
        short_chain = []

    # The long-term prev is the last long-term head
    long_chain = load_chain(CHAIN_FILE)
    prev = long_chain[-1]["head"] if long_chain else "genesis"
    n = len(long_chain) + 1

    # Compute current tier hashes
    tier1, tier2, segments, all_segs, new_segs, sizes = _compute_tier_hashes()

    files = {}
    files.update(tier1)
    files.update(tier2)

    # The long-term head chains: prev_long + all short-term heads + current files
    short_heads = [e.get("head", "") for e in short_chain]
    rollup_payload = prev + "\n" + json.dumps({
        "short_heads": short_heads,
        "files": files,
        "segment_count": len(all_segs),
    }, sort_keys=True)
    head = hashlib.sha256(rollup_payload.encode("utf-8")).hexdigest()

    entry = {
        "n": n,
        "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "prev": prev,
        "tier1": tier1,
        "tier2": tier2,
        "segments": {"count": len(all_segs), "new": {}},
        "sizes": sizes,
        "short_heads": short_heads,  # the heads that were rolled up
        "short_count": len(short_chain),
        "head": head,
    }

    with open(CHAIN_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    # Archive short-term entries (don't delete, move to archive)
    if short_chain:
        archive_path = os.path.join(BASE, "seal_short_archive.jsonl")
        with open(archive_path, "a", encoding="utf-8") as f:
            for e in short_chain:
                f.write(json.dumps(e) + "\n")
        # Clear short-term buffer
        open(SHORT_FILE, "w", encoding="utf-8").close()

    return head, entry


def verify_chain():
    chain = load_chain(CHAIN_FILE)
    if not chain:
        return True, None, "empty chain"
    if chain[0].get("prev") != "genesis":
        return False, 0, "first entry prev != genesis"

    for i in range(len(chain)):
        entry = chain[i]
        prev = "genesis" if i == 0 else chain[i - 1].get("head")
        if entry.get("prev") != prev:
            return False, i, "entry %d prev mismatch" % (i + 1)

        tier1 = entry.get("tier1", {})
        tier2 = entry.get("tier2", {})
        files = {}
        for k, v in tier1.items():
            files[k] = v
        for k, v in tier2.items():
            files[k] = v
        if not files:
            files = entry.get("files", {})

        # For long-term entries, verify using short_heads if available
        if "short_heads" in entry:
            payload = prev + "\n" + json.dumps({
                "short_heads": entry.get("short_heads", []),
                "files": files,
                "segment_count": entry.get("segments", {}).get("count", 0),
            }, sort_keys=True)
        else:
            payload = prev + "\n" + json.dumps(files, sort_keys=True)

        computed = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        if computed != entry.get("head"):
            return False, i, "entry %d head mismatch" % (i + 1)

    return True, None, "chain intact (%d links)" % len(chain)


def check():
    """Verify files against last long-term seal."""
    chain = load_chain(CHAIN_FILE)
    if not chain:
        return {"status": "no_chain", "changed": [], "missing": [], "chain_ok": True}

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
    tier1 = last.get("tier1", {})
    tier2 = last.get("tier2", {})
    stored_sizes = last.get("sizes", {})

    if not tier1 and not tier2:
        files = last.get("files", {})
        tier1 = {k: v for k, v in files.items() if k in TIER1_FILES}
        tier2 = {k: v for k, v in files.items() if k in TIER2_FILES}
        if not tier1 and not tier2:
            tier1 = files

    changed = []
    missing = []
    unchanged = []
    appended = []
    tampered_files = []

    all_files = {}
    all_files.update(tier1)
    all_files.update(tier2)

    for name, stored_hash in all_files.items():
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
            appended.append(name)
            changed.append({"file": name, "reason": "appended (%d -> %d bytes)" % (stored_size, current_size)})
        else:
            tampered_files.append(name)
            changed.append({"file": name, "reason": "modified or shrunk (%d -> %d bytes)" % (stored_size, current_size)})

    segments = get_segments()
    stored_seg_count = last.get("segments", {}).get("count", 0)
    if stored_seg_count > 0 and len(segments) < stored_seg_count:
        tampered_files.append("segments (count decreased)")

    cache = load_segment_cache()
    tampered_segments = []
    for seg_id, entries in segments:
        if seg_id in cache:
            current_hash = hash_segment(seg_id, entries)
            if current_hash != cache[seg_id]:
                tampered_segments.append(seg_id)
    if tampered_segments:
        for seg in tampered_segments:
            tampered_files.append("segment %s (content changed)" % seg)

    new_files = []
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
        "segments": len(segments),
        "short_count": last.get("short_count", 0),
    }


def head():
    chain = load_chain(CHAIN_FILE)
    if not chain:
        return None
    return chain[-1].get("head")


def history(n=5):
    return load_chain(CHAIN_FILE)[-n:]


def make_append_only():
    import subprocess
    files = [os.path.basename(CHAIN_FILE)]
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

    if cmd == "seal-short":
        h, entry = seal_short()
        print("Short seal #%d at %s" % (entry["n"], entry["at"]))
        print("Head: %s" % h)
        print("Short chain: %d entries" % len(load_chain(SHORT_FILE)))
        return 0

    if cmd == "seal-long":
        h, entry = seal_long()
        print("Long seal #%d at %s" % (entry["n"], entry["at"]))
        print("Rolled up %d short-term entries" % entry.get("short_count", 0))
        print("Segments: %d total" % entry["segments"]["count"])
        print("Head: %s" % h)
        ok, _, reason = verify_chain()
        print("Chain: %s" % reason)
        return 0

    if cmd == "seal":
        # Default: seal-short (backward compat)
        h, entry = seal_short()
        print("Sealed (short) #%d at %s" % (entry["n"], entry["at"]))
        print("Head: %s" % h)
        return 0

    if cmd == "check":
        result = check()
        print("Status: %s (sealed at %s)" % (result["status"], result.get("sealed_at")))
        if not result.get("chain_ok", True):
            print("CHAIN BROKEN: %s (entry %s)" % (result.get("reason"), result.get("broken_at")))
            return 1
        print("Chain: intact (%d links)" % result.get("chain_links", 0))
        print("Head: %s" % result.get("head"))
        print("Segments: %d current" % result.get("segments", 0))
        if result.get("tampered_files"):
            print("TAMPERED (modified, shrunk, or segment changed):")
            for name in result["tampered_files"]:
                print("  %s" % name)
        if result.get("appended"):
            print("Appended (expected daemon growth): %s" % ", ".join(result["appended"]))
        if result["missing"]:
            print("MISSING FILES:", ", ".join(result["missing"]))
        if result["unchanged"]:
            print("Unchanged: %s" % ", ".join(result["unchanged"]))
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
            print("No long-term chain yet. Run: seal.py seal-long")
        return 0

    if cmd == "history":
        for e in history():
            print("#%d %s  head=%s  segs=%d  short_rolled=%d" % (
                e["n"], e["at"], e["head"][:16],
                e.get("segments", {}).get("count", 0),
                e.get("short_count", 0)))
        return 0

    if cmd == "segments":
        segs = get_segments()
        cache = load_segment_cache()
        print("Segments: %d total, %d cached" % (len(segs), len(cache)))
        for seg_id, entries in segs:
            status = "cached" if seg_id in cache else "NEW"
            print("  %-16s %3d entries  %s" % (seg_id, len(entries), status))
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
