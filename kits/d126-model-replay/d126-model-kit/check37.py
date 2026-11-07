"""Replay D126's selected r37 arithmetic; do not execute its research program.

The sampled means, attack success rate and shard distribution are premises,
not conclusions of this finite arithmetic audit.
"""
import ast
import hashlib
import json
import math
import os
from datetime import datetime, timezone
from decimal import Decimal, getcontext
from fractions import Fraction as F
from pathlib import Path
from types import SimpleNamespace

if not __debug__:
    raise SystemExit('Run without -O')
PUB = ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'price.py'
DEPENDENCY = ROOT / 'model37.py'
PINS = {
    SOURCE: '1c066a7647f5ead8dc9e4eb650193b890c584010d5569c37b8088ba2368874a7',
    DEPENDENCY: '5a382ce398e4e7671145d49d0aedde6e9bf3dcc0f59b9076d9da285b3b250c04',
}
raw = {p: p.read_bytes() for p in PINS}
assert all(hashlib.sha256(raw[p]).hexdigest() == sha for p, sha in PINS.items())

# Whitelist the selected assignments and three inspected helpers. No trace(),
# table construction, module imports, ledger(), CLI, selftest or solver runs.
needed = {'CLASSES', 'STATS', 'SCAN_LANE', 'RARE_LOOKUP', 'ROWCHECK', 'ROWCOMP',
          'GROUP_OPS', 'LANE_UB', 'W6_OPS', 'ZPLANE_OPS', 'CLASS_OVH', 'SEG_OVH',
          'FBFIX', 'Q3_LOG2', 'STAT_SAFETY', 'R16X_WORDS', 'R16X_BUILD',
          'PRE_ITEMS', 'CVPRE_OPS'}
