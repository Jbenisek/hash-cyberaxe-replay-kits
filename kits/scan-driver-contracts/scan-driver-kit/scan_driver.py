#!/usr/bin/env python3
"""scan_driver.py --shard i/N [--minutes M] [--targets TARGETS.json]   (owner 10-26: targets-first census over TARGETS.json)

Queries (global order: every target itself, then every 1-edit neighbour, then every 2-edit neighbour; in each
level targets in file order, R before R+1):
  R in {target R (default 40), min(R+1, 41)}; kicks kept in 16..R-2 (W_{R-1} never added, per sched_scan patch)
  edit = add one kick in 16..R-2, or move one existing kick to a free slot in 16..R-2; pairs = two edits; deduped.
  require = smallest message word of the target.
Engine: kissat per query (10-26): base_R<n>.cnf written once + units (-e_{t,i} for silent words, d_req), -q --conflicts=B.
Budget ladder: level 0 = ~--l0sec (60) s of conflicts (calibrated once per shard on pub39 R40 UNSAT), 1 = 10x, 2 = 100x;
undecided -> re-queued at the next level; still undecided at level 2 -> written as UNDECIDED (how=cap).
Pruning (same R and require): UNSAT superset -> subset UNSAT; SAT subset -> superset SAT.
Output: census_<i>.tsv, one line per decided query, flushed:
  R  words  kicks  verdict  budget_level  seconds  how  target
Restart-safe: queries already decided in any census_*.tsv are skipped.
"""
import sys, os, sys, json, time, glob, itertools, subprocess
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sched_scan                     # sets WBITS=32, SCHED_ONLY=1; gives build_base(n)

LADDER = [float(x) for x in (sys.argv[sys.argv.index('--ladder') + 1] if '--ladder' in sys.argv else '1,10,100').split(',')]  # owner 10-27: edge-first, e.g. --l0sec 10 --ladder 1,3,6 = 10 s / 30 s / 60 s, nothing longer


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def neighbours(kicks, R):
    """Yield (edits, kickset) for 0, 1, 2 edits (add or move) within 16..R-2."""
    slots = list(range(16, R - 1))
    K0 = frozenset(k for k in kicks if 16 <= k <= R - 2)
    yield 0, K0
    lvl1 = []
    for a in slots:
        if a in K0: continue
        lvl1.append(K0 | {a})                               # add
        for b in sorted(K0):
            lvl1.append((K0 - {b}) | {a})                   # move b -> a
    for K in lvl1: yield 1, K
    for K in lvl1:                                          # second edit on top of each first edit
        for a in slots:
            if a in K: continue
            yield 2, K | {a}
            for b in sorted(K):
                yield 2, (K - {b}) | {a}


def build_queries(targets):
    seen = set(); out = []
    for ti, t in enumerate(targets):
        R0 = t.get('R', 40)
        if '--self-only' in sys.argv:                       # map rescan (owner 10-26): the exact shape only, at its own R
            W = frozenset(t['words']); req = min(W); K = frozenset(k for k in t['kicks'] if 16 <= k <= R0 - 1)
            key = (R0, W, K)
            if key not in seen: seen.add(key); out.append((0, ti, R0, W, K, req, t['name']))
            continue
        for R in sorted({R0, min(R0 + 1, 45)}):
            W = frozenset(t['words']); req = min(W)
            for d, K in neighbours(t['kicks'], R):
                key = (R, W, K)
                if key in seen: continue
                seen.add(key); out.append((d, ti, R, W, K, req, t['name']))
    out.sort(key=lambda q: (q[0], q[1], q[2]))             # distance, then target order, then R
    return out


def fmt(s): return ','.join(map(str, sorted(s)))


