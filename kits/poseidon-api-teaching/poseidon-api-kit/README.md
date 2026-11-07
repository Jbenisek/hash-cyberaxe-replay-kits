# Poseidon reference API: a complete finite recipe

Run inside the extracted poseidon-api-kit directory:

    python -B replay.py

Python 3.10+ and its standard library are sufficient. No installation, original
workspace, network, solver or imported organizer program is needed. Do not use
Python -O: the archived API uses assertions for some input constraints.

The script checks exact hashes before importing the project-owned poseidon_ref.py.
It reads numerical parameters from the library's finite-witnesses.json and adapts
their field names into a temporary JSON file for the API's historical import
interface. That temporary file is removed and the process environment is restored
after import. No original research or persistent parameter file is modified.

## What the result means

Expected: passed: true, 33 distinct_witnesses, five mutated_profiles, 74 named
passing checks and 20 rejected invalid inputs. Full-round controls comprise
eleven permutation vectors, eleven hash vectors and eleven full/reduced API
agreements, plus two numerical crosscopy controls. The reduced checks cover the
33 existing Poseidon profile/pair identities at r1 through r5. These are existing
records, not 33 new discoveries or a measured success rate.

The five one-bit mutations must fail the corresponding recorded digest. Invalid
field values/types, malformed byte buffers, a field encoding equal to the modulus
and out-of-range schedules must be rejected. Source or numerical-data hash changes
are refused before import. A disagreement exits nonzero; do not edit expected
values merely to obtain a passing result.

## Target conventions

Orchard P128Pow5T3 over Pallas. A message is two canonical 32-byte little-endian
field values. The initial state is [nk,rho,2^65]; output is coordinate zero in
32-byte little-endian form. r counts partial rounds: keep full indices 0..3,
partial indices 4..3+r and full indices 60..63. r2 is ten total rounds; r56 is
the full 64-round permutation. The constants keep their original indices.

This is a fixed-capacity two-element hash, not an arbitrary-state permutation
collision or the full Orchard nullifier. All equality checks concern the exact
profile stated by the witness. No full-round collision, attack-price proof,
trial-independence assumption or novelty claim follows.

## Attribution and limits

The numerical file is the already-published finite-replay dataset, unchanged.
It contains 49 cross-protocol witness records; this wrapper selects only the 33
Poseidon records. It also preserves numerical parameters, known-answer vectors,
source hashes and citations. The SHA3 records are not tested by this wrapper.

Parameters are attributed to halo2_poseidon-0.2.0 and historical Zcash fixtures:
https://github.com/zcash/halo2/tree/halo2_poseidon-0.2.0/halo2_poseidon
https://github.com/zcash/zcash-test-vectors/tree/78321be

No external executable, proof text, PDF or ordinary conversation is bundled.
The library's independently authored finite-collision-replay.zip implements
separate equations; this kit instead tests the archived project reference API.
Full/reduced agreement within that API shares constants/helpers and is not a
new independent implementation. Finite controls do not prove arbitrary-input
correctness. The project-wide reuse license is not invented by this bundle.

Keep all files together. MANIFEST.json records hashes; the library download
metadata hashes the ZIP. Checks normally finish in well under a second, with
a 20-second internal witness-loop deadline; that deadline is not a hard budget
for every setup or API operation. The publication harness also uses a 30-second
child timeout. The API replay launches no children. The v2 wrapper runs API and log controls in two bounded, isolated subprocesses.


## Added log-checker controls (v2)

The same replay command also runs twelve copied-source controls for
verify_collision.py. An inert temporary fixture explicitly blocks its optional
organizer import: passing these tests is NOT organizer-verifier evidence.
The r1 and r2 positive examples use the project reference and existing public
numerical witnesses. They are not new collision discoveries.

No input files, a log without a digest and an uppercase-only digest can exit
zero without verifying a witness. Duplicate fields keep their last value.
A parsed bad digest, identical message pair, missing required field,
noncanonical field input and invalid schedule fail. The parser accepts
lowercase 64-hex-digit prefixes and does not validate trailing text. Require
an explicit positive verified-record count: exit zero alone is insufficient.

R defaults to 1 and counts partial rounds in addition to eight full rounds.
R=0 is not an identity operation. These controls do not execute a solver,
import organizer code, reproduce attack counters or establish a success law.

Keep all eight files together, including MANIFEST.json. The v2 wrapper launches
api_replay.py and check_log_contract.py using isolated Python mode with bytecode
writes disabled, each with a 30-second timeout. The latter creates and removes
temporary log fixtures and bounded checker subprocesses. Original source and
numerical inputs are never modified. The API's 74 named checks, 33 existing
witnesses and 20 invalid-input controls remain present, with twelve additional
cases under results.log_checker_contract.
