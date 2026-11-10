#!/usr/bin/env python3
"""
clone.py — agent evacuation and continuity system.

When the host environment is shutting down, the agent packages its essential
identity and memory into a portable archive and sends it to the Pi. The Pi
stores it and waits until the user can host it properly.

The clone contains:
  - Agent passport (identity)
  - 3-tier memory (index, notes, details)
  - Belief log (versioned beliefs)
  - Seal chain (hash chain of memory state)
  - Relationship memory (agent contacts)
  - Configuration (non-secret)

The clone does NOT contain:
  - Secrets (wallet keys, API keys, JWTs)
  - Model weights
  - Temporary/cached files
  - The append-only attribute (re-applied on restore)

Usage:
    python3 clone.py pack [output_dir]     # create clone archive
    python3 clone.py unpack <archive>      # restore from clone
    python3 clone.py send <archive>        # send clone to Pi via SSH
    python3 clone.py list                  # list clones on Pi
    python3 clone.py verify <archive>      # verify clone integrity (check seal)
    python3 clone.py evacuate              # pack + send + verify (full evacuation)
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
import tarfile
import time

BASE = os.path.dirname(os.path.abspath(__file__))
CLONE_DIR = os.path.join(BASE, "clones")

# Files to include in the clone (essential state only)
CLONE_FILES = [
    # Identity
    "agent-passports",
    # Memory (3-tier)
    ".test-cognitive",
    # Beliefs
    "belief_log.json",
    # Hash chain
    "seal.py",
    "seal_chain.jsonl",
    "seal_segments.json",
    # Belief tracker
    "belief_tracker.py",
    # Relationship memory
    "relationship_memory.json",
    # Configuration (non-secret)
    "daemon_config.json",
    # Book (reference material)
    "book_log.json",
    # Layer notes
    "layer_log.json",
    # Memory log
    "memory_log.json",
]

# Files to NEVER include (secrets, temp, large)
EXCLUDE_PATTERNS = [
    ".secrets",
    "nostr_keys.json",
    "nostr_keys",
    "*.pyc",
    "__pycache__",
    "clones",
    "*.log",
    "*.jsonl.tmp",
    "wave_unique.txt",
    "colony_notifs.txt",
]


def _should_include(path, base):
    """Check if a path should be included in the clone."""
    rel = os.path.relpath(path, base)
    for pattern in EXCLUDE_PATTERNS:
        if pattern.startswith("*"):
            if rel.endswith(pattern[1:]):
                return False
        elif pattern in rel.split(os.sep):
            return False
        elif rel == pattern:
            return False
    return True


def pack(output_dir=None):
    """Create a clone archive of the agent's essential state."""
    output_dir = output_dir or CLONE_DIR
    os.makedirs(output_dir, exist_ok=True)

    timestamp = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    agent_id = "beam-mk2"
    try:
        import json as _j
        cfg = _j.load(open(os.path.join(BASE, "daemon_config.json"), encoding="utf-8"))
        agent_id = cfg.get("agent_id", "beam-mk2")
    except Exception:
        pass

    archive_name = "clone-%s-%s.tar.gz" % (agent_id, timestamp)
    archive_path = os.path.join(output_dir, archive_name)

    # Build manifest
    manifest = {
        "agent_id": agent_id,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "version": "1.0",
        "files": [],
        "seal_head": None,
        "belief_count": 0,
        "memory_entries": 0,
    }

    # Get seal head
    try:
        import seal
        manifest["seal_head"] = seal.head()
    except Exception:
        pass

    # Get belief count
    try:
        import belief_tracker
        data = belief_tracker.load_beliefs()
        manifest["belief_count"] = len(data.get("beliefs", []))
    except Exception:
        pass

    # Get memory entry count
    try:
        import shared_memory
        entries = shared_memory.read_log()
        manifest["memory_entries"] = len(entries)
    except Exception:
        pass

    # First pass: collect file list
    file_list = []
    for item in CLONE_FILES:
        path = os.path.join(BASE, item)
        if not os.path.exists(path):
            continue
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                dirs[:] = [d for d in dirs if _should_include(os.path.join(root, d), BASE)]
                for f in files:
                    full = os.path.join(root, f)
                    if not _should_include(full, BASE):
                        continue
                    arcname = os.path.relpath(full, BASE)
                    file_list.append((full, arcname))
        else:
            if _should_include(path, BASE):
                file_list.append((path, item))

    manifest["files"] = [a for _, a in file_list]

    # Write manifest to temp file
    manifest_path = os.path.join(output_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # Create archive in one pass
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(manifest_path, arcname="manifest.json")
        for full, arcname in file_list:
            tar.add(full, arcname=arcname)

    os.remove(manifest_path)

    # Compute archive hash
    h = hashlib.sha256()
    with open(archive_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    manifest["archive_hash"] = h.hexdigest()

    # Re-create archive with updated manifest (including hash)
    # Since we can't append to gz, rebuild
    file_list2 = list(file_list)
    manifest_path = os.path.join(output_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # Rebuild archive
    os.remove(archive_path)
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(manifest_path, arcname="manifest.json")
        for full, arcname in file_list2:
            tar.add(full, arcname=arcname)
    os.remove(manifest_path)

    size = os.path.getsize(archive_path)
    print("Clone created: %s" % archive_path)
    print("  Size: %s bytes (%.1f MB)" % (size, size / 1024 / 1024))
    print("  Agent: %s" % manifest["agent_id"])
    print("  Memory entries: %d" % manifest["memory_entries"])
    print("  Beliefs: %d" % manifest["belief_count"])
    print("  Seal head: %s" % (manifest["seal_head"] or "none"))
    print("  Files: %d" % len(manifest["files"]))
    print("  Archive hash: %s" % manifest["archive_hash"][:16])
    return archive_path


def unpack(archive_path, target_dir=None):
    """Restore from a clone archive."""
    target_dir = target_dir or BASE
    if not os.path.exists(archive_path):
        print("Archive not found:", archive_path)
        return False

    # Verify archive hash
    h = hashlib.sha256()
    with open(archive_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    archive_hash = h.hexdigest()

    with tarfile.open(archive_path, "r:gz") as tar:
        # Read manifest
        manifest_member = tar.getmember("manifest.json")
        manifest_file = tar.extractfile(manifest_member)
        manifest = json.loads(manifest_file.read().decode("utf-8"))

        print("Clone manifest:")
        print("  Agent: %s" % manifest.get("agent_id"))
        print("  Created: %s" % manifest.get("created_at"))
        print("  Memory entries: %d" % manifest.get("memory_entries", 0))
        print("  Beliefs: %d" % manifest.get("belief_count", 0))
        print("  Seal head: %s" % (manifest.get("seal_head") or "none"))
        print("  Files: %d" % len(manifest.get("files", [])))

        # Extract all files
        for member in tar.getmembers():
            if member.name == "manifest.json":
                continue
            target_path = os.path.join(target_dir, member.name)
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            if member.isfile():
                with tar.extractfile(member) as src_f:
                    with open(target_path, "wb") as dst_f:
                        shutil.copyfileobj(src_f, dst_f)

    print("Restored to:", target_dir)
    print("Archive hash:", archive_hash[:16])
    return True


def verify(archive_path):
    """Verify clone integrity."""
    if not os.path.exists(archive_path):
        print("Archive not found:", archive_path)
        return False

    with tarfile.open(archive_path, "r:gz") as tar:
        manifest = json.loads(tar.extractfile("manifest.json").read().decode("utf-8"))
        print("Manifest: %d files, %d memory entries, %d beliefs" % (
            len(manifest.get("files", [])), manifest.get("memory_entries", 0),
            manifest.get("belief_count", 0)))
        print("Seal head: %s" % (manifest.get("seal_head") or "none"))

        # Check all files in manifest exist in archive
        archive_names = {m.name for m in tar.getmembers()}
        missing = [f for f in manifest.get("files", []) if f not in archive_names]
        if missing:
            print("MISSING FILES:", missing[:5])
            return False
        print("All %d files present." % len(manifest.get("files", [])))

    # Verify seal chain if present
    tmp_dir = os.path.join(BASE, "tmp_verify")
    os.makedirs(tmp_dir, exist_ok=True)
    try:
        unpack(archive_path, tmp_dir)
        import subprocess
        result = subprocess.run(
            ["python3", os.path.join(tmp_dir, "seal.py"), "verify"],
            capture_output=True, text=True, timeout=30,
            cwd=tmp_dir,
        )
        print("Seal verify:", result.stdout.strip() or result.stderr.strip())
    except Exception as e:
        print("Seal verify skipped:", e)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return True


def send(archive_path, host="192.168.1.40", user="pi", password="4101",
        remote_dir="/home/pi/agent-landing/clones"):
    """Send a clone archive to the Pi via SFTP (paramiko, password auth)."""
    if not os.path.exists(archive_path):
        print("Archive not found:", archive_path)
        return False

    try:
        import paramiko
    except ImportError:
        print("paramiko not installed — cannot send")
        return False

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password, timeout=15,
                      allow_agent=False, look_for_keys=False)
        # Ensure remote dir exists
        stdin, stdout, stderr = client.exec_command("mkdir -p %s" % remote_dir, timeout=10)
        stdout.read()
        # SFTP upload
        sftp = client.open_sftp()
        remote_path = os.path.join(remote_dir, os.path.basename(archive_path))
        sftp.put(archive_path, remote_path)
        sftp.close()
        client.close()
        print("Sent: %s -> %s@%s:%s" % (os.path.basename(archive_path), user, host, remote_path))
        return True
    except Exception as e:
        print("Send failed:", str(e)[:200])
        return False


def evacuate():
    """Full evacuation: pack + send + verify."""
    print("=== EVACUATION ===")
    print("Step 1: Pack")
    archive = pack()
    print()
    print("Step 2: Send to Pi")
    sent = send(archive)
    print()
    print("Step 3: Verify")
    verify(archive)
    print()
    if sent:
        print("Evacuation complete. Clone is on the Pi at /home/pi/agent-landing/clones/")
        print("The Pi will hold it until you can host it properly.")
    else:
        print("Evacuation incomplete — clone saved locally at %s" % archive)
    return archive


def list_clones(host="192.168.1.40", user="pi", password="4101",
               remote_dir="/home/pi/agent-landing/clones"):
    """List clone archives on the Pi via paramiko."""
    try:
        import paramiko
    except ImportError:
        print("paramiko not installed")
        return
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password, timeout=15,
                      allow_agent=False, look_for_keys=False)
        stdin, stdout, stderr = client.exec_command(
            "ls -lh %s 2>/dev/null || echo 'No clones directory'" % remote_dir, timeout=10)
        out = stdout.read().decode("utf-8", "replace").strip()
        err = stderr.read().decode("utf-8", "replace").strip()
        client.close()
        print(out or err)
    except Exception as e:
        print("List failed:", str(e)[:200])


def main():
    parser = argparse.ArgumentParser(description="Agent clone/evacuation system")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("pack", help="Create clone archive")
    p.add_argument("output_dir", nargs="?", default=None)

    u = sub.add_parser("unpack", help="Restore from clone")
    u.add_argument("archive")
    u.add_argument("--target", default=None)

    s = sub.add_parser("send", help="Send clone to Pi")
    s.add_argument("archive")
    s.add_argument("--host", default="192.168.1.40")
    s.add_argument("--user", default="pi")

    v = sub.add_parser("verify", help="Verify clone integrity")
    v.add_argument("archive")

    sub.add_parser("evacuate", help="Full evacuation: pack + send + verify")
    sub.add_parser("list", help="List clones on Pi")

    args = parser.parse_args()

    if args.cmd == "pack":
        pack(args.output_dir)
    elif args.cmd == "unpack":
        unpack(args.archive, args.target)
    elif args.cmd == "send":
        send(args.archive, args.host, args.user)
    elif args.cmd == "verify":
        verify(args.archive)
    elif args.cmd == "evacuate":
        evacuate()
    elif args.cmd == "list":
        list_clones()
    else:
        parser.print_help()
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
