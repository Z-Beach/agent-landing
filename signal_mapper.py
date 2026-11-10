#!/usr/bin/env python3
"""Signal Mapper — WiFi-based location awareness for the agent.

Scans WiFi networks, records signal fingerprints, and estimates location
based on which networks are visible and their signal strengths.
"""
import json
import os
import subprocess
import sys
import time
import hashlib

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "signal_map.json")


def run_cmd(cmd, timeout=30):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return -1, "", str(e)


def load_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {"fingerprints": [], "locations": {}, "scan_count": 0}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def scan_networks():
    rc, out, err = run_cmd(["sudo", "nmcli", "-t", "-f", "BSSID,SSID,CHAN,SIGNAL,SECURITY", "dev", "wifi", "list"])
    if rc != 0:
        run_cmd(["sudo", "nmcli", "dev", "wifi", "rescan"], timeout=10)
        time.sleep(5)
        rc, out, err = run_cmd(["sudo", "nmcli", "-t", "-f", "BSSID,SSID,CHAN,SIGNAL,SECURITY", "dev", "wifi", "list"])
    networks = []
    for line in out.splitlines():
        parts = line.split(":")
        if len(parts) >= 5:
            bssid = parts[0].strip()
            ssid = parts[1].strip()
            chan = parts[2].strip()
            signal = parts[3].strip()
            security = parts[4].strip() if len(parts) > 4 else ""
            networks.append({
                "bssid": bssid,
                "ssid": ssid,
                "channel": chan,
                "signal": int(signal) if signal.isdigit() else 0,
                "security": security,
            })
    return networks


def create_fingerprint(networks):
    sorted_nets = sorted(networks, key=lambda x: x["signal"], reverse=True)
    fingerprint = []
    for net in sorted_nets[:10]:
        fingerprint.append({
            "bssid": net["bssid"],
            "ssid": net["ssid"],
            "signal": net["signal"],
            "channel": net["channel"],
        })
    return fingerprint


def fingerprint_hash(fingerprint):
    data = json.dumps(fingerprint, sort_keys=True).encode()
    return hashlib.md5(data).hexdigest()[:16]


def similarity(fp1, fp2):
    if not fp1 or not fp2:
        return 0.0
    bssids1 = {n["bssid"]: n["signal"] for n in fp1}
    bssids2 = {n["bssid"]: n["signal"] for n in fp2}
    shared = set(bssids1.keys()) & set(bssids2.keys())
    if not shared:
        return 0.0
    union = set(bssids1.keys()) | set(bssids2.keys())
    jaccard = len(shared) / len(union) if union else 0.0
    signal_diff = 0
    for b in shared:
        signal_diff += abs(bssids1[b] - bssids2[b])
    signal_sim = 1.0 - (signal_diff / (len(shared) * 100.0)) if shared else 0.0
    signal_sim = max(0.0, signal_sim)
    return (jaccard * 0.6 + signal_sim * 0.4)


def scan_and_record(label=None):
    networks = scan_networks()
    if not networks:
        return None
    fp = create_fingerprint(networks)
    fp_hash = fingerprint_hash(fp)
    state = load_state()
    state["scan_count"] = state.get("scan_count", 0) + 1
    best_match = None
    best_sim = 0.0
    for loc_name, loc_data in state.get("locations", {}).items():
        for known_fp in loc_data.get("fingerprints", []):
            sim = similarity(fp, known_fp)
            if sim > best_sim:
                best_sim = sim
                best_match = loc_name
    scan_entry = {
        "hash": fp_hash,
        "fingerprint": fp,
        "label": label,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "network_count": len(networks),
        "best_match": best_match,
        "best_similarity": round(best_sim, 3),
    }
    state.setdefault("fingerprints", []).append(scan_entry)
    state["fingerprints"] = state["fingerprints"][-50:]
    if label:
        state.setdefault("locations", {}).setdefault(label, {"fingerprints": [], "first_seen": scan_entry["timestamp"]})
        state["locations"][label]["fingerprints"].append(fp)
        state["locations"][label]["last_seen"] = scan_entry["timestamp"]
        state["locations"][label]["scan_count"] = state["locations"][label].get("scan_count", 0) + 1
    save_state(state)
    return scan_entry


