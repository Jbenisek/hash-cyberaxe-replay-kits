"""Run only finite schedule replay controls, never the exhaustive flags."""
import hashlib,json,subprocess,sys
from pathlib import Path
if not __debug__:raise SystemExit('Run without -O')
root=Path(__file__).resolve().parent
manifest=json.loads((root/'MANIFEST.json').read_text(encoding='utf-8'))
assert {r['path'] for r in manifest['files']}=={'verify.py','code/modular.py','code/explore.py',
        'data/results.json','check_contract.py','replay.py','README.md'}
for row in manifest['files']:
    raw=(root/row['path']).read_bytes()
    assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'],row['path']
p=subprocess.run([sys.executable,'-I','-B',str(root/'check_contract.py')],cwd=root,
                 capture_output=True,text=True,timeout=30)
assert p.returncode==0,p.stderr
r=json.loads(p.stdout)
assert r['passed'] and r['quick_checks']==99 and len(r['cases'])==6
print(json.dumps(r,indent=2))
