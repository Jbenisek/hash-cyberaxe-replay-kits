# Encoder and summary contracts: reproduce the interface boundaries

Extract the ZIP, enter `encoder-summary-kit`, and run:

    python -I -B replay.py

Python 3.10 or later, standard library only. Do not use `-O`. No solver,
network, original workspace or mounted drive is needed. The wrapper verifies
the manifest before running either check. It creates two small reports under
the extracted kit's `research/public_library/qa` directory. Generated test
formulas and synthetic tables live in disposable temporary directories.

## What is checked

The SHA-256 checker validates 80 Boolean gate assignments, 64 shape-symbol
assignments and ten deterministic 32-bit computation fixtures. They cover
1, 4, 17 and 39 steps, plus a three-step constant-offset example, in ordinary
CNF and native-XOR modes. Every generated clause is checked against the
constructed valuation; the final state agrees with a separate implementation.
Four standard SHA-256 known answers are compared with `hashlib`.

These are positive finite circuit fixtures and local truth tables, not an
exhaustive proof of every encoder mode or a SAT-solver correctness test.
No reduced-width, near-collision, totalizer, modular-difference, symmetry-
breaking or XOR3 configuration is certified by these checks.

The deliberately reproduced interface limits matter:

- `KOFF=7` changes the encoder constants, but the archived decoder reference
  ignores the offset. The two computed states differ.
- Unsigned `u/n` is inequality only; `SIGNED=1` fixes orientation. Unknown
  symbols add no constraints. Repeated row numbers retain the last row.
- A decoder run on an empty assignment can print the trivial equal-message,
  equal-working-state case. It is not a validated nontrivial collision.
- Decoder outputs are working states, not feedforward digests. The decoder
  does not check all CNF clauses or require a complete assignment.

The SHA-3 summary checker uses seven archived seed tables (252 records) and
five further fixtures. It reproduces the saved unmodified group: 23 successful
attempts, 736 sampled points and events `[736,736,736,0]`. Dropping F yields
28 successful attempts and `[0,896,896,0]` over 896 points.

The final three event columns are cumulative: R0, R0-and-R1, and
R0-and-R1-and-R2. They are not independent factors. The historical summary
also counts matching backup filenames, retains duplicate baseline records,
prints an empty result when no files match, and does not reject event totals
larger than the recorded sample size. Those negative controls are expected.
They do not mean the separately checked archived tables contain those errors.

## Where the inputs are

The kit mirrors a small part of the original relative folder structure so
the unmodified pinned sources and checks can resolve their inputs:

- `research/game/climber/guided/minsup/sha_cnf.py`: historical encoder.
- `research/tools/indep_sha256_check.py`: independent reference implementation.
- `research/dig/incoming/sha3-r5-U01/work2/`: read-only summary and seven tables.
- `research/public_library/scripts/`: the two bounded publication checkers.

For the historical summary by itself, enter its `work2` directory and run
`python -I -B summ_drop.py`. Do not add backup files matching `drop_k*.json`
to that directory. The package contains no connector generator or solver.

## Provenance and limits

The original project sources and numerical records remain unchanged. The
manifest identifies the exact reviewed editions. The publication checkers
add small synthetic controls and independent arithmetic, not new collision
witnesses, a complete attack implementation or a success-probability proof.
The separate SHA-3 local-objects kit explains the mathematical model and
dependency tables; this kit concentrates on source interfaces and failure modes.
No raw conversation, external paper or operational campaign payload is included.
