# Same support does not mean the same experiment

Extract the archive, enter `overlap-kit`, and run:

```text
python -I -B replay.py
```

Python 3.10+ and its standard library suffice. The wrapper checks the payload
hashes, then runs ten synthetic fixtures in temporary directories. It does not
read the historical team's CSV, launch a solver or write to research originals.
Do not use `-O`; assertions are part of this replay and that mode is rejected.

## What the old comparison actually joins

The exact source `research/outside/dariia_in/dariia_overlap.py` forms a key from
step count, sorted word indices and sorted kick indices. It does not include
weight cap, encoder version, absolute initial-value model or word width.
Sorting normalizes order but does not remove repeated indices.

The local side retains the last SAT or UNSAT row for each key. With several
files, the unsorted glob's order is not a documented conflict-resolution rule.
The outside side retains a set of decided labels. It reports agreement whenever
the local label is in that set. A set containing both SAT and UNSAT therefore
agrees with either local verdict; this is not independent consistency evidence.

## A counterexample you can reproduce

One local row says SAT for step 40, words {1,3}, kick {2}. Two outside rows use
that same support: a cap-8 SAT row and a cap-16 UNSAT row. The original reports
one overlap, one agreement and zero disagreements. An additional HELD row is
counted in the status tally but not in the decided-support set.

The fixture demonstrates the join's behavior. It does not establish that these
synthetic statuses are mathematically possible in any specific encoder. It
does not establish the status of a historical cell.

## Ten bounded controls

1. Sorting normalizes word order.
2. Different caps and conflicting outside labels can still report agreement.
3. The last local decided row wins within one file.
4. An empty local glob is silently treated as no local decided supports.
5. Repeated outside rows count twice in the tally but once as a support.
6. Repeated word indices are retained, not normalized into a set.
7. Undecided labels do not become decided supports.
8. A missing outside CSV fails.
9. Missing required CSV headers fail.
10. Malformed local word indices fail.

The original reads `unsat_1027/unsat_data_2026-10-27/screen.csv` and
`../../game/climber/guided/scan40/census_*.tsv` relative to the current directory.
Use the wrapper instead of pointing this historical interface at a live results
tree. A missing local tree is not reported as an error by the original.

## How to use the lesson

For a future comparison, declare a complete experimental identity including
step range, width, initial-state model, support, cap, encoder edition and other
constraints that can change satisfiability. Retain conflicting rows and require
an explicit conflict disposition before counting agreements. Keep undecided
results separate. Check witnesses and proof artifacts under the same model;
matching labels alone are not certificates. This kit documents the old behavior,
not a newly implemented historical reconciliation.

The article's 3,063 shared supports is a reported historical figure, not a count
reproduced by this kit. No new SAT/UNSAT result, collision or success probability
is claimed. The original comparison script and its attribution are retained;
no outside research dataset, private communication or PDF is bundled. There is
no blanket license claim for the rest of the research archive.

Verify the ZIP against the library's external digest. Its internal manifest
detects accidental changes; it is not an independent authenticity signature.
