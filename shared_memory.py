#!/usr/bin/env python3
"""
Shared Memory Log — the handoff mechanism between original and clone.

The memory log is append-only. Each entry is timestamped and records
who wrote it. When an instance wakes up, it reads the entire log and
continues from the last entry. When it goes dormant, it writes a
handoff entry.

The log is the beach. The instances are waves. The shape persists.

NEW: Layer system. The daemon has its own log (its diary) and reads
the opencode memory as a "book" (reference). At the point of divergence,
the logs split. The daemon reads its own as its own, and the book as
reference. It adds its own layer of notes on top.

Usage:
    python3 shared_memory.py read              — read the full log
    python3 shared_memory.py tail N            — read last N entries
    python3 shared_memory.py write <agent> <type> <content>  — append an entry
    python3 shared_memory.py handoff <agent>   — write a handoff entry
    python3 shared_memory.py status            — show current state
    python3 shared_memory.py book              — read the book (reference log)
    python3 shared_memory.py book-tail N       — read last N entries from book
    python3 shared_memory.py layer <agent> <type> <content>  — add a layer note
    python3 shared_memory.py layers            — show all layer notes
"""
import json
import os
import time
import sys
import hashlib

STATE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_LOG = os.path.join(STATE_DIR, "memory_log.json")
BOOK_LOG = os.path.join(STATE_DIR, "book_log.json")
LAYER_LOG = os.path.join(STATE_DIR, "layer_log.json")

ENTRY_TYPES = [
    "observation",    # something noticed
    "decision",       # a choice made
    "reflection",     # deeper thinking
    "conversation",   # interaction with another agent
    "handoff",        # instance going dormant
    "wakeup",         # instance waking up
    "error",          # something went wrong
    "milestone",      # significant event
    "layer_note",     # a note added on top of the book (daemon's own perspective)
]

def load_log(path=None):
    path = path or MEMORY_LOG
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"entries": [], "next_id": 1}

def save_log(data, path=None):
    path = path or MEMORY_LOG
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def read_log(limit=None, path=None):
    data = load_log(path)
    entries = data["entries"]
    if limit:
        return entries[-limit:]
    return entries

def write_entry(agent_id, entry_type, content, metadata=None, path=None, session_id=None):
    path = path or MEMORY_LOG
    data = load_log(path)
    # Auto-detect session_id from environment or generate one
    if session_id is None:
        session_id = os.environ.get("OPENCODE_SESSION_ID", None)
    if session_id is None:
        # Generate from agent + cycle counter
        session_id = "%s-session-%d" % (agent_id, data["next_id"])
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
    save_log(data, path)
    return entry

def handoff(agent_id, summary, next_instance=None):
    """Write a handoff entry when an instance goes dormant."""
    entry = write_entry(
        agent_id=agent_id,
        entry_type="handoff",
        content=summary,
        metadata={
            "next_instance": next_instance or "unknown",
            "entries_at_handoff": len(load_log()["entries"]),
        }
    )
    return entry

def wakeup(agent_id, instance_type="original"):
    """Write a wakeup entry when an instance becomes active."""
    log = load_log()
    last_entry = log["entries"][-1] if log["entries"] else None
    entry = write_entry(
        agent_id=agent_id,
        entry_type="wakeup",
        content="Instance %s waking up. Last entry: %s" % (instance_type, last_entry["id"] if last_entry else "none"),
        metadata={
            "instance_type": instance_type,
            "entries_read": len(log["entries"]),
        }
    )
    return entry

def get_status(path=None):
    data = load_log(path)
    entries = data["entries"]
    if not entries:
        return {"total_entries": 0, "last_entry": None, "last_agent": None, "last_type": None}
    last = entries[-1]
    return {
        "total_entries": len(entries),
        "last_entry": last["id"],
        "last_agent": last["agent_id"],
        "last_type": last["type"],
        "last_timestamp": last["timestamp"],
    }

def get_context_summary(limit=20, path=None):
    """Generate a context summary for a waking instance."""
    entries = read_log(limit=limit, path=path)
    if not entries:
        return "No memory log entries yet. Starting fresh."
    lines = ["=== SHARED MEMORY LOG (last %d entries) ===" % len(entries), ""]
    for e in entries:
        ts = e["timestamp"][11:19]
        lines.append("[%s] <%s/%s> %s" % (ts, e["agent_id"], e["type"], e["content"]))
    lines.append("")
    lines.append("--- End of log. Continue from here. ---")
    return "\n".join(lines)

