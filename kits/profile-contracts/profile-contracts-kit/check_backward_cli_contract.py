"""Bounded CLI and numerical checks, with copied tools and no live research writes."""
import hashlib,importlib.util,json,random,re,struct,subprocess,sys,tempfile
from datetime import datetime,timezone
from pathlib import Path
if not __debug__:raise SystemExit('Run without -O')
ROOT=Path(__file__).resolve().parent
pins={'backwalk.py':'458783cc11106c9fe43ff45a8562f28b5d6817ed5c344ccff60779b376303a53',
      'indep_sha256_check.py':'b241e3c742b9f345fc7a049897a6dfd6342573a2d899fa05876134eb40b5fc61'}
for name,sha in pins.items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha
spec=importlib.util.spec_from_file_location('backward_reference',ROOT/'indep_sha256_check.py')
ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)
rng=random.Random(1101);cases=[];row_checks=0
with tempfile.TemporaryDirectory(prefix='library-backward-cli-') as tmp:
    root=Path(tmp);profile=root/'profile';profile.mkdir()
    backward=profile/'backwalk.py';backward.write_bytes((ROOT/'backwalk.py').read_bytes())
    reference=root/'indep_sha256_check.py';reference.write_bytes((ROOT/'indep_sha256_check.py').read_bytes())
    pair=root/'pair.txt'
    def write_pair(a,b):pair.write_text('IV '+' '.join(f'{x:08x}' for x in ref.IV0)+'\nM1 '+' '.join(f'{x:08x}' for x in a)+'\nM2 '+' '.join(f'{x:08x}' for x in b)+'\n',encoding='utf-8')
    for n in (1,4,8,16,39,64):
        for active in (None,0,min(n-1,15)):
            a=[rng.getrandbits(32) for _ in range(16)];b=a.copy()
            if active is not None:b[active]^=1
            write_pair(a,b)
            p=subprocess.run([sys.executable,'-I','-B',str(backward),str(pair),str(n)],cwd=root,capture_output=True,text=True,check=True,timeout=10)
            exact=[tuple(int(v,16) if i in (1,3,4) else int(v) for i,v in enumerate(row)) for row in re.findall(r'step\s+(\d+): EXACT\s+dW=([0-9a-f]+)\s+-> row\s+(-?\d+) demands\s+dA=([0-9a-f]+)\s+dE=([0-9a-f]+)',p.stdout)]
            wa=ref.expand(a,64);wb=ref.expand(b,64)
            assert len(exact)>=1
            for _ in range(8):
                sa=sb=tuple(rng.getrandbits(32) for _ in range(8))
                for t,dw,row,da,de in exact:
                    assert all(sa[i]==sb[i] for i in (1,2,3,5,6,7))
                    sa=ref.back(sa,t,wa[t]);sb=ref.back(sb,t,wb[t])
                    assert row==t-4 and dw==(wa[t]-wb[t])&0xffffffff
                    assert da==(sa[3]-sb[3])&0xffffffff and de==(sa[7]-sb[7])&0xffffffff
                    row_checks+=1
                if 'VALUE-DEPENDENT' in p.stdout:assert any(sa[i]!=sb[i] for i in (1,2,3,5,6,7))
            cases.append({'steps':n,'active_input_word':active,'exact_rows':len(exact),'stops_at_value_dependence':'VALUE-DEPENDENT' in p.stdout})
    # Explicitly reproduce the absent lower bound: zero and negative horizons
    # succeed without evaluating any compression step.
    a=[0]*16;b=a.copy();b[0]=1;write_pair(a,b)
    vacuous=[]
    for n in (0,-1):
        p=subprocess.run([sys.executable,'-I','-B',str(backward),str(pair),str(n)],cwd=root,capture_output=True,text=True,check=True,timeout=10)
        assert 'walk stayed exact' in p.stdout and ': EXACT' not in p.stdout
        vacuous.append(n)
    # One complete main-program invocation, including its fixed-size randomized
    # gates. This does not mutate sources, create tables, or launch a solver.
    p=subprocess.run([sys.executable,'-I','-B',str(reference),str(pair),'0','-1','1','64'],cwd=root,capture_output=True,text=True,check=True,timeout=60)
    assert 'gate: 2000/2000 digests equal to hashlib' in p.stdout
    assert 'step inversion: 20000/20000 states restored' in p.stdout
    assert '0 steps: output words equal 8/8' in p.stdout and '-1 steps: output words equal 8/8' in p.stdout
    assert ref.compress(ref.IV0,a,64)!=ref.compress(ref.IV0,b,64)
    try:ref.compress(ref.IV0,a,65)
    except IndexError:pass
    else:raise AssertionError('Unexpected >64 step behavior')
    known=0
    for message in (b'',b'abc',b'reference',b'x'*55):
        pad=message+b'\x80'+b'\0'*(55-len(message))+struct.pack('>Q',len(message)*8)
        assert struct.pack('>8I',*ref.compress(ref.IV0,struct.unpack('>16I',pad)))==hashlib.sha256(message).digest();known+=1
report={'passed':True,'source_sha256':pins['backwalk.py'],
        'input_files':[{'path':'indep_sha256_check.py','sha256':pins['indep_sha256_check.py']}],
        'finished_at':datetime.now(timezone.utc).isoformat(),'cases':cases,
        'results':{'backward_cli_cases':len(cases),'inverse_row_comparisons':row_checks,
                   'vacuous_horizons':vacuous,'reference_cli_hashlib_checks':2000,'reference_cli_inverse_checks':20000,
                   'deterministic_hashlib_checks':known,'above64_raises_index_error':True},
        'scope':'Finite CLI/interface and arithmetic checks. Clean-terminal backward demands do not establish a reachable legal initial state or a collision. Randomized gate outcomes are not exhaustive proofs.'}
print(json.dumps(report,indent=2))
