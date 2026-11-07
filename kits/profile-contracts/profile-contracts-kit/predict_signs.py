#!/usr/bin/env python3
"""predict_signs.py BASE.xml [MIRROR.tsv ...]

Predict which SHA-256 message-word signs are free / pinned and which pinned
words form a linked group (flip only together), using the message expansion
    W_t = s1(W_t-2) + W_t-7 + s0(W_t-15) + W_t-16
as a GF(2) check matrix over the signed words of the base.

If MIRROR.tsv files (or directories containing them) are given -- or found next
to the base as ../mirror_* -- the prediction is scored against the measured
flip/mirror/combo SAT-UNSAT maps.
"""
import sys, os, re, glob, itertools

ROW = re.compile(r'^\s*(-?\d+) A: \S+ E: \S+ W: (\S+)', re.M)

# ---------------------------------------------------------------- parse base
def parse_base(path):
    txt = open(path).read()
    signed = {}            # row index -> set of signed bit positions
    N = 0
    for m in ROW.finditer(txt):
        t = int(m.group(1)); w = m.group(2)
        N = max(N, t + 1)
        bits = {i for i, c in enumerate(w) if c in 'un'}
        if bits:
            signed[t] = bits
    return signed, N

# ------------------------------------------------- build the GF(2) check rows
def build_checks(signed, N, model='word'):
    """Return (variables, equations).  Each equation is a frozenset of vars.

    model='word'  : a schedule input/output contributes iff that word carries
                    any difference (sign is a per-word variable).
    model='bit'   : bit-accurate -- an input contributes to the parity iff,
                    after s0/s1 rotation/shift, one of its difference bits lands
                    on a difference bit of the output word (MSB-first, w=32).
    """
    vars_ = sorted(signed)
    eqs = []
    for t in range(16, N):
        srcs = {'out': t, 's1': t - 2, 'add': t - 7, 's0': t - 15, 'id': t - 16}
        members = set()
        for role, s in srcs.items():
            if s not in signed:
                continue
            if model == 'word':
                members.add(s)
            else:  # bit-accurate
                out_bits = signed.get(t, set())
                if role == 'out':
                    members.add(s)
                elif _reaches(role, signed[s], out_bits):
                    members.add(s)
        if members:
            eqs.append(frozenset(members))
    return vars_, eqs

def _rotr(p, r):            # position p (MSB-first) under ROTR by r on 32 bits
    b = 31 - p
    return 31 - ((b - r) % 32)
def _shr(p, r):
    b = 31 - p
    nb = b - r
    return None if nb < 0 else 31 - nb
def _reaches(role, in_bits, out_bits):
    if not out_bits:
        return bool(in_bits)            # output carries no diff: still a relation
    maps = {'s0': [('r', 7), ('r', 18), ('s', 3)],
            's1': [('r', 17), ('r', 19), ('s', 10)],
            'add': [('id', 0)], 'id': [('id', 0)]}.get(role, [('id', 0)])
    for p in in_bits:
        for kind, r in maps:
            q = p if kind == 'id' else (_rotr(p, r) if kind == 'r' else _shr(p, r))
            if q is not None and q in out_bits:
                return True
    return False

# ------------------------------------------------------- GF(2) linear algebra
def nullspace(vars_, eqs):
    idx = {v: i for i, v in enumerate(vars_)}
    n = len(vars_)
    rows = [sum(1 << idx[v] for v in e) for e in eqs]
    # row reduce
    piv = {}
    for r in list(rows):
        for b, pr in piv.items():
            if r >> b & 1:
                r ^= pr
        if r:
            b = r.bit_length() - 1
            piv[b] = r
    pivcols = set(piv)
    basis = []
    for free in range(n):
        if free in pivcols:
            continue
        vec = 1 << free
        for b, pr in piv.items():
            if pr >> free & 1:
                vec |= 1 << b
        basis.append(vec)
    return idx, pivcols, basis

