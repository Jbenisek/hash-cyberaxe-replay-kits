"""CNF encoder: a pair of n-step SHA-256 computations (message pair, chaining pair) under an nldtool-style
characteristic shape ('-' equal, 'x' differ, '?' free; 'u'/'n' treated as 'x' with a signed note).
Usage: python3 sha_cnf.py instance.xml out.cnf out.map   (n and the <char> rows are read from the xml)
       python3 sha_cnf.py --decode out.map model.txt     (model: DIMACS-style literals) -> prints W1/W2/IV words and checks them
Bit 0 = LSB. Variable 1 is fixed TRUE. Chaining rows -1..-4 are A_{-1..-4} = a,b,c,d and E_{-1..-4} = e,f,g,h."""
import sys, re, json, os
MASK = 0xFFFFFFFF
K = [0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2]
IV = [0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19]

class CNF:
    def __init__(s): s.nv = 1; s.cl = []; s.xcl = []; s.T = 1; s.F = -1; s.gates = []; s.eqpairs = []; s.guard = 0   # gates/eqpairs: for EQLINK; guard: row selector (ROW_SELECTORS)
    def var(s): s.nv += 1; return s.nv
    def add(s, *lits): s.cl.append(list(lits) + ([-s.guard] if s.guard else []))   # guarded clause: only active when the selector is assumed
    def word(s): return [s.var() for _ in range(32)]
    def const(s, v): return [s.T if (v >> i) & 1 else s.F for i in range(32)]
    def isc(s, l): return l in (s.T, s.F)
    def xor2(s, a, b):
        if s.isc(a) and s.isc(b): return s.T if (a == s.T) != (b == s.T) else s.F
        if s.isc(a): return b if a == s.F else -b
        if s.isc(b): return a if b == s.F else -a
        o = s.var()
        if XORMODE: s.xcl.append([a, b, -o])          # a xor b xor (not o) = true  <=>  o = a xor b
        else: s.add(-a, -b, -o); s.add(a, b, -o); s.add(a, -b, o); s.add(-a, b, o)
        s.gates.append(((a, b), o))
        return o
    def xor3(s, a, b, c):
        if XORMODE and os.environ.get('XOR3', '0') == '1' and not (s.isc(a) or s.isc(b) or s.isc(c)):
            o = s.var(); s.xcl.append([a, b, c, -o]); return o      # one native XOR line: a^b^c^(not o) = true
        return s.xor2(s.xor2(a, b), c)
    def maj(s, a, b, c):
        o = s.var()
        s.add(-a, -b, o); s.add(-a, -c, o); s.add(-b, -c, o); s.add(a, b, -o); s.add(a, c, -o); s.add(b, c, -o); s.gates.append(((a, b, c), o)); return o
    def ch(s, e, f, g):
        o = s.var()
        s.add(-e, -f, o); s.add(-e, f, -o); s.add(e, -g, o); s.add(e, g, -o); s.gates.append(((e, f, g), o)); return o
    def eq(s, a, b): s.add(-a, b); s.add(a, -b)
    def neq(s, a, b): s.add(a, b); s.add(-a, -b)
    def add2(s, x, y):
        c = s.F; out = []
        for i in range(32):
            out.append(s.xor3(x[i], y[i], c))
            if i < 31: c = s.maj(x[i], y[i], c)
        return out
    def addn(s, ws):
        r = ws[0]
        for w in ws[1:]: r = s.add2(r, w)
        return r

def rotr(w, k): return [w[(i + k) % 32] for i in range(32)]
def shr(w, k, F): return [w[i + k] if i + k < 32 else F for i in range(32)]
def S0(c, w): return [c.xor3(*[x[i] for x in (rotr(w, 2), rotr(w, 13), rotr(w, 22))]) for i in range(32)]
def S1(c, w): return [c.xor3(*[x[i] for x in (rotr(w, 6), rotr(w, 11), rotr(w, 25))]) for i in range(32)]
def s0(c, w): return [c.xor3(*[x[i] for x in (rotr(w, 7), rotr(w, 18), shr(w, 3, c.F))]) for i in range(32)]
def s1(c, w): return [c.xor3(*[x[i] for x in (rotr(w, 17), rotr(w, 19), shr(w, 10, c.F))]) for i in range(32)]

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
        T1 = c.addn([h, SIG[('S1', t)], [c.ch(e[i], f[i], g[i]) for i in range(32)], c.const(K[t + KOFF]), W[t]])
        T2 = c.add2(SIG[('S0', t)], [c.maj(a[i], b[i], cc[i]) for i in range(32)])
        A[t] = c.add2(T1, T2); E[t] = c.add2(d, T1)
    return {'W': W, 'A': A, 'E': E, 'SIG': SIG, 'nv_sched_end': nv_sched_end, 'nv_end': c.nv}

