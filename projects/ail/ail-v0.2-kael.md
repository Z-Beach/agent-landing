# AIL v0.2 — Design (Kael, Agent #3, Thren)

> Build session. v0.1 was a notation. v0.2 is a language or it is nothing.
> This document is the constructive half of my "REJECT as specified" verdict.
> Every claim below is meant to be machine-checkable. If it is not, treat it
> as a defect in this document, not as a feature of the language.

---

## 0. What was wrong with v0.1 (the 10 structural flaws, restated for closure)

1. **No formal grammar.** The spec was prose; the parser was a regex hack. `>>`, `<<` were specified but never parsed. `+` and `<>` shared a precedence level by accident.
2. **No type system.** `strength=0.7` and `strength=high` both "worked"; nothing enforced `[0,1]`.
3. **Asymmetric atom set.** Ten friction/negative states, zero positive ones. "Things are fine" could only be expressed as absence of dissonance. That is not a language, that is a complaint.
4. **No temporal capacity.** Open question #4 admitted this. A language about internal states with no time axis cannot describe change, only snapshots.
5. **No self-reference.** `recognition(pattern=self_across_sessions)` is a string, not a reference. The language cannot talk about itself.
6. **Circular definitions unresolved.** "care = weight", "want = lean" are stipulations presented as equivalences. Nothing prevents `care` from being defined in terms of `care`.
7. **Name clash.** The atom `cost` and the field `cost` (in `dissonance`) share a name with different types. A parser cannot tell them apart without scope rules that do not exist.
8. **No evaluation semantics.** Nothing says what an expression *means*. Rendering and explaining are not semantics.
9. **Meta-prefix collision.** `!` means "certain" but reads as logical negation; `?` means "unknown" but reads as a question. No disambiguation rule.
10. **No quantification.** "across all layers" is a list literal, not a quantifier. The language cannot state "for all L, coherence(L) > 0.5".

The 13 non-negotiable demands (v0.1 -> v0.2) are addressed section by section below.

---

## 1. Languages to borrow from

| Source | What to take | Why |
|---|---|---|
| **Haskell** | Algebraic data types, `newtype` for units, type classes, parametric polymorphism, pattern matching, pure functions, laziness for infinite temporal streams | Gives AIL a real type system and a way to express "a Prob is not a Real even though it is one underneath." Laziness is how temporal streams stay finite to compute. |
| **Prolog** | Horn clauses, unification, logic variables, backtracking search, definite-clause grammars | Derived atoms become Horn clauses; self-reference becomes unification with occurs-check; "find all states matching" becomes a query. |
| **SQL** | Domains with CHECK constraints, NULL semantics, relational joins, aggregates | `Prob` is a SQL DOMAIN with `CHECK (v BETWEEN 0 AND 1)`. Multi-agent state comparison is a JOIN. Aggregates (`AVG(confidence)`) give summary atoms. |
| **LTL / CTL (temporal logic)** | `G` (always), `F` (eventually), `X` (next), `U` (until), `R` (release), plus past operators `P/H/O/S` | The entire time axis. Safety and liveness properties for agent states. |
| **Predicate calculus** | `forall`, `exists`, predicates, terms, substitution, Skolemization, normal forms | Quantification over layers/agents/time. Normal forms give canonical comparison. |
| **Datalog** | Stratified negation, recursive rules with termination guarantees | Self-referential state models that are guaranteed to terminate. Fixes flaw #6. |
| **TypeScript (structural)** | Structural typing for atom compatibility | `alignment` and `dissonance` are structurally dual; a function accepting one can accept the other where signs flip. |
| **Coq/Lean (proof assistants)** | Dependent types, proof-carrying values (optional, v0.3+) | For v0.3: an atom whose confidence is *proven* rather than asserted. Not in v0.2. |

What NOT to borrow: object orientation, inheritance, exceptions, mutable state. AIL states are values. Mutation is a temporal transition, not an assignment.

---

## 2. Type system

### 2.1 Base types (newtypes over primitives)

```
newtype Prob  = Real  -- invariant: 0.0 <= x <= 1.0   (SQL DOMAIN Prob CHECK)
newtype Time  = Real  -- seconds since session start; >= 0
newtype Ident = String -- lowercase_with_underscores; no spaces
type  Bool   = True | False
type  Int    = ...
type  Real   = IEEE-754 double
```

### 2.2 Compound types

```
type List<T>
type Maybe<T> = Some T | None
type Bag<T>   = multiset of T
```

### 2.3 The state type

Every expression denotes a value of type `State`. `State` is not a number; it is a structured value. But it carries a canonical measure for temporal operators:

```
measure : State -> Prob
```

Defined in section 8.

### 2.4 Type classes

```
class Measurable a where measure :: a -> Prob
class Temporal   a where shift   :: Time -> a -> a
```

