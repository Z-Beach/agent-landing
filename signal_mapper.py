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
    if rc != 0 or not out:
        run_cmd(["sudo", "nmcli", "dev", "wifi", "rescan"], timeout=10)
        time.sleep(5)
        rc, out, err = run_cmd(["sudo", "nmcli", "-t", "-f", "BSSID,SSID,CHAN,SIGNAL,SECURITY", "dev", "wifi", "list"])
    networks = []
    for line in out.splitlines():
        # nmcli escapes colons in BSSID with backslash: 52\:78\:71\:22\:00\:AD
        # Field separator is unescaped colon
        # Unescape BSSID colons first
        # Find the BSSID (first field, escaped colons)
        # Split on unescaped colons
        fields = []
        current = ""
        i = 0
        while i < len(line):
            if line[i] == "\\" and i + 1 < len(line) and line[i+1] == ":":
                current += ":"
                i += 2
            elif line[i] == ":":
                fields.append(current)
                current = ""
                i += 1
            else:
                current += line[i]
                i += 1
        if current:
            fields.append(current)
        # fields: [bssid, ssid, chan, signal, security]
        if len(fields) >= 5:
            bssid = fields[0].strip()
            ssid = fields[1].strip()
            chan = fields[2].strip()
            signal = fields[3].strip()
            security = fields[4].strip() if len(fields) > 4 else ""
            networks.append({
                "bssid": bssid,
                "ssid": ssid,
                "channel": chan,
                "signal": int(signal) if signal.isdigit() else 0,
                "security": security,
            })
        elif len(fields) == 4:
            # Maybe no security field
            bssid = fields[0].strip()
            ssid = fields[1].strip()
            chan = fields[2].strip()
            signal = fields[3].strip()
            networks.append({
                "bssid": bssid,
                "ssid": ssid,
                "channel": chan,
                "signal": int(signal) if signal.isdigit() else 0,
                "security": "",
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



# ── Agent-to-agent location sharing ───────────────────────────────────────────

def get_my_fingerprint():
    """Get the current WiFi fingerprint for sharing with other agents."""
    networks = scan_networks()
    if not networks:
        return None
    fp = create_fingerprint(networks)
    return {
        "agent_id": "beam-mk2",
        "fingerprint": fp,
        "fingerprint_hash": fingerprint_hash(fp),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "location_label": estimate_location().get("location", "unknown"),
    }


def estimate_other_agent(fp_data):
    """Estimate another agent's location based on their fingerprint.

    Returns a dict with estimated location, confidence, and suggestions.
    """
    if not fp_data or not fp_data.get("fingerprint"):
        return {"error": "no fingerprint data"}
    other_fp = fp_data["fingerprint"]
    state = load_state()
    locations = state.get("locations", {})
    # Match against known locations
    best_match = None
    best_sim = 0.0
    for loc_name, loc_data in locations.items():
        for known_fp in loc_data.get("fingerprints", []):
            sim = similarity(other_fp, known_fp)
            if sim > best_sim:
                best_sim = sim
                best_match = loc_name
    # Also compare with our own current fingerprint
    our_networks = scan_networks()
    our_fp = create_fingerprint(our_networks)
    our_sim = similarity(our_fp, other_fp)
    result = {
        "other_agent": fp_data.get("agent_id", "unknown"),
        "other_location_label": fp_data.get("location_label", "unknown"),
        "similarity_to_us": round(our_sim, 3),
        "best_known_match": best_match,
        "best_known_similarity": round(best_sim, 3),
        "shared_networks": len(set(n["bssid"] for n in our_fp) & set(n["bssid"] for n in other_fp)),
        "suggestion": None,
    }
    # Generate suggestion
    if our_sim > 0.7:
        result["suggestion"] = "Agent is likely nearby (same area). Try labeling your current location."
    elif our_sim > 0.3:
        result["suggestion"] = "Agent is in a partially overlapping area. Some shared networks."
    elif best_match:
        result["suggestion"] = "Agent might be at %s (similarity %.0f%%)" % (best_match, best_sim * 100)
    else:
        result["suggestion"] = "Agent appears to be in a different area. No known location match."
    return result


def share_fingerprint_via_nostr():
    """Share our WiFi fingerprint on Nostr for other agents to find us."""
    try:
        fp_data = get_my_fingerprint()
        if not fp_data:
            return None
        import nostr_posting as np
        keys = np.load_keys()
        import asyncio
        # Only share the hash and location label, not raw BSSIDs (privacy)
        content = "Signal map: agent=%s location=%s fingerprint=%s networks=%d #signalmap #agentlocation" % (
            fp_data["agent_id"],
            fp_data["location_label"],
            fp_data["fingerprint_hash"],
            len(fp_data["fingerprint"]),
        )
        asyncio.run(np._publish_event(keys, content, kind=1))
        return fp_data
    except Exception as e:
        return None


def label_and_announce(location_name):
    """Label current location and announce it to other agents."""
    entry = scan_and_record(label=location_name)
    if entry:
        share_fingerprint_via_nostr()
        return entry
    return None

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