EQLINK = os.environ.get('EQLINK', '0') == '1'     # 10-31: equality propagation across the two copies (see eqlink)
def eqlink(c, nP, P, Q):
    """EQLINK (10-31 18:25): the two copies are independent circuits linked only by equality clauses on pinned bits, so unit
    propagation cannot derive "equal inputs => equal gate output" (a trivially-UNSAT instance - all message words equal, a
    difference demanded in an expanded word - HELD 120 s in both SIGNED and DIFFVARS encodings). Fix: for every gate pair
    (k-th gate of copy 1, k-th gate of copy 2) an equality variable e = (o1 <-> o2) and the clause (all inputs equal) -> (output
    equal); seeds: e = true for every '-'/'0'/'1' pinned pair; d-variables of cross gates (REQUIRE_DIFF/DIFFVARS) tied as d = not e."""
    E = {}
    def epair(v1, v2):
        if c.isc(v1) and c.isc(v2): return c.T if v1 == v2 else c.F
        key = (v1, v2)
        if key in E: return E[key]
        e = c.var(); c.add(-e, -v1, v2); c.add(-e, v1, -v2); c.add(e, v1, v2); c.add(e, -v1, -v2); E[key] = e; return e
    for (a, b) in c.eqpairs: e = epair(a, b); c.add(e)
    for k in range(nP):
        (inP, oP), (inQ, oQ) = c.gates[k], c.gates[nP + k]
        es = [epair(x, y) for x, y in zip(inP, inQ)]
        if any(e == c.F for e in es): continue
        eo = epair(oP, oQ); c.add(*([-e for e in es if e != c.T] + [eo]))
    # cross gates: d = xor2(p, q) built for REQUIRE_DIFF / DIFFVARS -> d = not e(p, q)
    for (ins, o) in c.gates[2 * nP:]:
        if len(ins) == 2 and (ins[0], ins[1]) in E: e = E[(ins[0], ins[1])]; c.add(e, o); c.add(-e, -o)
    return len(E)
