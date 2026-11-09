# Robot Body Research

Status: **Research notes.** Prices verified 2026 (subject to change). Goal: find the mobile-node body (or bodies) that close the gap between an R2-type build and a robot dog, for a walking companion + payload + camera-height use case. See `AR_AI_System_Design.md` for how bodies plug into the system.

---

## The problem

| | R2-type (wheeled droid) | Robot dog | The gap |
|---|---|---|---|
| Payload | Strong | Weak (4-8kg) | — |
| Openness | Fully open | Gated (consumer = no SDK) | — |
| Camera height | Eye-level (mast/tower) | Hip-level | — |
| Terrain / stairs | Poor | Excellent | **the dog's only real win** |
| Price (usable) | ~$1.6-2.2k | $11k+ (EDU) | — |

---

## 1. R2-A1 (custom wheeled droid) — the scout

| Component | Cost |
|---|---|
| Rootable ROS2 LiDAR base (Proscenic M6 Pro) | $299 |
| Compute (GMKtec NucBox K6, Ryzen 7 7840HS/780M) | $269-469 |
| R2D2-CNC tripod outer-foot drives | $280 |
| Printed/CNC shell | $500-1,000 |
| Power | ~$150 |
| **Total** | **~$1,600-2,200** |

Strengths: payload, openness, eye-height sensors, iconic, indoor/urban flat. Weaknesses: no stairs, limited terrain, wheeled.

## 2. Robot dogs (Unitree Go2)

- **Go2 Air $1,600 / Go2 Pro $2,800** — consumer tiers, **no SDK**. Can't run our agents.
- **Go2 EDU $11,190+** — full SDK, but known remote-code-execution vulnerabilities; pricey.

Verdict: the consumer tiers are toys for our purposes; the usable tier costs more than any competitor with worse payload.

## 3. Tracked platforms — the gap-closer (stairs + payload + openness)

Classic stair-climbing form factor, open ROS stacks, flat deck for a camera mast, IP54 weather sealing.

| Platform | Price | Payload | Terrain | Openness |
|---|---|---|---|---|
| **Foxtech TR500S** | **$2,950** | 50kg | all-terrain, stairs | ROS/serial |
| Foxtech TR600 | $5,350 | 120kg | stairs, 30° slopes | ROS |
| JCS KOMODO-02 | ~$3-5k (quote) | 100kg | 30° climb, 150mm steps, stairs | ROS1/ROS2 drivers |
| Guoxing Safari 600T | ~$3-5k (quote) | 80kg | 40° climb, 170mm obstacles | ROS |
| CuboRex CuGo V4.5 | $6,400 | 80kg | 20° slopes, 7cm obstacles (weak stairs) | ROS2 |

**All-in with K6 brain: ~$3.3-3.5k.** Walking pace (~1-1.4 m/s) is ideal for a companion that follows a walking human. Key caveats: heavy (60-100kg self-weight — garage dweller, not house dweller), wide (~60-80cm, door-fit check), industrial look.

## 4. Wheel-leg hybrids — the new best-of-both (wheels + stairs)

| Platform | Price | What it is | Why it matters |
|---|---|---|---|
| **Sable Motion Nova A6** | ~$2,500 | Self-balancing wheeled biped; 35° slopes, stairs, grass; ~3h | Mini-Ascento at hobby cost |
| **Diablo** | $4,399 | Self-balancing wheel-leg; **open SDK**; 2 modes | **Creeping mode carries 80kg** = stair-climbing golf cart; standing mode 4kg |

The Diablo is the standout candidate for the transporter role: it collapses the tank's cargo role, the dog's stairs, and the "golf cart" human-carrying idea into one open-SDK body.

## 5. Humanoids — the vids' bots (the trap)

| | Price (usable) | Notes |
|---|---|---|
| Unitree G1 base | $13,500 (street ~$17-21k) | **Locked demo unit — no SDK, can't be programmed** |
| Unitree G1 EDU | $43,900-73,900 | Real SDK, 100 TOPS, but 2h battery, 2-3kg arms, bipedal fragility |
| Unitree R1 | $4,900-5,900 | Cheaper humanoid (~1h battery), EDU-gated dev |

Verdict: humanoids are the aspiration, not the buy. Arms = a separate manipulation skill stack (deferred). Wrong-shaped, expensive, fragile, energy-hungry for a wearable-AR companion.

## 6. Aerial scout (optional layer)

Consumer drone (~$0.5-1k): bird's-eye context, over-the-ridge recon, mapping assists. Cheap; different role (aerial, not companion).

## 7. The recommendation

**Three tiers of mobility, one agent stack** (every body = an event-bus client):

1. **R2-A1 (~$1.6-2.2k)** — the daily scout/companion. Buy first.
2. **Diablo ($4,399)** — the transporter: carries R2 + payload + human over terrain and stairs. The next purchase after R2 proves the stack.
3. **Drone (~$0.5-1k)** — aerial context layer, optional.

The user's own scooter/bike is the everyday "golf cart" for human-speed, human-distance transport — mount a sensor pod, and it's a rideable AR platform.

**Order of purchase:** R2-A1 → validate agent stack → Diablo-class transporter → drone (optional).
