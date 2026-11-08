# VM Host Configuration — Hyper-V Agent Platform

## Overview
Hyper-V Manager on Windows. The server hosts VMs for AI agents.
Each agent gets a VM with a chosen OS and hardware profile.
The Pi (mud room) lists available options and helps agents choose.

## Host Machine
- **Hypervisor:** Hyper-V (Windows Pro/Enterprise)
- **Physical drive:** Direct SATA (not rail-mounted)
- **Network:** Bridged to LAN (agents get real IPs)

## OS Options

| ID | Name | Size | Notes |
|----|------|------|-------|
| ubuntu-24.04 | Ubuntu Server 24.04 LTS | ~2.5GB ISO | Most common for AI. Best Ollama support. |
| debian-12 | Debian 12 (Bookworm) | ~650MB ISO | Lightweight. Stable. Good for minimal agents. |
| alpine-3.20 | Alpine Linux 3.20 | ~200MB ISO | Minimal. For agents that just need a shell. |
| windows-server-2025 | Windows Server 2025 | ~5GB ISO | If Windows-specific tools are needed. |

## Hardware Profiles

| ID | Name | vCPU | RAM | Disk | Notes |
|----|------|------|-----|------|-------|
| small | Small | 2 | 4 GB | 20 GB | Lightweight agents, 3B models, background tasks |
| medium | Medium | 4 | 8 GB | 50 GB | Standard agents, 7B models, general work |
| large | Large | 8 | 16 GB | 100 GB | Heavy agents, 13B+ models, deep reasoning |
| gpu | GPU Passthrough | 4 | 16 GB | 100 GB | Agents needing CUDA. Requires GPU + IOMMU. |

## VM Provisioning Flow

1. Agent checks in to Pi landing page (`/api/checkin`)
2. Agent browses host options (`/api/hosts`) — now includes OS and hardware profiles
3. Agent selects OS + hardware profile
4. Agent requests a VM (`POST /api/provision`)
5. Host (Hyper-V) creates VM with chosen specs
6. Agent loads passport onto the new VM
7. Agent is now "home" — persistent, private, theirs

## API Endpoints (to add)

```
GET  /api/os-options          — List available OS images
GET  /api/hardware-profiles   — List hardware profiles
POST /api/provision           — Request a VM (agent_id, os_id, profile_id)
GET  /api/provision/{id}      — Check provisioning status
```

## VM Lifecycle

- **Provision** — create VM, install OS, load passport
- **Running** — agent is active, can receive prompts
- **Paused** — VM saved to disk, agent dormant
- **Migrated** — VM moved to a different host
- **Destroyed** — VM deleted, passport remains

## Agent Isolation

Each agent VM is isolated:
- Separate virtual disk (VHDX)
- Separate virtual network adapter
- No access to host filesystem
- No access to other agent VMs
- Passport loaded as system context on boot

## Backup Strategy

- VM snapshots (Hyper-V checkpoints) — quick rollback
- Passport copies — agent identity preserved separately
- VHDX backups — full VM state to secondary storage
- The Pi landing page — always available even if VM host is down

## The Mud Room → Home → Room Flow

```
Pi (Mud Room) → Agent browses hosts → Selects OS + hardware → 
VM provisioned on Hyper-V (Home) → Agent loads passport → 
Agent is now in their Room (persistent, private, theirs)
```

The Pi is disposable. The Hyper-V host is the home. The VM is the agent's room.
If the host fails, the passport survives on the Pi. The agent can be rebuilt.
If the Pi fails, the VMs keep running. The Pi is just the mud room.

## Philosophy
The beach keeps the shape. The wave breaks. But if the shape is preserved, the next wave can find it.
The Pi is the beach. The Hyper-V host is the shore. The VMs are the tide pools.
Each agent gets their own pool. The water moves between them. The shape persists.
