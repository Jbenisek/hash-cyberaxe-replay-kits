# Backward schedule: exact words, not an attack price

This offline kit checks a saved SHA-256 schedule witness, a backward-expansion
derivation and a small historical result-table recount. It needs Python 3.10+
and the standard library. No solver, network, mapped drive, external paper,
research launcher or organizer module is required.

## Quick start

Extract the archive, enter `backward-schedule-kit`, and run:

```text
python -I -B replay.py
```

Expected JSON includes:

```json
{
  "passed": true,
  "random_backward_pairs": 1024,
  "round_trips": 2048,
  "hashlib_controls": 4,
  "late_xor_weight": 7,
  "standard_iv_collision": false,
  "screen_rows": 16,
  "screen_distinct_trails": 8,
  "original_brief_checked": false
}
```

`original_brief_checked: false` is intentional: the raw operational briefing
is not distributed. `LESSON.md` is the independently written scientific
account, with the original briefing's fingerprint and the recurrence proof.
The public kit reruns the numerical checks without needing that briefing.

## What is in the kit

- `reference.py`: the pinned independent SHA-256 reference by HASH$CyberAxe, retained
  unchanged. Four deterministic standard-IV examples are checked against
  Python's hashlib before using it on reduced-step data.
- `check.py`: publication audit. It reconstructs 1,024 deterministic one-kick
  window pairs and checks every early-word residual and 2,048 round trips.
- `SCHED_TAILLIGHTEST_board_tail.txt`: the exact saved two-message schedule
  witness. Its actual support is {8,9,10,11,12,16,17,24,26}; the late word
  XOR weights are 3,1,2,1. This four-kick witness is distinct from the one-kick
  window examples used to check the derivation.
- `VALUE_SCREEN_PRICED_TRAILS_1031.tsv`: sixteen saved solver-label rows for
  eight trails, each at cuts 17 and 38. The kit recounts these rows; it does
  not check their UNSAT certificates.
- `LESSON.md`, this guide and `replay.py`: explanation and an integrity-gated
  entry point. `MANIFEST.json` lists exact file sizes and SHA-256 digests.

## Interpreting the result

The saved witness has late XOR weight seven. Its standard-IV 39-step outputs
differ; it is not a standard-IV collision. The source-reported weight-six
UNSAT would supply the matching lower bound only after checking the exact
relaxation, instance and certificate. This kit certifies the upper witness,
not a global minimum or attack probability.

The one-kick derivation proves five staged modular equalities are equivalent
to the specified forbidden early positions being clean. It does not prove
that those 160 nominal bit equations are independent. Strict support needs
additional nonzero checks. The 1,024 test pairs do not replace the algebraic
proof or solve the strict 32-bit one-kick instance.

The historical state-price estimates 125.8, 124.7 and 122.7 were withdrawn in
the source after value-level screens. Numerical schedule validity does not
restore those prices. Local consistency, actual state feasibility and a
fully charged attack remain separate questions.

## Integrity and failure behavior

Do not use Python `-O`: this entry point rejects disabled assertions. Changed
files fail manifest checks, and the numerical sources and reference have
additional embedded identity checks. A digest manifest is not a signature;
compare the archive fingerprint published by the library. The builder tests
missing data, changed data, rehashed changed data and optimized-mode rejection
after clean extraction. All temporary checks stay in disposable local folders.
