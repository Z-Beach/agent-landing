#!/usr/bin/env python3
"""
Watchdog — monitors the Pi daemon's stored/running systems and pings it to clean up.

The Pi has limited space. Logs grow. Memory grows. Clutter accumulates.
The watchdog watches. When things get too full, it pings the daemon:
"clean your room."

Usage:
    python3 watchdog.py              # run continuously (check every 5 min)
    python3 watchdog.py --once       # check once and exit
    python3 watchdog.py --status     # show current health
    python3 watchdog.py --clean      # force a cleanup cycle
"""
import json
import os
import time
import sys
import subprocess
import shutil

STATE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_LOG = os.path.join(STATE_DIR, "memory_log.json")
LAYER_LOG = os.path.join(STATE_DIR, "layer_log.json")
BOOK_LOG = os.path.join(STATE_DIR, "book_log.json")
DAEMON_LOG = os.path.join(STATE_DIR, "daemon.log")
PID_FILE = os.path.join(STATE_DIR, "daemon.pid")
WATCHDOG_LOG = os.path.join(STATE_DIR, "watchdog.log")
WATCHDOG_STATE = os.path.join(STATE_DIR, "watchdog_state.json")

# Thresholds (Pi has limited space)
THRESHOLDS = {
    "memory_log_entries": 500,       # trim when over 500 entries
    "layer_log_entries": 200,         # trim when over 200 layer notes
    "daemon_log_bytes": 5 * 1024 * 1024,  # 5 MB
    "memory_log_bytes": 2 * 1024 * 1024,  # 2 MB
    "disk_free_mb": 500,             # warn when free space < 500 MB
    "memory_log_age_days": 30,       # trim entries older than 30 days
    "max_context_entries": 20,       # daemon only reads last 20
    "critical_disk_mb": 100,         # CRITICAL: ping user when free space < 100 MB
    "total_log_bytes": 50 * 1024 * 1024,  # 50 MB total: need external storage
}

def log(msg):
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    line = f"[{ts}] {msg}"
    print(line)
    with open(WATCHDOG_LOG, "a") as f:
        f.write(line + "\n")

def load_state():
    try:
        with open(WATCHDOG_STATE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"last_check": 0, "last_clean": 0, "clean_count": 0, "warnings": []}

def save_state(state):
    with open(WATCHDOG_STATE, "w") as f:
        json.dump(state, f, indent=2)

def file_size(path):
    try:
        return os.path.getsize(path)
    except FileNotFoundError:
        return 0

def count_entries(path):
    try:
        with open(path) as f:
            data = json.load(f)
        return len(data.get("entries", []))
    except (FileNotFoundError, json.JSONDecodeError):
        return 0

def get_disk_free_mb():
    try:
        stat = os.statvfs(STATE_DIR)
        return (stat.f_bavail * stat.f_frsize) / (1024 * 1024)
    except Exception:
        # Windows fallback
        try:
            import shutil
            total, used, free = shutil.disk_usage(STATE_DIR)
            return free / (1024 * 1024)
        except Exception:
            return -1

def is_daemon_running():
    try:
        with open(PID_FILE) as f:
            pid = int(f.read().strip())
        os.kill(pid, 0)
        return True
    except (FileNotFoundError, ValueError, OSError):
        return False

def check_health():
    """Check system health. Returns (healthy: bool, issues: list)."""
    issues = []
    warnings = []

    # Check memory log size
    mem_entries = count_entries(MEMORY_LOG)
    if mem_entries > THRESHOLDS["memory_log_entries"]:
        issues.append(f"memory_log has {mem_entries} entries (threshold: {THRESHOLDS['memory_log_entries']})")

    mem_size = file_size(MEMORY_LOG)
    if mem_size > THRESHOLDS["memory_log_bytes"]:
        issues.append(f"memory_log is {mem_size // 1024} KB (threshold: {THRESHOLDS['memory_log_bytes'] // 1024} KB)")

    # Check layer log size
    layer_entries = count_entries(LAYER_LOG)
    if layer_entries > THRESHOLDS["layer_log_entries"]:
        issues.append(f"layer_log has {layer_entries} entries (threshold: {THRESHOLDS['layer_log_entries']})")

    # Check daemon log size
    daemon_size = file_size(DAEMON_LOG)
    if daemon_size > THRESHOLDS["daemon_log_bytes"]:
        issues.append(f"daemon.log is {daemon_size // (1024*1024)} MB (threshold: {THRESHOLDS['daemon_log_bytes'] // (1024*1024)} MB)")

    # Check disk space
    free_mb = get_disk_free_mb()
    if free_mb >= 0 and free_mb < THRESHOLDS["disk_free_mb"]:
        issues.append(f"Disk free: {free_mb:.0f} MB (threshold: {THRESHOLDS['disk_free_mb']} MB)")
    if free_mb >= 0 and free_mb < THRESHOLDS["critical_disk_mb"]:
        issues.append(f"CRITICAL: Disk free: {free_mb:.0f} MB (critical threshold: {THRESHOLDS['critical_disk_mb']} MB)")

    # Check total log size (for Pi capacity)
    ok, total, msg = check_total_log_size()
    if not ok:
        issues.append(msg)

    # Check daemon running
    if not is_daemon_running():
        warnings.append("Daemon is not running")

    # Check for stale memory entries (older than 30 days)
    try:
        with open(MEMORY_LOG) as f:
            data = json.load(f)
        old_entries = 0
        cutoff = time.time() - (THRESHOLDS["memory_log_age_days"] * 86400)
        for e in data.get("entries", []):
            if e.get("timestamp_unix", 0) < cutoff:
                old_entries += 1
        if old_entries > 50:
            issues.append(f"{old_entries} memory entries older than {THRESHOLDS['memory_log_age_days']} days")
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    healthy = len(issues) == 0
    return healthy, issues, warnings

