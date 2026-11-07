"""Portable synthetic control-flow checks; no original launcher invocation."""
import hashlib,json,subprocess,sys
from pathlib import Path
if not __debug__:raise SystemExit('Run without -O')
ROOT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/'MANIFEST.json').read_text(encoding='utf-8'))
names=[r['path'] for r in manifest['files']]
assert len(names)==len(set(names))
assert set(names)=={'scan_driver.py','check_contract.py','replay.py','README.md'}
for row in manifest['files']:
    raw=(ROOT/row['path']).read_bytes()
    assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
result=subprocess.run([sys.executable,'-I','-B',str(ROOT/'check_contract.py')],
    cwd=ROOT,capture_output=True,text=True,timeout=30)
assert result.returncode==0,result.stderr
data=json.loads(result.stdout)
assert data['passed'] and len(data['cases'])==12 and not data['actual_encoder_or_solver_executed']
print(json.dumps(data,indent=2))
