Historical common-chaining-value SHA-256 compression pairs
=========================================================

This is historical project data, not a new attack or discovery claim.
It contains 1,286 distinct message-pair identities and 1,288 source receipts:
179 at 36 rounds; 478 at 37; 156 at 38; 473 at 39. No 40-round pair is included.

Both messages in every pair use the SAME CHOSEN NONSTANDARD input chaining
value. None starts from the standard SHA-256 IV. These are not ordinary
SHA-256 hash collisions. Padding eligibility and attack prices are not proved.

Run after extracting this folder, with a current Node.js installation:

    node replay.cjs

No network, mapped drive, solver or GPU is needed. The command checks pinned
input bytes, two standard SHA-256 controls, every pair's full 32-bit schedule,
working-state equality, feed-forward output equality and the exact census.
It accepts no launch arguments and performs no research search.

records.json is the complete parsed scientific data. Source receipts retain
the original relative paths, hashes and the round-binding method. Original
source bytes were checked during preparation; this kit does not redistribute
all source files or independently certify those historical provenance claims.
When the old text omitted a round count, the preparation audit required a
unique exact saved-state/output match over rounds 1 through 64, or an exact
pair match to a structured public witness record. Filenames never supplied R.

Some source representations duplicate pairs already present in three public
witness datasets. That comparison was not a complete semantic catalogue audit;
absence from those datasets is not evidence of novelty or missing publication.

The replay's SHA-256 implementation is the existing library implementation.
Its exact bytes and this edition of records.json are pinned in replay.cjs.
Changing either requires a separate review. A SHA-256 digest is an integrity
guard, not a satisfiability proof or a proof of historical authorship.

No blanket license is asserted; consult project publication terms and lineage.
