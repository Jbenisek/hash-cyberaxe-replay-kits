"""Replay saved prefix examples; no search, network or production writes."""
import hashlib, importlib.util, json, struct
from pathlib import Path
if not __debug__:
    raise SystemExit('Run without -O: assertions are required by this teaching verifier.')
HERE=Path(__file__).resolve().parent
manifest=json.loads((HERE/'MANIFEST.json').read_text(encoding='utf-8'))
for r in manifest['files']:
    p=(HERE/r['path']).resolve()
    assert p.is_relative_to(HERE) and p.is_file()
    raw=p.read_bytes()
    assert len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256'],r['path']
spec=importlib.util.spec_from_file_location('reference',HERE/'sha256_reference.py')
H=importlib.util.module_from_spec(spec);spec.loader.exec_module(H)
data=json.loads((HERE/'pairs.json').read_text(encoding='utf-8'))

def trace(w):
    s=tuple(H.IV0);W=H.expand(w,64);states=[]
    values={'A':{-i-1:H.IV0[i] for i in range(4)},
            'E':{-i-1:H.IV0[i+4] for i in range(4)},'W':dict(enumerate(W))}
    for t in range(64):
        s=H.step(s,t,W[t]);states.append(list(s));values['A'][t]=s[0];values['E'][t]=s[4]
    return values,states

def permits(c,a,b):
    if c=='?':return True
    if c=='-':return a==b
    if c=='x':return a!=b
    if c=='u':return (a,b)==(1,0)
    if c=='n':return (a,b)==(0,1)
    if c=='0':return (a,b)==(0,0)
    if c=='1':return (a,b)==(1,1)
    raise ValueError('Unsupported symbol: '+c)

def rows_for(traces,rows):
    checks=[]
    for row in rows:
        t=row['row'];bad={};counts={}
        for field in ('A','E','W'):
            if field not in row:continue
            pat=row[field];assert len(pat)==32
            bad[field]=[];counts[field]=sum(c!='?' for c in pat)
            for pos,c in enumerate(pat):
                bit=31-pos;a,b=[(tr[field][t]>>bit)&1 for tr in traces]
                if not permits(c,a,b):bad[field].append(bit)
        checks.append({'row':t,'violation_bits':bad,'constrained_bits':counts})
    return checks

for msg in (b'',b'abc',bytes(range(55))):
    block=msg+b'\x80'+b'\0'*(55-len(msg))+struct.pack('>Q',8*len(msg))
    assert struct.pack('>8I',*H.compress(H.IV0,struct.unpack('>16I',block)))==hashlib.sha256(msg).digest()
for c,expected in {'?':4,'-':2,'x':2,'u':1,'n':1,'0':1,'1':1}.items():
    assert sum(permits(c,a,b) for a in (0,1) for b in (0,1))==expected
assert permits('u',1,0) and not permits('u',0,1)
try:permits('z',0,0)
except ValueError:pass
else:raise AssertionError('Unknown symbol accepted')
ids=set();mask_count=0;full_equal=0;first_failures=[]
for row in data['records']:
    cv=[int(x,16) for x in row['chaining_value']];assert cv==H.IV0
    words=[[int(x,16) for x in ws] for ws in row['messages']]
    assert len(words)==2 and words[0]!=words[1]
    assert all(len(w)==16 and all(0<=v<2**32 for v in w) for w in words)
    ident=hashlib.sha256(struct.pack('>40I',*(cv+words[0]+words[1]))).hexdigest()
    assert ident==row['identity_sha256'];ids.add(ident)
    traces=[];states=[]
    for w in words:
        t,s=trace(w);traces.append(t);states.append(s)
    equal=[i+1 for i in range(64) if states[0][i]==states[1][i]]
    assert equal==row['equal_working_state_step_counts'];full_equal+=64 in equal
    if 'row_checks' in row:
        definition=data['characteristics'][row['mask_source']]['rows']
        checks=rows_for(traces,definition);assert checks==row['row_checks']
        failed=[r['row'] for r in checks if any(r['violation_bits'].values())]
        first=min(failed) if failed else None
        assert first==row['first_mask_violation_row'];first_failures.append(first);mask_count+=1
        # Mutate a word constrained equal at the start. It must not preserve
        # the previously verified prefix under this complete A/E/W checker.
        changed=words[0].copy();changed[0]^=1
        changed_trace,_=trace(changed)
        assert rows_for([changed_trace,traces[1]],definition)!=checks
assert len(data['records'])==51 and len(ids)==39 and mask_count==6 and full_equal==0
assert sorted(first_failures)==[15,18,18,19,20,21]
print(json.dumps({'passed':True,'source_records':51,'distinct_message_pairs':39,
    'full_mask_prefix_checks':6,'first_mask_violation_rows':first_failures,
    'full_64_step_equal_states':full_equal,'hashlib_controls':3,
    'mutation_and_unknown_symbol_controls':True,
    'scope':'Raw-block standard-IV prefix examples, not collisions or valid-padding certificates. Only six pairs have matching row masks here; malformed whole XML was not silently repaired.'},indent=2))
