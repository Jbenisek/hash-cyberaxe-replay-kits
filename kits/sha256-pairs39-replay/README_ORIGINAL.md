# SHA-256: 60 finite 39-step pairs

61 source rows contain 60 distinct unordered pairs. All 60 pass full working-state
and feed-forward equality at 39 steps. One overlaps the earlier 85-pair library
sets; 59 are additional identities, yielding 144 across the three sets.

These are chosen-CV, semi-free-start compression collisions, NOT standard-IV
SHA-256 hashes. Padding eligibility and discovery cost are not certified.
All 60 same-message, same-CV extensions fail at 40 steps. This finite negative
control does not prove that other pairs or parameters cannot reach 40 steps.

Extract this ZIP and run from its top directory with Node.js:

    node research/public_library/qa/replay_pairs39.cjs

Built-in modules only: no network, solver, sampling, or file writes. The checker
tests the standard abc vector and recomputes both messages at 39 and 40 steps.
Expected summary: source_rows=61, distinct_pairs=60, verified=60, failed=0,
previously_published=1, new_verified=59, standard_iv=0, one_step_collisions=0.

Historical tail estimates are metadata, NOT measured again or certified here.
The two earlier normalized collections are included only as identity baselines;
their own replay kits remain separately available. MANIFEST.json hashes all
included sources and the fresh verifier. Keep the original sources and credit.
