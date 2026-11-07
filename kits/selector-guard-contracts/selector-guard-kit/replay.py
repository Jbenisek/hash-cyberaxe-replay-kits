"""Offline finite option-interaction replay; no solver or historical run."""
import hashlib
import json
from pathlib import Path
import sys

if not __debug__:
    raise SystemExit('Run without -O')
HERE = Path(__file__).resolve().parent
manifest = json.loads((HERE/'MANIFEST.json').read_text(encoding='utf-8'))
expected = {'sha_cnf.py', 'check.py', 'replay.py', 'README.txt', 'PROVENANCE.json'}
if {row['path'] for row in manifest['files']} != expected or len(manifest['files']) != len(expected):
    raise SystemExit('Invalid kit inventory')
for row in manifest['files']:
    path = (HERE/row['path']).resolve()
    if not path.is_relative_to(HERE) or not path.is_file():
        raise SystemExit('Missing kit file')
    raw = path.read_bytes()
    if len(raw) != row['bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
        raise SystemExit('Changed kit file: ' + row['path'])
sys.path.insert(0, str(HERE))
import check
result = check.main(source=HERE/'sha_cnf.py', print_summary=False)
assert result['passed'] and len(result['fixtures']) == 12
assert result['unit_propagator_controls'] == 4
print(json.dumps(result, indent=2))
