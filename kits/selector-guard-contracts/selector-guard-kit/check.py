"""Finite unit-propagation controls for a pinned encoder option interaction.

Only a copied encoder's one-step, fixed-input emission is called. No solver,
selftest, external process or search is used. Public artifacts are not changed.
"""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import runpy
import tempfile
from datetime import datetime, timezone
from unittest.mock import patch

if not __debug__:
    raise SystemExit('Run without -O')
PUB = Path(__file__).resolve().parents[1]
SOURCE = PUB.parents[1] / 'research/game/climber/guided/kit/sha_cnf.py'
PIN = 'cb02f7a8615528db855d66c364288dd94f2c4ffe3de667f875b073c1f0b66811'


def propagate(clauses):
    """Assign only forced unit literals. A conflict is a proof, not a timeout."""
    values = {}
    for iteration in range(10000):
        changed = False
        for clause in clauses:
            if any(values.get(abs(lit)) == (lit > 0) for lit in clause if abs(lit) in values):
                continue
            free = [lit for lit in clause if abs(lit) not in values]
            if not free:
                return {'conflict': True, 'all_clauses_satisfied': False,
                        'assigned_variables': len(values), 'passes': iteration + 1}
            if len(free) == 1:
                lit = free[0]
                values[abs(lit)] = lit > 0
                changed = True
        if not changed:
            complete = all(any(abs(lit) in values and values[abs(lit)] == (lit > 0)
                               for lit in clause) for clause in clauses)
            return {'conflict': False, 'all_clauses_satisfied': complete,
                    'assigned_variables': len(values), 'passes': iteration + 1}
    raise AssertionError('Bound exceeded: do not turn this into an unrestricted search')


def one_step_a(word):
    """Independent fixed-IV arithmetic; only W0 differs in the fixture."""
    a, b, c, d, e, f, g, h = (0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
                             0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19)
    mask = 0xffffffff
    def rot(x, k):
        return ((x >> k) | (x << (32-k))) & mask
    first = h + (rot(e, 6) ^ rot(e, 11) ^ rot(e, 25)) + ((e & f) ^ (~e & g)) + 0x428a2f98 + word
    second = (rot(a, 2) ^ rot(a, 13) ^ rot(a, 22)) + ((a & b) ^ (a & c) ^ (b & c))
    return (first + second) & mask


def main(source=SOURCE, report_path=None, print_summary=True):
    raw = source.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == PIN
    # Unit-propagator positive and negative controls, including an empty clause.
    assert propagate([[1], [-1, 2]])['all_clauses_satisfied']
    assert propagate([[1], [-1]])['conflict']
    assert propagate([[]])['conflict']
    assert not propagate([[1, 2]])['all_clauses_satisfied']
    assert (one_step_a(0) ^ one_step_a(1)) & 1
    results = []
    with tempfile.TemporaryDirectory(prefix='library-selector-controls-') as temporary:
        folder = Path(temporary)
        copy = folder / 'sha_cnf.py'
        copy.write_bytes(raw)
        xml = folder / 'fixture.xml'
        xml.write_text('<param name="n" value="1"/>\n0 A: ' + '?'*31 + '- E: ' + '?'*32 + '\n', encoding='utf-8')
        for granularity in ('row', 'reg', 'bit'):
            for eqlink, selected, changed in ((False, False, True), (True, False, True),
                                             (False, True, True), (True, False, False)):
                pins1 = ','.join(f'{i}:00000000' for i in range(16))
                pins2 = ','.join(f'{i}:{int(changed and i == 0):08x}' for i in range(16))
                settings = {'ROW_SELECTORS': '1', 'SEL_FROM': '0', 'SEL_GRAN': granularity,
                            'EQLINK': str(int(eqlink)), 'PIN1': pins1, 'PIN2': pins2}
                # Explicitly empty option environment; do not inherit research modes.
                with patch.dict(os.environ, settings, clear=True):
                    mod = runpy.run_path(str(copy), run_name='library_selector_fixture')
                    with contextlib.redirect_stdout(io.StringIO()):
                        mod['encode'](str(xml), str(folder/'fixture.cnf'), str(folder/'fixture.map'), 'iv')
                mp = json.loads((folder/'fixture.map').read_text(encoding='utf-8'))
                lines = (folder/'fixture.cnf').read_text(encoding='utf-8').splitlines()
                assert not any(line.startswith('x') for line in lines)
                clauses = [list(map(int, line.split()))[:-1] for line in lines[1:]]
                assert int(lines[0].split()[3]) == len(clauses)
                assert mp['selectors']
                clauses += [[variable if selected else -variable] for variable in mp['selectors'].values()]
                result = propagate(clauses)
                expected_conflict = changed and (eqlink or selected)
                assert result['conflict'] == expected_conflict, (settings, result)
                assert result['all_clauses_satisfied'] == (not expected_conflict)
                results.append({'granularity': granularity, 'eqlink': eqlink,
                                'all_row_selectors_assumed': selected, 'W0_side_b': int(changed),
                                'emitted_variables': int(lines[0].split()[2]),
                                'emitted_clauses': len(lines)-1, **result})
    assert source.read_bytes() == raw
    report = {'passed': True, 'finished_at': datetime.now(timezone.utc).isoformat(),
              'source_sha256': PIN, 'source_bytes': len(raw), 'fixtures': results,
              'unit_propagator_controls': 4, 'independent_A0': [f'{one_step_a(x):08x}' for x in (0, 1)],
              'finding': 'EQLINK reasserts a guarded equality seed unconditionally. A fixed-input one-step instance satisfiable with every row selector false becomes unit-contradictory when EQLINK is enabled. Reproduced for row, reg and bit selector granularity.',
              'mechanism': 'apply_shape records eqpairs while c.guard is set. encode clears c.guard before eqlink; eqlink asserts each seed e without carrying its original guard.',
              'scope': 'Twelve fixed-input one-step CNF fixtures, four unit-propagator controls, no search or external solver. Not a claim about historical runs, other option combinations, full encoder soundness or collision discovery.',
              'recommendation': 'Do not combine EQLINK with relaxed row selectors for claims of prefix feasibility without a guard-aware correction and fresh tests. Preserve the historical edition and its artifacts; review any affected experimental configurations separately.'}
    if report_path is not None:
        report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    if print_summary:
        print(json.dumps(report, indent=2))
    return report


if __name__ == '__main__':
    main(report_path=PUB/'qa/live-encoder-selector-controls.json')
