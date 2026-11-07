# SHA-256 witness reproduction

Requires Node.js; no package installation or network access is used.
From this directory run:

    node examples/replay.cjs

Expected: PASS: 4 standard SHA-256 vectors; 54 39-step semi-free-start pairs; 1 negative control.

The compression API consumes sixteen 32-bit words and an eight-word common
chosen initial chaining value. It does not add message padding. The source's
expected_output is the working state BEFORE feed-forward. The replay checks
that field, then checks equality of both feed-forward outputs.

The four standard one-block vectors validate the 64-step implementation
against Node crypto. The 54 research pairs use 39 steps and a chosen common
initial state. They do not establish a standard fixed-IV SHA-256 collision.

Source lineage: research/game/climber/guided/pairfactory/found/FOUND_pf_001.txt
through FOUND_pf_054.txt. Individual provenance is in the library catalogue.
