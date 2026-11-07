"""Replay synthetic document-template contracts, not real package builds."""
import hashlib,json,subprocess,sys
from pathlib import Path
if not __debug__:raise SystemExit('Run without -O')
ROOT=Path(__file__).resolve().parent
PINS={'extract.py':'defe4d79fffa4ea40b37abab8f781b137f9ac2044d0d1faf0795ed24dd9cc5cb',
      'filltmpl.py':'4622198f9a101ee7d2ab09f87cf61bb70a9bb4ba9b0df828e3c155314781ad79',
      'mktmpl.py':'ca6dfd7f02ff33d4089376f0a50cec6e02002fc2402715c21423e7f6b34812f8',
      'newrow.py':'003eab8c9a3a92639e8b8d372e05b5ba9b900acdc12840093c20782363f795fe',
      'loo_test.py':'28d5c805933dccba30da90e28bef48613f6296ccd1fdc7807d81b1f5503db88a'}
expected={*PINS,'check_contracts.py','replay.py','README.md'}
manifest=json.loads((ROOT/'MANIFEST.json').read_text(encoding='utf-8'))
assert len(manifest['files'])==len(expected)
assert {r['path'] for r in manifest['files']}==expected
assert {p.name for p in ROOT.iterdir() if p.is_file()}==expected|{'MANIFEST.json'}
for row in manifest['files']:
    raw=(ROOT/row['path']).read_bytes()
    assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
for name,sha in PINS.items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha
p=subprocess.run([sys.executable,'-I','-B',str(ROOT/'check_contracts.py')],cwd=ROOT,
                 capture_output=True,text=True,timeout=30)
assert p.returncode==0,p.stderr
report=json.loads(p.stdout)
assert report['passed'] and len(report['cases'])==10 and all(r['passed'] for r in report['cases'])
assert {Path(r['path']).name:r['sha256'] for r in report['input_files']}==PINS
print(json.dumps(report,indent=2))
