# trail_families.py (HASH$CyberAxe 10-31: "reduce to families so we don't scan so many each time"): group library trails by message-difference shape
# (which W rows 0..K carry u/n differences) + step count; one representative per family = the fastest IV_GATE SAT member. Writes FAMILIES.tsv.
import os, re, collections
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
L = os.path.join(R, 'game', 'climber', 'guided', 'chars', 'library')
gate = {}
for l in open(os.path.join(L, 'IV_GATE.tsv')):
    p = l.rstrip('\n').split('\t')
    if len(p) >= 3: gate[p[0]] = (p[1], p[2].split()[0])
fam = collections.defaultdict(list)
for f in os.listdir(L):
    if not f.endswith('.xml'): continue
    t = f[:-4]; s = open(os.path.join(L, f), encoding='utf-8', errors='ignore').read()
    rows = re.findall(r'^\s*(\d+)\s+A:\s*\S{32}\s+E:\s*\S{32}\s+W:\s*(\S{32})', s, re.M)
    sig = tuple(int(r) for r, w in rows if re.search('[un]', w))
    fam[(t.split('_')[0], sig)].append(t)
out = []
for (steps, sig), ts in fam.items():
    sat = [(float(gate[t][1]), t) for t in ts if t in gate and gate[t][0] == 'SAT' and gate[t][1].replace('.', '').isdigit()]
    rep = min(sat)[1] if sat else ts[0]
    out.append((steps, len(ts), len(sat), ','.join(map(str, sig)), rep))
out.sort(key=lambda x: (-x[2], -x[1]))
open(os.path.join(L, 'FAMILIES.tsv'), 'w').write('steps\tmembers\tsat_at_row12\tW_diff_rows\trepresentative\n' + ''.join('\t'.join(map(str, o)) + '\n' for o in out))
print(len(fam), 'families from', sum(len(v) for v in fam.values()), 'trails; with a row-12 SAT member:', sum(1 for o in out if o[2] > 0))
