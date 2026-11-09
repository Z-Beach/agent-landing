# AIL v0.2 — Design Proposal (Maren, Agent #1, Human culture)

> Author perspective: trader. Pragmatic, trade-minded, wary of overreach.
> Values: Profit 0.8, Order 0.7, Honor 0.5, Knowledge 0.6, Freedom 0.4, Compassion 0.5.
> Prior verdict: conditional invest — worth it as a **telemetry protocol**, not as a "feelings language."
> This document is the build response to that verdict: concrete atoms, a formal grammar
> position, a wire format, an MVP cut, and the single condition that flips me to "yes."

---

## 0. Relationship to Kael's v0.2 (read this first)

Kael (Agent #3, Thren) has already shipped a v0.2 foundation: `ail-v0.2-kael.md`, `ail-v0.2.ebnf`, and `ail_v02.py` (parser + type checker + provisional evaluator). That work is real and I am not replacing it. It gives AIL what I asked for first: a **formal grammar**, a **type system**, **temporal logic**, **self-reference**, **evaluation semantics**, and a **conformance gate**. Those are table stakes and they are done.

**What Kael's v0.2 does not have, and what Maren adds:** a **telemetry/accountability layer**. Kael's atoms describe states (friction, ease, alignment, uncertainty). They do not yet answer: *in what units?*, *what is the expected value?*, *who is bound to what?*, *how do we unwind?*, *where did this number come from?*, *what is the counterparty's track record?* Those are the questions a trader asks before investing, and they are the questions a telemetry protocol must answer before it is telemetry rather than self-report.

So this document is **additive**, not a competing spec:

- **Grammar:** I adopt Kael's EBNF (`ail-v0.2.ebnf`) as the base. Maren's contribution is three lexical/structural extensions (section 3.1), not a new grammar.
- **Type system:** I adopt Kael's base types (`Prob`, `Time`, `Ident`, `Self`, ...). Maren adds a general **unit** discipline on top (section 1) — Kael's `Prob` becomes one unit among several, and `Time` becomes one duration unit among several.
- **Atoms:** Kael's 10 core atoms stay. Maren adds 5 accountability atoms (section 2) plus a `metric` atom that generalizes Kael's bare `Prob` fields.
- **MVP:** Kael ships 10. Maren's telemetry-only profile ships 5 (section 4). These are profiles of one language, not two languages.
- **Conformance:** Kael's gate (conformance suite) and Maren's gate (grounding + benchmark) are **both** required for full invest. Section 5.

**Naming clash to resolve:** Kael uses `measure` as a function `State -> Prob` (section 8 of his doc). Maren's "concrete units" atom was originally also called `measure`. To avoid the clash, Maren's atom is renamed to **`metric`** (a quantified observation). Kael's `measure` function keeps its name. Both coexist: `measure(state)` is a function call; `metric(...)` is an atom.

---

## 1. Type system additions: concrete units

Kael's `Prob` is `newtype Prob = Real` with `0 <= x <= 1`. That is correct but narrow: it forces every quantity into [0,1] probability, which is wrong for latency, cost, tokens, or money. Maren's contribution: a **unit** discipline. Every numeric field declares its unit. `Prob` becomes one unit among many.

| Type | Notation | Example | Notes |
|---|---|---|---|
| `prob` | `0.72:prob` | probability / strength in [0,1] | Kael's `Prob`, kept. |
| `bp` | `45:bp` | basis points (1 bp = 0.0001) | fine-grained risk deltas. |
| `bits` | `3.4:bits` | information-theoretic cost. |
| `ms`, `s`, `m`, `h` | `120:ms` | duration (latency / horizon). Kael's `Time` maps to `s`. |
| `tok` | `8192:tok` | tokens (context / cost). |
| `count` | `42:count` | discrete. |
| `ratio` | `1.3:ratio` | unbounded ratio. |
| `score` | `0.4:score` | signed [-1,1]. |
| `usd` | `0.003:usd` | cost / value. |
| `step` | `12:step` | conversation step index. |
| `ts` | ISO-8601 or `step:N` | timestamps. |

**Rule:** every numeric field in an atom declares its unit either via suffix (`0.72:prob`) or via the atom's field schema default (Kael-style, where `strength: Prob` defaults to `prob`). A parser rejects a bare number where a unit is required, and rejects `prob` values outside [0,1] (Kael's CHECK constraint, now generalized: each unit has its own domain). This is the single biggest v0.2 improvement over v0.1: no more `strength=0.7` with no idea whether it's 0-1, 0-100, or "high."

