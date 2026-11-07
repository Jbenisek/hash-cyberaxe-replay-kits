"""Bounded interface tests on copied arithmetic counters; no transform allocation."""
import hashlib,importlib.util,json,subprocess,sys,tempfile
from datetime import datetime,timezone
from pathlib import Path
if not __debug__:raise SystemExit('Run without -O')
ROOT=Path(__file__).resolve().parent
BASE='research/levers_1029/pos_r15_xconv/tools/'
PINS={'geo.py':'cdd7ebc0e8172a55f0426afe2dab96b441ec843058912d4967fc3a391e1ead50',
      'xconv.py':'010ef7da265de2774d9519d5c43bba2e2ed50915f0628cb402ff1302634786ad',
      'xconv1.py':'88535ee7467250a93ce83597feb0c1feeae3f81291043f234b879662fae94e01'}
originals={name:(ROOT/name).read_bytes() for name in PINS}
for name,raw in originals.items():assert hashlib.sha256(raw).hexdigest()==PINS[name]
with tempfile.TemporaryDirectory(prefix='library-xconv-interface-') as tmp:
    work=Path(tmp)
    for name,raw in originals.items():(work/name).write_bytes(raw)
    sys.path.insert(0,str(work))
    import geo,xconv,xconv1
    try:
        # Independent per-index summation of the model's boundary-stage charges.
        checked=0
        for L in (16,32,64,128):
            q=L//4
            for K in range(1,L//2+1):
                for cnt in (1,3,8):
                    first=3*q+2;last=3*q+2
                    for i in range(q):
                        active=int(i<K)+int(i+q<K)
                        base=geo.oc(4)+geo.F(cnt)
                        first+=base+([3+8*cnt,9+xconv.ROW+15*cnt,9+2*xconv.ROW+24*cnt][active])
                        need=[K<=i+j*q<2*K for j in range(4)]
                        p1=need[0] or need[2];p2=need[1] or need[3]
                        if not (p1 or p2):continue
                        h=lambda x,y:3 if x and y else 2 if x or y else 0
                        operations=8+2*h(p1,p2)+h(need[0],need[2])+h(need[1],need[3])+4*sum(need)
                        last+=base+9+sum(need)*xconv.ROW+operations*cnt
                    assert xconv1.first1(L,K,cnt)==first
                    assert xconv1.last1(L,K,cnt)==last
                    checked+=1
        cases=[{'case':'boundary-stages-match-per-index-count-model','parameter_triples':checked,'passed':True}]
        assert geo.runsplit(3,-1,8)==(0,[])
        cases.append({'case':'negative-layer-count-vacuously-returns-empty-split','passed':True})
        for module,L in ((xconv1,64),(xconv,48)):
            assert module.phase(L,12,8,32)==module.phase(L,12,8,39)
            try:module.phase(L,12,0,32)
            except ZeroDivisionError:pass
            else:raise AssertionError('zero batch size unexpectedly accepted')
        cases.append({'case':'both-phase-counters-drop-partial-group-and-reject-zero-divisor','passed':True})
        assert xconv.group(48,12,8)==xconv.group(49,12,8)
        cases.append({'case':'mixed-radix-group-accepts-nonmultiple-length-through-floor-division','passed':True})
        try:xconv1.group(64,33,8)
        except AssertionError:pass
        else:raise AssertionError('invalid output-window guard unexpectedly passed')
        cases.append({'case':'power-of-two-model-rejects-output-window-overrun','passed':True})
        outputs={}
        for name in ('geo.py','xconv1.py','xconv.py'):
            run=subprocess.run([sys.executable,'-B',str(work/name)],cwd=work,capture_output=True,text=True,check=True,timeout=10)
            outputs[name]={'stdout':run.stdout.strip(),'exit_code':run.returncode}
        assert outputs['geo.py']['stdout']==''
        assert outputs['xconv1.py']['stdout'].startswith('model ')
        assert outputs['xconv.py']['stdout'].startswith('model GEO(Lx)')
        cases.append({'case':'three-original-main-entrypoints-run-without-transform-or-file-output','passed':True})
        # Imports may create __pycache__ in this temporary tree; sources never change.
        for name,raw in originals.items():assert (work/name).read_bytes()==raw
    finally:sys.path.pop(0)
report={'passed':True,'finished_at':datetime.now(timezone.utc).isoformat(),
        'cases':cases,'results':{'boundary_parameter_triples':checked,'cli':outputs},
        'input_files':[{'path':BASE+name,'sha256':sha} for name,sha in PINS.items()],
        'scope':'Finite interfaces and per-index accounting under inherited charges; not a transform implementation, attack success law or complete price proof.'}
print(json.dumps(report,indent=2))
