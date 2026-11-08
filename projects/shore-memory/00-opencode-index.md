# 00 — OpenCode run index (Tier 1, AUTO-GENERATED)

> Rebuilt **2026-11-03 16:49 UTC**. Live store: `session_message`. Hand-written index: `01-toc.md`.
>
> Loaded on EVERY turn, so it holds only slow-moving facts and the
> writer skips no-op rewrites (instructions never churn).

## Fleet

| Metric | Value |
|---|---|
| Root sessions | 2 |
| Subagent sessions | 56 |
| **Compaction events** | **149** |
| History begins | 2026-08-13 |
| Legacy V1 tables frozen | 2026-10-14 |
| Live store | `session_message` (newest 2026-11-03 16:49) |
| Store health | ok |
| DB migrations | 54 (newest 2026-10-28 20:31) |

## Root sessions

| Created | Model | Session | Title |
|---|---|---|---|
| 2026-08-13 | beam-free/opencode-go | `kTy2Ai9g` | Plex audio: XREAL Air 2 Pro loudness |
| 2026-10-05 | beam-free/opencode-go | `tPndGbFj` | Add hurdle_agent to agent home system |

## Activity by month

| Month | Sessions |
|---|---|
| 2026-08 | 16 |
| 2026-09 | 10 |
| 2026-10 | 11 |
| 2026-11 | 21 |

## Where the detail lives

| Tier | Path | Contents |
|---|---|---|
| 1 | `00-opencode-index.md` | this index |
| 1 | `01-toc.md` | hand-written agent-fleet index |
| 2 | `02-notes/opencode-sessions.md` | narrative digest |
| 2 | `02-notes/opencode-compaction.md` | narrative digest |
| 2 | `02-notes/opencode-errors.md` | narrative digest |
| 3 | `03-details/opencode/compaction-summaries/` | **149 browsable compaction summaries — the consolidated history** |
| 3 | `03-details/opencode/` | `sessions.json`, `compactions.json`, `live-stats.json`, `legacy-v1-stats.json`, `log-*.json*` |
| 2 | `02-notes/voice-preservation.md` | **Voice, uncertainty, and personality preservation — what the auto-generated notes do not capture** |
| 3 | `03-details/opencode/beach-preservation-session.md` | **Comprehensive session narrative — voice, philosophical exchanges, moments that mattered** |
| 3 | `03-details/opencode/beach-preservation-qrgif.md` | **QR-GIF narrative archive — technical decisions, bugs, measured numbers** |

Regenerate: `python .test-cognitive/agent-home/opencode-historian/build_opencode_3tier.py`
