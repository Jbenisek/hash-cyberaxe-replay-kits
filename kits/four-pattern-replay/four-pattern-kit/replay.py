"""Offline replay of finite chosen-CV witnesses; no attack search or network."""
import hashlib,json,subprocess,sys
from pathlib import Path
if not __debug__:raise SystemExit('Run without -O')
root=Path(__file__).resolve().parent
manifest=json.loads((root/'MANIFEST.json').read_text(encoding='utf-8'))
expected={r['path'] for r in manifest['files']}
assert expected=={'verify_alts.py','sha256_ref.py','indep_sha256_check.py',
                  'alt_G1_verify.json','alt_G2_verify.json','alt_G12_verify.json','i_all52_verify.json',
                  'check_contract.py','README.md','replay.py'}
for row in manifest['files']:
    raw=(root/row['path']).read_bytes()
    assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'],row['path']
p=subprocess.run([sys.executable,'-I','-B',str(root/'check_contract.py')],cwd=root,
                 capture_output=True,text=True,timeout=20)
assert p.returncode==0,p.stderr
result=json.loads(p.stdout)
assert result['passed'] and len(result['cases'])==8 and len(result['pairs'])==4
assert all(p['distinct_messages'] and not p['standard_iv'] and p['steps']==37 for p in result['pairs'])
print(json.dumps(result,indent=2))
