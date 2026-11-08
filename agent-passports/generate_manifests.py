"""Generate manifest.json for each agent passport."""
import os
import json
import hashlib

PASSPORT_DIR = os.path.dirname(os.path.abspath(__file__))

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def generate_manifest(agent_id):
    agent_dir = os.path.join(PASSPORT_DIR, agent_id)
    files = []
    for root, dirs, filenames in os.walk(agent_dir):
        for fn in filenames:
            if fn == 'manifest.json':
                continue
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, agent_dir).replace('\\', '/')
            files.append({"path": rel, "sha256": sha256_file(full)})
    files.sort(key=lambda x: x["path"])

    # Read identity
    identity_path = os.path.join(agent_dir, "identity.json")
    with open(identity_path) as f:
        identity = json.load(f)

    manifest = {
        "agent_id": agent_id,
        "passport_version": identity.get("passport_version", "1.1"),
        "generated": "2026-11-05",
        "file_count": len(files),
        "files": files,
    }

    manifest_path = os.path.join(agent_dir, "manifest.json")
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f"Generated manifest for {agent_id}: {len(files)} files")

if __name__ == "__main__":
    for agent in ["beam", "maren", "vex", "kael"]:
        generate_manifest(agent)