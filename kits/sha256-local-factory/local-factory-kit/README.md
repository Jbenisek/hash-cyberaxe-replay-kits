# Six factory files, two collision identities

Extract the archive, enter `local-factory-kit`, then run:

```text
python -I -B replay.py
```

Python 3.10+ and its standard library are sufficient. No network, solver,
compiler, GPU or original checkout is required. This replay launches no jobs
and changes no input files. Run the wrapper, not the archived reference's
standalone random-test driver. Optimized Python mode (`-O`) is rejected.

## What you can reproduce

Six saved outputs from the project's November 1 factory kit contain **two**
distinct message-pair identities: one at 37 steps and one at 38 steps. Each
identity appears in three files under different base identifiers. The wrapper
recomputes all six, checks duplicate links and runs four standard-SHA-256
known-answer controls against Python's `hashlib`.

Both messages in each pair share a chosen initial chaining value; neither pair
uses SHA-256's standard IV. These are reduced-step compression collisions, not
collisions in the standard full SHA-256 hash. The supplied pairs cease to
collide when extended by one step and do not collide at 64 steps. Six one-bit
message mutations are also checked as negative controls.

The original `out=` field is the terminal working state **before feedforward**.
The replay adds the common chaining value word by word modulo 2^32 and checks
the complete resulting digest. `records.json` labels that feedforward digest
separately. Shared initial states preserve equality across feedforward, but do
not make the two representations interchangeable.

## Record table

| Steps | Saved base identifier | Identity | Duplicate of |
| --- | --- | --- | --- |
| 37 | d28_651af2505f0f | A | First record |
| 37 | d28_6da90fa8c6a7 | A | d28_651af2505f0f |
| 37 | d28_f17a31bfeb3e | A | d28_651af2505f0f |
| 38 | d29_0035a4af6a77 | B | First record |
| 38 | d29_50257c47044f | B | d29_0035a4af6a77 |
| 38 | d29_d1f818b92f02 | B | d29_0035a4af6a77 |

Every record has seed label 40000. Identity means step count, common chaining
value and the unordered pair of message blocks, not filename or signed-trail
identifier. All six originals are retained so provenance is not lost by
deduplication. A distinct filename or successful solver result is not proof
of a fresh message pair. The source kit's general freshness language must not
be treated as a proven uniqueness guarantee.

## Scope and attribution

The original numerical records are from
`research/tools/factory_kit_1101/pairs`. The source kit is credited to HASH$CyberAxe;
the independent compression reference is the HASH$CyberAxe team's
`research/tools/indep_sha256_check.py`. Publication packaging and these bounded
checks do not claim discovery of the original collisions. The separate
24-witness round-39 factory corpus is not this dataset.

No SAT solver, encoder, base XML, launch script or performance claim is included
or certified. This finite replay does not prove the factory finds new pairs,
establish a success probability, price an attack, certify all twenty base
families, or establish global novelty. The reference's four hashlib controls
are useful finite checks, not a proof of correctness on arbitrary inputs.

`MANIFEST.json` records every payload size and SHA-256 hash. Match the archive
hash against library download metadata as well: a self-contained manifest is
an integrity check, not an external signature. No blanket license over upstream
material is asserted.
