#!/usr/bin/env python3
# r39-way board price of a door-paid tail: EXACT r39 formula (pkg_r39_combined/work/time_calc.py)
# + r39 ledger window stats (led/win_*.json), evaluated at a given tail q.
# Numbers only. Read-only on inputs. The door-paid tail of the sparse 40/41 members
# costs ~= the published r39 pair's (HASH$CyberAxe note 10-28: rows>=16 digits 95 vs published 92),
# so its r39-way price is the published door-paid tail priced through this same pipeline.

# Publication path adapter: resolve data paths from the extracted source tree.
def _hca_public_path_text(value):
    if "__HCA_WORKSPACE__/" not in value:
        return value
    import os as _hca_os
    from pathlib import Path as _hca_Path
    root = _hca_os.environ.get("HASHCYBERAXE_WORKSPACE")
    if root is None:
        here = _hca_Path(__file__).resolve().parent
        root = next((str(p) for p in (here, *here.parents) if (p / "research").is_dir()), None)
    if root is None:
        raise FileNotFoundError("Extract the research source tree, or set HASHCYBERAXE_WORKSPACE to its archive directory.")
    return value.replace("__HCA_WORKSPACE__/", str(_hca_Path(root).resolve()).replace("\\", "/") + "/")

import json, math, glob
from fractions import Fraction
WORK = _hca_public_path_text('__HCA_WORKSPACE__/research/pkg_r39_combined/work')
W = [json.load(open(f))[0] for f in sorted(glob.glob(WORK + "/led/win_*.json"))]
n = len(W); ops = [w["ops"] for w in W]; cl = [w["distinct_claws"] for w in W]; gr = [w["distinct_groups"] for w in W]
T99 = {23: 2.499867, 72: 2.379}[n - 1]
def st(x):
    m = sum(x) / n; s = math.sqrt(sum((v - m) ** 2 for v in x) / (n - 1)); return m, s
mo, so = st(ops); mc, sc = st(cl); mg, sg = st(gr); rr = [g / c for g, c in zip(gr, cl)]; mr, sr = st(rr)
mu_p = math.ceil(mo + T99 * so / math.sqrt(n)); c_m = mc - T99 * sc / math.sqrt(n); r_m = mr - T99 * sr / math.sqrt(n)
def board_time(q):
    lp = math.log2(585 / 524288) - 32 + q; lam = -math.log(0.60999)
    G = lam / 2 ** lp; N = G / r_m; B = math.floor(N * (1 + 2 ** -19) / c_m) + 1
    WB = math.floor(B * mu_p * (1 + 2 ** -20)) + 1; R = 2 ** 51
    T = Fraction(WB + R + 6 * B, 2812) + 2 ** 36
    return math.log2(T.numerator) - math.log2(T.denominator)
R40 = 123.90836; R41 = 123.9247; R39LEAD = 116.707
# q choices for the door-paid tail (= published r39 door-paid tail cost):
#  best:  best r39 tail lcb999 (pf_013, best stage-B class)     -> lean/best-case (CLAUDE rule 12)
#  decl:  r39 shipped conservative declared tail q (QDECL)      -> conservative basis
Q = {"best(-74.4242 pf_013 lcb999)": -74.4242, "shipped(-75.49 QDECL)": -75.49}
print("r39 window stats: n=%d mu+=%d c-=%.2f r-=%.6f" % (n, mu_p, c_m, r_m))
print("ref leaders: r39=%.5f  r40=%.5f  r41=%.5f" % (R39LEAD, R40, R41))
for lbl, q in Q.items():
    t = board_time(q)
    print("q %-28s board=%.5f  d_r40=%+.5f  d_r41=%+.5f" % (lbl, t, t - R40, t - R41))
