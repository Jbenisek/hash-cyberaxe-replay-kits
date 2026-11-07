"""Check identities and run only the finite template comparison."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

if not __debug__:
    raise SystemExit('Run without -O')
HERE = Path(__file__).resolve().parent
for row in json.loads((HERE/'MANIFEST.json').read_text(encoding='utf-8'))['files']:
    target = (HERE/row['path']).resolve()
    if not target.is_relative_to(HERE) or not target.is_file():
        raise SystemExit('Missing or invalid kit file')
    raw = target.read_bytes()
    if len(raw) != row['bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
        raise SystemExit('Changed kit file: '+row['path'])
proc = subprocess.run([sys.executable,'-I','-B',str(HERE/'check.py')],cwd=HERE,
                      capture_output=True,text=True,timeout=30)
if proc.returncode:
    raise SystemExit(proc.stderr)
report = json.loads(proc.stdout)
assert report['passed'] and report['results']['generated_templates'] == 22
assert report['results']['old_first_difference_contradictions'] == 8
assert report['results']['toy_additive_injectivity_controls'] == 65536
print(json.dumps(report,indent=2))
