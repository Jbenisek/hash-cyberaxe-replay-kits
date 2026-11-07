#!/usr/bin/env python3
"""gen_boardpair.py SEEDWIT CHARSRC N BAND_START BAND_WIDTH RELEASE MODE OUTBASE
HASH$CyberAxe 10-28 (boardpairs). Middle-pin generator (ladder.py method) on a board's OWN characteristic,
generalised for any seed pair / step count, with band-position/width wiggle and single-row release.

  SEEDWIT   : json {cv:[8], M1:[16], M2:[16]} (hex strings) - the board's filed/seed pair.
  CHARSRC   : path to the board's own signed characteristic xml, or SELF (derive it from the seed pair).
  N         : step count (38 r38, 37 r37).
  BAND_START, BAND_WIDTH : pin the seed's A/E values (both copies) on state rows [BAND_START, BAND_START+BAND_WIDTH).
  RELEASE   : none | A<t> | E<t> | W<t> | AE<t>  (mk_release.py convention: free that cell -> 32 '?'; last 4 rows never freed).
  MODE      : real (one clause excluding the seed pair) | ctl (no exclusion).
Writes OUTBASE.xml/.cnf/.map; the CNF carries the mid-pin unit clauses and (real) the seed-exclusion clause.
SAT 'v' lines -> kit sha_cnf --decode + kit/indep_verify.py (must print INDEP VERIFIED)."""
import sys, os, re, json
HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.normpath(os.path.join(HERE, '..', 'kit')); sys.path.insert(0, KIT)
os.environ['SIGNED'] = '1'
import char_pair_profile as cpp
import sha_cnf


def load_seed(path):
    w = json.load(open(path))
    cv = [int(x, 16) for x in w['cv']]; m1 = [int(x, 16) for x in w['M1']]; m2 = [int(x, 16) for x in w['M2']]
    pr = cpp.profile(cv, m1, m2, int(w.get('R') or w.get('n') or len(cv) and 0) or len(m1) and 0 or 0) if False else None
    return cv, m1, m2


ROW = re.compile(r'^(\s*)(-?\d+)(\s+)A:(\s*)(\S+)(\s+)E:(\s*)(\S+)(?:(\s+)W:(\s*)(\S+))?(.*)$')


def self_char_lines(pr, n):
    z = '-' * 32
    L = ['<config>', '<options>', '  <option name="f" value="sha2"/>', f'  <option name="n" value="{n}"/>',
         '  <option name="w" value="32"/>', '</options>', '<comment>boardpairs SELF char (seed signed differences)</comment>', '<char value="']
    for t in range(-4, 0): L.append(f"{t:3d} A: {z} E: {z}")
    for t in range(n):
        L.append(f"{t:3d} A: {pr['rows']['A'][t]} E: {pr['rows']['E'][t]} W: {pr['rows']['W'][t]}")
    L += ['"/>', '</config>', '']
    return L


def apply_release(lines, release):
    if release in ('none', '', None): return lines
    cells = []
    for spec in ([release] if not release.startswith('AE') else ['A' + release[2:], 'E' + release[2:]]):
        k = spec[0]; t = int(spec[1:]); cells.append((k, t))
    out = list(lines)
    for i, l in enumerate(out):
        m = ROW.match(l)
        if not m: continue
        t = int(m.group(2))
        for (k, tt) in cells:
            if t != tt: continue
            grp = {'A': 5, 'E': 8, 'W': 11}[k]
            if m.group(grp) is None: continue
            val = m.group(grp); q = '?' * len(val)
            l = l[:m.start(grp)] + q + l[m.end(grp):]; m = ROW.match(l)
        out[i] = l
    return out


def main():
    seedwit, charsrc, N, bs, bw, release, mode, ob = sys.argv[1:9]
    N = int(N); bs = int(bs); bw = int(bw)
    cv, m1, m2 = load_seed(seedwit)
    pr = cpp.profile(cv, m1, m2, N); assert pr['collision'], 'seed is not a collision at n=%d' % N
    if charsrc == 'SELF':
        lines = self_char_lines(pr, N)
    else:
        lines = open(charsrc).read().split('\n')
    lines = apply_release(lines, release)
    open(ob + '.xml', 'w').write('\n'.join(lines if lines[-1] == '' else lines + ['']))
    so = sys.stdout; sys.stdout = open(os.devnull, 'w')
    sha_cnf.encode(ob + '.xml', ob + '.cnf', ob + '.map', 'sfs'); sys.stdout = so
    mp = json.load(open(ob + '.map'))
    pin = lambda bits, v: [(l if (v >> i) & 1 else -l) for i, l in enumerate(bits)]
    U = []
    for t in range(bs, bs + bw):
        if str(t) not in mp['A1all']: continue
        U += pin(mp['A1all'][str(t)], pr['A1'][t]) + pin(mp['A2all'][str(t)], pr['A2'][t])
        U += pin(mp['E1all'][str(t)], pr['E1'][t]) + pin(mp['E2all'][str(t)], pr['E2'][t])
    extra = ['%d 0' % u for u in U]
    if mode == 'real':
        cl = []
        for i in range(4):
            cl += [-l for l in pin(mp['A1'][str(-1 - i)], cv[i])] + [-l for l in pin(mp['A2'][str(-1 - i)], cv[i])]
            cl += [-l for l in pin(mp['E1'][str(-1 - i)], cv[4 + i])] + [-l for l in pin(mp['E2'][str(-1 - i)], cv[4 + i])]
        for w in range(16):
            cl += [-l for l in pin(mp['W1'][w], m1[w])] + [-l for l in pin(mp['W2'][w], m2[w])]
        extra.append(' '.join(map(str, cl)) + ' 0')
    head, body = open(ob + '.cnf').read().split('\n', 1); h = head.split()
    with open(ob + '.cnf', 'w') as f:
        f.write('p cnf %s %d\n' % (h[2], int(h[3]) + len(extra)))
        f.write(body.rstrip('\n') + '\n' + '\n'.join(extra) + '\n')
    print('OK pins=%d extra_clauses=%d' % (len(U), len(extra)))


if __name__ == '__main__':
    main()
