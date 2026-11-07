"""Bounded r56 source contracts; no full-field walk or parameter search."""
import contextlib
import hashlib
import io
import itertools
import json
from pathlib import Path
import runpy
import shutil
import tempfile
from datetime import datetime, timezone

if not __debug__:
    raise SystemExit('Run without -O')
PUB = Path(__file__).resolve().parents[1]
SOURCE = Path(__file__).resolve().parent / 'rho.py'
SHA = 'b5bd922909b12d8871b381c7a1bc4255541241b45df0adb18fe5ad4c3f53773c'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SHA
with tempfile.TemporaryDirectory(prefix='library-rho-contract-') as temp:
    copy = Path(temp) / 'rho.py'
    shutil.copyfile(SOURCE, copy)
    with contextlib.redirect_stdout(io.StringIO()):
        m = runpy.run_path(str(copy), run_name='bounded_library_rho')
    plan = m['plan']()
    assert plan['partial_rounds'] == 56 and len(m['ROUND_IDX']) == 64
    assert plan['step_field_ops'] == 807 and plan['C'] == 1392
    assert plan['memory']['total'] <= 1 << 20
    assert plan['steps'] == m['STEPS'] and plan['steps'] % m['UNROLL'] == 0
    p = m['P']
    base = m['after_round1'](*m['message'](0))
    next_state = m['after_round1'](*m['message'](1))
    inputs = (0, 1, 2, 123456789, p-1)
    messages = [m['message'](x) for x in inputs]
    assert len(set(messages)) == len(inputs)
    for x, message in zip(inputs, messages):
        assert all(0 <= v < p for v in message)
        state = m['after_round1'](*message)
        assert state == [(a+x*(b-a)) % p for a, b in zip(base, next_state)]
    equivalent = 0
    for kappa in (1, 2, 19):
        step = m['make_F'](kappa)
        _, outscale = m['kappa_consts'](kappa)
        assert outscale
        for x in (0, 1, p-1):
            message = m['message']((kappa*x-m['E0'][0]) % p)
            assert step(x) == m['digest'](*message) * pow(outscale, -1, p) % p
            equivalent += 1
    # Every bit offset, both packed field widths, including both word boundaries.
    packed = 0
    for width in (m['VBITS'], m['GBITS']):
        for offset in range(256):
            for value in (0, 1, (1 << width)-1):
                table = [0, 0, 0]
                m['_put'](table, offset, value)
                assert m['_get'](table, offset, width) == value
                assert sum(v << (256*i) for i, v in enumerate(table)) == value << offset
                packed += 1
    # Complete graph enumeration; no sampled approximation or actual Poseidon walk.
    checks, found = 0, 0
    statuses = {}
    for size in range(1, 5):
        for graph in itertools.product(range(size), repeat=size):
            for start in range(size):
                seen, path = {}, []
                x = start
                while x not in seen:
                    seen[x] = len(path)
                    path.append(x)
                    x = graph[x]
                tail = seen[x]
                cycle = path[tail:]
                for mask in range(1 << size):
                    predicate = lambda value, mask=mask: bool(mask & (1 << value))
                    pair, status, evaluations, ops = m['search'](graph.__getitem__, predicate, start, 18, size+1, size+1)
                    expected = tail > 0 and any(predicate(v) for v in cycle)
                    assert (pair is not None) == expected, (graph, start, mask, status)
                    if pair is not None:
                        a, b = pair
                        assert a != b and graph[a] == graph[b]
                        found += 1
                    assert evaluations == ops['trail'] + ops['rec']
                    assert ops['trail'] <= 18 and ops['rec'] <= 3*(size+1)
                    statuses[status] = statuses.get(status, 0) + 1
                    checks += 1
    assert checks == 17066
    # The API documents a block-multiple precondition but does not enforce it.
    _, status, evaluations, _ = m['search'](lambda x: x, lambda x: False, 0, 1, 1, 1)
    assert status == 'steps' and evaluations == 18
    # OR-insertion is append-only, not a general overwrite primitive.
    table = [0, 0]
    m['_put'](table, 0, 3)
    m['_put'](table, 0, 0)
    assert m['_get'](table, 0, 2) == 3
report = {'passed': True, 'finished_at': datetime.now(timezone.utc).isoformat(),
          'source_sha256': SHA, 'plan': plan, 'line_points': len(inputs),
          'step_reference_comparisons': equivalent, 'packed_field_cases': packed,
          'exhaustive_graph_cases': checks, 'found_valid_graph_pairs': found, 'graph_statuses': statuses,
          'invalid_nonmultiple_step_budget_overshoots_to': 18, 'put_is_or_not_overwrite': True,
          'full_field_attempt_run': False, 'parameter_tuning_run': False,
          'scope': 'Exact finite graph enumeration and named arithmetic/packing fixtures. Plan output remains conditional on H1 for the actual field map; no success-rate proof, full instruction listing audit, CPU timing claim or complete memory-price certification.'}
# Offline replay prints only.
print(json.dumps(report, indent=2))