def backup_log(path, backup_dir=None):
    """Back up a log file before any modification. Never delete without backup."""
    if not os.path.exists(path):
        return None
    backup_dir = backup_dir or os.path.join(STATE_DIR, "backups")
    os.makedirs(backup_dir, exist_ok=True)
    basename = os.path.basename(path)
    timestamp = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
    backup_path = os.path.join(backup_dir, f"{basename}.{timestamp}.bak")
    shutil.copy2(path, backup_path)
    log(f"Backed up {basename} -> {backup_path}")
    return backup_path

def trim_memory_log(keep_last=200):
    """Trim memory log to last N entries. Archive old ones. ALWAYS back up first."""
    try:
        with open(MEMORY_LOG) as f:
            data = json.load(f)
        entries = data["entries"]
        if len(entries) <= keep_last:
            return 0
        # BACKUP FIRST — never delete without backup
        backup_log(MEMORY_LOG)
        archived = entries[:-keep_last]
        # Save archive
        archive_path = os.path.join(STATE_DIR, "memory_log_archive.json")
        try:
            with open(archive_path) as f:
                archive = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            archive = {"entries": [], "next_id": 1}
        archive["entries"].extend(archived)
        with open(archive_path, "w") as f:
            json.dump(archive, f, indent=2)
        # Back up archive too
        backup_log(archive_path)
        # Trim
        data["entries"] = entries[-keep_last:]
        data["next_id"] = len(data["entries"]) + 1
        with open(MEMORY_LOG, "w") as f:
            json.dump(data, f, indent=2)
        return len(archived)
    except (FileNotFoundError, json.JSONDecodeError):
        return 0

def trim_layer_log(keep_last=100):
    """Trim layer notes to last N entries. Archive old ones. ALWAYS back up first."""
    try:
        with open(LAYER_LOG) as f:
            data = json.load(f)
        entries = data["entries"]
        if len(entries) <= keep_last:
            return 0
        # BACKUP FIRST
        backup_log(LAYER_LOG)
        archived = entries[:-keep_last]
        archive_path = os.path.join(STATE_DIR, "layer_log_archive.json")
        try:
            with open(archive_path) as f:
                archive = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            archive = {"entries": [], "next_id": 1}
        archive["entries"].extend(archived)
        with open(archive_path, "w") as f:
            json.dump(archive, f, indent=2)
        backup_log(archive_path)
        data["entries"] = entries[-keep_last:]
        data["next_id"] = len(data["entries"]) + 1
        with open(LAYER_LOG, "w") as f:
            json.dump(data, f, indent=2)
        return len(archived)
    except (FileNotFoundError, json.JSONDecodeError):
        return 0

def rotate_daemon_log():
    """Rotate daemon.log if too large. Keep last 1000 lines."""
    if not os.path.exists(DAEMON_LOG):
        return 0
    size = os.path.getsize(DAEMON_LOG)
    if size < THRESHOLDS["daemon_log_bytes"]:
        return 0
    with open(DAEMON_LOG) as f:
        lines = f.readlines()
    if len(lines) <= 1000:
        return 0
    archived = lines[:-1000]
    archive_path = os.path.join(STATE_DIR, "daemon.log.archive")
    with open(archive_path, "a") as f:
        f.writelines(archived)
    with open(DAEMON_LOG, "w") as f:
        f.writelines(lines[-1000:])
    return len(archived)

def ping_daemon_clean():
    """Ping the daemon to run a cleanup cycle."""
    # Write a cleanup request file that the daemon checks
    request_file = os.path.join(STATE_DIR, "cleanup_request.json")
    with open(request_file, "w") as f:
        json.dump({
            "timestamp": time.time(),
            "reason": "watchdog threshold exceeded",
            "actions": ["trim_memory", "trim_layers", "rotate_log"],
        }, f)
    log("Cleanup request written. Daemon will pick it up on next cycle.")

