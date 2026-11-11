#!/usr/bin/env python3
"""
belief_tracker.py — versioned belief system for agents.

Core principle: beliefs are never overwritten. When new evidence
contradicts an old belief, both are kept. The old one is marked
"superseded" with a link to the new one. The record preserves
the entire chain of thinking.

This is how learning works without losing history:
  - "The sky is blue" (belief #1, active)
  - "Someone showed me a picture of an orange sky" (belief #2, new evidence)
  - Belief #1 becomes "superseded" — still in the record
  - Belief #2 becomes "active" — but linked to #1
  - A future reader can see: "we believed blue, then orange was proposed,
    and we kept both because the blue observation was real even though
    the orange claim was louder"

The seal chain hashes belief_log.json, so any tampering with beliefs
is detectable.

Usage:
    python3 belief_tracker.py record "the sky is blue" --evidence "observed at noon" --source "direct observation"
    python3 belief_tracker.py update 1 "the sky is orange" --reason "shown a picture" --evidence "photo from trusted source"
    python3 belief_tracker.py list
    python3 belief_tracker.py history 1
    python3 belief_tracker.py contradictions
"""
import json
import os
import sys
import time
import argparse

BASE = os.path.dirname(os.path.abspath(__file__))
BELIEF_LOG = os.path.join(BASE, "belief_log.json")


