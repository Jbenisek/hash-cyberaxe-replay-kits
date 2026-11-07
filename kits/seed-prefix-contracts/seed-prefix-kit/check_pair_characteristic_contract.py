"""Bounded copied-script checks: characteristic construction and MINE closure meter.

Only disposable directories are written. No solver, game server, or live
research output is started or modified. Sources were read in full first.
"""
import csv,hashlib,importlib.util,json,os,re,struct,subprocess,sys,tempfile
from pathlib import Path
from datetime import datetime,timezone
if not __debug__: raise SystemExit('Run without -O')
ROOT=Path(__file__).resolve().parent
PINS={
 'pair2char.py':'88133bed956eaefad6f519b1e8afd9adb1faabff48ad84a0e93db64c1c0a3855',
 'mine_meter.py':'2c144dd2c3ee1e96720bb678f24ca52f62321fa5179ee1f1978fcbfcf385f036',
 'indep_sha256_check.py':'b241e3c742b9f345fc7a049897a6dfd6342573a2d899fa05876134eb40b5fc61'}
for rel,sha in PINS.items():assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==sha,rel
spec=importlib.util.spec_from_file_location('independent_ref',ROOT/'indep_sha256_check.py')
ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)
def trace(words,cv,n):
    w=ref.expand(words,n); state=tuple(cv); out={-1:(cv[0],cv[4]),-2:(cv[1],cv[5]),-3:(cv[2],cv[6]),-4:(cv[3],cv[7])}
    for i in range(n): state=ref.step(state,i,w[i]);out[i]=(state[0],state[4])
    return out,w