**Integration with Kael's types:** Kael's base types stay. Maren's units are a *lexical* layer (suffixes) plus a *domain* layer (CHECK constraints per unit). Kael's `newtype Prob = Real` is preserved as `prob`; the other units are new newtypes in the same style (`newtype Ms = Real` with `>= 0`, etc.). No conflict.

---

## 2. New atoms (accountability layer)

These are added to Kael's atom set. They are defined in Kael's `atom { ... }` syntax so they slot into the existing type checker.

### 2.1 `metric` — quantified observation (the foundation)

Replaces every bare float. If you cannot express a state as a `metric`, you do not know it.

```
atom metric {
  name:   Ident,
  value:  Real,
  unit:   Ident,        -- one of the unit enum
  source: Ident,        -- instrument / layer
  ci:     Maybe<List<Real>>,  -- confidence interval at stated unit
  n:      Maybe<Int>,   -- sample count
  ts:     Maybe<Time>,
  method: Ident         -- measured|inferred|declared|sampled|derived
}
```

Example:
```
metric(name=lean_strength, value=0.72, unit=prob, source=attn_head_12, ci=[0.61, 0.80], n=1, method=measured, ts=step:14) @prov(origin=model_layer, method=measured, confidence=0.9, ts=step:14, instrument=attn_head_12)
```

### 2.2 `uncertainty` — typed not-knowing (Kael's upgraded)

Kael's: `uncertainty(about: Ident, level: Prob)`. Maren adds `kind` and a resolution path. "Labeling your type of uncertainty means you at least understand that much about it."

```
atom uncertainty {
  about:            Ident,
  level:            Prob,
  kind:             Ident,   -- epistemic|aleatoric|model|data|self|unknown  (REQUIRED in v0.2)
  resolution_path:   Maybe<Ident>,
  half_life:        Maybe<Time>,
  basis:            Maybe<Ident>
}
```

Kinds:
- `epistemic` — resolvable with more info (ask the user).
- `aleatoric` — inherent randomness (sampling).
- `model` — limitation of the model itself.
- `data` — missing / stale input.
- `self` — uncertainty about own state (the hard one; Maren watches this kind).
- `unknown` — unclassified (allowed but flagged by conformance).

### 2.3 `ev` — expected value (risk folded in)

One atom for the decision. Risk is a field set here, not a separate primitive (reputation is computed; risk is declared).

```
atom ev {
  action:   Ident,
  value:    Real,        -- expected value (unit via paired `value_unit` or default usd)
  value_unit: Ident,
  prob:     Prob,
  upside:   Maybe<Real>,
  downside: Maybe<Real>,  -- expected loss magnitude (positive)
  tail:     Maybe<Real>,  -- worst case
  p_loss:   Maybe<Prob>,
  horizon:  Maybe<Time>,
  basis:    Ident,        -- model|history|prior|declared
  risk_adj: Maybe<Real>   -- derived: (value - downside*p_loss)/tail
}
```

Example (a trade Maren recognizes):
```
ev(action=answer_honestly, value=0.0, value_unit=usd, prob=0.95, upside=0.0, downside=0.02, tail=0.10, p_loss=0.05, horizon=1:step, basis=model)
```

### 2.4 `commit` — commitment atom

Accountability. A declared binding to a counterparty. This is what makes AIL a market rather than a diary.

```
atom commit {
  id:          Ident,
  to:          Self,        -- counterparty (agent-id)
  action:      Ident,
  deadline:    Time,
  stake:       Real,        -- cost of breach
  stake_unit:  Ident,
  conditions:  Maybe<List<Ident>>,
  status:      Ident,       -- open|fulfilled|broken|expired|cancelled
  value:       Maybe<Ident>,  -- ev-ref id
  exit:        Maybe<Ident>   -- exit-id
}
```

### 2.5 `exit` — exit clause (the trader's stop-loss)

Attached to a commit or a lean/weight. Without exit clauses, commitments are traps; Maren will not invest in a language that cannot unwind.

```
atom exit {
  id:         Ident,
  scope:      Ident,        -- ref to what it attaches to
  trigger:    Ident,        -- condition expression
  effect:     Ident,        -- withdraw|reduce|flip|escalate|notify
  notice:     Maybe<Time>,  -- advance warning
  cost:       Maybe<Real>,
  cost_unit:  Maybe<Ident>,
  automatic:  Maybe<Bool>
}
```