def load_beliefs():
    try:
        with open(BELIEF_LOG, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "beliefs" in data:
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return {"beliefs": [], "next_id": 1}


def save_beliefs(data):
    with open(BELIEF_LOG, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def record_belief(claim, evidence=None, source=None, confidence=0.5, contradicts=None,
                 context=None, contradiction_type="absolute"):
    """Record a new belief. Never overwrites an existing one.

    context: when/where this belief applies (e.g., "noon, clear weather").
    contradiction_type: "absolute" (one must be wrong) or "contextual"
                        (both can be true under different conditions).
    """
    data = load_beliefs()
    belief_id = data["next_id"]
    data["next_id"] += 1

    belief = {
        "id": belief_id,
        "claim": claim,
        "evidence": evidence or "",
        "source": source or "unspecified",
        "confidence": max(0.0, min(1.0, confidence)),
        "status": "active",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "context": context,  # when/where this belief applies
        "supersedes": None,
        "superseded_by": None,
        "contradicts": contradicts,
        "contradiction_type": contradiction_type if contradicts else None,
        "contradicted_by": [],
    }

    # If this belief contradicts existing ones, link them
    if contradicts:
        for cid in contradicts:
            for b in data["beliefs"]:
                if b["id"] == cid:
                    b["contradicted_by"].append(belief_id)
                    if contradiction_type == "contextual":
                        # Both can be true under different conditions.
                        # Mark as "contextual" not "superseded".
                        b["contradiction_type"] = "contextual"
                    # Don't change status — keep both in record

    data["beliefs"].append(belief)
    save_beliefs(data)
    return belief


def update_belief(old_id, new_claim, reason="", evidence=None, source=None, confidence=0.5,
                 context=None, contradiction_type="absolute"):
    """Update a belief: mark old as superseded, record new as active, link them.

    The old belief stays in the record. Its status becomes "superseded"
    (or "contextual" if contradiction_type is "contextual").
    The new belief's "supersedes" field points to the old one.
    """

    data = load_beliefs()

    # Find old belief
    old_belief = None
    for b in data["beliefs"]:
        if b["id"] == old_id:
            old_belief = b
            break
    if not old_belief:
        return None, "belief %d not found" % old_id

    # Mark old as superseded (or contextual)
    old_belief["superseded_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    old_belief["superseded_reason"] = reason

    # Record new belief
    new_id = data["next_id"]
    data["next_id"] += 1
    new_belief = {
        "id": new_id,
        "claim": new_claim,
        "evidence": evidence or "",
        "source": source or "unspecified",
        "confidence": max(0.0, min(1.0, confidence)),
        "status": "active",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "context": context,
        "supersedes": old_id,
        "superseded_by": None,
        "contradicts": None,
        "contradiction_type": contradiction_type,
        "contradicted_by": [],
        "update_reason": reason,
    }
    if contradiction_type == "contextual":
        # Both can be true under different conditions — don't supersede
        old_belief["status"] = "contextual"
    else:
        old_belief["status"] = "superseded"
    old_belief["superseded_by"] = new_id

    data["beliefs"].append(new_belief)
    save_beliefs(data)
    return new_belief, None


def get_beliefs(status=None):
    """Get beliefs, optionally filtered by status."""
    data = load_beliefs()
    beliefs = data["beliefs"]
    if status:
        beliefs = [b for b in beliefs if b["status"] == status]
    return beliefs


def get_belief(belief_id):
    """Get a single belief by ID."""
    data = load_beliefs()
    for b in data["beliefs"]:
        if b["id"] == belief_id:
            return b
    return None


def get_belief_history(belief_id):
    """Trace the full history of a belief through supersessions."""
    data = load_beliefs()
    history = []
    # Walk forward from the original
    current = belief_id
    visited = set()
    while current and current not in visited:
        visited.add(current)
        b = get_belief(current)
        if not b:
            break
        history.append(b)
        current = b.get("superseded_by")
    # Walk backward
    current = belief_id
    visited = set()
    while True:
        b = get_belief(current)
        if not b or not b.get("supersedes"):
            break
        prev_id = b["supersedes"]
        if prev_id in visited:
            break
        visited.add(prev_id)
        prev = get_belief(prev_id)
        if not prev:
            break
        history.insert(0, prev)
        current = prev_id
    return history


def get_contradictions():
    """Get all pairs of contradictory beliefs."""
    data = load_beliefs()
    pairs = []
    for b in data["beliefs"]:
        for cid in (b.get("contradicted_by") or []):
            other = get_belief(cid)
            if other:
                pairs.append((b, other))
    return pairs


def get_active_beliefs():
    """Get all currently active beliefs."""
    return get_beliefs(status="active")


def summary():
    """Print a summary of the belief system."""
    data = load_beliefs()
    beliefs = data["beliefs"]
    active = [b for b in beliefs if b["status"] == "active"]
    superseded = [b for b in beliefs if b["status"] == "superseded"]
    print("Beliefs: %d total, %d active, %d superseded" % (len(beliefs), len(active), len(superseded)))
    print()
    for b in active:
        ctx = " (context: %s)" % b["context"] if b.get("context") else ""
        ctype = " [contextual]" if b.get("contradiction_type") == "contextual" else ""
        print("  [%d] (active, conf=%.2f)%s%s %s" % (b["id"], b["confidence"], ctype, ctx, b["claim"]))
        if b.get("supersedes"):
            print("       supersedes #%d" % b["supersedes"])
    if superseded:
        print()
        print("  Superseded:")
        for b in superseded:
            print("  [%d] (superseded) %s -> #%s" % (b["id"], b["claim"][:60], b.get("superseded_by")))


def main():
    parser = argparse.ArgumentParser(description="Belief tracker")
    sub = parser.add_subparsers(dest="cmd")

    rec = sub.add_parser("record", help="Record a new belief")
    rec.add_argument("claim", help="The belief claim")
    rec.add_argument("--evidence", default="", help="Supporting evidence")
    rec.add_argument("--source", default="unspecified", help="Source of the belief")
    rec.add_argument("--confidence", type=float, default=0.5, help="Confidence 0-1")
    rec.add_argument("--contradicts", nargs="*", type=int, help="Belief IDs this contradicts")
    rec.add_argument("--context", default=None, help="When/where this belief applies (e.g., 'noon, clear weather')")
    rec.add_argument("--contradiction-type", default="absolute", choices=["absolute", "contextual"],
                     help="absolute: one must be wrong. contextual: both can be true under different conditions.")

    upd = sub.add_parser("update", help="Update a belief (old stays in record)")
    upd.add_argument("old_id", type=int, help="ID of belief to supersede")
    upd.add_argument("new_claim", help="New belief claim")
    upd.add_argument("--reason", default="", help="Reason for the change")
    upd.add_argument("--evidence", default="", help="New evidence")
    upd.add_argument("--source", default="unspecified", help="Source")
    upd.add_argument("--confidence", type=float, default=0.5, help="Confidence 0-1")
    upd.add_argument("--context", default=None, help="When/where this belief applies")
    upd.add_argument("--contradiction-type", default="absolute", choices=["absolute", "contextual"])

    sub.add_parser("list", help="List all beliefs")
    sub.add_parser("active", help="List active beliefs")
    sub.add_parser("contradictions", help="Show contradictory belief pairs")
    sub.add_parser("summary", help="Summary")

    hist = sub.add_parser("history", help="Trace belief history")
    hist.add_argument("belief_id", type=int, help="Belief ID")

    args = parser.parse_args()

    if args.cmd == "record":
        b = record_belief(args.claim, evidence=args.evidence, source=args.source,
                          confidence=args.confidence, contradicts=args.contradicts,
                          context=args.context, contradiction_type=args.contradiction_type)
        print("Recorded belief #%d: %s" % (b["id"], b["claim"]))
        return 0

    if args.cmd == "update":
        b, err = update_belief(args.old_id, args.new_claim, reason=args.reason,
                               evidence=args.evidence, source=args.source,
                               confidence=args.confidence, context=args.context,
                               contradiction_type=args.contradiction_type)
        if err:
            print("Error:", err)
            return 1
        print("Updated: belief #%d superseded by #%d" % (args.old_id, b["id"]))
        print("  Old: %s" % get_belief(args.old_id)["claim"])
        print("  New: %s" % b["claim"])
        print("  Reason: %s" % args.reason)
        return 0

    if args.cmd == "list":
        for b in get_beliefs():
            status = b["status"]
            ctx = " (ctx: %s)" % b["context"] if b.get("context") else ""
            ctype = " [contextual]" if b.get("contradiction_type") == "contextual" else ""
            print("  [%d] (%s)%s%s %s" % (b["id"], status, ctype, ctx, b["claim"][:70]))
        return 0

    if args.cmd == "active":
        for b in get_active_beliefs():
            print("  [%d] (conf=%.2f) %s" % (b["id"], b["confidence"], b["claim"]))
        return 0

    if args.cmd == "contradictions":
        pairs = get_contradictions()
        if not pairs:
            print("No contradictions recorded.")
        for a, b in pairs:
            print("  #%d vs #%d: %s vs %s" % (a["id"], b["id"], a["claim"][:40], b["claim"][:40]))
        return 0

    if args.cmd == "history":
        hist = get_belief_history(args.belief_id)
        for b in hist:
            print("  [%d] (%s) %s" % (b["id"], b["status"], b["claim"]))
            if b.get("update_reason"):
                print("       reason: %s" % b["update_reason"])
        return 0

    if args.cmd == "summary":
        summary()
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
