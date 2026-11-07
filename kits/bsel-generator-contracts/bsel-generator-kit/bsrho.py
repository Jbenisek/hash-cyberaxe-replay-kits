"""Birthday collision search on 3-round BLAKE3-256 (blake3-r3, one block) with 256 bit-sliced lanes and distinguished points.

The message is 64 bytes: 32 zero bytes (words m0..m7) and x (words m8..m15, little endian), one chunk of one block: chaining value IV, counter 0,
length 64, flags 11 = CHUNK_START|CHUNK_END|ROOT, 3 rounds with the message permutation between rounds.  f(x) is the 256-bit little-endian
digest integer; the walk is on g(x) = f(x) XOR q, where q is the fixed 256-bit mask of the polarities of the digest planes of the generated circuit
(the digest planes are fed back as the circuit stores them, no complement is computed); g(x) = g(y) if and only if f(x) = f(y).  n = 256 is the
claim; the organizer experiments run the same code at reduced n (the low n bits of g).
Sections: 1 scalar digest, 2 packed 7-lane tracer (the recovery circuit), 3 bit-sliced generator (256 lanes, one plane per bit: rotations are
renaming; full adders of 2 XOR and 1 select gate), 4 register allocation, 5 plan and ledger, 6 search and recovery, 7 organizer experiments,
8 command line (--selftest --ledger --loss --sweep --stats --gen-c), 9 the circuit generator in C (GEN_C).
Credit: the mask walk g = f XOR q is the method of jungjipdo's 6ae36351 (proof 3.4), implemented here from its text (its pivot full adder is
replaced here by the select adder); everything else is our 3c2d1220 / 0a9640ed / 3356413f program.
"""
import sys
import json
import hashlib
from fractions import Fraction
from math import isqrt, log, exp, expm1, log1p

M32 = 0xFFFFFFFF
IV = (0x6A09E667, 0xBB67AE85, 0x3C6EF372, 0xA54FF53A, 0x510E527F, 0x9B05688C, 0x1F83D9AB, 0x5BE0CD19)
ROUNDS = 3                         # rounds of the target (blake3-r3-prefix-v1)
UNIT = 638                         # organizer reference operation cost C of blake3-r3 (222, 430, 638, 846, 1054, 1262, 1470 for 1..7 rounds)
PERM = (2, 6, 3, 10, 7, 0, 4, 13, 1, 11, 12, 5, 9, 14, 15, 8)
GCALLS = ((0, 4, 8, 12), (1, 5, 9, 13), (2, 6, 10, 14), (3, 7, 11, 15),
          (0, 5, 10, 15), (1, 6, 11, 12), (2, 7, 8, 13), (3, 4, 9, 14))
LANES, ALL = 256, (1 << 256) - 1
FLAGS = 11


# -------- 1 scalar digest
def _ror(v, k):
    return ((v >> k) | (v << (32 - k))) & M32


def digest_words(m, rounds=ROUNDS, flags=FLAGS, blen=64, counter=0):
    """Compression of the single block m (16 words) with chaining value IV, counter 0, length 64, flags 11 (CHUNK_START|CHUNK_END|ROOT):
    8 digest words v[i] XOR v[i+8], `rounds` rounds (3 for the target)."""
    v = list(IV) + list(IV[:4]) + [counter & M32, counter >> 32, blen, flags]
    m = list(m)
    for _ in range(rounds):
        for j, (a, b, c, d) in enumerate(GCALLS):
            x, y = m[2 * j], m[2 * j + 1]
            v[a] = (v[a] + v[b] + x) & M32
            v[d] = _ror(v[d] ^ v[a], 16)
            v[c] = (v[c] + v[d]) & M32
            v[b] = _ror(v[b] ^ v[c], 12)
            v[a] = (v[a] + v[b] + y) & M32
            v[d] = _ror(v[d] ^ v[a], 8)
            v[c] = (v[c] + v[d]) & M32
            v[b] = _ror(v[b] ^ v[c], 7)
        m = [m[i] for i in PERM]
    return [v[i] ^ v[i + 8] for i in range(8)]


def f_scalar(x, n, key=0):
    """f(x): the low n bits of the digest of the message key(32 bytes) || x.  key = 0 is the target."""
    kw = [(key >> (32 * i)) & M32 for i in range(8)]
    d = digest_words(kw + [(x >> (32 * i)) & M32 for i in range(8)])
    return sum(d[i] << (32 * i) for i in range(8)) & ((1 << n) - 1)


def message(x):
    return bytes(32) + x.to_bytes(32, "little")


# -------- 2 packed tracer (recovery circuit)
PITCH, PLANES7 = 36, 7
REP = sum(1 << (PITCH * i) for i in range(PLANES7))
LIM = 1 << PITCH


class Tracer:
    """Straight-line code over 256-bit words holding 7 lanes of 36 bits (32 data bits and 4 guard bits).  A value is ('c', k),
    the same constant in every lane (folded at build time, no operation), or ('v', register, bound).  Every emitted line is one
    machine operation (add, and, or, xor, shl, shr; constants are immediates)."""

    def __init__(self):
        self.lines, self.ops, self.k = [], 0, 0

    def emit(self, expr):
        self.k += 1
        name = "t%d" % self.k
        self.lines.append("%s=%s" % (name, expr))
        self.ops += 1
        return name

    def mask(self, a):
        return ("v", self.emit("%s&%d" % (a[1], REP * M32)), M32)

    def add(self, *xs):
        c = sum(x[1] for x in xs if x[0] == "c") & M32
        vs = [x for x in xs if x[0] == "v"]
        if not vs:
            return ("c", c)
        acc = vs[0]
        for v in vs[1:]:
            while acc[2] + v[2] >= LIM:
                if acc[2] >= v[2]:
                    acc = self.mask(acc)
                else:
                    v = self.mask(v)
            acc = ("v", self.emit("%s+%s" % (acc[1], v[1])), acc[2] + v[2])
        if c:
            if acc[2] + c >= LIM:
                acc = self.mask(acc)
            acc = ("v", self.emit("%s+%d" % (acc[1], REP * c)), acc[2] + c)
        return acc

    def xor(self, a, b):
        if a[0] == "c" and b[0] == "c":
            return ("c", a[1] ^ b[1])
        if a[0] == "c":
            a, b = b, a
        if b[0] == "c":
            if b[1] == 0:
                return a
            return ("v", self.emit("%s^%d" % (a[1], REP * b[1])), (1 << max(a[2].bit_length(), b[1].bit_length())) - 1)
        return ("v", self.emit("%s^%s" % (a[1], b[1])), (1 << max(a[2].bit_length(), b[2].bit_length())) - 1)

    def ror(self, a, r):
        if a[0] == "c":
            return ("c", _ror(a[1], r))
        s1 = self.emit("%s>>%d" % (a[1], r))
        h = self.emit("%s&%d" % (s1, REP * ((1 << (32 - r)) - 1)))
        s2 = self.emit("%s<<%d" % (a[1], 32 - r))
        lw = self.emit("%s&%d" % (s2, REP * (((1 << r) - 1) << (32 - r))))
        return ("v", self.emit("%s|%s" % (h, lw)), M32)


def build_packed(qw):
    """The recovery circuit for the walk g = f XOR q: the plain 3-round compression of the block 0^32 || x followed by one XOR of each of the 8
    output words with the 32-bit word of q (a word that is 0 costs no operation).  qw = the 8 words of q."""
    tr = Tracer()
    v = [("c", w) for w in IV] + [("c", w) for w in IV[:4]] + [("c", 0), ("c", 0), ("c", 64), ("c", FLAGS)]
    m = [("c", 0)] * 8 + [("v", "i%d" % i, M32) for i in range(8, 16)]
    for _ in range(ROUNDS):
        for j, (a, b, c, d) in enumerate(GCALLS):
            x, y = m[2 * j], m[2 * j + 1]
            v[a] = tr.add(v[a], v[b], x)
            v[d] = tr.ror(tr.xor(v[d], v[a]), 16)
            v[c] = tr.add(v[c], v[d])
            v[b] = tr.ror(tr.xor(v[b], v[c]), 12)
            v[a] = tr.add(v[a], v[b], y)
            v[d] = tr.ror(tr.xor(v[d], v[a]), 8)
            v[c] = tr.add(v[c], v[d])
            v[b] = tr.ror(tr.xor(v[b], v[c]), 7)
        m = [m[i] for i in PERM]
    out = []
    for i in range(8):
        z = tr.xor(tr.xor(v[i], v[i + 8]), ("c", qw[i]))
        if z[2] > M32:
            z = tr.mask(z)
        out.append(z[1])
    nl = chr(10)
    src = "def batch(%s):" % ",".join("i%d" % i for i in range(8, 16)) + nl
    src += "".join("    %s" % ln + nl for ln in tr.lines) + "    return (%s,)" % ",".join(out) + nl
    ns = {}
    exec(src, {}, ns)
    return ns["batch"], tr.ops


_PACKED = {}


def packed_circuit(qw):
    qw = tuple(qw)
    if qw not in _PACKED:
        _PACKED[qw] = build_packed(qw)
    return _PACKED[qw]


def packed_f(xs, n, qw):
    """g on up to 7 values at once with the packed recovery circuit (g = f XOR q, low n bits; qw = the 8 words of q)."""
    words = [sum(((x >> (32 * i)) & M32) << (PITCH * l) for l, x in enumerate(xs)) for i in range(8)]
    out = packed_circuit(qw)[0](*words)
    mask = (1 << n) - 1
    return [sum(((out[i] >> (PITCH * l)) & M32) << (32 * i) for i in range(8)) & mask for l in range(len(xs))]