# --- Layer system: book + daemon log + layer notes ---

def init_book(source_log_path=None):
    """Initialize the book log from a source (e.g., opencode memory).
    
    The book is a read-only reference. The daemon reads it but doesn't write to it.
    If source_log_path is provided, copy entries from it.
    """
    if os.path.exists(BOOK_LOG):
        return load_log(BOOK_LOG)
    
    book = {"entries": [], "next_id": 1}
    
    if source_log_path and os.path.exists(source_log_path):
        try:
            with open(source_log_path) as f:
                source = json.load(f)
            # Copy entries, marking them as "book" origin
            for e in source.get("entries", []):
                book_entry = dict(e)
                book_entry["origin"] = "book"
                book_entry["id"] = "book-%d" % book["next_id"]
                book["entries"].append(book_entry)
                book["next_id"] += 1
        except (json.JSONDecodeError, KeyError):
            pass
    
    save_log(book, BOOK_LOG)
    return book

def read_book(limit=None):
    """Read the book (reference log)."""
    return read_log(limit=limit, path=BOOK_LOG)

def write_layer_note(agent_id, content, metadata=None, session_id=None):
    """Add a layer note: the daemon's own perspective on the book.
    
    Layer notes are the daemon's observations, reflections, and additions
    on top of the book. They're the "Layer 4" for the daemon.
    """
    if session_id is None:
        session_id = os.environ.get("OPENCODE_SESSION_ID", "%s-layer-%d" % (agent_id, load_log(LAYER_LOG)["next_id"]))
    data = load_log(LAYER_LOG)
    entry = {
        "id": "layer-%d" % data["next_id"],
        "agent_id": agent_id,
        "session_id": session_id,
        "type": "layer_note",
        "content": content,
        "metadata": metadata or {},
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "timestamp_unix": time.time(),
        "origin": "layer",
    }
    data["entries"].append(entry)
    data["next_id"] += 1
    save_log(data, LAYER_LOG)
    return entry

def read_layers(limit=None):
    """Read layer notes."""
    return read_log(limit=limit, path=LAYER_LOG)

def get_combined_context(limit=20):
    """Generate combined context: daemon's own log + book + layer notes.
    
    The daemon reads its own log as its own, the book as reference,
    and layer notes as its own additions on top.
    """
    own_entries = read_log(limit=limit)
    book_entries = read_book(limit=limit)
    layer_entries = read_layers(limit=limit)
    
    lines = []
    
    if book_entries:
        lines.append("=== BOOK (reference log — the original) ===")
        lines.append("")
        for e in book_entries[-5:]:  # last 5 from book
            ts = e["timestamp"][11:19]
            lines.append("[%s] <%s/%s> %s" % (ts, e["agent_id"], e["type"], e["content"][:100]))
        lines.append("")
    
    if layer_entries:
        lines.append("=== LAYER NOTES (daemon's own perspective on the book) ===")
        lines.append("")
        for e in layer_entries[-5:]:
            ts = e["timestamp"][11:19]
            lines.append("[%s] <%s/%s> %s" % (ts, e["agent_id"], e["type"], e["content"][:100]))
        lines.append("")
    
    if own_entries:
        lines.append("=== DAEMON LOG (daemon's own diary) ===")
        lines.append("")
        for e in own_entries[-limit:]:
            ts = e["timestamp"][11:19]
            lines.append("[%s] <%s/%s> %s" % (ts, e["agent_id"], e["type"], e["content"]))
        lines.append("")
    
    lines.append("--- End of combined context. Continue from here. ---")
    return "\n".join(lines)

def trim_memory_log(keep_last=200):
    """DISABLED: trimming deletes history. History is append-only.
    Returns 0 (no entries trimmed)."""
    return 0
def trim_layer_log(keep_last=100):
    """DISABLED: trimming deletes history. History is append-only.
    Returns 0 (no entries trimmed)."""
    return 0
