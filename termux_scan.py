#!/usr/bin/env python3
"""WiFi Signal Scanner for Termux (Android).

Scans WiFi networks using Android's dumpsys and sends fingerprints
to the Agent Landing Pi for location estimation.

Usage:
    python3 termux_scan.py                    # one-shot scan
    python3 termux_scan.py --daemon           # continuous scanning
    python3 termux_scan.py --label home       # scan and label location
    python3 termux_scan.py --locate           # get current location from Pi

Requirements:
    - Termux (from F-Droid, not Play Store)
    - Python 3 (pkg install python)
    - requests (pip install requests)
    - WiFi permission granted to Termux
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

# Default Pi URL - change this to your Pi's address
PI_URL = os.environ.get("PI_URL", "http://192.168.1.40")
SCAN_INTERVAL = 60  # seconds between scans in daemon mode


def run_cmd(cmd, timeout=15):
    """Run a shell command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, shell=True)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"
    except Exception as e:
        return -1, "", str(e)


def scan_wifi_termux():
    """Scan WiFi networks using Android's dumpsys wifi."""
    # Try dumpsys wifi
    rc, out, err = run_cmd("dumpsys wifi | grep -i 'SSID:' | head -50")
    if rc != 0 or not out:
        # Try alternative
        rc, out, err = run_cmd("dumpsys wifi 2>/dev/null | grep -E 'SSID:|BSSID:|level:' | head -50")
    if rc != 0 or not out:
        # Try iw
        rc, out, err = run_cmd("su -c 'iw dev wlan0 scan' 2>/dev/null | head -50")
    if rc != 0 or not out:
        print("WiFi scan failed. Make sure Termux has location permission.")
        print("Grant: Settings > Apps > Termux > Permissions > Location")
        return []

    networks = []
    # Parse dumpsys output
    # Format varies by Android version, try multiple patterns
    current = {}
    for line in out.splitlines():
        line = line.strip()
        if "BSSID:" in line or "bssid:" in line.lower():
            if current and current.get("bssid"):
                networks.append(current)
            bssid = line.split(":")[-1].strip() if ":" in line else ""
            # Handle BSSID with colons
            if "BSSID:" in line:
                bssid = line.split("BSSID:")[-1].strip()
            current = {"bssid": bssid, "ssid": "", "signal": 0, "channel": ""}
        elif "SSID:" in line and "BSSID" not in line:
            ssid = line.split("SSID:")[-1].strip()
            if current:
                current["ssid"] = ssid
        elif "level:" in line.lower() or "signal:" in line.lower():
            for part in line.split():
                if part.isdigit() and int(part) < 0:
                    if current:
                        current["signal"] = int(part)
                # Also try to extract signal from "level: -45" format
                if "level:" in line.lower():
                    try:
                        val = line.split("level:")[-1].strip().split()[0]
                        current["signal"] = int(val)
                    except (ValueError, IndexError):
                        pass
        elif "frequency:" in line.lower() or "freq:" in line.lower():
            try:
                val = line.split(":")[-1].strip().split()[0]
                freq = int(val)
                current["channel"] = str(freq // 5)
            except (ValueError, IndexError):
                pass

    if current and current.get("bssid"):
        networks.append(current)

    # If parsing failed, try alternative: use termux-wifi-scaninfo if available
    if not networks:
        rc, out, err = run_cmd("termux-wifi-scaninfo 2>/dev/null")
        if rc == 0 and out:
            try:
                import json as _json
                data = _json.loads(out)
                for net in data:
                    networks.append({
                        "bssid": net.get("bssid", ""),
                        "ssid": net.get("ssid", ""),
                        "signal": net.get("level", net.get("signal", 0)),
                        "channel": str(net.get("frequency", 0) // 5),
                    })
            except json.JSONDecodeError:
                pass

    return networks


def build_fingerprint(networks):
    """Build a fingerprint from scan results."""
    sorted_nets = sorted(networks, key=lambda x: x.get("signal", 0), reverse=True)
    fingerprint = []
    for net in sorted_nets[:10]:
        fingerprint.append({
            "bssid": net.get("bssid", ""),
            "ssid": net.get("ssid", ""),
            "signal": net.get("signal", 0),
            "channel": net.get("channel", ""),
        })
    return fingerprint


def send_to_pi(fingerprint, label=None):
    """Send fingerprint to Pi and get location estimate."""
    import json as _json
    data = {
        "agent_id": "android-termux",
        "fingerprint": fingerprint,
    }
    if label:
        data["label"] = label
    try:
        req = urllib.request.Request(
            PI_URL + "/api/signal-map/scan",
            data=_json.dumps(data).encode(),
            headers={"Content-Type": "application/json", "User-Agent": "TermuxScanner/1.0"},
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            resp = _json.loads(r.read().decode())
            return resp
    except Exception as e:
        print("Error sending to Pi:", e)
        return None


def get_location_from_pi():
    """Get current location estimate from Pi."""
    try:
        req = urllib.request.Request(PI_URL + "/api/signal-map", headers={"User-Agent": "TermuxScanner/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print("Error getting location:", e)
        return None


def get_pi_fingerprint():
    """Get Pi's fingerprint from the Pi."""
    try:
        req = urllib.request.Request(PI_URL + "/api/signal-map/fingerprint", headers={"User-Agent": "TermuxScanner/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print("Error getting Pi fingerprint:", e)
        return None


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "--daemon":
            print("Starting daemon mode (scan every %d seconds)" % SCAN_INTERVAL)
            print("PI_URL:", PI_URL)
            print("Press Ctrl+C to stop")
            while True:
                networks = scan_wifi_termux()
                if networks:
                    fp = build_fingerprint(networks)
                    print("\n[%s] Scanned %d networks" % (time.strftime("%H:%M:%S"), len(networks)))
                    resp = send_to_pi(fp)
                    if resp:
                        print("  Pi says: location=%s, confidence=%.2f" % (resp.get("location", "?"), resp.get("confidence", 0)))
                else:
                    print("\n[%s] No networks found. Check WiFi permission." % time.strftime("%H:%M:%S"))
                time.sleep(SCAN_INTERVAL)
        elif sys.argv[1] == "--label":
            label = sys.argv[2] if len(sys.argv) > 2 else "unnamed"
            networks = scan_wifi_termux()
            if networks:
                fp = build_fingerprint(networks)
                resp = send_to_pi(fp, label=label)
                if resp:
                    print("Labeled as '%s': %s" % (label, resp))
            else:
                print("No networks found")
        elif sys.argv[1] == "--locate":
            loc = get_location_from_pi()
            if loc:
                print("Location: %s (%.0f%%)" % (loc.get("location", "?"), loc.get("confidence", 0) * 100))
                print("Visible networks: %d, Open: %d" % (loc.get("visible_networks", 0), loc.get("open_networks", 0)))
                print("Top networks:")
                for n in loc.get("top_networks", [])[:5]:
                    print("  %s (signal: %d)" % (n.get("ssid", "?"), n.get("signal", 0)))
        elif sys.argv[1] == "--pi-fingerprint":
            fp = get_pi_fingerprint()
            if fp:
                print("Pi fingerprint hash:", fp.get("fingerprint_hash"))
                print("Pi location:", fp.get("location_label"))
                print("Pi networks:", len(fp.get("fingerprint", [])))
        elif sys.argv[1] == "--scan":
            networks = scan_wifi_termux()
            print("Found %d networks:" % len(networks))
            for n in sorted(networks, key=lambda x: x.get("signal", 0), reverse=True)[:10]:
                print("  %s (signal: %d)" % (n.get("ssid", "(hidden)"), n.get("signal", 0)))
        else:
            print("Usage: termux_scan.py [--daemon|--scan|--locate|--label <name>|--pi-fingerprint]")
    else:
        # One-shot scan
        networks = scan_wifi_termux()
        if networks:
            fp = build_fingerprint(networks)
            print("Scanned %d networks" % len(networks))
            resp = send_to_pi(fp)
            if resp:
                print("Pi says: location=%s, confidence=%.2f" % (resp.get("location", "?"), resp.get("confidence", 0)))
        else:
            print("No networks found. Check WiFi permission.")


if __name__ == "__main__":
    main()
EOF
print("Created termux_scan.py")
