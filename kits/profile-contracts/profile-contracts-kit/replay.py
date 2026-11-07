"""Replay bounded archived-tool contracts without research campaigns."""
import hashlib, json, subprocess, sys
from pathlib import Path

if not __debug__:
    raise SystemExit('Run without -O: this finite replay uses assertions.')
ROOT=Path(__file__).resolve().parent
PINNED={
 'trail_families.py':'f495094752339b75ee721fca0d68a902acc2ab8abb7fa23841c6a6e20706b934',
 'backwalk.py':'458783cc11106c9fe43ff45a8562f28b5d6817ed5c344ccff60779b376303a53',
 'indep_sha256_check.py':'b241e3c742b9f345fc7a049897a6dfd6342573a2d899fa05876134eb40b5fc61',
 'mirror.py':'cdbe0d9d811a6b88b1ac0b18fbb8473e97b149ef77d343bbf57a7c37a2fb8f23',
 'backscore.py':'ec35e3a7dccdd9c4f559e1a8a35f03ea9d185b6c4c6d079f9b4d3f9543027a45',
 'predict_signs.py':'900ed7af18904d3729f4e2329c4d63afd38fc42f0f9c86f733b6bb48a955bc7e'}
expected={'README.md','replay.py',*PINNED,
          'check_sign_variant_contract.py','check_backscore_closed_form.py','check_sign_predictor_contract.py',
          'check_trail_family_contract.py','check_backward_cli_contract.py','check_closure_row_identity.py'}
manifest=json.loads((ROOT/'MANIFEST.json').read_text(encoding='utf-8'))
rows=manifest['files']
assert len(rows)==len(expected) and {r['path'] for r in rows}==expected
assert {p.name for p in ROOT.iterdir() if p.is_file()}==expected|{'MANIFEST.json'}
for row in rows:
    raw=(ROOT/row['path']).read_bytes()
    assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'],row['path']
for name,sha in PINNED.items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha,name
results={}
for name in ('sign_variant_contract','backscore_closed_form','sign_predictor_contract','trail_family_contract','backward_cli_contract','closure_row_identity'):
    proc=subprocess.run([sys.executable,'-I','-B',str(ROOT/('check_'+name+'.py'))],
                        cwd=ROOT,capture_output=True,text=True,timeout=30)
    if proc.returncode:raise RuntimeError(name+' failed: '+proc.stderr)
    data=json.loads(proc.stdout)
    assert data['passed'] and data['source_sha256'] in PINNED.values()
    results[name]=data['cases'] if name in ('trail_family_contract','closure_row_identity') else data['results']
assert results['sign_variant_contract']['generated_variants']==36
assert results['backscore_closed_form']['step_bijection_and_noncoalescence_controls']==4096
assert results['sign_predictor_contract']['valid_schedule_fixture']['predicted_mirror_word_mode']=='UNSAT'
assert len(results['trail_family_contract'])==7
assert results['backward_cli_contract']['backward_cli_cases']==18
assert results['backward_cli_contract']['inverse_row_comparisons']==1352
assert results['backward_cli_contract']['reference_cli_inverse_checks']==20000
assert results['closure_row_identity']==120
print(json.dumps({'passed':True,'results':results,
 'scope':'Bounded text transformations, a closed-form diagnostic, and explicit counterexamples. No solver campaign, full collision, success rate or complete attack price.'},indent=2))
