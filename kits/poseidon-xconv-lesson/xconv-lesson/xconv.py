# exact count of the geometric phase (group-buffer convolution) under proof.md 4.2 charges; validated against 4.6's GEO at Lx
import math
from geo import F, COL, oc, runsplit
OB3 = (7, 22); ROW = 2 + 6 + 2; VD_GROUP = 20
def first3(L, Kin, cnt):
    n = L // 3; c2 = max(0, Kin - n); c1 = min(Kin, n) - c2; c0 = n - c1 - c2
    base = oc(3) + OB3[0] + F(cnt)
    return c2 * (base + 2 * ROW + 19 * cnt) + c1 * (base + ROW + 10 * cnt) + c0 * (base + 6 * cnt) + 3 * n + 2
def last3(L, Kin, cnt):
    n = L // 3; K = Kin
    pts = sorted(set([0, n] + [min(n, max(0, x - j * n)) for j in range(3) for x in (K, 2 * K)])); c = 0
    for lo, hi in zip(pts, pts[1:]):
        if hi <= lo: continue
        need = [K <= lo + j * n < 2 * K for j in range(3)]; assert need == [K <= hi - 1 + j * n < 2 * K for j in range(3)]
        s = sum(need)
        if not s: continue
        ar = {1: 4, 2: 8, 3: 10}[s]
        c += (hi - lo) * (oc(3) + OB3[0] + F(cnt) + s * ROW + (6 + ar + 4 * s) * cnt)
    return c + 3 * n + 2
def group(L, Kin, cnt):
    n = L // 3; a = n.bit_length() - 1; assert n == 1 << a and Kin <= 2 * n and 2 * Kin <= L
    run, split = runsplit(a, a - 2, cnt)
    mc = n >> 2; mid = mc * (oc(4) + 13 + 36 * cnt + F(cnt) + 3) + 2 - mc * 6 * cnt
    return dict(first=first3(L, Kin, cnt), run=run, split=split, mid=mid, last=last3(L, Kin, cnt),
                tot=first3(L, Kin, cnt) + 6 * run + 3 * mid + last3(L, Kin, cnt))
def phase(L, Kin, cnt, pos, margin=0):
    ng = pos // cnt; g = group(L, Kin, cnt)
    return 2 * (7 * Kin + 2) + ng * (VD_GROUP + g['tot'] + margin) + 3 * ng + 2, g
if __name__ == '__main__':
    K = 173472348; GEO = 186964682507269812494; cnt = 1 << 10
    P, g = phase(3 << 27, K, cnt, 1 << 32)
    print('model GEO(Lx)', P, 'akki', GEO, 'per-group residual', (GEO - P) / (1 << 22))
    P2, g2 = phase(3 << 28, 2 * K, cnt, 1 << 31, margin=1 << 27)
    print('X2', P2, g2['split'], g2, 'vs 1.5GEO+14n1', (3 * GEO + 1) // 2 + 14 * K * (1 << 32), 'scaling', GEO * 29 // 28)
