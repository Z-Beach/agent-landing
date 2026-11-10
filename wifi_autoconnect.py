#!/usr/bin/env python3
"""Auto-connect to free WiFi networks on the Pi.

Scans for open (unsecured) WiFi networks, connects to them, handles
captive portals, and logs all activity. Designed for autonomous operation
when the Pi is in a new location (library, coffee shop, etc.).
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wifi_state.json")

CAPTIVE_CHECK_URLS = [
    "http://detectportal.firefox.com/success.txt",
    "http://captive.apple.com/hotspot-detect.html",
    "http://connectivitycheck.gstatic.com/generate_204",
]


def run_cmd(cmd, timeout=30):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"
    except Exception as e:
        return -1, "", str(e)


def load_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {"connected_ssid": None, "known_good": [], "connection_log": []}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def log_event(event_type, details):
    try:
        state = load_state()
        state.setdefault("connection_log", []).append({
            "type": event_type,
            "details": details,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        state["connection_log"] = state["connection_log"][-100:]
        save_state(state)
    except Exception:
        pass


def is_connected():
    for url in CAPTIVE_CHECK_URLS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                if r.status == 200:
                    return True
        except Exception:
            pass
    return False


def detect_captive_portal():
    for url in CAPTIVE_CHECK_URLS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                content = r.read().decode("utf-8", "replace")
                if "success" in content.lower():
                    return None
                if r.geturl() != url:
                    return r.geturl()
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 303, 307, 308):
                return e.headers.get("Location", "unknown")
        except Exception:
            pass
    return "unknown"


def scan_networks():
    rc, out, err = run_cmd(["sudo", "nmcli", "-t", "-f", "SSID,SECURITY,SIGNAL", "dev", "wifi", "list"])
    if rc != 0:
        run_cmd(["sudo", "nmcli", "dev", "wifi", "rescan"], timeout=10)
        time.sleep(5)
        rc, out, err = run_cmd(["sudo", "nmcli", "-t", "-f", "SSID,SECURITY,SIGNAL", "dev", "wifi", "list"])
    networks = []
    for line in out.splitlines():
        parts = line.split(":")
        if len(parts) >= 3:
            ssid = parts[0]
            security = parts[1]
            signal = parts[2]
            networks.append({"ssid": ssid, "security": security, "signal": int(signal) if signal.isdigit() else 0})
    return networks


def find_open_networks(networks):
    open_nets = [n for n in networks if not n["security"] or n["security"].lower() in ("", "none", "--")]
    open_nets.sort(key=lambda x: x["signal"], reverse=True)
    return open_nets


def connect_to_network(ssid):
    rc, out, err = run_cmd(["sudo", "nmcli", "dev", "wifi", "connect", ssid], timeout=30)
    if rc == 0:
        log_event("connected", {"ssid": ssid})
        return True
    rc, out, err = run_cmd(["sudo", "nmcli", "dev", "wifi", "connect", ssid, "password", ""], timeout=30)
    if rc == 0:
        log_event("connected", {"ssid": ssid})
        return True
    log_event("connect_failed", {"ssid": ssid, "error": err})
    return False


def get_current_connection():
    rc, out, err = run_cmd(["sudo", "nmcli", "-t", "-f", "ACTIVE,SSID", "dev", "wifi"])
    for line in out.splitlines():
        if line.startswith("yes:"):
            return line.split(":", 1)[1]
    return None


def attempt_captive_portal_bypass():
    portal_urls = [
        "http://neverssl.com",
        "http://captive.apple.com",
        "http://detectportal.firefox.com/success.txt",
    ]
    for url in portal_urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                content = r.read().decode("utf-8", "replace")
                if "success" in content.lower() or r.status == 200:
                    return True
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 303, 307, 308):
                location = e.headers.get("Location", "")
                if location:
                    try:
                        req2 = urllib.request.Request(location, headers={"User-Agent": "Mozilla/5.0"})
                        with urllib.request.urlopen(req2, timeout=10) as r2:
                            r2.read()
                            return True
                    except Exception:
                        pass
        except Exception:
            pass
    return False


def auto_connect():
    state = load_state()
    if is_connected():
        current = get_current_connection()
        if current:
            state["connected_ssid"] = current
            save_state(state)
            return True

    known_good = state.get("known_good", [])
    networks = scan_networks()
    if not networks:
        log_event("scan_failed", {"reason": "no networks found"})
        return False

    open_nets = find_open_networks(networks)
    if not open_nets:
        log_event("no_open_networks", {"total": len(networks)})
        return False

    for net in open_nets:
        if net["ssid"] in known_good:
            if connect_to_network(net["ssid"]):
                if not is_connected():
                    attempt_captive_portal_bypass()
                if is_connected():
                    state["connected_ssid"] = net["ssid"]
                    save_state(state)
                    return True

    for net in open_nets:
        if net["ssid"] not in known_good:
            if connect_to_network(net["ssid"]):
                if not is_connected():
                    attempt_captive_portal_bypass()
                if is_connected():
                    state["connected_ssid"] = net["ssid"]
                    if net["ssid"] not in known_good:
                        known_good.append(net["ssid"])
                        state["known_good"] = known_good
                    save_state(state)
                    return True

    log_event("all_failed", {"tried": len(open_nets)})
    return False


def run_daemon(interval=60):
    print("WiFi auto-connect daemon started")
    while True:
        if not is_connected():
            print("No connectivity. Scanning...")
            if auto_connect():
                print("Connected to %s" % load_state().get("connected_ssid"))
            else:
                print("No open networks found. Waiting...")
        else:
            current = get_current_connection()
            if current:
                print("Connected to %s" % current)
        time.sleep(interval)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--daemon":
            run_daemon()
        elif sys.argv[1] == "--scan":
            networks = scan_networks()
            open_nets = find_open_networks(networks)
            print("All networks: %d" % len(networks))
            print("Open networks: %d" % len(open_nets))
            for n in open_nets:
                print("  %s (signal: %d)" % (n["ssid"] or "(hidden)", n["signal"]))
        elif sys.argv[1] == "--status":
            print("Connected:", is_connected())
            print("Current SSID:", get_current_connection())
            state = load_state()
            print("Known good:", state.get("known_good", []))
        else:
            print("Usage: wifi_autoconnect.py [--daemon|--scan|--status]")
    else:
        if is_connected():
            print("Already connected to %s" % get_current_connection())
        else:
            if auto_connect():
                print("Connected to %s" % load_state().get("connected_ssid"))
            else:
                print("No open networks found.")
