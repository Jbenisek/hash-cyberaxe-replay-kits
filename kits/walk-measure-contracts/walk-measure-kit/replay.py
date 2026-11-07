"""Offline measurement-contract replay. Does not import the research rho module."""
import hashlib,json,subprocess,sys
from pathlib import Path
if not __debug__:raise SystemExit('Run without -O')
ROOT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/'MANIFEST.json').read_text(encoding='utf-8'))
names=[row['path'] for row in manifest['files']]
assert len(names)==len(set(names))
assert set(names)=={'measure.py','check_contract.py','replay.py','README.md'}
for row in manifest['files']:
    raw=(ROOT/row['path']).read_bytes()
    assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
result=subprocess.run([sys.executable,'-I','-B',str(ROOT/'check_contract.py')],
    cwd=ROOT,capture_output=True,text=True,timeout=30)
assert result.returncode==0,result.stderr
report=json.loads(result.stdout)
assert report['passed'] and len(report['cases'])==16 and not report['actual_rho_imported']
print(json.dumps(report,indent=2))
