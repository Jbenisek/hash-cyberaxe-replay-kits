# A search ordering score is not a success probability

This finite lesson uses the unchanged historical `bitcost.py` source and
synthetic logs. It needs Python 3.9 or later and only the standard library.
It does not launch a solver, read historical campaign logs, or use the network.

After extracting the ZIP, enter `bitcost-kit` and run:

```text
python -I -B replay.py
```

Expect `passed: true`, thirteen library controls and an empty-ranking CLI
control. The kit creates and removes temporary fixture files. Its source hash
and manifest are checked before execution. Do not use Python's `-O` mode.

## What the score actually counts

For each supplied file, the tool collects names with a parsable timestamp and
SAT, HELD or UNSAT observations. It records the first SAT time for each name,
not the minimum time. Each file contributes one observation per name. A file
where the name never has SAT counts as stalled. The ordering key is the
fraction of such files followed by the median of first-SAT times.

That is a file-based ordering heuristic. It is not an estimator of the attack's
success probability, a mathematical difficulty bound or a complete work price.
In particular, UNSAT and timeout remain different scientific outcomes even
when this ordering policy gives them the same score.

| Input arrangement | Score for the same name |
| --- | --- |
| One HELD file and one SAT file | stall = 1/2 |
| Those two runs appended to one file | stall = 0 |
| The HELD path supplied twice, the SAT path once | stall = 2/3 |
| SAT at 8 seconds, then SAT at 1 second in one file | recorded time = 8 |

## Guard the boundary before reuse

- Deduplicate resolved paths and preserve explicit target and run identities.
- Validate the tab-separated header. The source always discards the first line.
- Reject nonfinite or negative times; `float()` accepts NaN and negative values.
- Avoid leading-underscore candidate names: the source normalizes them for
  iteration, but not for the successful-time lookup. The fixture `_p` with SAT
  becomes a stalled `p`.
- Check that names are not silently excluded by the `base` and `swap` rules.
- Inspect how many rows/files were accepted. Missing inputs and malformed times
  can be silently skipped. Empty ranking writes a newline and exits zero.
- The unseen-name prior is fixed at `(0.5, 1000000)` by default. It is not a
  runtime measurement of the solver's current cap. A name with no successful
  time receives a separate `1000000000` sentinel.

These are source-contract findings on artificial examples. They do not show
that a particular historical experiment used duplicate paths or bad times.

## Provenance

`bitcost.py` is the project tool from the HASH$CyberAxe export's
`newdoors/headaware/lens` directory, retained unchanged. SHA-256:
`254dd5cde6663e6f24ed4c1b2ed4a6820934408a3feb5a393b931dce6d2bc814`.

The library adds `check.py`, `replay.py`, this explanation, the manifest and
provenance metadata. No persistent-solver wrapper is included: the exact
dependency implementing the historical driver's protocol remains a separate
recovery requirement. This kit is useful without that solver.
