"""Pinned estimator contracts; no original rho import or research walk campaign."""
import ast
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import itertools
import json
import math
from pathlib import Path
import random
from types import SimpleNamespace

if not __debug__:
    raise SystemExit('Run without -O')
PUB=Path(__file__).resolve().parents[1]
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'measure.py'
PIN='ea3720d4bd96a2a28c8c54cadcba9f4f5f42c1d7b3f4d3f5fb65d30ac03e3629'
raw=SOURCE.read_bytes()
assert hashlib.sha256(raw).hexdigest()==PIN
tree=ast.parse(raw.decode('utf-8'))
names={'first_repeat','loglik','mle','interval','run'}
functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
assert len(functions)==len(names) and {n.name for n in functions}==names
env={'math':math,'random':random,'hashlib':hashlib,'SHIFT':0}
exec(compile(ast.Module(body=functions,type_ignores=[]),'pinned-walk-estimator-functions','exec'),env)
cases=[]
def passed(name,**detail):
    cases.append({'name':name,'passed':True,**detail})
def rejects(fn,exception):
    try:fn()
    except exception:return
    raise AssertionError('Expected '+exception.__name__)

repeat=env['first_repeat'];ll=env['loglik']
assert repeat(lambda v:v,0)==1
assert repeat(lambda v:7,0)==2
assert repeat(lambda v:7,7)==1
passed('first-repeat-includes-return-to-initial-state')
assert repeat(lambda v:(v+1)%4,0)==4
assert len({(v+1)%4 for v in range(4)})==4
passed('permutation-cycle-repeats-without-distinct-input-collision')

# Exhaustively enumerate every map on N <= 5 from fixed start 0.
# This tests the random-function first-repeat law exactly, not a crypto map.
enumerations=[]
for N in range(1,6):
    counts=[0]*(N+1)
    for values in itertools.product(range(N),repeat=N):
        counts[repeat(values.__getitem__,0)]+=1
    survival=Fraction(1)
    for n in range(1,N+1):
        prob=survival*Fraction(n,N)
        assert Fraction(counts[n],N**N)==prob
        survival*=1-Fraction(n,N)
    assert sum(counts)==N**N and survival==0
    enumerations.append({'N':N,'maps':N**N,'counts_by_repeat_index':counts[1:]})
passed('exact-random-map-law-through-five-states',enumerations=enumerations)

def direct(c,ts,N):
    return sum(sum(math.log1p(-c*i/N) for i in range(1,n))+math.log(c*n/N) for n in ts)
for ts in ([1],[2,2,4],[9,2,9,1],[4,3,2,1]):
    assert math.isclose(ll(.8,ts,64),direct(.8,ts,64),rel_tol=1e-13,abs_tol=1e-13)
passed('sorted-accumulator-matches-direct-likelihood-including-duplicates')
assert ll(1,[1,2,3,4],4)==direct(1,[1,2,3,4],4)
passed('unit-rate-hazard-valid-through-final-state')
assert math.isclose(ll(4,[1],1),math.log(4))
passed('unvalidated-last-hazard-can-exceed-one',invalid_probability=4)
rejects(lambda:ll(4,[2],1),ValueError)
passed('invalid-survival-hazard-raises-domain-error')
assert ll(.8,[],64)==0
empty_fit=env['mle']([],64)
assert .05<=empty_fit<.050001
passed('empty-sample-produces-boundary-fit-without-evidence',fit=empty_fit)
for N in (4,1024):
    fit=env['mle']([1]*3,N)
    assert 3.99999<fit<=4
passed('short-walk-sample-saturates-hard-coded-upper-fit-bound')
rejects(lambda:env['mle']([4],4),ValueError)
passed('valid-small-state-sample-can-crash-unconstrained-fit-search')
rejects(lambda:env['interval']([4],4,1),ValueError)
passed('interval-search-also-enters-invalid-hazard-domain')
lo,hi=env['interval']([],64,empty_fit)
assert .02<=lo<.020001 and 5.99999<hi<=6
passed('empty-sample-interval-spans-arbitrary-search-bracket',lo=lo,hi=hi)

# Check run wiring with a fixed map stand-in. Capture samples rather than
# trusting fitted summaries; all original functions above were tested unchanged.
def run_wiring(shift,K=3):
    selected=[];samples=[];probes=[]
    def kappa_of(index):selected.append(index);return index
    env.update(SHIFT=shift,m=SimpleNamespace(G_SET=7,kappa_of=kappa_of,make_F=lambda k:lambda v:75))
    old_mle,old_interval=env['mle'],env['interval']
    old_repeat=env['first_repeat']
    def probed_repeat(f,start):probes.append(f(0));return old_repeat(f,start)
    def capture(ts,N):samples.append((list(ts),N));return 1.0
    env['mle']=capture;env['interval']=lambda ts,N,ch:(.5,1.5);env['first_repeat']=probed_repeat
    try:out=env['run'](8,K,17)
    finally:env['mle'],env['interval'],env['first_repeat']=old_mle,old_interval,old_repeat
    return out,selected,samples,probes
out,selected,samples,probes=run_wiring(0)
assert selected==[random.Random(17*1000003+k).randrange(7) for k in range(3)]
expected_real=[];expected_ctrl=[]
for k in range(3):
    rng=random.Random(17*1000003+k);rng.randrange(7);v0=rng.randrange(256)
    expected_real.append(1 if v0==75 else 2)
    key=b'ctrl%d-%d-%d'%(8,17,k)
    expected_ctrl.append(repeat(lambda v:int.from_bytes(hashlib.sha256(key+v.to_bytes(8,'little')).digest()[:8],'little')&255,v0))
assert samples==[(expected_real,256),(expected_ctrl,256)]
passed('run-seeds-map-set-initial-state-and-control-key-match-code')
shifted,_,shifted_samples,shifted_probes=run_wiring(2)
assert shifted_samples[1]==samples[1]
assert probes[::2]==[75]*3 and shifted_probes[::2]==[18]*3
assert probes[1::2]==shifted_probes[1::2]
assert set(shifted)=={'w','K','seedbase','real','ctrl'}
assert all(set(shifted[k])=={'c','lo','hi','sum_t'} for k in ('real','ctrl'))
passed('shift-affects-real-map-only-and-is-absent-from-output-metadata')
assert run_wiring(0)[2]==samples
passed('same-seed-is-reproducible-not-an-independent-replication')
out,_,samples,_=run_wiring(0,0)
assert samples==[([],256),([],256)] and out['K']==0
passed('zero-trials-not-rejected-by-run')

report={'passed':True,'finished_at':datetime.now(timezone.utc).isoformat(),
        'source_sha256':PIN,'cases':cases,'actual_rho_imported':False,
        'scope':'Exact extracted estimator and run wiring; exhaustive synthetic maps up to five states. No real Poseidon map, full-width rate, interval coverage or attack price certified.'}
# Report returned through stdout only.
print(json.dumps(report,indent=2))
