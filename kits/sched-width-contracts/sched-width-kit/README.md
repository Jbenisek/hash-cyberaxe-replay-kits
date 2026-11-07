# Small-word tests can change the algebra

This finite kit replays a model-boundary finding in the project's historical
`schedcnf.py`. It needs Python 3.9 or later, only the standard library, and no
network, compiler, SAT solver, or research jobs.

Extract the ZIP, enter `sched-width-kit`, and run:

```text
python -I -B replay.py
```

The replay verifies the manifest and a separately pinned source hash, computes
four pairs of linear-map ranks, and checks three explicit schedule witnesses.
It finishes in seconds on an ordinary computer. Do not use Python's `-O` mode;
the wrapper rejects it because assertions are part of the check.

## The exact 8-bit counterexample

Use 17 schedule words, required message support D={14}, and empty expanded
support L. Message A consists of sixteen zero words. Message B is identical
except for word 14, which is hexadecimal DE (222).

The historical scaling defines sigma1(x) = ROTR4(x) XOR ROTR5(x) XOR SHR3(x).
For DE, those three terms are ED, F6 and 1B. Their XOR is zero. Both expanded
word-16 values are therefore zero: the schedules differ only at word 14.

Fixed-input propagation supplies all 290 variables of the direct CNF and
checks all 867 clauses. No branching search is used. The relaxation for the
same cell contains an empty clause, so it rejects this concrete valid pair.
Two additional 2-bit witnesses check sigma0 at message word 1 and sigma1 at
word 14. Each direct CNF has 66 variables and 151 checked clauses.

| Word bits | sigma0 rank | sigma1 rank |
| --- | --- | --- |
| 2 | 1 | 1 |
| 8 | 8 | 7 |
| 16 | 16 | 16 |
| 32 | 32 | 32 |

## What follows, and what does not

A lone unequal summand cannot disappear under addition with common other
summands. But an unequal input to a noninjective sigma can produce an equal
summand. The shortcut must distinguish those cases. Restrict it to transforms
proved injective at the selected width, or encode the transformed equality.

The 32-bit rank checks do not show this defect at standard width, and do not
certify the rest of the encoder. This kit demonstrates no compression
collision, historical wrong verdict, attack cost, or full solver correctness.
The unrelated empty-model control also records that `--check` can print
MISMATCH while exiting zero. Inspect the verdict, not just the exit status.

## Files and provenance

- `schedcnf.py`: unchanged historical project source credited in its header to
  HASH$CyberAxe, October 31. SHA-256:
  `f442b063a19cb413bd3d96698395b5ca44a32ef3e9942f1096446a048399d7a4`.
- `check.py`: publication audit; uses copied source and temporary files only.
- `replay.py`: integrity wrapper and expected-result checks.
- `PROVENANCE.json` and `MANIFEST.json`: scope and byte identities.

The manifest detects accidental edits, not malicious replacement of the entire
kit. Compare the ZIP digest with the library's bundle metadata when acquiring
it. Original source behavior is preserved, not silently repaired. The copied
source reads environment settings; the audit clears its relevant settings for
each case and sets the tested width explicitly.
