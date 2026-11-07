# Standard-IV prefix examples: replay the actual conditions

Extract this kit and run `python replay.py` inside `prefix-pairs-kit` with
Python 3.9 or newer. Only the Python standard library is needed. Expected:
51 source records, 39 distinct ordered message pairs, six complete A/E/W
row-mask comparisons, zero equal working states after all 64 steps.
Do not run with `-O`; the verifier deliberately refuses disabled assertions.

These are saved October 31 prefix examples, **not 39 new collisions**.
Every pair starts from the standard SHA-256 IV and has different raw 16-word
blocks. Padding eligibility, an attack success law and a discovery price are
not established. Equal early states before the messages diverge do not imply
a complete hash collision. The records retain the exact checked step counts.

Only two matching characteristic descriptions accompany this export. Six pair
files match them. The other 45 source files have numerical replay only; their
filenames are not accepted as proofs of prefix-condition satisfaction.

## Results with matching characteristics

- Four S12K13 files first violate the full saved A/E/W row table at rows
  18, 19, 20 and 21, respectively. In this ladder, A/E rows from 13 onward
  are all `?`. The later successes extend schedule conditions, not full state
  conditions. The two notions of depth must remain separate.
- The S40_join_A web prefix first violates row 15; the later saved prefix
  first violates row 18. Its verified rows 0 through 17 have full A/E
  conditions. Neither pair closes the full 40-step state.

The saved S12K13 table also leaves A/E rows 0–8 unconstrained. Across rows
9–12 it imposes eight A and 25 E bit conditions: 33 literal state conditions
in total. The four verified prefixes respectively impose 320, 352, 384 and
416 literal W conditions. These are literal mask counts, not independent
probability exponents. For the full S40_join_A prefix through row 17, the
counts are 576 A, 576 E and 576 W conditions.

Rows are zero-based: rows 0 through 17 include 18 SHA-256 updates. Negative
A/E rows encode the initial state. Mask strings run most-significant bit first.
`u` means member 1 bit 1, member 2 bit 0; `n` means 0,1; `-` equal; `x`
different; `0` and `1` pin both members; `?` imposes no condition. Unknown
symbols are rejected, not ignored. The verifier compares A, E **and W**.

Some original XML has an unescaped `<` in descriptive comment text. The source
was not amended. The data projection records this syntax failure and extracts
only a uniquely delimited, separately parsed `char` element. It does not
certify the original document as a valid XML encoder input. No XML options,
commands or operational notes are included.

The export's printed `out` words were checked against all 1–64-step traces;
they describe working state, not SHA-256 feedforward. `pairs.json` preserves
that interpretation as audit metadata. The portable replay recomputes the
states and row checks; it does not reread the original text export. Common-IV
feedforward preserves full-state equality or inequality at a fixed step.

## Files and provenance

- `pairs.json`: data-only numerical words, exact row projections, original
  source-relative filenames and SHA-256 fingerprints, expected checked rows.
- `sha256_reference.py`: exact reviewed project independent implementation,
  credited in its original header. Its command-line entry point is not run.
- `replay.py`: publication verifier; imports the reference, runs three standard
  hashlib controls, all records, strict symbol controls and one-bit mutations.
- `MANIFEST.json`: byte lengths and hashes of all other kit files. Hashes
  identify this bundle; they are not signatures or attack-probability proofs.

The publication adds validation and scope, not a new discovery attribution.
Original research contributors retain credit. No ordinary chats, solver jobs,
external papers/PDFs or blanket third-party redistribution license are bundled.