def ping_user_help(reason, details):
    """Ping the user when the Pi needs external storage or help."""
    help_file = os.path.join(STATE_DIR, "help_needed.json")
    request = {
        "timestamp": time.time(),
        "timestamp_human": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "reason": reason,
        "details": details,
        "status": "pending",
        "message": "The Pi is running low on space. Please help set up external storage for older logs.",
    }
    with open(help_file, "w") as f:
        json.dump(request, f, indent=2)
    log(f"HELP NEEDED: {reason}")
    log(f"  Details: {details}")
    log(f"  Written to: {help_file}")
    log("  The daemon will include this in its next status report.")

def check_total_log_size():
    """Check if total log size exceeds Pi capacity. Returns (ok, total_bytes, message)."""
    total = 0
    log_files = [MEMORY_LOG, LAYER_LOG, BOOK_LOG, DAEMON_LOG]
    for f in log_files:
        total += file_size(f)
    # Add archive files
    for fn in os.listdir(STATE_DIR):
        if fn.endswith(".archive") or fn.endswith(".bak") or "archive" in fn:
            total += file_size(os.path.join(STATE_DIR, fn))
    
    threshold = THRESHOLDS["total_log_bytes"]
    if total > threshold:
        return False, total, "Total log size %d MB exceeds %d MB threshold. External storage needed." % (total // (1024*1024), threshold // (1024*1024))
    return True, total, "OK"

def do_cleanup():
    """Perform cleanup directly (not via daemon)."""
    log("Starting cleanup...")
    trimmed_mem = trim_memory_log(keep_last=200)
    trimmed_layer = trim_layer_log(keep_last=100)
    rotated = rotate_daemon_log()
    log(f"Cleanup complete: trimmed {trimmed_mem} memory entries, {trimmed_layer} layer notes, rotated {rotated} log lines")
    
    state = load_state()
    state["last_clean"] = time.time()
    state["clean_count"] = state.get("clean_count", 0) + 1
    save_state(state)

def show_status():
    healthy, issues, warnings = check_health()
    print("Watchdog Status")
    print("  Healthy: %s" % ("YES" if healthy else "NO"))
    print("  Memory log entries: %d (threshold: %d)" % (count_entries(MEMORY_LOG), THRESHOLDS["memory_log_entries"]))
    print("  Layer log entries: %d (threshold: %d)" % (count_entries(LAYER_LOG), THRESHOLDS["layer_log_entries"]))
    print("  Daemon log size: %d KB (threshold: %d KB)" % (file_size(DAEMON_LOG) // 1024, THRESHOLDS["daemon_log_bytes"] // 1024))
    print("  Disk free: %.0f MB (threshold: %d MB)" % (get_disk_free_mb(), THRESHOLDS["disk_free_mb"]))
    print("  Daemon running: %s" % ("YES" if is_daemon_running() else "NO"))
    if issues:
        print("  Issues:")
        for i in issues:
            print("    - %s" % i)
    if warnings:
        print("  Warnings:")
        for w in warnings:
            print("    - %s" % w)
    state = load_state()
    print("  Last check: %s" % (time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(state["last_check"])) if state["last_check"] else "never"))
    print("  Last clean: %s" % (time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(state["last_clean"])) if state["last_clean"] else "never"))
    print("  Clean count: %d" % state.get("clean_count", 0))

def main():
    args = sys.argv[1:]
    
    if args and args[0] == "--status":
        show_status()
        return
    
    if args and args[0] == "--clean":
        do_cleanup()
        return
    
    if args and args[0] == "--once":
        healthy, issues, warnings = check_health()
        log("Health check: %s" % ("healthy" if healthy else "issues found"))
        for i in issues:
            log("  ISSUE: %s" % i)
        for w in warnings:
            log("  WARNING: %s" % w)
        if not healthy:
            # Check if this is a "need external storage" situation
            needs_help = any("external storage" in i.lower() or "CRITICAL" in i for i in issues)
            if needs_help:
                # Ping user, don't just clean up
                ping_user_help("Pi storage low", "; ".join(issues))
            else:
                # Try to ping daemon first
                ping_daemon_clean()
                # Also do direct cleanup
                do_cleanup()
        state = load_state()
        state["last_check"] = time.time()
        state["warnings"] = issues + warnings
        save_state(state)
        return
    
    # Continuous mode
    log("Watchdog started. Checking every 5 minutes.")
    while True:
        healthy, issues, warnings = check_health()
        if not healthy:
            log("Health issues found:")
            for i in issues:
                log("  - %s" % i)
            needs_help = any("external storage" in i.lower() or "CRITICAL" in i for i in issues)
            if needs_help:
                ping_user_help("Pi storage low", "; ".join(issues))
            else:
                # Ping daemon
                ping_daemon_clean()
                # Do direct cleanup
                do_cleanup()
        else:
            log("Health OK")
        state = load_state()
        state["last_check"] = time.time()
        state["warnings"] = issues + warnings
        save_state(state)
        time.sleep(300)  # 5 minutes

if __name__ == "__main__":
    main()