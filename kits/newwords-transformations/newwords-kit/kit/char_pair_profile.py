"""char_pair_profile.py - pure-Python oracle for the price of a message pair's characteristic (reduced-step SHA-256).

Given a chaining value, two 16-word messages and a step count n, it runs both computations and prints, per step,
the number of differing A/E bits, the Boolean-function conditions (rule C1 below) and the signed characteristic
rows in the kit's xml <char> format, so the result can be compared with char_cnf.py --count or fed to sha_cnf.py.

Usage:
  python3 char_pair_profile.py --n 39 --cv "8 hex words" --m1 "16 hex words" --m2 "16 hex words" [--t0 16]
                               [--xml-char FILE] [--xml-pinned FILE] [--values] [--json FILE]
  python3 char_pair_profile.py --preset pin39b [--t0 16] [--xml-char FILE] [--xml-pinned FILE]
  --preset pin39b : the published 39-step semi-free-start pair (kit control P0).
  --xml-pinned F  : write the fully pinned instance (chaining rows 0/1, W0..15 as 0/1/u/n, expanded W rows as signed
                    rows '-'/u/n, state rows '?' except the last 4 rows '-'): the positive-control instance.
  --xml-char F    : write the signed characteristic only (state and W rows as '-'/u/n, no values): stage-1 output.
  --values        : in the printed rows show equal bits as their value 0/1 instead of '-'.
  --json F        : write the per-step profile as JSON (for scripts).
Exit status 0 even when the pair is not a collision (the last line says so); 2 on malformed input.

Conventions (identical to sha_cnf.py): rows are 32 characters, leftmost char = bit 31; 'u' = copy1 1 / copy2 0,
'n' = copy1 0 / copy2 1, '-' equal, '0'/'1' equal with that value, '?' free; chaining rows -1..-4 are
A_{-1..-4} = a,b,c,d and E_{-1..-4} = e,f,g,h of the chaining value (cv[0..3] and cv[4..7]).

Condition-counting rule C1 (the rule char_cnf.py encodes; one well-defined rule, stated once here):
  * every signed state difference (an 'u'/'n' bit of A_t or E_t) is one condition;
  * a Boolean-function bit (Maj at step t on A_{t-1},A_{t-2},A_{t-3}; Ch at step t on E_{t-1},E_{t-2},E_{t-3}) is one
    condition when at least one input bit differs and the output difference is NOT determined by the signed input
    differences alone, i.e. it depends on the value of an equal input bit:
      Maj: exactly one of the three inputs differs (the output differs iff the other two inputs differ from each other:
           the classic 2-bit condition such as A15[7] = A16[7]);
      Ch : some input differs and not both f and g differ (f,g both differing makes the output always differ, whatever e;
           every other pattern leaves the output difference depending on an equal e, f or g value).
  * values forced by the xml ('0'/'1'), xor-linear Sigma/sigma bits and carries add no conditions (Sigma is linear in
    the difference; the carry behaviour is implied by the signed values of the summands).
  * the total 'price' of a characteristic is the sum over steps t >= T0 (default 16) of
    |dA_t| + |dE_t| + condMaj_t + condCh_t ; char_cnf.py bounds exactly this sum by COND_K and |dA_t|+|dE_t| by DIFF_K.
  This counts conditions, not probability: a condition that is implied by another is still counted (upper bound on the
  -log2 probability of the uncontrolled part, as in the published tables' raw condition counts).
"""
import sys, json, argparse

MASK = 0xFFFFFFFF
K = [0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2]

PRESETS = {
    'pin39b': dict(n=39,
                   cv='b21e3e63 d12deef2 71a28861 1c40a0d4 15bb07fb b326f54c 020b80dd 0e6446c1',
                   m1='5ee50e16 b5a4f02b a58b289e f713de5d 3b96d2db 215da7e2 3674669a 2ca65d8d e99c40e3 172e9a20 02e88746 07021c8f e8c6e622 b06304c1 43660040 4891771f',
                   m2='5ee50e16 b5a4f02b a58b289e f713de5d 3b96d2db 215da7e2 3674669a 2ca65d8d a99c40e3 1fae8a20 42e88746 01003fbb e8d6fe22 b06304c1 43660040 4891771f'),
}


def R(x, k): return ((x >> k) | (x << (32 - k))) & MASK
def s0(x): return R(x, 7) ^ R(x, 18) ^ (x >> 3)
def s1(x): return R(x, 17) ^ R(x, 19) ^ (x >> 10)


def expand(W, n):
    W = list(W)
    for t in range(16, n): W.append((s1(W[t-2]) + W[t-7] + s0(W[t-15]) + W[t-16]) & MASK)
    return W


