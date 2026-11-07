# mk_tap.py OUT N DIFFW STATEFREE : xml with W rows '?' on DIFFW (comma list) else '-', chaining '-', state rows in STATEFREE
# ("a-b") '?', other state rows '-' (last 4 rows always '-').
import sys
out, n, dw, sf = sys.argv[1], int(sys.argv[2]), {int(x) for x in sys.argv[3].split(',')}, sys.argv[4]
lo, hi = map(int, sf.split('-'))
L = ['<config>', '<options>', '  <option name="f" value="sha2"/>', f'  <option name="n" value="{n}"/>', '  <option name="w" value="32"/>', '</options>', '<char value="']
for t in range(-4, 0): L.append(f"{t:3d} A: {'-'*32} E: {'-'*32}")
for t in range(n):
    s = '?' * 32 if lo <= t <= hi and t < n - 4 else '-' * 32
    w = '?' * 32 if t in dw else '-' * 32
    L.append(f"{t:3d} A: {s} E: {s} W: {w}")
L += ['"/>', '</config>', '']
open(out, 'w').write('\n'.join(L))
