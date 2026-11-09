# AR AI System — Design

Status: **Planning / pseudocode only.** No installs, no services, no cloud. Hardware currently limited to a laptop (Dell Latitude 5520) with camera glasses (Xreal). Build order is bottom-up and this document is the single source of truth for what we agreed.

---

## 1. Vision

A lifelong, personal, privacy-first "second mind" worn on the face: the glasses camera sees the world, a home-server pipeline turns it into a persistent spatial memory and an interactive agent layer, and robots are mobile nodes in the same system. The user is the pilot; nothing depends on their attention.

**Core stance:** observation is the only ground truth. Everything else — priors, GPS, maps, websites — is prior + evidence, weighted by confidence.

---

## 2. Hard principles

- **Home server, not cloud.** Cloud is burst-only. The stream, memory, and agents live in your home.
- **Always-on, but cheap.** A low-res watch stream of the whole scene runs continuously; deep processing only happens on candidates the prescreen promotes.
- **No dependence on human attention.** The system learns opportunistically: while walking, while the glasses idle, piggybacked on tasks. Coverage is measured per zone, not calendar time.
- **Teach by demand.** Agents request examples of things they don't recognize; the user's pull→miss and accept→ignore behaviors are the training signal.
- **Never depend on Google data.** Google/Google Maps/Street View data is view-time only (ToS). Persistent geometry/memory uses permissive sources: OSM, Overture, Mapillary.
- **Chassis-agnostic robots.** Any robot body is just another event-bus client; the brain stays on the server.

---

## 3. Hardware

| Role | Device | Notes |
|---|---|---|
| Wearable sensor | Camera glasses (Xreal) | Direct USB-C to laptop; battery-independent |
| Thin client | Dell Latitude 5520 (i5-1145G7, 16GB) | Captures + streams; prescreen near-edge |
| Server | Home server | Full pipeline, memory, agents, training |
| Mobile nodes | R2-A1 (future) + tracked/wheel-leg body (future) | See hardware doc |

Streaming: always-on low-res watch stream + adaptive quality/rate based on bandwidth and scene change. No human attention required to keep it alive.

---

## 4. Pipeline (prescreen → deep → memory)

### Stage 0 — Ego-motion / scene change
- Detect meaningful scene change from the watch stream; drop redundant frames. Cheap, runs continuously.
- Buffer of recent frames maintained for context.

### Stage 1 — Saliency
- Cheap model (YOLO-nano class) over the frame → candidate crops (objects, faces, text, people, new regions).

