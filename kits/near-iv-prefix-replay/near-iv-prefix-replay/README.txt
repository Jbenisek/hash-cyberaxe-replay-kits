NEAR-IV EXAMPLES: FIVE RAW-BLOCK PREFIX CHECKS

Extract near-iv-prefix-replay and run:
  python -I -B replay.py

Python 3.9 or newer; standard library only. Optimized -O execution is rejected.
No network, solver, historical search or GPU is used. Original pair and mask
files, the SHA-pinned independent reference and records.json are included.

Expect five saved examples, four conforming prefixes through row 18, one
example keeping initial b/c/d at their standard-IV values, and zero 39-step
collisions. Distances from the IV are 22, 24, 25, 46 and 57 bits. Seven complete
mask editions represent only two distinct projections over rows 0..18.

The 25-bit-distance example keeps b, c and d at the IV. The 24-bit example
changes c bit 14: c=3c6eb372, whereas IV c=3c6ef372. Restoring that bit with
both original messages unchanged lowers the distance to 23 bits but fails
the retained row-7 E value pins. This single diagnostic is not an impossibility
claim or a search over repaired messages.

All four printed out pairs are 39-step working states, before feedforward.
The checker independently computes the actual feedforward outputs; none of
their eight words agrees at step 39 for any of these five examples. The
22-bit example first fails the checked full mask at row 16, consistent with
its filename's rows0..15 scope.

These are raw compression blocks with a shared, chosen chaining value. None
starts at the standard IV, and no valid-padding assertion is made. Prefix
conformity does not establish a full 39-step characteristic or collision.
One file prints its common chain once; that single-chain shared-CV convention
is explicit in records.json. The other four print it identically twice.

The verifier preserves signed u=(1,0) and n=(0,1), checks A/E/W values and
differences at every bit, verifies three complete SHA-256/hashlib controls,
and rejects a one-bit message mutation for each matching mask. It also checks
the c-bit repair diagnostic and all saved numerical fields. Its manifest is
an integrity inventory, not a signature. The historical eight-pair population
has not been recovered by this five-file export.
