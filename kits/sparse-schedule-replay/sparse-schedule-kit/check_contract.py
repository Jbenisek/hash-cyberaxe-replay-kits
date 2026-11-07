"""Run only the quick sparse-schedule verifier in a disposable source copy."""
import hashlib,json,subprocess,sys,tempfile
from pathlib import Path
from datetime import datetime,timezone
if not __debug__:raise SystemExit('Run without -O')
ROOT=Path(__file__).resolve().parent
BASE=ROOT
pins={
 'verify.py':'e3aba6d0e0a4747566a52c96fd0eb57fc885e46ef138874c015711ac1bb13b35',
 'code/modular.py':'9cf365f15e8c18e47ea3f29071dab3a8e44a987de10f0b4b386933c9fb532fc6',
 'code/explore.py':'c080f33d4193f64316338e25e81ac8bb9295f8a806e0db1f08c81ea373c5fb2d',
 'data/results.json':'cd747b161427cea4c6ca4b943cdeb8a6925092ec2a776d3d803eaf49cc584530'}
raws={name:(BASE/name).read_bytes() for name in pins}
for name,raw in raws.items():assert hashlib.sha256(raw).hexdigest()==pins[name],name
saved=json.loads(raws['data/results.json'])
cases=[]
with tempfile.TemporaryDirectory(prefix='library-sparse-schedule-') as tmp:
    work=Path(tmp)
    for name,raw in raws.items():
        target=work/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    def run(optimized=False,*args):
        return subprocess.run([sys.executable,'-I','-B',*(['-O'] if optimized else []),str(work/'verify.py'),*args],
                              cwd=work,capture_output=True,text=True,timeout=15)
    p=run();assert p.returncode==0 and '99 quick replay/certificate checks' in p.stdout,p.stdout+p.stderr
    cases.append({'case':'default-99-quick-checks-26-linear-four-modular-64-basis-five-support','passed':True})
    # The quick CLI does not read the descriptive summary or saved regression statuses.
    changed=json.loads(raws['data/results.json']);changed['summary']=[];changed['regression_tests']=['synthetic-not-a-proof']
    target=work/'data/results.json';target.write_text(json.dumps(changed),encoding='utf-8')
    p=run();assert p.returncode==0 and '99 quick replay/certificate checks' in p.stdout
    cases.append({'case':'summary-and-saved-regression-statuses-not-verified','passed':True})
    changed=json.loads(raws['data/results.json']);next(iter(changed['linear_witnesses'].values()))['weight']+=1
    target.write_text(json.dumps(changed),encoding='utf-8');p=run()
    assert p.returncode!=0 and 'AssertionError' in p.stderr
    cases.append({'case':'wrong-saved-linear-weight-rejected-with-assertions','passed':True})
    p=run(True);assert p.returncode==0 and '99 quick replay/certificate checks' in p.stdout
    cases.append({'case':'optimized-python-removes-weight-guard-and-still-prints-pass','passed':True})
    changed=json.loads(raws['data/results.json']);changed['linear_witnesses']={};changed['modular_witnesses']={}
    target.write_text(json.dumps(changed),encoding='utf-8');p=run()
    assert p.returncode==0 and '69 quick replay/certificate checks' in p.stdout
    cases.append({'case':'empty-witness-maps-accepted-with-lower-check-count','passed':True})
    p=run(False,'--not-a-real-option');assert p.returncode!=0 and 'unrecognized arguments' in p.stderr
    cases.append({'case':'unknown-cli-option-rejected','passed':True})
report={'passed':True,'finished_at':datetime.now(timezone.utc).isoformat(),'source_sha256':pins['verify.py'],'source_pins':pins,
        'cases':cases,'quick_checks':99,'linear_witnesses':26,'modular_witnesses':4,
        'basis_checks':64,'late_support_groups_checked':5,
        'scope':'Quick linear/modular schedule and sigma-inverse checks only; no compression collision, global minimum proof, full support recomputation, compiler, or expensive enumeration executed.'}
# Report returned through stdout only.
print(json.dumps(report,indent=2))