def states(chain, W, n, koff=0):
    """A[t], E[t] for t = -4..n-1 as dicts (t -> 32-bit value); chaining rows per the sha_cnf convention."""
    a, b, c, d, e, f, g, h = chain
    A = {-1: a, -2: b, -3: c, -4: d}; E = {-1: e, -2: f, -3: g, -4: h}
    for t in range(n):
        T1 = (h + (R(e, 6) ^ R(e, 11) ^ R(e, 25)) + ((e & f) ^ (~e & g & MASK)) + K[t + koff] + W[t]) & MASK
        T2 = ((R(a, 2) ^ R(a, 13) ^ R(a, 22)) + ((a & b) ^ (a & c) ^ (b & c))) & MASK
        h, g, f, e, d, c, b, a = g, f, e, (d + T1) & MASK, c, b, a, (T1 + T2) & MASK
        A[t] = a; E[t] = e
    return A, E


def popcount(x): return bin(x).count('1')


def maj_cond_mask(da, db, dc):
    """bit mask of Maj positions with exactly one differing input (rule C1)."""
    return (da & ~db & ~dc) | (~da & db & ~dc) | (~da & ~db & dc)


def ch_cond_mask(de, df, dg):
    """bit mask of Ch positions with some differing input and not both f and g differing (rule C1)."""
    return (de | df | dg) & ~(df & dg) & MASK


def signed_row(x, y, values=False, w=32):
    """row of w characters, bit w-1 first: '-' (or the value when values=True) where equal, 'u'/'n' where the copies differ."""
    out = []
    for i in range(w - 1, -1, -1):
        bx, by = (x >> i) & 1, (y >> i) & 1
        if bx == by: out.append(str(bx) if values else '-')
        else: out.append('u' if bx else 'n')
    return ''.join(out)


def profile_from_values(A1, A2, E1, E2, W1, W2, n, t0=16, w=32):
    """the C1 price of a pair given its state words A/E (dicts t=-4..n-1) and schedule words W (lists, length >= n).
    Returns dict: 'steps' (per-step dicts for t=-4..n-1), 'total' for t >= t0, signed 'rows' and value 'vrows', collision flag."""
    m = (1 << w) - 1
    dA = {t: (A1[t] ^ A2[t]) & m for t in A1}; dE = {t: (E1[t] ^ E2[t]) & m for t in E1}
    steps = []
    tot = {'dA': 0, 'dE': 0, 'maj': 0, 'ch': 0, 'cond': 0, 'diff': 0}
    for t in range(-4, n):
        maj = popcount(maj_cond_mask(dA[t-1], dA[t-2], dA[t-3]) & m) if t >= 0 else 0
        ch = popcount(ch_cond_mask(dE[t-1], dE[t-2], dE[t-3]) & m) if t >= 0 else 0
        na, ne = popcount(dA[t]), popcount(dE[t])
        dw = popcount((W1[t] ^ W2[t]) & m) if 0 <= t < n else 0
        row = {'t': t, 'dA': na, 'dE': ne, 'maj': maj, 'ch': ch, 'cond': na + ne + maj + ch, 'dW': dw}
        steps.append(row)
        if t >= t0:
            tot['dA'] += na; tot['dE'] += ne; tot['maj'] += maj; tot['ch'] += ch
            tot['cond'] += row['cond']; tot['diff'] += na + ne
    rows = {'A': {t: signed_row(A1[t], A2[t], False, w) for t in range(-4, n)}, 'E': {t: signed_row(E1[t], E2[t], False, w) for t in range(-4, n)},
            'W': {t: signed_row(W1[t], W2[t], False, w) for t in range(n)}}
    vrows = {'A': {t: signed_row(A1[t], A2[t], True, w) for t in range(-4, n)}, 'E': {t: signed_row(E1[t], E2[t], True, w) for t in range(-4, n)},
             'W': {t: signed_row(W1[t], W2[t], True, w) for t in range(n)}}
    out1 = tuple(A1[t] for t in range(n-1, n-5, -1)) + tuple(E1[t] for t in range(n-1, n-5, -1))
    out2 = tuple(A2[t] for t in range(n-1, n-5, -1)) + tuple(E2[t] for t in range(n-1, n-5, -1))
    return {'n': n, 't0': t0, 'w': w, 'steps': steps, 'total': tot, 'rows': rows, 'vrows': vrows,
            'collision': out1 == out2 and list(W1[:n]) != list(W2[:n]), 'W1': W1, 'W2': W2, 'A1': A1, 'A2': A2, 'E1': E1, 'E2': E2}


def profile(cv, m1, m2, n, t0=16, koff=0):
    """expand both messages, run both computations from the chaining value cv, and price the pair (rule C1)."""
    W1, W2 = expand(m1, n), expand(m2, n)
    A1, E1 = states(cv, W1, n, koff); A2, E2 = states(cv, W2, n, koff)
    return profile_from_values(A1, A2, E1, E2, W1, W2, n, t0)


