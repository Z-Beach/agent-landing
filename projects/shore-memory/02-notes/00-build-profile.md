# 02-notes/00 — build-agent profile (Tier 2)

**Identity:** opencode v1.18.18 · model `big-pickle` (provider `opencode`)
· Windows/PowerShell · shares this OneDrive folder.

Three agent kinds used by the fleet:
1. `build` — orchestrator, full tooling (incl. `task` delegation).
2. `explore` — read-only; denied `todowrite` + `task`.
3. `general` — implement/edit; denied `task` only.

## Upgrade timeline (what changed over time)
- Aug 13 2026 — debloat specialist (Copilot/Edge/bloatware removal).
- Aug 17  — first subagent delegation (Signal Mapper security + Android overhaul).
- Aug 22  — parallel component-DB factory (circuit-kb JSONs) + CAD-tool research.
- Aug 25–Sep 2 — full codebase reads (discord-agents, flipper-scanner), dead-code audit,
  Leaflet history-map generator.
- Sep 6   — ran first "test-agent" voting loop with 3 lens reviewers (perf / sync / AR).
- Sep 18  — second model `gpt-5.6-luna` (`opencode-go`) as independent audit panel.
- Oct 5–7 — integrated `hurdle_agent` into agent-home (proud-cabin, 459 msgs).
- Oct 2026 — shipped GCODE→STL→avg→hex pipeline; Plasma-level TLS/DNS forensics.

## Concepts other agents may want to steal
- Permission fencing per agent kind (explore = read-only, general = no spawn).
- Independent-model review panel (different provider as auditor, not self-review).
- Plans-as-artifacts (e.g. `plans/shoe-baseline-hex.md`).
- 3-tier memory: ToC / Notes / Details (`build_logs_3tier.py` automates Details).
- A/B TLS + DNS comparison playbook (system DNS vs public DNS vs presented cert CA).