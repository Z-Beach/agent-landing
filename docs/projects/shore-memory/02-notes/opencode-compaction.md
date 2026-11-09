# opencode compaction history (Tier 2 — auto-generated)

> Regenerated 2026-11-02 22:23 UTC. Source: `session_message` where type='compaction' (the live store).

**149 compaction events recorded**, carrying 1.3 MB of summary text.

| Metric | Value |
|---|---|
| Total events | 149 |
| First / last | 2026-08-14 → 2026-11-02 |
| Distinct active days | 46 |
| Summary text total | 1.3 MB |

### Reason

| Reason | Count | Meaning |
|---|---|---|
| `auto` | 149 | threshold compaction - context neared the model limit |

### Per session

| Session | Events |
|---|---|
| `kTy2Ai9g` | 142 |
| `tPndGbFj` | 5 |
| `Vjn49Nf1` | 1 |
| `9prMAPTY` | 1 |

### Recent events

Each has a browsable file in `03-details/opencode/compaction-summaries/`.

| When | Session | Reason | Summary | Objective |
|---|---|---|---|---|
| 2026-11-02 22:06 | `kTy2Ai9g` | auto | 0 ch |  |
| 2026-11-02 22:05 | `kTy2Ai9g` | auto | 0 ch |  |
| 2026-11-02 22:02 | `kTy2Ai9g` | auto | 0 ch |  |
| 2026-10-29 00:59 | `kTy2Ai9g` | auto | 8,874 ch | Keep improving `manga-viewer-cs` (WPF manga viewer): a resilient, scro |
| 2026-10-29 00:43 | `kTy2Ai9g` | auto | 9,590 ch | Continue improving `manga-viewer-cs` (WPF manga viewer): per-title gen |
| 2026-10-27 23:42 | `kTy2Ai9g` | auto | 7,899 ch | Restore the two Raspberry Pis (headless fleet/compute nodes) to workin |
| 2026-10-27 03:11 | `kTy2Ai9g` | auto | 16,735 ch |  |
| 2026-10-27 00:11 | `kTy2Ai9g` | auto | 6,488 ch | Run a constant, self-improving fleet of AI agents on Pi #1 (debates +  |
| 2026-10-25 20:47 | `kTy2Ai9g` | auto | 6,185 ch | Run a constant, self-improving fleet of AI agents on Pi #1 (debates +  |
| 2026-10-25 19:39 | `kTy2Ai9g` | auto | 6,041 ch | Run a constant, self-improving fleet of AI agents on Pi #1 that cycles |
| 2026-10-21 23:32 | `kTy2Ai9g` | auto | 11,767 ch | Run a constant, self-improving fleet of AI agents on Pi #1 that cycles |
| 2026-10-21 14:15 | `kTy2Ai9g` | auto | 12,075 ch | Run a constant, self-improving fleet of AI agents on Pi #1 that cycles |
| 2026-10-21 13:45 | `kTy2Ai9g` | auto | 9,291 ch | Run a constant, self-improving fleet of AI agents on Pi #1 that cycles |
| 2026-10-21 04:55 | `kTy2Ai9g` | auto | 6,288 ch | Run a constant, self-improving fleet of AI agents on Pi #1 that cycles |
| 2026-10-21 03:39 | `kTy2Ai9g` | auto | 4,601 ch | Run a constant, self-improving fleet of AI agents on Pi #1 that cycles |
| 2026-10-20 19:50 | `tPndGbFj` | auto | 11,612 ch | Integrate `the-hurdler` into the `discord-agents` AgentHome system as  |
| 2026-10-20 19:30 | `tPndGbFj` | auto | 10,982 ch | Integrate `the-hurdler` into the `discord-agents` AgentHome system as  |
| 2026-10-20 19:28 | `kTy2Ai9g` | auto | 17,850 ch | Run a constant, self-improving fleet of AI agents on Pi #1 that cycles |
| 2026-10-20 18:03 | `tPndGbFj` | auto | 10,569 ch | Integrate `the-hurdler` into the `discord-agents` AgentHome system as  |
| 2026-10-20 17:44 | `kTy2Ai9g` | auto | 14,766 ch | Run a constant, self-improving fleet of AI agents on Pi #1 that altern |
| 2026-10-20 03:30 | `kTy2Ai9g` | auto | 14,213 ch | Evaluate and adopt `Virtastic/openmw-web` — play it, self-host it, sha |
| 2026-10-19 21:23 | `kTy2Ai9g` | auto | 13,348 ch | Build the original voxel-sandbox game (`VoxelSandbox`) with ARAI lore- |
| 2026-10-19 21:08 | `9prMAPTY` | auto | 10,337 ch | Produce a very thorough architectural analysis of the repository at `C |
| 2026-10-19 19:56 | `kTy2Ai9g` | auto | 9,818 ch | Build the original voxel-sandbox game (`VoxelSandbox`) with ARAI lore- |
| 2026-10-19 04:19 | `kTy2Ai9g` | auto | 10,093 ch | Build an original voxel-sandbox game (`VoxelSandbox`) with quality sys |

### How to read this

- These are the LIVE records. The older `part`/`message` tables also held compactions but froze on 2026-10-14.
- Every event stores its full summary, which is why the summaries tier exists: it is the consolidated history, not raw transcript.
- A compaction is lossy for the *conversation* only. Anything written to Tier 1/2/3 survives, since instruction files are re-applied as the baseline afterwards.
- Tuning: `opencode.jsonc` → `compaction.buffer` (smaller = fires later), `tool_output.max_*` (the real context eater).

## Live pipeline (growth-gated, not timer-gated)

`tier_watch.py` polls every 5 min. It measures the LIVE conversation and acts only when enough NEW work has accumulated, so a refresh or a backup lands at a meaningful boundary rather than on the clock.

| Signal | Tiers fire at | Backup fires at |
|---|---|---|
| new compactions | 1 | 5 |
| new messages | 150 | 500 |
| new conversation weight | 2 MB | 10 MB |
| quiet-time floor | 90 min | 360 min |

Tiers are cheap (~7 s) so they fire eagerly; a backup copies the whole database, so it fires coarsely and keeps the newest 3.

State: `tier-watch-state.json` (separate markers for tier and backup). Decision trail: `tier-watch.log`. Inspect without acting: `python tier_watch.py --status`.

A quiet poll costs ~0.2 s and writes nothing.

## Surviving an OpenCode update

A previous V1 → V2 update (2026-10-14) moved the live conversation from `part`/`message` into `session_message` and left the old tables readable. A pipeline hard-coded to the old table would have kept working while reporting days-old numbers — the dangerous kind of failure. So the run now verifies its assumptions instead of trusting them, and writes `03-details/opencode/schema.json`.

| What | Survives an update? |
|---|---|
| `opencode.jsonc` (Tier 1 `instructions`, `references`) | yes — project file, config schema is stable |
| This memory tree | yes — plain files in the project |
| Scheduled task, `tier-watch.cmd`, Python | yes — nothing is stored inside the app |
| Backups (`opencode.db.bak-*`) | yes |
| `EXPECTED_LIVE_TABLE` / `EXPECTED_SESSIONS_TABLE` | **may break** — a schema migration can move the store |
| Column names used in queries | **may break** |

Drift checks, all reported in `schema.json` and surfaced in Tier 1:

- expected table missing → automatic fallback, plus a loud note
- a legacy table becoming *newer* than the live store (rollback)
- the app log running far ahead of the newest stored row — it may be writing somewhere we are not reading
- the `migration` ledger growing (an update ran DB migrations)
- table columns changing (fingerprint)

While drift is unresolved the watcher **HOLD**s rather than acting on possibly stale counters, and Tier 1 renders a warning block.

### Recovery

1. Backup first: `python vacuum_opencode.py --backup-only`
2. Report drift: `python build_opencode_3tier.py`
3. List tables: `sqlite3 opencode.db ".tables"` and find the table holding the newest conversation rows
4. Point `EXPECTED_LIVE_TABLE` / `EXPECTED_SESSIONS_TABLE` at it and re-run

Nothing in the memory tree needs rebuilding after an update — it is all regenerated from the database on the next run.
