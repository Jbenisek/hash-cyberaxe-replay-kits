"""Exact finite-grid checks of D126's r38 arithmetic, not its attack premises."""
import ast,hashlib,io,json,math,os
from datetime import datetime,timezone
from decimal import Decimal,getcontext
from fractions import Fraction as F
from pathlib import Path
from types import SimpleNamespace
if not __debug__:raise SystemExit('Run without -O')
PUB=ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'price.py'
DEPENDENCY=ROOT/'model38.py'
RUNS=ROOT/'runs'
pins={SOURCE:'1c066a7647f5ead8dc9e4eb650193b890c584010d5569c37b8088ba2368874a7',
      DEPENDENCY:'2abe5c854d04f544395884f360c6b987f04d58f1b5da7a053f902c46d2158387',
      RUNS/'costs.json':'02c4ad8666084abdbdebd10a03edd972f47e5a7e7ae7aad6c800a49f6920aa0d',
      RUNS/'pre1.json':'553e80c110fa3f1e83f86b8e34c2e6e92568ed3316a17cc5ef7456b4441a7cbd',
      RUNS/'pre2.json':'ea062fb5984a8e7b51b3ef00a48af79a37724c56d12303ed0e967805d0a3ee4f'}
raw={p:p.read_bytes() for p in pins}
assert all(hashlib.sha256(raw[p]).hexdigest()==sha for p,sha in pins.items())

# Execute only the fully read ledger's constants and pre_ops, not its module,
# CLI, ledger(), imports or expensive integer-power certificate path.
tree=ast.parse(raw[DEPENDENCY].decode('utf-8'))
constant_names={'C','SR','F7','NB','MASK_E17_BITS','CNT17'}
assignments=[n for n in tree.body if isinstance(n,ast.Assign) and len(n.targets)==1
             and isinstance(n.targets[0],ast.Name) and n.targets[0].id in constant_names]
assert {n.targets[0].id for n in assignments}==constant_names
pre=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='pre_ops']
assert len(pre)==1
dep={}
exec(compile(ast.Module(body=assignments+pre,type_ignores=[]),'pinned-ledger-constants-and-pre_ops','exec'),dep)
m=SimpleNamespace(**{k:dep[k] for k in constant_names},pre_ops=dep['pre_ops'],RUNS='fixture-runs')
tree=ast.parse(raw[SOURCE].decode('utf-8'))
names={'ceil_frac','lg','r38_rows'}
functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
assert len(functions)==len(names)
def loaded(path,name):
    assert name=='ledger38d_d126' and str(path).replace('\\','/').endswith('/ledger38d.py')
    return m
def opened(path):
    name=str(path).replace('\\','/')
    assert name in {'fixture-runs/costs.json','fixture-runs/pre1.json','fixture-runs/pre2.json'}
    return io.StringIO(raw[RUNS/name.rsplit('/',1)[1]].decode('utf-8'))
# This is the effective precision after the original r38 dependency import.
getcontext().prec=80
env={'F':F,'Decimal':Decimal,'math':math,'json':json,'os':os,
     'ROOT':'fixture-root','load':loaded,'open':opened}
exec(compile(ast.Module(body=functions,type_ignores=[]),'pinned-d126-r38-functions','exec'),env)
rows=env['r38_rows']()
assert [r[0] for r in rows]==list(range(46))
assert rows[0][1:4]==(276300922872053836590,F(4355254316452512304843545,1364),2344036320154681344765568)
assert rows[19][1:4]==(144861257685868825855453042,F(977240457355965757398995463315,2728),4470913155625365120)
score=lambda row:row[2]*max(F(1),F(row[3],1<<20))
ordered=sorted(rows,key=score)
assert ordered[0][0]==19 and score(ordered[0])<score(ordered[1])

# Verify the q3 mantissa truncation with integers, not a floating sqrt.
mantissa=math.floor(2**.5*2**40)
assert mantissa==math.isqrt(1<<81)
assert mantissa**2<=1<<81<(mantissa+1)**2
q3=F(mantissa,1<<142)  # 2^-102 * floor(sqrt(2)*2^40)/2^40

def ln_bounds(x,terms=48):
    assert 1<=x<=2
    z=(x-1)/(x+1);power=z;total=F(0)
    for j in range(terms):
        total+=2*power/(2*j+1);power*=z*z
    return total,total+2*power/((2*terms+1)*(1-z*z))
ln2=ln_bounds(F(2))
def log2_bounds(x):
    assert x>0
    exponent=x.numerator.bit_length()-x.denominator.bit_length()
    if x<F(2)**exponent:exponent-=1
    mantissa=x/(F(2)**exponent)
    low,high=ln_bounds(mantissa)
    return exponent+low/ln2[1],exponent+high/ln2[0]
def certify_up5(x,approx):
    k=math.ceil(approx*100000)
    low,high=log2_bounds(x)
    assert F(k-1,100000)<low<=high<=F(k,100000)
    return k
def exp_negative_upper(x):
    # e^x >= sum(x^j/j!, j=0..63) for x>=0, hence its reciprocal
    # is a rigorous upper bound on e^-x. No floating exponent is used.
    assert x>=0
    term=total=F(1)
    for j in range(1,64):term=term*x/j;total+=term
    return 1/total

records=[]
pf=F(m.F7,1<<32);entry=F(m.SR*22,1<<32)
E=[3*(entry+m.NB),entry*pf,entry*pf*F(1,1<<m.MASK_E17_BITS),F(m.SR)*pf*F(m.CNT17,1<<64)]
for k,NG,T,mem,time_log,mem_log,reported_overflow in rows:
    B=1<<k;maxb=14*22*768;Be=F(m.NB*maxb,B)
    caps=[3*(Be+F(m.NB,B)),Be,Be,Be]
    overflow=sum(caps[i]/(F(1,256)*NG*(E[i]/B)) for i in range(3))
    overflow+=caps[3]/(NG*(E[3]/B))
    assert float(overflow)==reported_overflow
    q=F(m.SR)*pf*q3/F(2*B)
    success_lower=1-exp_negative_upper(NG*q)-overflow
    assert success_lower>=F(39,100),k
    s=score(rows[k])
    records.append({'k':k,'groups':NG,'T_num':T.numerator,'T_den':T.denominator,
        'memory_bytes':mem,'score_argument_num':s.numerator,'score_argument_den':s.denominator,
        'time_log2_up5_units':certify_up5(T,time_log),
        'score_log2_up5_units':certify_up5(s,time_log+max(0,mem_log-20)),
        'model_success_at_least_39_percent_proved':True})
assert records[0]['time_log2_up5_units']==7143541
assert records[19]['time_log2_up5_units']==8821101
assert records[19]['score_log2_up5_units']==13016628
report={'passed':True,'finished_at':datetime.now(timezone.utc).isoformat(),
    'source_sha256':pins[SOURCE],'input_files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':pins[p]} for p in pins if p!=SOURCE],
    'rows':records,'grid_rows':46,'best_shard_k':19,'exact_rational_ranking':True,
    'rigorous_rounding_certificates':92,'r37_executed':False,'original_dependency_module_imported':False,
    'scope':'All 46 r38 rows of the pinned derived shard model, with exact rational ranking, rigorous log rounding and conditional success inequalities. Not a proof of the shard sampling law, cost inputs, memory layout, or cryptographic success premise; r37 not executed.'}
report['original_source_bytes_checked']=False
print(json.dumps(report,indent=2))
