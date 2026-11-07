#!/usr/bin/env python3
"""nw2.py PAIR BAND MODE OUTBASE : "new words" instance (HASH$CyberAxe 10-28; base pinladder/ladder.py).
Identical to nw.py EXCEPT every A and E row strictly BEFORE the pinned middle band is also set to '?' (all 32
bits, both copies); rows inside and after the band are unchanged. Keep the pair's own signed characteristic A/E
rows for the band and after; set EVERY W row to '?' (all 16 message words and every schedule row free). Pin the
pair's middle A/E VALUES (both copies) over one band: BAND in {b0811:rows 8-11, b1215:rows 12-15, b1619:rows
16-19}. MODE real = one clause excluding the pair (the 16 message words, both copies: not all equal to the
pair's) | ctl = no exclusion (control). SIGNED=1, chaining sfs (free start). R = the char's n."""
import sys, os, re, json
HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.normpath(os.path.join(HERE, '..', 'kit')); sys.path.insert(0, KIT)
os.environ['SIGNED'] = '1'
import char_pair_profile as cpp
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
CHARS = os.path.normpath(os.path.join(HERE, '..', 'chars'))
KIN = os.path.join(ROOT, 'outside', 'kepler_in')
OWN = {'pub39': os.path.join(CHARS, 'pin39b_char.xml'),
       'llw39': os.path.join(CHARS, 'llw39_char.xml'),
       'mns38': os.path.join(CHARS, 'mns38_char.xml'),
       'hyb38': os.path.join(CHARS, 'hyb38_pin38_to_pin38b_s17g5.xml')}
WIT = {'pub39': 'angle_pub39_char_w32_WITNESS.json',
       'llw39': 'angle_llw39_char_w32_WITNESS.json',
       'mns38': 'angle_mns38_char_w32_WITNESS.json',
       'hyb38': 'angle_hyb38_s17g5_WITNESS.json'}
BANDS = {'b0811': range(8, 12), 'b1215': range(12, 16), 'b1619': range(16, 20)}


def pair(name):
    w = json.load(open(os.path.join(KIN, WIT[name])))
    cv, m1, m2 = [[int(x, 16) for x in w[k]] for k in ('cv', 'M1', 'M2')]
    R = int(w['R']); pr = cpp.profile(cv, m1, m2, R); assert pr['collision'], name
    return cv, m1, m2, pr, R


def mkchar(name, out, band=None):
    """Copy the pair's own char A/E rows verbatim; set every W content row to '?'. If band given, also set every
    A/E row strictly before the band's first row to '?' (both copies). Return R."""
    txt = open(OWN[name]).read()
    n = int(re.search(r'name="n" value="(\d+)"', txt).group(1))
    q = '?' * 32
    bstart = min(BANDS[band]) if band is not None else None
    L = ['<config>', '<options>', '  <option name="f" value="sha2"/>', f'  <option name="n" value="{n}"/>',
         '  <option name="w" value="32"/>', '</options>',
         f'<comment>newwords2 {name} R={n}: A/E before band free, own char A/E band+after, every W row free</comment>', '<char value="']
    for m in re.finditer(r'^\s*(-?\d+)\s+A:\s*(\S+)\s+E:\s*(\S+)(?:\s+W:\s*(\S+))?', txt, re.M):
        t = int(m.group(1)); a, e = m.group(2), m.group(3)
        if bstart is not None and t >= 0 and t < bstart:
            a = q; e = q
        if t >= 0:
            L.append(f"{t:3d} A: {a} E: {e} W: {q}")
        else:
            L.append(f"{t:3d} A: {a} E: {e}")
    open(out, 'w').write('\n'.join(L + ['"/>', '</config>', '']))
    return n


def build(name, band, mode, ob):
    import sha_cnf
    cv, m1, m2, pr, R = pair(name); mkchar(name, ob + '.xml', band)
    so = sys.stdout; sys.stdout = open(os.devnull, 'w')
    sha_cnf.encode(ob + '.xml', ob + '.cnf', ob + '.map', 'sfs'); sys.stdout = so
    mp = json.load(open(ob + '.map'))
    pin = lambda bits, v: [(l if (v >> i) & 1 else -l) for i, l in enumerate(bits)]
    U = []
    for t in BANDS[band]:
        U += pin(mp['A1all'][str(t)], pr['A1'][t]) + pin(mp['A2all'][str(t)], pr['A2'][t])
        U += pin(mp['E1all'][str(t)], pr['E1'][t]) + pin(mp['E2all'][str(t)], pr['E2'][t])
    extra = ['%d 0' % u for u in U]
    if mode == 'real':
        cl = []
        for w in range(16):
            cl += [-l for l in pin(mp['W1'][w], m1[w])] + [-l for l in pin(mp['W2'][w], m2[w])]
        extra.append(' '.join(map(str, cl)) + ' 0')
    L = open(ob + '.cnf').read().split('\n', 1); h = L[0].split()
    with open(ob + '.cnf', 'w') as f:
        f.write('p cnf %s %d\n' % (h[2], int(h[3]) + len(extra)))
        f.write(L[1].rstrip('\n') + '\n' + '\n'.join(extra) + '\n')


if __name__ == '__main__':
    if sys.argv[1] == 'char': print(mkchar(sys.argv[2], sys.argv[3]))
    else: build(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
