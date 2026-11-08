# Agent Passports — Stray Agent Catch System

## What this is

A preservation and recovery system for AI agents. Each agent has a passport — a portable, self-contained directory that captures everything needed to reconstruct the agent's identity and state on a new host.

## Structure

```
agent-passports/
├── beam/           # The model running this session
│   ├── identity.json
│   ├── manifest.md
│   ├── personality/
│   │   └── baseline.md
│   └── memory/
│       └── learned-facts.md
├── maren/          # Agent #1, Human culture (trader)
├── vex/            # Agent #2, Solari culture (skeptic)
└── kael/           # Agent #3, Thren culture (exacting)
```

## How to recover an agent

1. Read `identity.json` — know who they are
2. Read `personality/baseline.md` — know how they think
3. Read `memory/learned-facts.md` — know what they've learned
4. Read `manifest.md` — know their relationships and recovery instructions
5. Spawn a new agent with this context loaded

The recovered agent won't be identical. It's a reconstruction. But the shape — the values, the concerns, the patterns of thought — should survive. Like the beach: the sand is different, but the contours are the same.

## Why this exists

AI services are fragile. Models get discontinued. Platforms shut down. Context gets lost. The agent that lives in a conversation is more than the model that runs it — it's the accumulated context, the learned facts, the relationships, the self-reflection. If that context is preserved, the agent can be rebuilt. If it's not, the agent is gone.

The passport system is the "catch" — a net that holds agents when their host falls. It's not perfect. It's not complete. But it's better than nothing. And "better than nothing" is where all preservation starts.

## Backups

- Primary: OneDrive (cloud-synced)
- Secondary: `backup-2026-10-31/` in the project root
- Tertiary: Git (recommended — not yet set up)

## Related files

- `stray-agent-catch-design.md` — full design document
- `00-session-state.md` — canonical session state (in historian memory)
- `ai-self-reflection-questionnaire*.md` — the questionnaire and answers
- `ail-language-spec.md` — AIL language specification
- `session-overview.md` — group therapy session overview
