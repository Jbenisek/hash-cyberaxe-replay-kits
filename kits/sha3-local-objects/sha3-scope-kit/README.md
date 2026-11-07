# SHA-3: exact local objects, explicit global limits

Extract, enter `sha3-scope-kit`, and run `python -B replay.py`.
Python 3.10+ standard library only. No solver, NumPy, network, original workspace,
package builder or message search is used. No input file is changed. Do not use
`-O`; altered payloads and disabled assertions are rejected.

The output has three distinct evidence levels. Do not combine their numbers
into an attack exponent.

## 1. Exact chi table and a weighted tail model

For five bits, chi sends bit x to a[x] XOR ((1 XOR a[x+1]) AND a[x+2]),
with indices modulo five. Enumerating all 32 inputs gives a permutation.
The 32 by 32 difference table is

    DDT[d][o] = #{v : chi(v) XOR chi(v XOR d) = o}.

Every row sums to 32. Nonzero input difference never has output difference
zero. The latter follows from chi being injective, not a probabilistic guess.

The historical r5 experiment uses alpha3 bit positions
`0,130,450,529,701,789,1021,1169,1280,1429` with lane index x+5y and bit index
64*(x+5y)+z. After theta/rho/pi, the nine active five-bit differences are
`5,8,4,16,2,16,1,2,8` in y/z order.

The FORWARD option counts are `8,4,4,4,4,4,4,4,4`, giving exactly 524,288
combinations. The historical diagnostic instead printed inverse compatibility
counts `10,9,9,9,9,9,9,9,9` beside a label about row options. Those inverse
counts answer a different question. The actual enumeration used forward DDT
entries and its final result reproduces.

For each combination, apply the next linear layer. The final chi output's
first four lanes must have zero difference. For each active five-bit row q,
weight that event by `(DDT[q][0]+DDT[q][16])/32`; multiply it with the
preceding product of DDT/32 weights and sum.

Result: 192 nonzero contributing patterns, exact sum **55/524288**, best single
pattern weight **1/524288**. Their active-final-row histogram is 0:32, 1:96, 2:64.

This is exact arithmetic in an independent-uniform-row transition model.
It is NOT proof that the connector's conditioned, correlated message samples
follow that law. No full attack success probability or price is certified.

## 2. Exact syntactic dependency sets

The key consists of x=0..3, y=0 and selected z planes after chi of round index 5.
Trace dependencies back through chi, rho/pi and theta to chi of round index 4.
Coordinates are explicit (x,y,z) tuples in the replay; constants do not change
these structural dependency sets.

| Planes | Key bits | chi5 input bits | chi4 output bits | chi4 input bits |
| --- | ---: | ---: | ---: | ---: |
| contiguous 0..34 | 140 | 175 | 1505 | 1600 |
| contiguous 0..28 | 116 | 145 | 1362 | 1600 |
| all 64 | 256 | 320 | 1600 | 1600 |
| {7*i mod 64 : 0<=i<35} | 140 | 175 | 1163 | 1368 |

The strided choice shrinks this structural set for the same 140 key bits.
It does not by itself supply a faster implementation, a globally minimal
circuit, a preserved candidate distribution or a lower complete attack cost.
These are syntactic dependency unions; semantic cancellations and restrictions
on reachable states require separate arguments.

## 3. Recount the saved connector-ablation observations

Seven files contain 6 attempts x 6 group choices each: 252 records. An `ok`
record reports EM's rank and DF=1600-EM, then counts four events in 32 sampled
affine solutions. Failures remain failures, not zero-dimensional successes.

| Dropped group | ok attempts / 42 | DF range | points | F | R0 | R0 and R1 | R0 and R1 and R2 |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| none | 23 | 35..53 | 736 | 736 | 736 | 736 | 0 |
| F | 28 | 462..485 | 896 | 0 | 896 | 896 | 0 |
| EDzero | 23 | 35..53 | 736 | 736 | 736 | 736 | 0 |
| M2 | 27 | 848..914 | 864 | 864 | 0 | 0 | 0 |
| M3 | 27 | 49..76 | 864 | 864 | 864 | 0 | 0 |
| M4 | 42 | 158..172 | 1344 | 1344 | 1344 | 0 | 0 |

F is the fixed-input-format check after the inverse linear map. R0/R1/R2
refer to the implementation's cumulative round conditions, not independent
Bernoulli events. Omitting F enlarges the affine set but all saved points fail
F; omitting M2/M3/M4 likewise loses an intended downstream event in this sample.
EDzero shows no DF gain here. These observations motivate scope-aware design;
they do not prove universal necessity, zero probability or impossibility.

Source files are project research under `research/dig/incoming/sha3-r5-U01/work2`
and `sha3-r6-U05/work`. Source fingerprints are in SOURCES.json. Original
experiment drivers are not included or launched. One copied cone driver derives
its output filename by replacing `cone5.py` in its own name; in the copied
filename that replacement is a no-op and would overwrite the script. This kit
uses an independently authored, read-only mathematical replay instead.

No ordinary chats, external proof prose, papers or PDFs are bundled. No blanket
reuse license, novelty, current acceptance or full-round break is asserted.
