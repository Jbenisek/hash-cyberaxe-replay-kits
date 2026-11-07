ABSORPTION JAM / LEAK MAP: SAVED NUMERIC TABLE REPLAY

Run Python 3.11 or newer, standard library only:

    python -I -B replay.py

This bounded check reads seven retained first-failure histograms and a
61-specimen leak table. It checks sums, exact representative joins, group
totals and recorded pass16 logarithms. It does not perform the historical
GPU sweeps, allocate a search table, install software or use the network.

Each histogram has 2^32 shifts. Each has one full-predicate hit, d=0.
That is the unchanged starting input, not a new pair. The source's printed
label "new pairs" does not change that numerical fact. The 48 observations
reaching row 19 are summed over ten specimens in the 37-step d29 group;
they still fail at row 19, rather than producing complete new collisions.

These logs use h-absorb: add d to initial h and subtract d from W0 in both
messages. The step-0 T1 value is unchanged; so are states through step 15.
W16 then changes by -d through message expansion. The source checks each
supplied W mask before its step and A/E masks afterwards. Reaching the end
means those masks passed; a separate full-output collision check is needed.

The saved pass16 rates divide nonzero surviving shifts by 2^32, not 2^32-1.
That denominator choice is intentionally preserved. Historical timing is
not validated by this replay. A table checksum is not evidence that the
original GPU run used the intended conditions, source or input pair.

Required before replaying the original experiment: exact CONDS and pair
identities, source/build/mode and run manifests, and an independent
compression verifier. The 61-row aggregation source is still requested.
The kit does not bundle a GPU launcher or claim all 61 full histograms
were recovered. Numerical joins cover the seven retained representatives.

Credit: the HASH$CyberAxe team's project research supplied the kernels and saved tables.
This teaching kit adds a scoped reconciliation, not new round reach or a
new attack. See the source digests and boundary notes in tables.json.