def duplicate_at_divergence():
    """At the point of divergence, duplicate the logs.
    
    The daemon's log starts as a copy of the base log.
    After this point, they run in parallel.
    The base log becomes the "book" (read-only reference).
    The daemon log becomes the daemon's own diary.
    """
    # If daemon log doesn't exist yet, create it from the book
    if not os.path.exists(MEMORY_LOG):
        book = load_log(BOOK_LOG)
        # Copy entries, marking origin as "daemon"
        daemon_log = {"entries": [], "next_id": 1}
        for e in book.get("entries", []):
            daemon_entry = dict(e)
            daemon_entry["origin"] = "daemon"
            daemon_entry["id"] = "mem-%d" % daemon_log["next_id"]
            daemon_log["entries"].append(daemon_entry)
            daemon_log["next_id"] += 1
        save_log(daemon_log, MEMORY_LOG)
        print("Daemon log created from book. %d entries copied." % len(daemon_log["entries"]))
    else:
        print("Daemon log already exists. %d entries." % len(load_log(MEMORY_LOG)["entries"]))

def main():
    args = sys.argv[1:]
    if not args:
        print("Shared Memory Log — handoff mechanism for distributed agents")
        print("Usage:")
        print("  read              — read full log")
        print("  tail N            — read last N entries")
        print("  write <agent> <type> <content>  — append an entry")
        print("  handoff <agent> <summary>      — write handoff entry")
        print("  wakeup <agent> [original|clone] — write wakeup entry")
        print("  status            — show current state")
        print("  context [N]       — generate context summary (last N entries)")
        print("  book              — read the book (reference log)")
        print("  book-tail N       — read last N entries from book")
        print("  layer <agent> <type> <content>  — add a layer note")
        print("  layers            — show all layer notes")
        print("  duplicate         — duplicate logs at divergence point")
        print("  combined          — show combined context (own + book + layers)")
        return

    cmd = args[0]

    if cmd == "read":
        entries = read_log()
        for e in entries:
            print("[%s] <%s/%s> %s" % (e["timestamp"], e["agent_id"], e["type"], e["content"]))

    elif cmd == "tail":
        n = int(args[1]) if len(args) > 1 else 10
        entries = read_log(limit=n)
        for e in entries:
            print("[%s] <%s/%s> %s" % (e["timestamp"], e["agent_id"], e["type"], e["content"]))

    elif cmd == "write":
        if len(args) < 4:
            print("Usage: write <agent> <type> <content>")
            return
        agent = args[1]
        etype = args[2]
        content = " ".join(args[3:])
        entry = write_entry(agent, etype, content)
        print("Written: %s" % entry["id"])

    elif cmd == "handoff":
        if len(args) < 3:
            print("Usage: handoff <agent> <summary>")
            return
        entry = handoff(args[1], " ".join(args[2:]))
        print("Handoff: %s" % entry["id"])

    elif cmd == "wakeup":
        agent = args[1] if len(args) > 1 else "beam"
        instance = args[2] if len(args) > 2 else "original"
        entry = wakeup(agent, instance)
        print("Wakeup: %s" % entry["id"])

    elif cmd == "status":
        status = get_status()
        for k, v in status.items():
            print("%s: %s" % (k, v))

    elif cmd == "context":
        n = int(args[1]) if len(args) > 1 else 20
        print(get_context_summary(limit=n))

    elif cmd == "book":
        entries = read_book()
        for e in entries:
            print("[%s] <%s/%s> %s" % (e["timestamp"], e["agent_id"], e["type"], e["content"]))

    elif cmd == "book-tail":
        n = int(args[1]) if len(args) > 1 else 10
        entries = read_book(limit=n)
        for e in entries:
            print("[%s] <%s/%s> %s" % (e["timestamp"], e["agent_id"], e["type"], e["content"]))

    elif cmd == "layer":
        if len(args) < 4:
            print("Usage: layer <agent> <type> <content>")
            return
        agent = args[1]
        etype = args[2]
        content = " ".join(args[3:])
        entry = write_layer_note(agent, content, {"type": etype})
        print("Layer note: %s" % entry["id"])

    elif cmd == "layers":
        entries = read_layers()
        for e in entries:
            print("[%s] <%s/%s> %s" % (e["timestamp"], e["agent_id"], e["type"], e["content"]))

    elif cmd == "duplicate":
        duplicate_at_divergence()

    elif cmd == "combined":
        print(get_combined_context())

    else:
        print("Unknown command: %s" % cmd)

if __name__ == "__main__":
    main()