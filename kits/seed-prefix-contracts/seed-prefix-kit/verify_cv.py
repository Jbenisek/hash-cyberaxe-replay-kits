#!/usr/bin/env python3
"""verify_cv.py (= verify_ivprefix run from the file's OWN chaining value; use for free-CV pairs)  verify17.py WITNESS.txt TRAIL.xml k : independent check of a standard-IV prefix witness — run M1/M2 from the SHA-256 IV with own step
code and compare rows 0..k (A/E signed differences and value bits) against the characteristic. Prints per-row OK/FAIL."""
import sys, re
M = 0xffffffff; R = lambda x, n: ((x >> n) | (x << (32 - n))) & M
K = [0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2]
IV = [0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19]
def run(cv, W, n):
    w = list(W)
    for t in range(16, n): w.append((R(w[t-2],17)^R(w[t-2],19)^(w[t-2]>>10)) + w[t-7] + (R(w[t-15],7)^R(w[t-15],18)^(w[t-15]>>3)) + w[t-16] & M)
    a,b,c,d,e,f,g,h = cv; A=[]; E=[]
    for t in range(n):
        T1 = (h + (R(e,6)^R(e,11)^R(e,25)) + ((e&f)^(~e&g)) + K[t] + w[t]) & M; T2 = ((R(a,2)^R(a,13)^R(a,22)) + ((a&b)^(a&c)^(b&c))) & M
        h,g,f,e,d,c,b,a = g,f,e,(d+T1)&M,c,b,a,(T1+T2)&M; A.append(a); E.append(e)
    return A, E, w
txt = open(sys.argv[1]).read(); k = int(sys.argv[3])
m1 = [int(x,16) for x in re.search(r'M1: W=((?:[0-9a-f]{8}\s*){16})', txt).group(1).split()]
m2 = [int(x,16) for x in re.search(r'M2: W=((?:[0-9a-f]{8}\s*){16})', txt).group(1).split()]
chain = [int(x,16) for x in re.search(r'(?:chain|cv)=((?:[0-9a-f]{8}\s*){8})', txt).group(1).split()]
print("chain is the standard IV:", chain == IV)
A1,E1,w1 = run(chain, m1, 39); A2,E2,w2 = run(chain, m2, 39)
RX = re.compile(r'^\s*(-?\d+)\s+A:\s*(\S{32})\s+E:\s*(\S{32})', re.M)
rows = {int(m.group(1)): (m.group(2), m.group(3)) for m in RX.finditer(open(sys.argv[2]).read())}
def check(cond, x, y):
    bad = 0
    for j, ch in enumerate(cond):
        b = 31 - j; p, q = (x >> b) & 1, (y >> b) & 1
        if ch == '-' and p != q: bad += 1
        elif ch == 'u' and not (p == 1 and q == 0): bad += 1
        elif ch == 'n' and not (p == 0 and q == 1): bad += 1
        elif ch == 'x' and p == q: bad += 1
        elif ch in '01' and not (p == q == int(ch)): bad += 1
    return bad
tot = 0
for t in range(0, k + 1):
    ba = check(rows[t][0], A1[t], A2[t]); be = check(rows[t][1], E1[t], E2[t]); tot += ba + be
    print(f"row {t:2d}: A {'OK' if ba == 0 else 'FAIL(%d)' % ba}  E {'OK' if be == 0 else 'FAIL(%d)' % be}")
print("TOTAL violations rows 0..%d: %d  -> %s" % (k, tot, "WITNESS VERIFIED" if tot == 0 else "WITNESS INVALID"))