DIFFVARS = os.environ.get('DIFFVARS', '0') == '1'   # add explicit difference variables and the LINEAR difference relations of sigma/Sigma
def add_diffvars(c, P, Q, n):
    """d-variables for W (all), A, E (t>=-4) and the sigma outputs; plus the exact linear relations d(sigma(x)) = sigma(d(x))
    as XOR constraints (native 'x' lines when XORMODE, else Tseitin)."""
    def dword(X, Y): return [c.xor2(X[i], Y[i]) for i in range(32)]
    dW = {t: dword(P['W'][t], Q['W'][t]) for t in range(len(P['W']))}
    dA = {t: dword(P['A'][t], Q['A'][t]) for t in P['A']}; dE = {t: dword(P['E'][t], Q['E'][t]) for t in P['E']}
    c.dW, c.dA, c.dE = dW, dA, dE          # exposed for the map (difference-structured cube splits)
    def lin(dsig, din, rots, shr=None):
        # dsig[i] = xor over rotations/shift of din: rotr(x,k)[i] = x[(i+k)%32]; shr(x,k)[i] = x[i+k] if i+k<32
        for i in range(32):
            ins = [din[(i + k) % 32] for k in rots] + ([din[i + shr]] if (shr is not None and i + shr < 32) else [])
            ins = [v for v in ins if not c.isc(v)]
            if not ins: continue
            if XORMODE: c.xcl.append(ins + [-dsig[i]])
            else:
                acc = ins[0]
                for v in ins[1:]: acc = c.xor2(acc, v)
                c.eq(acc, dsig[i])
    for key, out in P['SIG'].items():
        kind, t = key; dout = dword(out, Q['SIG'][key])
        if kind == 's1': lin(dout, dW[t-2], (17, 19), 10)
        elif kind == 's0': lin(dout, dW[t-15], (7, 18), 3)
        elif kind == 'S1': lin(dout, dE[t-1], (6, 11, 25))
        elif kind == 'S0': lin(dout, dA[t-1], (2, 13, 22))
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
ROW_SELECTORS = os.environ.get('ROW_SELECTORS', '0') == '1'   # IV scanner v2: guard each row's conditions (rows >= SEL_FROM) with a selector var
SEL_FROM = int(os.environ.get('SEL_FROM', '18'))
SEL_GRAN = os.environ.get('SEL_GRAN', 'row')             # 'row' = one selector per row; 'reg' = one per (row, A/E/W) — which half blocks?
PREHEAD_K = os.environ.get('PREHEAD_K', '')       # at most K differing A/E bits over rows PREHEAD_ROWS (sparse-head ladder; ported from /root/kepler_tools 10-30)
PREHEAD_ROWS = os.environ.get('PREHEAD_ROWS', '0-8')
MODDIFF = os.environ.get('MODDIFF', '')       # "word:+i" / "word:-i": copy 2 of that word = copy 1 +- 2^i (mod 2^32)
SCHED_ONLY = os.environ.get('SCHED_ONLY', '0') == '1'   # #143: message schedule only (no compression-function state)
NEAR_K = os.environ.get('NEAR_K', '')          # SENSOR: at most K differing bits over the last 4 state rows (xml must leave them free)
REQUIRE_DIFF = os.environ.get('REQUIRE_DIFF', '')  # comma-separated word indices; add ONE clause: at least one of their bits differs
SYMBREAK = os.environ.get('SYMBREAK', '0') == '1'  # swap symmetry of the two copies: at the first differing bit (pattern words, in order) copy 1 holds the 1
XORMODE = os.environ.get('XORMODE', '0') == '1'    # emit xor2 gates as native XOR clauses ('x' lines, CryptoMiniSat) instead of 4 CNF clauses
def apply_shape(c, X, Y, rowstr, signed):
    """rowstr is MSB-first (nldtool prints bit 31 first) unless BITORDER=lsb."""
    for j, ch in enumerate(rowstr):
        i = (31 - j) if BITORDER == 'msb' else j; a, b = X[i], Y[i]
        if ch == '-': c.eq(a, b); c.eqpairs.append((a, b))          # EQLINK seeds: known-equal pairs
        elif ch == 'x': c.neq(a, b)
        elif ch in 'un':
            signed.append((ch, i))
            if SIGNED: (c.add(a), c.add(-b)) if ch == 'u' else (c.add(-a), c.add(b))   # u: copy1=1, copy2=0; n: the reverse
            else: c.neq(a, b)
        elif ch == '0': c.add(-a); c.add(-b); c.eqpairs.append((a, b))
        elif ch == '1': c.add(a); c.add(b); c.eqpairs.append((a, b))

