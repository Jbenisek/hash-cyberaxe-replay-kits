# Reproduce the SHA-2 mask corrections

Extract, enter `mkxml-kit`, and run:

```text
python -I -B replay.py
```

Python 3.10+ with its standard library is sufficient. Ten bounded controls
run copied source in disposable directories. No solver, compiler, network,
collision search or original checkout is used. Each source invocation has a
ten-second timeout; the combined harness has a 45-second timeout. The original
source and supplied files are not edited. Optimized Python mode is rejected.

## Why these historical templates matter

The source retains both overconstrained and corrected versions of the T1314
release experiment. Reproducing a failed model exactly is not enough: it must
encode the intended question. The kit checks these changes directly:

| Version | Expanded W16 through W42 | A/E state rows |
| --- | --- | --- |
| Original pinned | All constrained equal | A free only 8–18; E free only 8–22 |
| FIX | Free except equal rows 24, 26, 39–42 | Same restricted state rows |
| FIX2 | Same corrected W masks | Both A and E free 8–42 |

The first correction releases 21 expanded words. The second releases state
rows that had imposed additional equalities. This verifies which masks are
written, not whether the resulting instances are satisfiable or yield a
collision. Historical comments reporting initial-check failures are not
independently replayed solver verdicts.

The kit also includes the exact historical control XML and found signed
characteristic. It recounts 44 rows, 128 word masks and 380 single-bit
conditions: A=60, E=283, W=37. Of these, 167 are signed differences:
A=59, E=82, W=26. No `?` remains. Every found mask refines its input mask;
altering the pinned initial E difference or a mask width is rejected.

That inclusion check does not validate the modular compression equations.
There are no concrete message values or digests in this characteristic file.
Counting conditions, fitting input masks and proving an attack probability
are different obligations. Two-bit relations are not included in the 380.

## Interfaces and hazards reproduced

The ordinary command writes 31 XML files. `twoblock` adds two files.
`twoblock_reg e0 f31 g15 h28` adds eight register-specific files. The latter
maps e/f/g/h to input rows E-1/-2/-3/-4 and output rows E39/38/37/36 at
40 steps. The supplied signed masks intend opposite input/output differences
for the B2 feedforward cancellation, but no concrete block pair is supplied.

The B1 comment says standard IV. Its emitted masks specify equal input pairs,
not the eight absolute SHA-256 IV values. Check the consuming model's actual
initial values before calling a result a standard-IV attack. This kit does
not execute nldtool or certify its implicit defaults.

An absent output directory fails. An invalid register fails after leaving
31 ordinary files. An invalid `e32` bit request exits zero with a 33-character
mask. An unknown mode is ignored. Running the source again overwrites its
named outputs. Therefore use an empty disposable directory, validate the bit
range 0–31 and parse every output width; exit zero is not a full input check.
Do not import the original source for helper access: generation occurs at
module top level. The safer entry point for this lesson is `replay.py`.

## Provenance and limits

The exact project generator was previously attached to the teaching article
for `research/levers_1021/s256_r40_search/nldtool/mkxml.py`. When that live path
became unavailable, the attached text matched the complete original SHA-256
fingerprint and was retained unchanged. This is source recovery, not a
rewrite or a substitute edition. Source comments credit the LLW 2024/349
SHA-224 control and project release-set research; the library does not claim
invention of those characteristics or include the external paper.

The package supplies no numerical 40-step collision, SAT/UNSAT proof, attack
price or success probability. A passing report means the ten stated generator
and recount controls were reproduced, including deliberately invalid cases.
Member hashes are in MANIFEST.json; compare the ZIP with the separately
published download hash. A self-contained manifest is not a signature.
