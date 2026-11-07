import re, os, sys
tests = []
for f in ('tests.txt', 'tests2.txt'):
    if os.path.exists(f): tests += [l.split('|',1) for l in open(f).read().splitlines() if l and not l.startswith('#')]
def load(n):
    p = f'out/{n}.txt'
    if not os.path.exists(p): return None
    t = open(p).read(); d = {}
    d['exit'] = (re.findall(r'^exit (\d+)', t, re.M) or ['?'])[-1]
    d['pre'] = [float(x) for x in re.findall(r'prefix log2 P\(rows 6\.\.21\) = (-?[\d.]+)', t)]
    d['vt'] = {int(m[1]): (int(m[2]), int(m[3]), int(m[4])) for m in re.finditer(r'VTAG class (\d) .*? N (\d+) CELLS (\d+) EXACT (\d+)', t)}
    d['false'] = (re.findall(r'false collisions (\d+)', t) or ['?'])[-1]
    d['frow'] = {int(a): int(b) for a, b in re.findall(r'VTAG violator first failing base row (\d+): (\d+)', t)}
    vs = {}
    for r, k in re.findall(r'VSTAGE row (\d+) violators alive after resampling (\d+) of', t): vs.setdefault(int(r), []).append(int(k))
    d['vs'] = {r: sum(k) for r, k in vs.items()}
    d['e16'] = (re.findall(r'E16 set under the prefix conditions: (\d+)', t) or ['?'])[0]
    return d
for n, r in tests:
    d = load(n)
    if not d or not d['vt']: print(f'{n:8s} NOT DONE exit {d["exit"] if d else "-"}'); continue
    N0, C0, ex0 = d['vt'][0]; n1, c1, ex1 = d['vt'][1]
    ub = 1 + 3/ex0 if ex0 else float('nan')
    alive = [k for k, v in sorted(d['vs'].items()) if v]
    die = (max(alive) + 1) if alive else None
    verdict = ('NO-VIOLATOR' if n1 == 0 else ('NECESSARY' if ex1 == 0 else 'LEVER?'))
    print(f'{n:8s} {verdict:11s} seeds {len(d["pre"])} E16set {d["e16"]} prefix {sum(d["pre"])/max(1,len(d["pre"])):.3f} N0 {N0} EX0 {ex0} N1 {n1} EX1 {ex1} UBgain {ub:.4f} gain x{(ex0+ex1)/ex0 if ex0 else 0:.4f} frow {d["frow"]} alive_rows {alive} die_at {die} false {d["false"]} exit {d["exit"]}')
