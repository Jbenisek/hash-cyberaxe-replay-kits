"""Replay the existing API controls plus the copied-source log-checker controls."""
import hashlib,json,subprocess,sys
from pathlib import Path
if not __debug__:raise SystemExit('Run without -O')
root=Path(__file__).resolve().parent
manifest=json.loads((root/'MANIFEST.json').read_text(encoding='utf-8'))
assert {r['path'] for r in manifest['files']}=={'poseidon_ref.py','finite-witnesses.json',
 'api_replay.py','verify_collision.py','check_log_contract.py','replay.py','README.md'}
for r in manifest['files']:
    raw=(root/r['path']).read_bytes()
    assert len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256'],r['path']
def run(name):
    p=subprocess.run([sys.executable,'-I','-B',str(root/name)],cwd=root,capture_output=True,text=True,timeout=30)
    assert p.returncode==0,p.stderr
    r=json.loads(p.stdout);assert r['passed'];return r
api=run('api_replay.py');logs=run('check_log_contract.py')
assert len(logs['cases'])==12 and api['results']['distinct_witnesses']==33
api['results']['log_checker_contract']={'cases':logs['cases'],'scope':logs['scope']}
api['scope']+=' Twelve log-checker controls additionally reproduce reference-only behavior with organizer imports explicitly blocked.'
print(json.dumps(api,indent=2))