def main():
    i, N = map(int, arg('--shard', '0/1').split('/'))
    minutes = float(arg('--minutes', '0')) or None
    targets = json.load(open(arg('--targets', os.path.join(HERE, 'TARGETS.json'))))
    allq = build_queries(targets)
    done = set()
    for f in glob.glob(os.path.join(HERE, 'census_*.tsv')):
        for l in open(f):
            p = l.rstrip('\n').split('\t')
            if len(p) >= 7 and not l.startswith('#') and p[3] != 'UNDECIDED':
                done.add((int(p[0]), p[1], p[2]))
    mine = [q for j, q in enumerate(allq) if j % N == i and (q[2], fmt(q[3]), fmt(q[4])) not in done]
    if '--reverse' in sys.argv: mine = mine[::-1]          # queued shards work from the back of the list (no overlap with front shards)
    out = open(os.path.join(HERE, 'census_%d.tsv' % i), 'a')
    out.write('# shard %d/%d start %s queries_total=%d mine_left=%d\n' % (i, N, time.strftime('%F %T'), len(allq), len(mine)))
    out.flush()
    print('# shard %d/%d total %d mine %d' % (i, N, len(allq), len(mine)), flush=True)

    t_end = time.time() + 60 * minutes if minutes else None
    bases = {}; known = {}              # R -> (header-less clause bytes, nv, ncl, dvar, evars); (R, req) -> [(S, verdict)]
    tmpdir = '/dev/shm' if os.path.isdir('/dev/shm') else '/tmp'
    tmp = os.path.join(tmpdir, 'scan40_q_%d_%d.cnf' % (os.getpid(), i))

    def get(R):
        if R not in bases:
            cl, dvar, nv = sched_scan.build_base(R); ev = sched_scan.build_base.evars
            path = os.path.join(HERE, 'base_R%d.cnf' % R)
            if not os.path.exists(path):                    # written once per R, atomically (shards may race)
                tp = path + '.%d.tmp' % os.getpid()
                with open(tp, 'w') as f:
                    f.write('p cnf %d %d\n' % (nv, len(cl)))
                    f.write(''.join(' '.join(map(str, c)) + ' 0\n' for c in cl))
                os.replace(tp, path)
            with open(path, 'rb') as f:
                hdr = f.readline().split(); body = f.read()
            bases[R] = (body, int(hdr[2]), int(hdr[3]), dvar, ev)
        return bases[R]

    def units(R, S, req):
        body, nv, ncl, dvar, ev = get(R)
        u = [-e for t in range(R) if t not in S for e in ev[t]] + [dvar[req]]
        return u

    RETRY = int(arg('--retry', '1'))   # owner 10-27 bench: the slow tail is run-to-run variance; try RETRY seeds at a rung before climbing
    LAST = {}
    def run(R, S, req, budget, stats=False, tmax=None, seed=1):
        """kissat on base + units; returns (True/False/None, seconds, conflicts or None)."""
        body, nv, ncl, dvar, ev = get(R)
        u = units(R, S, req)
        with open(tmp, 'wb') as f:
            f.write(b'p cnf %d %d\n' % (nv, ncl + len(u))); f.write(body)
            f.write(''.join('%d 0\n' % x for x in u).encode())
        # never -q: the statistics block is the compass (API2110). 15:22: the comment had swallowed '+ seed + [tmp]' -> kissat read stdin (empty under the queue manager) and exited 1.
        cmd = ['kissat'] + (['--conflicts=%d' % budget] if budget else []) + (['--seed=%d' % seed] if seed != 1 else []) + [tmp]
        ts = time.time()
        try:
            _pr = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=tmax); o = _pr.stdout.decode(); _rc = _pr.returncode
        except subprocess.TimeoutExpired:
            o = ''; _rc = 'timeout'
        dt = time.time() - ts
        try: os.remove(tmp)
        except OSError: pass
        r = None
        for l in o.splitlines():
            if l.startswith('s '):
                r = True if l.strip() == 's SATISFIABLE' else False if l.strip() == 's UNSATISFIABLE' else None
        nc = None; LAST.clear(); LAST['_raw'] = ['rc=%s' % _rc] + [l[:160] for l in o.splitlines()[-5:]]   # first lines kept for the calib-failure message (15:12)
        for l in o.splitlines():
            for key in ('conflicts', 'decisions', 'propagations', 'restarts'):
                if l.startswith('c %s:' % key):
                    try: LAST[key] = int(l.split()[2])
                    except ValueError: pass
        nc = LAST.get('conflicts')
        return r, dt, nc

    # calibrate once per shard: pub39 core {8..12} + kicks {16,17,24,26,33} at R40 (known UNSAT in ~1-3 s)
    CW, CK = frozenset(range(8, 13)), frozenset([16, 17, 24, 26, 33])
    r, dt, nc = run(40, CW | CK, 8, 0, stats=True, tmax=300)
    if r is not False or not nc:
        out.write('# calib FAILED verdict=%s conflicts=%s %.1f s\n' % (r, nc, dt)); out.close()
        print('# calib FAILED', r, nc, dt, '| kissat said:', ' / '.join(LAST.get('_raw', [])[:14]), flush=True); sys.exit(2)
    L0SEC = float(arg('--l0sec', '60'))
    base_conf = max(1000, int(nc / max(dt, 1e-3) * L0SEC))
    out.write('# calib pub39 R40 UNSAT %d conflicts in %.2f s -> level0 budget %d conflicts (~%g s), engine kissat\n'
              % (nc, dt, base_conf, L0SEC)); out.flush()
    print('# calib budget %d (%d conf in %.2f s)' % (base_conf, nc, dt), flush=True)

    queue = deque((q, 0) for q in mine)
    n_dec = 0
    while queue:
        if t_end and time.time() > t_end: break
        (d, ti, R, W, K, req, name), lvl = queue.popleft()
        S = W | K
        how = None; v = None
        for U, uv in known.get((R, req), []):
            if uv == 'UNSAT' and S <= U: v, how = 'UNSAT', 'pruned(%s)' % fmt(U); break
            if uv == 'SAT' and U <= S: v, how = 'SAT', 'pruned(%s)' % fmt(U); break
        dt = 0.0
        if v is None:
            tmax = max(1.0, t_end - time.time()) if t_end else None
            r, dt, _ = run(R, S, req, base_conf * LADDER[lvl], tmax=tmax)
            for _sd in range(2, RETRY + 1):
                if r is not None: break
                r, dt2, _ = run(R, S, req, base_conf * LADDER[lvl], tmax=tmax, seed=_sd); dt += dt2
            if r is None:
                if t_end and time.time() > t_end:
                    queue.appendleft(((d, ti, R, W, K, req, name), lvl)); break
                if lvl + 1 < len(LADDER):
                    out.write('#u\t%d\t%s\t%s\tUNDECIDED\t%d\t%.1f\tinterim\t%s\n' % (R, fmt(W), fmt(K), lvl, dt, name)); out.flush()   # interim rung line (pull interim results, 15:35); parsers skip '#'
                    queue.append(((d, ti, R, W, K, req, name), lvl + 1)); continue
                v, how = 'UNDECIDED', 'cap'
            else:
                v, how = ('SAT' if r else 'UNSAT'), 'solve'
                known.setdefault((R, req), []).append((S, v))
        out.write('%d\t%s\t%s\t%s\t%d\t%.1f\t%s\t%s\t%s\t%s\t%s\t%s\n' % (R, fmt(W), fmt(K), v, lvl, dt, how, name, LAST.get('conflicts', '-'), LAST.get('decisions', '-'), LAST.get('propagations', '-'), LAST.get('restarts', '-'))); out.flush()   # cols 9-12: conflicts decisions propagations restarts (API2110 compass)
        n_dec += 1
    out.write('# shard %d stop %s decided=%d left=%d\n' % (i, time.strftime('%F %T'), n_dec, len(queue))); out.close()
    print('# stop decided %d left %d' % (n_dec, len(queue)), flush=True)


if __name__ == '__main__':
    main()
