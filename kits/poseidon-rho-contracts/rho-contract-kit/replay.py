"""Verify payload identity, run only the bounded rho contract fixtures."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

if not __debug__:
    raise SystemExit('Run without -O')
HERE = Path(__file__).resolve().parent
for row in json.loads((HERE / 'MANIFEST.json').read_text())['files']:
    path = HERE / row['path']
    if path.parent != HERE or not path.is_file():
        raise SystemExit('Missing or invalid kit file')
    raw = path.read_bytes()
    if len(raw) != row['bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
        raise SystemExit('Kit file changed: ' + row['path'])
p = subprocess.run([sys.executable, '-I', '-B', str(HERE / 'check.py')], cwd=HERE,
                   capture_output=True, text=True, timeout=30)
if p.returncode:
    raise SystemExit(p.stderr)
r = json.loads(p.stdout)
assert r['passed'] and r['exhaustive_graph_cases'] == 17066 and r['packed_field_cases'] == 1536
assert r['found_valid_graph_pairs'] == 4408
assert not r['full_field_attempt_run'] and not r['parameter_tuning_run']
print(json.dumps(r, indent=2))
