"""CNF encoder: a pair of n-step SHA-256 computations (message pair, chaining pair) under an nldtool-style
characteristic shape ('-' equal, 'x' differ, '?' free; 'u'/'n' treated as 'x' with a signed note).
Usage: python3 sha_cnf.py instance.xml out.cnf out.map   (n and the <char> rows are read from the xml)
       python3 sha_cnf.py --decode out.map model.txt     (model: DIMACS-style literals) -> prints W1/W2/IV words and checks them
Bit 0 = LSB. Variable 1 is fixed TRUE. Chaining rows -1..-4 are A_{-1..-4} = a,b,c,d and E_{-1..-4} = e,f,g,h.
Width: WBITS=w (default 32) encodes the reduced-width family SHA-256/w (w in {8,12,16,24,32}): words have w bits, every
rotation/shift amount k is scaled to sc(k) = max(1, (k*w + 16)//32) (the team's generator rule), round constants and IV are
truncated to the low w bits. At WBITS=32 the output is byte-identical to the width-free encoder (same variables, same clause
order). <char> rows may be 32 characters (the RIGHTMOST w are used = low bits, leftmost char being bit 31) or exactly w.
The .map records 'wbits' when w != 32 and --decode reads the width from the map (the environment is not needed)."""
import sys, re, json, os
W = int(os.environ.get('WBITS', '32'))               # word width in bits (reduced-width family); 32 = SHA-256 proper
if not 1 <= W <= 32: sys.exit(f"WBITS={W} out of range 1..32")
MASK = (1 << W) - 1
def sc(k, w=None):
    """scaled rotation/shift amount for width w (default: the module width); identity at w=32, never below 1."""
    w = W if w is None else w
    return max(1, (k * w + 16) // 32)
R_S0, R_S1 = tuple(sc(k) for k in (2, 13, 22)), tuple(sc(k) for k in (6, 11, 25))       # Sigma_0, Sigma_1 rotations
R_s0, H_s0, R_s1, H_s1 = tuple(sc(k) for k in (7, 18)), sc(3), tuple(sc(k) for k in (17, 19)), sc(10)   # sigma_0/1 rot + shift
for _nm, _rot, _sh in (('Sigma0', R_S0, 0), ('Sigma1', R_S1, 0), ('sigma0', R_s0, H_s0), ('sigma1', R_s1, H_s1)):
    # two coinciding rotation amounts cancel in the xor (the function degenerates); the team generator refuses such widths (4, 5, 7).
    if len(set(_rot)) < len(_rot) or max(_rot + (_sh,)) >= W:
        print(f"warning: WBITS={W}: {_nm} rotations {_rot} shift {_sh} coincide or reach the width; not a member of the scaled family", file=sys.stderr)
K = [0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2]
IV = [0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19]
# K and IV stay the full 64 / 8 SHA-256 constants; truncation to w bits happens where a word is built (const, sha_ref, decode).

class CNF:
    def __init__(s): s.nv = 1; s.cl = []; s.xcl = []; s.T = 1; s.F = -1
    def var(s): s.nv += 1; return s.nv
    def add(s, *lits): s.cl.append(list(lits))
    def word(s): return [s.var() for _ in range(W)]
    def const(s, v): return [s.T if (v >> i) & 1 else s.F for i in range(W)]     # low W bits of v
    def isc(s, l): return l in (s.T, s.F)
    def xor2(s, a, b):
        if s.isc(a) and s.isc(b): return s.T if (a == s.T) != (b == s.T) else s.F
        if s.isc(a): return b if a == s.F else -b
        if s.isc(b): return a if b == s.F else -a
        o = s.var()
        if XORMODE: s.xcl.append([a, b, -o])          # a xor b xor (not o) = true  <=>  o = a xor b
        else: s.add(-a, -b, -o); s.add(a, b, -o); s.add(a, -b, o); s.add(-a, b, o)
        return o
    def xor3(s, a, b, c):
        if XORMODE and os.environ.get('XOR3', '0') == '1' and not (s.isc(a) or s.isc(b) or s.isc(c)):
            o = s.var(); s.xcl.append([a, b, c, -o]); return o      # one native XOR line: a^b^c^(not o) = true
        return s.xor2(s.xor2(a, b), c)
    def maj(s, a, b, c):
        o = s.var()
        s.add(-a, -b, o); s.add(-a, -c, o); s.add(-b, -c, o); s.add(a, b, -o); s.add(a, c, -o); s.add(b, c, -o); return o
    def ch(s, e, f, g):
        o = s.var()
        s.add(-e, -f, o); s.add(-e, f, -o); s.add(e, -g, o); s.add(e, g, -o); return o
    def eq(s, a, b): s.add(-a, b); s.add(a, -b)
    def neq(s, a, b): s.add(a, b); s.add(-a, -b)
    def add2(s, x, y):
        c = s.F; out = []
        for i in range(W):
            out.append(s.xor3(x[i], y[i], c))
            if i < W - 1: c = s.maj(x[i], y[i], c)
        return out
    def addn(s, ws):
        r = ws[0]
        for w in ws[1:]: r = s.add2(r, w)
        return r

def rotr(w, k): return [w[(i + k) % W] for i in range(W)]
def shr(w, k, F): return [w[i + k] if i + k < W else F for i in range(W)]
def S0(c, w): return [c.xor3(*[x[i] for x in (rotr(w, R_S0[0]), rotr(w, R_S0[1]), rotr(w, R_S0[2]))]) for i in range(W)]
def S1(c, w): return [c.xor3(*[x[i] for x in (rotr(w, R_S1[0]), rotr(w, R_S1[1]), rotr(w, R_S1[2]))]) for i in range(W)]
def s0(c, w): return [c.xor3(*[x[i] for x in (rotr(w, R_s0[0]), rotr(w, R_s0[1]), shr(w, H_s0, c.F))]) for i in range(W)]
def s1(c, w): return [c.xor3(*[x[i] for x in (rotr(w, R_s1[0]), rotr(w, R_s1[1]), shr(w, H_s1, c.F))]) for i in range(W)]

def sha_instance(c, n, chaining):
    """returns dict with W (list of words), A (index t -> word, t from -4), E, and the sigma outputs (for DIFFVARS)."""
    W = [c.word() for _ in range(16)]; SIG = {}
    for t in range(16, max(n, 16) + EXTRAW if n >= 16 else n):
        SIG[('s1', t)] = s1(c, W[t-2]); SIG[('s0', t)] = s0(c, W[t-15])
        W.append(c.addn([SIG[('s1', t)], W[t-7], SIG[('s0', t)], W[t-16]]))
    A = {}; E = {}
    nv_sched_end = c.nv            # variable ids <= this (and > the previous instance's end) belong to the message schedule
    if chaining == 'iv':
        for i in range(4): A[-1-i] = c.const(IV[i]); E[-1-i] = c.const(IV[4+i])
    else:
        for i in range(4): A[-1-i] = c.word(); E[-1-i] = c.word()
    if SCHED_ONLY:
        # schedule-only pre-filter (#143): no step function; state rows are free words so shape/collision rows are trivially satisfiable.
        for t in range(n): A[t] = c.word(); E[t] = c.word()
        return {'W': W, 'A': A, 'E': E, 'SIG': SIG, 'nv_sched_end': nv_sched_end, 'nv_end': c.nv}
    for t in range(n):
        a, b, cc, d = A[t-1], A[t-2], A[t-3], A[t-4]; e, f, g, h = E[t-1], E[t-2], E[t-3], E[t-4]
        SIG[('S1', t)] = S1(c, e); SIG[('S0', t)] = S0(c, a)
        T1 = c.addn([h, SIG[('S1', t)], [c.ch(e[i], f[i], g[i]) for i in range(WB)], c.const(K[t + KOFF]), W[t]])
        T2 = c.add2(SIG[('S0', t)], [c.maj(a[i], b[i], cc[i]) for i in range(WB)])
        A[t] = c.add2(T1, T2); E[t] = c.add2(d, T1)
    return {'W': W, 'A': A, 'E': E, 'SIG': SIG, 'nv_sched_end': nv_sched_end, 'nv_end': c.nv}
WB = W   # alias: inside sha_instance the local name W is the schedule list (as in the original), so the width is read as WB

DIFFVARS = os.environ.get('DIFFVARS', '0') == '1'   # add explicit difference variables and the LINEAR difference relations of sigma/Sigma
def add_diffvars(c, P, Q, n):
    """d-variables for W (all), A, E (t>=-4) and the sigma outputs; plus the exact linear relations d(sigma(x)) = sigma(d(x))
    as XOR constraints (native 'x' lines when XORMODE, else Tseitin)."""
    def dword(X, Y): return [c.xor2(X[i], Y[i]) for i in range(W)]
    dW = {t: dword(P['W'][t], Q['W'][t]) for t in range(len(P['W']))}
    dA = {t: dword(P['A'][t], Q['A'][t]) for t in P['A']}; dE = {t: dword(P['E'][t], Q['E'][t]) for t in P['E']}
    c.dW, c.dA, c.dE = dW, dA, dE          # exposed for the map (difference-structured cube splits)
    def lin(dsig, din, rots, shr=None):
        # dsig[i] = xor over rotations/shift of din: rotr(x,k)[i] = x[(i+k)%W]; shr(x,k)[i] = x[i+k] if i+k<W
        for i in range(W):
            ins = [din[(i + k) % W] for k in rots] + ([din[i + shr]] if (shr is not None and i + shr < W) else [])
            ins = [v for v in ins if not c.isc(v)]
            if not ins: continue
            if XORMODE: c.xcl.append(ins + [-dsig[i]])
            else:
                acc = ins[0]
                for v in ins[1:]: acc = c.xor2(acc, v)
                c.eq(acc, dsig[i])
    for key, out in P['SIG'].items():
        kind, t = key; dout = dword(out, Q['SIG'][key])
        if kind == 's1': lin(dout, dW[t-2], R_s1, H_s1)
        elif kind == 's0': lin(dout, dW[t-15], R_s0, H_s0)
        elif kind == 'S1': lin(dout, dE[t-1], R_S1)
        elif kind == 'S0': lin(dout, dA[t-1], R_S0)
    return dW, dA, dE

def parse_xml(path):
    txt = open(path).read()
    n = int(re.search(r'name="n" value="(\d+)"', txt).group(1))
    rows = {}
    for m in re.finditer(r'^\s*(-?\d+)\s+A:\s*(\S+)\s+E:\s*(\S+)(?:\s+W:\s*(\S+))?', txt, re.M):
        t = int(m.group(1)); rows[t] = (m.group(2), m.group(3), m.group(4))
    return n, rows

import os
BITORDER = os.environ.get('BITORDER', 'msb')     # 'msb': leftmost char = bit 31 (nldtool default assumed); 'lsb': leftmost = bit 0
CHAINREV = os.environ.get('CHAINREV', '0') == '1'  # test hook: reverse the chaining rows (-1 <-> -4, -2 <-> -3)
SIGNED = os.environ.get('SIGNED', '0') == '1'      # u/n as signed value conditions (symmetric under swapping the copies)
KOFF = int(os.environ.get('KOFF', '0'))            # sub-window: step t of the instance uses round constant K[t + KOFF]
EXTRAW = int(os.environ.get('EXTRAW', '0'))        # also expand W up to n+EXTRAW and require those words equal (silent tail)
MODDIFF = os.environ.get('MODDIFF', '')       # "word:+i" / "word:-i": copy 2 of that word = copy 1 +- 2^i (mod 2^W), i < W
SCHED_ONLY = os.environ.get('SCHED_ONLY', '0') == '1'   # #143: message schedule only (no compression-function state)
NEAR_K = os.environ.get('NEAR_K', '')          # SENSOR: at most K differing bits over the last 4 state rows (xml must leave them free)
NEAR_ENC = os.environ.get('NEAR_ENC', 'seq')   # NEAR_K cardinality: 'seq' (sequential counter, default, CNF unchanged) or 'tot' (totalizer, as char_cnf.py)
NEAR_OUTS = os.environ.get('NEAR_OUTS', '0') == '1'  # with NEAR_ENC=tot: keep the root's unary outputs o_1..o_m and list them in the map ('near_tot_outs')
if NEAR_ENC not in ('seq', 'tot'): sys.exit(f"NEAR_ENC={NEAR_ENC}: expected seq (sequential counter) or tot (totalizer)")
REQUIRE_DIFF = os.environ.get('REQUIRE_DIFF', '')  # comma-separated word indices; add ONE clause: at least one of their bits differs
SYMBREAK = os.environ.get('SYMBREAK', '0') == '1'  # swap symmetry of the two copies: at the first differing bit (pattern words, in order) copy 1 holds the 1
XORMODE = os.environ.get('XORMODE', '0') == '1'    # emit xor2 gates as native XOR clauses ('x' lines, CryptoMiniSat) instead of 4 CNF clauses
def apply_shape(c, X, Y, rowstr, signed):
    """rowstr is MSB-first (nldtool prints bit 31 first) unless BITORDER=lsb.
    A row longer than the width W (a 32-char row at reduced width) is cut to its W low-bit characters: the rightmost W in msb
    order, the leftmost W in lsb order. A row of length <= W is used as is (left-aligned from the top bit, as before)."""
    if len(rowstr) > W: rowstr = rowstr[-W:] if BITORDER == 'msb' else rowstr[:W]
    for j, ch in enumerate(rowstr):
        i = (W - 1 - j) if BITORDER == 'msb' else j; a, b = X[i], Y[i]
        if ch == '-': c.eq(a, b)
        elif ch == 'x': c.neq(a, b)
        elif ch in 'un':
            signed.append((ch, i))
            if SIGNED: (c.add(a), c.add(-b)) if ch == 'u' else (c.add(-a), c.add(b))   # u: copy1=1, copy2=0; n: the reverse
            else: c.neq(a, b)
        elif ch == '0': c.add(-a); c.add(-b)
        elif ch == '1': c.add(a); c.add(b)

def totalizer_atmost(lits, K, newvar, add, outs=False):
    """Clauses for sum(lits) <= K over constant-free literals (balanced totalizer, Bailleux-Boufkhad 2003; ported from char_cnf.py).

    Each tree node over m leaves gets unary outputs o[0..m'-1], o[j-1] standing for 'at least j of the leaves below are true'.
    Only the forcing direction is encoded (-a_i | -b_j | o_{i+j}, a_0 = b_0 = true omitted), which is exact for an upper bound.
    outs=False (char_cnf's form): outputs capped at K+1 and the root's o_{K+1} = false is folded into binary clauses -a_i | -b_j;
    K <= 0 and K >= len(lits) are handled directly. Returns [].
    outs=True: outputs are NOT capped, the root is materialised as o_1..o_n (n = len(lits)) and the bound is the single unit
    clause -o_{K+1} (omitted when K >= n). Returns the root list, so an incremental driver can drop the unit and instead
    assume -o_{K'+1} for any K' (descending K without re-encoding). newvar() allocates a fresh variable, add(*lits) emits a clause."""
    n = len(lits)
    if not outs:
        if K < 0: add(); return []
        if K == 0:
            for l in lits: add(-l)
            return []
        if n <= K: return []
    cap = n if outs else K + 1

    def build(lo, hi, root):
        if hi - lo == 1: return [lits[lo]]
        mid = (lo + hi) // 2
        a = build(lo, mid, False); b = build(mid, hi, False)
        if root and not outs:
            for i in range(len(a) + 1):
                j = cap - i
                if 0 <= j <= len(b): add(*([-a[i - 1]] if i else []) + ([-b[j - 1]] if j else []))
            return []
        m = min(hi - lo, cap)
        o = [newvar() for _ in range(m)]
        for i in range(len(a) + 1):
            for j in range(len(b) + 1):
                if 0 < i + j <= m: add(*([-a[i - 1]] if i else []) + ([-b[j - 1]] if j else []) + [o[i + j - 1]])
        return o
    if outs and n == 0: return []
    o = build(0, n, True)
    if outs:
        if K < 0: add()
        elif K < n: add(-o[K])                                  # at most K: o_{K+1} false
    return o

def encode(xml, out_cnf, out_map, chaining='free'):
    n, rows = parse_xml(xml)
    near_tot_outs = None
    c = CNF(); c.add(c.T)
    P = sha_instance(c, n, chaining); Q = sha_instance(c, n, chaining)
    signed = []
    for t, (ra, re_, rw) in rows.items():
        tt = (-5 - t) if (CHAINREV and t < 0) else t
        apply_shape(c, P['A'][tt], Q['A'][tt], ra, signed); apply_shape(c, P['E'][tt], Q['E'][tt], re_, signed)
        if rw is not None and t >= 0 and t < n: apply_shape(c, P['W'][t], Q['W'][t], rw, signed)
    for t in range(n, n + EXTRAW):
        if t < len(P['W']):
            for i in range(W): c.eq(P['W'][t][i], Q['W'][t][i])
    if DIFFVARS: add_diffvars(c, P, Q, n)
    if MODDIFF:
        # modular single-term difference on one schedule word: copy 2 = copy 1 + s*2^i (mod 2^W), e.g. MODDIFF="9:+5" or "9:-5".
        # This is the classic local-collision start (delta = +-2^i in the first word), which may show as several XOR bits.
        w, spec = MODDIFF.split(':'); w = int(w); sign, i = spec[0], int(spec[1:])
        if not 0 <= i < W: sys.exit(f"MODDIFF={MODDIFF}: bit index {i} outside the word width {W}")
        const = (2 ** i) if sign == '+' else ((2 ** W - 2 ** i) & MASK)
        Ssum = c.add2(P['W'][w], c.const(const))
        for b in range(W): c.eq(Ssum[b], Q['W'][w][b])
    if NEAR_K:
        # SENSOR: distance to collision. The xml leaves the last 4 state rows free; require at most K differing bits
        # across A[n-4..n-1] and E[n-4..n-1] (sequential counter). K=0 is the collision instance.
        K = int(NEAR_K); ds = []
        for t in range(n - 4, n):
            for reg in ('A', 'E'):
                for i in range(W):
                    d = c.xor2(P[reg][t][i], Q[reg][t][i])
                    if d == c.T: ds.append(c.T)
                    elif d != c.F: ds.append(d)
        if ds.count(c.T) > K: c.add(c.F)
        elif NEAR_ENC == 'tot':
            ds = [d for d in ds if d != c.T]; K -= 0
            # totalizer (same literal list ds, same K as the sequential counter below); NEAR_OUTS=1 keeps the root outputs
            outs = totalizer_atmost(ds, K, c.var, c.add, outs=NEAR_OUTS)
            if NEAR_OUTS: near_tot_outs = outs
        else:
            ds = [d for d in ds if d != c.T]; K -= 0
            # sequential counter: s[i][j] = at least j+1 of ds[0..i] are true; forbid s[i][K]
            prev = None
            for i, d in enumerate(ds):
                cur = [c.var() for _ in range(K + 1)]
                c.add(-d, cur[0])                                   # d -> s[i][0]
                if prev:
                    for j in range(K + 1):
                        c.add(-prev[j], cur[j])                     # s[i-1][j] -> s[i][j]
                        if j + 1 <= K: c.add(-prev[j], -d, cur[j + 1])   # s[i-1][j] and d -> s[i][j+1]
                c.add(-cur[K])                                      # never K+1 true
                prev = cur
    if REQUIRE_DIFF:
        diffs = []
        for w in [int(x) for x in REQUIRE_DIFF.split(',') if x != '']:
            for i in range(W):
                d = c.xor2(P['W'][w][i], Q['W'][w][i])   # d true iff the two copies differ at this bit
                if d == c.T: diffs = [c.T]; break
                if d != c.F: diffs.append(d)
            if diffs == [c.T]: break
        if diffs == [c.T]: pass                          # trivially satisfiable difference requirement
        elif diffs: c.cl.append(list(diffs))             # at least one differing bit among the pattern words
        else: c.add(c.F)                                 # no free difference possible -> force UNSAT (equal only)
        if SYMBREAK and diffs and diffs != [c.T]:
            # swap symmetry: for the first differing bit (in pattern-word order) copy 1 holds the 1.
            # prefix p_k = "no difference among bits < k"; constraint: (p_k and d_k) -> x1_k
            order = [(w, i) for w in [int(x) for x in REQUIRE_DIFF.split(',') if x != ''] for i in range(W)]
            p = c.T
            for (w, i), d in zip(order, diffs if len(diffs) == len(order) else []):
                x1 = P['W'][w][i]
                c.add(-p, -d, x1)                        # p and d -> x1
                np_ = c.var(); c.add(-np_, p); c.add(-np_, -d); c.add(np_, -p, d)   # np_ = p and not d
                p = np_
    with open(out_cnf, 'w') as f:
        f.write(f"p cnf {c.nv} {len(c.cl) + len(c.xcl)}\n")
        for cl in c.cl: f.write(" ".join(map(str, cl)) + " 0\n")
        for xc in c.xcl: f.write("x " + " ".join(map(str, xc)) + " 0\n")
    mp = {'n': n, 'chaining': chaining, 'W1': P['W'][:16], 'W2': Q['W'][:16],
          'A1': {str(t): P['A'][t] for t in range(-4, 0)}, 'E1': {str(t): P['E'][t] for t in range(-4, 0)},
          'A2': {str(t): Q['A'][t] for t in range(-4, 0)}, 'E2': {str(t): Q['E'][t] for t in range(-4, 0)},
          'A1all': {str(t): P['A'][t] for t in range(-4, n)}, 'E1all': {str(t): P['E'][t] for t in range(-4, n)},
          'A2all': {str(t): Q['A'][t] for t in range(-4, n)}, 'E2all': {str(t): Q['E'][t] for t in range(-4, n)},
          # sigma families for core attribution: schedule-side (s0/s1 at word t) vs state-side (S0/S1 at step t)
          'SIGsched1': {f"{k[0]}_{k[1]}": v for k, v in P['SIG'].items() if k[0] in ('s0', 's1')},
          'SIGstate1': {f"{k[0]}_{k[1]}": v for k, v in P['SIG'].items() if k[0] in ('S0', 'S1')},
          'SIGsched2': {f"{k[0]}_{k[1]}": v for k, v in Q['SIG'].items() if k[0] in ('s0', 's1')},
          'SIGstate2': {f"{k[0]}_{k[1]}": v for k, v in Q['SIG'].items() if k[0] in ('S0', 'S1')},
          # variable-id ranges for exact attribution of auxiliary (adder) variables: copy 1 schedule/state, copy 2 schedule/state
          'ranges': {'sched1': [2, P['nv_sched_end']], 'state1': [P['nv_sched_end'] + 1, P['nv_end']],
                     'sched2': [P['nv_end'] + 1, Q['nv_sched_end']], 'state2': [Q['nv_sched_end'] + 1, Q['nv_end']]}}
    if DIFFVARS and hasattr(c, 'dW'):
        mp['D'] = {str(t): c.dW[t] for t in c.dW}          # per-bit difference variables of every schedule word
        mp['DA'] = {str(t): c.dA[t] for t in c.dA}; mp['DE'] = {str(t): c.dE[t] for t in c.dE}
    if W != 32: mp['wbits'] = W                           # reduced width recorded for --decode; absent at 32 (map unchanged)
    if near_tot_outs is not None: mp['near_tot_outs'] = near_tot_outs   # NEAR_ENC=tot NEAR_OUTS=1: o_j true iff >= j difference bits set
    json.dump(mp, open(out_map, 'w'))
    print(f"n={n} vars={c.nv} clauses={len(c.cl)} shape rows={len(rows)} signed-bits-as-x={len(signed)}" + (f" width={W}" if W != 32 else ""))

def sha_ref(n, chain, Wmsg, width=None):
    """independent Python reference at word width `width` (default: the module width WBITS); K, chain and message truncated to width."""
    w = W if width is None else width; m = (1 << w) - 1          # W here is the module width (the message list is Wmsg)
    rS0, rS1 = [sc(k, w) for k in (2, 13, 22)], [sc(k, w) for k in (6, 11, 25)]
    rs0, hs0, rs1, hs1 = [sc(k, w) for k in (7, 18)], sc(3, w), [sc(k, w) for k in (17, 19)], sc(10, w)
    R = lambda x, k: ((x >> k) | (x << (w - k))) & m
    Wx = [x & m for x in Wmsg]
    for t in range(16, n):
        def _s0(x): return (R(x, rs0[0]) ^ R(x, rs0[1]) ^ (x >> hs0)) & m
        def _s1(x): return (R(x, rs1[0]) ^ R(x, rs1[1]) ^ (x >> hs1)) & m
        Wx.append((_s1(Wx[t-2]) + Wx[t-7] + _s0(Wx[t-15]) + Wx[t-16]) & m)
    a, b, c_, d, e, f, g, h = [x & m for x in chain]
    for t in range(n):
        T1 = (h + (R(e, rS1[0]) ^ R(e, rS1[1]) ^ R(e, rS1[2])) + ((e & f) ^ (~e & g)) + K[t] + Wx[t]) & m
        T2 = ((R(a, rS0[0]) ^ R(a, rS0[1]) ^ R(a, rS0[2])) + ((a & b) ^ (a & c_) ^ (b & c_))) & m
        h, g, f, e, d, c_, b, a = g, f, e, (d + T1) & m, c_, b, a, (T1 + T2) & m
    return (a, b, c_, d, e, f, g, h)

def decode(mapf, modelf):
    mp = json.load(open(mapf)); n = mp['n']; w = mp.get('wbits', 32); m = (1 << w) - 1; hx = (w + 3) // 4   # hex digits per word
    val = {}
    for tok in open(modelf).read().split():
        try: l = int(tok)
        except ValueError: continue
        if l: val[abs(l)] = l > 0
    def wv(bits):
        v = 0
        for i, b in enumerate(bits):
            if b == 1: bit = 1
            elif b == -1: bit = 0
            else: bit = 1 if val.get(abs(b), False) != (b < 0) else 0
            v |= bit << i
        return v
    out = {}
    for k in ('1', '2'):
        W = [wv(w_) for w_ in mp['W' + k]]
        if mp['chaining'] == 'iv': chain = [x & m for x in IV]
        else: chain = [wv(mp['A' + k][str(-1-i)]) for i in range(4)] + [wv(mp['E' + k][str(-1-i)]) for i in range(4)]
        out[k] = (W, chain, sha_ref(n, chain, W, w))
        print(f"M{k}: W=" + " ".join(f"{x:0{hx}x}" for x in W)); print(f"   chain=" + " ".join(f"{x:0{hx}x}" for x in chain))
        print(f"   out=" + " ".join(f"{x:0{hx}x}" for x in out[k][2]))
    print("messages differ:", out['1'][0] != out['2'][0], " outputs equal:", out['1'][2] == out['2'][2])
    print("state XOR diff per register:", " ".join(f"{x ^ y:0{hx}x}" for x, y in zip(out['1'][2], out['2'][2])),
          " chaining XOR diff:", " ".join(f"{x ^ y:0{hx}x}" for x, y in zip(out['1'][1], out['2'][1])))

if __name__ == '__main__':
    if sys.argv[1] == '--decode': decode(sys.argv[2], sys.argv[3])
    else: encode(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else 'free')
