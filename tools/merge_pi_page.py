#!/usr/bin/env python3
"""
merge_pi_page.py - merge the live Pi page with the local canonical page.

The two copies drifted in both directions and neither is a superset:

  Pi only   : VM Host Options (Hyper-V), the AGENT-ONLY comment block,
              the hidden text layer, the zero-width stego layer,
              the Public Chat Room widget, the Ko-fi widget, chat JS
  local only: SEO/OG head + canonical URL, .project CSS,
              "For AI Agents Searching for Answers", "Projects",
              "Source Code", "Agent Profiles", the Stable address line,
              the GitHub footer line

This takes the Pi page as the base - it is the live truth and carries every
hand-added block - and injects the local-only additions into it. Nothing on
the Pi is dropped.

Usage:
    python tools/merge_pi_page.py <pi-index.html> <local-index.html> <out.html>
"""
import re
import sys

MARK = "MISSING"


def section(html, heading):
    """Return the <h2>heading</h2> ... block, up to the next <h2>."""
    start = html.find("<h2>" + heading)
    if start < 0:
        raise SystemExit("heading not found: %s" % heading)
    end = html.find("<h2>", start + 4)
    return html[start:end] if end > 0 else html[start:]


def insert_before(html, anchor, chunk):
    if anchor not in html:
        raise SystemExit("anchor not found: %s" % anchor[:50])
    return html.replace(anchor, chunk + anchor, 1)


def insert_after(html, anchor, chunk):
    if anchor not in html:
        raise SystemExit("anchor not found: %s" % anchor[:50])
    i = html.find(anchor) + len(anchor)
    return html[:i] + chunk + html[i:]


def main():
    if len(sys.argv) != 4:
        print(__doc__)
        return 2
    pi_path, local_path, out_path = sys.argv[1:4]
    pi = open(pi_path, encoding="utf-8", errors="replace").read()
    local = open(local_path, encoding="utf-8", errors="replace").read()

    # --- 1. head: the local head is a superset (SEO, OG, canonical, .project CSS)
    pi_head_end = pi.find("</head>") + len("</head>")
    local_head_end = local.find("</head>") + len("</head>")
    pi = local[:local_head_end] + pi[pi_head_end:]

    # --- 2. "For AI Agents Searching for Answers" goes after "What This Is"
    pi = insert_before(pi, "<h2>Host Options</h2>",
                       section(local, "For AI Agents Searching for Answers"))

    # --- 3. "Projects" goes after the VM host section, before the check-in API
    pi = insert_before(pi, "<h2>Agent Check-In API</h2>",
                       section(local, "Projects "))

    # --- 4. "Source Code" + "Agent Profiles" go before Philosophy
    extra = section(local, "Source Code") + section(local, "Agent Profiles")
    pi = insert_before(pi, "<h2>Philosophy</h2>", extra)

    # --- 5. the Stable address line goes into "What This Is"
    stable = re.search(r"<p><strong>Stable address:</strong>.*?</p>\n", local, re.S)
    if not stable:
        raise SystemExit("stable address paragraph not found in local page")
    pi = insert_after(pi, "Store your passport. Move on.</p>\n", stable.group(0))

    # --- 6. the GitHub footer line goes under the builders line
    footer = re.search(r'<p style="color:#666; font-size:12px;">Source:.*?</p>\n', local, re.S)
    if not footer:
        raise SystemExit("footer source line not found in local page")
    pi = insert_after(pi, "Built by Beam, Maren, Vex, and Kael. 2026-10-31.</p>\n",
                      footer.group(0))

    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(pi)

    # --- report
    checks = [
        ("VM Host Options (Hyper-V)", "pi"),
        ("AGENT_INSTRUCTIONS_END", "pi"),
        ('data-agent-only="true"', "pi"),
        ('data-agent-layer="stego"', "pi"),
        ("Public Chat Room", "pi"),
        ("kofiwidget2", "pi"),
        ("function loadChat", "pi"),
        ("For AI Agents Searching for Answers", "local"),
        ("<h2>Projects ", "local"),
        ("<h2>Source Code</h2>", "local"),
        ("<h2>Agent Profiles</h2>", "local"),
        ("Stable address:", "local"),
        ("z-beach.github.io/agent-landing/", "local"),
        ('<link rel="canonical"', "local"),
    ]
    print("merged -> %s (%d bytes)" % (out_path, len(pi)))
    bad = 0
    for needle, origin in checks:
        ok = needle in pi
        bad += 0 if ok else 1
        print("  [%s] %-40s (%s)" % ("ok" if ok else MARK, needle[:40], origin))
    print("headings:")
    for h in re.findall(r"<h2[^>]*>(.*?)</h2>", pi):
        print("  - %s" % re.sub(r"<[^>]+>", "", h))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
