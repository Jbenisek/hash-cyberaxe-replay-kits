# First repeat is not yet a collision

This offline lesson explains the pinned Poseidon reduced-width measurement
script, not the full Poseidon map, an attack's success probability, or its price.
It preserves the research program unchanged and extracts five function
definitions for bounded tests. The original `rho` dependency is not imported.

## Run the lesson

Extract the archive, enter `walk-measure-kit`, then run:

```text
python -I -B replay.py
```

Requirements: Python 3.10+ and the standard library. No solver, network,
organizer module, cloud job or Poseidon search is started. Output is JSON:
`passed: true`, 16 cases, `actual_rho_imported: false`.
Assertions are required; optimized `-O` mode is rejected. Altered distributed
bytes fail manifest checks. A manifest is an integrity record, not a signature.

## What is measured?

Starting from v0, the script counts evaluations until the first visited state
reappears, including a return to v0. A cycle of an injective map also repeats.
For example, v -> (v+1) mod 4 repeats after four steps but has no distinct-input
collision. If a nonempty tail enters a cycle, the tail predecessor and cycle
predecessor of the entry point give a collision; a pure cycle lacks the first
predecessor. Recovery and distinctness therefore need a separate check.

For a uniformly random function on N states and a fixed starting state, before
the first repeat the next image at step n is a fresh uniform choice. Exactly n
states have already been seen. Thus

```text
Pr(T=n) = product(i=1..n-1, 1-i/N) * n/N,  1 <= n <= N.
```

The lesson enumerates every map on one through five states: 3,413 maps in
total. Every repeat-index count equals this exact rational law. This is a
finite check of a random-map argument, not a claim about concrete Poseidon.

## Where the fitted law needs care

The original replaces each hazard n/N with c*n/N. Its likelihood can be used
on observed samples only when every relevant hazard is a probability. It does
not check that domain. For example, loglik(4,[1],1) returns log(4), although
four is not a probability. Survival terms can instead raise a domain error.
The empirical n=4 sample on N=4 is possible, but the hard-coded fit bracket
can still crash before finding a result.

With c=1 the model is a normalized law on 1..N. For c<1 those first N hazards
leave positive survival mass even though a deterministic N-state walk must
have repeated by N. For c>1 the hazards eventually exceed one unless an
appropriate terminal rule is defined. The implementation is a fitted
early-repeat model, not an automatically normalized global family for every c.

The fit searches c in [0.05,4]. The interval searches [0.02,6] with likelihood
ratio cutoff 3.84. These are arbitrary search limits and an asymptotic
statistical threshold, not exact finite-sample coverage. Empty samples still
produce a fitted value and nearly the entire interval bracket. A sample of
immediate repeats reaches the upper fitting bound. Save boundary hits and
failures instead of silently treating them as reliable estimates.

## Original interface and reproducibility

The historical entry point is `python measure.py w trials seedbase`; it
imports sibling `rho.py`. Do not run that original during this lesson.
Per-trial RNG seed is seedbase*1000003+k. It selects an index in range(G_SET),
then a start in range(2^w). Reusing the same seed recreates the experiment;
it is not an independent replication. The header's r24/96-map description
does not determine the imported map.

The real iteration is `(F(v) >> SHIFT) & (2^w-1)`. SHIFT defaults to zero.
The control takes the low w bits of the first eight SHA-256 bytes, interpreted
little-endian, of a textual per-trial key followed by v encoded in eight
little-endian bytes. SHIFT is not applied to that control. Widths above 64
are not a like-for-like control and eight-byte input encoding can overflow.

Output retains w, K, seedbase and four-decimal fitted c/lo/hi plus sum_t for
each arm. It does not retain SHIFT, individual lengths, chosen map indices,
source hashes or likelihood diagnostics. The sum alone cannot reconstruct
the likelihood. For a new study, retain those raw observations and identities
alongside the historical summary, and explicitly validate the model domain.

## What these checks do not prove

No historical rate study is rerun. No original rho implementation is audited
by these fixtures. A synthetic stand-in tests only run wiring; other cases
execute the exact extracted estimator functions. Reduced-width feedback maps
are not the full-field map. A plausible control and a fitted rate do not prove
the package's fixed-map success premise or its attack cost.
