# builds CELLS.jsonl records (list in records.json) from out/*.txt, links_out.txt, local_counts.txt; appended via research/dig/add_cell.py
import re, os, json, sys, subprocess
EV = 'research/retest/dig38_1029/'
res = {}
for l in subprocess.run([sys.executable, 'analyze.py'], capture_output=True, text=True).stdout.splitlines():
    p = l.split()
    if 'NOT' in p[1]: continue
    d = dict(re.findall(r'(\w+) (\S+)', ' '.join(p[2:])))
    d['alive'] = re.search(r'alive_rows (\[[^\]]*\])', l).group(1); d['die'] = re.search(r'die_at (\S+)', l).group(1)
    d['frow'] = re.search(r'frow (\{[^}]*\})', l).group(1)
    res[p[0]] = d
spec = {l.split('|')[0]: l.split('|')[1].strip() for f in ('tests.txt', 'tests2.txt') for l in open(f) if '|' in l}
def verdict(n):
    d = res[n]; n1, ex1 = int(d['N1']), int(d['EX1'])
    if ex1 > 0: return 'VIOLATORS REACH THE EVENT', True
    if n1 > 0: return 'NECESSARY (violators reach rows 22..37, 0 EXACT)', False
    if d['alive'] != '[]': return 'NECESSARY (violators alive rows %s, die at row %s, never reach the window)' % (d['alive'], d['die']), False
    return 'NO VIOLATOR DRAWABLE (held/implied in the attack model)', False
def num(n):
    d = res[n]; v, lev = verdict(n)
    return ('%s; violator EXACT %s vs required EXACT %s on %s seeds (N0 %s, N1 %s); gain <= %s (rule of three); E16 set %s; false collisions %s' %
            (v, d['EX1'], d['EX0'], d['seeds'], d['N0'], d['N1'], d['UBgain'], d['E16set'], d['false'])), lev
QT = {'Q2': 'Q2: drop each printed condition of this object singly - does the event still occur on the full path? (batch drop of all of them bounds every single drop)',
      'Q5': 'Q5: joint drop of one condition in each of the two rows against the two singles (batch joint drop of both rows bounds every pair)'}
recs = []
def rec(cell, ri, rj, obj, q, status, number, ev, notes, lever=False, gain=0.0):
    recs.append(dict(hash='sha256-38', row_i=ri, row_j=rj, object=obj, question=QT.get(q, q), labels=['Z'], status=status, number=number,
        source='our traillab_d38 (drop_sweep38 build, VTAG) window rows 22..37 event out, prefix-relax, seeds 9401..9406, np 4096 mt 8192; dig38_1029',
        own_test=True, evidence=ev, date='2026-10-29', lever=lever, gain_bits=gain, notes='universe cell %s. %s' % (cell, notes), topic='dig38_1029'))
MONO = 'A batch drop admits a superset of every single (or pair) drop violator set, so violator EXACT 0 here bounds each single drop by the same rule-of-three gain.'
# --- test-backed cells
T = {'r14|A|Q2': ['b14A'], 'r14|E|Q2': ['b14E'], 'r14|REL|Q2': ['b14R'], 'r15|A|Q2': ['b15A'], 'r15|E|Q2': ['b15E'], 'r15|W|Q2': ['b15W'],
     'r15|REL|Q2': ['b15R'], 'r16|E|Q2': ['b16E'], 'r16|W|Q2': ['b16W'], 'r16|REL|Q2': ['b16R'], 'r19|E|Q2': ['b19v', 'b19R'], 'r7|W|Q2': ['b7W'],
     'r8|W|Q2': ['b8W'], 'r6|E|Q2': ['b6E'], 'r5|REL|Q2': ['b6E'], 'r6|REL|Q2': ['b6E'], 'r7|A|Q2': ['b7AE'], 'r7|E|Q2': ['b7AE'], 'r7|REL|Q2': ['b7AE', 'b7W'],
     'r8|A|Q2': ['b8AE'], 'r8|E|Q2': ['b8AE'], 'r8|REL|Q2': ['b8AE', 'b8W'], 'r9|E|Q2': ['b9E'], 'r10|E|Q2': ['b10E'], 'r11|A|Q2': ['b11A'], 'r11|E|Q2': ['b11E'],
     'r11|REL|Q2': ['b11E'], 'r12|A|Q2': ['b12AE'], 'r12|E|Q2': ['b12AE'], 'r13|A|Q2': ['b13E'], 'r13|E|Q2': ['b13E'], 'r13|REL|Q2': ['b13E']}
LC = {m.group(1): m.group(0) for m in re.finditer(r'^([AEW]\d+) cell .*$', open('local_counts.txt').read(), re.M)}
for c, tl in T.items():
    if not all(t in res and res[t]['seeds'] == '6' and int(res[t]['N0']) > 0 for t in tl): continue
    loc, ob, q = c.split('|'); r = int(loc[1:])
    nums, levs = zip(*[num(t) for t in tl])
    lc = '; '.join(LC.get(k + str(r), '') for k in ('AEW' if ob == 'REL' else ob))
    obj = 'dig38_1029 %s: %s' % ('+'.join(tl), ' ; '.join(spec[t] for t in tl))
    st = 'LOCAL_ONLY' if all(verdict(t)[0].startswith('NO VIOLATOR') for t in tl) else 'COMPUTED'
    known = ' b19v relaxes the E19 coset value bits 30040e32 = the known four-pattern lever (ATLAS38 G8, drop_sweep38 c2_tie), already in the r38 claim: not new.' if 'b19v' in tl else ''
    held = ' LOCAL_ONLY: the relaxation changes nothing in this sampler (rows <= 15 come from the held anchor rows 10..13 and the rows 14..15 init; the late words W6, W7, W8 are drawn from their own sets: rand, F7, the W8 cell), so necessity is not testable here; the answer is the local count.' if st == 'LOCAL_ONLY' else ''
    rec('sha256-38|' + c, r, None, obj, q, st, ' | '.join('%s: %s' % (t, x) for t, x in zip(tl, nums)), '; '.join(EV + 'out/%s.txt' % t for t in tl) + '; ' + EV + 'analyze.py',
        MONO + known + held + ' Local count (chi38 cell, ' + EV + 'local_counts.txt): ' + lc[:300], lever=any(levs), gain=None if any(levs) else 0.0)
# --- fixed message words W9..W11: no free value in the attack model
for c in ('r9|W|Q2', 'r10|W|Q2', 'r11|W|Q2'):
    loc, ob, q = c.split('|'); r = int(loc[1:])
    recs.append(None); recs.pop()
    rec('sha256-38|' + c, r, None, 'dig38_1029 W%d printed bits = the message-word difference (signed); W%d is a fixed word of the pair (free words W6, W7, W8 only)' % (r, r), q, 'LOCAL_ONLY',
        'NO VIOLATOR DRAWABLE: W%d is fixed in the attack model; its printed bits are the message difference itself, a drop is a different characteristic, not a relaxation' % r,
        EV + 'out/b14A.txt (model header: free words W6 W7 W8); ' + EV + 'sched.txt; ' + EV + 'local_counts.txt', 'Local count: ' + LC.get('W%d' % r, ''))
json.dump(recs, open('records_q2.json', 'w'), indent=0)
print(len(recs), 'records;', sum(r['lever'] for r in recs), 'lever')
