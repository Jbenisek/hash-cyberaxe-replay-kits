# A ledger is a record of an experiment, not its proof

This finite Python 3.9+ standard-library kit recounts four unchanged historical
files. It runs no research launcher, encoder, solver or sampling campaign.
Extract, enter `steering-ledgers-kit`, then run:

```text
python -I -B replay.py
```

Expected output: `passed: true`, 64 alpha identifiers, 4,194,304 summed integer
weights, 21 class-snapshot rows, 67 larger-ledger rows, and eight final census
targets plus two interim events. Missing or changed files are rejected before
recounting. The checker pins historical digests independently of the manifest.

## What each record means

| Source | What is reproduced | What is not established |
| --- | --- | --- |
| alpha_set_W10_64.tsv | 64 unique hex identifiers; headerless positive counts sum to 2^22; min 64,772, max 66,184 | Whether the weights came from exhaustive enumeration or sampling; complete reachability proof |
| CLASS_MAP_38.tsv | 21 rows, fixed beta 03011296; 15 UNSAT labels and six unresolved/timeout labels | Checked UNSAT certificates, arbitrary-class success or exact total attack cost |
| RES.txt | 67 unique labels: all 64 inventory values and three outside-list values; 56 UNSAT codes and 11 timeout codes | Identity of encoded instances across different snapshots; new solver results |
| census_0.tsv | Eight final targets and two interim events; one target visits levels 0, 1 and 2 | Ten independent cells, complete discovery cost or checked solver proofs |

Within the 64-value inventory the larger ledger has 53 UNSAT return-code labels
and 11 timeout-code outcomes. The three additional labels are outside the saved
inventory. That membership test does not independently prove their algebraic
unreachability. Return code 124 remains unresolved, not UNSAT.

The smaller and larger class ledgers are separate snapshots. Preserve both.
Different timings for a shared label must not be silently substituted; a
filename is not an exact CNF identity. No proof certificate is included.

## Schemas and common mistakes

The alpha inventory has no header. Its first line is a real class; discarding
it as a header loses data. The second column is an integer weight of unresolved
generation provenance, not a guaranteed probability or number of collisions.

The class snapshot has alpha, beta, verdict, seconds, witness, classes and L.
A dash means unavailable. No numerical witness is supplied by this table.

Census final lines have twelve columns: rounds, input-word support,
expanded-word support, verdict, budget level, seconds, result source, target
label, conflicts, decisions, propagations and restarts. Lines starting `#u`
are interim events with eight fields after the prefix; other comment lines
describe the shard and calibration. `top_rec_d+2_R38` has two undecided rungs
then one UNSAT-labelled rung. These are three events for one recorded target.

Recorded seconds are per event and environment-specific. They are not a
contest reference-machine charge. Do not add labels or timeouts to a collision
count, infer statistical independence, or treat local restrictions as a
universal impossibility theorem.

## Provenance and limits

The four files retain exact original bytes. `PROVENANCE.json` identifies their
paths, hashes and the independent publication recount. `MANIFEST.json` covers
all packaged files. The kit includes no original executables, raw conversation,
external paper or operational launcher. No blanket third-party licence or
worldwide novelty claim is implied.
