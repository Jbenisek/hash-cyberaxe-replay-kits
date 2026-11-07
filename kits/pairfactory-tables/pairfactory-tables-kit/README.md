# Read the table before counting the result

This finite kit contains four unchanged historical pairfactory summary tables
and an independent publication recount. Python 3.9+ and the standard library
are sufficient. It does not run a solver, generate collisions or reprice an attack.

Extract, enter `pairfactory-tables-kit`, and run:

```text
python -I -B replay.py
```

The output must contain `passed: true` and the following totals:

| Table | Rows | Checked meaning |
| --- | --- | --- |
| CLASS_SUMMARY.tsv | 128 | 33 priced classes, 90 summed n_priced, 16 True rule labels, 95 impossible annotations |
| RESULTS.tsv | 54 | 54 SAT / INDEP_VERIFIED labels and distinct result labels |
| RESULTS2.tsv | 121 | 117 UNSAT, 4 UNDECIDED; 115 distinct job numbers, six reused |
| TAILS_B.tsv | 7 | All seven named stage-B means match the rounded class-summary entries |

These are 310 historical summary rows, not 310 collision witnesses.

## How to read the fields

`CLASS_SUMMARY.tsv` has a hexadecimal class key and a seven-character sign code
in the header's position order (5,7,8,14,16,29,30). `rule_good` is a historical
classification, not feasibility. `n_priced` counts summarized observations;
bestA/meanA/worstA are rounded values, and `-` means missing, not zero. Stage-B
entries identify follow-up results; `impossible` remains a reported annotation,
not a proof checked by this replay.

`RESULTS.tsv` records job, source, edited band, first/child kind, reported
verdict, wall/CPU seconds, verification marker, result label and exclusion
count. `INDEP_VERIFIED` is the historical verifier marker, not proof that trials
were statistically independent. Join labels to actual numerical witnesses
before counting distinct collisions. This kit contains no such witness files.

`RESULTS2.tsv` records class-search attempts. Job numbers repeat, so retain
the complete row and input context. `source=none, band=none` marks an unpinned
attempt, distinct from a source/band-restricted test. `UNDECIDED` is not UNSAT;
a later verdict requires matching the exact instance before superseding it.

`TAILS_B.tsv` stores signature, mean_lin, lcb999 and a historical relative
result directory. The inspected producer `tail_stats_dir.py` prints base-two
logarithms, despite the short `mean_lin` column label: it forms fourteen
q_i = 2^log2_carrier_i * hits_i / (20*80*2048), averages those linear q_i,
then prints log2(mean(q_i)). This is not the average of the logarithms.
Its lcb999 field is log2(m - 3.852*s/sqrt(14)), with sample standard deviation
s of those fourteen q_i. Positivity and statistical coverage are separate
requirements; the historical script does not guard nonpositive logarithm
arguments. The kit recalculates all seven rounded means and bounds from a
numeric projection of 98 recovered seed files (fourteen per signature), with
1,960 saved chain observations. No underlying trial generator is rerun and
the bound's coverage is not proved. Paths are references, not commands.

Producer source SHA-256:
`b9315d4beed3d4d2c21f9b1cb1bb6ea2bcf5395b62a181cec06c1f2c3d00ec52`.
The producer is described here, not executed or included as a portable runner.

`tail-observations.json` retains carrier values, chain counts, control values,
source paths and original SHA-256 identities. It omits empty trial records and
null message fields; it is a projection, not the original full JSON files.
Publication checks all 98 original digests before packaging. The standalone
replay pins the projection, sums integer counts and reproduces the floating
calculation to the saved four decimals. It does not independently reconstruct
the projection from originals absent from this kit. All original message
fields were null: these are numerical observations, not collision witnesses.
The stored floating carrier values do not define exact rational probabilities.

## What is verified

The replay pins all four original digests, parses the complete tables, checks
unique class keys, counts verdicts and repeated job numbers, checks ordering of
rounded stage-A values, and matches the seven stage-B means across tables.
It does not replay solver certificates, derive confidence coverage, infer an
attack probability, or establish whole-message nontriviality or digest equality.

## Integrity and credit

Historical tables retain their exact project bytes. The publication contributes
the recount, this guide and integrity wrapper. `MANIFEST.json` lists every kit
payload; `PROVENANCE.json` records the four source identities and scope. The
checker also pins source hashes independently of the manifest. Missing,
altered and rehashed-source controls are rejected. Optimized Python mode is
rejected because assertions protect the wrapper's expected-result checks.

No raw conversation, external paper, solver executable or operational launcher
is included. No blanket third-party license or external novelty is asserted.
