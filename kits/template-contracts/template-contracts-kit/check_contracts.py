"""Run historical text-template utilities on disposable, synthetic files only.

No real package is built or altered. Child tempfile roots are confined to the
test directory because the original leave-one-out tool does not clean its roots.
"""
import hashlib,json,os,subprocess,sys,tempfile
from datetime import datetime,timezone
from pathlib import Path
if not __debug__:raise SystemExit('Run without -O')
ROOT=Path(__file__).resolve().parent
BASE='research/launch/port/'
pins={'extract.py':'defe4d79fffa4ea40b37abab8f781b137f9ac2044d0d1faf0795ed24dd9cc5cb',
      'filltmpl.py':'4622198f9a101ee7d2ab09f87cf61bb70a9bb4ba9b0df828e3c155314781ad79',
      'mktmpl.py':'ca6dfd7f02ff33d4089376f0a50cec6e02002fc2402715c21423e7f6b34812f8',
      'newrow.py':'003eab8c9a3a92639e8b8d372e05b5ba9b900acdc12840093c20782363f795fe',
      'loo_test.py':'28d5c805933dccba30da90e28bef48613f6296ccd1fdc7807d81b1f5503db88a'}
originals={name:(ROOT/name).read_bytes() for name in pins}
for name,raw in originals.items():assert hashlib.sha256(raw).hexdigest()==pins[name]
cases=[]
with tempfile.TemporaryDirectory(prefix='library-template-contracts-') as tmp:
    work=Path(tmp);bin=work/'tools';bin.mkdir();scratch=work/'temp';scratch.mkdir()
    for name,raw in originals.items():(bin/name).write_bytes(raw)
    env={**os.environ,'TMP':str(scratch),'TEMP':str(scratch),'TMPDIR':str(scratch)}
    def run(name,*args,ok=True):
        p=subprocess.run([sys.executable,'-I','-B',str(bin/name),*map(str,args)],cwd=work,
                         env=env,capture_output=True,text=True,timeout=10)
        assert (p.returncode==0)==ok,(name,p.returncode,p.stderr)
        return p
    def check(name):cases.append({'case':name,'passed':True})
    rows=[]
    for n,text in ((39,'Title\nvalue 12\nalpha\nend\n'),(40,'Title\nvalue 27\nbeta\ninserted\nend\n')):
        d=work/('r'+str(n));d.mkdir();(d/'note.txt').write_text(text,encoding='utf-8',newline='\n');rows.append(d)
    out=work/'templates';run('mktmpl.py',out,'note.txt',*rows)
    for n,d in zip((39,40),rows):
        filled=work/('filled'+str(n));run('filltmpl.py',out/'note.txt.tmpl',out/'note.txt.vals.json','r'+str(n),filled)
        assert filled.read_bytes()==(d/'note.txt').read_bytes()
    check('numeric-line-and-block-slots-reconstruct-two-synthetic-rows')
    extracted=work/'extracted.json'
    run('extract.py',out/'note.txt.tmpl',rows[1]/'note.txt','held',extracted)
    filled=work/'held.txt';run('filltmpl.py',out/'note.txt.tmpl',extracted,'held',filled)
    assert filled.read_bytes()==(rows[1]/'note.txt').read_bytes()
    check('extract-and-fill-roundtrip-on-fitting-row')
    simple=work/'simple.tmpl';simple.write_text('value={{s0}}',encoding='utf-8')
    negative=work/'negative.txt';negative.write_text('value=-3',encoding='utf-8')
    prior=extracted.read_bytes();p=run('extract.py',simple,negative,'row',extracted,ok=False)
    assert 'DOES NOT FIT' in p.stdout and extracted.read_bytes()==prior
    check('negative-number-slot-rejected-and-old-extraction-file-retained')
    repeated=work/'repeated.tmpl';repeated.write_text('{{s0}} {{s0}}',encoding='utf-8')
    values=work/'values.json';values.write_text(json.dumps({'r':{'s0':'7'}}),encoding='utf-8')
    run('filltmpl.py',repeated,values,'r',filled);assert filled.read_text()=='7 7'
    p=run('extract.py',repeated,filled,'r',extracted,ok=False)
    assert 'redefinition of group name' in p.stderr
    check('fill-accepts-repeated-slot-but-extractor-regex-rejects-it')
    block=work/'block.tmpl';block.write_text('{{B0}}',encoding='utf-8')
    values.write_text(json.dumps({'r':{'B0':'ab'}}),encoding='utf-8')
    run('filltmpl.py',block,values,'r',filled);assert filled.read_text()=='a\nb'
    check('block-string-is-expanded-as-character-lines-without-schema-validation')
    # Newrow works only against this two-file dummy; never a real submission.
    base=work/'dummy-base';base.mkdir();(base/'note.txt').write_text('old',encoding='utf-8')
    values.write_text(json.dumps(json.loads((out/'note.txt.vals.json').read_text())['r40']),encoding='utf-8')
    dummy=work/'dummy-output';run('newrow.py',out,values,'fresh',base,dummy)
    assert (dummy/'note.txt').read_bytes()==(rows[1]/'note.txt').read_bytes()
    p=run('newrow.py',out,values,'fresh',base,dummy,ok=False);assert 'exists:' in p.stderr
    check('newrow-refills-dummy-only-and-refuses-existing-destination')
    broken=work/'broken-output'
    run('newrow.py',out,values,'fresh',base,broken,'missing/note.txt=note.txt',ok=False)
    assert (broken/'note.txt').read_text()=='old' and (broken/'.vals_tmp.json').exists()
    check('newrow-failure-leaves-partial-copy-and-temporary-values-file')
    crlf=[]
    for n in (41,42):
        d=work/('r'+str(n));d.mkdir();(d/'note.txt').write_bytes(('value '+str(n)+'\r\n').encode());crlf.append(d)
    p=run('loo_test.py','note.txt',*crlf)
    assert 'reconstruction of 2 rows: EXACT' in p.stdout
    newlineout=work/'newline-templates';run('mktmpl.py',newlineout,'note.txt',*crlf)
    run('filltmpl.py',newlineout/'note.txt.tmpl',newlineout/'note.txt.vals.json','r41',filled)
    assert filled.read_bytes()!=(crlf[0]/'note.txt').read_bytes()
    assert filled.read_text()==(crlf[0]/'note.txt').read_text()
    check('loo-EXACT-means-universal-newline-text-equality-not-byte-identity')
    collision=[]
    for label,n in (('left',1),('right',2)):
        d=work/label/'r39';d.mkdir(parents=True);(d/'note.txt').write_text('value '+str(n),encoding='utf-8');collision.append(d)
    collided=work/'collision-templates';run('mktmpl.py',collided,'note.txt',*collision)
    assert set(json.loads((collided/'note.txt.vals.json').read_text()))=={'r39'}
    p=run('loo_test.py','note.txt',*collision)
    assert 'RECONSTRUCT FAIL r39' in p.stdout and 'reconstruction of 2 rows: FAILED' in p.stdout
    check('duplicate-derived-row-keys-overwrite-values-and-FAILED-still-exits-zero')
    # The checker compares fixed-line sets, not actual held-out extraction.
    # Extra held-out text may pass that summary despite not fitting the template.
    more=work/'r43';more.mkdir();(more/'note.txt').write_text('unique text\nvalue 43\n',encoding='utf-8')
    p=run('loo_test.py','note.txt',*crlf,more)
    assert 'r43 held out: FITS' in p.stdout and 'leave-one-out: ALL FIT' in p.stdout,p.stdout
    p=run('extract.py',newlineout/'note.txt.tmpl',more/'note.txt','held',extracted,ok=False)
    assert 'DOES NOT FIT' in p.stdout
    check('loo-reports-ALL-FIT-but-heldout-row-fails-actual-extraction')
report={'passed':True,'finished_at':datetime.now(timezone.utc).isoformat(),'cases':cases,
        'input_files':[{'path':BASE+name,'sha256':sha} for name,sha in pins.items()],
        'scope':'Ten disposable text-template interface controls. No actual research/submission package, verifier, server or solver was run. Text reconstruction is not scientific validity or a price proof.'}
print(json.dumps(report,indent=2))
