"""Replay synthetic log semantics only, with pinned source integrity."""
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
assert report['passed'] and report['controls'] == 13
assert report['split_files_stall'] == .5 and report['appended_runs_stall'] == 0
assert report['duplicate_path_stall'] == '2/3' and report['empty_rank_writes_newline']
print(json.dumps(report,indent=2))
