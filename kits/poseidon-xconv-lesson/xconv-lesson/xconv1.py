# power-of-two length (r15): pruned first/last two layers fused with the row copies
from geo import F, oc, runsplit
from xconv import ROW, VD_GROUP
def _hb(x, y): return 3 if (x and y) else (2 if (x or y) else 0)
def first1(L, K, cnt, b=9):
    q = L >> 2; n2 = max(0, K - q); n1 = min(K, q) - n2; n0 = q - n1 - n2; base = oc(4) + b + F(cnt)
    return n2 * (base + 2 * ROW + 24 * cnt) + n1 * (base + ROW + 15 * cnt) + n0 * (oc(4) + 3 + F(cnt) + 8 * cnt) + 3 * q + 2
def last1(L, K, cnt, b=9):
    q = L >> 2; pts = sorted(set([0, q] + [min(q, max(0, x - j * q)) for j in range(4) for x in (K, 2 * K)])); c = 0
    for lo, hi in zip(pts, pts[1:]):
        if hi <= lo: continue
        need = [K <= lo + j * q < 2 * K for j in range(4)]; assert need == [K <= hi - 1 + j * q < 2 * K for j in range(4)]
        P1 = need[0] or need[2]; P2 = need[1] or need[3]; s = sum(need)
        if not (P1 or P2): continue
        pp = 8 + 2 * _hb(P1, P2) + _hb(need[0], need[2]) + _hb(need[1], need[3]) + 4 * s
        c += (hi - lo) * (oc(4) + b + F(cnt) + s * ROW + pp * cnt)
    return c + 3 * q + 2
def group(L, K, cnt):
    a = L.bit_length() - 1; assert L == 1 << a and 2 * K <= L
    run, split = runsplit(a, a - 4, cnt)   # layers 2 .. a-3 (l0 offset ignored for twiddle 1 = fewer savings, upper bound)
    mc = L >> 2; mid = mc * (oc(4) + 13 + 36 * cnt + F(cnt) + 3) + 2 - mc * 6 * cnt
    f, l = first1(L, K, cnt), last1(L, K, cnt)
    return dict(first=f, run=run, split=split, mid=mid, last=l, tot=f + 2 * run + mid + l)
def phase(L, K, cnt, pos, margin=0):
    ng = pos // cnt; g = group(L, K, cnt)
    return 2 * (7 * K + 2) + ng * (VD_GROUP + g['tot'] + margin) + 3 * ng + 2, g
if __name__ == '__main__':
    import math
    K = 55512; GEO = 37111614155774934; cnt = 1024
    P, g = phase(1 << 17, K, cnt, 1 << 32); print('model', P, 'akki', GEO, 'resid/group', (GEO - P) / (1 << 22), g)
