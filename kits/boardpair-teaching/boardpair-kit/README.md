# SHA-256 board-pair teaching kit

This is a complete, finite teaching bundle for two historical seeds and their
middle-band encoding. It is not a search campaign, new collision discovery,
standard-IV SHA-256 attack, success-rate measurement or contest submission.

## First run: finite witnesses (Python 3.9+; standard library only)

Extract the ZIP. Open a terminal in boardpair-kit and run:

    python -B replay.py

Expected: JSON with passed: true, standard_abc: true, two cases, and no encodings.
Each seed must pass its stated 37/38-step target; a one-step extension, a changed
message and an identical-message pair must be rejected. The wrapper checks the
exact success marker: the historical verifier exits zero even for a noncollision.
Both messages use the same chosen chaining value. No padding eligibility or
standard initial-value collision is claimed.

## Optional: generate and inspect four full-width CNF files

    python -B replay.py --encode

Expected: the same finite checks plus four encoding summaries: ctl and real at
37 and 38 steps. Each uses SELF, band start 16, width 4, no row release. Each has
512 middle-band unit clauses; real adds one 1,536-literal exclusion clause. The
wrapper verifies DIMACS counts/ranges, all appended pins, unchanged maps and
identical base clauses across ctl/real. It does not prove the whole encoder
equivalent to SHA-256 and does not ask a SAT solver whether the real instance
has another solution.

Only one child runs at a time. Finite children have 15-second timeouts; each
encoder has a 60-second timeout. The four encoder files and verifier fixtures
are made inside a temporary directory and removed on normal exit. This is a
bounded component check, not a measured peak-memory guarantee or cheap solver
budget. Allow disk space for tens of megabytes. No network access is used.

## Understand the historical source before changing the example

boardpairs/gen_boardpair.py writes XML, CNF and variable-map files. It has no
argument-validation layer. Only the exact mode real adds seed exclusion;
misspellings act like ctl. Inherited encoder environment settings change the
model; replay.py clears those settings and sets full width explicitly.

The source comment says the final four rows are never released, but
apply_release does not enforce that. This kit uses release=none. A custom
release may remove final-state equality constraints and must not be presented
as a collision experiment without checking its complete constraints.

The separate archival pathcheck.py is intentionally not included: it scans a
campaign directory and trusts saved INDEP VERIFIED text. It is a path-summary
tool, not a verifier. This bundle recomputes the finite outputs instead.

Raw C1 counts are characteristic statistics, not independent-event probabilities
or exact attack costs. A locally correct arithmetic count does not prove the
historical commentary's probability interpretation.

## Attribution and distribution

r38_s102 is the project's P8 seed. r37_tab17 is an EXTERNAL numerical control:
the project's setup_seeds.py credits Table 17 of ePrint 2026/1120,
https://eprint.iacr.org/2026/1120 . That attribution is preserved from the local
lineage, not a claim of a newly checked publisher page. No paper/PDF is bundled.

The encoder and profiler are project research code. The encoder retains its
Bailleux-Boufkhad (2003) totalizer credit. The profiler's unused pin39b preset
is labelled published in its source; it is not claimed as a project discovery.
No blanket code-reuse license is invented; consult the project's release terms.

MANIFEST.json binds every other kit file to its source or publication wrapper.
The library's download metadata binds the complete ZIP. Hashes identify bytes;
they are not scientific proof or protection against a substituted manifest.
