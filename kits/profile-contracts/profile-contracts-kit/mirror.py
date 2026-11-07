#!/usr/bin/env python3
"""mirror.py BASE.xml OUTDIR (HASH$CyberAxe 2026-10-30: 'how do the times differ in the mirror; why is no one trying negative space').
Writes sign variants of a signed base: base; mirror (u<->n on every W row = M1/M2 swapped); xexp (expanded rows 16+ sign-free 'x',
the fair control for the flips); flipK (u<->n on message word K only, expanded rows sign-free) for every differing message word.
Same words, same bits, only the signs move. list.txt names the variants."""
import sys, os, re
base, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
t = open(base).read()
if os.environ.get('SCHED') == '1':                       # schedule-only: drop the end-state constraint (A/E rows all free)
    t = re.sub(r'(A: |E: )(\S+)', lambda m: m.group(1) + '?' * len(m.group(2)), t)
if os.environ.get('STATEX') == '1':                     # signed state rows -> sign-free 'x' (flips of W stay comparable when the state carries signs)
    t = re.sub(r'(A: |E: )(\S+)', lambda m: m.group(1) + re.sub('[un]', 'x', m.group(2)), t)
ROW = re.compile(r'^(\s*)(-?\d+)( A: \S+ E: \S+ W: )(\S+)', re.M)
SW = str.maketrans('un', 'nu')
def variant(fn):
    return ROW.sub(lambda m: m.group(1) + m.group(2) + m.group(3) + fn(int(m.group(2)), m.group(4)), t)
diff = [int(m.group(2)) for m in ROW.finditer(t) if 0 <= int(m.group(2)) < 16 and re.search('[un]', m.group(4))]
V = {'base': t, 'mirror': variant(lambda r, w: w.translate(SW))}
unsign = lambda r, w: re.sub('[un]', 'x', w) if r >= 16 else w
V['xexp'] = variant(unsign)
for k in diff:
    V['flip%d' % k] = variant(lambda r, w, k=k: w.translate(SW) if r == k else unsign(r, w))
if len(sys.argv) > 3:                                     # optional: all sign combos over the listed free-sign words (e.g. 10,12,13)
    import itertools
    ks = [int(x) for x in sys.argv[3].split(',')]; V = {'xexp': V['xexp']}
    for r in range(1, len(ks) + 1):
        for S in itertools.combinations(ks, r):
            V['flip' + '_'.join(map(str, S))] = variant(lambda q, w, S=S: w.translate(SW) if q in S else unsign(q, w))
for name, txt in V.items():
    open(os.path.join(out, name + '.xml'), 'w').write(txt)
open(os.path.join(out, 'list.txt'), 'w').write('\n'.join(V) + '\n')
print('variants', len(V), 'differing message words', diff)
