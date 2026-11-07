# Four-pattern witness replay and verifier boundaries

Extract the ZIP into a fresh directory, enter `four-pattern-kit`, and run:

```text
python -I -B replay.py
```

Requires Python 3.10 or newer, standard library only. No compiler, solver,
network, GPU, research checkout or original absolute path is needed. The test
uses a disposable temporary directory and does not alter supplied witnesses.
The source CLI's two absolute path literals are relocated in the disposable
copy; its compression and output logic are unchanged.

Expected: JSON with `passed: true`, eight interface controls, seven full-SHA-256
hashlib controls, and four nontrivial 37-step collisions. Each pair uses its own
common chosen chaining value. None is a standard-IV collision. Both references
rebuild the schedule and compare all eight feedforward output words against
the saved digest. Their agreement is finite numerical evidence, not a theorem
about every implementation or an attack's success probability.

## What the records show

Zero-based state row `t` means the state after compression step `t`. The pair
of side-A bits `(E18[1], E18[10])` is:

| Witness | Pattern | Initial state |
| --- | --- | --- |
| alt_G1 | 10 | Chosen CV |
| alt_G2 | 01 | Chosen CV |
| alt_G12 | 00 | Chosen CV |
| i_all52 | 00 | Chosen CV |

The four files therefore cover three patterns, not all four patterns. The
printed P11 baseline is not supplied by this kit. Do not count four files as
four distinct pattern classes. The report also records bits 1, 10 and 29 at
rows 17 and 18 to make the row convention explicit.

## Why the wrapper alone is insufficient

The archived `verify_alts.py` prints a comparison. It does not assert it.
A one-bit mutation produces `37-step equal: False` and exit code zero.
Identical messages produce `True`; the wrapper does not test nontriviality.
Saved `collision`, `digest`, constraint and flipped-value flags are ignored.
A missing second file leaves the first positive line printed before failure.
This kit tests those behaviors deliberately; its overall PASS means those
boundaries were reproduced, not that the negative fixture is a collision.

The companion `sha256_ref.py` has an unrelated direct-execution driver that
expects historical `llw24` files and writes results. It is imported here, not
run as that driver. Run the kit's `replay.py`, not the original wrappers.

## Limits and provenance

No 25-million-trial retest, SMC prefix sampler, complete characteristic-cell
audit, minimum-search theorem, probability estimate or charging claim is
reproduced. The report's scope is intentionally narrower than the historical
four-pattern retest report. No scripts that manage or submit jobs are included.

The original verifier and four numerical files come from the project's
`research/retest/four_pattern_contradiction` and `research/tighten/r37_unforced_files`.
The second reference is `research/tools/indep_sha256_check.py`, credited in its
header to HASH$CyberAxe. Source hashes and member sizes are in `MANIFEST.json`.
The article retains the historical characteristic and correction credits;
packaging these tests is not a new discovery of the underlying collisions.
No blanket license over upstream research is asserted.
