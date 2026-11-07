"""Offline pinned schedule-cell replay; never starts a research search."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
if not __debug__:
    raise SystemExit('Run without -O')
ROOT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/'MANIFEST.json').read_text(encoding='utf-8'))
names=[r['path'] for r in manifest['files']]
assert len(names)==len(set(names))
assert set(names)=={'check_cells.py','chi37.txt','check_contract.py','replay.py','README.md'}
for row in manifest['files']:
    raw=(ROOT/row['path']).read_bytes()
    assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
result=subprocess.run([sys.executable,'-I','-B',str(ROOT/'check_contract.py')],
                      cwd=ROOT,capture_output=True,text=True,timeout=45)
assert result.returncode==0,result.stderr
data=json.loads(result.stdout)
assert data['passed'] and len(data['cases'])==8 and data['free_model_fraction']=='1/8'
print(json.dumps(data,indent=2))
