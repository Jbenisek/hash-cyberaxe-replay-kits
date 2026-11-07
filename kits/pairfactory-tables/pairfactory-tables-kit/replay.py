"""Verify identities and recount four historical tables, without any solver."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

if not __debug__:
    raise SystemExit('Run without -O')
HERE=Path(__file__).resolve().parent
for row in json.loads((HERE/'MANIFEST.json').read_text(encoding='utf-8'))['files']:
    target=(HERE/row['path']).resolve()
    if not target.is_relative_to(HERE) or not target.is_file():
        raise SystemExit('Missing or invalid kit file')
    raw=target.read_bytes()
    if len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:
        raise SystemExit('Changed kit file: '+row['path'])
proc=subprocess.run([sys.executable,'-I','-B',str(HERE/'check.py')],cwd=HERE,
                    capture_output=True,text=True,timeout=15)
if proc.returncode:
    raise SystemExit(proc.stderr)
report=json.loads(proc.stdout)
assert report['passed'] and sum(s['rows'] for s in report['sources'])==310
assert report['classes']['rows']==128 and report['classes']['priced_classes']==33
assert report['results']['RESULTS2.tsv']['reused_job_numbers']==6
assert report['stage_b_summary_entries_matched']==7
tails=subprocess.run([sys.executable,'-I','-B',str(HERE/'recount_tails.py')],cwd=HERE,
                     capture_output=True,text=True,timeout=15)
if tails.returncode:
    raise SystemExit(tails.stderr)
report['tail_observations']=json.loads(tails.stdout)
assert report['tail_observations']['passed']
print(json.dumps(report,indent=2))
