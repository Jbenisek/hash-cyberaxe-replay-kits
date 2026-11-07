#!/usr/bin/env python3
"""backwalk.py PAIRFILE R (HASH$CyberAxe 2026-10-30: compute what the tail demands, do not sample it).
Start from a clean end (all 8 state words equal after R steps) and walk the step function backward with the cell's
message-word differences (modular, from the pair's expansion). At each step backward, the two oldest words (d = A_{t-4},
h = E_{t-4}) leave the window; their required modular difference follows exactly when every word feeding Sigma0, Sigma1,
Ch and Maj at that step has zero difference:  dT1 must cancel, so dh = -(dW_t) - (other dT1 terms), dd = -dT1 ... .
The walk prints, step by step, whether the demand is EXACT (all mixing inputs clean) or VALUE-DEPENDENT (a nonzero
difference enters a mixing function) and stops being exact there: that row is the knot that needs the time profile.
PAIRFILE lines 'M1 <16 hex>', 'M2 <16 hex>' (no chaining value needed: the walk is in differences)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import indep_sha256_check as H
M = 0xffffffff
L = {l.split()[0]: [int(x, 16) for x in l.split()[1:]] for l in open(sys.argv[1]) if l[:2] in ('M1', 'M2')}
R = int(sys.argv[2])
X1, X2 = H.expand(L['M1'], 64), H.expand(L['M2'], 64)
dW = [(X1[t] - X2[t]) & M for t in range(64)]
# window after step t: A[t], A[t-1], A[t-2], A[t-3], E[t], E[t-1], E[t-2], E[t-3]; differences kept by row index
dA, dE = {}, {}
for r in range(R - 4, R): dA[r] = 0; dE[r] = 0          # clean end: the 8 words after R steps (rows R-4..R-1)
print('backward from a clean end after %d steps (rows %d..%d all zero difference)' % (R, R - 4, R - 1))
exact = True
for t in range(R - 1, -1, -1):                          # step t computed row t from rows t-1..t-4 and W[t]
    mix_inputs = {'A%d' % (t - 1): dA.get(t - 1), 'A%d' % (t - 2): dA.get(t - 2), 'A%d' % (t - 3): dA.get(t - 3),
                  'E%d' % (t - 1): dE.get(t - 1), 'E%d' % (t - 2): dE.get(t - 2), 'E%d' % (t - 3): dE.get(t - 3)}
    known = all(v is not None for v in mix_inputs.values())
    clean_mix = known and all(v == 0 for v in mix_inputs.values())
    if not clean_mix:
        dirty = [k for k, v in mix_inputs.items() if v not in (0, None)]
        print('step %2d: VALUE-DEPENDENT from here (mixing inputs with a difference: %s; unknown: %s) -> the knot starts at rows %d..%d'
              % (t, dirty or '-', [k for k, v in mix_inputs.items() if v is None] or '-', max(t - 4, 0), t))
        exact = False
        break
    # all mixing inputs clean: dT2 = 0; dA[t] = dT1 + dT2 = dT1 ; dE[t] = dd + dT1 ; dT1 = dh + dW[t]
    dT1 = (dA[t]) & M                                    # since dT2 = 0, dA[t] = dT1
    dh = (dT1 - dW[t]) & M                              # dT1 = dh + dW  ->  dh = dT1 - dW
    dd = (dE[t] - dT1) & M                              # dE[t] = dd + dT1 -> dd = dE[t] - dT1
    dE[t - 4] = dh; dA[t - 4] = dd
    print('step %2d: EXACT  dW=%08x  -> row %2d demands  dA=%08x  dE=%08x' % (t, dW[t], t - 4, dd, dh))
if exact: print('walk stayed exact to row 0')
