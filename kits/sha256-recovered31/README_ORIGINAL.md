# Recovered SHA-256 witness set

31 finite pairs: 29 at 38 steps, two at 39 steps. All use full 32-bit words
and a common chosen chaining value (semi-free-start compression). They are
NOT standard-IV SHA-256 collisions. No message-padding eligibility is claimed.

Extract this ZIP, change into its top folder, and run with Node.js:

    node research/public_library/qa/replay_resolve31.cjs

The script reads the included registry and original witness files, checks the
64-step abc control, and independently recomputes both messages at n and n+1
steps. It prints JSON, performs no search, writes no files and uses no network.
Expected summary: verified=31, r38=29, r39=2, standard_iv=0,
one_step_collisions=0. A failure throws an error and exits nonzero.

Original and distributed witness bytes must have identical SHA-256 hashes.
This is a finite replay, not an estimate of discovery time, probability,
minimum support, novelty or a proof that another pair cannot extend a round.
Keep this set separate from the library's 54-pair r39 pairfactory selector.