# --------------------------------------------------------------- classify
def classify(path, model='word'):
    signed, N = parse_base(path)
    vars_, eqs = build_checks(signed, N, model)
    idx, pivcols, basis = nullspace(vars_, eqs)

    cols = {v: set() for v in vars_}        # column support
    for j, e in enumerate(eqs):
        for v in e:
            cols[v].add(j)

    free, pinned = [], []
    for v in vars_:
        if not cols[v]:                     # zero column -> flip-alone is valid
            free.append(v)
        else:
            pinned.append(v)

    # hard-pinned: appears in a weight-1 check -> can never flip
    hard = sorted({next(iter(e)) for e in eqs if len(e) == 1})

    # linked groups: union-find over each check's support (pinned words only)
    parent = {v: v for v in pinned}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    def union(a, b):
        parent[find(a)] = find(b)
    for e in eqs:
        members = [v for v in e if v in parent]
        for a, b in zip(members, members[1:]):
            union(a, b)
    groups = {}
    for v in pinned:
        groups.setdefault(find(v), []).append(v)
    groups = [sorted(g) for g in groups.values()]

    def nullset(S):                         # is flip-set S in the null space?
        want = 0
        for v in S:
            if v in idx:
                want ^= 1 << idx[v]
        for b in nullspace.__wrapped__ if False else []:
            pass
        # verify directly against equations
        for e in eqs:
            if sum(1 for v in e if v in S) & 1:
                return False
        return True

    return dict(signed=signed, N=N, vars=vars_, eqs=eqs,
                free=sorted(free), pinned=sorted(pinned), hard=hard,
                groups=sorted(groups, key=len, reverse=True),
                nullset=nullset)

# --------------------------------------------------------------- predict map
def predict_variant(name, info):
    """Return 'SAT'/'UNSAT' prediction for a mirror.py variant name."""
    if name in ('base', 'xexp'):
        return 'SAT'
    if name == 'mirror':
        return 'SAT' if info['nullset'](info['vars']) else 'UNSAT'
    m = re.match(r'flip([\d_]+)$', name)
    if m:
        S = [int(x) for x in m.group(1).split('_')]
        return 'SAT' if info['nullset'](S) else 'UNSAT'
    return '?'

# --------------------------------------------------------------- score vs tsv
def load_tsv(path):
    out = {}
    for line in open(path):
        parts = line.replace('\t', ' ').split()
        if len(parts) >= 2 and parts[1].upper() in ('SAT', 'UNSAT'):
            out[parts[0]] = parts[1].upper()
    return out

def find_tsvs(base, extra):
    paths = []
    for a in extra:
        if os.path.isdir(a):
            paths += glob.glob(os.path.join(a, 'MIRROR.tsv'))
        elif a.endswith('.tsv'):
            paths.append(a)
    if not paths:                           # auto-discover ../mirror_*
        root = os.path.dirname(os.path.abspath(base))
        paths += glob.glob(os.path.join(root, '..', 'mirror_*', 'MIRROR.tsv'))
    return sorted(set(paths))

# --------------------------------------------------------------- main
def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    base = sys.argv[1]
    info = classify(base, model=os.environ.get('MODEL', 'word'))

    print('base:', base)
    print('signed words:', info['vars'])
    print('FREE   (flip-alone SAT):', info['free'])
    print('PINNED (flip-alone UNSAT):', info['pinned'])
    if info['hard']:
        print('HARD-PINNED (never flip):', info['hard'])
    for i, g in enumerate(info['groups']):
        tag = 'linked group' if len(g) > 1 else 'singleton'
        print(f'  {tag} {i}: {g}'
              + ('  <- flip only together' if len(g) > 1 else ''))

    tsvs = find_tsvs(base, sys.argv[2:])
    if not tsvs:
        return
    tot_hit = tot = 0
    print('\nscoring against measured maps:')
    for tsv in tsvs:
        meas = load_tsv(tsv)
        hit = n = 0
        for name, got in meas.items():
            pred = predict_variant(name, info)
            if pred == '?':
                continue
            n += 1; tot += 1
            if pred == got:
                hit += 1; tot_hit += 1
        if n:
            print(f'  {os.path.relpath(tsv):50s} {hit:3d}/{n:<3d} '
                  f'{100*hit/n:5.1f}%')
    if tot:
        print(f'  {"OVERALL":50s} {tot_hit:3d}/{tot:<3d} '
              f'{100*tot_hit/tot:5.1f}%')

if __name__ == '__main__':
    main()
