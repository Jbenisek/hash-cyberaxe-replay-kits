#!/usr/bin/env python3
"""backscore.py (HASH$CyberAxe 2026-10-30: 10x the backward walk into a usable score). Pure arithmetic, no solver.
For every pair (M1, M2) and a target step count R: walk back from a clean end (all 8 words equal after R steps) with the pair's
modular message-word differences. Each step whose mixing inputs (A/E of the three newer rows) are all clean is EXACT and fixes the
modular difference the two oldest words must carry. The walk stops at the first step where a nonzero difference enters a mixing
function: from there it depends on values (the knot).
Score per (pair, R):
  depth   = exact steps walked back from the end before the knot (more = longer computed tail)
  knot    = first row of the knot
  demand  = signed-digit (NAF) weight of all nonzero differences the exact steps demand (fewer = cheaper to produce)
  score   = demand + 2 * max(0, 8 - depth)   (bits; lower is better; a knot right at the end costs extra)
Inputs: pair files (lines 'M1 <16 hex>', 'M2 <16 hex>', R from the name 'R<nn>_' or a '# ... R=nn' header) and LIT_PAIRS.jsonl.
Writes BACKSCORE.tsv: source, R_own, R_target, depth, knot, demand, score."""
import sys, os, re, json, glob
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import indep_sha256_check as H
M = 0xffffffff

def naf_weight(x):
    x &= M
    if x >= 1 << 31: x -= 1 << 32
    w = 0
    while x:
        if x & 1: w += 1; x -= 2 - (x & 3)
        x >>= 1
    return w

def walk(dW, R):
    dA, dE = {}, {}
    for r in range(R - 4, R): dA[r] = 0; dE[r] = 0
    depth, demand = 0, 0
    for t in range(R - 1, -1, -1):
        ins = [dA.get(t - 1), dA.get(t - 2), dA.get(t - 3), dE.get(t - 1), dE.get(t - 2), dE.get(t - 3)]
        if any(v is None for v in ins) or any(v != 0 for v in ins): return depth, t, demand
        dT1 = dA[t]; dh = (dT1 - dW[t]) & M; dd = (dE[t] - dT1) & M
        dE[t - 4] = dh; dA[t - 4] = dd; depth += 1; demand += naf_weight(dh) + naf_weight(dd)
    return depth, -1, demand

def pairs():
    W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
    for f in glob.glob(os.path.join(W, 'game/climber/guided/newdoor_1029/owner_r42/game_1030/*.pair.txt')) + \
             glob.glob(os.path.join(W, 'runs_1030/close48/*.pair')) + glob.glob(os.path.join(W, 'runs_1030/close2/*.pair')):
        txt = open(f).read(); L = {l.split()[0]: l.split()[1:] for l in txt.split('\n') if l[:2] in ('M1', 'M2')}
        m = re.search(r'R=(\d+)', txt) or re.search(r'R(\d+)_', os.path.basename(f))
        if 'M1' in L and 'M2' in L and m and len(L['M1']) == 16: yield os.path.basename(f), int(m.group(1)), L['M1'], L['M2']
    for l in open(os.path.join(W, 'game/climber/guided/d6full_head/sat5/up39/LIT_PAIRS.jsonl')):
        r = json.loads(l); yield 'LIT_' + r['key'], int(r['h']), r['M1'], r['M2']

rows = []
for name, R, m1, m2 in pairs():
    X1, X2 = H.expand([int(x, 16) for x in m1], 64), H.expand([int(x, 16) for x in m2], 64)
    dW = [(X1[t] - X2[t]) & M for t in range(64)]
    for Rt in (R, R + 1):
        depth, knot, demand = walk(dW, Rt)
        rows.append((name, R, Rt, depth, knot, demand, demand + 2 * max(0, 8 - depth)))
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'BACKSCORE.tsv')
with open(out, 'w') as f:
    f.write('source\tR_own\tR_target\tdepth\tknot\tdemand\tscore\n')
    for r in sorted(rows, key=lambda r: (r[6], -r[3])): f.write('\t'.join(map(str, r)) + '\n')
print('pairs scored:', len({r[0] for r in rows}), ' rows:', len(rows), '->', out)
for tgt in ('own', 'step-up'):
    sel = [r for r in rows if (r[2] == r[1]) == (tgt == 'own')]
    sel.sort(key=lambda r: (r[6], -r[3]))
    print('\n== target: %s length (best 8 by score)' % tgt)
    for r in sel[:8]: print('  score %3d  depth %2d  knot row %3d  demand %3d  R%d->%d  %s' % (r[6], r[3], r[4], r[5], r[1], r[2], r[0][:60]))
