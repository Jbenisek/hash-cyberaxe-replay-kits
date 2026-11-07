"""Check the exact closed form of the archived heuristic, not an attack law."""
import ast,hashlib,itertools,json,random
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent
source=ROOT/'backscore.py';raw=source.read_bytes()
tree=ast.parse(raw.decode('utf-8'));names={'walk','naf_weight'}
defs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
assert len(defs)==2
M=2**32-1;ns={'M':M};exec(compile(ast.Module(body=defs,type_ignores=[]),str(source),'exec'),ns)
def independent_naf(x):
    x&=M;x=x-2**32 if x>=2**31 else x
    magnitude=abs(x);digits=[]
    while magnitude:
        digit=0 if magnitude%2==0 else (1 if magnitude%4==1 else -1)
        digits.append(digit);magnitude=(magnitude-digit)//2
    assert sum(d*(1<<i) for i,d in enumerate(digits))==abs(x)
    assert all(not (a and b) for a,b in zip(digits,digits[1:]))
    return sum(d!=0 for d in digits)
def closed(dw,n):
    active=[i for i in range(n) if dw[i]&M]
    if not active:return n,-1,0
    j=active[-1];return n-j,j-1,independent_naf(-dw[j])
binary=0;structured=0;random_count=0
for n in range(1,11):
    for dw in itertools.product((0,1),repeat=n):
        assert ns['walk'](dw,n)==closed(dw,n);binary+=1
rng=random.Random(20261101)
for n in (1,2,4,8,16,32,39,40,64):
    for j in range(n):
        for delta in (1,2,3,0x40000000,0x80000000,0xffffffff,rng.getrandbits(32) or 1):
            dw=[rng.getrandbits(32) for _ in range(j)]+[delta]+[0]*(n-j-1)
            assert ns['walk'](dw,n)==closed(dw,n);structured+=1
for _ in range(4096):
    n=rng.randrange(1,65);dw=[rng.getrandbits(32) if rng.randrange(4)==0 else 0 for _ in range(n)]
    assert ns['walk'](dw,n)==closed(dw,n);random_count+=1
for x in range(-4096,4097):assert ns['naf_weight'](x)==independent_naf(x)
example=ns['walk']([1]+[0]*7,8)
assert example==(8,-1,1)
def rotate(x,n):return ((x>>n)|(x<<(32-n)))&M
def sigma0(x):return rotate(x,2)^rotate(x,13)^rotate(x,22)
def sigma1(x):return rotate(x,6)^rotate(x,11)^rotate(x,25)
def majority(a,b,c):return (a&b)^(a&c)^(b&c)
def choose(e,f,g):return (e&f)^((~e)&g)
def step(s,w,k):
    a,b,c,d,e,f,g,h=s
    t1=(h+sigma1(e)+choose(e,f,g)+k+w)&M
    t2=(sigma0(a)+majority(a,b,c))&M
    return ((t1+t2)&M,a,b,c,(d+t1)&M,e,f,g)
def inverse(s,w,k):
    new_a,a,b,c,new_e,e,f,g=s
    t1=(new_a-sigma0(a)-majority(a,b,c))&M
    d=(new_e-t1)&M
    h=(t1-sigma1(e)-choose(e,f,g)-k-w)&M
    return a,b,c,d,e,f,g,h
for _ in range(4096):
    state=tuple(rng.getrandbits(32) for _ in range(8))
    w,k=rng.getrandbits(32),rng.getrandbits(32)
    assert inverse(step(state,w,k),w,k)==state
    assert step(inverse(state,w,k),w,k)==state
    left=step(state,(w+1)&M,k);right=step(state,w,k)
    assert left!=right
    for unused in range(7):
        w,k=rng.getrandbits(32),rng.getrandbits(32)
        left,right=step(left,w,k),step(right,w,k)
        assert left!=right
report={'passed':True,'finished_at':datetime.now(timezone.utc).isoformat(),
    'source_sha256':hashlib.sha256(raw).hexdigest(),
    'results':{'binary_difference_vectors':binary,'structured_full_width_vectors':structured,'random_full_width_vectors':random_count,
               'naf_controls':8193,'step_bijection_and_noncoalescence_controls':4096,
               'eight_step_example':{'dW':[1]+[0]*7,'depth':8,'returned_knot':-1,'demand':1,'score':1}},
    'closed_form':'If all dW[0:R] are zero: (depth,knot,demand)=(R,-1,0). Otherwise let j be the last nonzero dW row: (R-j,j-1,NAF_weight(-dW[j] mod 2^32)).',
    'proof':['The initial four A and E row differences are zero. Walking backward across dW=0 leaves every new difference zero.',
             'At the first nonzero dW[j], mixing inputs are still clean: dT1=0, new dA[j-4]=0 and dE[j-4]=-dW[j].',
             'If j>0, the next step j-1 uses E[j-4] as its third E mixing input, so the code stops immediately. If j=0, the loop ends. Only that one nonzero demand contributes.'],
    'scope':'Two extracted pure functions, not the source file-discovery/writing driver. The closed form is a theorem about this algorithm. It does not prove a complete backward solution, prefix compatibility, a success probability or a cost in bits. The returned knot is the stopping step, not the first row of its dependency window.'}
# Report returned through stdout; no persistent output.
print(json.dumps(report,indent=2))