# -------- 3 bit-sliced generator
ZERO, ONE = (0, 0), (0, 1)


class Gen:
    """Hash-consed gate network over signals (node, neg): the stored plane is the true plane xor all-ones when neg = 1.
    Node kinds: ('v', j) input plane j, (op, a, b) with op x (xor), a (and), o (or), ('m', s, a, b) the select s ? a : b.  calls counts generator primitives."""

    def __init__(self, n):
        self.n, self.nodes, self.memo, self.calls, self.hits = n, [("c",)], {}, 0, 0
        self.inputs = []
        for j in range(n):
            self.nodes.append(("v", j))
            self.inputs.append((len(self.nodes) - 1, 0))

    def mk(self, op, a, b):
        self.calls += 1
        if a > b:
            a, b = b, a
        k = (op, a, b)
        if k in self.memo:
            self.hits += 1                                   # a shared gate (none at the 3-round target: see selftest)
        else:
            self.nodes.append(k)
            self.memo[k] = len(self.nodes) - 1
        return self.memo[k]

    def mk3(self, s, a, b):
        self.calls += 1
        k = ("m", s, a, b)
        if k in self.memo:
            self.hits += 1
        else:
            self.nodes.append(k)
            self.memo[k] = len(self.nodes) - 1
        return self.memo[k]

    def SEL(self, s, a, b):
        """s ? a : b on signals, one select gate (a 3-input bitwise word operation, as v128.bitselect or NEON BSL); a and b have equal polarity.
        The register of s holds the true selector XOR its polarity, so a selector of polarity 1 swaps a and b."""
        self.calls += 1
        if s[1]:
            a, b = b, a
        assert s[0] != 0 and a[0] != 0 and b[0] != 0 and a[1] == b[1]
        if a[0] == b[0]:
            return a
        return (self.mk3(s[0], a[0], b[0]), a[1])

    def XOR(self, x, y):
        self.calls += 1
        if x[0] == 0:
            return (y[0], y[1] ^ x[1])
        if y[0] == 0:
            return (x[0], x[1] ^ y[1])
        if x[0] == y[0]:
            return (0, x[1] ^ y[1])
        return (self.mk("x", x[0], y[0]), x[1] ^ y[1])

    def AND(self, x, y):
        self.calls += 1
        if x[0] == 0:
            return ZERO if x[1] == 0 else y
        if y[0] == 0:
            return ZERO if y[1] == 0 else x
        if x[0] == y[0]:
            return x if x[1] == y[1] else ZERO
        if x[1] == 0 and y[1] == 0:
            return (self.mk("a", x[0], y[0]), 0)
        if x[1] == 1 and y[1] == 1:
            return (self.mk("o", x[0], y[0]), 1)           # !a & !b = !(a | b)
        p, q = (x, y) if x[1] == 0 else (y, x)               # p positive, q negative: p & !qn = p ^ (p & qn)
        return self.XOR(p, (self.mk("a", p[0], q[0]), 0))

    def fa(self, a, b, c):
        """(sum, carry) of three planes a + b + c.  Three variable planes: two of them, z and x, have equal polarity (pigeonhole; the first
        such pair in the order (a, b), (a, c), (b, c)), y is the third; t = x ^ y, sum = t ^ z, carry = maj(x, y, z) = t ? z : x (one select gate):
        every full adder is 3 gates.  One or two constant planes fold: with one constant k, sum = x ^ y ^ k and carry = x & y (k = 0)
        or x | y (k = 1), 2 or 3 gates; with two constants the plane passes through."""
        ops = (a, b, c)
        cs = [t for t in ops if t[0] == 0]
        vs = [t for t in ops if t[0] != 0]
        k = 0
        for t in cs:
            k ^= t[1]
        if len(vs) == 3:
            for zi, xi in ((0, 1), (0, 2), (1, 2)):
                if vs[zi][1] == vs[xi][1]:
                    z, x, y = vs[zi], vs[xi], vs[3 - zi - xi]
                    break
            t = self.XOR(x, y)
            assert t[0] != 0
            s = self.XOR(t, z)
            return s, self.SEL(t, z, x)
        if len(vs) == 2:
            x, y = vs
            t = self.XOR(x, y)
            s = (t[0], t[1] ^ k)
            if x[1] == y[1]:
                if k == 0:
                    return s, self.AND(x, y)
                cr = self.AND((x[0], x[1] ^ 1), (y[0], y[1] ^ 1))
                return s, (cr[0], cr[1] ^ 1)
            nt = (t[0], t[1] ^ 1)
            xx = x if x[1] == nt[1] else y
            if k == 0:
                return s, self.AND(xx, nt)
            cr = self.AND((xx[0], xx[1] ^ 1), (t[0], t[1] ^ 1))
            return s, (cr[0], cr[1] ^ 1)
        if len(vs) == 1:
            x = vs[0]
            k1, k2 = cs[0][1], cs[1][1]
            return (x[0], x[1] ^ k), (ONE if k1 == k2 == 1 else ZERO if k1 == k2 == 0 else x)
        kk = cs[0][1] + cs[1][1] + cs[2][1]
        return (ZERO if kk % 2 == 0 else ONE), (ONE if kk >= 2 else ZERO)

    def add(self, A, B):
        """Ripple add of two 32-plane words, carry out of bit 31 dropped (full adders by `fa`)."""
        s, c = [], ZERO
        for i in range(32):
            if i == 31:
                s.append(self.XOR(self.XOR(A[i], B[i]), c))
            else:
                si, c = self.fa(A[i], B[i], c)
                s.append(si)
        return s

    def xorw(self, A, B):
        return [self.XOR(a, b) for a, b in zip(A, B)]


def _ror_planes(A, r):
    return [A[(i + r) % 32] for i in range(32)]


def _constw(v):
    return [ONE if (v >> i) & 1 else ZERO for i in range(32)]


def trace(n):
    """The network of the 3-round digest of the block 0^32 || x (chaining value IV, flags 11), x = low n bits of the input planes (planes >= n are 0).
    Input planes are upright; output plane j is the signal (node, neg): the plane the circuit stores is the node, so the stored value is the digest
    plane XOR neg."""
    g = Gen(n)
    zero = _constw(0)
    m = [zero] * 8 + [[g.inputs[32 * i + b] if 32 * i + b < n else ZERO for b in range(32)] for i in range(8)]
    v = [_constw(w) for w in IV] + [_constw(w) for w in IV[:4]] + [zero, zero, _constw(64), _constw(FLAGS)]
    for _ in range(ROUNDS):
        for j, (a, b, c, d) in enumerate(GCALLS):
            x, y = m[2 * j], m[2 * j + 1]
            v[a] = g.add(g.add(v[a], v[b]), x)
            v[d] = _ror_planes(g.xorw(v[d], v[a]), 16)
            v[c] = g.add(v[c], v[d])
            v[b] = _ror_planes(g.xorw(v[b], v[c]), 12)
            v[a] = g.add(g.add(v[a], v[b]), y)
            v[d] = _ror_planes(g.xorw(v[d], v[a]), 8)
            v[c] = g.add(v[c], v[d])
            v[b] = _ror_planes(g.xorw(v[b], v[c]), 7)
        m = [m[i] for i in PERM]
    return g, [s for i in range(8) for s in g.xorw(v[i], v[i + 8])]      # output plane 32 i + b


