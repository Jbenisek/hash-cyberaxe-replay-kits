# Time, memory and the shard trade-off

This offline lesson reproduces **79 rows of two historical SHA-256 cost
models**, not a collision search or a submission-ready attack. It needs Python
3.11 or later and only the standard library. No network, mapped drives, solver,
large tables or research workspace is required.

## Run it

Extract the archive, open a terminal in `d126-model-kit`, and run:

```text
python -I -B replay.py
```

It prints JSON containing all rows, exact time numerators/denominators, byte
counts, and certified upward roundings. It does not write any output files.
To keep a report, redirect stdout using your shell. Do not use `-O`: the
verification assertions must remain enabled. Normal execution takes seconds,
not the astronomical time represented by the model.

## What the experiment teaches

The historical score is `log2(T) + max(0, log2(M_bytes) - 20)`. Above 1 MiB,
ranking it is equivalent to comparing `T*M_bytes/2^20` exactly. A smaller table
can be worth a slower search, but fixed tables do not shrink with the shards.
This lesson preserves those fixed terms rather than subtracting shard bits
from the whole memory budget.

| Model | Shard exponent k | Time, rounded upward | Memory bytes | Score, rounded upward |
| --- | ---: | ---: | ---: | ---: |
| r37 unsharded | 0 | 61.48770 | 1,105,515,320,967,168 | 91.46134 |
| r37 grid minimum | 5 | 65.87516 | 35,088,251,224,064 | 90.87121 |
| r38 unsharded | 0 | 71.43541 | 2,344,036,320,154,681,344,765,568 | 132.39068 |
| r38 grid minimum | 19 | 88.21101 | 4,470,913,155,625,365,120 | 130.16628 |

These are unique minima **in the tested grids** (r37: k=0..32; r38: k=0..45),
not global optima over every design. The exact r37 winning time is
`89459989869750967895523/1322`; the r38 winning time is
`977240457355965757398995463315/2728`.

## What is actually checked

- Exact rational ranking, with 191 rigorous upward-rounding certificates.
  Bounds for logarithms come from a positive atanh series and its tail, not
  from rounding an ordinary floating-point printout.
- Integer checks of the rate truncations against the declared exponents.
- A rational-series certificate for each model's stated success inequality.
  This checks the numerical inequality **if its probabilistic premises hold**.
- The r37 scan-overhead inequality for every class size from 1 through 3,600.
  Its 222 sampled input rows match the corresponding recorded class sizes.
- The original r37 memory formula floors a division at k=28..32. Rounding up
  adds one byte to each of those rows and leaves k=5 as the exact winner.
  This fixes the integer division only; it does not prove balanced shards or
  an implemented peak-memory bound.

## Important limits

The r37 table uses sampled conditional means, multiplied by 1.02. That margin
does not prove a bound or make those samples admissible for a premise-free
claim. The success rates, concentration/independence assumptions, shard laws,
actual instruction counts and lifetime memory layout still require their own
evidence. A certified model calculation is not a certified cryptanalytic attack.
These are historical rules and parameters, not a statement of today's rules.

Only selected arithmetic definitions, numerical inputs and new audit code are
included. The original research programs, their search paths and operational
briefings are omitted. `model37.py` retains ledger data and three small helpers;
`model38.py` retains constants and preprocessing arithmetic. Neither is a full
implementation. `price.py` contains the selected historical arithmetic functions.
The checkers supply their confined environment rather than importing the
research modules. `PROVENANCE.json` records original source fingerprints and
the selection boundary. Original-source bytes are not checked by offline replay;
the included selected bytes are checked against the manifest and checker pins.

## Files and provenance

`check37.py` and `check38.py` are the finite audits; `price.py` calculates the
rows; `model37.py`, `model38.py`, and `runs/` supply the selected inputs.
`replay.py` checks the payload manifest before running the audits in isolated
Python subprocesses. The manifest detects accidental changes; it is not an
authenticity signature or a defense against an attacker replacing every file.

This is the library's replay of Sol's D126 accounting study, over the project's
r37c and r38d ledgers. Their cryptanalytic lineage and inherited premises remain
those of the source work. Sharding and Pareto optimization are established
methods, not inventions claimed by this lesson. No third-party PDF, raw user
chat, credential or server-management code is included.