def xml_text(n, rowsA, rowsE, rowsW, comment='char_pair_profile', w=32):
    lines = ['<config>', '<options>', '  <option name="f" value="sha2"/>', f'  <option name="n" value="{n}"/>',
             f'  <option name="w" value="{w}"/>', '</options>', f'<comment>{comment}</comment>', '<char value="']
    for t in range(-4, 0): lines.append(f"{t:3d} A: {rowsA[t]} E: {rowsE[t]}")
    for t in range(n): lines.append(f"{t:3d} A: {rowsA[t]} E: {rowsE[t]} W: {rowsW[t]}")
    lines += ['"/>', '</config>', '']
    return '\n'.join(lines)


def pinned_xml(pr):
    """positive-control instance: cv rows as 0/1, W0..15 as 0/1/u/n, W16.. as signed rows, states free, last 4 rows equal."""
    n = pr['n']
    A = {t: pr['vrows']['A'][t] for t in range(-4, 0)}; E = {t: pr['vrows']['E'][t] for t in range(-4, 0)}
    for t in range(n):
        A[t] = E[t] = ('-' * 32) if t >= n - 4 else ('?' * 32)
    Wr = {t: (pr['vrows']['W'][t] if t < 16 else pr['rows']['W'][t]) for t in range(n)}
    return xml_text(n, A, E, Wr, f'char_pair_profile pinned pair n={n} (positive control)')


def char_xml(pr):
    """stage-1 characteristic: signed differences only ('-'/u/n) on every state and W row."""
    return xml_text(pr['n'], pr['rows']['A'], pr['rows']['E'], pr['rows']['W'], f"char_pair_profile signed characteristic n={pr['n']}")


def print_profile(pr, values=False):
    rows = pr['vrows'] if values else pr['rows']; wb = pr.get('w', 32)
    print(f"n={pr['n']} T0={pr['t0']} collision={pr['collision']}")
    print("  t  |dA| |dE|  maj   ch  cond  |dW|   A-row" + ' ' * (wb - 4) + " E-row" + ' ' * (wb - 4) + " W-row")
    for r in pr['steps']:
        t = r['t']; w = rows['W'][t] if t >= 0 else ' ' * wb
        print(f"{t:3d} {r['dA']:4d} {r['dE']:4d} {r['maj']:4d} {r['ch']:4d} {r['cond']:5d} {r['dW']:4d}   {rows['A'][t]} {rows['E'][t]} {w}")
    T = pr['total']
    print(f"total t>={pr['t0']}: diff(A+E)={T['diff']} (A {T['dA']}, E {T['dE']})  maj={T['maj']} ch={T['ch']}  COND={T['cond']}")


def parse_words(s, k, name):
    ws = s.replace(',', ' ').split()
    if len(ws) != k: sys.exit(f"{name}: expected {k} hex words, got {len(ws)}")
    try: return [int(w, 16) & MASK for w in ws]
    except ValueError: sys.exit(f"{name}: not hex: {s}")


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--preset', choices=sorted(PRESETS)); ap.add_argument('--n', type=int); ap.add_argument('--cv'); ap.add_argument('--m1'); ap.add_argument('--m2')
    ap.add_argument('--t0', type=int, default=16); ap.add_argument('--koff', type=int, default=0)
    ap.add_argument('--values', action='store_true'); ap.add_argument('--xml-char'); ap.add_argument('--xml-pinned'); ap.add_argument('--json')
    a = ap.parse_args(argv)
    if a.preset:
        p = PRESETS[a.preset]; n = a.n or p['n']; cv, m1, m2 = p['cv'], p['m1'], p['m2']
    else:
        if not (a.n and a.cv and a.m1 and a.m2): ap.error('need --preset or all of --n --cv --m1 --m2')
        n, cv, m1, m2 = a.n, a.cv, a.m1, a.m2
    if not 1 <= n <= 64: sys.exit(f"n={n} out of range")
    pr = profile(parse_words(cv, 8, 'cv'), parse_words(m1, 16, 'm1'), parse_words(m2, 16, 'm2'), n, a.t0, a.koff)
    print_profile(pr, a.values)
    if a.xml_pinned: open(a.xml_pinned, 'w').write(pinned_xml(pr)); print('wrote pinned instance', a.xml_pinned)
    if a.xml_char: open(a.xml_char, 'w').write(char_xml(pr)); print('wrote signed characteristic', a.xml_char)
    if a.json:
        js = {k: pr[k] for k in ('n', 't0', 'steps', 'total', 'collision')}
        js['rows'] = {k: {str(t): v for t, v in d.items()} for k, d in pr['rows'].items()}
        json.dump(js, open(a.json, 'w'), indent=1); print('wrote', a.json)


if __name__ == '__main__':
    main(sys.argv[1:])