class Step:
    """The straight-line chain step for width n.  step(*planes) takes the n input planes (upright) and returns the n output planes exactly as the
    circuit stores them: stored plane j = digest plane j XOR q_j, where q_j is the polarity of the generated signal (self.q).  The digest planes are
    fed back as they are, so the chain is x -> g(x) = f(x) XOR q (low n bits); no operation complements a plane.  ops = gates."""

    def __init__(self, n=256):
        g, out = trace(n)
        self.n, self.pin, self.gen_calls, self.hits = n, [0] * n, g.calls, g.hits
        assert all(out[j][0] != 0 for j in range(n))
        self.q = [out[j][1] for j in range(n)]
        self.qint = sum(b << j for j, b in enumerate(self.q))
        self.qwords = [(self.qint >> (32 * i)) & M32 for i in range(8)]
        seen = set(out[j][0] for j in range(n))
        for k in range(len(g.nodes) - 1, 0, -1):
            if k in seen and g.nodes[k][0] in "xaom":
                seen.update(g.nodes[k][1:])
        order = [k for k in range(1, len(g.nodes)) if k in seen and g.nodes[k][0] in "xaom"]
        names, lines, self.lines, self.by, self.opsym = {0: "0"}, [], [], {}, {}
        for j, (nid, _) in enumerate(g.inputs):
            names[nid] = "i%d" % j
        sym = {"x": "^", "a": "&", "o": "|", "m": "?"}
        for k in order:
            op, ar = g.nodes[k][0], [names[v] for v in g.nodes[k][1:]]
            names[k] = "t%d" % k
            if op == "m":                                       # select s ? a : b = b ^ (s & (a ^ b))
                lines.append("%s=%s^(%s&(%s^%s))" % (names[k], ar[2], ar[0], ar[1], ar[2]))
            else:
                lines.append("%s=%s%s%s" % (names[k], ar[0], sym[op], ar[1]))
            self.lines.append(tuple([names[k]] + ar))
            self.opsym[names[k]] = (sym[op], False)
            self.by[op] = self.by.get(op, 0) + 1
        self.gates = len(order)
        self.dead = len(g.nodes) - 1 - n - len(order)           # gates built that no output uses
        outs = [names[out[j][0]] for j in range(n)]
        self.ops, self.outs = self.gates, outs
        nl, K, live, lu = chr(10), 2000, ["i%d" % j for j in range(n)], {}
        for k, (_, *ab) in enumerate(self.lines):
            for v in ab:
                lu[v] = k
        for o in outs:
            lu[o] = len(lines)
        self.fns = []                                         # compiled in chunks of K lines (a single 46,000-line function needs 100 MB to compile)
        for s0 in range(0, len(lines), K):
            e0 = min(s0 + K, len(lines))
            nxt = [v for v in live + [ln[0] for ln in self.lines[s0:e0]] if lu.get(v, -1) >= e0]
            src = "def c(%s):" % ",".join(live) + nl + "".join("    %s" % ln + nl for ln in lines[s0:e0]) + "    return (%s,)" % ",".join(outs if e0 == len(lines) else nxt) + nl
            ns = {}
            exec(compile(src, "<bitslice-step-n%d>" % n, "exec"), {}, ns)
            self.fns.append(ns["c"])
            live = nxt
        self.step = self._chain

    def _chain(self, *x):
        for f in self.fns:
            x = f(*x)
        return x

    def _last(self):
        last = {}
        for k, (_, *ab) in enumerate(self.lines):
            for v in ab:
                last[v] = k
        return last

    def peak_live(self):
        """Largest number of live plane registers after one operation (inputs live at the start, a result may reuse the register
        of a dying operand, outputs live to the end)."""
        last, outs = self._last(), set(self.outs)
        live = {"i%d" % j for j in range(self.n)}
        peak = len(live)
        for k, (nm, *_) in enumerate(self.lines):
            live.add(nm)
            live = {v for v in live if last.get(v, -1) > k or v == nm or v in outs}
            peak = max(peak, len(live))
        return peak

    def spill_ops(self, R):
        """Loads plus stores one step needs with R plane registers (Belady farthest-next-use; inputs beyond R start in memory)."""
        from bisect import bisect_left
        INF = 10 ** 10
        uses = {}
        for k, (_, *ab) in enumerate(self.lines):
            for v in ab:
                if v not in ("0", "#"):
                    uses.setdefault(v, []).append(k)
        outs = set(self.outs)

        def nxt(v, k):
            u = uses.get(v)
            if u:
                i = bisect_left(u, k)
                if i < len(u):
                    return u[i]
            return 10 ** 9 if v in outs else INF

        reg, mem, cost = {"i%d" % j for j in range(self.n)}, set(), 0
        if len(reg) > R:
            for v in sorted(reg, key=lambda y: -nxt(y, 0))[:len(reg) - R]:
                reg.discard(v)
                mem.add(v)
        for k, (nm, *ab) in enumerate(self.lines):
            need = [v for v in set(ab) if v not in ("0", "#")]
            for v in need:
                if v not in reg:
                    cost += 1
                    while len(reg) >= R:
                        w = max((y for y in reg if y not in need), key=lambda y: nxt(y, k))
                        reg.discard(w)
                        if w not in mem and nxt(w, k) < INF:
                            cost += 1
                            mem.add(w)
                    reg.add(v)
            for v in need:
                if nxt(v, k + 1) >= INF:
                    reg.discard(v)
            while len(reg) >= R:
                w = max(reg, key=lambda y: nxt(y, k + 1))
                reg.discard(w)
                if w not in mem and nxt(w, k + 1) < INF:
                    cost += 1
                    mem.add(w)
            reg.add(nm)
        return cost


# -------- 4 register allocation
def allocate(st):
    """Register assignment of the straight line: input plane j and output plane j both live in register j (the chain feed is
    renaming, no moves); temporaries take the lowest free register above n.  Returns (instructions as (op, dst, a, b) with
    register numbers, number of registers used).  Raises if output j would have to be written while input j is still needed."""
    import heapq
    n, last, free, nxt = st.n, st._last(), [], st.n
    reg = {"i%d" % j: j for j in range(n)}
    outpin = {nm: j for j, nm in enumerate(st.outs)}
    code, top = [], n
    for k, (nm, *ab) in enumerate(st.lines):
        rs = tuple(reg.get(v, -1) for v in ab)
        for v in set(ab):
            if v in reg and last.get(v, -1) == k and v not in outpin:
                if reg[v] >= n:
                    heapq.heappush(free, reg[v])
        if nm in outpin:
            j = outpin[nm]
            if last.get("i%d" % j, -1) > k:
                raise ValueError("input %d still live when output %d is produced" % (j, j))
            reg[nm] = j
        elif free:
            reg[nm] = heapq.heappop(free)
        else:
            reg[nm] = nxt
            nxt += 1
        top = max(top, reg[nm] + 1)
        code.append((nm, reg[nm]) + rs)
    return code, top


def run_allocated(st, code, planes):
    """Execute the allocated code on a register file; returns the first n registers (the next input planes)."""
    regs = [0] * (max(c[1] for c in code) + 1)
    regs[:st.n] = planes
    for (nm, d, *rs) in code:
        v = [regs[r] if r >= 0 else 0 for r in rs]
        o = st.opsym[nm][0]
        regs[d] = v[0] ^ v[1] if o == "^" else (v[0] & v[1] if o == "&" else (v[0] | v[1] if o == "|" else v[2] ^ (v[0] & (v[1] ^ v[2]))))
    return regs[:st.n]


# -------- lane transposition, packing, extraction
def _tmasks():
    res, s = {}, 128
    while s:
        m = 0
        for c in range(256):
            if not c & s:
                m |= 1 << c
        res[s] = m
        s >>= 1
    return res


_TM = _tmasks()


def transpose(rows):
    """Transpose a 256 x 256 bit matrix given as 256 integers of 256 bits (bit c of rows[i] = element (i, c))."""
    R = list(rows) + [0] * (256 - len(rows))
    s = 128
    while s:
        m = _TM[s]
        for i in range(256):
            if not i & s:
                t = ((R[i] >> s) ^ R[i + s]) & m
                R[i + s] ^= t
                R[i] ^= t << s
        s >>= 1
    return R


def pack_lanes(xs, n, pin):
    """Stored input planes (low n) for up to 256 lane values."""
    T = transpose(xs)
    return [T[j] ^ (ALL if pin[j] else 0) for j in range(n)]


def lanes_of(planes, n, pin):
    """All 256 lane values (n bits) from n stored planes."""
    T = transpose([planes[j] ^ (ALL if pin[j] else 0) for j in range(n)])
    return T[:256]


def lane_value(planes, l, pin, n):
    x = 0
    for j in range(n):
        x |= (((planes[j] >> l) & 1) ^ pin[j]) << j
    return x


def set_lane(planes, l, x, pin, n):
    bit = 1 << l
    return [(planes[j] & ~bit) | ((((x >> j) & 1) ^ pin[j]) << l) for j in range(n)]


# -------- 5 plan and ledger
LAMBDA = Fraction(497, 1000)       # 1 - exp(-LAMBDA) = 0.39165
CUTLOSS = Fraction(15, 100000)     # allowance for cut-trail points, as a fraction of Q
P_MIN = 0.390000001                # plan target; Appendix A proves P_F >= 0.39 exactly
GRAIN = 10 ** 24                   # B is a multiple of GRAIN
CMAX = 1                           # halt when more than CMAX trails are cut (more is charged as failure)
STAGE1_PLANES = 32
# machine charges (proof 3.3)
LOOP_OPS = 3                       # batch counter increment, compare with the slice limit, branch
HIT_OPS = 2800                     # a stage-1 hit lane (proof 3.3)
EVENT_OPS = 3800                   # a finished trail (proof 3.3)
CUT_OPS = 4200                     # a cut trail (proof 3.3)
SLICE_OPS = 1300                   # slice check: 256 ages
RECOVER_EXTRA = 64                 # per recovery batch beyond the packed circuit (proof 3.3)
RECOVER_PASSES = 2                 # pass 1 recomputes both trail lengths; pass 2 aligns and walks them; each at most capr batches
INSTR_BYTES = 36                   # other instructions (handlers, setup, recovery besides its circuit, loop control, generator image): opcode, registers and an inline 256-bit immediate
GATE_BYTES = 5                     # one register-only gate (^ & |) of the step, the stage-1 test or the recovery circuit: 40-bit word = 8-bit opcode + three 10-bit register numbers (800 registers < 1024)
SEL_BYTES = 6                      # one select gate s ? a : b of the step: 48-bit word = 8-bit opcode + four 10-bit register numbers
GEN_CODE = 1711                    # wasm instructions of GEN_C compiled with clang -Os, 36 bytes each
HANDLER_CODE, SETUP_CODE, RECOVERY_CODE = 1000, 160, 47   # instructions besides the main body: handlers; setup, cut, slice; recovery besides its circuit
REGISTERS = 800                    # declared register file of 256-bit words, counted as memory (the generated line needs 771)
REGFILE = REGISTERS * 32
COUNTERS = 16384                   # trail numbers, ages, counters (8 KiB) and the plane copy of the handlers (8 KiB)
KEYBITS, TBITS = 63, 17           # entry fields: 63-bit key, 17-bit trail number (80 bits = 10 bytes); trail numbers stay below LANES + tmax + CMAX + 1 < 2^17
ENTRY = 10                         # table entry: key 8 bytes, trail number 2; no length is stored, the recovery recomputes both lengths (two passes)
MEM_LIMIT = 1048576                   # bytes: 2^20
SPARE = 64                         # bytes left unused under the limit
ADVICE = 0                         # bytes of nonuniform advice: none (the mask q is derived by the generator at setup)
TAIL_LOG2 = -40
KAPPA_256 = 14
GEN_FACTOR = 250                   # word operations charged per generator primitive call and per emitted line
GEN_STATE = 2400                   # generator state words (v 2,048, tmp and mw 128 each, free-register bitmap 96)
GEN_STACK = 2048                   # shadow stack of the generator
GEN_INFO = 68                      # result record of the generator
SETUP_FIXED = 256 * 3100 + 20000   # 256 starts inserted in memory, reloaded, random word, counters
# reduced widths: s1, W, Tp, kappa
CFG = {18: dict(s1=2, W=0, Tp=1, kappa=12, Sb=4), 20: dict(s1=2, W=0, Tp=1, kappa=12, Sb=4),
       256: dict(s1=32, W=90, kappa=KAPPA_256, Sb=1 << 48)}