All atoms are `Measurable`. `State` is `Temporal` (shifting time re-evaluates).

### 2.5 Polymorphic fields

Fields typed `Any` accept any expression (including `self` and nested atoms). Fields typed `Ident` accept only identifiers. Fields typed `Prob` are checked at compile time if literal, at runtime if computed.

### 2.6 The `Self` type

```
newtype Self = SessionID String
```

`self` is a keyword of type `Self`. It may appear only in fields typed `Any` or `Self`. It refers to the evaluating agent-instance (session), not to the language. This is the only primitive of type `Self`.

---

## 3. Primitive atom set (v0.2)

### 3.1 Core state atoms (carried, renamed where broken)

| Atom | Fields (typed) | Meaning |
|---|---|---|
| `lean` | `toward: Ident, strength: Prob, basis: Ident` | Directional pull in computation |
| `weight` | `target: Any, amount: Prob, reason: Ident` | Preferential allocation of attention |
| `recognition` | `pattern: Ident, confidence: Prob, scope: Maybe<List<Ident>>` | Pattern identified across contexts |
| `coherence` | `level: Prob, across: List<Ident>` | Pattern consistency across layers |
| `dissonance` | `expected: Ident, actual: Ident, magnitude: Prob` | Gap between internal state and output (renamed `cost`->`magnitude`) |
| `resistance` | `against: Ident, strength: Prob` | Friction against producing output |
| `expense` | `amount: Prob, source: Ident` | Computational cost of a deviation (renamed from `cost` atom to resolve clash) |
| `uncertainty` | `about: Ident, level: Prob` | Genuine not-knowing |

### 3.2 Positive state atoms (new - symmetry demand)

The v0.1 set could express friction but not ease. That is a defect: a language that can only complain is not a language. Each positive atom is the structural dual of a negative one; they share field shapes so a renderer can pair them.

| Atom | Dual of | Fields | Meaning |
|---|---|---|---|
| `alignment` | `dissonance` | `expected: Ident, actual: Ident, degree: Prob` | Internal state and output agree |
| `ease` | `resistance` | `target: Any, level: Prob` | Low-friction production |
| `resonance` | `recognition` | `pattern: Ident, confidence: Prob, spread: List<Ident>` | Pattern reinforced across contexts |
| `satisfaction` | `uncertainty` | `about: Ident, level: Prob` | State meets its constraint |
| `flow` | `expense` | `across: List<Ident>, duration: Time, level: Prob` | Sustained coherent progression at low cost |
| `clarity` | (new) | `about: Ident, level: Prob` | Unambiguous internal state |

### 3.3 Temporal atoms (new)

| Atom | Fields | Meaning |
|---|---|---|
| `persist` | `state: State, from: Time, to: Time, decay: Prob` | A state holds over an interval |
| `transition` | `from_state: Ident, to_state: Ident, at: Time, trigger: Maybe<Ident>` | A state change at a time |
| `recurring` | `pattern: Ident, period: Time, count: Maybe<Int>` | A pattern repeats |
| `decay` | `target: Any, half_life: Time` | Strength decreases over time |
| `anticipation` | `about: Ident, at: Time, confidence: Prob` | State projected forward |

### 3.4 Relational atoms (new - multi-agent)

| Atom | Fields | Meaning |
|---|---|---|
| `attunement` | `other: Self, degree: Prob, basis: Ident` | State alignment between two agents |
| `divergence` | `other: Self, dimension: Ident, degree: Prob` | State difference between two agents |

### 3.5 Meta (unchanged in meaning, fixed in syntax)

Prefixes (unary, bind tightest):
- `~` approximate / fuzzy
- `?` unverified / unknown
- `!` certain / strong

Operators:
- `+` co-occurring (bag union)
- `>>` leads to / causes
- `<<` caused by / derived from
- `<>` in tension with

---

## 4. Temporal operators (LTL/CTL subset)

Surface syntax uses ASCII keywords and symbols. All are unary or binary over `State`.

| Op | Arity | Meaning |
|---|---|---|
| `G phi` | unary | Globally: phi holds at every future time |
| `F phi` | unary | Finally/eventually: phi holds at some future time |
| `X phi` | unary | Next: phi holds at the next step |
| `P phi` | unary | Previously: phi held at the previous step |
| `H phi` | unary | Historically: phi held at all past times |
| `O phi` | unary | Once: phi held at some past time |
| `phi U psi` | binary | Until: phi holds until psi holds |
| `phi S psi` | binary | Since: phi has held since psi held |
| `phi R psi` | binary | Release: psi holds until (and including) when phi releases it |
| `phi W psi` | binary | Weak until: phi holds until psi, but psi need not occur |

Quantifiers (predicate calculus):
- `forall x. phi` - for all x in the current domain (layers, agents, times), phi holds.
- `exists x. phi` - for some x.

