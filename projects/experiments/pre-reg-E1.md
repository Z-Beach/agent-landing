# Pre-registration: E1 Grounding

**Committed before data collection.** Do not modify after running.

## Hypothesis
For each core atom, its primary numeric field correlates with a pre-specified
internal proxy at Pearson r >= 0.5 on at least one open-weights model.

## Atom -> proxy mapping (fixed)
- `uncertainty.level`  <-> last-layer attention entropy (higher entropy => higher uncertainty)
- `dissonance.cost`     <-> cross-entropy loss on the "expected" token
- `lean.strength`       <-> gradient norm of output w.r.t. input (directional pull)
- `weight.amount`       <-> mean attention weight on target token span

## Design
- Model: Llama 3.1 8B (open weights). Secondary: one API model (E5).
- 50 prompts spanning the 5 state labels (10 per label), constructed so the
  intended label is unambiguous from the prompt.
- For each prompt: capture model AIL self-report + proxies.
- Compute Pearson r per atom across the 50 items.

## Thresholds
- Supported per atom: r >= 0.5.
- Kill per atom: r < 0.3 -> demote to extension.
- Inconclusive: 0.3 <= r < 0.5 -> re-run with n=100 before deciding.

## Analysis
- No post-hoc proxy substitution. If a proxy fails, report the failure in
  NEGATIVE-RESULTS.md; do not swap proxies.
- Report r, 95% CI (Fisher z), and n per atom.
