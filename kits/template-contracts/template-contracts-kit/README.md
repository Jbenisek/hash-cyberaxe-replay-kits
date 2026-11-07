# Document-template contracts: finite, disposable controls

Requires Python 3.10+ with its standard library. Extract into a fresh directory:

```text
python -I -B template-contracts-kit/replay.py
```

Expected: `passed: true`, with ten documented cases. Every source and helper
is checked against the manifest before execution. Changed inputs, unexpected
top-level files and Python `-O` are rejected. Compare the ZIP digest against
the library's download metadata as well; a manifest is not a trust authority.

The fixture runner copies the five original utilities into a temporary tree,
creates synthetic notes, and checks actual behavior. Even `newrow.py` copies
only a generated dummy, never a real package. Child TEMP/TMP/TMPDIR locations
are confined to the disposable root because the historical leave-one-out
script itself leaves its temporary directories behind. No network, solver,
compiler, server, submission, proof generation or original workspace is used.

## What the tests establish

1. Numeric, whole-line and inserted-block slots can reconstruct two LF notes.
2. A fitting file can be extracted and refilled exactly in that fixture.
3. A negative numeric slot is rejected and an old extraction file survives.
4. The filler accepts repeated slot names that the extractor's regex rejects.
5. A string supplied for a block becomes separate character lines, without a
   schema-validation error.
6. The row assembler refills the dummy and refuses an existing destination.
7. A missing mapped parent leaves a partial dummy copy and `.vals_tmp.json`.
8. The leave-one-out tool prints `EXACT` across CRLF/LF differences because
   it compares decoded text, not raw bytes.
9. Duplicate derived row keys overwrite values; a printed reconstruction
   `FAILED` still exits zero.
10. A held-out note with an extra literal line is reported `FITS` / `ALL FIT`,
    but actual extraction using the two-row training template rejects it.

These deliberate negative controls pass when the original behavior is
reproduced. They do not mean the original defects were repaired. The original
sources retain their reviewed bytes.

## The reuse rule

Validate slot types, unique row keys, exact trusted path mappings and a fresh
output destination. Build the template on the training rows, then actually
extract the held-out row, refill it, and compare bytes or explicit normalized
text according to the intended claim. Check return codes **and** diagnostics;
neither a zero exit code nor `ALL FIT` is a sufficient certificate here.

Do not point these scripts at a live submission or a directory containing
private material. The assembler copies the entire base and does not validate
path containment, provenance, mathematical claims or a complete operation
ledger. Template reconstruction is not cryptographic validity, predictive
generalization, rights clearance or contest acceptance.

The utilities are project document-reconstruction work. The synthetic fixture
harness and this explanation are publication additions; no historical package
timing or reconstruction corpus was rerun. No blanket reuse license is asserted.
