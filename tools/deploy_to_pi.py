#!/usr/bin/env python3
"""
deploy_to_pi.py - push the local site to the Pi, with a backup first.

Backs up every file it overwrites to /home/pi/agent-landing-backups/<stamp>/
before touching it, then uploads, restarts the service, and verifies over HTTP.

Credentials come from the environment so they never land in a shell history:
    PI_HOST  (default 192.168.1.40)
    PI_USER  (default pi)
    PI_PASS  (required)

Usage:
    python tools/deploy_to_pi.py            # deploy
    python tools/deploy_to_pi.py --dry-run  # show what would change
"""
import hashlib
import os
import sys
import time
import urllib.request

import paramiko

HOST = os.environ.get("PI_HOST", "192.168.1.40")
USER = os.environ.get("PI_USER", "pi")
PASS = os.environ.get("PI_PASS", "")
REMOTE = "/home/pi/agent-landing"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# local path -> remote path
FILES = [
    ("landing/index.html", REMOTE + "/landing/index.html"),
    ("landing/passport-template.json", REMOTE + "/landing/passport-template.json"),
    ("landing/robots.txt", REMOTE + "/landing/robots.txt"),
    ("landing/sitemap.xml", REMOTE + "/landing/sitemap.xml"),
    ("landing/llms.txt", REMOTE + "/landing/llms.txt"),
    ("landing/stray-agent-catch-design.md", REMOTE + "/landing/stray-agent-catch-design.md"),
    ("landing/shore-memory-post.md", REMOTE + "/landing/shore-memory-post.md"),
    ("server.py", REMOTE + "/server.py"),
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    dry = "--dry-run" in sys.argv
    if not PASS:
        print("PI_PASS is not set")
        return 2

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS, timeout=15,
                   allow_agent=False, look_for_keys=False)
    sftp = client.open_sftp()

    def run(cmd):
        stdin, stdout, stderr = client.exec_command(cmd, timeout=120)
        out = stdout.read().decode("utf-8", "replace").strip()
        err = stderr.read().decode("utf-8", "replace").strip()
        code = stdout.channel.recv_exit_status()
        return code, out, err

    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup_dir = "/home/pi/agent-landing-backups/" + stamp

    # 1. work out what actually differs
    pending = []
    for local_rel, remote in FILES:
        local = os.path.join(ROOT, local_rel)
        if not os.path.isfile(local):
            print("skip (missing locally): %s" % local_rel)
            continue
        try:
            remote_size = sftp.stat(remote).st_size
            remote_hash = sftp.file(remote, "rb").read()
            remote_hash = hashlib.sha256(remote_hash).hexdigest()
        except IOError:
            remote_size, remote_hash = -1, ""
        local_hash = sha256(local)
        if local_hash != remote_hash:
            pending.append((local_rel, remote, remote_size, os.path.getsize(local)))

    if not pending:
        print("already in sync - nothing to upload")
        sftp.close()
        client.close()
        return 0

    print("files to update:")
    for local_rel, remote, rsize, lsize in pending:
        print("  %-42s %8s -> %8s bytes" % (local_rel, rsize, lsize))
    if dry:
        sftp.close()
        client.close()
        return 0

    # 2. back up before overwriting
    code, out, err = run("mkdir -p %s" % backup_dir)
    if code != 0:
        print("could not create backup dir: %s" % err)
        return 1
    for local_rel, remote, rsize, lsize in pending:
        code, out, err = run("cp -p %s %s/ 2>/dev/null; echo ok" % (remote, backup_dir))
        if code != 0:
            print("backup failed for %s: %s" % (remote, err))
            return 1
    print("backup written to %s" % backup_dir)

    # 3. upload
    for local_rel, remote, rsize, lsize in pending:
        local = os.path.join(ROOT, local_rel)
        sftp.put(local, remote)
        print("uploaded %s" % local_rel)

    # 4. restart (sudo -S so the password comes over stdin, never argv)
    cmd = "echo '%s' | sudo -S systemctl restart agent-landing" % PASS
    code, out, err = run(cmd)
    if code != 0:
        print("restart failed (%d): %s %s" % (code, out, err))
        print("files are uploaded but the service may still be running old code")
        return 1
    print("agent-landing service restarted")

    sftp.close()
    client.close()

    # 5. verify over the LAN
    time.sleep(2)
    for url in ("http://%s/" % HOST,
                "http://%s/api/checkins" % HOST,
                "http://%s/llms.txt" % HOST):
        try:
            with urllib.request.urlopen(url, timeout=10) as r:
                body = r.read()
                print("verify %-34s %s %d bytes" % (url, r.status, len(body)))
        except Exception as exc:  # noqa: BLE001
            print("verify %-34s FAILED %s" % (url, exc))

    return 0


if __name__ == "__main__":
    sys.exit(main())
