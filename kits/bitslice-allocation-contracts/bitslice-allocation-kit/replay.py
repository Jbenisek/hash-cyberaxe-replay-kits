"""Portable finite step-allocation and statistic replay; no hash searches."""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import runpy
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

if not __debug__:
    raise SystemExit('Run without -O; assertions are required')
HERE = Path(__file__).resolve().parent
SOURCES = {
    'single_block.py': ('b8341c83cfbdfd05cc52bd99d8a5e97ac46c0e008549082da4be5d764b917bfa', 19022),
    'fixed_prefix.py': ('4f46578df1c1bec00b363b269bd139833fd61c3f734f4c5513685f60cd2ee943', 18869),
}
SCOPE = ('The generated straight-line program and register assignment agree structurally. '
         'This does not prove universal hash-generator correctness, caller/handler allocation, '
         'historical search execution, success probability or full attack price. '
         'The repeated-entry counterexample uses artificial outputs, not hash collisions.')

def verify_allocation(st, code, registers):
    # Structural certificate for this generated straight-line allocation.
    # Induction: every allocated operand still holds its named SSA value;
    # writing the destination establishes that invariant for the next line.
    # This covers every plane input, but not generation/hash equivalence or
    # handler/caller storage beyond the emitted step.
    function = ast.parse(st.src).body[0]
    assert [a.arg for a in function.args.args] == [f'i{j}' for j in range(st.n)]
    assignments = function.body[:-1]
    assert len(assignments) == len(code) == len(st.lines)
    held = {j: f'i{j}' for j in range(st.n)}
    operators = {'^': ast.BitXor, '&': ast.BitAnd, '|': ast.BitOr}
    for syntax, row, allocated in zip(assignments, st.lines, code):
        name, a, b = row
        nm, dst, ra, rb = allocated
        op, immediate = st.opsym[name]
        assert nm == name and isinstance(syntax, ast.Assign)
        assert len(syntax.targets) == 1 and syntax.targets[0].id == name
        expr = syntax.value
        assert isinstance(expr, ast.BinOp) and isinstance(expr.op, operators[op])
        if a == '0':
            assert ra == -1 and isinstance(expr.left, ast.Constant) and expr.left.value == 0
        else:
            assert held.get(ra) == a and isinstance(expr.left, ast.Name) and expr.left.id == a
        if immediate:
            assert b == '#' and isinstance(expr.right, ast.Constant) and expr.right.value == ((1 << 256) - 1)
        elif b == '0':
            assert rb == -1 and isinstance(expr.right, ast.Constant) and expr.right.value == 0
        else:
            assert held.get(rb) == b and isinstance(expr.right, ast.Name) and expr.right.id == b
        assert 0 <= dst < registers
        held[dst] = name
    assert isinstance(function.body[-1], ast.Return)
    assert [e.id for e in function.body[-1].value.elts] == st.outs
    assert [held[j] for j in range(st.n)] == st.outs
    return len(code)

def main():
    manifest = json.loads((HERE / 'MANIFEST.json').read_text(encoding='utf-8'))
    expected_files = set(SOURCES) | {'replay.py', 'README.txt', 'PROVENANCE.json'}
    assert {row['path'] for row in manifest['files']} == expected_files
    assert len(manifest['files']) == len(expected_files)
    for row in manifest['files']:
        assert Path(row['path']).name == row['path']
        raw = (HERE / row['path']).read_bytes()
        assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256']
    results = []
    for name, (pin, expected_ops) in SOURCES.items():
        raw = (HERE / name).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == pin
        with tempfile.TemporaryDirectory(prefix='bitslice-allocation-replay-') as temp:
            copy = Path(temp) / 'source.py'
            copy.write_bytes(raw)
            m = runpy.run_path(str(copy), run_name='finite_copy')['serve'].__globals__
            step = m['step256']()
            code, registers = m['allocate'](step)
            assert step.ops == expected_ops and registers == 771
            assert verify_allocation(step, code, registers) == expected_ops
            # Reject two distinct ways of disconnecting an assignment from
            # its generated program; never modify the retained source.
            altered = list(code)
            nm, dst, ra, rb = altered[0]
            altered[0] = (nm, dst, registers + 1, rb)
            try:
                verify_allocation(step, altered, registers)
            except AssertionError:
                pass
            else:
                raise AssertionError('Altered register was accepted')
            other = SimpleNamespace(**vars(step))
            tree = ast.parse(step.src)
            op = tree.body[0].body[0].value
            op.op = ast.BitAnd() if not isinstance(op.op, ast.BitAnd) else ast.BitOr()
            other.src = ast.unparse(tree)
            try:
                verify_allocation(other, code, registers)
            except AssertionError:
                pass
            else:
                raise AssertionError('Altered instruction was accepted')
            values = [5, 5, 5, 7]
            fake = SimpleNamespace(pin=[0] * 256, step=lambda *planes: values)
            with patch.dict(m, {'LANES': 4, 'M_T2': 4,
                                'pack_lanes': lambda xs, *args: xs,
                                'lanes_of': lambda xs, *args: xs}):
                a, b, obs = m['e2_trial']('finite-statistic-fixture', 1, fake)
            pairs = sum(c * (c - 1) // 2 for c in Counter(values).values())
            assert obs['dup_w0'] == 2 and pairs == 3 and a != b
            results.append({'source': name, 'source_sha256': pin,
                'step_instructions_checked': expected_ops, 'register_extent': registers,
                'tamper_controls_rejected': 2, 'artificial_duplicate_count': 2,
                'artificial_equal_pairs': 3})
    print(json.dumps({'passed': True, 'results': results, 'scope': SCOPE}, indent=2))

if __name__ == '__main__':
    main()
