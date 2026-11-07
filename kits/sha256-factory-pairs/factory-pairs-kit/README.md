# Thirty-three collisions and nine schedule examples

Extract this kit and run `node factory-pairs-kit/replay.cjs`.
Only Node.js and its standard library are needed; no solver, GPU or network.

Expected results:

- 33 distinct 39-step SHA-256 compression collisions with 33 distinct common
  chosen chaining values. None uses the standard IV.
- 99 negative controls: one changed input bit, a 40-step extension and a
  64-step extension for each pair. None collides.
- Five 40–44-step standard-IV schedule examples. Their computed lit schedule
  rows match the data, but their state and compression outputs differ.
- Four 41–44-step chosen-CV schedule examples, separately labeled. Their exact
  supports, printed working states and computed feedforward outputs reproduce;
  none collides. All nine schedule identities are distinct.
- Four full SHA-256 known answers checked against Node's crypto library.

## The model matters

Each collision uses sixteen raw 32-bit message words and the same chosen
eight-word chaining value on both sides. Feedforward adds that common value
to the final working state. These are compression examples, not standard-IV
hash collisions or legal padded-message certificates. The number 283 is the
historical factory label; this kit does not price 2^283 work or certify a
condition count.

The current factory table records fifty seeds, thirty-three SAT-labelled outputs and
seventeen HELD runs at approximately a 300-second cap. Those timings and the observed 33/50 ratio
are historical reports, not a sampling-law proof, expected discovery cost or
contest-ready success rate. The pairs themselves are checked independently
of those reported labels. They are archived project outputs, not discoveries
made by this publication audit and not a new round record.

The five standard-IV files were previously missing from the publication audit.
Their availability closes a source-evidence gap, not the open full-collision
problem. The saved printed outputs in those files are working states before
feedforward; the JSON identifies this convention explicitly.

The four additional chosen-CV schedule files are SPARSE41, LADDER42, LADDER43
and LADDER44. Their expanded nonzero rows are respectively {18,26,27},
{16,17,18,27}, {16,17,18,19,28} and {16,17,18,19,20,29}. These are not the
same objects as the standard-IV examples: preserve both the initial-state law
and actual message words. The latter three contain terminal bit patterns in
one working state; that is not equality of the two complete states.

## Provenance and safety

`pairs.json` contains only selected numerical records, safe source identifiers
and hashes. It does not redistribute the full registry, surrounding user-agent
conversations, operational commands or any external paper. The selected factory
entries are marked team-origin in the source registry.

The earlier edition compared 24 identities with 145 existing library identities,
yielding 169 across those sets. This edition replays all 33 current table entries
and compares step count, common CV and unordered message pair against those 169.
Twenty-four are already represented; nine are additional, yielding 178 across
those selected sets—not 178 new discoveries today. Other prefix-only,
local-factory or game-measurement collections are not added to that scoped total.

The Python audit and this JavaScript replay independently agree on the finite
outputs. The manifest binds every file. Modified payloads are rejected; hashes
identify an edition, not an attack success law or an unrestricted license.
The package preparation also rejects a false chosen-CV schedule output with
a consistently rehashed manifest, demonstrating a numerical check independent
of the metadata digest.
