"""Replay the copied XML generator contract in disposable directories."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
if not __debug__:
    raise SystemExit('Run without -O')
root = Path(__file__).resolve().parent
manifest = json.loads((root / 'MANIFEST.json').read_text(encoding='utf-8'))
assert {r['path'] for r in manifest['files']} == {'mkxml.py', 'control.xml', 'control.found.txt', 'check_contract.py', 'README.md', 'replay.py'}
for row in manifest['files']:
    raw = (root / row['path']).read_bytes()
    assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256'], row['path']
child = subprocess.run([sys.executable, '-I', '-B', str(root / 'check_contract.py')],
                       cwd=root, capture_output=True, text=True, timeout=45)
assert child.returncode == 0, child.stderr
result = json.loads(child.stdout)
assert result['passed'] and len(result['cases']) == 10
print(json.dumps(result, indent=2))
