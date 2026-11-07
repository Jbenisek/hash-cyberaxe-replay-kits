#!/usr/bin/env python3
"""fulltrail.py PAIRFILE R OUT.xml : the honest full-trail question for a schedule pair at height R - every W row carries the pair's
signed difference (expanded to R words), every state row 0..R-5 is free ('?'), rows -4..-1 and R-4..R-1 carry no difference ('-'),
values free, chaining value free. SAT = a complete R-step semi-free-start pair on that word pattern. HASH$CyberAxe 10-30 06:5x."""
import sys
pf, R, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
M = 0xffffffff
def Rr(x, n): return ((x >> n) | (x << (32 - n))) & M
def expand(w):
    W = list(w)
    for t in range(16, R):
        s0 = Rr(W[t-15], 7) ^ Rr(W[t-15], 18) ^ (W[t-15] >> 3); s1 = Rr(W[t-2], 17) ^ Rr(W[t-2], 19) ^ (W[t-2] >> 10)
        W.append((W[t-16] + s0 + W[t-7] + s1) & M)
    return W
sg = lambda x, y: ''.join('-' if ((x >> i) & 1) == ((y >> i) & 1) else ('u' if (x >> i) & 1 else 'n') for i in range(31, -1, -1))
m = {}
for ln in open(pf):
    p = ln.split()
    if p and p[0] in ('M1', 'M2'): m[p[0]] = [int(x, 16) for x in p[1:17]]
X1, X2 = expand(m['M1']), expand(m['M2'])
Z, Q = '-' * 32, '?' * 32
L = ['<config>', '<options><option name="f" value="sha2"/><option name="n" value="%d"/><option name="w" value="32"/></options>' % R, '<char value="']
for t in range(-4, R):
    a = Z if (t < 0 or t >= R - 4) else Q
    L.append('%3d A: %s E: %s' % (t, a, a) + (' W: %s' % sg(X1[t], X2[t]) if t >= 0 else ''))
open(out, 'w').write('\n'.join(L + ['"/>', '</config>']) + '\n')
print('rows', R + 4, 'W diff rows', [t for t in range(R) if X1[t] != X2[t]])