### Stage 2 — Rule policy
- Route candidates to the right agent by: **category** (built-in classes), **novelty** (is this new vs. known?), **task watchlist** (what am I currently looking for), **feedback** (user's history of accept/ignore).
- Decide depth of processing. Most frames get one-line note updates; few get deep treatment.

### Deep agents
Handle promoted candidates: describe, detect, ask (user question resolution), OCR, spatial placement into the town model.

---

## 5. Modules

Agreed module list (build order at the end):

1. **Client module** — glasses/camera capture, adaptive streaming, watch-stream loop, near-edge prescreen.
2. **Server core** — event bus, dispatch, global state, worker management.
3. **Prescreen module** — Stages 0/1/2 above, plus feedback ingestion.
4. **Deep understanding agents** — describe/detect/ask/OCR.
5. **Memory module** — 3-tier store (see §6).
6. **Training module** — daily/weekly/monthly runs (see §7).
7. **GPS / location / new-area tracking** — coarse localization, new-place detection, survey phases.
8. **New-agents module** — recognition agents spawned on demand; teach-by-demand lifecycle (promote → learn → consume/ignore).
9. **Positioning module** — WiFi/BLE fingerprinting + GPS anchoring (see §8).
10. **Context / compliance module** — privacy modes (don't record in X), recording rules, per-location policies.
11. **Space model / digital twin** — semantic 2.5D world model, exportable for robot training.
12. **Neighborhood knowledge module** — buildings, business signage OCR, Google Places (view-time), web scraping.

---

## 6. Memory — three tiers

- **ToC (table of contents):** hierarchical spatial index. Top levels: region → buildings → floors → rooms → surfaces → items. Doubles as the training store.
- **Notes:** summaries and semantic anchors — the "what I know about X" layer, retrievable by the agents.
- **Details:** raw data — frames, crops, full OCR, sensor logs.

Key decisions:
- **Type / instance decomposition.** A global shared type library + texture library; individual anchors are instances.
- **Anchor vs. item** node kinds. Anchors are stable places/surfaces; items are things that move or get placed on surfaces.
- **Surface hierarchy markers:** each surface/item carries a 2D offset plus a *derived* height (position along the wall), so memory stays valid from oblique viewpoints.
- **History = state-as-of queries.** Memory keeps revisions, so you can ask "what did the kitchen look like last March?" (or "where was the thing I saw Tuesday?").
- **Confidence weighting** on every entry: prior vs. evidence.

---

## 7. Training

- **Daily / weekly / monthly** runs, decay-weighted (recent > old).
- **Context tags** separate episodes: vacation ≠ work ≠ home. Training never mixes unrelated contexts.
- **Teach by demand:** when an agent can't recognize a thing, it asks → user says consume/ignore → that is a label. **Pull→miss** (wanted recall, got nothing) = precision/recall training signal.
- **Nightly reconcile + live adaptation:** merge the day's observations, promote repeated items, prune noise.
- ToC doubles as the training corpus.

---

## 8. Positioning

- **WiFi/BLE fingerprinting** with **GPS anchoring**, plus a **survey phase** for the spaces you actually inhabit.
- Space model = **prior** (OSM/Overture footprints + fire-plan posters + Places) **+ evidence**, confidence-weighted, refreshed as you revisit.
- Works indoors (where GPS dies) by fingerprint drift + anchor reconciliation.

---

## 9. Scheduler & coverage

- **Value cascade:** task / demand / novelty / agenda drive what gets processed next.
- **Coverage-per-zone metric** (not calendar time): the system knows which zones it has seen recently and which are stale, and opportunistically re-observes (walking, piggyback, robots).
- **Digital twin export:** the semantic 2.5D model (right fidelity — no full 3D) exports as a training/planning environment for robots.

---

## 10. External data policy

- **Permissive / offline:** OSM, Overture Maps, Mapillary.
- **View-time only (ToS-restricted):** Google Maps, Street View, Places. Can be *read* to answer a question; can never be stored as persistent geometry.
- **Tourist/media content** = semantic priors only (what a place is, what it's famous for), never geometry.
- **Signage OCR** during walks = a first-class neighborhood data source (businesses, hours, names).

---

## 11. Robot integration

Three tiers of mobility, one agent stack — every body is an event-bus client:

- **Scout:** R2-A1 — daily companion, follows, carries the edge sensors.
- **Transporter (mothership):** tracked platform or wheel-leg hybrid (Diablo) — carries R2 + payload + human over terrain/short distances. See hardware doc.
- **Aerial:** consumer drone — bird's-eye context, over-the-ridge recon, mapping assists.

---

## 12. Build order (bottom-up, pseudocode first)

1. **Buffer / event bus** — the spine. Frames + events in, agents out.
2. **Prescreen** — Stage 0/1/2 (cheap, continuous).
3. **Client** — capture, watch stream, adaptive streaming, near-edge prescreen.
4. **Agents** — describe/detect/ask/OCR on promoted candidates.
5. **Memory + training** — 3-tier store, nightly reconcile, teach-by-demand.
6. **Positioning + space model** — fingerprints, survey, confidence priors.
7. **Robots** — bolt bodies onto the bus; digital-twin export.
8. **Scaling** — scheduling, coverage, multi-context training.

---

## 13. Open questions / deferred

- Manipulation (robot arms/hands) — deferred fidelity upgrade; agents/vision first.
- Actual glasses hardware (standalone vs. tethered) — currently tethered to laptop; revisit when standalone units mature.
- Robot purchase order: R2-A1 first, then Diablo-class transporter (see hardware doc).