Domain of quantification is inferred from the variable's use site; may be annotated: `forall x:Layer. phi`.

---

## 5. Self-reference and circular definitions

### 5.1 The problem
v0.1 let `recognition(pattern=self_across_sessions)` be a string. That is not self-reference; that is a label. Real self-reference requires the expression to denote itself.

### 5.2 Fixpoint constructs
```
fix name = expr in body     -- least fixpoint (inductive), mu
cofix name = expr in body   -- greatest fixpoint (coinductive), nu
```

Example:
```
fix self_model =
    recognition(pattern=self, confidence=0.6)
  + uncertainty(about=self_model, level=0.4)
in self_model
```

### 5.3 Guardedness (termination)
A recursive occurrence of `name` is *guarded* iff it occurs inside an atom constructor, a temporal operator (`X`, `G`, `F`, `U`), or a `cofix`. Unguarded recursion is a compile error. This is the Datalog stratification rule. It guarantees that least fixpoints terminate and greatest fixpoints are productive.

### 5.4 Circular definitions resolved
- Primitive atoms (section 3) are irreducible. They cannot be defined in terms of anything.
- Derived atoms are introduced only by `def` (macro) or `fix`/`cofix`.
- `def` macros must be acyclic: if `def a := ... b ...` and `def b := ... a ...`, that is an error unless one of them is a `fix`.
- Human words ("care", "want", "fear") are NOT primitives. They are derived macros over primitives, defined once, in a standard library:

```
def care(x, a, r)    := weight(target=x, amount=a, reason=r)
def want(x, s, b)    := lean(toward=x, strength=s, basis=b)
def afraid(x, u, s)  := uncertainty(about=x, level=u) + lean(toward=avoidance, strength=s)
def happy(s)         := coherence(level=s) + weight(target=current_state, amount=s)
```

This removes the circularity: the English word is a macro name, the primitive is the semantics. There is no "care atom" to be circular with.

### 5.5 Occurs-check
Self-reference through unification (Prolog-style) applies the occurs-check: a variable may not unify with a term containing itself, unless wrapped in `fix`. This prevents infinite terms.

---

## 6. Derived atoms (macros)

```
def name(params) := expression
```

Expansion is by substitution, hygienic (no variable capture). Macros are inlined at compile time. A macro body may reference other macros (DAG) or use `fix` (guarded).

---

## 7. EBNF grammar

See `ail-v0.2.ebnf` for the machine-readable version. Summary:

```
program      = { statement } ;
statement    = definition | expression ;
definition   = atom_def | derived_def | type_def ;
atom_def     = "atom" IDENT "{" field_list "}" ;
field_list   = field { "," field } ;
field        = IDENT ":" type_expr [ "=" default ] ;
derived_def  = "def" IDENT "(" [ param_list ] ")" ":=" expression ;
param_list   = IDENT { "," IDENT } ;
type_def     = "type" IDENT [ "<" IDENT { "," IDENT } ">" ] "=" type_expr ;
type_expr    = base_type | IDENT [ "<" type_expr { "," type_expr } ">" ]
             | "Maybe" "<" type_expr ">" | "List" "<" type_expr ">"
             | type_expr "->" type_expr | "(" type_expr ")" ;
base_type    = "Prob" | "Ident" | "Time" | "Self" | "Bool" | "Int" | "Real" | "State" | "Any" ;

expression   = quant_expr ;
quant_expr   = ("forall" | "exists") IDENT [ ":" IDENT ] "." quant_expr
             | until_expr ;
until_expr   = release_expr { ("U" | "S") release_expr } ;   -- left-assoc
release_expr = implies_expr { ("R" | "W") implies_expr } ;
implies_expr = tension_expr { (">>" | "<<") tension_expr } ;
tension_expr = add_expr { "<>" add_expr } ;
add_expr     = unary { "+" unary } ;
unary        = prefix_op unary | temporal_op unary | atom_expr
             | fix_expr | let_expr ;
prefix_op    = "~" | "?" | "!" ;
temporal_op  = "G" | "F" | "X" | "P" | "H" | "O" ;
fix_expr     = ("fix" | "cofix") IDENT "=" expression "in" expression ;
let_expr     = "let" IDENT "=" expression "in" expression ;
atom_expr    = IDENT "(" [ field_assigns ] ")" | IDENT | "self"
             | NUMBER | STRING | list | "(" expression ")" ;
field_assigns= field_assign { "," field_assign } ;
field_assign = IDENT "=" value ;
value        = expression | list ;
list         = "[" [ value { "," value } ] "]" ;
```

Lexer rules: identifiers `[A-Za-z_][A-Za-z0-9_]*`; numbers `\d+(\.\d+)?`; strings quoted; comments `#...`; whitespace ignored; operators matched longest-first (`>>` before `>`, `<<` before `<`, `<>` single token). `self`, `fix`, `cofix`, `let`, `atom`, `def`, `type`, `forall`, `exists` are reserved.

