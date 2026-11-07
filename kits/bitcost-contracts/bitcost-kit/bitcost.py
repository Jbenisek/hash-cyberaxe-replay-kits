#!/usr/bin/env python3
"""bitcost.py - the shared BIT-COST model (owner 10-31: "time and bit costs are our paths and guides").
From any set of stair.tsv files (previous runs on the SAME target), each candidate name gets
   stall = (# runs where it was probed but never pinned) / (# runs that probed it)      and      t = median seconds of its successful pins.
cost(name) = (stall, t); unseen names get the prior (0.5, cap) so they sit between proven-cheap and proven-hard ones.
CLI:  bitcost.py rank OUT.order GLOB [GLOB...]        -> all seen names, cheapest first (feed to stair.py --order)
      bitcost.py hardest K GLOB [GLOB...]             -> the K most-stalled names (split candidates for cubes)
      bitcost.py table GLOB [GLOB...]                 -> name, stall, median_s, runs
Library: load(globs) -> {name: (stall, median_s, runs)} ; key(costs) -> sort key for a list of names."""
import sys, glob, statistics, collections
def load(globs):
    held = collections.Counter(); seen = collections.Counter(); t = collections.defaultdict(list)
    for g in globs:
        for f in glob.glob(g, recursive=True):
            got = {}
            try: lines = list(open(f))[1:]
            except Exception: continue
            for l in lines:
                p = l.rstrip('\n').split('\t')
                if len(p) < 4 or p[1] in ('base',) or p[1].startswith('swap'): continue
                n, v = p[1], p[2]
                try: s = float(p[3])
                except ValueError: continue
                if v == 'SAT' and n not in got: got[n] = s
                elif v in ('HELD', 'UNSAT'): got.setdefault('_' + n, 1)
            for n in {k.lstrip('_') for k in got}:
                seen[n] += 1
                if n in got: t[n].append(got[n])
                else: held[n] += 1
    return {n: (held[n] / seen[n], statistics.median(t[n]) if t[n] else 1e9, seen[n]) for n in seen}
def key(costs, prior=(0.5, 1e6)):
    return lambda n: costs.get(n, prior + (0,))[:2]
if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'rank':
        c = load(sys.argv[3:]); names = sorted(c, key=key(c)); open(sys.argv[2], 'w').write("\n".join(names) + "\n"); print(f"{len(names)} names ranked -> {sys.argv[2]}")
    elif cmd == 'hardest':
        c = load(sys.argv[3:]); names = sorted(c, key=lambda n: (-c[n][0], -c[n][2])); print(" ".join(names[:int(sys.argv[2])]))
    elif cmd == 'table':
        c = load(sys.argv[2:])
        for n in sorted(c, key=key(c)): print(f"{n}\t{c[n][0]:.2f}\t{c[n][1] if c[n][1] < 1e8 else '-'}\t{c[n][2]}")
