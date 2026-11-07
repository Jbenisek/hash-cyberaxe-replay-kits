"""Collision-rate measurement on the real r=24 walk map at reduced widths (premise support, Section 8).  Usage: python measure.py w trials seedbase
Map at width w: F_w(v) = low w bits of F_kappa(v), kappa = kappa_t with t drawn per trial from the set of 96, start uniform in [0, 2^w).  Each walk runs to its
first repeat (t, the index of the first value equal to an earlier one).  Control: keyed SHA-256 reduced to w bits.  Output: one JSON line per width."""
import sys, os, json, hashlib, math, random
SHIFT = int(os.environ.get('SHIFT', '0'))
import rho as m


def first_repeat(f, v0):
    seen = {v0}
    v = v0
    t = 0
    while True:
        v = f(v)
        t += 1
        if v in seen:
            return t
        seen.add(v)


def loglik(c, ts, N):
    # P(t = n) = prod_{i<n} (1 - c i / N) * c n / N ; evaluate with a running sum over the sorted distinct values
    tot = 0.0
    srt = sorted(ts)
    acc, i = 0.0, 1
    for n in srt:
        while i < n:
            acc += math.log1p(-c * i / N)
            i += 1
        tot += acc + math.log(c * n / N)
    return tot


def mle(ts, N):
    lo, hi = 0.05, 4.0
    for _ in range(60):
        a, b = lo + (hi - lo) / 3, hi - (hi - lo) / 3
        if loglik(a, ts, N) < loglik(b, ts, N):
            lo = a
        else:
            hi = b
    return (lo + hi) / 2


def interval(ts, N, ch):
    top = loglik(ch, ts, N)
    inside = lambda c: 2 * (top - loglik(c, ts, N)) <= 3.84
    a, b = 0.02, ch
    for _ in range(50):
        mid = (a + b) / 2
        if inside(mid):
            b = mid
        else:
            a = mid
    lo = b
    a, b = ch, 6.0
    for _ in range(50):
        mid = (a + b) / 2
        if inside(mid):
            a = mid
        else:
            b = mid
    return lo, a


def run(w, K, seedbase):
    N = 1 << w
    mask = N - 1
    ts_real, ts_ctrl = [], []
    for k in range(K):
        rng = random.Random(seedbase * 1000003 + k)
        kappa = m.kappa_of(rng.randrange(m.G_SET))
        F = m.make_F(kappa)
        v0 = rng.randrange(N)
        ts_real.append(first_repeat(lambda v: (F(v) >> SHIFT) & mask, v0))
        key = b"ctrl%d-%d-%d" % (w, seedbase, k)
        ts_ctrl.append(first_repeat(lambda v: int.from_bytes(hashlib.sha256(key + v.to_bytes(8, "little")).digest()[:8], "little") & mask, v0))
    out = {"w": w, "K": K, "seedbase": seedbase}
    for nm, ts in (("real", ts_real), ("ctrl", ts_ctrl)):
        ch = mle(ts, N)
        lo, hi = interval(ts, N, ch)
        out[nm] = {"c": round(ch, 4), "lo": round(lo, 4), "hi": round(hi, 4), "sum_t": sum(ts)}
    return out


if __name__ == "__main__":
    print(json.dumps(run(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))))