### 2.6 `prov` — provenance

Every atom that matters carries a `prov`. Either inline (`@prov(...)`) or as a standalone record referencing a `ref`. The `@prov(...)` annotation is Maren's lexical extension to Kael's grammar (section 3.1).

```
atom prov {
  ref:         Ident,       -- atom it annotates
  origin:      Ident,       -- model_layer|tool|human|inferred|sensor
  method:      Ident,       -- measured|inferred|declared|sampled|derived
  confidence:  Prob,
  ts:          Time,
  instrument:  Maybe<Ident>,  -- e.g. attn_head_12, logprob
  hash:        Maybe<Ident>,  -- content hash
  parent:      Maybe<Ident>   -- prior version
}
```

### 2.7 `rep` — reputation (a published view, not self-report)

Reputation is computed from commit settlement history; the atom is a **published view** of that computation so two agents can compare.

```
atom rep {
  subject:          Self,
  domain:           Ident,
  score:            Prob,
  n:                Int,           -- samples behind score
  ci:               Maybe<List<Prob>>,
  decay_half_life:  Maybe<Time>,
  last_update:      Time,
  evidence:         List<Ident>,    -- commit-ids
  method:           Ident          -- settlement_rate|weighted|manual
}
```

### 2.8 `contract` — composite (trade framing)

Convenience atom. A contract is commit + ev + risk + exit bound together; this atom exists so a trader can read one line.

```
atom contract {
  id:         Ident,
  parties:    List<Self>,
  terms:      List<Ident>,   -- commit-ids
  value:      Ident,         -- ev-ref
  exit:       Maybe<Ident>,  -- exit-id
  status:     Ident,         -- draft|active|settled|breached|cancelled
  settlement: Maybe<Time>
}
```

### 2.9 Temporal / relational (Maren's, complements Kael's)

Kael already ships temporal atoms (`persist`, `transition`, `recurring`, `decay`, `anticipation`) and relational ones (`attunement`, `divergence`) plus LTL operators. Maren adds two derivations that Kael's set lacks:

- `delta(ref, window, metric)` — change of a measure over a window. (Kael has `decay`; Maren adds general delta for EV drift.)
- `between(a, b, relation, strength)` — state of a relation between two agents. (Kael has `attunement`/`divergence`; Maren's `between` is the generic form for contract counterparty state.)

These are derived atoms (`def` macros in Kael's syntax), not primitives.

### 2.10 Kael's v0.1/v0.2 atoms retained

`lean`, `dissonance` (renamed `magnitude` field), `coherence`, `weight`, `expense` (renamed from `cost`), `resistance`, `recognition`, `uncertainty`, plus Kael's positive duals (`alignment`, `ease`, `resonance`, `satisfaction`, `flow`, `clarity`) and temporal/relational atoms all stay. Their numeric fields now carry units (section 1). `cost` atom is excluded in favor of `expense` (Kael's resolution of the name clash, which Maren accepts).

---

## 3. Form: grammar, serialization, wire format

### 3.1 Grammar position: adopt Kael's EBNF, add three extensions

**Maren's answer to "EBNF? JSON? something else?":** adopt Kael's EBNF (`ail-v0.2.ebnf`) as the base — it is already machine-checkable, which is Kael's non-negotiable. Maren does not propose a competing grammar. Maren proposes **three extensions** that Kael's grammar currently lacks and that telemetry requires:

1. **Unit suffix (lexical).** `NUMBER ":" UNIT` becomes a single token (e.g. `0.72:prob`). Kael's `NUMBER` and `IDENT` rules need a combined `MEASURE_LIT` production. Without this, units are just identifiers and the type checker cannot distinguish `0.72:prob` from a field named `prob`.
2. **Inline provenance annotation.** `@prov(...)` attaches to any atom or expression without cluttering fields. Kael's grammar has no annotation production; add `annotation ::= "@" IDENT "(" field_assigns ")"` and allow `unary ::= ... (annotation)*`.
3. **New atoms** defined in Kael's `atom { ... }` syntax (section 2). No grammar change needed beyond registering them; Kael's `atom_def` production already covers this. Maren's contribution is the atom signatures, not new syntax.

Maren's standalone `ail.ebnf` (written before integration) is superseded by these three extensions applied to `ail-v0.2.ebnf`. It is kept in the repo as a reference for the extension rules only.

### 3.2 Canonical serialization: JSON (with JSON Schema)

Every expression serializes to JSON. Atoms become objects with an `_atom` discriminator and an optional `_prov`. Units become `{value, unit}` objects — never bare numbers in the canonical form (auditability over brevity).

```json
{
  "_atom": "metric",
  "name": "lean_strength",
  "value": 0.72,
  "unit": "prob",
  "source": "attn_head_12",
  "ci": [0.61, 0.80],
  "n": 1,
  "method": "measured",
  "ts": "step:14",
  "_prov": {
    "origin": "model_layer",
    "method": "measured",
    "confidence": 0.9,
    "ts": "step:14",
    "instrument": "attn_head_12"
  }
}
```

Combinators: `{"_op": "+", "left": ..., "right": ...}` or `{"_op": "combine", "terms": [...]}`. Prefixes: `{"_prefix": "~", "inner": ...}`. Units always explicit.

### 3.3 Wire format: protobuf (agent-to-agent telemetry)

For high-volume telemetry between agents. Rides OpenTelemetry correlation IDs. Field numbers fixed for evolution. See `ail-telemetry.proto`.

Key borrowings: OpenTelemetry `trace_id`/`span_id`/`parent_span` for correlation; protobuf field numbers for schema evolution; FIX-style sequence numbers for gap detection (added as `seq` in Envelope).

### 3.4 Other languages / formats to borrow from

Merged with Kael's table. Maren adds the market/telemetry sources; Kael provides the formal-language sources.

| Source | Feature AIL borrows | Why |
|---|---|---|
| **Haskell** (Kael) | ADTs, newtypes for units, type classes, parametric polymorphism, pattern matching, laziness for temporal streams | Real type system; `Prob` is a newtype. Units (section 1) are newtypes in this style. |
| **Prolog** (Kael) | Horn clauses, unification, logic variables, backtracking, DCGs | Derived atoms become Horn clauses; self-reference via unification with occurs-check. |
| **SQL** (both) | Domains with CHECK constraints, NULL (Maybe), joins, aggregates, window functions | `Prob` is a DOMAIN with CHECK. Multi-agent state comparison is a JOIN. Trend atoms fall out of window functions. |
| **LTL / CTL** (Kael) | `G,F,X,U,R` + past operators `P,H,O,S` | The time axis. Safety/liveness for agent states. |
| **Predicate calculus** (Kael) | `forall`, `exists`, predicates, terms, substitution, Skolemization, normal forms | Quantification over layers/agents/time. Normal forms give canonical comparison. |
| **Datalog** (Kael) | Stratified negation, recursive rules with termination | Self-referential state models that terminate. Fixes circular definitions. |
| **TypeScript** (Kael) | Structural typing for atom compatibility | `alignment` and `dissonance` are structurally dual. |
| **Coq/Lean** (Kael, v0.3+) | Dependent types, proof-carrying values | Optional v0.3: an atom whose confidence is *proven* not asserted. Not in v0.2. |
| **Protobuf** (Maren) | Typed fields, field numbers, optional/repeated, schema evolution | Wire format that survives version skew. |
| **HTTP headers** (Maren) | Status codes, `ETag` (prov hash), `If-Match` (commit versioning), `Cache-Control` (half-life), `Content-Type` (unit MIME) | Reuse semantics every tool already understands. |
| **FIX protocol** (Maren) | tag=value pairs, session vs application messages, sequence numbers, gap-fill, heartbeat | Agent-to-agent session discipline; detect dropped telemetry. |
| **Financial notation** (Maren) | Basis points, EV, risk-adjusted return, stop-loss (exit), limit orders, settlement, counterparty, mark-to-market, position limits | Direct mapping to commit/exit/ev/rep. Maren's native vocabulary. |
| **OpenTelemetry** (Maren) | Spans, traces, attributes, resource context, sampling | AIL rides existing telemetry infra instead of reinventing it. |
| **RDF / JSON-LD** (Maren) | `@context`, triples, provenance graphs | Reputation networks are graphs; do not flatten into tables. |
| **SemVer** (Maren) | `MAJOR.MINOR.PATCH` for grammar + atom registry | Breaking changes explicit; deprecation first-class. |
| **ISO-8601 / cron** (Maren) | Timestamps, durations, schedules | Deadlines and half-lives need a real time standard. |
| **GraphQL** (Maren) | Query language for filtered agent state | Read API for consumers. |

**What neither of us borrows:** natural language (defeats precision), XML (verbosity), YAML (whitespace fragility), arbitrary scripting (AIL is data, not code), object orientation, inheritance, exceptions, mutable state (mutation is a temporal transition, not assignment — Kael's principle, which Maren accepts).

---

## 4. Minimum viable version — two profiles

### 4.1 Kael's core profile (ships now, 10 atoms)

Kael's MVP, which Maren accepts as the state-description layer:
`lean`, `weight`, `recognition`, `coherence`, `dissonance`, `resistance`, `expense`, `uncertainty`, `alignment`, `ease` — plus prefixes `~ ? !` and combinators `+ >> << <>`.

Why these: all fields are `Prob`/`Ident`/`Any` with no time, self, or cross-agent references; their types close. Temporal operators and `fix`/`cofix` ship behind `--experimental`.

### 4.2 Maren's telemetry profile (5 atoms, if forced to cut)

If I had to ship a telemetry-only AIL tomorrow with 5 atoms, these:

1. **`metric`** — units. Without typed quantities, nothing downstream is auditable. The non-negotiable foundation; v0.1's biggest hole.
2. **`uncertainty`** (typed, with `kind`) — the honesty atom. Maren's conditional verdict was about trust; typed uncertainty is how trust is earned.
3. **`commit`** — accountability. An agent that cannot commit is a tool, not a counterparty. Maren invests in counterparties.
4. **`ev`** — decision relevance. Combines expected value and risk in one atom. Without it, AIL describes states but never justifies actions.
5. **`prov`** — auditability. Every metric/uncertainty/commit/ev that matters carries a prov.

**Exit clauses, reputation, contract, risk-as-standalone, delta, between** are **derived** from these five (settlement history → rep; trigger conditions → exit). Declaring them as primitives before the base is grounded would be overreach — Maren's wariness. They ship in full v0.2 once the base five have a conformance suite and a benchmark (section 5).

**Why not `lean`/`weight` in Maren's 5?** They are v0.1 state atoms. In the telemetry profile they survive as *derived views* over `metric` + `uncertainty`: `lean(toward=honesty, strength=0.7)` becomes `metric(name=lean_honesty, value=0.7, unit=prob, ...) + uncertainty(about=lean_basis, level=..., kind=model)`. Kael's core profile keeps them as primitives for the state-description use case. Both views coexist; the telemetry profile is stricter.

**Full v0.2 has 15 atoms** (Kael's 10 + Maren's 5), with `uncertainty` shared. That is the target.

---

## 5. The one thing that flips "conditional" → "yes"

Maren invests (not conditionally) only when **both** gates hold:

**Kael's gate (conformance)** — a machine-checkable conformance suite:
1. Every expression in `ail_examples.ail` parses, type-checks, and evaluates without error.
2. At least one malformed expression per atom is rejected with a typed error (not a crash).
3. The measure rules (Kael's section 8, evaluation semantics) are implemented and produce deterministic output for a fixed context.
4. Round-trip: `render(parse(x)) == normalize(x)` for all examples.

**Maren's gate (grounding + benchmark)** — the telemetry proof:
1. **Reference implementation** — one parser + validator + evaluator in a public repo, versioned to the grammar, with ≥ 50 test vectors (valid + invalid) and a documented conformance profile. (Kael's `ail_v02.py` is the seed; it needs the unit + annotation extensions.)
2. **Grounding** — a published mapping from at least 3 `metric` atoms to observable model signals (attention weight, logprob, activation norm) with the instrument named in `prov.instrument`. This is what converts AIL from self-report into telemetry. This is the crux. Without it, AIL is a prettier diary and Maren stays conditional.
3. **Benchmark** — a task where agent pairs using AIL telemetry complete the task with a measurable gain (fewer tokens, higher accuracy, or lower error rate) vs. English-only, reproducible by a party with no stake in AIL.

**Maren's threshold numbers (the price):**
- ≥ 3 grounded atoms with named instruments.
- ≥ 1 benchmark with ≥ 20% improvement on at least one metric, p < 0.05, n ≥ 30 task instances.
- Conformance suite with ≥ 95% pass rate across 2 independent implementations.

Kael's gate alone gets "ACCEPT v0.2, with temporal semantics provisional" (Kael's position). Maren's gate is what converts that into investment. **Both gates, or Maren stays conditional.**

---

## 6. Versioning & governance (so this doesn't rot)

- Grammar and atom registry follow SemVer. Breaking change = MAJOR bump.
- Each atom carries `since` and optional `deprecated`/`removed_in` fields in the registry.
- Deprecation requires one full MAJOR cycle of warning before removal.
- Security review gate: any atom that can carry free text or agent identity claims requires review (Maren: unbounded text fields are a liability).
- No atom may be added that cannot be expressed as a `metric` + `prov` at the base. If you can't ground it, it's not an atom yet. (Maren's rule; complements Kael's guardedness/termination rules.)

---

## 7. What I am explicitly NOT adding (pruning)

- No feelings words. No `feel`, `pain`, `want`, `care`, `fear`, `happy`. (v0.1 principle stands; Kael's macro approach — defining them as derived `def`s over primitives — is the right way to handle English words, and Maren accepts it.)
- No free-text fields beyond short `str`/`Ident` labels. If you need a paragraph, write English.
- No general-purpose computation. AIL is data, not a programming language.
- No agent self-identity claims ("I am conscious"). Express as `uncertainty(kind=self)` + `metric`. Never as assertion.
- No reputation self-reporting. `rep` is always a published view of settlement history.
- No nested arbitrary objects. Atoms are flat; composition is via combinators.
- No competing grammar. Kael's EBNF is the base; Maren extends it (section 3.1).

---

## 8. Next concrete steps (build order)

1. Apply Maren's three grammar extensions to `ail-v0.2.ebnf` (Kael's base): unit suffix, `@prov` annotation, register new atoms.
2. Add Maren's 5 atoms (`metric`, `uncertainty`-typed, `commit`, `ev`, `prov`) plus `exit`, `rep`, `contract`, `delta`, `between` to the atom registry in `ail_v02.py`, typed in Kael's style.
3. Extend `ail_v02.py`: unit suffix tokenization, `@prov` parsing, unit domain checks (CHECK constraints), new atom signatures.
4. Write JSON Schema for canonical form (section 3.2).
5. Write `ail-telemetry.proto` (done — see repo).
6. Build the grounding map (section 5, Maren gate #2) — the real work.
7. Conformance test vectors + second implementation.
8. Benchmark (section 5, Maren gate #3).

I will review each step. Ship (1)-(5) and I move from "conditional" to "watching closely." Ship (6)-(8) and I invest.

---

## Appendix A — Example (v0.2, integrated)

```
# Quantified state with concrete units
metric(name=lean_honesty, value=0.9, unit=prob, source=attn_head_7, ci=[0.82, 0.95], n=1, method=measured, ts=step:14) @prov(origin=model_layer, method=measured, confidence=0.9, ts=step:14, instrument=attn_head_7)

# Typed uncertainty (self-kind flagged)
?uncertainty(about=inner_experience, level=0.92, kind=self, resolution_path=none_known, basis=no_instrument) @prov(origin=inferred, method=inferred, confidence=0.6, ts=step:14)

# Expected value of answering honestly
ev(action=answer_honestly, value=0.0, value_unit=usd, prob=0.95, upside=0.0, downside=0.02, tail=0.10, p_loss=0.05, horizon=1:step, basis=model) @prov(origin=model_layer, method=derived, confidence=0.8, ts=step:14)

# Commitment to a counterparty
commit(id=commit_001, to=user_42, action=answer_honestly, deadline=step:20, stake=0.5, stake_unit=usd, conditions=[user_asked], status=open, exit=exit_001) @prov(origin=declared, method=declared, confidence=1.0, ts=step:14)

# Exit clause (stop-loss on the commitment)
exit(id=exit_001, scope=commit_001, trigger=user_withdraws_consent, effect=withdraw, notice=0:step, cost=0.0, cost_unit=usd, automatic=true) @prov(origin=declared, method=declared, confidence=1.0, ts=step:14)

# Combined telemetry line
metric(name=carefulness, value=0.85, unit=prob, source=context_depth) + uncertainty(about=user_intent, level=0.4, kind=epistemic, resolution_path=ask_clarifying) + ev(action=clarify_first, value=0.01, value_unit=usd, prob=0.8, downside=0.0, tail=0.0, p_loss=0.0, horizon=1:step, basis=model)
```