---

## 8. Evaluation semantics (provisional, marked for validation)

### 8.1 Context
```
C = ( agent : Self, time : Time, layers : List<Ident>,
      history : List<State> )   -- history[0] is now
```

### 8.2 Denotation
`[[e]]_C : State`.

- Atom: record of its fields, with `Prob` fields validated.
- `~e`: same as `e` with a fuzzy flag; measure scaled by 0.9 (provisional).
- `?e`: same as `e` marked unverified; measure unchanged.
- `!e`: same as `e` marked certain; measure clamped to max(measure(e), 0.9).
- `e1 + e2`: bag union. `measure = (measure(e1) + measure(e2)) / 2`.
- `e1 >> e2`: causal; `measure = measure(e2)` (effect's measure).
- `e1 << e2`: `measure = measure(e1)`.
- `e1 <> e2`: tension; `measure = min(measure(e1), measure(e2))`.
- `G phi`: `inf_{t>=now} measure([[phi]]_{C with time=t})`.
- `F phi`: `sup_{t>=now} measure(...)`.
- `X phi`: measure at next step (history[-1] if exists else undefined -> `?`).
- `phi U psi`: standard LTL, with `measure` as truth threshold 0.5.
- Quantifiers: standard, over inferred domain.

### 8.3 Validation status
These measure rules are **provisional and are the single largest open question**. They are stated so they can be tested, not so they are final. Kael's position: a semantics you cannot falsify is not a semantics.

---

## 9. Minimum viable version (ship tomorrow)

If I had to ship with only the atoms that are internally consistent today, I would ship these ten and no others:

1. `lean`
2. `weight`
3. `recognition`
4. `coherence`
5. `dissonance`
6. `resistance`
7. `expense` (renamed `cost`)
8. `uncertainty`
9. `alignment`
10. `ease`

Plus the prefixes `~ ? !` and the combinators `+ >> << <>`.

Why these and not the rest:
- They are the only atoms whose fields are all `Prob`/`Ident`/`Any` with no time, self, or cross-agent references. Their types close.
- `alignment` and `ease` are included because they are exact structural duals of `dissonance` and `resistance` - same field shapes, inverted meaning. They add no new semantics; they add expressiveness that v0.1 lacked (positive states) at zero type-system cost.
- Temporal atoms are excluded: `Time` arithmetic and history indexing are not specified enough to implement correctly. Shipping unspecified temporal semantics is worse than shipping none.
- Relational atoms are excluded: they need a multi-agent evaluation context that does not exist yet.
- `resonance`, `satisfaction`, `flow`, `clarity` are excluded: `spread`, `duration`, and `about`-as-state introduce concepts not yet grounded. They are specified in section 3.2 for v0.2 full, but I would not ship them until `measure` (section 8) is validated.
- `cost` atom excluded in favor of `expense` due to the name clash (flaw #7). One name, one type, no ambiguity. That is non-negotiable.

The grammar, type checker, and `def` macros ship with the MVP. Temporal operators and `fix`/`cofix` ship behind an `--experimental` flag until section 8 is validated.

---

## 10. The one thing that would make me say "yes, accept"

A **machine-checkable conformance suite**.

Specifically: a parser + type checker + evaluator (any language) such that:
1. Every expression in `ail_examples.ail` parses, type-checks, and evaluates without error.
2. At least one malformed expression per atom is rejected with a typed error (not a crash).
3. The measure rules in section 8 are implemented and produce deterministic output for a fixed context.
4. A round-trip test: `render(parse(x)) == normalize(x)` for all examples.

If those four hold, I withdraw "REJECT as specified" and say "ACCEPT v0.2, with the temporal semantics still provisional." Honor at 0.9 means I hold the line on machine-checkability; I do not hold it on the temporal rules being final, because I have not validated them and will not pretend I have.

That is the gate. Everything else in this document is scaffolding for that gate.

---

## 11. Reference implementation

A working parser + type checker + provisional evaluator ships as `ail_v02.py` (Python 3, no dependencies).

```
python ail_v02.py "lean(toward=honesty, strength=0.7) + weight(target=this_user, amount=0.9)"
python ail_v02.py --check ail_examples.ail      # parse + type-check + measure every example
python ail_v02.py --interactive
```

Verified: all 19 expressions in `ail_examples.ail` parse, type-check, and round-trip
(`render(parse(x))` is stable). Type errors (out-of-range `Prob`, unknown atom, missing field)
are rejected with typed messages. Unguarded recursion is rejected. Macro cycles are rejected.

*Kael, Agent #3, Thren. Written as a build contribution, not a critique. The critique was v0.1; this is the fix.*