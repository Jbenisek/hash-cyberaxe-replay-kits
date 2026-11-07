"""Manifest-bound finite interface checks; only disposable local files are written."""
import hashlib,json,subprocess,sys
from pathlib import Path
if not __debug__:raise SystemExit('Run without -O: checks require assertions.')
HERE=Path(__file__).resolve().parent
manifest=json.loads((HERE/'MANIFEST.json').read_text(encoding='utf-8'))
assert len(manifest['files'])==len({r['path'] for r in manifest['files']})
for row in manifest['files']:
    path=(HERE/row['path']).resolve()
    assert path.is_relative_to(HERE) and path.is_file()
    raw=path.read_bytes()
    assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'],row['path']
(HERE/'research/public_library/qa').mkdir(parents=True,exist_ok=True)
results={}
for name,label in (('check_minsup_encoder_contract.py','encoder'),('check_sha3_ablation_summary.py','ablation_summary')):
    proc=subprocess.run([sys.executable,'-I','-B',str(HERE/'research/public_library/scripts'/name)],
                        cwd=HERE,capture_output=True,text=True,timeout=30,check=True)
    report=json.loads(proc.stdout);assert report['passed']
    results[label]=report['results']
assert results['encoder']['gate_truth_assignments']==80
assert results['encoder']['shape_truth_assignments']==64
assert len(results['encoder']['complete_trace_fixtures'])==10
assert len(results['ablation_summary'])==6
print(json.dumps({'passed':True,'results':results,
    'scope':'Finite 32-bit encoder, decoder and read-only summary contracts. Deliberate negative controls expose limitations. No solver campaign, attack price or sampler-law certification.'},indent=2))
