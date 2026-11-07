"""Replay numerical closure measurements and safe table arithmetic only."""
import hashlib,importlib.util,json,struct
from pathlib import Path
if not __debug__:raise SystemExit('Run without -O')
HERE=Path(__file__).resolve().parent
for r in json.loads((HERE/'MANIFEST.json').read_text())['files']:
    p=(HERE/r['path']).resolve();assert p.is_relative_to(HERE)
    raw=p.read_bytes();assert len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256']
spec=importlib.util.spec_from_file_location('reference',HERE/'sha256_reference.py')
H=importlib.util.module_from_spec(spec);spec.loader.exec_module(H)
data=json.loads((HERE/'game-research.json').read_text())
for msg in (b'',b'abc',bytes(range(55))):
    block=msg+b'\x80'+b'\0'*(55-len(msg))+struct.pack('>Q',8*len(msg))
    assert struct.pack('>8I',*H.compress(H.IV0,struct.unpack('>16I',block)))==hashlib.sha256(msg).digest()
def trace(cv,w,n):
    s=tuple(cv);a=[];e=[]
    for t,word in enumerate(H.expand(w,n)[:n]):
        s=H.step(s,t,word);a.append(s[0]);e.append(s[4])
    return a,e,s
def tz(v):return 32 if not v else (v&-v).bit_length()-1
seen=set();std=0;equal=0
for r in data['closure_pairs']:
    n=r['steps'];assert type(n)==int and 4<=n<=64
    cv=[int(x,16) for x in r['chaining_value']];ws=[[int(x,16) for x in w] for w in r['messages']]
    assert len(cv)==8 and len(ws)==2 and len(ws[0])==len(ws[1])==16 and ws[0]!=ws[1]
    ident=hashlib.sha256(struct.pack('>41I',*([n]+cv+ws[0]+ws[1]))).hexdigest()
    assert ident==r['identity_sha256'];seen.add(ident)
    a,e,s=trace(cv,ws[0],n);b,f,s2=trace(cv,ws[1],n)
    bits=[(a[t]^b[t]).bit_count()+(e[t]^f[t]).bit_count() for t in range(n-4,n)]
    assert bits==r['closure_row_mismatches'] and bits[0]==r['first_row_mismatches']
    assert sum(bits)==r['working_state_mismatches']==sum((x^y).bit_count() for x,y in zip(s,s2))
    assert 128-sum(bits)==r['half_reference_minus_mismatches']
    assert tz((a[n-4]-b[n-4])&H.M)==r['trailing_zero_modular_A']
    assert tz((e[n-4]-f[n-4])&H.M)==r['trailing_zero_modular_E']
    outputs=[[f'{(x+y)&H.M:08x}' for x,y in zip(st,cv)] for st in (s,s2)]
    assert outputs==r['feedforward_outputs']
    assert (s==s2)==r['working_states_equal'];equal+=s==s2
    assert (cv==H.IV0)==r['standard_iv'];std+=cv==H.IV0
    changed=ws[0].copy();changed[0]^=1
    assert [f'{x:08x}' for x in H.compress(cv,changed,n)]!=outputs[0]
groups=data['difference_groups'];horizons=data['reported_horizons']
assert len(groups)==293 and sum(r['saved_record_count'] for r in groups)==1417
assert sum(r['reported_local_schedule_score'] is None for r in groups)==69
assert len({(r['steps'],r['reported_difference_group']) for r in groups})==293
assert len(horizons)==70 and sum(r['reported_two_bit_horizon'] is None for r in horizons)==46
assert len(data['closure_pairs'])==70 and len(seen)==57 and std==33 and equal==0
print(json.dumps({'passed':True,'meter_records':70,'distinct_meter_pair_identities':57,
    'standard_iv_records':33,'collisions':0,'difference_group_rows':293,
    'saved_group_record_count':1417,'reported_horizon_records':70,'unknown_horizons':46,
    'known_answer_and_mutation_controls':True,
    'scope':'Exact replay of numerical compression traces and table arithmetic. No schedule-group equivalence, independent-trial law, horizon feasibility, padding eligibility or complete price certified.'},indent=2))
