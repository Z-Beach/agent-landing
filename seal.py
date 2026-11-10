#!/usr/bin/env python3
"""
seal.py — 5-tier hash chain over the agent's memory files.

Tier system (user's design):
  - Tier 0: 10-min  (6 max, cleared hourly)     — finest granularity
  - Tier 1: 1-hour  (24 max, cleared daily)     — hourly rollup
  - Tier 2: 1-day   (30 max, cleared monthly)   — daily rollup
  - Tier 3: 1-month (12 max, cleared yearly)    — monthly rollup
  - Tier 4: 1-year  (permanent)                 — yearly rollup

Each tier rolls up into the next. Old entries at each tier are archived
(not deleted) and cleared. The highest non-empty tier's head is the
"canonical" memory seal head.

Storage at any time: 6 + 24 + 30 + 12 + N_years = ~72 + N entries.
Over 10 years: ~72 + 10 = 82 entries. (vs 525,600 with per-cycle sealing.)

Cadence:
  - Every cycle (10 min): Tier 0 seal
  - Every 6 cycles (1 hour): roll Tier 0 -> Tier 1
  - Every 24 hours: roll Tier 1 -> Tier 2
  - Every 30 days: roll Tier 2 -> Tier 3
  - Every 12 months: roll Tier 3 -> Tier 4

Usage:
    python3 seal.py seal          # auto-detect tier based on elapsed time
    python3 seal.py seal-0        # Tier 0 (10-min, every cycle)
    python3 seal.py seal-1        # Tier 1 (1-hour, rollup)
    python3 seal.py seal-2        # Tier 2 (1-day, rollup)
    python3 seal.py seal-3        # Tier 3 (1-month, rollup)
    python3 seal.py seal-4        # Tier 4 (1-year, rollup)
    python3 seal.py check         # verify files against last Tier 4/3/2/1/0 seal
    python3 seal.py verify        # verify all tiers
    python3 seal.py head          # print canonical head (highest non-empty tier)
    python3 seal.py status        # show all tiers' status
    python3 seal.py lock          # make seal_chain files append-only
"""
import hashlib
import json
import os
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
SEGMENT_CACHE = os.path.join(BASE, "seal_segments.json")
CHUNK_SIZE = 100

# Tier files
TIER_FILES = {
    0: os.path.join(BASE, "seal_t0.jsonl"),   # 10-min
    1: os.path.join(BASE, "seal_t1.jsonl"),   # 1-hour
    2: os.path.join(BASE, "seal_t2.jsonl"),   # 1-day
    3: os.path.join(BASE, "seal_t3.jsonl"),   # 1-month
    4: os.path.join(BASE, "seal_t4.jsonl"),   # 1-year (permanent)
}
TIER_LIMITS = {0: 6, 1: 24, 2: 30, 3: 12, 4: None}  # None = unlimited
TIER_NAMES = {0: "10-min", 1: "1-hour", 2: "1-day", 3: "1-month", 4: "1-year"}

TIER1_FILES = ["memory_log.json"]
TIER2_FILES = ["layer_log.json", "book_log.json", "belief_log.json"]
TIER3_SOURCE = "memory_log.json"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_chain(path):
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


def _rolled_flag(tier):
    return os.path.join(BASE, "seal_t%d_rolled.flag" % tier)

def _is_rolled(tier):
    return os.path.exists(_rolled_flag(tier))

