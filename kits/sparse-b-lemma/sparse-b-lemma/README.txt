Sparse B: finite controls for a lossless top-bit implication

Python 3.9+ standard library. Run:
  python -I -B replay.py

This is a tiny arithmetic demonstration, not a schedule or collision search.
Expected: 8190 root residues checked over widths 1..12, 1024 local recurrence
controls over widths 1..32, both orientations at each width. No actual message
schedule is constructed. No compression collision or price is checked.

The complete proof is in PROOF.txt. theorem.json records its exact support and
limits. manifest.json binds every included file; replay.py also checks the
theorem against its built-in assumptions. Do not run with optimized -O Python.
It uses B's EXACT support, including nonzero difference at input word 13:
  input words: 8,9,10,11,13,15
  expanded differing rows: 16,20,25,28,29
All other words through W39 agree. For d_t = W_t(B)-W_t(A) modulo 2^w,
the true schedule recurrence gives d20=d13, d29=d13 and d36=d20+d29=0.
Thus 2*d13=0. Since d13 is nonzero, it is exactly 2^(w-1). The XOR differences
of W13,W20,W29 are therefore the top bit alone. Its u/n orientation is not fixed.

The controls exercise the local common-addend equations, not the existence of
a complete schedule satisfying all support conditions. Keeping that distinction
is essential. If the input support is only allowed and W13 may agree, the zero
root remains and the nonzero conclusion cannot be imposed unconditionally.

Credit: sparse B and its top-bit observation were reported by HASH$CyberAxe. This
audit spells out the recurrence proof, assumptions, sign boundary and finite
controls. No novelty claim or valid full-width characteristic is implied.
