# Archived profile-tool contracts, with finite controls

Requires Python 3.10 or later, standard library only. Extract the ZIP into a
fresh directory and run:

```text
python -I -B profile-contracts-kit/replay.py
```

The replay checks every manifest byte before running. It refuses `-O`, changed
source bytes and unexpected top-level files. Do not run the archived source
drivers directly: backscore's original driver writes a project table and
expects a historical directory tree. The replay extracts only reviewed pure
definitions from backscore and predict_signs. It executes mirror only on
disposable text fixtures in fresh temporary directories; those are removed
automatically. No solver, network service or original research directory is used.
The additional family writer and backward diagnostic run only from copied
scripts in synthetic temporary trees. The independent reference CLI runs its
fixed-size sanity gates once; it creates no research files.

## What is reproduced

- **mirror.py:** eight modes and 36 text variants. Its default mirror reverses
  W signs, not signed A/E pins. Partial flips relax expanded-word signs.
- **backscore.py:** 7,584 difference vectors, 8,193 signed-digit controls and
  4,096 step-inverse/noncoalescence controls. If j is the last nonzero expanded
  word difference below R, its return is exactly
  `(R-j, j-1, NAF_weight(-dW[j] mod 2^32))`; all-zero gives `(R,-1,0)`.
  The clean-end recurrence stops immediately after reaching that nonzero word.
  A score-one eight-step pattern can still be impossible from a shared initial
  state: the first update differs, and subsequent equal-word updates are bijections.
- **predict_signs.py:** A=(1,1,0,...,0), B=(0,...,0) gives W16(A)=02004001,
  W16(B)=0. Exact W masks and wildcard A/E masks admit both orientations, while
  both predictor modes call the mirror UNSAT. A parity-connected component need
  not flip together. The separate unused-basis counterexample is labeled as
  unused; it is not blamed for the direct prediction failure.
- **trail_families.py:** seven synthetic writer cases. Filename prefixes,
  ordered u/n support, duplicate gate rows and lexical SAT tie-breaking are
  checked. x-only support is ignored. Scientific-notation times are skipped;
  malformed decimal or empty time tokens can crash before replacing the old
  output. Group membership is not a solver-equivalence theorem.
- **backwalk.py:** 18 positive-step CLI fixtures and 1,352 comparisons with
  explicit inverse states. Exact demands stop at the first unequal mixing
  input; they need not reach a common legal initial state. Zero and negative
  horizons run no step and misleadingly report completion.
- **indep_sha256_check.py:** one complete CLI invocation runs 2,000 randomized
  hashlib checks and 20,000 randomized eight-step inverse trials. Four fixed
  hashlib controls supplement these. The CLI reports 8/8 equality for distinct
  messages at zero and negative steps, so validate 1..64 before interpreting a
  comparison. Above 64 raises an index error. Printed counts and successful
  process exit do not validate message nontriviality, standard IV or padding.
- **Closure-row identity:** 120 scalar controls at zero-based C=26,27,28,
  with zero to four equal suffix words. A common end state fixes A/E rows
  C-3..C. Equal-word inverse steps preserve equality. At the first unequal
  inverse word j, only the recovered h differs, by -Delta W_j modulo 2^32,
  which is E_(j-4) in shifted-row notation. Hence C-4 is the first possible
  affected row, not a guaranteed first difference. Every tested inverse pair
  is forwarded again to the same input state. This does not test a GPU patch
  or establish full-schedule consistency or compatibility with an initial IV.

The mathematical explanations and source lineage are in the library's backward
score and sign-variant articles. Original tools retain their project/HASH$CyberAxe
credit. The test harness and exposition are publication additions. Historical
solver measurements remain reported; these tests do not rerun them.

## Limits

These are tool contracts and model counterexamples, not a collision kit.
They do not prove a full XML format contract, schedule-space classification,
collision probability, independent residual conditions or a contest price.
Finite controls accompany the closed-form proof; they are not a substitute for
it. An absent or rejected heuristic does not invalidate independent witnesses.