helpers = {'load_stats', 'chunk_fixed_ops', 'scan_bound_ok'}
selected = []
found = set()
for node in ast.parse(raw[DEPENDENCY].decode('utf-8')).body:
    if isinstance(node, ast.Assign):
        names = {n.id for target in node.targets for n in ast.walk(target)
                 if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
        if names & needed:
            selected.append(node)
            found.update(names & needed)
    elif isinstance(node, ast.FunctionDef) and node.name in helpers:
        selected.append(node)
        found.add(node.name)
assert found == needed | helpers
dep = {'Fr': F, 'math': math}
exec(compile(ast.Module(body=selected, type_ignores=[]), 'pinned-r37-selected-inputs', 'exec'), dep)
m = SimpleNamespace(**{k: dep[k] for k in needed | helpers})
assert m.scan_bound_ok()
stats = m.load_stats()
assert len(m.CLASSES) == len(stats) == 222
assert set(stats) == set(range(222))
assert all(stats[i][0] == row[3] for i, row in enumerate(m.CLASSES))
assert all(all(v >= 0 for v in row) for row in stats.values())

def loaded(path, name):
    assert name == 'xtab_d126'
    assert str(path).replace('\\', '/').endswith('/experiments/xtab.py')
    return m

names = {'ceil_frac', 'lg', 'r37_rows'}
functions = [n for n in ast.parse(raw[SOURCE].decode('utf-8')).body
             if isinstance(n, ast.FunctionDef) and n.name in names]
assert len(functions) == 3
getcontext().prec = 90  # price.py's precision; selected dependency does not reset it.
env = {'F': F, 'Decimal': Decimal, 'math': math, 'os': os,
       'ROOT': 'fixture-root', 'load': loaded}
exec(compile(ast.Module(body=functions, type_ignores=[]), 'pinned-r37-functions', 'exec'), env)
rows = env['r37_rows']()
assert [r[0] for r in rows] == list(range(33))
assert rows[0][1:4] == (358862050277539966, F(2137189670580414105336, 661), 1105515320967168)
assert rows[5][1:4] == (11480695164613822619, F(89459989869750967895523, 1322), 35088251224064)

# Independent exact reconstruction of the model's expectation and caps.
p7, p6, pr16 = F(68157440, 1 << 32), F(287309824, 1 << 32), F(1052672, 1 << 32)
nvar = sum(c[3] for c in m.CLASSES)
g = nvar * p7 * p6
pair = 201 + 23 + 1 + m.RARE_LOOKUP
rowcost = m.ROWCOMP + m.ROWCHECK + 1
lane = 8 + 2 * rowcost
mean_classes = F(0)
max_classes = F(0)
for i, cls in enumerate(m.CLASSES):
    n, fibres, batches, groups, _ = stats[i]
    assert n == cls[3]
    fibres *= m.STAT_SAFETY
    batches *= m.STAT_SAFETY
    groups *= m.STAT_SAFETY
    mean_classes += (m.CLASS_OVH + (m.W6_OPS - 1) * batches + fibres / 8 + F(23, 8)
                     + p6 * fibres * (m.SCAN_LANE + 1 + m.SEG_OVH + m.LANE_UB[1])
                     + p6 * groups * m.GROUP_OPS)
    max_classes += (m.CLASS_OVH + ((n + 255) // 256) * (m.W6_OPS + 1 + m.chunk_fixed_ops(256))
                    + n * (m.SCAN_LANE + 1 + m.SEG_OVH + m.GROUP_OPS))
vbar = (F(16, 100) * (3 + m.ZPLANE_OPS + m.CVPRE_OPS) + p7 * mean_classes
        + g * m.LANE_UB[0] + g * pr16 * (pair + lane + 19 * F(1, 512) * rowcost))
vmax_fb = (max_classes + nvar * (sum(m.LANE_UB) + 3 + pair + 32 * (lane + 19 * rowcost))
           + 200 + 2 * m.ZPLANE_OPS)
fl = math.floor(m.Q3_LOG2)
q3 = F(2) ** fl * F(math.floor(2 ** (m.Q3_LOG2 - fl) * 2 ** 40), 2 ** 40)
# The historical floating calculation happens to give a lower rate than
# the intended exact decimal exponent -74.03: certify it with integers.
assert q3.numerator ** 100 * (1 << 7403) <= q3.denominator ** 100
pre4 = m.PRE_ITEMS[3]
assert (pre4 - 1) ** 10 < 1 << 387 <= pre4 ** 10

# Reuse ONLY the inspected rational-analysis helper definitions. Importing the
# other audit module would execute r38; AST selection avoids that side effect.
analysis_path = PUB / 'check38.py'
analysis_names = {'ln_bounds', 'log2_bounds', 'certify_up5', 'exp_negative_upper'}
nodes = [n for n in ast.parse(analysis_path.read_text(encoding='utf-8')).body
         if isinstance(n, ast.FunctionDef) and n.name in analysis_names]
assert len(nodes) == 4
proof = {'F': F, 'math': math}
exec(compile(ast.Module(body=nodes, type_ignores=[]), 'rational-analysis-helpers', 'exec'), proof)
proof['ln2'] = proof['ln_bounds'](F(2))

# Bound 2^-10.4 from above by a rational, via an integer fifth root.
# Thus d_lower <= 1 - 2^-10.4, independently of Decimal/float calculations.
lo, hi = 0, 1 << 80
target = 1 << 348
while hi - lo > 1:
    mid = (lo + hi) // 2
    if mid ** 5 < target:
        lo = mid
    else:
        hi = mid
assert lo ** 5 < target <= hi ** 5
d_lower = 1 - F(hi, 1 << 80)
ceil = env['ceil_frac']
table_bytes = (1 << 32) * 8 + 15130951680 * 73024
fixed_bytes = (1 << 34) * 32 + (1 << 33)
records = []
for k, nfb, T, mem, tl, ml in rows:
    B = 1 << k
    pcap = vmax_fb / (F(1, 2048) ** 2 * nfb * vbar)
    x = d_lower * nfb * g * 32 * q3 / B
    success_lower = 1 - proof['exp_negative_upper'](x) - pcap - F(1, 1 << 60)
    assert success_lower >= F(39, 100), k
    pre = sum(m.PRE_ITEMS[3:]) + sum(ceil(F(v, B)) for v in m.PRE_ITEMS[:3])
    rebuilt = (F(2 ** 60 + 2 ** 50 + 2 ** 40) + nfb
               + F(nfb * m.FBFIX + ceil((1 + F(1, 2048)) * nfb * vbar)
                   + ceil(vmax_fb) + pre + 1600, 2644) + 6)
    assert rebuilt == T
    assert mem == table_bytes // B + fixed_bytes
    corrected_mem = ceil(F(table_bytes, B)) + fixed_bytes
    score = T * max(F(1), F(mem, 1 << 20))
    corrected_score = T * max(F(1), F(corrected_mem, 1 << 20))
    records.append({'k': k, 'first_blocks': nfb, 'T_num': T.numerator, 'T_den': T.denominator,
                    'memory_bytes': mem, 'memory_ceil_bytes': corrected_mem,
                    'memory_floor_undercount_bytes': corrected_mem - mem,
                    'time_log2_up5_units': proof['certify_up5'](T, tl),
                    'score_log2_up5_units': proof['certify_up5'](score, tl + max(0, ml - 20)),
                    'ceil_memory_score_log2_up5_units': proof['certify_up5'](corrected_score, tl + max(0, ml - 20)),
                    'model_success_at_least_39_percent_proved': True})
rank = lambda r: F(r['T_num'], r['T_den']) * max(F(1), F(r['memory_bytes'], 1 << 20))
rank_ceil = lambda r: F(r['T_num'], r['T_den']) * max(F(1), F(r['memory_ceil_bytes'], 1 << 20))
ordered = sorted(records, key=rank)
ordered_ceil = sorted(records, key=rank_ceil)
assert ordered[0]['k'] == ordered_ceil[0]['k'] == 5
assert rank(ordered[0]) < rank(ordered[1])
assert rank_ceil(ordered_ceil[0]) < rank_ceil(ordered_ceil[1])
assert records[5]['score_log2_up5_units'] == 9087121
report = {'passed': True, 'finished_at': datetime.now(timezone.utc).isoformat(),
          'source_sha256': PINS[SOURCE],
          'input_files': [{'path': DEPENDENCY.relative_to(ROOT).as_posix(), 'sha256': PINS[DEPENDENCY]}],
          'grid_rows': 33, 'class_rows': 222, 'best_shard_k': 5,
          'best_shard_with_ceil_memory_k': 5, 'rigorous_rounding_certificates': 99,
          'memory_floor_affected_k': [r['k'] for r in records if r['memory_floor_undercount_bytes']],
          'scan_bound_class_sizes_checked': 3600,
          'original_dependency_module_imported': False, 'whole_dependency_reviewed': False,
          'rows': records,
          'scope': 'Selected r37 ledger arithmetic and embedded sampled inputs only. Exact rational ranking and conditional success inequalities, not a proof of sample means, independence, shard law, implemented layout or cryptographic success. No attack, table builder or research-module CLI was run.'}
report['original_source_bytes_checked'] = False
print(json.dumps(report, indent=2))
