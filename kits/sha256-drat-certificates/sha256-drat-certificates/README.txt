TWO SCOPED SHA-256 FORMULA CERTIFICATES

What is here
------------
Two retained CNF formulas, their DRAT proofs, numerical variable maps, the
two characteristic XMLs and the exact reviewed encoder. The publication audit
freshly checked both proofs on copies and regenerated both clause sequences.
These are existing research artifacts, not newly discovered attacks.

pub39: 82,195 variables / 380,081 clauses. Its map declares 39 steps and the
standard IV. Both copies' eight IV words were checked against the standard
constants. This is one encoded characteristic, not all 39-step collisions.

joint46: 86,033 variables / 394,911 clauses. Its map declares 40 steps and a
free chaining value. Two retained CNF filenames have identical bytes; count
them as one formula, not two independent encodings.

Start safely
------------
Requires Python 3.11 or newer, standard library only for the identity check.
In this extracted directory:

    python -B check.py

This verifies manifest byte counts and SHA-256 identities. It does NOT check
the proofs. The output explicitly says proof_replay_performed=false.

To reconstruct the formulas from their bundled source and characteristic:

    python -B check.py --rebuild

This runs the copied encoder with SIGNED=1 and BITORDER=msb, clearing optional
research controls. It compares every clause in order, ignoring only platform
newlines, and compares every retained variable-map field. The newer encoder
also records W1all/W2all. Reconstruction alone is not an UNSAT proof.

To check the proofs, obtain/build DRAT-trim yourself from the upstream project:
https://github.com/marijnheule/drat-trim
We do not download or run an installer. The checker is third-party software;
its authors and license remain upstream. The audit records its exact binary
hash and C-source hash; a reproducible binary build has not been established.

With your platform's locally built executable:

    python -B check.py --rebuild --checker /absolute/path/to/drat-trim

The wrapper first accepts a tiny valid control and rejects an invalid proof.
It then checks the two copied proofs one at a time, with a 40-second checker
limit and 55-second parent timeout per invocation. It never calls a solver,
starts workers or accesses the network. Original distributed inputs are not
modified. A different platform/build can have a different binary hash; that
fact is reported rather than silently hidden.

Interpret the result
--------------------
Fresh checker acceptance proves refutation of these exact Boolean formulas
under that checker's documented semantics. It does not, by itself, prove that
every encoder option matches a desired SHA-256 question, that a whole family
is impossible, or that a collision search has a particular success rate.

The retained proofs produce duplicate-literal and ignored unit-deletion
warnings. DRAT-trim documents those normalization/deletion behaviors. The
audited acceptance is not a claim of strict warning-free DRAT syntax. Do not
suppress warnings when investigating a portability difference.

The 40-step encoding log prints signed-bits-as-x=212 while its launcher asks
for SIGNED=1. The label is misleading: the reviewed signed branch adds the
two oriented unit constraints. Reconstructing with signed handling reproduces
both original formulas exactly. This resolves the edition/option identity;
it does not supply an all-input theorem about every encoder mode.

The audit did not rerun the original multi-seed launches. UNKNOWN runs remain
UNKNOWN, and the historical HELD label for the particular joint46 formula is
superseded by its retained and freshly replayed refutation only.

Rights and provenance
---------------------
Only project research formulas, proofs, numerical maps, characteristic XMLs,
the project encoder and this wrapper are
included. No agent/user chats, launch scripts, network credentials, external
papers/ebooks or third-party checker executable are bundled. Original source
locators and exact digests are in manifest.json. Retain these qualifiers and
credits when redistributing or writing about the artifacts.
