"""Read-only SHA-3 summary replay in disposable directories; no connector run."""
import hashlib,json,runpy,subprocess,sys,tempfile
from datetime import datetime,timezone
from pathlib import Path
PUB=Path(__file__).resolve().parents[1];ROOT=PUB.parents[1]
source=ROOT/'research/dig/incoming/sha3-r5-U01/work2/summ_drop.py'
raw=source.read_bytes();digest=hashlib.sha256(raw).hexdigest()
assert digest=='d08b8c36a1b694f03a3d8301a768f9fd7ed2e22eb715e37b7bffe603b703ca49'
inputs=[];cases=[]
def run(files):
    with tempfile.TemporaryDirectory(prefix='publication-sha3-summary-') as tmp:
        work=Path(tmp);(work/'summ_drop.py').write_bytes(raw)
        for name,content in files.items():(work/name).write_bytes(content)
        p=subprocess.run([sys.executable,'-I','-B','summ_drop.py'],cwd=work,capture_output=True,text=True,timeout=5)
        assert p.returncode==0,p.stderr
        return p.stdout
saved={}
for k in (1,2,5,6,8,9,11):
    p=source.with_name('drop_k'+str(k)+'.json');b=p.read_bytes();saved[p.name]=b
    inputs.append({'source_identifier':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(b).hexdigest()})
text=run(saved)
assert text.count('runs 42')==6
assert 'none runs 42 ok 23 DF (35, 53)' in text
assert 'events F,R0,R1,R2 [736, 736, 736, 0] of 736' in text
assert 'F runs 42 ok 28 DF (462, 485)' in text
assert 'events F,R0,R1,R2 [0, 896, 896, 0] of 896' in text
cases.append({'case':'seven archived seed files','files':7,'records':252,'groups':6,'unmodified_ok':23,'unmodified_sampled_points':736,'dropped_F_ok':28})
assert run({}).strip()=='[]'
cases.append({'case':'empty folder','result':'prints empty list; no missing-data failure'})
base={'att':0,'drop':'none','status':'ok','DF':10,'EM':1590,'npts':16,'ev_F_R0_R1_R2':[16,8,4,0]}
drop={**base,'drop':'F','DF':12,'EM':1588}
text=run({'drop_k1.json':json.dumps([base,drop]).encode()})
assert 'F runs 1 ok 1 DF (12, 12)' in text and 'dDF (2, 2)' in text
cases.append({'case':'paired synthetic baseline','DF_gain':2})
text=run({'drop_k1.json':json.dumps([base,{**base,'DF':11,'EM':1589},drop]).encode()})
assert 'none runs 2 ok 2' in text and 'dDF (-1, 0)' in text and 'dDF (1, 1)' in text
cases.append({'case':'duplicate baseline attempt','result':'both records counted; last record used for paired baseline'})
one=json.dumps([base]).encode()
text=run({'drop_k1.json':one,'drop_k1_backup.json':one})
assert 'none runs 2 ok 2' in text and '[32, 16, 8, 0] of 32' in text
cases.append({'case':'backup filename matches glob','result':'duplicate file contributes again; no independent-trial or dedup check'})
text=run({'drop_k1.json':json.dumps([{**base,'ev_F_R0_R1_R2':[999,8,4,0]}]).encode()})
assert '[999, 8, 4, 0] of 16' in text
cases.append({'case':'event count exceeds number of points','result':'printed without validation'})
report={'passed':True,'finished_at':datetime.now(timezone.utc).isoformat(),'source_sha256':digest,
        'archived_input_files':inputs,'results':cases,
        'scope':'Six bounded read-only summary fixtures, not a connector rerun, independent sampling claim or zero-probability theorem. Original archived numerical data were separately recounted by the SHA-3 local-objects kit.'}
(PUB/'qa/sha3-ablation-summary-runtime-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