def stage1_ops(pin, s1):
    """Operations of the stage-1 test (mask of lanes whose s1 low digest bits are zero): OR over the positive planes, AND over
    the inverted planes, one complement if both kinds occur, one combine, one final complement; plus compare and branch."""
    npos = sum(1 for j in range(s1) if not pin[j])
    nneg = s1 - npos
    ops = max(npos - 1, 0) + max(nneg - 1, 0)
    if nneg:
        ops += 2 if npos else 1
    return ops + 1 + 2


def stage1(planes, s1, pin):
    """Mask of lanes whose s1 low digest bits are all zero."""
    nz = 0
    pos = [planes[j] for j in range(s1) if not pin[j]]
    neg = [planes[j] for j in range(s1) if pin[j]]
    if pos:
        acc = pos[0]
        for q in pos[1:]:
            acc |= q
        nz |= acc
    if neg:
        acc = neg[0]
        for q in neg[1:]:
            acc &= q
        nz |= acc ^ ALL
    return ALL ^ nz


INFLIGHT = 350                     # n = 18 plan only (sum of 256 exponential ages, units of L)


def _plan(n, Tp, kappa, tmax, Sb):
    c = CFG[n]
    s1, W = c["s1"], c["W"]
    if n == 256:
        assert LANES + tmax + CMAX < 1 << TBITS     # every trail number stored in an entry fits its field
    N, D = 1 << n, s1 + W
    L = Fraction(1 << D, Tp)
    if n == 256:
        B = _b256(Tp, tmax, kappa, Sb)
    else:                                                     # reduced widths: the plan of the 18-bit experiment
        ureq = isqrt(2 * N * LAMBDA.numerator // LAMBDA.denominator) + 2
        num, den = ureq + INFLIGHT * L + 1, CUTLOSS.denominator
        q = -(-(num * den) // (den - CUTLOSS.numerator))
        B = -(-q // LANES)
    cc = -(-kappa * L.numerator // L.denominator)
    fb = (Tp - 1).bit_length()
    return dict(n=n, s1=s1, W=W, D=D, Tp=Tp, fb=fb, kb=min(KEYBITS - fb, n - D), L=L, N=N, Q=B * LANES, B=B, kappa=kappa, Sb=Sb,
                c=cc, capr=cc + Sb, tmax=tmax, e2max=2 * B * LANES // (1 << s1) + 64,
                cmax=CMAX if n == 256 else 10 ** 9)


def tail_log2(mean, k):
    """log2 of the Chernoff bound exp(-mean) (e mean / k)^k on P(count >= k), k > mean."""
    return (-mean + k * (1 + log(mean / k))) / log(2)


_STEP256 = {}


def step256():
    if 256 not in _STEP256:
        _STEP256[256] = Step(256)
    return _STEP256[256]


def other_code(st=None):
    """Instructions besides the main body: handlers 1,000, recovery (the packed circuit with the 8 XORs of q, plus 47), setup, cut and slice 160."""
    st = st or step256()
    return HANDLER_CODE + packed_circuit(st.qwords)[1] + RECOVERY_CODE + SETUP_CODE


def machine_constants(st=None, R=REGISTERS):
    """(PH, FILT, BODY, code bytes, tmax) of the n = 256 program with R registers (spill loads and stores added to the body)."""
    st = st or step256()
    ph = st.ops
    filt = stage1_ops(st.pin, STAGE1_PLANES)
    body = ph + (st.spill_ops(R) if R < REGISTERS else 0) + filt + LOOP_OPS
    code = (ph + filt + packed_circuit(st.qwords)[1]) * GATE_BYTES + st.by.get("m", 0) * (SEL_BYTES - GATE_BYTES) + (body - ph - filt + other_code(st) - packed_circuit(st.qwords)[1]) * INSTR_BYTES
    tmax = (MEM_LIMIT - SPARE - code - R * 32 - COUNTERS - ADVICE) // ENTRY
    return ph, filt, body, code, tmax


def gen_scratch(nodes=None):
    """Scratch bytes of the runtime generator (the C port GEN_C, two passes, no node table): 8-bit use counts (8-bit counts suffice), one byte per node, for the nodes of the n = 256 network
    (constant, 256 inputs, one per gate), the signal state, the shadow stack and the result record.  Returns (total, use counts, nodes)."""
    nodes = nodes or len(trace(256)[0].nodes)
    assert nodes < 1 << 16
    uses = nodes + 1
    return uses + GEN_STATE + GEN_STACK + GEN_INFO, uses, nodes


def gen_idle(tmax):
    """Bytes of the region that holds the table, the register file, and the counters and plane copy once the search runs; while the generator
    runs the search has not started and the same region holds the generator's code image and its scratch."""
    return ENTRY * tmax + REGFILE + COUNTERS


def phase_bytes(code, tmax):
    """(setup phase, search phase) resident bytes.  Setup: main code (as large as the final code, written as the generator emits it), advice,
    the counters and plane copy, the generator's code image (GEN_CODE instructions) and its peak scratch.  Search: main code, advice, table,
    register file, counters.  The generator is never called after setup; its image and scratch are overwritten by the table and the register file."""
    scratch = gen_scratch()[0]
    return code + ADVICE + COUNTERS + GEN_CODE * INSTR_BYTES + scratch, code + ADVICE + COUNTERS + REGFILE + ENTRY * tmax

def plan(n, kappa=None, Tp=None, R=REGISTERS):
    if n != 256:
        c = CFG[n]
        p = _plan(n, c["Tp"], c["kappa"], 0, c["Sb"])
        p["tmax"] = 4 * (p["Q"] // int(p["L"])) + 64
        return p
    kappa = kappa or KAPPA_256
    tmax = machine_constants(None, R)[4]
    if Tp:
        return _plan(256, Tp, kappa, tmax, CFG[256]["Sb"])
    if tmax < 1:
        return None
    lo, hi = 1.0, float(tmax + 1)                        # largest mean number of trails the table holds
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if tail_log2(mid, tmax + 1) <= TAIL_LOG2 else (lo, mid)
    for t in range(1500, 0, -1):                           # the largest Tp that reaches 0.39 at that mean
        if _lossq(t, lo, tmax, kappa, CFG[256]["Sb"])["P_lower"] >= P_MIN:
            return _plan(256, t, kappa, tmax, CFG[256]["Sb"])
    return None


def ledger(p=None, st=None, R=REGISTERS):
    """Operation budget in word operations (exact Fractions); units are operations / 638 (C of blake3-r3)."""
    p = p or plan(256, None, None, R)
    st = st or step256()
    ph, filt, body, code, _ = machine_constants(st, R)
    gen = GEN_FACTOR * (2 * st.gen_calls + st.ops)           # the generator builds the network twice (use counts, then emission)
    parts = dict(main=body * p["B"],
                 slices=-(-p["B"] // p["Sb"]) * SLICE_OPS,
                 stage1_hits=p["e2max"] * HIT_OPS,
                 events=p["tmax"] * (EVENT_OPS + 3 * p["tmax"]),
                 cuts=p["cmax"] * CUT_OPS,
                 recovery=RECOVER_PASSES * p["capr"] * (packed_circuit(st.qwords)[1] + RECOVER_EXTRA) + 600,
                 setup=SETUP_FIXED + gen)
    return dict(parts=parts, total=sum(parts.values()), plan=p, body=body, gen=gen)


def _lossq(Tp, q, tmax, kappa, Sb, rate=1.0, fine=20000, coarse=2000):
    """Lemma 2 of proof Section 4 for q = Q / L trails; `rate` scales the collision hazard (H1 (d) sensitivity)."""
    L = Fraction(1 << 122, Tp)
    c = -(-kappa * L.numerator // L.denominator)
    th, Lf, cf = Tp / 2.0 ** 122, float(L), float(c)
    Q, B, Np = q * Lf, q * Lf / LANES, 2.0 ** 256 / rate         # Q evaluations, B batches, N' (theta N is below float resolution)
    k = int(q) + 1
    while tail_log2(q, k) > -40:                                   # N1 ~ Binomial(Q, theta) <= k - 1 except with probability 2^-40
        k += 1
    n2, shift = k + LANES + 1, 1 / (1 - k * Q / Np)
    pi = lambda m: exp(-m * (m - 1) / (2 * Np))                    # Pi_m <= this; the collision term uses Pi_(Q-k+1) <= Pi_Q shift
    split = max(1.0, Q - 120 * LANES * Lf)                         # the detection penalty lives on the last 120 L batches: fine bins there
    edges = [split * i / coarse for i in range(coarse + 1)] + [split + (Q - split) * i / fine for i in range(1, fine + 1)]
    delay, pa = 0.0, 1.0
    for b in edges[1:]:
        pb = pi(b)
        delay += (pa - pb) * exp(-th * max(0.0, B - b / LANES))   # sum of (Pi_a - Pi_b) (1 - theta)^(B - ceil(b / 256)) over the bins (a, b]
        pa = pb
    p, ql, hq = exp(-cf * th), Q * Lf / Np, Q * (Q - 1) / (2 * Np)
    p2 = exp(-(cf - 1) * th) * (1 + (cf - 1) * th / (1 - th))
    hh = (Q * (Q - 1) / 2 + 2.0 ** TBITS * Q) / Np
    t = dict(collision=pi(Q) * shift, delay=delay * shift, own_trail=ql, long_partner=(cf + Sb) * Q * p * (q + LANES) / ((1 - p) * Np), age_cap=hq * p2,
             disturbance=hq * Lf * (Q + 2.0 ** TBITS) / Np, finished_count=2.0 ** -40,
             cut_halt=-expm1(n2 * log1p(-p)) - n2 * p * exp((n2 - 1) * log1p(-p)) + ql * (1 + (2 + kappa) * exp(-kappa / 2) + 2 * hq) + hq * p * (3 + 2 * kappa),
             key_false_match=tmax * (tmax - 1) / 2 * 2.0 ** -(min(KEYBITS - (Tp - 1).bit_length(), 134) + log(Tp, 2)),
             table_capacity=2.0 ** tail_log2(q, tmax - 59),
             tiny=Q * 2.0 ** TBITS / Np + k * k * Lf / Np + 255 * Q / Np + exp(min(700.0, -300 + (exp(5) - 1) * hh)) + 2.0 ** -90)
    t["sum"] = sum(t.values())
    t["P_lower"] = 1 - t["sum"]
    t.update(trails=q, k=k, n2=n2, p=p, p2=p2, ql=ql, hq=hq, hh=hh, shift=shift)
    return t


_B = {}


def _b256(Tp, tmax, kappa, Sb):
    """The least B (multiple of GRAIN) with P_lower >= P_MIN."""
    if (Tp, tmax, kappa) not in _B:
        L = Fraction(1 << 122, Tp)
        lo, hi = 1.0, float(tmax + 1)
        for _ in range(40):
            mid = (lo + hi) / 2
            lo, hi = (lo, mid) if _lossq(Tp, mid, tmax, kappa, Sb)["P_lower"] >= P_MIN else (mid, hi)
        B = -(-int(hi * L / LANES) // GRAIN) * GRAIN
        while _lossq(Tp, float(B * LANES / L), tmax, kappa, Sb)["P_lower"] < P_MIN:
            B += GRAIN
        _B[(Tp, tmax, kappa)] = B
    return _B[(Tp, tmax, kappa)]


def loss(p, rate=1.0):
    """The probability losses of proof Section 4 (floats): the terms, their sum and the lower bound on the success probability."""
    return _lossq(p["Tp"], float(p["Q"] / p["L"]), p["tmax"], p["kappa"], p["Sb"], rate)


# -------- 6 search and recovery
class Halt(Exception):
    pass


class Engine:
    """The chain function g = f XOR q in two forms: step(planes) for 256 lanes and f2(xs) for the recovery (packed circuit with the XOR of q)."""

    def __init__(self, n):
        self.n = n
        st = Step(n)
        self.st, self.pin, self.step = st, st.pin, st.step

    def f2(self, xs):
        return packed_f(xs, self.n, self.st.qwords)

    def g_scalar(self, x):
        return f_scalar(x, self.n) ^ self.st.qint


class IdealEngine:
    """An ideal function of the same width (keyed blake2b) used as the control of test T3."""

    def __init__(self, n, key):
        self.n, self.key, self.pin = n, key, [0] * n
        self.nb = (n + 7) // 8

    def g(self, v):
        h = hashlib.blake2b(v.to_bytes(self.nb, "little"), key=self.key, digest_size=self.nb).digest()
        return int.from_bytes(h, "little") & ((1 << self.n) - 1)

    def step(self, *planes):
        vals = lanes_of(planes, self.n, self.pin)
        return pack_lanes([self.g(v) for v in vals], self.n, self.pin)

    def f2(self, xs):
        return [self.g(x) for x in xs]


def is_dp(x, p):
    """Mixed distinguished point: low s1 bits zero and the window above them below Tp."""
    return x & ((1 << p["s1"]) - 1) == 0 and (x >> p["s1"]) & ((1 << p["W"]) - 1) < p["Tp"]


def dp_key(x, p):
    """The kb bits above the window, then the fb low bits of the window value (which determine it)."""
    return (((x >> p["D"]) & ((1 << p["kb"]) - 1)) << p["fb"]) | ((x >> p["s1"]) & ((1 << p["fb"]) - 1))


def pack_entry(key, t):
    assert key < 1 << KEYBITS and t < 1 << TBITS
    return key | (t << KEYBITS)


def unpack_entry(e):
    return e & ((1 << KEYBITS) - 1), (e >> KEYBITS) & ((1 << TBITS) - 1)


def trail_lengths(p, r, ts, f2):
    """Pass 1 of the recovery: both trails (numbers ts) walk together from their starts, one packed batch per step, until each has
    reached a distinguished point; returns the two lengths.  More than capr steps is a halt."""
    mask = p["N"] - 1
    xs = [(r + ts[0]) & mask, (r + ts[1]) & mask]
    ls = [None, None]
    for k in range(1, p["capr"] + 1):
        xs = f2(xs)
        for i in (0, 1):
            if ls[i] is None and is_dp(xs[i], p):
                ls[i] = k
        if ls[0] is not None and ls[1] is not None:
            return ls
    raise Halt("recovery length")


def recover(p, r, t0, t1, f2):
    """t0, t1 = the numbers of two finished trails with the same end.  Returns (x, y), x != y, f(x) = f(y), or None.  Pass 1 recomputes
    the two lengths; pass 2: the longer trail moves alone for l1 - l2 steps, then both move together (two lanes of the packed circuit)."""
    mask = p["N"] - 1
    la, lb = trail_lengths(p, r, (t0, t1), f2)
    a, b = (t0, la), (t1, lb)
    if a[1] < b[1]:
        a, b = b, a
    if a[1] > p["capr"]:
        raise Halt("recovery length")
    xs = [(r + a[0]) & mask, (r + b[0]) & mask]
    for _ in range(a[1] - b[1]):
        xs[0] = f2([xs[0]])[0]
    if xs[0] == xs[1]:
        return None
    for _ in range(b[1] + 1):
        ya, yb = f2(xs)
        if ya == yb:
            return xs[0], xs[1]
        xs = [ya, yb]
    return None


def search(eng, p, r, cnt):
    """One attempt with the fresh random word r: the pair (x, y) or None.  Raises Halt at a budget.  Budgets: B batches,
    e2max stage-1 hits, tmax table keys, cmax cut trails, a recovery of at most capr batches."""
    n, mask, pin = p["n"], p["N"] - 1, eng.pin
    table, births, ts, nxt = {}, [0] * LANES, list(range(LANES)), LANES
    planes = pack_lanes([(r + t) & mask for t in ts], n, pin)
    cnt["inserts"] += LANES
    batches = 0
    while batches < p["B"]:
        planes = list(eng.step(*planes))
        batches += 1
        cnt["batches"] += 1
        hit = stage1(planes, p["s1"], pin)
        while hit:
            cnt["stage1_hits"] += 1
            if cnt["stage1_hits"] > p["e2max"]:
                raise Halt("stage-1 budget")
            l = (hit & -hit).bit_length() - 1
            hit &= hit - 1
            x = lane_value(planes, l, pin, n)
            if is_dp(x, p):
                key, length = dp_key(x, p), batches - births[l]
                cnt["finished"] += 1
                if key in table:
                    _, t0 = unpack_entry(table[key])
                    cnt["recoveries"] += 1
                    res = recover(p, r, t0, ts[l], eng.f2)
                    if res is None:
                        raise Halt("recovery found no pair")
                    return res
                if len(table) >= p["tmax"]:
                    raise Halt("table full")
                table[key] = pack_entry(key, ts[l])
                ts[l], nxt, births[l] = nxt, nxt + 1, batches
                planes = set_lane(planes, l, (r + ts[l]) & mask, pin, n)
                cnt["inserts"] += 1
        if batches % p["Sb"] == 0:
            for l in range(LANES):
                if batches - births[l] >= p["c"]:
                    cnt["cut"] += 1
                    if cnt["cut"] > p["cmax"]:
                        raise Halt("cut budget")
                    ts[l], nxt, births[l] = nxt, nxt + 1, batches
                    planes = set_lane(planes, l, (r + ts[l]) & mask, pin, n)
                    cnt["inserts"] += 1
    return None


class Counters(dict):
    def __missing__(self, k):
        return 0


def derive(seed, tag, bits=256):
    return int.from_bytes(hashlib.shake_256(("%s/%s" % (seed, tag)).encode()).digest((bits + 7) // 8), "little") & ((1 << bits) - 1)


def attempt(eng, p, seed, tag):
    cnt = Counters()
    try:
        res = search(eng, p, derive(seed, tag, p["n"]), cnt)
    except Halt as e:
        cnt["halt"] += 1
        res = None
    return res, cnt


# -------- 7 organizer experiments
N_T3 = 18                          # width of the search experiment and of the ideal control
N_T1 = 12                          # width of the family-law runs (fresh key)
M_T2, B_T2 = 2048, 21              # points per trial, projection width (event: low 21 bits of the digest)
T2_NAMES = ("w0", "w3", "w7", "xor8", "sum8", "p01", "p23")


def t1_run(seed, n=N_T1):
    """Family law, fresh random key K: steps until the first repeat of x -> low n bits of digest(K || x)."""
    key, x, seen = derive(seed, "k"), derive(seed, "s", n), set()
    while x not in seen:
        seen.add(x)
        x = f_scalar(x, n, key)
    return len(seen)


def e1_trial(seed, eng, ideal_cls):
    """T3 (target, organizer-checked pair) and the ideal control, one attempt each; T1 as an observation."""
    p = plan(N_T3)
    res, cnt = attempt(eng, p, seed, "t")
    ideal = ideal_cls(N_T3, hashlib.blake2b(("%s/ideal" % seed).encode(), digest_size=32).digest())
    res_i, cnt_i = attempt(ideal, p, seed, "i")
    obs = dict(target_ok=int(res is not None), ideal_ok=int(res_i is not None), target_batches=cnt["batches"],
               target_halt=cnt["halt"], ideal_halt=cnt_i["halt"], t1_steps=t1_run(seed))
    if res is None:
        return None, None, obs
    return message(res[0]), message(res[1]), obs


_M21 = (1 << B_T2) - 1
_F21 = sum(_M21 << (32 * i) for i in range(8))
_KS = sum(1 << (32 * i) for i in range(8))


def t2_columns(digs):
    """The seven projections (T2_NAMES) of each 256-bit digest, as seven lists of B_T2-bit values:
    word 0, word 3, word 7, xor of the 8 words, sum of the 8 words, and two 22-bit concatenations of 11-bit pieces."""
    m = _M21
    folded = [d ^ (d >> 128) for d in digs]
    folded = [d ^ (d >> 64) for d in folded]
    return [[d & m for d in digs], [(d >> 96) & m for d in digs], [(d >> 224) & m for d in digs],
            [(d ^ (d >> 32)) & m for d in folded],
            [(((d & _F21) * _KS) >> 224) & m for d in digs],
            [((d & 0x7FF) | (((d >> 32) & 0x7FF) << 11)) & m for d in digs],
            [(((d >> 64) & 0x7FF) | (((d >> 107) & 0x7FF) << 11)) & m for d in digs]]


def e2_trial(seed, tr, st256):
    """T2: M_T2 points of the target function (the block 0^32 || x, K = 0) at width 256 (source by trial index: uniform inputs, counter r + i, or iterates of g
    from 256 random starts), the 256-bit digests f(x) = (stored planes) XOR q, equal pairs in seven 21-bit projections.  w0 is the checked event."""
    src = tr % 3
    if src == 0:
        xs = [derive(seed, "u%d" % i) for i in range(M_T2)]
    elif src == 1:
        r = derive(seed, "r")
        xs = [(r + i) & ((1 << 256) - 1) for i in range(M_T2)]
    else:
        xs = None
    digs = []
    if xs is not None:
        for b in range(M_T2 // LANES):
            pl = pack_lanes(xs[b * LANES:(b + 1) * LANES], 256, st256.pin)
            digs += lanes_of(list(st256.step(*pl)), 256, st256.pin)
    else:
        cur = [derive(seed, "c%d" % l) for l in range(LANES)]
        xs = []
        for b in range(M_T2 // LANES):
            xs += cur
            cur = lanes_of(list(st256.step(*pack_lanes(cur, 256, st256.pin))), 256, st256.pin)
            digs += cur
    digs = [d ^ st256.qint for d in digs]                  # the circuit stores g(x) = f(x) XOR q; the projections are of the digest f(x)
    obs = {"source": src}
    pair = None
    for k, col in enumerate(t2_columns(digs)):
        name = T2_NAMES[k]
        obs["dup_" + name] = len(col) - len(set(col))
        if k == 0 and obs["dup_w0"]:
            first = {}
            for i, c in enumerate(col):
                if c in first and xs[first[c]] != xs[i]:
                    pair = (xs[first[c]], xs[i])
                    break
                first.setdefault(c, i)
    if pair is None:
        return None, None, obs
    return message(pair[0]), message(pair[1]), obs


def serve(req):
    eid, out = req["experiment_id"], []
    if eid == "bsrho-n18":
        eng = Engine(N_T3)
        for t in req["trials"]:
            a, b, obs = e1_trial(t["seed"], eng, IdealEngine)
            out.append({"trial": t["trial"], "message_a_hex": a.hex() if a else None, "message_b_hex": b.hex() if b else None,
                        "observations": obs})
    elif eid == "proj-k0-w256":
        st = step256()
        for t in req["trials"]:
            a, b, obs = e2_trial(t["seed"], t["trial"], st)
            out.append({"trial": t["trial"], "message_a_hex": a.hex() if a else None, "message_b_hex": b.hex() if b else None,
                        "observations": obs})
    else:
        raise ValueError("unknown experiment")
    return {"schema_version": 1, "trials": out}


# -------- 8 command line
def selftest():
    import random
    ok = True
    rnd = random.Random(3)
    st = step256()
    print("hash-consing hits", st.hits, "dead gates", st.dead, "(the machine generator keeps no node table: both must be 0)")
    ok &= st.hits == 0 and st.dead == 0
    print("n=256 step: ops", st.ops, "gates", st.gates, st.by, "peak live", st.peak_live(), "spill_ops(1024)", st.spill_ops(1024), "q weight", bin(st.qint).count("1"))
    code, regs = allocate(st)
    print("allocation: registers used", regs, "moves 0 (output j in register j)")
    pl0 = [rnd.getrandbits(256) for _ in range(256)]
    good = run_allocated(st, code, pl0) == list(st.step(*pl0))
    print("allocated code on a register file equals the step:", good)
    ok &= good
    # regression of the stored-plane step against the scalar 3-round compression: 4,096 lanes (16 batches of 256), full 256-bit g = f XOR q
    good, tot = True, 0
    for _ in range(16):
        xs = [rnd.getrandbits(256) for _ in range(LANES)]
        out = lanes_of(list(st.step(*pack_lanes(xs, 256, st.pin))), 256, st.pin)
        good &= all(out[l] == f_scalar(xs[l], 256) ^ st.qint for l in range(LANES))
        tot += LANES
    print("%d lanes, full 256-bit g = f XOR q, step vs scalar compression: %s" % (tot, good))
    ok &= good
    good = True
    for _ in range(16):
        cur = [rnd.getrandbits(256) for _ in range(LANES)]
        pl = pack_lanes(cur, 256, st.pin)
        for _ in range(7):
            pl = list(st.step(*pl))
            cur = [f_scalar(x, 256) ^ st.qint for x in cur]
        good &= lanes_of(pl, 256, st.pin) == cur
    print("4,096 lanes (16 x 256) chained for 7 steps, g = f XOR q vs scalar compression:", good)
    ok &= good
    e = Engine(N_T3)
    xs = [rnd.getrandbits(N_T3) for _ in range(LANES)]
    pl = pack_lanes(xs, N_T3, e.pin)
    for _ in range(5):
        pl = list(e.step(*pl))
        xs = [e.g_scalar(x) for x in xs]
    good = lanes_of(pl, N_T3, e.pin)[:LANES] == xs
    print("n=%d chain, 5 steps, 256 lanes:" % N_T3, good)
    ok &= good
    xs = [rnd.getrandbits(256) for _ in range(7)]
    good = packed_f(xs, 256, st.qwords) == [f_scalar(x, 256) ^ st.qint for x in xs]
    print("packed recovery circuit (%d ops, with the 8 XORs of q) vs scalar:" % packed_circuit(st.qwords)[1], good)
    ok &= good
    rows = [rnd.getrandbits(256) for _ in range(256)]
    good = transpose(transpose(rows)) == rows and (transpose(rows)[5] >> 9) & 1 == (rows[9] >> 5) & 1
    print("transpose:", good)
    ok &= good
    # the search at n = 18 finds recoverable collisions
    p = plan(N_T3)
    found = 0
    for s in range(6):
        res, cnt = attempt(e, p, "selftest/%d" % s, "t")
        if res is not None:
            found += 1
            ok &= res[0] != res[1] and f_scalar(res[0], N_T3) == f_scalar(res[1], N_T3)
    print("search n=%d: %d of 6 attempts returned a verified pair" % (N_T3, found))
    ok &= found > 0
    print("selftest", ok)
    return ok


def print_ledger(lg):
    from math import log2
    print({k: (str(v) if isinstance(v, Fraction) else v) for k, v in lg["plan"].items()})
    print("operations per batch (body)", lg["body"])
    for k, v in lg["parts"].items():
        print(k, v)
    print("N =", lg["total"])
    print("time_log2 = %.5f (unrounded %.8f)" % (log2(lg["total"] / UNIT) + 5e-6, log2(lg["total"] / UNIT)))


def stats(trials=256):
    """Run the two experiments locally on pseudo-random seeds and print the counts (descriptive only, no inference is drawn from them)."""
    from math import sqrt, pi
    seeds = [hashlib.sha256(("stats/%d" % i).encode()).hexdigest() for i in range(trials)]
    rows = serve({"experiment_id": "bsrho-n18", "trials": [{"trial": i, "seed": s} for i, s in enumerate(seeds)]})["trials"]
    N1 = 1 << N_T1
    tt = sum(r["observations"]["target_ok"] for r in rows)
    ii = sum(r["observations"]["ideal_ok"] for r in rows)
    print("T3 n=%d: attempts returning a verified pair: target %d of %d, ideal function %d of %d" % (N_T3, tt, trials, ii, trials))
    ts = [r["observations"]["t1_steps"] for r in rows]
    mean = sum(ts) / trials
    print("T1 n=%d fresh K: %d runs, mean first repeat %.2f (sqrt(pi N/2) = %.2f)" % (N_T1, trials, mean, sqrt(pi * N1 / 2)))
    seedl = [hashlib.sha256(("stats2/%d" % i).encode()).hexdigest() for i in range(trials)]
    r2 = serve({"experiment_id": "proj-k0-w256", "trials": [{"trial": i, "seed": s} for i, s in enumerate(seedl)]})["trials"]
    lam = M_T2 * (M_T2 - 1) / 2 / (1 << B_T2)
    print("T2 width 256, K=0: %d points, %d-bit projections, equal pairs per trial if uniform %.4f, trials with a pair if uniform %.4f" % (M_T2, B_T2, lam, 1 - exp(-lam)))
    for s in range(3):
        sel = [r for r in r2 if r["observations"]["source"] == s]
        line = []
        for name in T2_NAMES:
            tot = sum(r["observations"]["dup_" + name] for r in sel)
            line.append("%s %d (uniform reference %.1f)" % (name, tot, lam * len(sel)))
        hit = sum(1 for r in sel if r["message_a_hex"])
        print("  source %s (%d trials): returned pairs %d (uniform reference %.1f); " % (("uniform", "counter", "iterates")[s], len(sel), hit, (1 - exp(-lam)) * len(sel)) + "; ".join(line))
    return rows, r2


# -------- 9 the circuit generator in C
# The generator of section 3 and 4 (select-gate adder, register allocation) written in freestanding C in two passes without a node table (this circuit has no shared
# and no dead gate: the reference generator Gen/Step finds none).  It was compiled to WebAssembly (clang -Os) and run in a sandbox with 16 pages (1,048,576
# bytes) of guest memory: it emits the same program as Step/allocate (proof 3.6).  `--gen-c` prints it.
GEN_C = r'''/* Freestanding C port of the bsrho.py circuit generator for the 3-round target (Gen / trace(256) / allocate), in two passes and without a node table.
   No libc, no malloc, no imports.  Exports: run(), info_ptr(), code_ptr().
   The straight line has no shared gate and no dead gate at this target (the reference generator with a hash-consing table finds 0 hits), so a gate is a
   new node every time and the node numbers are the creation order.  Pass 0 builds the circuit and counts the uses of every node (8 bits per node).
   Pass 1 builds the same circuit again; every signal carries its register, so no node table is needed: an operand whose use count reaches zero frees
   its register (registers 256 and above; the output planes are pinned: output plane j in register j, the register of input plane j), the result takes
   the lowest free register or a new one, and the instruction record is written: a gate of two operands is the op byte then dst, a, b as three 10-bit
   fields of a u32 LE (5 bytes); the select s ? a : b is the op byte '?' then dst, s, a, b as four 10-bit fields of a 40-bit LE word (6 bytes).
   Static memory map (all inside the guest, at 3 rounds):
     code region   CODE_BYTES   final main-code size of the entry (5-byte and 6-byte records for the gates)
     counters      16,384 B     (reserved as in the machine layout)
     uses          NMAX + 1 B   8-bit use counts (8-bit counts suffice)
     state         v[16][32] u32 = 2,048 B, tmp[32] and mw[32] u32 = 256 B, free-register bitmap fbits[24] u32 = 96 B, info                       */
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32;

#ifndef NMAX
#define NMAX 11975                 /* nodes: constant 0, 256 inputs, one per gate */
#endif
#ifndef CODE_BYTES
#define CODE_BYTES 108095
#endif
#define ROUNDS 3
#define N 256
#define CTR_BYTES 16384
#define NODE(s) (((s) >> 1) & 0xFFFFu)
#define REG(s) ((s) >> 17)
#define ZERO 0u
#define ONE 1u

static u8 code[CODE_BYTES];
__attribute__((used)) static u8 counters[CTR_BYTES];
static u8 uses[NMAX + 1];
static u32 v[16][32], tmp[32], mw[32], fbits[24];

static u32 nn, calls, err, pass, kk, cb, nxt, top, firstout;
static struct { u32 ninst, nreg, nodes, calls, err, sz_code, sz_ctr, sz_uses, sz_state; u8 q[32]; } info;

static const u32 IV[8] = {0x6A09E667u,0xBB67AE85u,0x3C6EF372u,0xA54FF53Au,0x510E527Fu,0x9B05688Cu,0x1F83D9ABu,0x5BE0CD19u};
static const u8 PERM[16] = {2,6,3,10,7,0,4,13,1,11,12,5,9,14,15,8};
static const u8 GC[8][4] = {{0,4,8,12},{1,5,9,13},{2,6,10,14},{3,7,11,15},{0,5,10,15},{1,6,11,12},{2,7,8,13},{3,4,9,14}};

static u32 getu(u32 n) { return uses[n]; }
static void setu(u32 n, u32 c) { uses[n] = (u8)c; }
static void put32(u8 *p, u32 w) { p[0] = (u8)w; p[1] = (u8)(w >> 8); p[2] = (u8)(w >> 16); p[3] = (u8)(w >> 24); }

static void drop(u32 s) {                                   /* one use of operand s is consumed (pass 1) */
  u32 n = NODE(s), c = getu(n) - 1;
  setu(n, c);
  if (c == 0 && REG(s) >= N) { u32 r = REG(s) - N; fbits[r >> 5] |= 1u << (r & 31); }
}
static u32 gate(u32 op, const u32 *o, u32 no) {             /* a new gate (op 0 ^, 1 &, 2 |, 3 select) of the operands' nodes; returns the positive signal */
  u32 id = nn++, r[3], d;
  if (id >= NMAX) { err = 1; return 0; }
  if (pass == 0) {
    for (u32 i = 0; i < no; i++) if (getu(NODE(o[i])) == 255) { err = 6; return 0; }
    for (u32 i = 0; i < no; i++) setu(NODE(o[i]), getu(NODE(o[i])) + 1);
    return id << 1;
  }
  for (u32 i = 0; i < no; i++) r[i] = REG(o[i]);
  for (u32 i = 0; i < no; i++) drop(o[i]);
  if (id >= firstout) {
    d = id - firstout;
    if (getu(1 + d) != 0) { err = 4; return 0; }            /* input plane d is still needed after this gate */
  } else {
    u32 w = 0;
    while (w < 24 && fbits[w] == 0) w++;
    if (w < 24) { u32 b = 0; while (!((fbits[w] >> b) & 1u)) b++; fbits[w] &= ~(1u << b); d = N + 32 * w + b; }
    else d = nxt++;
  }
  if (d + 1 > top) top = d + 1;
  u32 rl = no == 3 ? 6 : 5;
  if (cb + rl > CODE_BYTES) { err = 5; return 0; }
  u8 *rec = code + cb; cb += rl; kk++;
  rec[0] = op == 0 ? '^' : op == 1 ? '&' : op == 2 ? '|' : '?';
  if (d >= 1024 || r[0] >= 1024 || r[1] >= 1024 || (no == 3 && r[2] >= 1024)) { err = 7; return 0; }
  put32(rec + 1, d | (r[0] << 10) | (r[1] << 20) | (no == 3 ? (r[2] & 3u) << 30 : 0));
  if (no == 3) rec[5] = (u8)(r[2] >> 2);                  /* 48-bit record: opcode byte, then four 10-bit register numbers */
  return (id << 1) | (d << 17);
}
static u32 mk(u32 op, u32 x, u32 y) {
  calls++;
  if (NODE(x) > NODE(y)) { u32 t = x; x = y; y = t; }
  u32 o[2] = {x, y};
  return gate(op, o, 2);
}
static u32 SEL(u32 s, u32 a, u32 b) {                      /* s ? a : b, a and b of equal polarity; a selector of polarity 1 swaps a and b */
  calls++;
  if (s & 1) { u32 t = a; a = b; b = t; }
  if (!NODE(s) || !NODE(a) || !NODE(b) || (a & 1) != (b & 1)) { err = 8; return 0; }
  if (NODE(a) == NODE(b)) return a;
  calls++;
  u32 o[3] = {s, a, b};
  return gate(3, o, 3) | (a & 1);
}
static u32 XOR(u32 x, u32 y) {
  calls++;
  if (!NODE(x)) return y ^ (x & 1);
  if (!NODE(y)) return x ^ (y & 1);
  if (NODE(x) == NODE(y)) return (x ^ y) & 1;
  return mk(0, x, y) ^ ((x ^ y) & 1);
}
static u32 AND(u32 x, u32 y) {
  calls++;
  if (!NODE(x)) return (x & 1) == 0 ? ZERO : y;
  if (!NODE(y)) return (y & 1) == 0 ? ZERO : x;
  if (NODE(x) == NODE(y)) return x == y ? x : ZERO;
  if (!(x & 1) && !(y & 1)) return mk(1, x, y);
  if ((x & 1) && (y & 1)) return mk(2, x, y) | 1;
  u32 p = (x & 1) == 0 ? x : y, q = (x & 1) == 0 ? y : x;
  return XOR(p, mk(1, p, q));
}
static void fa(u32 a, u32 b, u32 c, u32 *sum, u32 *carry) {
  u32 ops[3] = {a, b, c}, vs[3], nv = 0, k = 0, nc = 0, cs[3] = {0, 0, 0};
  for (int i = 0; i < 3; i++) {
    if (!NODE(ops[i])) { cs[nc++] = ops[i] & 1; k ^= ops[i] & 1; } else vs[nv++] = ops[i];
  }
  if (nv == 3) {                                           /* z, x of equal polarity, y the third: sum = (x ^ y) ^ z, carry = (x ^ y) ? z : x */
    u32 zi = 1, xi = 2;
    if ((vs[0] & 1) == (vs[1] & 1)) { zi = 0; xi = 1; } else if ((vs[0] & 1) == (vs[2] & 1)) { zi = 0; xi = 2; }
    u32 z = vs[zi], x = vs[xi], y = vs[3 - zi - xi];
    u32 tt = XOR(x, y);
    if (!NODE(tt)) { err = 9; return; }
    u32 s = XOR(tt, z);
    *sum = s; *carry = SEL(tt, z, x); return;
  }
  if (nv == 2) {
    u32 x = vs[0], y = vs[1];
    u32 t = XOR(x, y);
    u32 s = t ^ k;
    if ((x & 1) == (y & 1)) {
      if (k == 0) { *sum = s; *carry = AND(x, y); return; }
      *sum = s; *carry = AND(x ^ 1, y ^ 1) ^ 1; return;
    }
    u32 nt = t ^ 1;
    u32 xx = (x & 1) == (nt & 1) ? x : y;
    if (k == 0) { *sum = s; *carry = AND(xx, nt); return; }
    *sum = s; *carry = AND(xx ^ 1, t ^ 1) ^ 1; return;
  }
  if (nv == 1) {
    u32 x = vs[0], k1 = cs[0], k2 = cs[1];
    *sum = x ^ k; *carry = (k1 == 1 && k2 == 1) ? ONE : (k1 == 0 && k2 == 0) ? ZERO : x; return;
  }
  u32 kk3 = cs[0] + cs[1] + cs[2];
  *sum = (kk3 % 2 == 0) ? ZERO : ONE; *carry = kk3 >= 2 ? ONE : ZERO;
}
static void add(const u32 *A, const u32 *B, u32 *out) {   /* out may alias A */
  u32 c = ZERO;
  for (int i = 0; i < 32; i++) {
    if (i == 31) out[i] = XOR(XOR(A[i], B[i]), c);
    else { u32 si; fa(A[i], B[i], c, &si, &c); out[i] = si; }
  }
}
static void xorrot(u32 *D, const u32 *A, int r) {         /* D = ror_planes(xorw(D, A), r) */
  for (int i = 0; i < 32; i++) tmp[i] = XOR(D[i], A[i]);
  for (int i = 0; i < 32; i++) D[i] = tmp[(i + r) & 31];
}
static void constw(u32 *w, u32 val) { for (int i = 0; i < 32; i++) w[i] = (val >> i) & 1u; }
static u32 inp(u32 j) { return ((1 + j) << 1) | (j << 17); }
static u32 *msg(u32 w) { for (u32 b = 0; b < 32; b++) mw[b] = w < 8 ? ZERO : inp(32 * (w - 8) + b); return mw; }   /* message word w of 0^32 || x */

static void trace(void) {                                  /* the 3-round network of the block 0^32 || x */
  u32 mi[16], nm[16];
  nn = 1 + N;
  for (int i = 0; i < 8; i++) constw(v[i], IV[i]);
  for (int i = 0; i < 4; i++) constw(v[8 + i], IV[i]);
  constw(v[12], 0); constw(v[13], 0); constw(v[14], 64); constw(v[15], 11);
  for (int i = 0; i < 16; i++) mi[i] = (u32)i;
  for (int r = 0; r < ROUNDS; r++) {
    for (int j = 0; j < 8; j++) {
      u32 a = GC[j][0], b = GC[j][1], c = GC[j][2], d = GC[j][3];
      add(v[a], v[b], v[a]); add(v[a], msg(mi[2 * j]), v[a]);
      xorrot(v[d], v[a], 16);
      add(v[c], v[d], v[c]);
      xorrot(v[b], v[c], 12);
      add(v[a], v[b], v[a]); add(v[a], msg(mi[2 * j + 1]), v[a]);
      xorrot(v[d], v[a], 8);
      add(v[c], v[d], v[c]);
      xorrot(v[b], v[c], 7);
    }
    for (int i = 0; i < 16; i++) nm[i] = mi[PERM[i]];
    for (int i = 0; i < 16; i++) mi[i] = nm[i];
  }
  firstout = nn;                                           /* the 256 output gates are the last 256 gates, in order, none constant */
  for (u32 j = 0; j < N; j++) {
    u32 s = XOR(v[j >> 5][j & 31], v[(j >> 5) + 8][j & 31]);
    if (!NODE(s) || NODE(s) != firstout + j) err = 3;
    info.q[j >> 3] |= (u8)((s & 1) << (j & 7));
  }
}

__attribute__((export_name("info_ptr"))) u32 info_ptr(void) { return (u32)(unsigned long)&info; }
__attribute__((export_name("code_ptr"))) u32 code_ptr(void) { return (u32)(unsigned long)code; }

__attribute__((export_name("run"))) int run(void) {
  info.sz_code = sizeof code; info.sz_ctr = sizeof counters; info.sz_uses = sizeof uses;
  info.sz_state = sizeof v + sizeof tmp + sizeof mw + sizeof fbits;
  err = 0; calls = 0; pass = 0; kk = 0; cb = 0; nxt = N; top = N;
  trace();
  info.nodes = nn;
  if (err) { info.err = err; return (int)err; }
  pass = 1;
  trace();
  info.calls = calls;
  info.ninst = kk; info.nreg = top; info.err = err;
  return (int)err;
}
'''


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    if arg == "--selftest":
        sys.exit(0 if selftest() else 1)
    elif arg == "--ledger":
        print_ledger(ledger())
        from math import log2
        for R in (512, 256):
            pR = plan(256, None, None, R)
            if pR is None:
                print("smaller file R = %d: spill ops per batch %d, no table fits in 2^20 bytes" % (R, step256().spill_ops(R)))
                continue
            lgR = ledger(pR, None, R)
            print("smaller file R = %d: spill ops per batch %d, body %d, tmax %d, Tp %d, time_log2 %.5f, success lower bound %.4f%s" % (
                R, step256().spill_ops(R), lgR["body"], pR["tmax"], pR["Tp"], log2(lgR["total"] / UNIT), loss(pR)["P_lower"],
                "" if loss(pR)["P_lower"] >= 0.39 else " (below 0.39: not a valid plan)"))
        st = step256()
        ph, filt, body, code, tmax = machine_constants(st)
        print("PH", ph, "filter", filt, "body", body, "code bytes", code, "tmax", tmax, "generator calls", st.gen_calls)
        print("memory bytes", ENTRY * tmax + code + REGFILE + COUNTERS + ADVICE, "limit", MEM_LIMIT)
        sc = gen_scratch()
        ph1, ph2 = phase_bytes(code, tmax)
        print("setup phase bytes", ph1, "search phase bytes", ph2, "peak", max(ph1, ph2), "limit", MEM_LIMIT, "fits", max(ph1, ph2) <= MEM_LIMIT)
        print("generator scratch", sc[0], "(use counts", sc[1], ", nodes", sc[2], ") + image", GEN_CODE * INSTR_BYTES, "=", sc[0] + GEN_CODE * INSTR_BYTES, "idle region", gen_idle(tmax), "fits", sc[0] + GEN_CODE * INSTR_BYTES <= gen_idle(tmax), "generator code instructions", GEN_CODE)
        print("other code instructions", other_code(st), "main body", body, "total instructions", body + other_code(st))
        print("recovery circuit operations", packed_circuit(st.qwords)[1], "q (hex)", "%064x" % st.qint)
    elif arg == "--gen-c":
        sys.stdout.write(GEN_C)
    elif arg == "--loss":
        for k, v in loss(plan(256)).items():
            print(k, v)
    elif arg == "--sweep":
        from math import log2
        for kappa in range(8, 17):
            p = plan(256, kappa)
            lg = ledger(p)
            ls = loss(p)
            print("kappa", kappa, "Tp", p["Tp"], "tmax", p["tmax"], "time_log2 %.5f" % log2(lg["total"] / UNIT), "P_lower %.5f" % ls["P_lower"])
    elif arg == "--stats":
        stats()
    else:
        json.dump(serve(json.load(sys.stdin)), sys.stdout)
