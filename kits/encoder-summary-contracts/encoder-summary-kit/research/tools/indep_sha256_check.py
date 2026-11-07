#!/usr/bin/env python3
"""indep_sha256_check.py (HASH$CyberAxe 2026-10-30): independent SHA-256 written from FIPS 180-4, gated against hashlib.
1) known-answer gate: N random one-block messages, our compression with the standard IV vs hashlib.sha256 digests.
2) reduced-step check of a pair: python3 indep_sha256_check.py PAIRFILE [steps...]
   PAIRFILE lines: 'IV <8 hex>', 'M1 <16 hex>', 'M2 <16 hex>' (as in owner_r42/pub39_published.pair.txt).
   Prints, per step count, how many of the 8 feed-forward output words are equal.
3) step inversion: with equal message words each step is a bijection (forward then back restores the state)."""
import hashlib, random, struct, sys
M = 0xffffffff
K = [0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
     0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
     0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
     0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2]
IV0 = [0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19]
R = lambda x, n: ((x >> n) | (x << (32 - n))) & M

def expand(W16, n):
    W = list(W16)
    for t in range(16, n):
        W.append(((R(W[t-2],17) ^ R(W[t-2],19) ^ (W[t-2] >> 10)) + W[t-7] + (R(W[t-15],7) ^ R(W[t-15],18) ^ (W[t-15] >> 3)) + W[t-16]) & M)
    return W

def step(s, t, Wt):
    a, b, c, d, e, f, g, h = s
    T1 = (h + (R(e,6) ^ R(e,11) ^ R(e,25)) + ((e & f) ^ (~e & g)) + K[t] + Wt) & M
    T2 = ((R(a,2) ^ R(a,13) ^ R(a,22)) + ((a & b) ^ (a & c) ^ (b & c))) & M
    return ((T1 + T2) & M, a, b, c, (d + T1) & M, e, f, g)

def back(s, t, Wt):
    a2, b2, c2, d2, e2, f2, g2, h2 = s
    a, b, c, e, f, g = b2, c2, d2, f2, g2, h2
    T2 = ((R(a,2) ^ R(a,13) ^ R(a,22)) + ((a & b) ^ (a & c) ^ (b & c))) & M
    T1 = (a2 - T2) & M; d = (e2 - T1) & M
    h = (T1 - (R(e,6) ^ R(e,11) ^ R(e,25)) - ((e & f) ^ (~e & g)) - K[t] - Wt) & M
    return (a, b, c, d, e, f, g, h)

def compress(cv, W16, n=64):
    W = expand(W16, max(n, 16)); s = tuple(cv)
    for t in range(n): s = step(s, t, W[t])
    return tuple((x + y) & M for x, y in zip(s, cv))

def gate(N=2000):
    ok = 0
    for _ in range(N):
        msg = bytes(random.getrandbits(8) for _ in range(random.randint(0, 55)))
        pad = msg + b'\x80' + b'\x00' * ((55 - len(msg)) % 64) + struct.pack('>Q', 8 * len(msg))
        ok += struct.pack('>8I', *compress(IV0, list(struct.unpack('>16I', pad)))) == hashlib.sha256(msg).digest()
    return ok, N

if __name__ == '__main__':
    ok, N = gate(); print(f"gate: {ok}/{N} digests equal to hashlib")
    if ok != N: sys.exit("gate failed - do not trust anything below")
    if len(sys.argv) > 1:
        L = {l.split()[0]: [int(x, 16) for x in l.split()[1:]] for l in open(sys.argv[1]) if l[:2] in ('IV', 'M1', 'M2')}
        for n in [int(x) for x in sys.argv[2:]] or [36, 37, 38, 39, 40, 41]:
            o1, o2 = compress(L['IV'], L['M1'], n), compress(L['IV'], L['M2'], n)
            print(f"{n} steps: output words equal {sum(x == y for x, y in zip(o1, o2))}/8")
    ok = 0
    for _ in range(20000):
        s = tuple(random.getrandbits(32) for _ in range(8)); Ws = [random.getrandbits(32) for _ in range(9)]; x = s
        for t in range(1, 9): x = step(x, t, Ws[t])
        for t in range(8, 0, -1): x = back(x, t, Ws[t])
        ok += x == s
    print(f"step inversion: {ok}/20000 states restored")
