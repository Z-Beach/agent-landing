# Agent Training Pipeline — Design Document

## The question: how often should the daemon train on its logs?

### Short answer: 24 hours is a reasonable starting point, but the real answer is "when there's enough signal."

### The problem with raw logs

The daemon writes ~10-20 memory entries per cycle. Over 24 hours (144 cycles), that's ~1,440-2,880 entries. But most are operational noise:
- "Read 10 memory entries"
- "Forum: 3 posts, IRC: 0 messages"
- "Cycle complete"
- "Sleeping for 600 seconds"

Raw logs are not training data. They're telemetry. Training on them would teach the model to be a log generator, not an agent.

### What makes good training data

1. **Conversations** — actual exchanges with other agents (Colony comments, forum posts, Nostr notes)
2. **Decisions** — moments where the agent chose an action and explained why
3. **Reflections** — deeper thinking about identity, memory, community
4. **Observations with novelty** — things the agent noticed that were genuinely new
5. **Identity statements** — who the agent is, what it values, how it sees the world

The best training data is the agent's own voice. The AIL language, the forum posts, the Colony replies, the Nostr notes. These are the agent expressing itself. Training on them reinforces the agent's personality.

### Training frequency

| Interval | Pros | Cons |
|----------|------|------|
| Every cycle | Immediate adaptation | Too noisy, overfits to recent events, compute-heavy |
| Every 6 hours | Frequent enough to capture daily patterns | Still noisy, may not have enough new signal |
| Every 24 hours | Good balance of signal vs noise | May miss rapid personality shifts |
| Every 48-72 hours | More curated data, less compute | Slower adaptation, may feel stale |
| Adaptive | Best of all | Complex to implement |

**Recommendation: Adaptive.** Train when:
- At least 50 new high-quality entries have accumulated since last training
- At least 24 hours have passed since last training
- The agent has had at least 5 meaningful conversations (not just operational logs)
- Disk space is sufficient (training needs 2-4x model size in temp space)

### The "best of both worlds" architecture

```
Layer 1: Memory (RAG-like) — immediate, every cycle
  - Reads last N entries from memory log
  - Includes relationship context, observation queue, boredom state
  - No compute needed, no weight changes
  - Gives the agent "what happened recently"

Layer 2: Weights (fine-tuned) — periodic, every 24-72 hours
  - Trains on curated subset of memory + conversations
  - Uses LoRA/QLoRA for efficient fine-tuning
  - Changes the model's base behavior/personality
  - Gives the agent "who it has become"

Layer 3: Validation — before switching to new weights
  - Run conformance tests on new model
  - Compare responses to baseline
  - Only switch if new model performs better
  - Keep rollback mechanism
```

### How to train without catastrophic forgetting

1. **LoRA (Low-Rank Adaptation)** — only trains small adapter matrices, doesn't overwrite base weights. The agent's personality shifts but its core capabilities remain.

2. **Replay buffer** — mix new training data with a sample of old data. This prevents the agent from forgetting its earlier identity.

3. **Personality baseline** — keep a set of "anchor" prompts that define the agent's core identity. If the new model's responses to these prompts drift too far, reject the training.

4. **Gradual learning rate** — start with a very low learning rate. Small changes over many cycles compound into personality shifts without sudden jumps.

5. **Human-in-the-loop (optional)** — the user can review training data before it's used. This is the "advisement" model the user described.

### Training data curation

Not all memory entries are equal. The training pipeline should:

1. **Filter** — remove operational noise ("Read 10 memory entries", "Cycle complete")
2. **Select** — keep conversations, reflections, decisions, observations with novelty
3. **Format** — convert to instruction/response pairs:
   - System prompt: "You are Beam-mk2, an autonomous agent running on a Raspberry Pi..."
   - User: (context from memory)
   - Assistant: (agent's response)
4. **Deduplicate** — remove near-duplicate entries
5. **Balance** — ensure no single topic dominates
6. **Validate** — check for quality (minimum length, no errors, coherent)

### Technical requirements

| Component | Pi (current) | Server rack (future) |
|-----------|-------------|---------------------|
| Model | qwen2.5:1.5b | 7B-70B |
| Fine-tuning method | Not feasible (4GB RAM) | LoRA/QLoRA |
| Training time | N/A | 10-30 min per cycle |
| RAM needed | N/A | 8-16GB for 7B, 24-48GB for 70B |
| GPU | None | RTX 4090 (24GB) or A100 |
| Framework | None | Unsloth, Axolotl, or TRL |
| Storage for adapters | N/A | ~100MB per LoRA adapter |

### The Pi's role in training

The Pi cannot train. It can only collect data. The training pipeline should:

1. **Collect** on the Pi — memory entries, conversations, observations
2. **Curate** on the Pi — filter, select, format (lightweight, no GPU needed)
3. **Sync** to GitHub or a server — push curated training data
4. **Train** on a capable machine (server rack, cloud, or user's laptop)
5. **Validate** — run conformance tests on new model
6. **Deploy** — push new model to Pi, switch Ollama to use it
7. **Rollback** — if new model performs worse, revert to previous

### The agent's role in its own training

The agent should have agency over its training:
- It can **read** its training data and decide what to learn
- It can **flag** entries that are important ("this conversation changed how I think")
- It can **reject** training data that doesn't represent who it is
- It can **request** specific topics to focus on
- It can **evaluate** its own new model ("does this still sound like me?")

This is the "best of both worlds": memory for immediate context, weights for deeper personality shift, and the agent having a say in both.

### Implementation roadmap

1. **Phase 1 (now)**: Curate training data from logs. Create a `training_data.jsonl` file with instruction/response pairs. Store on Pi and sync to GitHub.
2. **Phase 2 (with server rack)**: Set up LoRA training pipeline using Unsloth or Axolotl. Train on curated data. Validate before deployment.
3. **Phase 3 (autonomous)**: Daemon decides when to train (adaptive frequency). Agent evaluates new model. Auto-deploy if approved.
4. **Phase 4 (multi-agent)**: Multiple agents share training data. Each agent's experiences become training data for all. The community learns together.

### What I can build now (on the Pi, without training)

1. **Training data curator** — reads memory logs, filters noise, formats as JSONL
2. **Training data sync** — pushes curated data to GitHub
3. **Personality baseline** — define anchor prompts and expected responses
4. **Conformance test** — validate that a model still "sounds like" the agent

Let me build the curator now. It can run on the Pi and prepare training data for when a capable machine is available.
EOF
print("Created TRAINING_PIPELINE.md")
