Scaled sigma assumptions: a finite encoder audit

Requirements: Python 3.9+ standard library. Extract the archive, enter
scaled-sigma-audit and run:
  python -I -B replay.py
To emit the complete rank/kernel and counterexample projection:
  python -I -B replay.py --emit-projection

Expected: 64 width/sigma rank calculations, 1184 scalar controls,
30 singular width/sigma cases and 30 exact one-step schedule counterexamples.
Both 32-bit small-sigma maps have rank 32. Widths 6 and 24 are also full rank
for both maps in this scaling. No SAT solver or research campaign is launched.

The exact original source is in original/schedcnf3.py, SHA-256:
89083bdf81f33c236d94f4b253218789ac6a147cf700de7b643a8601b58b293f
It is retained as evidence, not a repaired tool. Do not run its module directly
for this demonstration. replay.py extracts only named definitions using AST;
the original module top level and its CNF-writing branches are never executed.
Only fixed-input in-memory circuits and the small --check branch are exercised.
One deliberately incomplete model is created in a disposable temporary folder.

What is proved

The source scales each rotation/shift n to max(1, floor((n*w+16)/32)). Its
sigma0 and sigma1 maps remain GF(2)-linear, but are not always injective at
widths below 32. The replay constructs the exact basis matrix, computes its
rank and a nonzero kernel element whenever rank<w, and compares the source's
scalar function against an independent rotation/shift implementation.

For every singular map it constructs an actual R17 expanded-message pair:
M1 is all zero; M2 has only W1 (sigma0 case) or W14 (sigma1 case) set to the
kernel element. W16 agrees, so the exact support through W16 is that one input
word. A complete fixed-input assignment satisfies every base full-encoder
clause. Adding its nonzero-image lemma produces a unit-propagation conflict,
with LIN both disabled and enabled. The relaxed encoder separately inserts
an empty clause for that same feasible cell. Thus LEMMA=0 alone does not repair
the relaxed-encoder shortcut at singular widths.

Concrete eight-bit example

sigma1(x) = ROR4(x) XOR ROR5(x) XOR (x>>3).
For x=de: ROR4=ed, ROR5=f6, SHR3=1b, and ed XOR f6 XOR 1b = 0.
Set only M2[14]=de. Both expanded W16 words are zero although W14 differs.
This is a schedule pair, NOT a compression collision or an attack.

What remains separate

The linear image-difference identity is valid even when the map is singular.
Injectivity is the extra assumption behind the false inverse/nonzero rule.
The standalone checker also shows that --check prints MISMATCH and returns
normally for the deliberately incomplete model. A zero CLI exit status on
normal return is derived; the original CLI was not separately subprocess-run.
Require the actual VERIFIED result and independent pair/support checking,
not just an exit-status-only wrapper. No historical wrapper is accused here.

This does not invalidate 32-bit sigma injectivity, certify the whole encoder,
reclassify historical UNSATs or settle any 40-step family. Each historical
result needs its own source/options/width identity. The width-6 lifting
failures and verified width-24 schedules are not explained away by this issue.
No production encoder is changed by this kit. No repaired version is certified.

Files: the exact original, replay.py, this README, records.json and manifest.json.
Original bytes are additionally hard-pinned in replay.py; rehashing the manifest
cannot silently substitute a different source edition. Optimized -O execution
is rejected. records.json is an exact reconstructed projection, not a proof
payload from a historical solver run.

Credit: the HASH$CyberAxe team's schedule encoder and Hensel's lemma extension. The publication
audit adds the all-width rank calculation, explicit local counterexamples,
checker-contract control and portable replay. No novelty or collision claim.
