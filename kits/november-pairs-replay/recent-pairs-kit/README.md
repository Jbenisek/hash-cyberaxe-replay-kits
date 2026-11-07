# One colliding control and three incomplete state candidates

Extract the kit, enter recent-pairs-kit and run `node replay.cjs`.
Expected: passed=true, candidates=4, collisions=1, noncollisions=3.
The verifier also checks the standard SHA-256 abc known answer, rejects a
one-bit mutation of the colliding pair and rejects its 40-step extension.

All four objects use full 32-bit SHA-256 words, 39 steps and a common chosen
chaining value within each pair. None uses the standard IV. The routine accepts
16 raw message words; it does not establish message-padding eligibility.

The colliding control is angle_pub39_char_w32, recorded as new values on a
known published characteristic (pin39b). It is newly added to this library's
finite replay set, not a new round record or an assertion of new discovery now.
Its source describes a positive control. The other three UP39 files are state
candidates: their full 39-step compression outputs differ. A filename containing
pair is not itself a collision claim, and this result is not a criticism of
experiments that deliberately test partial objects.

pairs.json includes exact numerical words, recomputed outputs, original paths
and source SHA-256 values. It excludes surrounding operational notes and chats.
The SHA-256 implementation is the publication's existing independent JavaScript
replay, not an imported solver or encoder. No search, network or project writes
occur. The bounded replay needs only Node.js and its standard library.

MANIFEST.json identifies every other kit file. Hashes identify bytes, not an
attack success law. No discovery cost, statistical gain, full-round hash break
or blanket source-code license is asserted. No external paper/PDF is bundled.
