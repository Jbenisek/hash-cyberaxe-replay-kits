SAVED PAIRS, REPLAYED; DECODER COMMENTS, ISOLATED

This pack preserves 125 distinct unordered (rounds, common CV, message-pair)
identities represented by 155 retained files. It contains numerical specimens,
provenance hashes, independent replay arithmetic and a tiny decoder regression
lesson. It does not rerun searches, original launchers or SAT decoding campaigns.

Requirements: Node.js with BigInt buffer support; Python 3.11+ for the optional
parser lesson. Standard libraries only. No network, installer or solver.

From the extracted redecoded-pairs directory:

    node replay.cjs
    python -B decoder-control.py

The first command checks all file identities, seven full-round SHA-256 reference
gates, every stored reduced-round collision including feedforward, and one-bit
and one-step controls. Expected: 125 distinct pairs, 155 source-file rows,
zero standard-IV pairs, zero surviving one-bit controls, and two surviving
one-step controls (the 25- and 28-step specimens). A one-step extension is a
test, not an assumption that every specimen must fail it.

Distinct pairs by step count: 25:1, 28:1, 31:1, 36:2, 37:22, 38:32, 39:66.
File rows by step count:      25:1, 28:1, 31:2, 36:2, 37:25, 38:36, 39:88.
There are 127 ordered identities; identifying swapped message order gives125.
The earlier summary's126 count does not match either rule on these exact155
files. We report the current hashed collection, not a conjecture about why
that historical number differed.

The second command checks seven synthetic log fixtures against exact extracts
of two decoder functions. The hash function is deliberately stubbed: this
command tests literal ingestion only and is not a collision verifier. With
column-zero v-lines, the revised decoder excludes statistics integers. The
older parser lets trailing comments overwrite message bits. Both still allow
missing assignments to default and contradictory assignments to use their
last value. Indented prefixes are outside the demonstrated safe contract.
The full encoder modules and their top-level code are not executed here.

Scientific scope
----------------
These are common-chosen-CV compression collisions. They are not ordinary
standard-IV SHA-256 hash collisions, new step records or attack work factors.
The public collection comparison found43 already represented and82 absent
from the five explicitly checked baseline collections (177 distinct prior
identities). This is not a global novelty claim. The comparison metadata and
baseline hashes are retained in pairs.json; offline replay does not require
the old collections or re-establish their availability.

Some original recovery scripts guessed a suitable map by variable count and
then accepted numerical equality. Numerical collision replay does not prove
that the recovered pair satisfies the original solver's CNF, XML characteristic
or map provenance. Preserve those distinctions when citing the data.

No user-agent chat, raw coordination, original research launcher, credentials,
external paper or ebook is included. Decoder extracts and underlying specimens
are project research; arithmetic reuse and original source hashes are recorded
in manifest.json. Keep the model and scope with any redistributed pair.