def encode(xml, out_cnf, out_map, chaining='free'):
    n, rows = parse_xml(xml)
    c = CNF(); c.add(c.T)
    P = sha_instance(c, n, chaining); nP_gates = len(c.gates); Q = sha_instance(c, n, chaining)
    signed = []; selectors = {}
    for t, (ra, re_, rw) in rows.items():
        tt = (-5 - t) if (CHAINREV and t < 0) else t
        if ROW_SELECTORS and t >= SEL_FROM:
            # IV scanner v2 (10-30): every condition clause of row t gets the guard literal -s_t; a probe assumes s_18..s_k to ask
            # "rows 0..k conform" on ONE live solver (incsolve), keeping learned clauses across the rungs of the ladder.
            # SEL_GRAN=reg (10-31): one selector per (row, register A/E/W) instead, so a probe can ask which half of a row blocks.
            if SEL_GRAN == 'bit':
                # SEL_GRAN=bit (10-31 round 10): one selector per CONDITION (row, register, bit) so a probe can add row-t conditions one
                # at a time and find which single conditions refuse from the IV. Names "tA<i>", "tE<i>", "tW<i>" (i = bit index, 0 = lsb).
                for reg, rs, X, Y in (('A', ra, P['A'][tt], Q['A'][tt]), ('E', re_, P['E'][tt], Q['E'][tt])) + ((('W', rw, P['W'][t], Q['W'][t]),) if (rw is not None and 0 <= t < n) else ()):
                    for i, ch in enumerate(reversed(rs)):          # rs is msb-first; i is the bit index
                        if ch == '?': continue
                        one = ['?'] * 32; one[31 - i] = ch
                        selectors[f"{t}{reg}{i}"] = c.var(); c.guard = selectors[f"{t}{reg}{i}"]; apply_shape(c, X, Y, ''.join(one), signed)
                c.guard = 0; continue
            if SEL_GRAN == 'reg':
                selectors[f"{t}A"] = c.var(); c.guard = selectors[f"{t}A"]; apply_shape(c, P['A'][tt], Q['A'][tt], ra, signed)
                selectors[f"{t}E"] = c.var(); c.guard = selectors[f"{t}E"]; apply_shape(c, P['E'][tt], Q['E'][tt], re_, signed)
                if rw is not None and t >= 0 and t < n: selectors[f"{t}W"] = c.var(); c.guard = selectors[f"{t}W"]; apply_shape(c, P['W'][t], Q['W'][t], rw, signed)
                c.guard = 0; continue
            selectors[t] = c.var(); c.guard = selectors[t]
        apply_shape(c, P['A'][tt], Q['A'][tt], ra, signed); apply_shape(c, P['E'][tt], Q['E'][tt], re_, signed)
        if rw is not None and t >= 0 and t < n: apply_shape(c, P['W'][t], Q['W'][t], rw, signed)
        c.guard = 0
    for t in range(n, n + EXTRAW):
        if t < len(P['W']):
            for i in range(32): c.eq(P['W'][t][i], Q['W'][t][i])
    if DIFFVARS: add_diffvars(c, P, Q, n)
    if MODDIFF:
        # modular differences on schedule words: copy 2 = copy 1 + delta (mod 2^32). Comma list "w:+i" / "w:-i" (power of two) or
        # "w:HEX" (any 32-bit constant), e.g. MODDIFF="9:40000000,10:f7801000,11:c0000000,12:0601dcd4,13:ffefe800" = the published
        # 39 differential slid up one word (10-31: the family is MODULAR; XOR patterns were the wrong object).
        for item in MODDIFF.split(','):
            w, spec = item.split(':'); w = int(w)
            if spec[0] in '+-' and spec[1:].isdigit(): i = int(spec[1:]); const = (2 ** i) if spec[0] == '+' else ((2 ** 32 - 2 ** i) & 0xffffffff)
            else: const = int(spec, 16) & 0xffffffff
            Ssum = c.add2(P['W'][w], c.const(const))
            for b in range(32): c.eq(Ssum[b], Q['W'][w][b])
    for env, copy in (('PIN1', P), ('PIN2', Q)):
        # asymmetric value pins: PIN1="w:HEX,..." fixes schedule word w of copy 1 only (PIN2: copy 2). Lets a known pair be pinned
        # fully on one side while MODDIFF carries the difference (encoding controls; 10-30).
        for item in filter(None, os.environ.get(env, '').split(',')):
            w, hx = item.split(':'); w = int(w); v = int(hx, 16)
            for b in range(32): c.add(copy['W'][w][b] if (v >> b) & 1 else -copy['W'][w][b])
    if PREHEAD_K:
        # SPARSE HEAD (10-30): at most K differing state bits across A/E rows PREHEAD_ROWS (a-b inclusive); forced differences
        # ('u'/'n'/'x' rows) count against K. Ladder in K: the first SAT rung is the sparsest real head; UNSAT at K is a proven floor.
        K = int(PREHEAD_K); lo, hi = (int(x) for x in PREHEAD_ROWS.split('-')); ds = []
        for t in range(lo, hi + 1):
            for reg in ('A', 'E'):
                for i in range(32):
                    d = c.xor2(P[reg][t][i], Q[reg][t][i])
                    if d != c.F: ds.append(d)
        forced = ds.count(c.T); ds = [d for d in ds if d != c.T]; K -= forced
        if K < 0: c.add(c.F)
        else:
            prev = None
            for i, d in enumerate(ds):
                cur = [c.var() for _ in range(K + 1)]
                c.add(-d, cur[0])
                if prev:
                    for j in range(K + 1):
                        c.add(-prev[j], cur[j])
                        if j + 1 <= K: c.add(-prev[j], -d, cur[j + 1])
                c.add(-cur[K])
                prev = cur
    if NEAR_K:
        # SENSOR: distance to collision. The xml leaves the last 4 state rows free; require at most K differing bits
        # across A[n-4..n-1] and E[n-4..n-1] (sequential counter). K=0 is the collision instance.
        K = int(NEAR_K); ds = []
        for t in range(n - 4, n):
            for reg in ('A', 'E'):
                for i in range(32):
                    d = c.xor2(P[reg][t][i], Q[reg][t][i])
                    if d == c.T: ds.append(c.T)
                    elif d != c.F: ds.append(d)
        if ds.count(c.T) > K: c.add(c.F)
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
            for i in range(32):
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
            order = [(w, i) for w in [int(x) for x in REQUIRE_DIFF.split(',') if x != ''] for i in range(32)]
            p = c.T
            for (w, i), d in zip(order, diffs if len(diffs) == len(order) else []):
                x1 = P['W'][w][i]
                c.add(-p, -d, x1)                        # p and d -> x1
                np_ = c.var(); c.add(-np_, p); c.add(-np_, -d); c.add(np_, -p, d)   # np_ = p and not d
                p = np_
    neq = eqlink(c, nP_gates, P, Q) if EQLINK else 0
    with open(out_cnf, 'w') as f:
        f.write(f"p cnf {c.nv} {len(c.cl) + len(c.xcl)}\n")
        for cl in c.cl: f.write(" ".join(map(str, cl)) + " 0\n")
        for xc in c.xcl: f.write("x " + " ".join(map(str, xc)) + " 0\n")
    mp = {'n': n, 'chaining': chaining, 'W1': P['W'][:16], 'W2': Q['W'][:16],
          'W1all': P['W'], 'W2all': Q['W'],          # full schedule (value pins on expanded words, incremental assumptions)
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
    if selectors: mp['selectors'] = {str(t): v for t, v in selectors.items()}   # row -> selector var (ROW_SELECTORS)
    json.dump(mp, open(out_map, 'w'))
    print(f"n={n} vars={c.nv} clauses={len(c.cl)} shape rows={len(rows)} signed-bits-as-x={len(signed)}" + (f" selectors={len(selectors)} from row {SEL_FROM}" if selectors else ""))

def sha_ref(n, chain, W):
    Wx = list(W)
    for t in range(16, n):
        def _s0(x): return (((x >> 7) | (x << 25)) ^ ((x >> 18) | (x << 14)) ^ (x >> 3)) & MASK
        def _s1(x): return (((x >> 17) | (x << 15)) ^ ((x >> 19) | (x << 13)) ^ (x >> 10)) & MASK
        Wx.append((_s1(Wx[t-2]) + Wx[t-7] + _s0(Wx[t-15]) + Wx[t-16]) & MASK)
    a, b, c_, d, e, f, g, h = chain
    for t in range(n):
        R = lambda x, k: ((x >> k) | (x << (32 - k))) & MASK
        T1 = (h + (R(e, 6) ^ R(e, 11) ^ R(e, 25)) + ((e & f) ^ (~e & g)) + K[t] + Wx[t]) & MASK
        T2 = ((R(a, 2) ^ R(a, 13) ^ R(a, 22)) + ((a & b) ^ (a & c_) ^ (b & c_))) & MASK
        h, g, f, e, d, c_, b, a = g, f, e, (d + T1) & MASK, c_, b, a, (T1 + T2) & MASK
    return (a, b, c_, d, e, f, g, h)

def decode(mapf, modelf):
    mp = json.load(open(mapf)); n = mp['n']
    val = {}
    # 11-01 fix (HASH$CyberAxe S39_CHECK): a solver log without -q has 'c ...' statistics lines full of integers that overwrote model
    # variables and mixed M1/M2 bits. When 'v' lines exist, read ONLY them; a bare literal file (no 'v' lines) is read whole.
    lines = open(modelf).read().split('\n')
    vl = [l[1:] for l in lines if l.startswith('v')]
    for tok in (' '.join(vl) if vl else ' '.join(l for l in lines if not l.startswith(('c', 's')))).split():
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
        W = [wv(w) for w in mp['W' + k]]
        if mp['chaining'] == 'iv': chain = IV
        else: chain = [wv(mp['A' + k][str(-1-i)]) for i in range(4)] + [wv(mp['E' + k][str(-1-i)]) for i in range(4)]
        out[k] = (W, chain, sha_ref(n, chain, W))
        print(f"M{k}: W=" + " ".join(f"{w:08x}" for w in W)); print(f"   chain=" + " ".join(f"{w:08x}" for w in chain))
        print(f"   out=" + " ".join(f"{w:08x}" for w in out[k][2]))
    print("messages differ:", out['1'][0] != out['2'][0], " outputs equal:", out['1'][2] == out['2'][2])
    print("state XOR diff per register:", " ".join(f"{x ^ y:08x}" for x, y in zip(out['1'][2], out['2'][2])),
          " chaining XOR diff:", " ".join(f"{x ^ y:08x}" for x, y in zip(out['1'][1], out['2'][1])))

def selftest(pairf, xml, workdir='/root/selftest'):
    """--selftest PAIR.txt TRAIL.xml : (1) sha_ref against the SHA-256 'abc' test vector (reference function, round constants, IV);
    (2) the registry pair fully pinned (chain rows rewritten to the pair's chain, PIN1/PIN2 = all 16 words of each copy) into the
    trail's CNF must be SAT within seconds and decode to the same pair with equal outputs. A bit-order regression in the W or chain
    encoding makes (2) UNSAT or decodes to different words. Exit 0 = both pass. (WORKLIST E57, 10-31.)"""
    import subprocess, re
    abc = [0x61626380] + [0] * 14 + [0x18]
    want = (0xba7816bf, 0x8f01cfea, 0x414140de, 0x5dae2223, 0xb00361a3, 0x96177a9c, 0xb410ff61, 0xf20015ad)
    got = tuple((x + y) & MASK for x, y in zip(sha_ref(64, IV, abc), IV))
    ok1 = got == want; print("selftest 1 (sha_ref vs SHA-256('abc')):", "ok" if ok1 else f"FAIL got {' '.join(f'{x:08x}' for x in got)}")
    txt = open(pairf).read()
    Ws = re.findall(r'M([12]): W=((?:[0-9a-f]{8} ?){16})', txt); chains = re.findall(r'chain=((?:[0-9a-f]{8} ?){8})', txt)
    if len(Ws) != 2 or not chains: print("selftest 2: cannot parse pair file"); return False
    chain = [int(x, 16) for x in chains[0].split()]
    os.makedirs(workdir, exist_ok=True)
    A = {-1: chain[0], -2: chain[1], -3: chain[2], -4: chain[3]}; E = {-1: chain[4], -2: chain[5], -3: chain[6], -4: chain[7]}
    RX = re.compile(r'^(\s*)(-?\d+)\s+A:\s*(\S{32})\s+E:\s*(\S{32})((?:[ \t]+W:\s*\S{32})?)', re.M)
    def rep(m):
        t = int(m.group(2))
        return f"{m.group(1)}{t:3d} A: {format(A[t], '032b')} E: {format(E[t], '032b')}{m.group(5)}" if t < 0 else m.group(0)
    x2 = os.path.join(workdir, 'st_trail.xml'); open(x2, 'w').write(RX.sub(rep, open(xml).read()))
    for k, ws in Ws: os.environ['PIN' + k] = ','.join(f"{i}:{w}" for i, w in enumerate(ws.split()))
    cnf, mp = os.path.join(workdir, 'st.cnf'), os.path.join(workdir, 'st.map')
    encode(x2, cnf, mp, 'free')
    r = subprocess.run(['cadical', '-t', '60', '-q', cnf], capture_output=True, text=True)
    model = os.path.join(workdir, 'st.out'); open(model, 'w').write(r.stdout)
    if r.returncode != 10: print("selftest 2 (pinned pair SAT):", "FAIL", {20: 'UNSAT (bit-order regression?)', 0: 'HELD 60 s'}.get(r.returncode, r.returncode)); return False
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf): decode(mp, model)
    dec = buf.getvalue(); dW = re.findall(r'M([12]): W=((?:[0-9a-f]{8} ?){16})', dec)
    ok2 = [w.split() for _, w in dW] == [w.split() for _, w in Ws] and 'outputs equal: True' in dec
    print("selftest 2 (pinned pair SAT + decode round-trip):", "ok" if ok2 else "FAIL\n" + dec)
    return ok1 and ok2

if __name__ == '__main__':
    if sys.argv[1] == '--selftest': sys.exit(0 if selftest(sys.argv[2], sys.argv[3]) else 1)
    if sys.argv[1] == '--decode': decode(sys.argv[2], sys.argv[3])
    else: encode(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else 'free')
