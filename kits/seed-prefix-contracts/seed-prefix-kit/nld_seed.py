#!/usr/bin/env python3
# nld_seed.py PAIR.txt R FIX_TO OUT.xml VALUE_ROWS [SETUP.xml]
# Like pair2char.py, but for the rows in VALUE_ROWS (e.g. "7-16") it writes the pair's actual bit
# VALUES as 0/1 conditions wherever the two messages agree, and keeps the signed difference (u/n)
# where they disagree. All other rows behave exactly as in pair2char.py.

# Publication path adapter: resolve data paths from the extracted source tree.
def _hca_public_path_text(value):
    if "__HCA_WORKSPACE__/" not in value:
        return value
    import os as _hca_os
    from pathlib import Path as _hca_Path
    root = _hca_os.environ.get("HASHCYBERAXE_WORKSPACE")
    if root is None:
        here = _hca_Path(__file__).resolve().parent
        root = next((str(p) for p in (here, *here.parents) if (p / "research").is_dir()), None)
    if root is None:
        raise FileNotFoundError("Extract the research source tree, or set HASHCYBERAXE_WORKSPACE to its archive directory.")
    return value.replace("__HCA_WORKSPACE__/", str(_hca_Path(root).resolve()).replace("\\", "/") + "/")

import sys, re, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mine_meter.py')).read().split('rows = []')[0].replace('os.path.abspath(__file__)', "'.'")
ns = {}; exec(src, ns); run = ns['run']; M = 0xffffffff
pf, R, FIX, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
vr_arg = sys.argv[5] if len(sys.argv) > 5 else ''
setup = sys.argv[6] if len(sys.argv) > 6 else _hca_public_path_text('__HCA_WORKSPACE__/research/runs_1031/boomtrails/R40a_ft26.xml')
def parse_rows(s):
    out = set()
    for part in s.split(','):
        part = part.strip()
        if not part: continue
        if '-' in part:
            a, b = part.split('-'); out.update(range(int(a), int(b) + 1))
        else:
            out.add(int(part))
    return out
VALUE_ROWS = parse_rows(vr_arg)
t = open(pf).read(); W = re.findall(r'W=((?:[0-9a-f]{8}\s*){16})', t); C = re.findall(r'chain=((?:[0-9a-f]{8}\s*){8})', t)
W1, W2 = W[0].split(), W[1].split(); C1 = C[0].split(); C2 = C[1].split() if len(C) > 1 else C1
def full(Wh, cv):
    A, E = run(Wh, cv, R); w = [int(x, 16) for x in Wh]
    for i in range(16, R): w.append(((((w[i-2]>>17)|(w[i-2]<<15))&M ^ ((w[i-2]>>19)|(w[i-2]<<13))&M ^ (w[i-2]>>10)) + w[i-7] + ((((w[i-15]>>7)|(w[i-15]<<25))&M) ^ (((w[i-15]>>18)|(w[i-15]<<14))&M) ^ (w[i-15]>>3)) + w[i-16]) & M)
    c = [int(x, 16) for x in cv]; pre = {-1: (c[0], c[4]), -2: (c[1], c[5]), -3: (c[2], c[6]), -4: (c[3], c[7])}
    return {**{k: v for k, v in pre.items()}, **{i: (A[i], E[i]) for i in range(R)}}, w
S1, w1 = full(W1, C1); S2, w2 = full(W2, C2)
sg = lambda a, b: ''.join('-' if not ((a ^ b) >> (31 - j)) & 1 else ('u' if (a >> (31 - j)) & 1 else 'n') for j in range(32))
# value mode: agree -> actual 0/1, differ -> signed diff u/n
sgv = lambda a, b: ''.join((('1' if (a >> (31 - j)) & 1 else '0') if not ((a ^ b) >> (31 - j)) & 1 else ('u' if (a >> (31 - j)) & 1 else 'n')) for j in range(32))
rows = []
for i in range(-4, R):
    sgf = sgv if i in VALUE_ROWS else sg
    if i <= FIX or i in VALUE_ROWS:
        a, e = sgf(S1[i][0], S2[i][0]), sgf(S1[i][1], S2[i][1])
    elif i >= R - 4 and not os.environ.get('NOZERO'):
        a = e = '-' * 32
    else:
        a = e = '?' * 32
    wstr = (f' W: {(sgv if i in VALUE_ROWS else sg)(w1[i], w2[i])}' if i >= 0 else '')
    rows.append(f' {i:2d} A: {a} E: {e}' + wstr)
s = open(setup).read(); blk = s[s.index('"/>', s.index('<char value=')) + 3:s.rindex('</config>')]
open(out, 'w', newline='\n').write('<config>\n<options><option name="f" value="sha2"/><option name="n" value="%d"/><option name="w" value="32"/></options>\n<char value="\n' % R + '\n'.join(rows) + '\n"/>' + blk + '</config>\n')
print(out, 'R', R, 'fixed rows -4..%d, value rows %s, free %d..%d, zero %d..%d' % (FIX, sorted(VALUE_ROWS), FIX + 1, R - 5, R - 4, R - 1))
