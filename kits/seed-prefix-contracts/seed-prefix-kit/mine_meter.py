#!/usr/bin/env python3
# mine_meter.py (Plumb 11-01): closure distance of every game MINE pair (pair with chain1/chain2 = the shared free starting state).
# Runs both messages R real SHA-256 rounds from that state and counts differing bits of A and E at the closure rows R-4..R-1
# (a collision needs all of them zero). first = bits wrong at row R-4 (the first pinned round); total = over the 4 rows. Lower is closer.
# bits_over_chance = 128 - closure_bits_total (chance = 128 of 256 wrong; positive = closer than chance). History appended to MINE_METER_HISTORY.tsv.
# tz_* = trailing zeros (2-adic depth) of the modular A/E difference at row R-4 (the HASH$CyberAxe team's carry-chain lead; chance mean ~1).
# Writes research/runs_1101/funnel/MINE_METER.tsv, closest first.
import json, glob, os
R0 = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
M = 0xffffffff; rot = lambda x, n: ((x >> n) | (x << (32 - n))) & M
K = [0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
     0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
     0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
     0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2]
def run(W, cv, n):
    w = [int(x, 16) for x in W]
    for t in range(16, n): w.append(((rot(w[t-2],17)^rot(w[t-2],19)^(w[t-2]>>10)) + w[t-7] + (rot(w[t-15],7)^rot(w[t-15],18)^(w[t-15]>>3)) + w[t-16]) & M)
    a,b,c,d,e,f,g,h = [int(x, 16) for x in cv]; A = []; E = []
    for t in range(n):
        t1 = (h + (rot(e,6)^rot(e,11)^rot(e,25)) + ((e&f)^(~e&g)) + K[t] + w[t]) & M; t2 = ((rot(a,2)^rot(a,13)^rot(a,22)) + ((a&b)^(a&c)^(b&c))) & M
        h,g,f,e,d,c,b,a = g,f,e,(d+t1)&M,c,b,a,(t1+t2)&M; A.append(a); E.append(e)
    return A, E
rows = []; seen = set()
for f in sorted(glob.glob(os.path.join(R0,'game','engine','data','raw','web_*.jsonl'))) + [os.path.join(R0,'runs_1031','wcost','owner_shots_1031.jsonl')]:
    for l in open(f, encoding='utf-8', errors='ignore'):
        if 'chain1' not in l: continue
        try: d = json.loads(l)
        except Exception: continue
        p = d.get('pair') or {}
        if not (p.get('chain1') and p.get('chain2') and len(p.get('M1',[])) == 16 and d.get('R')): continue
        sid = d.get('shot_id'); 
        if sid in seen: continue
        seen.add(sid); n = int(d['R'])
        if p['chain1'] != p['chain2']: continue
        A1,E1 = run(p['M1'], p['chain1'], n); A2,E2 = run(p['M2'], p['chain2'], n)
        bits = [bin(A1[i]^A2[i]).count('1') + bin(E1[i]^E2[i]).count('1') for i in range(n-4, n)]
        tz = lambda x: 32 if x == 0 else (x & -x).bit_length() - 1
        r0 = n-4; tzA = tz((A1[r0]-A2[r0]) & M); tzE = tz((E1[r0]-E2[r0]) & M)
        rows.append((bits[0], sum(bits), 128 - sum(bits), tzA, tzE, n, d.get('level'), d.get('knob'), ','.join(map(str,d.get('words',[]))), ','.join(map(str,d.get('kicks') or [])), sid))
rows.sort()
out = os.path.join(R0,'runs_1101','funnel','MINE_METER.tsv')
with open(out,'w',newline='\n') as o:
    o.write('first_row_bits\tclosure_bits_total\tbits_over_chance\ttz_dA_first\ttz_dE_first\tR\tlevel\tknob\twords\tkicks\tshot_id\n')
    for r in rows: o.write('\t'.join(map(str,r))+'\n')
import datetime
with open(os.path.join(R0,'runs_1101','funnel','MINE_METER_HISTORY.tsv'),'a',newline='\n') as h:
    for r in rows: h.write(datetime.datetime.now().strftime('%Y-%m-%d %H:%M')+'\t'+'\t'.join(map(str,r))+'\n')
print('mine pairs measured:', len(rows), '| best bits over chance:', max((r[2] for r in rows), default=None))
