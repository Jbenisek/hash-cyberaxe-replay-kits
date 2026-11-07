"""Run the finite r37/r38 arithmetic lesson, not a cryptanalytic search."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

if not __debug__:
    raise SystemExit('Run without -O')
ROOT = Path(__file__).resolve().parent
manifest = json.loads((ROOT / 'MANIFEST.json').read_text(encoding='utf-8'))
expected = {'check37.py', 'check38.py', 'price.py', 'model37.py', 'model38.py',
            'runs/costs.json', 'runs/pre1.json', 'runs/pre2.json',
            'README.md', 'PROVENANCE.json', 'replay.py'}
names = [r['path'] for r in manifest['files']]
assert len(names) == len(set(names)) and set(names) == expected
for row in manifest['files']:
    raw = (ROOT / row['path']).read_bytes()
    assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256']
reports = {}
for kind in ('37', '38'):
    result = subprocess.run([sys.executable, '-I', '-B', str(ROOT / ('check' + kind + '.py'))],
                            cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    reports['r' + kind] = json.loads(result.stdout)
assert reports['r37']['passed'] and reports['r37']['grid_rows'] == 33
assert reports['r38']['passed'] and reports['r38']['grid_rows'] == 46
assert reports['r37']['best_shard_k'] == 5 and reports['r38']['best_shard_k'] == 19
assert reports['r37']['memory_floor_affected_k'] == [28, 29, 30, 31, 32]
print(json.dumps({'passed': True, 'grid_rows': 79, 'rigorous_rounding_certificates': 191,
                  'best_k': {'r37': 5, 'r38': 19}, 'reports': reports,
                  'scope': 'Finite arithmetic of historical, conditional shard models. Sample means, success laws, independence, layouts and actual operation costs are not proved by this replay.'}, indent=2))
