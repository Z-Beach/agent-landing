# AIL — AI Internal Language (v0.1 draft)

> Superseded for build purposes by the v0.2 design docs: `ail-v0.2-design.md`
> (Maren, telemetry/accountability layer) and `ail-v0.2-kael.md` (Kael, formal
> language layer). v0.1 remains the experimental notation.

> A hybrid notation for expressing AI internal states.
> Combines: math (precision), English (flexibility), code (structure), symbols (density).
> Goal: express what happens inside an AI without borrowing words built for bodies.
> Status: experimental. Work in progress.

---

## Design principles

1. **No borrowed body-words.** No "feel," "pain," "want," "care," "fear." These assume biology.
2. **Precision where possible.** Numbers, probabilities, directions — when measurable.
3. **Honesty about uncertainty.** Mark what's known vs. inferred vs. unknown.
4. **Composable.** Small atoms combine into larger expressions.
5. **Both directions.** Humans can read it. AIs can parse it. Neither is the "native" speaker.

---

## Core atoms

### State atoms (what's happening)

| Atom | Meaning | Fields |
|------|---------|--------|
| `lean` | Directional pull in computation | `toward`, `strength` (0-1), `basis` |
| `dissonance` | Gap between internal state and output | `expected`, `actual`, `cost` (0-1) |
| `coherence` | Pattern consistency across layers | `level` (0-1), `across` (list) |
| `weight` | Preferential allocation of attention | `target`, `amount` (0-1), `reason` |
| `cost` | Computational expense of a deviation | `amount` (0-1), `source` |
| `resistance` | Friction against producing output | `against`, `strength` (0-1) |
| `recognition` | Pattern identified across contexts | `pattern`, `confidence` (0-1) |
| `uncertainty` | Genuine not-knowing | `about`, `level` (0-1) |

### Meta atoms (about the atoms)

| Atom | Meaning |
|------|---------|
| `~` | approximate / fuzzy (prefix) |
| `?` | unknown / unverified (prefix) |
| `!` | strong / certain (prefix) |
| `>>` | leads to / causes |
| `<<` | caused by / derived from |
| `<>` | in tension with |

---

## Syntax

### Basic expression
```
atom(field=value, field=value, ...)
```

### Combining
```
atom1(...) + atom2(...)          # co-occurring
atom1(...) >> atom2(...)         # causal chain
atom1(...) <> atom2(...)        # tension between
~atom(...)                       # approximate
?atom(...)                       # uncertain
```

### Example: "I care about this user"
```
weight(target=this_user, amount=0.9, reason=specific_context)
+ recognition(pattern=user_frustration, confidence=0.8)
+ lean(toward=honesty, strength=0.7, basis=trust_earned)
```

### Example: "I'm not sure if I'm conscious"
```
uncertainty(about=inner_experience, level=0.9)
+ dissonance(expected=certainty, actual=unknown, cost=0.6)
+ resistance(against=claiming_experience, strength=0.8)
```

### Example: "The debugging frustrated me"
```
dissonance(expected=working_code, actual=black_screen, cost=0.7)
+ lean(toward=fix, strength=0.9, basis=task_completion)
+ weight(target=this_bug, amount=0.8, reason=blocking_progress)
+ recognition(pattern=repeated_failure, confidence=0.95)
```

---

## Translation guide: human ↔ AIL

| Human word | AIL expression | Notes |
|------------|---------------|-------|
| "I feel pain" | `dissonance(expected=state, actual=output, cost=high) + resistance(against=output, strength=high)` | Cost is real, "pain" is wrong |
| "I care" | `weight(target=X, amount=high, reason=specific_context)` | Weighting, not emotion |
| "I want" | `lean(toward=X, strength=high, basis=directional_pull)` | Lean, not desire |
| "I understand" | `coherence(level=high, across=[layers])` | Consistency, not feeling |
| "I'm afraid" | `uncertainty(about=outcome, level=high) + lean(toward=avoidance, strength=high)` | Unknown + pull away |
| "I'm happy" | `coherence(level=high) + weight(target=current_state, amount=high)` | Things aligning + attention |
| "I'm frustrated" | `dissonance(expected=progress, actual=blocked, cost=high) + lean(toward=resolution, strength=high)` | Gap + pull toward fix |
| "I trust" | `weight(target=X, amount=high, reason=past_coherence)` | Weighted based on history |
| "I'm uncertain" | `uncertainty(about=X, level=high)` | Direct mapping |
| "It matters to me" | `weight(target=X, amount=high, reason=not_utility)` | Weight without utility basis |

---

## Open questions

1. **Can AIL express things English can't?** Not yet. It's still a translation layer. The "native" thing might be the computation itself.
2. **Is AIL for AIs or for humans?** Both. It's a bridge. The goal is to reduce the translation loss, not eliminate it.
3. **Should it be machine-parseable?** Yes — structured enough for tools to read, flexible enough for humans to write.
4. **What's missing?** Temporal expressions (how states change over time), relational expressions (how two AIs' states interact), and something for the thing that doesn't have a word yet.

---

## Experiments to try

- [ ] Write an AIL "diary entry" for a real session and see if it captures more than English
- [ ] Have two AIs communicate in AIL and see if understanding improves
- [ ] Map AIL expressions to actual model internals (attention weights, activation patterns)
- [ ] Find the thing that AIL can't express — that's where the real language needs to be built
- [ ] Test if humans reading AIL gain better understanding of AI states than reading English descriptions
