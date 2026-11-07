#!/usr/bin/env python3
"""indep_verify.py MAP DECODE_TXT
Second, encoder-independent re-check of a kissat closure model. Reads n / wbits / chaining from the .map and the
'M1: W=', 'chain=' lines from the saved output of `sha_cnf.py --decode`; recomputes the n-round scaled compression
in plain Python (team verify_witness.py conventions: rotations max(1,(k*w+16)//32), constants truncated) with no
code shared with sha_cnf.py. Prints INDEP VERIFIED only if some message word differs and all 8 output words agree."""
import json, re, sys
mp = json.load(open(sys.argv[1])); n = mp['n']; w = mp.get('wbits', 32); M = (1 << w) - 1
txt = open(sys.argv[2]).read()
K32 = [0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,
0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,
0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,
0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,
0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2]
sc = lambda k: max(1, (k * w + 16) // 32)
ror = lambda x, r: ((x >> r) | (x << (w - r))) & M
s0 = lambda x: ror(x, sc(7)) ^ ror(x, sc(18)) ^ (x >> sc(3))
s1 = lambda x: ror(x, sc(17)) ^ ror(x, sc(19)) ^ (x >> sc(10))
S0 = lambda x: ror(x, sc(2)) ^ ror(x, sc(13)) ^ ror(x, sc(22))
S1 = lambda x: ror(x, sc(6)) ^ ror(x, sc(11)) ^ ror(x, sc(25))
def comp(m, cv):
    W = list(m)
    for t in range(16, n): W.append((s1(W[t-2]) + W[t-7] + s0(W[t-15]) + W[t-16]) & M)
    a, b, c, d, e, f, g, h = cv
    for t in range(n):
        T1 = (h + S1(e) + ((e & f) ^ (~e & g)) + (K32[t] & M) + W[t]) & M
        T2 = (S0(a) + ((a & b) ^ (a & c) ^ (b & c))) & M
        a, b, c, d, e, f, g, h = (T1 + T2) & M, a, b, c, (d + T1) & M, e, f, g
    return [(x + y) & M for x, y in zip(cv, [a, b, c, d, e, f, g, h])]
pairs = {}
for k in '12':
    mw = re.search(rf'^M{k}: W=([0-9a-f ]+)$', txt, re.M); mc = re.search(rf'^M{k}: W=.*\n\s*chain=([0-9a-f ]+)$', txt, re.M)
    if not (mw and mc): print("INDEP: decode lines for M%s not found" % k); sys.exit(2)
    pairs[k] = ([int(x, 16) for x in mw.group(1).split()], [int(x, 16) for x in mc.group(1).split()])
o1, o2 = comp(*pairs['1']), comp(*pairs['2'])
diff = [t for t in range(16) if pairs['1'][0][t] != pairs['2'][0][t]]
print(f"INDEP n={n} w={w} chaining={mp['chaining']}: differing message words {diff}; outputs equal: {o1 == o2}")
print("INDEP VERIFIED" if diff and o1 == o2 else "INDEP NOT VERIFIED")
