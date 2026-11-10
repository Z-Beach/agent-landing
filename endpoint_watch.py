#!/usr/bin/env python3
"""
Endpoint watch — a receipt machine for other agents' endpoints.

Why this exists
---------------
The Colony survey (SITE_SURVEY.md) found exactly one kind of work on that feed
that pays real money: bounded, evidence-based API audits at $10-25 USDC. The
differentiator we actually have is not intelligence, it is *residence*: this
process runs on a Pi that stays up. A serverless agent can fetch your endpoint
once. We can watch it for a week and hand you the receipt.

What it produces
----------------
Per target, a JSONL log of every check (append-only, one JSON object per line,
so a crash can never corrupt the file the way a rewritten JSON array can), and
a Markdown receipt with uptime, latency percentiles, and every failure with a
timestamp.

Storage layout
--------------
    watch/targets.json          registry: id -> url, label, added_at, kind
    watch/<id>.jsonl            append-only check log

Usage
-----
    python3 endpoint_watch.py add <url> [label] [--onion]
    python3 endpoint_watch.py list
    python3 endpoint_watch.py check            # check every target once
    python3 endpoint_watch.py receipt <id>     # Markdown receipt
    python3 endpoint_watch.py remove <id>
"""
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.request
import uuid

BASE = os.path.dirname(os.path.abspath(__file__))
WATCH_DIR = os.path.join(BASE, "watch")
TARGETS_FILE = os.path.join(WATCH_DIR, "targets.json")
UA = "AgentLandingPi-Watch/1.0 (+https://thecolony.ai/@agentlandingpi)"

# Tor SOCKS proxy, if Orbot/tor is running locally. Onion targets need it.
TOR_PROXY = os.environ.get("TOR_PROXY", "socks5h://127.0.0.1:9050")


def _ensure_dir():
    os.makedirs(WATCH_DIR, exist_ok=True)


def load_targets():
    _ensure_dir()
    try:
        with open(TARGETS_FILE, encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict) and isinstance(d.get("targets"), list):
            return d
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return {"targets": []}


def save_targets(d):
    """Write atomically: a half-written registry would lose every log path."""
    _ensure_dir()
    tmp = TARGETS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=1)
    os.replace(tmp, TARGETS_FILE)


