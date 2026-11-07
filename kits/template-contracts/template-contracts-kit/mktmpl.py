import re, sys, json, os, difflib
# mktmpl.py <out> <file-rel> <rowdir>...  -> <out>/<base>.tmpl + <out>/<base>.vals.json
# Rows are aligned to the first row (difflib on number-blind lines). Lines equal in every row stay fixed text.
# Lines present in every row whose only differences are numbers keep their text and get number slots {{sN}}.
# Other differing lines become {{WN}} (whole line); lines missing in some rows and extra lines become block slots {{BN}}
# on a line of their own (empty value = no lines).
out, rel, rows = sys.argv[1], sys.argv[2], sys.argv[3:]
NUM = re.compile(r'(?:\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b|\b[0-9a-f]{8}\b|\d[\d,]*(?:\.\d+)?(?:e-?\d+)?)')
def key(r):
    parts = [p for p in r.replace('\\', '/').rstrip('/').split('/') if p]
    rid = [p for p in parts if re.fullmatch(r'r\d+\w*', p)]
    return rid[-1] if rid else [p for p in parts if p != 'pkg'][-1]
T = {r: open(os.path.join(r, rel), encoding='utf-8').read().split('\n') for r in rows}
base = T[rows[0]]; n = len(base)
sk = lambda l: NUM.sub('#', l)
# per row: mapped[i] = row line for base line i (or None); ins[i] = row lines inserted before base line i (i == n: at the end)
M, I = {}, {}
for r in rows:
    mp, ins = [None] * n, [[] for _ in range(n + 1)]
    sm = difflib.SequenceMatcher(None, [sk(l) for l in base], [sk(l) for l in T[r]], autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == 'equal':
            for k in range(i2 - i1): mp[i1 + k] = T[r][j1 + k]
        elif op == 'replace':
            m = min(i2 - i1, j2 - j1)
            for k in range(m): mp[i1 + k] = T[r][j1 + k]
            if j2 - j1 > m: ins[i2] += T[r][j1 + m:j2]
        elif op == 'insert':
            ins[i1] += T[r][j1:j2]
    M[r], I[r] = mp, ins
tmpl, vals, cnt = [], {key(r): {} for r in rows}, {'s': 0, 'W': 0, 'B': 0}
def new(kind):
    cnt[kind] += 1; return '%s%d' % (kind, cnt[kind] - 1)
def block(lines_by_row):
    if all(not v for v in lines_by_row.values()): return
    if len({tuple(v) for v in lines_by_row.values()}) == 1:
        tmpl.extend(next(iter(lines_by_row.values()))); return
    k = new('B'); tmpl.append('{{%s}}' % k)
    for r in rows: vals[key(r)][k] = list(lines_by_row[r])
for i in range(n + 1):
    block({r: I[r][i] for r in rows})
    if i == n: break
    line = {r: M[r][i] for r in rows}
    if any(v is None for v in line.values()):
        block({r: [line[r]] if line[r] is not None else [] for r in rows}); continue
    if len(set(line.values())) == 1:
        tmpl.append(base[i]); continue
    if len({sk(v) for v in line.values()}) != 1:
        k = new('W'); tmpl.append('{{%s}}' % k)
        for r in rows: vals[key(r)][k] = line[r]
        continue
    col = {r: NUM.findall(line[r]) for r in rows}
    b, o, pos = line[rows[0]], [], 0
    for j, m in enumerate(NUM.finditer(b)):
        o.append(b[pos:m.start()])
        if len({col[r][j] for r in rows}) == 1: o.append(m.group())
        else:
            k = new('s'); o.append('{{%s}}' % k)
            for r in rows: vals[key(r)][k] = col[r][j]
        pos = m.end()
    o.append(b[pos:]); tmpl.append(''.join(o))
os.makedirs(out, exist_ok=True)
bn = os.path.basename(rel)
open(os.path.join(out, bn + '.tmpl'), 'w', encoding='utf-8', newline='\n').write('\n'.join(tmpl))
json.dump(vals, open(os.path.join(out, bn + '.vals.json'), 'w', encoding='utf-8'), indent=0)
print(bn, 'lines', len(tmpl), 'fixed', sum(1 for l in tmpl if '{{' not in l), 'number slots', cnt['s'], 'whole-line', cnt['W'], 'blocks', cnt['B'])
