# Sparse SHA-256 schedule checks, not collision checks

In the extracted `sparse-schedule-kit` directory, run:

```text
python -I -B replay.py
```

Python 3.10 or newer, standard library only. No compilation, solver, network,
research workspace or large enumeration is required. A temporary directory is
used for all mutations. The supplied sources and data are checked against their
manifest and the checker's pinned source identities.

Expected: `passed: true`, six interface controls, and `quick_checks: 99`:

- 26 saved linearized schedule witnesses (expansion, weight, late support);
- four modular schedule-pair witnesses (full 41-word expansion, selected weight/support);
- 64 sigma-inverse basis checks;
- five late-support incidence comparisons, for horizons 37 through 41.

The 99 count groups some assertions together; it is not the number of bit
assignments exhaustively searched. Linearized expansion replaces modular sums
with XOR. Modular expansion uses the native additions, but still checks only
the schedule. Neither object proves a compression collision.

## What the negative controls establish

The original `verify.py` relies on Python assertions. A deliberately wrong
saved weight fails normally but prints PASS under `python -O`. This kit rejects
optimized execution. Removing all saved witness maps still produces a smaller
69-check PASS from the original verifier. The kit pins the complete original
data and expects the full 99-check result. It also tests that descriptive
`summary` and `regression_tests` fields are not verified by the quick CLI.

## What is not reproduced

Historical global linear minima, full-support enumerations, 2,048 round trips
and other saved regression claims are not established by this quick command.
The original optional `--recompute-minima` and `--recompute-supports` modes
require additional sources/certificates and a compiler; those large workloads
are deliberately not included or executed by this teaching kit. Do not append
those flags to `replay.py`. Native modular global minima remain open in the
historical data, and no success probability or attack-cost proof is supplied.

Sources are the project's `research/sha256grid/sol6_schedule/sha256_sparse_schedule_research`
archive. The original sources retain their credit and scope. The added harness
documents replay boundaries, not a new discovery of these schedule witnesses.
No blanket license over upstream work is asserted.
