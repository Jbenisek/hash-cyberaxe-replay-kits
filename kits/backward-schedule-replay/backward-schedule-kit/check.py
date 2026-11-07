"""Read-only finite checks of the backward-schedule research and kick-7 witness."""
import hashlib,importlib.util,json,random,struct
from pathlib import Path
if not __debug__:raise SystemExit('Run without -O')
PUB=ROOT=Path(__file__).resolve().parent
FOLDER=ROOT
# Raw operational briefing omitted; original fingerprint retained as provenance only.
ref=ROOT/'reference.py'
assert hashlib.sha256(ref.read_bytes()).hexdigest()=='b241e3c742b9f345fc7a049897a6dfd6342573a2d899fa05876134eb40b5fc61'
spec=importlib.util.spec_from_file_location('backward_schedule_reference',ref)
H=importlib.util.module_from_spec(spec);spec.loader.exec_module(H)
for message in (b'',b'abc',bytes(range(32)),bytes(range(55))):
    block=message+b'\x80'+b'\0'*(55-len(message))+struct.pack('>Q',len(message)*8)
    assert struct.pack('>8I',*H.compress(H.IV0,struct.unpack('>16I',block)))==hashlib.sha256(message).digest()
MASK=(1<<32)-1
def rotr(x,n):return ((x>>n)|(x<<(32-n)))&MASK
def s0(x):return rotr(x,7)^rotr(x,18)^(x>>3)
def s1(x):return rotr(x,17)^rotr(x,19)^(x>>10)
def backward(window):
    assert len(window)==16
    w=[0]*23+list(window)
    for t in range(38,15,-1):w[t-16]=(w[t]-s1(w[t-2])-w[t-7]-s0(w[t-15]))&MASK
    assert H.expand(w[:16],39)==w
    return w
def differences(a,b):return [(y-x)&MASK for x,y in zip(a,b)]
def ds(f,x,d):return (f((x+d)&MASK)-f(x))&MASK
random_checks=0
for seed in range(1024):
    rng=random.Random(seed)
    window=[rng.getrandbits(32) for _ in range(16)]
    delta=rng.randrange(1,1<<32)
    alternate=window.copy();alternate[1]=(alternate[1]+delta)&MASK
    a,b=backward(window),backward(alternate);d=differences(a,b)
    assert all(d[i]==0 for i in range(16,23))
    assert d[24]==delta and all(d[i]==0 for i in range(23,39) if i!=24)
    expected={15:(-delta)&MASK}
    for j in (14,13,12,11):expected[j]=(-ds(s0,a[j+1],d[j+1]))&MASK
    expected[10]=(-ds(s1,a[24],delta)-ds(s0,a[11],d[11]))&MASK
    expected[9]=(-ds(s0,a[10],d[10]))&MASK
    expected[8]=(delta-ds(s0,a[9],d[9]))&MASK
    expected[7]=(-ds(s0,a[8],d[8]))&MASK
    expected[6]=(delta-ds(s0,a[7],d[7]))&MASK
    expected[5]=(-d[14]-ds(s0,a[6],d[6]))&MASK
    expected[4]=(-d[13]-ds(s0,a[5],d[5]))&MASK
    expected[3]=(-d[12]-ds(s0,a[4],d[4]))&MASK
    expected[2]=(-d[11]-ds(s0,a[3],d[3]))&MASK
    expected[1]=(-ds(s1,a[15],d[15])-d[10]-ds(s0,a[2],d[2]))&MASK
    expected[0]=(-ds(s1,a[14],d[14])-d[9]-ds(s0,a[1],d[1]))&MASK
    assert all(expected[i]==d[i] for i in range(16))
    conditions=[ds(s0,a[9],d[9])==delta,
                ds(s0,a[5],d[5])==(-d[13])&MASK,
                ds(s0,a[3],d[3])==(-d[11])&MASK,
                ds(s1,a[15],d[15])==(-d[10])&MASK,
                ds(s1,a[14],d[14])==(-d[9])&MASK]
    assert all(conditions)==all(d[i]==0 for i in (0,1,2,4,7,8))
    random_checks+=1
pair_path=FOLDER/'SCHED_TAILLIGHTEST_board_tail.txt'
pair_raw=pair_path.read_bytes()
assert hashlib.sha256(pair_raw).hexdigest()=='a44679e91014f36eff1eb148c56ea52424057d46120a3836f114e6c45a5a716e'
text=pair_raw.decode('utf-8-sig')
messages=[]
for tag in ('M1','M2'):
    line=next(line for line in text.splitlines() if line.startswith(tag+' '))
    words=[int(x,16) for x in line.split()[1:]]
    assert len(words)==16;messages.append(words)
schedules=[H.expand(m,39) for m in messages]
support=[i for i,(a,b) in enumerate(zip(*schedules)) if a!=b]
assert support==[8,9,10,11,12,16,17,24,26]
weights={str(i):(schedules[0][i]^schedules[1][i]).bit_count() for i in support}
assert {i:weights[str(i)] for i in (16,17,24,26)}=={16:3,17:1,24:2,26:1}
assert sum(weights[str(i)] for i in support if i>=16)==7
outputs=[H.compress(H.IV0,m,39) for m in messages]
assert outputs[0]!=outputs[1]
screen_path=FOLDER/'VALUE_SCREEN_PRICED_TRAILS_1031.tsv'
screen_raw=screen_path.read_bytes()
assert hashlib.sha256(screen_raw).hexdigest()=='5d8f34821965db1472c9bfaa9b43cf8600cae18c8349eaca1ce83d17c6e13e2b'
rows=[line.split('\t') for line in screen_raw.decode('utf-8-sig').splitlines() if line.strip()]
assert len(rows)==16 and all(len(r)==3 and r[1]=='UNSATISFIABLE' for r in rows)
trails={}
for name,verdict,seconds in rows:
    trail,cut=name.rsplit('_k',1)
    trails.setdefault(trail,[]).append(int(cut))
assert len(trails)==8 and all(sorted(cuts)==[17,38] for cuts in trails.values())
report={'passed':True,'brief_sha256':'240693f413317f71eac17265aeadbd60096dd2eb858ed1b9a4bd51b697551dab','original_brief_checked':False,
    'random_backward_pairs':random_checks,'round_trips':2*random_checks,'hashlib_controls':4,
    'pair_source':pair_path.name,'pair_sha256':hashlib.sha256(pair_raw).hexdigest(),
    'messages':[[f'{v:08x}' for v in m] for m in messages],
    'support':support,'xor_weights':weights,'late_xor_weight':7,
    'standard_iv_collision':False,'standard_iv_outputs':[[f'{v:08x}' for v in o] for o in outputs],
    'screen_table_sha256':hashlib.sha256(screen_raw).hexdigest(),'screen_rows':16,
    'screen_distinct_trails':8,'screen_cuts':[17,38],
    'scope':'Exact saved schedule witness and finite backward identities. The saved table has sixteen reported UNSAT rows for eight trails, not sixteen distinct trails. No UNSAT certificate, strict global minimum, independent-condition rank, real attack price or complete solver implementation audited.'}
# Report returned through stdout only.
print(json.dumps(report,indent=2))