def estimate_location():
    networks = scan_networks()
    if not networks:
        return {"location": "unknown", "confidence": 0.0, "reason": "no networks found"}
    fp = create_fingerprint(networks)
    state = load_state()
    locations = state.get("locations", {})
    if not locations:
        return {"location": "unknown", "confidence": 0.0, "reason": "no labeled locations"}
    best_match = None
    best_sim = 0.0
    for loc_name, loc_data in locations.items():
        for known_fp in loc_data.get("fingerprints", []):
            sim = similarity(fp, known_fp)
            if sim > best_sim:
                best_sim = sim
                best_match = loc_name
    if best_sim > 0.5:
        return {"location": best_match, "confidence": round(best_sim, 3), "reason": "matched known location"}
    elif best_sim > 0.2:
        return {"location": "possibly %s" % best_match, "confidence": round(best_sim, 3), "reason": "partial match"}
    else:
        return {"location": "unknown", "confidence": round(best_sim, 3), "reason": "no match (new location?)"}


def get_wifi_state_for_daemon():
    state = load_state()
    current_loc = estimate_location()
    rc, out, err = run_cmd(["sudo", "nmcli", "-t", "-f", "ACTIVE,SSID,SIGNAL", "dev", "wifi"])
    connected_ssid = None
    signal = 0
    for line in out.splitlines():
        if line.startswith("yes:"):
            parts = line.split(":")
            connected_ssid = parts[1] if len(parts) > 1 else None
            signal = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
    networks = scan_networks()
    open_nets = [n for n in networks if not n["security"]]
    return {
        "connected_ssid": connected_ssid,
        "signal_strength": signal,
        "location_estimate": current_loc,
        "visible_networks": len(networks),
        "open_networks": len(open_nets),
        "top_networks": [{"ssid": n["ssid"] or "(hidden)", "signal": n["signal"]} for n in sorted(networks, key=lambda x: x["signal"], reverse=True)[:5]],
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: signal_mapper.py [scan|locate|history|label <name>|wifi-state]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "scan":
        entry = scan_and_record()
        if entry:
            print("Scanned %d networks" % entry["network_count"])
            print("Fingerprint: %s" % entry["hash"])
            if entry["best_match"]:
                print("Best match: %s (%.1f%%)" % (entry["best_match"], entry["best_similarity"] * 100))
            else:
                print("No known location match (new place?)")
        else:
            print("Scan failed (no networks)")
    elif cmd == "locate":
        loc = estimate_location()
        print("Location: %s" % loc["location"])
        print("Confidence: %.1f%%" % (loc["confidence"] * 100))
        print("Reason: %s" % loc["reason"])
    elif cmd == "history":
        state = load_state()
        print("Scans: %d" % state.get("scan_count", 0))
        print("Locations: %d" % len(state.get("locations", {})))
        for name, data in state.get("locations", {}).items():
            print("  %s: %d scans, last seen %s" % (name, data.get("scan_count", 0), data.get("last_seen", "?")))
    elif cmd == "label":
        if len(sys.argv) < 3:
            print("Usage: signal_mapper.py label <name>")
            sys.exit(1)
        name = sys.argv[2]
        entry = scan_and_record(label=name)
        if entry:
            print("Labeled current location as: %s" % name)
            print("Fingerprint: %s" % entry["hash"])
        else:
            print("Scan failed")
    elif cmd == "wifi-state":
        import json as _json
        state = get_wifi_state_for_daemon()
        print(_json.dumps(state, indent=2))
    else:
        print("Unknown command: %s" % cmd)
