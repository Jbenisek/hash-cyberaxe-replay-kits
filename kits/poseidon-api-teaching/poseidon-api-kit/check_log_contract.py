"""Exercise the archived log checker with copied code and public finite data.

An import-blocking fixture ensures no organizer executable is used. This tests
the optional-reference-unavailable mode only; it is not dual-verifier evidence.
"""
import hashlib,json,os,subprocess,sys,tempfile
from datetime import datetime,timezone
from pathlib import Path
if not __debug__:raise SystemExit('Run without -O')
ROOT=Path(__file__).resolve().parent
source=ROOT/'verify_collision.py'
reference=ROOT/'poseidon_ref.py'
datafile=ROOT/'finite-witnesses.json'
pins={'verify_collision.py':'c78a48a119c772c52450cd3fed27d30f11538289695baf44534ed1b2be9e62c2',
      'poseidon_ref.py':'344246fc03ae862cd42beabcade902edea45d23df6cb62751f741c3df636f171',
      'finite-witnesses.json':'dd6dd429e8b69c6271bc438de48054c6bf912f47635d243a2a94be3e3778d7ae'}
raws={p.name:p.read_bytes() for p in (source,reference,datafile)}
for name,raw in raws.items():assert hashlib.sha256(raw).hexdigest()==pins[name],name
data=json.loads(raws['finite-witnesses.json']);params=data['parameters']['poseidon'];cases=[]
with tempfile.TemporaryDirectory(prefix='library-poseidon-logs-') as tmp:
    root=Path(tmp);work=root/'orchard/exec_r2e';work.mkdir(parents=True)
    for name in ('verify_collision.py','poseidon_ref.py'):(work/name).write_bytes(raws[name])
    blocker=root/'pareto_clone/verifier';blocker.mkdir(parents=True)
    (blocker/'__init__.py').write_text("raise ImportError('publication fixture: organizer execution blocked')\n",encoding='utf-8')
    constants=root/'parameters.json'
    constants.write_text(json.dumps({'round_constants':params['round_constants_hex'],'mds':params['mds_hex']}),encoding='utf-8')
    def run(*logs,r=None):
        env={**os.environ,'ORCHARD_CONSTANTS_JSON':str(constants)};env.pop('R',None)
        if r is not None:env['R']=str(r)
        p=subprocess.run([sys.executable,'-I','-B',str(work/'verify_collision.py'),*map(str,logs)],
                         cwd=work,env=env,capture_output=True,text=True,timeout=10)
        assert 'organizer execution blocked' in p.stdout,p.stdout+p.stderr
        return p
    def check(name):cases.append({'case':name,'passed':True})
    def values(r):
        row=next(x for x in data['witnesses'] if x['profile']==f'poseidon-orchard-r{r}-prefix-v1')
        aa,bb=bytes.fromhex(row['message_a_hex']),bytes.fromhex(row['message_b_hex'])
        return dict(nk1=int.from_bytes(aa[:32],'little'),rho1=int.from_bytes(aa[32:],'little'),
                    nk2=int.from_bytes(bb[:32],'little'),rho2=int.from_bytes(bb[32:],'little'),
                    digest=int.from_bytes(bytes.fromhex(row['expected_digest']),'little'))
    def write(name,vals):
        path=root/name;path.write_text(''.join(f'COLLISION {k} 0x{v:064x}\n' for k,v in vals.items()),encoding='utf-8');return path
    p=run();assert p.returncode==0 and 'collision verified' not in p.stdout
    check('no-input-files-exit-zero-without-a-witness')
    empty=root/'empty.log';empty.write_text('ordinary progress line\n',encoding='utf-8')
    p=run(empty);assert p.returncode==0 and 'collision verified' not in p.stdout
    check('log-without-parsed-digest-is-skipped-with-zero-exit')
    uppercase=root/'uppercase.log';uppercase.write_text('COLLISION digest 0x'+'F'*64+'\n',encoding='utf-8')
    p=run(uppercase);assert p.returncode==0 and 'collision verified' not in p.stdout
    check('uppercase-hex-digest-is-not-parsed-and-file-is-skipped')
    v=values(1);good=write('r1.log',v);p=run(good)
    assert p.returncode==0 and 'collision verified reference ok None' in p.stdout
    check('r1-default-positive-with-reference-only-no-organizer')
    p=run(write('r2.log',values(2)),r=2)
    assert p.returncode==0 and 'collision verified reference ok None' in p.stdout
    check('explicit-r2-positive-original-index-schedule')
    bad=dict(v);bad['digest']^=1;p=run(write('bad-digest.log',bad))
    assert p.returncode==1 and 'FAILED ref mismatch' in p.stdout
    check('incorrect-supplied-digest-rejected')
    equal=dict(v);equal['nk2']=equal['nk1'];equal['rho2']=equal['rho1'];p=run(write('equal.log',equal))
    assert p.returncode==1 and 'FAILED reference ok' in p.stdout
    check('identical-message-pair-rejected-despite-equal-hashes')
    duplicate=root/'duplicate.log'
    duplicate.write_text('COLLISION digest 0x'+'0'*64+'\n'+good.read_text(),encoding='utf-8')
    p=run(duplicate);assert p.returncode==0 and 'collision verified' in p.stdout
    check('last-duplicate-tag-overwrites-earlier-digest')
    invalid=dict(v);invalid['nk1']=int(params['modulus_hex'],16);p=run(write('invalid.log',invalid))
    assert p.returncode!=0 and 'non-canonical field element' in p.stderr
    check('noncanonical-field-input-rejected-by-reference')
    incomplete=dict(v);del incomplete['rho2'];p=run(write('missing.log',incomplete))
    assert p.returncode!=0 and 'KeyError' in p.stderr
    check('digest-present-but-required-field-missing-fails')
    p=run(good,r='invalid');assert p.returncode!=0 and 'ValueError' in p.stderr
    check('invalid-round-environment-rejected')
    p=run(good,r=57);assert p.returncode!=0 and 'AssertionError' in p.stderr
    check('out-of-range-partial-round-count-rejected')
report={'passed':True,'finished_at':datetime.now(timezone.utc).isoformat(),'source_sha256':pins['verify_collision.py'],
        'source_pins':pins,'cases':cases,'positive_profiles':[1,2],
        'scope':'Twelve copied-source log-parser controls with public numerical witnesses. Organizer executable deliberately unavailable. No search, full-round collision, attack probability or dual-verifier certification. r counts partial rounds plus eight full rounds.'}
# Report returned through stdout only.
print(json.dumps(report,indent=2))
