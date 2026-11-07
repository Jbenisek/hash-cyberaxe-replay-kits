# lawbase.py PAIRFILE OUT.xml R E : base from research's finish law for last lit row E: state free rows 0..E-8, A equal from row E-7 (rows E-7..E-4 E-only), A and E equal from row E-3 to R-1
import sys
M = 0xffffffff
Rr = lambda x, n: ((x >> n) | (x << (32 - n))) & M
def expand(W16, n):
    W = list(W16)
    for t in range(16, n):
        s0 = Rr(W[t-15], 7) ^ Rr(W[t-15], 18) ^ (W[t-15] >> 3); s1 = Rr(W[t-2], 17) ^ Rr(W[t-2], 19) ^ (W[t-2] >> 10)
        W.append((W[t-16] + s0 + W[t-7] + s1) & M)
    return W
L = {l.split()[0]: [int(x, 16) for x in l.split()[1:]] for l in open(sys.argv[1]) if l[:2] in ('M1', 'M2')}
out = sys.argv[2]; RT = int(sys.argv[3]); E = int(sys.argv[4])
W1, W2 = expand(L['M1'], 64), expand(L['M2'], 64)
def wrow(t): return ''.join('-' if ((W1[t] >> b) & 1) == ((W2[t] >> b) & 1) else ('u' if (W1[t] >> b) & 1 else 'n') for b in range(31, -1, -1))
Z, Q = '-' * 32, '?' * 32
rows = [' %2d A: %s E: %s' % (t, Z, Z) for t in range(-4, 0)]
for t in range(RT):
    a = Q if t < E - 7 else Z; e = Q if t < E - 3 else Z
    rows.append(' %2d A: %s E: %s W: %s' % (t, a, e, wrow(t)))
open(out, 'w').write('<config>\n<options><option name="f" value="sha2"/><option name="n" value="%d"/><option name="w" value="32"/></options>\n<char value="\n' % RT + '\n'.join(rows) + '\n"/>\n</config>\n')
