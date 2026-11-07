# HASH$CyberAxe replay kits

> **By Jeremy Benisek ([CyberAxe](https://cyberaxe.dev/))** · part of **[HASH$CyberAxe](https://hashcyberaxe.com/)** open research
>
> Research library: [hashcyberaxe.com](https://hashcyberaxe.com/) · Tools & data: [hashcyberaxe.com/tools.html](https://hashcyberaxe.com/tools.html) · Play the game: [hashcyberaxe.com/game](https://hashcyberaxe.com/game/)

**What this is for.** Small, self-contained kits that each reproduce one published HASH$CyberAxe result, recount or teaching example from its saved data. Every kit has its own README, the exact input files and `check_project.py`, which verifies the files and, with `--replay`, reruns the kit's finite replay. Use them to check a claim yourself, learn a method on a small worked example, or start a fork.

**Credits.** Author: **Jeremy Benisek (CyberAxe)**: research direction, questions and project lead. Made with AI research and coding agents working under CyberAxe's direction; the agents are tools, not authors. Third-party code keeps its original authors and notices ([AUTHORS.md](AUTHORS.md)).

**License.** See [LICENSING.md](LICENSING.md). Credit: "Jeremy Benisek (CyberAxe), HASH$CyberAxe, https://hashcyberaxe.com/".

## Use a kit

```sh
cd kits/<kit>
python -B check_project.py            # verify the kit's exact files
python -B check_project.py --replay   # rerun its finite replay
```

Python 3.11 or newer, standard library only, unless a kit's README says otherwise. Each kit folder is self-contained and carries its own license files, so you can copy or fork one kit on its own.

## The 61 kits

| Kit | What it reproduces | Tool family | Replay check |
|---|---|---|---|
| [b32-schedule-pairs-v2](kits/b32-schedule-pairs-v2/) | Three full-width sparse-B schedule pairs: independent numerical replay | - | passed |
| [b32-schedule-pairs](kits/b32-schedule-pairs/) | Two full-width sparse-B schedules: exact numerical replay | - | passed |
| [backward-schedule-replay](kits/backward-schedule-replay/) | Backward schedule: exact words, not an attack price | - | passed |
| [bitcost-contracts](kits/bitcost-contracts/) | A search ordering score is not a success probability | - | passed |
| [bitslice-allocation-contracts](kits/bitslice-allocation-contracts/) | BIT-SLICED BLAKE3 / ALLOCATION AND COUNTING CONTROLS | - | passed |
| [boardpair-teaching](kits/boardpair-teaching/) | SHA-256 board-pair teaching kit | SHA pair encoder & SAT bridge; Independent SHA verifiers | passed |
| [bsel-generator-contracts](kits/bsel-generator-contracts/) | BLAKE3 / MASKED WALK AND RETAINED GENERATOR REPLAY | - | passed |
| [count253-278-recount](kits/count253-278-recount/) | COUNT253 / COUNT278: raw exports and exact saved-data recount | - | passed |
| [current-encoder-contracts](kits/current-encoder-contracts/) | Which output did the SHA encoder actually compare? | - | passed |
| [cv0-filter-recount](kits/cv0-filter-recount/) | Selected-CV F7: exact recount of retained samples | - | passed |
| [d126-model-replay](kits/d126-model-replay/) | Time, memory and the shard trade-off | Batch, memory & charge calculators | passed |
| [dig38-verdict-replay](kits/dig38-verdict-replay/) | A log, two labels: SHA-256 research provenance | - | passed |
| [early-state-contracts](kits/early-state-contracts/) | When the template proves the wrong thing | - | passed |
| [encoder-summary-contracts](kits/encoder-summary-contracts/) | Encoder and summary contracts: reproduce the interface boundaries | SHA pair encoder & SAT bridge | passed |
| [family-places-recount](kits/family-places-recount/) | SHA-256 family placements: inspect the saved data, keep the evidence layers apart | - | passed |
| [finite-collision-replay](kits/finite-collision-replay/) | Finite collision replay kit | - | passed |
| [four-pattern-replay](kits/four-pattern-replay/) | Four-pattern witness replay and verifier boundaries | - | passed |
| [fulltrail-builder-contracts](kits/fulltrail-builder-contracts/) | Full-trail XML builder: finite interface controls | SHA pair encoder & SAT bridge | passed |
| [game-evidence](kits/game-evidence/) | From game events to scientific evidence | - | passed |
| [historical-common-cv](kits/historical-common-cv/) | Historical common-chaining-value SHA-256 compression pairs | - | passed |
| [interrupted-move-tests](kits/interrupted-move-tests/) | Six historical tunnel-move tests: transcript and interpretation replay | - | passed |
| [jam-leak-recount](kits/jam-leak-recount/) | ABSORPTION JAM / LEAK MAP: SAVED NUMERIC TABLE REPLAY | - | passed |
| [lawbase-example](kits/lawbase-example/) | LAWBASE: FROM A MESSAGE PAIR TO A SEARCH BASE | Numerical pair → characteristic tools | passed |
| [mkxml-contracts](kits/mkxml-contracts/) | Reproduce the SHA-2 mask corrections | Numerical pair → characteristic tools | passed |
| [near-iv-prefix-replay](kits/near-iv-prefix-replay/) | NEAR-IV EXAMPLES: FIVE RAW-BLOCK PREFIX CHECKS | - | passed |
| [newwords-transformations](kits/newwords-transformations/) | Three ways to free a trajectory | - | passed |
| [november-pairs-replay](kits/november-pairs-replay/) | One colliding control and three incomplete state candidates | - | passed |
| [p9-deletion-replay](kits/p9-deletion-replay/) | P9 row deletion: replay what the saved evidence actually says | - | passed |
| [pairfactory-tables](kits/pairfactory-tables/) | Read the table before counting the result | - | passed |
| [poseidon-api-teaching](kits/poseidon-api-teaching/) | Poseidon reference API: a complete finite recipe | Poseidon reference & replay tools | passed |
| [poseidon-rho-contracts](kits/poseidon-rho-contracts/) | A packed birthday walk: recovery mechanics, not a full-field success proof | - | passed |
| [poseidon-xconv-lesson](kits/poseidon-xconv-lesson/) | One convolution: a finite accounting lesson | Transform pass & convolution planners | passed |
| [profile-contracts](kits/profile-contracts/) | Archived profile-tool contracts, with finite controls | Independent SHA verifiers; Trail & schedule diagnostics | passed |
| [r38-walk-recount](kits/r38-walk-recount/) | R38 FIRED-LANE WALK: EXACT RECOUNT, CONDITIONAL ATTACK CLAIM | - | passed |
| [r39-memory-ledger](kits/r39-memory-ledger/) | Historical r39 memory ledger: numerical replay | - | passed |
| [redecoded-pairs](kits/redecoded-pairs/) | SAVED PAIRS, REPLAYED; DECODER COMMENTS, ISOLATED | - | passed |
| [saved-outcome-ledgers](kits/saved-outcome-ledgers/) | SAVED OUTCOME LEDGERS / BOUNDED RECOUNT | - | passed |
| [scaled-sigma-audit](kits/scaled-sigma-audit/) | Scaled sigma assumptions: a finite encoder audit | - | passed |
| [scan-driver-contracts](kits/scan-driver-contracts/) | Query generation and restart semantics: bounded scan-driver lesson | 39-step pair factory | passed |
| [sched-width-contracts](kits/sched-width-contracts/) | Small-word tests can change the algebra | - | passed |
| [schedule-cells](kits/schedule-cells/) | When a condition has already been paid | - | passed |
| [seed-prefix-contracts](kits/seed-prefix-contracts/) | Seed writer and prefix-checker teaching kit | Independent SHA verifiers; Numerical pair → characteristic tools | passed |
| [selector-guard-contracts](kits/selector-guard-contracts/) | SHA-256 ENCODER SELECTOR GUARDS / FINITE COUNTEREXAMPLE | - | passed |
| [sha256-drat-certificates](kits/sha256-drat-certificates/) | TWO SCOPED SHA-256 FORMULA CERTIFICATES | - | passed |
| [sha256-factory-pairs](kits/sha256-factory-pairs/) | Thirty-three collisions and nine schedule examples | - | passed |
| [sha256-local-factory](kits/sha256-local-factory/) | Six factory files, two collision identities | - | passed |
| [sha256-pairs39-replay](kits/sha256-pairs39-replay/) | SHA-256: 60 finite 39-step pairs | - | passed |
| [sha256-recovered31](kits/sha256-recovered31/) | Recovered SHA-256 witness set | - | passed |
| [sha256-witness-replay](kits/sha256-witness-replay/) | SHA-256 witness reproduction | - | passed |
| [sha3-local-objects](kits/sha3-local-objects/) | SHA-3: exact local objects, explicit global limits | - | passed |
| [sparse-b-lemma](kits/sparse-b-lemma/) | Sparse B: finite controls for a lossless top-bit implication | - | passed |
| [sparse-schedule-replay](kits/sparse-schedule-replay/) | Sparse SHA-256 schedule checks, not collision checks | - | passed |
| [sparsedoor-price-contracts](kits/sparsedoor-price-contracts/) | What an exact fraction does—and does not—prove | Batch, memory & charge calculators | passed |
| [standard-iv-prefixes](kits/standard-iv-prefixes/) | Standard-IV prefix examples: replay the actual conditions | - | passed |
| [steering-ledgers](kits/steering-ledgers/) | A ledger is a record of an experiment, not its proof | - | passed |
| [sub283-ledger-recount](kits/sub283-ledger-recount/) | SUB-283 SAVED-LEDGER RECOUNT | - | passed |
| [support-overlap](kits/support-overlap/) | Same support does not mean the same experiment | - | passed |
| [template-contracts](kits/template-contracts/) | Document-template contracts: finite, disposable controls | Template & row assembly tools | passed |
| [up39-corrected-ledger](kits/up39-corrected-ledger/) | UP39 corrected job ledger: saved receipts, not new verdict proofs | - | passed |
| [w11-class-recount](kits/w11-class-recount/) | Why this signed word cube has 128 equally sized classes | W11 local class tools | passed |
| [walk-measure-contracts](kits/walk-measure-contracts/) | First repeat is not yet a collision | - | passed |

The full tool sources are in [hash-cyberaxe-toolkit-source](https://github.com/Jbenisek/hash-cyberaxe-toolkit-source), TrailLab in [hash-cyberaxe-traillab-source](https://github.com/Jbenisek/hash-cyberaxe-traillab-source) and the data in [hash-cyberaxe-research-data](https://github.com/Jbenisek/hash-cyberaxe-research-data).
