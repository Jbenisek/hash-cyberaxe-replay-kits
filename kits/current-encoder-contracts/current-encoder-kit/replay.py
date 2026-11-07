"""Offline wrapper: verify exact payloads, then run the bounded contract."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

if not __debug__:
    raise SystemExit('Run without -O; checks must remain enabled')
HERE = Path(__file__).resolve().parent
manifest = json.loads((HERE / 'MANIFEST.json').read_text(encoding='utf-8'))
for row in manifest['files']:
    path = HERE / row['path']
    if path.parent != HERE or not path.is_file():
        raise SystemExit('Invalid or missing kit file')
    raw = path.read_bytes()
    if len(raw) != row['bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
        raise SystemExit('Kit file differs: ' + row['path'])
proc = subprocess.run([sys.executable, '-I', '-B', str(HERE / 'check.py')],
                      cwd=HERE, capture_output=True, text=True, timeout=30)
if proc.returncode:
    raise SystemExit(proc.stderr)
report = json.loads(proc.stdout)
assert report['passed'] and len(report['fixtures']) == 12 and len(report['vacuous_ranges']) == 4
assert sum(not r['expected_complete_assignment_pass'] for r in report['fixtures']) == 2
assert not report['external_solver_or_search']
print(json.dumps(report, indent=2))
