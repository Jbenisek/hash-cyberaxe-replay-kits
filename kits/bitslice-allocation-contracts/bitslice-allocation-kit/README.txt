BIT-SLICED BLAKE3 / ALLOCATION AND COUNTING CONTROLS

Extract the complete ZIP. Inside bitslice-allocation-kit run:
    python -I -B replay.py
Python 3.9+ standard library. No installation, network, solver, independent
organizer reference or historical workspace is needed. Do not use -O.
The replay uses disposable source copies and prints JSON, without writing a
permanent result file. It generates finite circuits; it does not search for
collisions or scan prefixes. Do not run the original selftest/stats/scan modes.

Expected: passed=true, two results. The single-block step checks 19,022
instructions; the fixed-prefix step checks 18,869. Both use register extent
771. Each rejects two altered-assignment controls. Artificial [5,5,5,7]
outputs give a reported repeated-entry count of 2 and an equal-pair count of 3.
Artificial returned pairs are NOT cryptographic collision witnesses.

What the structural check proves:
For each generated instruction, the checker verifies its operation and both
operands against the generated Python AST. It tracks which named symbolic
value each register holds. Each read must still hold the required value;
each write updates that fact. All final output registers must hold the
specified outputs. Induction over the instructions proves equivalence of
that generated straight-line program and its allocated execution for every
plane input. Dying operands may share a destination because reads precede
the write. The constant all-ones mask is checked explicitly.

What it does NOT prove:
Universal correctness of the BLAKE3 circuit generator; allocation of callers
or handlers; whole-word memory layout; historical preprocessing execution;
prefix minimality; success probability; or a complete attack price. Finite
independent digest comparisons are separately documented in the library;
the organizer's reference implementation is intentionally not bundled here.

The original source bytes are retained. Fixed SHA-256 pins are checked in
addition to the manifest, so changing a source and updating only its manifest
entry still fails. Archive integrity is not authorship authentication: obtain
the ZIP through the library's recorded archive SHA-256. No research sources
or campaign parameters are modified by this replay.