def sg(a,b):return ''.join('-' if ((a^b)>>i)&1==0 else 'u' if (a>>i)&1 else 'n' for i in range(31,-1,-1))
hx=lambda w:[f'{v:08x}' for v in w]
m1=[((i+1)*0x01234567)&0xffffffff for i in range(16)];m2=m1.copy();m2[0]^=1
cv=ref.IV0; s1,w1=trace(m1,cv,10);s2,w2=trace(m2,cv,10)
checks=[]
with tempfile.TemporaryDirectory(prefix='library-pair-contract-') as scratch:
    tmp=Path(scratch); research=tmp/'research'; scripts=research/'tools/funnel';scripts.mkdir(parents=True)
    for name in ('pair2char.py','mine_meter.py'):(scripts/name).write_bytes((ROOT/name).read_bytes())
    pair=tmp/'pair.txt';pair.write_text('W='+' '.join(hx(m1))+'\nW='+' '.join(hx(m2))+'\nchain='+' '.join(hx(cv))+'\n',encoding='utf-8')
    setup=tmp/'setup.xml';setup.write_text('<config><char value="old"/><search><setting value="retained"/></search></config>',encoding='utf-8')
    def build(fix,nozero=None,input_file=pair,steps=10):
        out=tmp/'out.xml';env=os.environ.copy();env.pop('NOZERO',None)
        if nozero is not None:env['NOZERO']=nozero
        p=subprocess.run([sys.executable,'-I','-B',str(scripts/'pair2char.py'),str(input_file),str(steps),str(fix),str(out),str(setup)],env=env,cwd=tmp,capture_output=True,text=True,timeout=10)
        return p,out.read_text(encoding='utf-8') if out.exists() else ''
    p,text=build(4);assert p.returncode==0,p.stderr
    parsed={int(i):(a,e,w) for i,a,e,w in re.findall(r'(-?\d+) A: ([un?\-]+) E: ([un?\-]+)(?: W: ([un?\-]+))?',text)}
    assert set(parsed)==set(range(-4,10))
    for i,(a,e,w) in parsed.items():
        expected=[sg(s1[i][j],s2[i][j]) for j in (0,1)] if i<=4 else ['-'*32]*2 if i>=6 else ['?'*32]*2
        assert [a,e]==expected
        assert w==(sg(w1[i],w2[i]) if i>=0 else '')
    assert '<search><setting value="retained"/></search>' in text
    checks.append({'case':'normal-prefix-free-gap-and-forced-closure','rows':14,'schedule_rows':10,'passed':True})
    for n in (17,39,64):
        p,text=build(n-5,steps=n);assert p.returncode==0,p.stderr
        a,wa=trace(m1,cv,n);b,wb=trace(m2,cv,n)
        parsed={int(i):(aa,ee,ww) for i,aa,ee,ww in re.findall(r'(-?\d+) A: ([un?\-]+) E: ([un?\-]+)(?: W: ([un?\-]+))?',text)}
        assert len(parsed)==n+4
        for i,(aa,ee,ww) in parsed.items():
            assert [aa,ee]==([sg(a[i][j],b[i][j]) for j in (0,1)] if i<=n-5 else ['-'*32]*2)
            assert ww==(sg(wa[i],wb[i]) if i>=0 else '')
    checks[0]['additional_expanded_schedule_and_prefix_steps']=[17,39,64]
    p,text=build(8);assert p.returncode==0
    for i in (6,7,8):
        assert f'{i:2d} A: {sg(s1[i][0],s2[i][0])} E: {sg(s1[i][1],s2[i][1])}' in text
    checks.append({'case':'fixed-prefix-overrides-overlapping-zero-tail','passed':True})
    p,text=build(4,'0');assert p.returncode==0
    assert all(f'{i:2d} A: '+ '?'*32+' E: '+'?'*32 in text for i in range(6,10))
    assert 'zero 6..9' in p.stdout
    checks.append({'case':'NOZERO-string-zero-disables-tail-despite-printed-zero-label','passed':True})
    upper=tmp/'uppercase.txt';upper.write_text(pair.read_text().upper(),encoding='utf-8')
    p,_=build(4,input_file=upper);assert p.returncode!=0
    checks.append({'case':'uppercase-pair-format-not-supported','passed':True})
    # Run the complete writer only after mirroring its workspace-relative paths
    # inside this temporary directory. It cannot reach the real research root.
    data=research/'game/engine/data/raw';data.mkdir(parents=True)
    owner=research/'runs_1031/wcost';owner.mkdir(parents=True)
    (owner/'owner_shots_1031.jsonl').write_text('',encoding='utf-8')
    output=research/'runs_1101/funnel';output.mkdir(parents=True)
    def record(sid,second_cv=cv):return {'shot_id':sid,'R':10,'pair':{'M1':hx(m1),'M2':hx(m2),'chain1':hx(cv),'chain2':hx(second_cv)}}
    changed=list(cv);changed[0]^=1
    records=[record('ordinary'),record('blocked',changed),record('blocked'),record(None),record(None)]
    (data/'web_fixture.jsonl').write_text('\n'.join(json.dumps(r) for r in records)+'\n',encoding='utf-8')
    rejected=subprocess.run([sys.executable,'-I','-B',str(scripts/'mine_meter.py')],cwd=tmp,capture_output=True,text=True,timeout=10)
    assert rejected.returncode!=0 and 'TypeError' in rejected.stderr and 'NoneType' in rejected.stderr
    checks.append({'case':'tied-score-mixed-missing-and-string-shot-ids-crash-sort','passed':True})
    # Distinguish an earlier tuple coordinate to examine ID retention separately
    # from the demonstrated sort failure; this is a second explicit fixture.
    for row in records:row['level']=1 if row['shot_id'] is None else 0
    (data/'web_fixture.jsonl').write_text('\n'.join(json.dumps(r) for r in records)+'\n',encoding='utf-8')
    def meter():
        p=subprocess.run([sys.executable,'-I','-B',str(scripts/'mine_meter.py')],cwd=tmp,capture_output=True,text=True,timeout=10)
        assert p.returncode==0,p.stderr
        with (output/'MINE_METER.tsv').open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
    measured=meter();assert {r['shot_id'] for r in measured}=={'ordinary','None'}
    bits=[sum((s1[i][j]^s2[i][j]).bit_count() for j in (0,1)) for i in range(6,10)]
    tz=lambda x:32 if x==0 else (x&-x).bit_length()-1
    for row in measured:
        assert int(row['first_row_bits'])==bits[0] and int(row['closure_bits_total'])==sum(bits)
        assert int(row['bits_over_chance'])==128-sum(bits)
        assert int(row['tz_dA_first'])==tz((s1[6][0]-s2[6][0])&0xffffffff)
        assert int(row['tz_dE_first'])==tz((s1[6][1]-s2[6][1])&0xffffffff)
    checks.append({'case':'meter-values-independent-trace-match','rows':len(measured),'passed':True})
    checks.append({'case':'rejected-chain-record-reserves-shot-id-and-missing-ids-collapse','passed':True})
    assert meter()==measured
    assert len((output/'MINE_METER_HISTORY.tsv').read_text().splitlines())==4
    checks.append({'case':'rerun-overwrites-current-table-and-appends-history-again','passed':True})
    # Exact full-round reference sanity controls, separate from the meter score.
    for msg in (b'',b'abc',b'test',b'x'*55):
        pad=msg+b'\x80'+b'\0'*(55-len(msg))+struct.pack('>Q',8*len(msg))
        assert struct.pack('>8I',*ref.compress(cv,list(struct.unpack('>16I',pad))))==hashlib.sha256(msg).digest()
report={'passed':True,'source_hashes':PINS,'cases':checks,'standard_hashlib_controls':4,
        'finished_at':datetime.now(timezone.utc).isoformat(),
        'scope':'Finite copied-script interface and arithmetic checks, not trail satisfiability, collision discovery or success-rate certification.',
        'live_research_outputs_modified':False}
print(json.dumps(report,indent=2))
