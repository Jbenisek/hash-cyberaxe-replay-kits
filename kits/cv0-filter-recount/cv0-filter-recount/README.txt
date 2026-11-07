Selected-CV F7: exact recount of retained samples
================================================

Run: python -I -B replay.py
Python 3.9+. No network, solver, random sampler or remote worker.
Optional NumPy speeds up the same finite arithmetic. Without NumPy, the
standard-library fallback checks all 70 rows on one CPU and can take several
minutes. To force that path, run: python -I -B replay.py --scalar

The two binary files are original retained q pools, renamed only for this
kit. Each contains 1,048,576 little-endian uint32 words. records.json pins
their original identities, the reference specimen and all 70 count rows.
The checker derives the local F7 constants from sixteen reference steps,
then checks every stored q for every recorded CV0. The NumPy path also
checks 9,450 scalar/vector comparisons including wraparound cases.

The event is
  w = (0x40b794c4 - CV0 + q) mod 2^32
  [sigma0(w + 0x20000000) - sigma0(w)] mod 2^32 == 0x03bff800
where sigma0(x)=rotr7(x) XOR rotr18(x) XOR(x>>3).
The input to sigma0 is always reduced to 32 bits.

The word 4d2f1627 gives 136827/1048576 on cv0fresh1. It does NOT appear in
the 64-candidate cv0pick2 scan. An older sixteen-candidate output gives a
different count for that word, but its pool identity has not been recovered
by this audit. Do not invent an independent second recount of the winner.

These are G-passing SAMPLED q pools. Exact counting of their members is
not exact counting of the underlying population. The inherited uniform-CV
baseline 287309824/2^32 is not independently enumerated by this kit.
No statistical independence, unbiased selection, exact population success
or whole-attack gain is certified. Fixing CV0 changes the trial law; its
generation/selection cost and downstream success must be established before
using this effect to lower a claim price. No new attack score is provided.

Only the data projection, numerical pools and new finite checker are shipped.
No private chats, remote launchers or original sampling driver are included.
