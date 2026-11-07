# dariia_overlap.py : Dariia's screen.csv (support = words+kicks at steps N, weight cap, status) vs our scan40 census: how many of her
# decided supports we also decided, agreement, and how many are new to us. Read-only on both sides. Run with python -I.
import csv, glob, collections, os
D = 'unsat_1027/unsat_data_2026-10-27/screen.csv'
ours = {}
for f in glob.glob('../../game/climber/guided/scan40/census_*.tsv'):
    for l in open(f):
        p = l.rstrip('\n').split('\t')
        if len(p) < 4 or not p[0].isdigit(): continue
        R = int(p[0]); W = tuple(sorted(int(x) for x in p[1].split(',') if x)); K = tuple(sorted(int(x) for x in p[2].split(',') if x))
        if p[3] in ('SAT', 'UNSAT'): ours[(R, W, K)] = p[3]
th = collections.Counter(); keys = {}
for r in csv.DictReader(open(D)):
    W = tuple(sorted(int(x) for x in r['words'].split())); K = tuple(sorted(int(x) for x in r['kicks'].split())); R = int(r['steps'])
    k = (R, W, K); th[(r['status'])] += 1
    if r['status'] in ('SAT', 'UNSAT'): keys.setdefault(k, set()).add(r['status'])
both = {k: (ours[k], v) for k, v in keys.items() if k in ours}
agree = sum(1 for k, (o, v) in both.items() if o in v); dis = [(k, o, v) for k, (o, v) in both.items() if o not in v]
print('Dariia rows by status', dict(th)); print('her decided supports (distinct)', len(keys), '| ours decided', len(ours))
print('overlap', len(both), 'agree', agree, 'disagree', len(dis)); print('disagreements', dis[:8])
new = [k for k in keys if k not in ours]; print('her supports NEW to us', len(new), '| by R', sorted(collections.Counter(k[0] for k in new).items()))
us_only_R40 = sum(1 for k in ours if k[0] == 40 and k not in keys); print('ours not in hers (R40)', us_only_R40)
