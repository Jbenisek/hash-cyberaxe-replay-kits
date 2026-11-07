#!/usr/bin/env python3
"""schedcnf.py — direct 32-bit message-schedule PAIR encoding for one cell (HASH$CyberAxe 10-31, "find our own").

A cell = (R, D, L): message words D (subset of 0..15) carry a nonzero difference, expanded words L (subset of 16..R-1) carry a
nonzero difference, every other word W0..W(R-1) is equal in the pair. This writes the plain SAT question "do two 16-word messages
exist whose schedules differ exactly on D u L through word R-1" as CNF (two schedules, shared variables on equal message words,
bitwise equality / nonzero on expanded words). No difference model, no sampling: a SAT is a witness pair, an UNSAT is exact.

usage: schedcnf.py R D L OUT.cnf      e.g.  schedcnf.py 39 3,5,6,9,10,11,12,13,14,15 24 c4.cnf
       schedcnf.py --check R D L MODEL   (verify a solver model: recompute both schedules in Python, print the pair)
Var layout: message word i of side s (0/1), bit b -> var 1 + (s*16 + i)*32 + b (side 1 shares side-0 vars when i not in D)."""
import sys, os
SHARE = os.environ.get('SHARE', '1') == '1'   # SHARE=0 reproduces the first (unshared) encoding
DSUB = os.environ.get('DSUB', '0') == '1'      # DSUB=1: message words D are allowed (may be zero); kicks L stay exactly nonzero
LSUB = os.environ.get('LSUB', '0') == '1'      # LSUB=1: kicks L are allowed (may be zero)
HW = int(os.environ['HW']) if os.environ.get('HW') else None   # relax only: total XOR weight of the support words <= HW
HWSET = {int(x) for x in os.environ['HWSET'].split(',')} if os.environ.get('HWSET') else None   # words counted in the weight (default: all support)
WB = int(os.environ.get('WB', '32'))           # word width (reduced-width ladder): rotations/shifts scaled as gen_scaled.py sc()
def sc(n): return max(1, (n * WB + 16) // 32)
M = (1 << WB) - 1
def rotr(x, n): return ((x >> n) | (x << (WB - n))) & M
def s0(x): return rotr(x, sc(7)) ^ rotr(x, sc(18)) ^ (x >> sc(3))
def s1(x): return rotr(x, sc(17)) ^ rotr(x, sc(19)) ^ (x >> sc(10))
def expand(w, R):
    w = list(w)
    for t in range(16, R): w.append((s1(w[t-2]) + w[t-7] + s0(w[t-15]) + w[t-16]) & M)
    return w

class CNF:
    def __init__(s): s.n = 0; s.cl = []; s.T = None
    def v(s): s.n += 1; return s.n
    def word(s): return [s.v() for _ in range(WB)]
    def true(s):
        if s.T is None: s.T = s.v(); s.cl.append([s.T])
        return s.T
    def xor(s, a, b):
        if a == -b: return s.true()
        c = s.v(); s.cl += [[-a, -b, -c], [a, b, -c], [a, -b, c], [-a, b, c]]; return c
    def xor3(s, a, b, c):   # None = constant 0
        xs = [x for x in (a, b, c) if x is not None]
        r = xs[0]
        for x in xs[1:]: r = s.xor(r, x)
        return r
    def add(s, x, y):   # 32-bit modular add, LSB = index 0
        out, c = [], None
        for i in range(WB):
            a, b = x[i], y[i]
            if c is None:
                out.append(s.xor(a, b)); cc = s.v(); s.cl += [[-a, -b, cc], [a, -cc], [b, -cc]]; c = cc
            else:
                z = s.v()
                s.cl += [[-a, -b, -c, z], [-a, b, c, z], [a, -b, c, z], [a, b, -c, z], [a, b, c, -z], [a, -b, -c, -z], [-a, b, -c, -z], [-a, -b, c, -z]]
                out.append(z)
                if i < WB - 1:
                    cc = s.v(); s.cl += [[-a, -b, cc], [-a, -c, cc], [-b, -c, cc], [a, b, -cc], [a, c, -cc], [b, c, -cc]]; c = cc
        return out
    def sig(s, x, r1, r2, sh):   # bit i of rotr(x,r1)^rotr(x,r2)^(x>>sh); 32-bit constants, scaled to WB
        r1, r2, sh = sc(r1), sc(r2), sc(sh)
        return [s.xor3(x[(i + r1) % WB], x[(i + r2) % WB], x[i + sh] if i + sh < WB else None) for i in range(WB)]

def build(R, D, L):
    C = CNF(); W = [[None] * R for _ in range(2)]
    for i in range(16): W[0][i] = C.word()
    for i in range(16): W[1][i] = C.word() if i in D else W[0][i]
    for t in range(16, R):
        for s in range(2):
            if s == 1 and SHARE and all(W[1][t-j] is W[0][t-j] for j in (2, 7, 15, 16)): W[1][t] = W[0][t]; continue   # inputs equal -> word equal
            a = C.add(C.sig(W[s][t-2], 17, 19, 10), W[s][t-7]); a = C.add(a, C.sig(W[s][t-15], 7, 18, 3)); W[s][t] = C.add(a, W[s][t-16])
        if W[1][t] is W[0][t]:
            if t in L and not LSUB: C.cl.append([])   # a kick whose inputs are all equal cannot differ: exact UNSAT by structure
            continue
        if t in L:
            if not LSUB: C.cl.append([C.xor(W[0][t][b], W[1][t][b]) for b in range(WB)])   # kick: nonzero difference (LSUB=1: kick allowed, may be zero)
        else:   # forced equal: bind bitwise, then share the side-0 word downstream (later words with equal inputs need no adders)
            for b in range(WB): C.cl += [[-W[0][t][b], W[1][t][b]], [W[0][t][b], -W[1][t][b]]]
            if SHARE: W[1][t] = W[0][t]
    if not DSUB:
        for t in sorted(D):   # message words in D: nonzero difference (DSUB=1: D is the ALLOWED support, any word may be zero)
            C.cl.append([C.xor(W[0][t][b], W[1][t][b]) for b in range(WB)])
    else: C.cl.append([C.xor(W[0][t][b], W[1][t][b]) for t in sorted(D) for b in range(WB)])   # at least one message difference
    return C, W

def build_relax(R, D, L):
    """RELAXATION (backward-derived): one modular difference equation per schedule step t=16..R-1, written only over the words that
    carry a difference (S = D u L); every equal word cancels out of its step, so its VALUE never enters. Values of the S words are
    left free. Dropping the value links between S words can only add solutions: UNSAT here is an exact UNSAT of the cell.
    A SAT gives (X_j, X'_j) for j in S, which --lift pins into the full pair encoding to get (and verify) a real message pair."""
    C = CNF(); S = sorted(D | L); X = {j: (C.word(), C.word()) for j in S}
    XD = {j: [C.xor(X[j][0][b], X[j][1][b]) for b in range(WB)] for j in S}
    for j in S: C.cl.append(XD[j])   # every support word differs
    if os.environ.get('PINXOR'):   # PINXOR="8:40000000,9:08801000": fix the XOR difference pattern of chosen words (unit clauses, no new vars)
        for item in os.environ['PINXOR'].split(','):
            j, h = item.split(':'); j = int(j); h = int(h, 16)
            if j in XD:
                for b in range(WB): C.cl.append([XD[j][b] if (h >> b) & 1 else -XD[j][b]])
    sig1 = lambda w: C.sig(w, 17, 19, 10); sig0 = lambda w: C.sig(w, 7, 18, 3)
    for t in range(16, R):
        # step t: W[t] - sigma1(W[t-2]) - W[t-7] - sigma0(W[t-15]) - W[t-16] = 0 on both sides; equal words cancel
        lhs = {0: [], 1: []}; rhs = {0: [], 1: []}   # side s: W_t(s') + other terms(s)  ==  W_t(s) + other terms(s')
        terms = [(t, None), (t - 2, sig1), (t - 7, None), (t - 15, sig0), (t - 16, None)]
        present = [(j, f) for j, f in terms if j in X]
        if not present: continue
        if len(present) == 1: C.cl.append([]); continue   # a lone difference in one step cannot cancel: exact UNSAT
        A, B = [], []   # A = W_t' + others ; B = W_t + others'   (moving W_t to the other side)
        for j, f in present:
            v0, v1 = (f(X[j][0]), f(X[j][1])) if f else (X[j][0], X[j][1])
            if j == t: A.append(v1); B.append(v0)
            else: A.append(v0); B.append(v1)
        sa, sb = A[0], B[0]
        for w in A[1:]: sa = C.add(sa, w)
        for w in B[1:]: sb = C.add(sb, w)
        for b in range(WB): C.cl += [[-sa[b], sb[b]], [sa[b], -sb[b]]]
    if HW is not None:   # weight counter LAST (plain-relax var numbering stays a prefix -> a plain-relax model is an exact phase hint)
        bits = [x for j in S if (HWSET is None or j in HWSET) for x in XD[j]]   # Sinz sequential counter over the XOR bits
        K = HW; n = len(bits); s = [[C.v() for _ in range(K)] for _ in range(n)]
        for i in range(n):
            C.cl.append([-bits[i], s[i][0]])
            if i > 0:
                for k in range(K): C.cl.append([-s[i-1][k], s[i][k]])
                for k in range(1, K): C.cl.append([-bits[i], -s[i-1][k-1], s[i][k]])
                if os.environ.get('HWSOFT') != '1': C.cl.append([-bits[i], -s[i-1][K-1]])   # HWSOFT=1: no hard cap, bound only by assumptions
        C.hwinfo = f"hw<={K} over {n} bits"; C.hwout = s[n-1]   # assume -hwout[k] to force weight <= k (k < K)
    return C, X

def main():
    if sys.argv[1] == '--relax':
        R, D, L, out = int(sys.argv[2]), {int(x) for x in sys.argv[3].split(',') if x}, {int(x) for x in sys.argv[4].split(',') if x}, sys.argv[5]
        C, _ = build_relax(R, D, L)
        with open(out, 'w') as f:
            f.write(f"p cnf {C.n} {len(C.cl)}\n")
            for c in C.cl: f.write(' '.join(map(str, c)) + ' 0\n')
        print(f"{out}: RELAX R={R} D={sorted(D)} L={sorted(L)} vars={C.n} clauses={len(C.cl)}"); return
    if sys.argv[1] == '--lift':   # --lift R D L RELAX_MODEL OUT.cnf : full pair encoding with the support-word values pinned
        R, D, L = int(sys.argv[2]), {int(x) for x in sys.argv[3].split(',') if x}, {int(x) for x in sys.argv[4].split(',') if x}
        Cr, X = build_relax(R, D, L); val = {}
        for l in open(sys.argv[5]):
            if l.startswith('v'):
                for x in l.split()[1:]:
                    x = int(x)
                    if x: val[abs(x)] = x > 0
        C, W = build(R, D, L)
        for j in X:
            for s in range(2):
                for b in range(WB):
                    v = W[s][j][b]; C.cl.append([v if val.get(X[j][s][b], False) else -v])
        with open(sys.argv[6], 'w') as f:
            f.write(f"p cnf {C.n} {len(C.cl)}\n")
            for c in C.cl: f.write(' '.join(map(str, c)) + ' 0\n')
        print("lift:", ' '.join(f"W{j}=({sum((1<<b) for b in range(WB) if val.get(X[j][0][b], False)):08x},{sum((1<<b) for b in range(WB) if val.get(X[j][1][b], False)):08x})" for j in X)); return
    if sys.argv[1] == '--check':
        R, D, L = int(sys.argv[2]), {int(x) for x in sys.argv[3].split(',') if x}, {int(x) for x in sys.argv[4].split(',') if x}
        C, W = build(R, D, L); val = {}
        for l in open(sys.argv[5]):
            if l.startswith('v'):
                for x in l.split()[1:]:
                    x = int(x)
                    if x: val[abs(x)] = x > 0
        m = [[sum((1 << b) for b in range(WB) if val.get(W[s][i][b], False)) for i in range(16)] for s in range(2)]
        e = [expand(m[s], R) for s in range(2)]
        sup = [t for t in range(R) if e[0][t] != e[1][t]]
        want = sorted(D | L)
        print("M1", ' '.join(f"{x:08x}" for x in m[0])); print("M2", ' '.join(f"{x:08x}" for x in m[1]))
        print("difference support through word", R - 1, ":", sup, "| wanted", want, "->", "VERIFIED" if sup == want else "MISMATCH")
        return
    R, D, L, out = int(sys.argv[1]), {int(x) for x in sys.argv[2].split(',') if x}, {int(x) for x in sys.argv[3].split(',') if x}, sys.argv[4]
    C, _ = build(R, D, L)
    with open(out, 'w') as f:
        f.write(f"p cnf {C.n} {len(C.cl)}\n")
        for c in C.cl: f.write(' '.join(map(str, c)) + ' 0\n')
    print(f"{out}: R={R} D={sorted(D)} L={sorted(L)} vars={C.n} clauses={len(C.cl)}")

if __name__ == '__main__': main()