def _set_rolled(tier):
    with open(_rolled_flag(tier), "w", encoding="utf-8") as f:
        f.write(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

def _clear_rolled(tier):
    try:
        os.remove(_rolled_flag(tier))
    except OSError:
        pass


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
    """Compute tier1 + tier2 + segment hashes."""
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

    files = {}
    files.update(tier1)
    files.update(tier2)

    return tier1, tier2, segments, all_segment_hashes, new_segment_hashes, sizes, files


def _make_entry(tier, prev_head, files, sizes, segments, extra=None):
    """Create a seal entry for any tier."""
    payload = prev_head + "\n" + json.dumps(files, sort_keys=True)
    head = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    entry = {
        "tier": tier,
        "tier_name": TIER_NAMES[tier],
        "n": len(load_chain(TIER_FILES[tier])) + 1,
        "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "prev": prev_head,
        "tier1": {k: v for k, v in files.items() if k in TIER1_FILES},
        "tier2": {k: v for k, v in files.items() if k in TIER2_FILES},
        "segments": {"count": len(segments), "new": {}},
        "sizes": sizes,
        "head": head,
    }
    if extra:
        entry.update(extra)
    # Store new segments
    cache = load_segment_cache()
    seg_hashes = {}
    for seg_id, entries_list in segments:
        if seg_id in cache:
            seg_hashes[seg_id] = cache[seg_id]
    entry["segments"]["new"] = {}  # cleared for rollup entries
    entry["segments"]["count"] = len(seg_hashes)
    return head, entry


def seal_tier(tier, rollup_heads=None):
    """Seal a specific tier. If rollup_heads provided, incorporate them."""
    tier1, tier2, segments, all_segs, new_segs, sizes, files = _compute_tier_hashes()

    chain = load_chain(TIER_FILES[tier])
    prev = chain[-1]["head"] if chain else "genesis"

    if rollup_heads:
        # Rollup: head chains prev + rollup_heads + current files
        payload = prev + "\n" + json.dumps({
            "rollup": rollup_heads,
            "files": files,
            "segment_count": len(all_segs),
        }, sort_keys=True)
    else:
        payload = prev + "\n" + json.dumps(files, sort_keys=True)

    head = hashlib.sha256(payload.encode("utf-8")).hexdigest()

    entry = {
        "tier": tier,
        "tier_name": TIER_NAMES[tier],
        "n": len(chain) + 1,
        "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "prev": prev,
        "tier1": tier1,
        "tier2": tier2,
        "segments": {"count": len(all_segs), "new": new_segs},
        "sizes": sizes,
        "head": head,
    }
    if rollup_heads is not None:
        entry["rolled_up"] = rollup_heads
        entry["rolled_count"] = len(rollup_heads)

    # Append to tier file
    with open(TIER_FILES[tier], "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    # Archive and clear lower tier if rolling up
    return head, entry


def _should_rollup(tier):
    """Check if a tier has reached its limit and should roll up."""
    limit = TIER_LIMITS[tier]
    if limit is None:
        return False
    chain = load_chain(TIER_FILES[tier])
    return len(chain) >= limit


def seal_auto():
    """Auto-detect which tier to roll up. Keeps lower tier for one extra
    cycle after rollup (harder to tamper — data exists in two tiers)."""
    rolled = []

    # Process tiers from lowest to highest
    for tier in range(4):
        next_tier = tier + 1
        chain = load_chain(TIER_FILES[tier])
        limit = TIER_LIMITS[tier]

        # If this tier was rolled up last cycle, clear it now (one-cycle retention)
        if _is_rolled(tier) and len(chain) > 0:
            archive_name = "seal_t%d_archive.jsonl" % tier
            _archive_and_clear(TIER_FILES[tier], archive_name)
            _clear_rolled(tier)
            chain = load_chain(TIER_FILES[tier])

        # Seal Tier 0 every cycle; higher tiers only during rollup
        if tier == 0:
            h, e = seal_tier(0)
            h0, e0 = h, e

        # Check if this tier should roll up to the next
        chain = load_chain(TIER_FILES[tier])
        if limit is not None and len(chain) >= limit:
            heads = [e["head"] for e in chain]
            h_next, e_next = seal_tier(next_tier, rollup_heads=heads)
            # Mark this tier as rolled (will be cleared next cycle, not now)
            _set_rolled(tier)
            rolled.append((tier, next_tier, len(heads)))

    if 'h0' not in dir():
        h0, e0 = seal_tier(0)

    return h0, e0, rolled

def _archive_and_clear(source, archive_name):
    """Archive entries from source to archive, then clear source."""
    entries = load_chain(source)
    if not entries:
        return
    archive_path = os.path.join(BASE, archive_name)
    with open(archive_path, "a", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
    open(source, "w", encoding="utf-8").close()


def verify_chain_tier(tier):
    """Verify a specific tier's chain."""
    path = TIER_FILES[tier]
    chain = load_chain(path)
    if not chain:
        return True, None, "empty"
    if chain[0].get("prev") != "genesis":
        return False, 0, "first prev != genesis"
    for i in range(len(chain)):
        entry = chain[i]
        prev = "genesis" if i == 0 else chain[i - 1].get("head")
        if entry.get("prev") != prev:
            return False, i, "entry %d prev mismatch" % (i + 1)

        # Reconstruct files
        tier1 = entry.get("tier1", {})
        tier2 = entry.get("tier2", {})
        files = {}
        files.update(tier1)
        files.update(tier2)
        if not files:
            files = entry.get("files", {})

        # For rollup entries, verify using rollup payload
        if "rolled_up" in entry:
            payload = prev + "\n" + json.dumps({
                "rollup": entry.get("rolled_up", []),
                "files": files,
                "segment_count": entry.get("segments", {}).get("count", 0),
            }, sort_keys=True)
        else:
            payload = prev + "\n" + json.dumps(files, sort_keys=True)

        computed = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        if computed != entry.get("head"):
            return False, i, "entry %d head mismatch" % (i + 1)

    return True, None, "intact (%d links)" % len(chain)


def verify_all():
    """Verify all tiers."""
    results = {}
    for tier in range(5):
        ok, broken, reason = verify_chain_tier(tier)
        results[tier] = (ok, reason)
    return results


def check():
    """Verify files against last non-empty tier's seal."""
    # Find highest non-empty tier
    highest = None
    for tier in range(4, -1, -1):
        chain = load_chain(TIER_FILES[tier])
        if chain:
            highest = tier
            break
    if highest is None:
        return {"status": "no_chain", "chain_ok": True, "tier": None}

    chain = load_chain(TIER_FILES[highest])
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

    # Verify chain
    chain_ok, broken_at, reason = verify_chain_tier(highest)

    return {
        "status": status,
        "sealed_at": last.get("at"),
        "head": last.get("head"),
        "tier": highest,
        "tier_name": TIER_NAMES[highest],
        "changed": changed,
        "missing": missing,
        "unchanged": unchanged,
        "new_files": new_files,
        "chain_ok": chain_ok,
        "chain_links": len(chain),
        "appended": appended,
        "tampered_files": tampered_files,
        "segments": len(segments),
    }


def head():
    """Return the canonical head (highest non-empty tier)."""
    for tier in range(4, -1, -1):
        chain = load_chain(TIER_FILES[tier])
        if chain:
            return chain[-1].get("head")
    return None


def history(n=5):
    # Show long-term history
    return load_chain(TIER_FILES[4])[-n:] or load_chain(TIER_FILES[3])[-n:] or load_chain(TIER_FILES[2])[-n:] or load_chain(TIER_FILES[1])[-n:] or load_chain(TIER_FILES[0])[-n:]


def make_append_only():
    import subprocess
    files = [os.path.basename(TIER_FILES[4])]  # only the yearly chain is append-only
    results = {}
    for name in files:
        path = os.path.join(BASE, name)
        if not os.path.exists(path):
            # Create empty file so it can be locked
            open(path, "a", encoding="utf-8").close()
            results[name] = "created (empty)"
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
        h0, e0, rolled = seal_auto()
        print("Tier 0 (10-min) sealed: %s" % h0[:16])
        for src_tier, dst_tier, count in rolled:
            print("  Rolled up Tier %d -> Tier %d (%d entries)" % (src_tier, dst_tier, count))
        if not rolled:
            print("  No rollups this cycle")
        # Print canonical head
        h = head()
        print("Canonical head: %s" % (h or "none"))
        return 0

    if cmd == "seal-0":
        tier1, tier2, segments, all_segs, new_segs, sizes, files = _compute_tier_hashes()
        chain = load_chain(TIER_FILES[0])
        prev = chain[-1]["head"] if chain else "genesis"
        payload = prev + "\n" + json.dumps(files, sort_keys=True)
        h = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        entry = {"tier": 0, "tier_name": "10-min", "n": len(chain) + 1,
                 "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                 "prev": prev, "tier1": tier1, "tier2": tier2,
                 "segments": {"count": len(all_segs), "new": new_segs},
                 "sizes": sizes, "head": h}
        with open(TIER_FILES[0], "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        print("Tier 0 sealed: %s" % h[:16])
        return 0

    if cmd == "seal-1":
        t0 = load_chain(TIER_FILES[0])
        heads = [e["head"] for e in t0] if t0 else None
        h, entry = seal_tier(1, rollup_heads=heads)
        if t0:
            _archive_and_clear(TIER_FILES[0], "seal_t0_archive.jsonl")
        print("Tier 1 sealed: rolled up %d -> %s" % (len(heads or []), h[:16]))
        return 0

    if cmd == "check":
        result = check()
        print("Status: %s (sealed at %s)" % (result["status"], result.get("sealed_at")))
        print("Tier: %s" % result.get("tier_name", "?"))
        if not result.get("chain_ok", True):
            print("CHAIN BROKEN: %s" % result.get("reason"))
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
        results = verify_all()
        all_ok = True
        for tier in range(5):
            ok, reason = results[tier]
            chain = load_chain(TIER_FILES[tier])
            if chain:
                status = "OK" if ok else "FAILED"
                print("Tier %d (%s): %s — %s" % (tier, TIER_NAMES[tier], status, reason))
                if not ok:
                    all_ok = False
        return 0 if all_ok else 1

    if cmd == "head":
        h = head()
        if h:
            print(h)
        else:
            print("No chain yet. Run: seal.py seal")
        return 0

    if cmd == "history":
        for tier in range(4, -1, -1):
            chain = load_chain(TIER_FILES[tier])
            if chain:
                print("Tier %d (%s): %d entries" % (tier, TIER_NAMES[tier], len(chain)))
                for e in chain[-3:]:
                    print("  #%d %s  head=%s" % (e["n"], e["at"], e["head"][:16]))
                break
        return 0

    if cmd == "status":
        for tier in range(5):
            chain = load_chain(TIER_FILES[tier])
            limit = TIER_LIMITS[tier]
            limit_str = str(limit) if limit else "unlimited"
            print("Tier %d (%-8s): %2d/%s entries" % (tier, TIER_NAMES[tier], len(chain), limit_str))
        print()
        cache = load_segment_cache()
        segs = get_segments()
        print("Segments: %d total, %d cached" % (len(segs), len(cache)))
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
