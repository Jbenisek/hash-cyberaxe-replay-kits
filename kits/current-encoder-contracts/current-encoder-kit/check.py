"""Pinned copied-encoder fixtures, evaluated gates, no search or external solver.

Original research files are never modified. Complete circuit assignments are
constructed from fixed inputs, then checked against every emitted CNF clause.
These tests cover named modes, not every combination of encoder options.
"""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import runpy
import shutil
import tempfile
from datetime import datetime, timezone
from unittest.mock import patch

if not __debug__:
    raise SystemExit('Run without -O')
PUB = Path(__file__).resolve().parents[1]
SOURCE = Path(__file__).resolve().parent / 'sha_cnf.py'
SHA = 'c431c124e449c3b7939f2fdec373a8abb7ba3e651b2dc884c64d4aa03308faec'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SHA
OPTIONS = ('WBITS DIFFVARS BITORDER CHAINREV SIGNED KOFF EXTRAW MODDIFF '
           'SCHED_ONLY NEAR_K NEAR_ENC NEAR_OUTS REQUIRE_DIFF SYMBREAK '
           'XORMODE XOR3 FEEDFWD TRUNC224 PREHEAD_K PREHEAD_ROWS PREHEAD_ROWCAP').split()


def reference(words, cv, n, width, constants, offset):
    """Word arithmetic, separate from the source's gate and sha_ref functions."""
    mask = (1 << width) - 1
    scale = lambda k: max(1, (k * width + 16) // 32)
    def rot(x, k):
        k = scale(k)
        return ((x >> k) | (x << (width - k))) & mask
    schedule = list(words)
    for t in range(16, n):
        x, y = schedule[t-15], schedule[t-2]
        schedule.append(((rot(x, 7) ^ rot(x, 18) ^ (x >> scale(3))) + schedule[t-16]
                         + (rot(y, 17) ^ rot(y, 19) ^ (y >> scale(10))) + schedule[t-7]) & mask)
    a, b, c, d, e, f, g, h = cv
    for t in range(n):
        first = (h + (rot(e, 6) ^ rot(e, 11) ^ rot(e, 25))
                 + ((e & f) ^ (~e & g)) + constants[t+offset] + schedule[t]) & mask
        second = ((rot(a, 2) ^ rot(a, 13) ^ rot(a, 22))
                  + ((a & b) ^ (a & c) ^ (b & c))) & mask
        a, b, c, d, e, f, g, h = (first + second) & mask, a, b, c, (d + first) & mask, e, f, g
    return [a, b, c, d, e, f, g, h]


def load(copy, settings):
    env = {k: v for k, v in os.environ.items() if k not in OPTIONS}
    env.update({k: str(v) for k, v in settings.items()})
    with patch.dict(os.environ, env, clear=True):
        namespace = runpy.run_path(str(copy), run_name='bounded_library_fixture')
    return namespace['encode'].__globals__


def fixture(folder, copy, name, width=8, n=1, offset=0, trunc=False, changed=False,
            chaining='free', feed=True, reuse=False):
    m = (1 << width) - 1
    mod = load(copy, {'WBITS': width, 'FEEDFWD': int(feed), 'TRUNC224': int(trunc),
                      'KOFF': offset, 'DIFFVARS': int(reuse)})
    cv1 = [v & m for v in mod['IV']] if chaining == 'iv' else [(13 + 29*i) & m for i in range(8)]
    cv2 = cv1.copy()
    words1 = [(17 + 43*i) & m for i in range(16)]
    words2 = words1.copy()
    if changed:
        assert chaining == 'free' and n == 1
        # Preserve T1 and the full one-step working state, but change H_h.
        cv2[7] = (cv2[7] + 1) & m
        words2[0] = (words2[0] - 1) & m
    def order(cv, words):
        return words + ([] if chaining == 'iv' else [cv[j] for i in range(4) for j in (i, 4+i)])
    inputs = iter(order(cv1, words1) + order(cv2, words2))
    instances = []
    base = mod['CNF']

    class Evaluated(base):
        def __init__(self):
            super().__init__()
            self.values = {1: True}
            self.equalities = []
            instances.append(self)
        def value(self, lit):
            return self.values[abs(lit)] == (lit > 0)
        def set(self, lit, value):
            bit = bool(value) == (lit > 0)
            if abs(lit) in self.values:
                assert self.values[abs(lit)] == bit
            self.values[abs(lit)] = bit
            return lit
        def word(self):
            result = super().word()
            value = next(inputs)
            for i, lit in enumerate(result):
                self.set(lit, (value >> i) & 1)
            return result
        def xor2(self, a, b):
            return self.set(super().xor2(a, b), self.value(a) ^ self.value(b))
        def maj(self, a, b, c):
            return self.set(super().maj(a, b, c), sum(self.value(x) for x in (a, b, c)) >= 2)
        def ch(self, e, f, g):
            return self.set(super().ch(e, f, g), self.value(f) if self.value(e) else self.value(g))
        def eq(self, a, b):
            self.equalities.append((a, b))
            return super().eq(a, b)

    mod['CNF'] = Evaluated
    xml, cnf, mapping = (folder / (name + suffix) for suffix in ('.xml', '.cnf', '.map'))
    xml.write_text(f'<config><param name="n" value="{n}"/></config>', encoding='utf-8')
    with contextlib.redirect_stdout(io.StringIO()):
        mod['encode'](str(xml), str(cnf), str(mapping), chaining)
    c, = instances
    assert next(inputs, None) is None
    mp = json.loads(mapping.read_text())
    assert set(c.values) == set(range(1, c.nv+1)), 'Unevaluated gate'
    def word(bits):
        return sum(int(c.value(lit)) << i for i, lit in enumerate(bits))
    state_results = []
    for side, cv, words in (('1', cv1, words1), ('2', cv2, words2)):
        state = [word(mp[reg+side+'all'][str(n-1-i)]) for reg in ('A', 'E') for i in range(4)]
        expected = reference(words, cv, n, width, mod['K'], offset)
        assert state == expected
        state_results.append(state)
        if feed:
            assert [word(x) for x in mp['H'+side]] == [(a+b) & m for a, b in zip(cv, state)]
    # Check actual serialized clauses, not just the in-memory list.
    lines = cnf.read_text().splitlines()
    assert lines[0] == f'p cnf {c.nv} {len(c.cl)}'
    serialized = [list(map(int, line.split()))[:-1] for line in lines[1:]]
    assert serialized == c.cl and not c.xcl
    bad = sum(not any(c.value(lit) for lit in clause) for clause in serialized)
    should_fail = changed and feed and not trunc
    assert bool(bad) == should_fail
    if feed and not reuse:
        assert len(c.equalities) == (7 if trunc else 8) * width
    assert 'KOFF' not in mp and 'koff' not in mp and 'TRUNC224' not in mp and 'trunc224' not in mp
    model = folder / (name + '.model')
    model.write_text('v ' + ' '.join(str(k if v else -k) for k, v in c.values.items()) + ' 0\n')
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        mod['decode'](str(mapping), str(model))
    if changed:
        assert state_results[0] == state_results[1]
        assert 'messages differ: True  outputs equal: True' in output.getvalue()
        assert word(mp['H1'][7]) != word(mp['H2'][7])
    if offset:
        assert list(mod['sha_ref'](n, cv1, words1, width)) != state_results[0]
    # Synthetic true-constant difference fixture is not reachable at the literal
    # level in these real instances (including fixed IV and DIFFVARS).
    for reg in ('A', 'E'):
        for t in range(-4, n):
            for a, b in zip(mp[reg+'1all'][str(t)], mp[reg+'2all'][str(t)]):
                assert not (abs(a) == abs(b) == 1 and a != b)
        if reuse:
            assert all(lit != 1 for bits in mp['D'+reg].values() for lit in bits)
    return {'name': name, 'width': width, 'rounds': n, 'koff': offset, 'truncation': trunc,
            'feedforward': feed, 'chaining': chaining, 'diffvars': reuse,
            'variables': c.nv, 'clauses': len(c.cl), 'unsatisfied_clauses': bad,
            'expected_complete_assignment_pass': not should_fail}


results = []
with tempfile.TemporaryDirectory(prefix='library-current-encoder-') as temp:
    folder = Path(temp)
    copy = folder / 'sha_cnf.py'
    shutil.copyfile(SOURCE, copy)
    for width in (8, 32):
        for chaining in ('free', 'iv'):
            results.append(fixture(folder, copy, f'w{width}-{chaining}', width=width, chaining=chaining))
        for trunc in (False, True):
            results.append(fixture(folder, copy, f'w{width}-changed-{trunc}', width=width, trunc=trunc, changed=True))
        results.append(fixture(folder, copy, f'w{width}-offset', width=width, offset=5))
        results.append(fixture(folder, copy, f'w{width}-schedule', width=width, n=17, reuse=True))
    # Full encode confirms malformed ranges are silently vacuous, not rejected.
    range_results = []
    for setting in ('PREHEAD_K', 'PREHEAD_ROWCAP'):
        for span in ('1-0', '4-6'):
            mod = load(copy, {'WBITS': 8, setting: 0, 'PREHEAD_ROWS': span})
            xml = folder / 'range.xml'
            xml.write_text('<param name="n" value="1"/>')
            def encode_to(stem):
                with contextlib.redirect_stdout(io.StringIO()):
                    mod['encode'](str(xml), str(folder / (stem+'.cnf')), str(folder / (stem+'.map')))
                return (folder / (stem+'.cnf')).read_bytes()
            with_cap = encode_to('cap')
            mod[setting] = ''
            assert with_cap == encode_to('no-cap')
            range_results.append({'setting': setting, 'rows': span, 'identical_to_no_cap': True})

report = {'passed': True, 'finished_at': datetime.now(timezone.utc).isoformat(),
          'source_sha256': SHA, 'copied_full_source_loaded': True, 'external_solver_or_search': False,
          'fixtures': results, 'vacuous_ranges': range_results,
          'findings': [
              'FEEDFWD gate values agree with CV plus independent working-state arithmetic in all named fixtures.',
              'TRUNC224 equates seven words; a compensated h/message change passes the seven-word predicate but fails all-eight equality.',
              'Decoder outputs-equal is working-state equality, not the feedforward or truncated predicate. It also accepts and displays an unsatisfying model without checking clauses.',
              'KOFF=5 is applied by the circuit but not sha_ref/decode, and the map omits the offset and truncation setting.',
              'Reversed or absent positive preheader ranges produce byte-identical CNF to no cap.',
              'No opposite constant A/E input literals occur in these fixtures. The separate synthetic constant-accounting issue does not demonstrate a real-instance failure.'
          ],
          'limits': 'Twelve fixed-input circuit evaluations, four range controls; no SAT search, probability estimate, all-option validation, or historical-verdict audit. Source files unchanged.'}
# Offline replay prints only; no repository report write.
print(json.dumps(report, indent=2))