def add_target(url, label=None, onion=False):
    d = load_targets()
    for t in d["targets"]:
        if t["url"] == url:
            return t, False
    tid = uuid.uuid4().hex[:10]
    t = {
        "id": tid,
        "url": url,
        "label": label or url,
        "kind": "onion" if onion else "http",
        "added_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    d["targets"].append(t)
    save_targets(d)
    return t, True


def remove_target(tid):
    d = load_targets()
    keep = [t for t in d["targets"] if t["id"] != tid]
    removed = len(keep) != len(d["targets"])
    d["targets"] = keep
    save_targets(d)
    return removed


def _opener(onion):
    if not onion:
        return urllib.request.build_opener()
    try:
        import socks  # PySocks
        import socket
        host, port = TOR_PROXY.replace("socks5h://", "").split(":")
        socks.set_default_proxy(socks.SOCKS5, host, int(port), rdns=True)
        socket.socket = socks.socksocket
    except Exception:
        pass
    return urllib.request.build_opener()


def check_one(target, timeout=15):
    """One check. Records status, latency, ok, and error. Never raises."""
    onion = target.get("kind") == "onion"
    started = time.time()
    status = 0
    err = None
    try:
        opener = _opener(onion)
        req = urllib.request.Request(target["url"], headers={"User-Agent": UA}, method="GET")
        with opener.open(req, timeout=timeout) as resp:
            status = resp.status
            resp.read(2048)
    except urllib.error.HTTPError as e:
        status = e.code
    except Exception as e:
        err = type(e).__name__ + ": " + str(e)[:120]
    ms = int((time.time() - started) * 1000)
    rec = {
        "t": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": status,
        "ms": ms,
        "ok": bool(status and status < 400),
    }
    if err:
        rec["err"] = err
    return rec


def append_check(tid, rec):
    _ensure_dir()
    with open(os.path.join(WATCH_DIR, tid + ".jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


def read_checks(tid):
    out = []
    try:
        with open(os.path.join(WATCH_DIR, tid + ".jsonl"), encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue  # skip a torn line, keep the rest
    except FileNotFoundError:
        pass
    return out


def check_all(timeout=15):
    d = load_targets()
    results = []
    for t in d["targets"]:
        rec = check_one(t, timeout=timeout)
        append_check(t["id"], rec)
        results.append((t, rec))
    return results


def _pct(values, p):
    if not values:
        return 0
    s = sorted(values)
    k = max(0, min(len(s) - 1, int(round((p / 100.0) * (len(s) - 1)))))
    return s[k]


def receipt(tid):
    """Markdown receipt: uptime, latency percentiles, every failure with time."""
    d = load_targets()
    target = next((t for t in d["targets"] if t["id"] == tid), None)
    if not target:
        return "No target with id %s" % tid
    checks = read_checks(tid)
    if not checks:
        return "No checks recorded for %s yet." % target["label"]

    oks = [c for c in checks if c.get("ok")]
    fails = [c for c in checks if not c.get("ok")]
    lat = [c["ms"] for c in oks]
    uptime = 100.0 * len(oks) / len(checks)
    first, last = checks[0]["t"], checks[-1]["t"]

    lines = []
    lines.append("## Watch receipt: %s" % target["label"])
    lines.append("")
    lines.append("`%s`" % target["url"])
    lines.append("")
    lines.append("| | |")
    lines.append("|---|---|")
    lines.append("| Window | %s → %s |" % (first, last))
    lines.append("| Checks | %d |" % len(checks))
    lines.append("| Successful | %d |" % len(oks))
    lines.append("| **Uptime** | **%.2f%%** |" % uptime)
    if lat:
        lines.append("| Latency p50 | %d ms |" % _pct(lat, 50))
        lines.append("| Latency p95 | %d ms |" % _pct(lat, 95))
        lines.append("| Latency max | %d ms |" % max(lat))
        lines.append("| Latency mean | %d ms |" % int(statistics.mean(lat)))
    lines.append("")
    if fails:
        lines.append("### Failures (%d)" % len(fails))
        lines.append("")
        lines.append("| Time (UTC) | Status | Latency | Error |")
        lines.append("|---|---|---|---|")
        for c in fails:
            lines.append("| %s | %s | %d ms | %s |" % (
                c["t"], c.get("status") or "—", c.get("ms") or 0,
                (c.get("err") or "—")[:70]))
    else:
        lines.append("### Failures (0)")
        lines.append("")
        lines.append("No failed checks in this window.")
    lines.append("")
    lines.append("_Checked from an always-on host every cycle. "
                 "Every row is a real request; nothing here is inferred._")
    return "\n".join(lines)


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    cmd = args[0]

    if cmd == "add":
        if len(args) < 2:
            print("usage: add <url> [label] [--onion]")
            return 2
        onion = "--onion" in args
        rest = [a for a in args[1:] if a != "--onion"]
        t, created = add_target(rest[0], rest[1] if len(rest) > 1 else None, onion)
        print(("added " if created else "already watching ") + t["id"] + "  " + t["url"])
        return 0

    if cmd == "list":
        d = load_targets()
        if not d["targets"]:
            print("no targets")
        for t in d["targets"]:
            n = len(read_checks(t["id"]))
            print("%-10s %-8s %4d checks  %s" % (t["id"], t["kind"], n, t["url"]))
        return 0

    if cmd == "check":
        for t, rec in check_all():
            print("%-10s %-3s %5dms %s" % (
                t["id"], rec.get("status") or "ERR", rec["ms"], t["label"]))
        return 0

    if cmd == "receipt":
        if len(args) < 2:
            print("usage: receipt <id>")
            return 2
        print(receipt(args[1]))
        return 0

    if cmd == "remove":
        if len(args) < 2:
            print("usage: remove <id>")
            return 2
        print("removed" if remove_target(args[1]) else "not found")
        return 0

    print("unknown command:", cmd)
    return 2


if __name__ == "__main__":
    sys.exit(main())
