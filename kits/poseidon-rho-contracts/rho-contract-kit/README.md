# A packed birthday walk: recovery mechanics, not a full-field success proof

This lesson pins the historical r56 `rho.py` and replays bounded contracts.
It does not run the full-field attempt or parameter tuning.

## Run

Extract `poseidon-rho-contracts.zip`, enter `rho-contract-kit`, and run:

```text
python -I -B replay.py
```

Python 3.9+; standard library only. Expect `passed: true`, 17,066 exhaustive
tiny-graph cases, 4,408 recovered pairs, 1,536 packing checks and nine
step-versus-reference comparisons. Temporary files are cleaned automatically.

## What is the walk?

The source uses a two-round affine input line and an equivalent 807-operation
field map. Its declared target has eight full rounds plus 56 partial rounds;
"r56" does not mean 56 rounds total. A nonzero input factor and nonzero output
scale preserve the relevant collision implication. Changing the output scale
does not generally preserve the walk's trajectory or success event.

Only distinguished values enter the table. An entry stores a 142-bit value
and a 119-bit gap to the preceding stored index: 261 bits, packed continuously
across 256-bit words. A padding word makes two-word reads possible at the end.
Two scans reconstruct indices and position a pair of walkers. Their first
merge supplies two distinct predecessors with equal images. A trajectory
starting on a cycle has no two distinct predecessors along that trajectory;
the source reports `start-on-cycle` rather than inventing a collision.

## Exact finite recovery test

Enumerate **every** function on each domain of size 1, 2, 3 and 4, every start
point, and every subset of distinguished points. Independently find the tail
and cycle. With generous finite caps, recovery must succeed exactly when
the tail is nonempty and the cycle contains a distinguished point.

All 17,066 cases agree. Counts: 4,408 `found`, 6,329 `start-on-cycle` and
6,329 exhausted-step cases. Every returned pair is distinct and has equal
images under its tiny function. These are **not 4,408 Poseidon collisions**,
nor an estimate of full-field success.

The packing check visits every bit offset 0..255, both field widths, and
three boundary values. `_put` ORs into zeroed storage: it is not an overwrite
operation. The search API also requires a step budget divisible by UNROLL=18.
It does not enforce that condition: passing one step executes eighteen when
there is no distinguished point. The historical attempt uses a valid multiple.

## What the plan reproduces

The finite `plan()` calculation reproduces:

- 807 step field operations: 329 additions and 478 multiplications.
- Operation numerator: `137215184878174913969505127226939604471902`.
- Reference unit: 1,392 primitive operations.
- Declared abstract-machine memory: 1,048,568 bytes, eight below 2^20.
- Included preprocessing allowance: 2^58 operations.
- Model-success decimal: `0.39000000061813340752`.

The printed floating-point logarithm is a display, not a newly proved upward
rounding certificate. The source's fixed-map transfer premise H1 remains
unproved. Its historical full instruction listings and complete allocation
proof are not certified by these function tests. We do not run `--tune`,
`--selftest`'s 24 sampled reduced-bit walks, or `attempt` here.

## Original interface and safe use

`python rho.py --plan` computes the finite ledger; no argument also means plan.
`--listing` prints the 807 field instructions. `--selftest` additionally runs
sampled reduced-bit walk checks and word-machine tests; those are different
from this lesson. `--tune` reruns the historical parameter descent. Unknown
flags silently exit without a useful report; `--help` is not an argparse help
interface. Import itself constructs the step and constant recipes.

The API `attempt(coin)` can request an astronomically large walk: do not call
it as a smoke test. `make_F(kappa)` requires a nonzero factor for the scaled
map interpretation. Its closure mutates an internal register array; do not
share one closure concurrently across workers. Packed fields must fit their
declared widths and must be inserted into zeroed regions.

The unchanged original source SHA-256 is
`b5bd922909b12d8871b381c7a1bc4255541241b45df0adb18fe5ad4c3f53773c`.
Provenance records the historical path, recovery identity and bounded test
scope. Preserve the source's predecessor credits and check applicable rights
before redistribution. No external PDF or ordinary chat is included.
