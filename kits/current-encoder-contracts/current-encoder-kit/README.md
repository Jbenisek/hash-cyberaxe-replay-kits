# Which output did the SHA encoder actually compare?

A bounded contract lesson for the changed `guided/kit/sha_cnf.py` edition.
It is not a collision-search campaign or certification of every encoder mode.

## Run

Extract `current-encoder-contracts.zip`, enter `current-encoder-kit`, and run:

```text
python -I -B replay.py
```

Python 3.9+ and its standard library suffice. No solver, network connection or
original repository is needed. Temporary fixtures are removed after the run.
Expect `passed: true`, twelve circuit evaluations and four vacuous-range
controls. Two deliberately failing complete assignments are expected negative
controls, not failures of the lesson. No original research files are changed.

## The useful distinction

SHA compression has a working state and a feedforward output. For each word,
`H[i] = CV[i] + state[i] mod 2^w`. With a common CV, equality of the entire
working state and equality of the entire feedforward output are equivalent.
With different CVs, that implication does not hold.

In the pinned encoder, `FEEDFWD=1` imposes equality of all eight feedforward
words. Adding `TRUNC224=1` imposes equality of the first seven only. This is
a SHA-224-style output predicate, not automatically standard SHA-224: the
initial-state constants and message domain still need their own specification.

Our one-step negative control increments the second initial h by one and
decrements the second W0 by one. Their sum in T1 is unchanged, so both working
states agree. Only the last feedforward word differs. The seven-word predicate
passes, all-eight equality fails, and the historical decoder prints
`outputs equal: True` in both cases because it compares the working states.
This is a deliberately unequal-CV example, not a newly claimed standard-IV
collision. In the failing case we explicitly supply an unsatisfying model to
show that the decoder does not check the CNF.

## What is checked

- Widths 8 and 32, free and standard initial states, one-step outputs, and a
  17-step schedule/DIFFVARS fixture at each width.
- Every computed gate assignment against the actual serialized CNF clauses.
- Feedforward words against a separate word-arithmetic implementation.
- `KOFF=5`: the circuit uses the shifted constants; `sha_ref`/decode does not.
- `PREHEAD_ROWS=1-0` and `4-6` for a one-step instance: aggregate and per-row
  caps silently generate the same CNF as no cap.
- Tampered source and optimized Python execution are rejected by the wrapper.

The map records H word variables, but not KOFF or TRUNC224. Preserve the
invocation settings separately. An H line printed from a model is not an
independent recomputation of H or a clause certificate.

## What the synthetic cap finding does not prove

A separate small audit found that a wrapper discards true constant literals
without subtracting them from its remaining bound. That does **not** establish
an error in these SHA instances. In the unmodified encoder, both fixed-IV
copies have equal constant A/E bits; free initial words are variables; each
computed state word has nonconstant output literals. XORing corresponding
bits therefore yields false constants or nonconstant literals, never the
true constant required by that synthetic counterexample. Equality/value pins
add clauses; they do not rewrite those literals. Do not use the synthetic
fixture to invalidate historical runs.

## Limits and use

This finite exercise is not an all-input arithmetic equivalence proof,
all-option audit, success-rate estimate, SAT search or historical result
revalidation. Native XOR mode, arbitrary shape combinations and full solver
integration are outside these fixtures. A safe witness check must record the
width, rounds, offset, IV freedom and target predicate; verify a complete
assignment against its constraints; then independently recompute the intended
digest and check message distinctness and the permitted input domain.

The older published encoder edition and its evidence remain separate.
The exact newer source included here has SHA-256
`c431c124e449c3b7939f2fdec373a8abb7ba3e651b2dc884c64d4aa03308faec`.
`PROVENANCE.json` records its origin and the separate lesson implementation.
No external papers or ordinary chats are bundled. Preserve attribution and
inspect applicable rights before redistributing research source.
