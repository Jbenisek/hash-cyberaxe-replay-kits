"""Exact local chi tables, a weighted tail model and structural dependency sets.

Standard library only. No solver, message search, external imports or file writes.
These are finite mathematical objects, not a conditioned-message success law.
"""
import itertools,json,hashlib
from fractions import Fraction
from pathlib import Path

if not __debug__: raise SystemExit('Run without -O')
HERE=Path(__file__).resolve().parent
manifest=json.loads((HERE/'MANIFEST.json').read_text())
for item in manifest['files']:
    path=(HERE/item['path']).resolve();assert path.is_relative_to(HERE)
    raw=path.read_bytes()
    assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'],'Changed kit file'
ROT=((0,36,3,41,18),(1,44,10,45,2),(62,6,43,15,61),(28,55,25,21,56),(27,20,39,8,14))
M64=(1<<64)-1
def chi5(v):
    b=[(v>>i)&1 for i in range(5)]
    return sum((b[i]^((1-b[(i+1)%5])*b[(i+2)%5]))<<i for i in range(5))
table=[[0]*32 for _ in range(32)]
images=[chi5(x) for x in range(32)];assert len(set(images))==32
for d in range(32):
    for x in range(32):table[d][images[x]^images[x^d]]+=1
assert all(sum(row)==32 for row in table)
assert all(table[d][0]==0 for d in range(1,32))
# Justify the rejection shortcut below, independently of the saved tail total.
# A nonzero row with no bit 4 cannot produce an output supported only on bit 4.
assert all(table[d][0]+table[d][16]==0 for d in range(1,16))

def back(outputs,dependencies):return set().union(*(dependencies(o) for o in outputs))
def chi_dep(o):
    x,y,z=o;return {((x+i)%5,y,z) for i in range(3)}
inverse_rho_pi={}
for x,y,z in itertools.product(range(5),range(5),range(64)):
    inverse_rho_pi[(y,(2*x+3*y)%5,(z+ROT[x][y])%64)]=(x,y,z)
assert len(inverse_rho_pi)==1600
def theta_dep(o):
    x,y,z=o
    return {(x,y,z)}|{((x-1)%5,yy,z) for yy in range(5)}|{((x+1)%5,yy,(z-1)%64) for yy in range(5)}
def cone(planes):
    key={(x,0,z) for x in range(4) for z in planes}
    chi5_inputs=back(key,chi_dep)
    theta5_outputs={inverse_rho_pi[o] for o in chi5_inputs}
    chi4_outputs=back(theta5_outputs,theta_dep)
    chi4_inputs=back(chi4_outputs,chi_dep)
    return {'key_bits':len(key),'chi5_inputs':len(chi5_inputs),
            'chi4_outputs':len(chi4_outputs),'chi4_inputs':len(chi4_inputs)}
cones={label:cone(planes) for label,planes in [('contiguous35',range(35)),('contiguous29',range(29)),('all64',range(64)),('stride7_35',sorted({7*i%64 for i in range(35)}))]}
assert [(r['chi4_outputs'],r['chi4_inputs']) for r in cones.values()]==[(1505,1600),(1362,1600),(1600,1600),(1163,1368)]

def rol(x,k):return ((x<<k)|(x>>(64-k)))&M64 if k else x
def linear(s):
    lanes=[(s>>(64*i))&M64 for i in range(25)]
    parity=[lanes[x]^lanes[x+5]^lanes[x+10]^lanes[x+15]^lanes[x+20] for x in range(5)]
    result=[0]*25
    for x,y in itertools.product(range(5),range(5)):
        value=lanes[x+5*y]^parity[(x-1)%5]^rol(parity[(x+1)%5],1)
        result[y+5*((2*x+3*y)%5)]=rol(value,ROT[x][y])
    return sum(v<<(64*i) for i,v in enumerate(result))
alpha3=sum(1<<i for i in (0,130,450,529,701,789,1021,1169,1280,1429))
beta3=linear(alpha3);active=[];options=[]
for y,z in itertools.product(range(5),range(64)):
    d=sum(((beta3>>(64*(x+5*y)+z))&1)<<x for x in range(5))
    if not d:continue
    active.append(d);choices=[]
    for out,weight in enumerate(table[d]):
        if not weight:continue
        value=sum(((out>>x)&1)<<(64*(x+5*y)+z) for x in range(5))
        choices.append((linear(value)&((1<<320)-1),weight))
    options.append(choices)
assert active==[5,8,4,16,2,16,1,2,8]
def half(groups):
    values=[(0,1)]
    for choices in groups:values=[(a^b,p*q) for a,p in values for b,q in choices]
    return values
left,right=half(options[:5]),half(options[5:])
total=Fraction(0);surviving=0;hist={};best=Fraction(0)
for a,pa in left:
    for b,pb in right:
        v=a^b;last=(v>>256)&M64
        if ((v|(v>>64)|(v>>128)|(v>>192))&M64)&~last:continue
        numerator=pa*pb;denominator=32**len(active);count=0
        for z in range(64):
            if not (last>>z)&1:continue
            d=sum(((v>>(64*x+z))&1)<<x for x in range(5))
            numerator*=table[d][0]+table[d][16];denominator*=32;count+=1
        if numerator:
            contribution=Fraction(numerator,denominator);total+=contribution;best=max(best,contribution)
            surviving+=1;hist[count]=hist.get(count,0)+1
assert len(left)*len(right)==524288 and total==Fraction(55,524288)
assert surviving==192 and hist=={0:32,1:96,2:64} and best==Fraction(1,1<<19)
ablation={label:{'records':0,'ok':0,'points':0,'events':[0,0,0,0],'df':[],'paired_df_gain':[],'failures':{}} for label in ('none','F','EDzero','M2','M3','M4')}
for seed in (1,2,5,6,8,9,11):
    records=json.loads((HERE/'data'/f'drop_k{seed}.json').read_text())
    assert len(records)==36 and len({(r['att'],r['drop']) for r in records})==36
    base={r['att']:r for r in records if r['drop']=='none'}
    assert set(base)==set(range(6))
    for r in records:
        group=ablation[r['drop']];group['records']+=1
        if r['status']!='ok':
            assert r['status'] in ('cond','lin') and r['DF'] is None
            group['failures'][r['status']]=group['failures'].get(r['status'],0)+1;continue
        assert r['DF']==1600-r['EM'] and r['npts']==32
        e=r['ev_F_R0_R1_R2'];assert len(e)==4 and all(0<=x<=32 for x in e) and e[3]<=e[2]<=e[1]
        group['ok']+=1;group['points']+=32;group['df'].append(r['DF'])
        group['events']=[a+b for a,b in zip(group['events'],e)]
        if base[r['att']]['status']=='ok':group['paired_df_gain'].append(r['DF']-base[r['att']]['DF'])
expected=[(23,736,[736,736,736,0]),(28,896,[0,896,896,0]),(23,736,[736,736,736,0]),
          (27,864,[864,0,0,0]),(27,864,[864,864,0,0]),(42,1344,[1344,1344,0,0])]
for group,(ok,points,events) in zip(ablation.values(),expected):
    assert group['records']==42 and (group['ok'],group['points'],group['events'])==(ok,points,events)
    dimensions=group.pop('df');group['df_range']=[min(dimensions),max(dimensions)]
    gains=group.pop('paired_df_gain');group['paired_df_gain_range']=[min(gains),max(gains)]
print(json.dumps({'passed':True,'chi5_inputs':32,'ddt_input_pairs':1024,'chi5_is_permutation':True,
    'ablation_saved_data':ablation,
    'structural_cones':cones,
    'tail_model':{'active_input_differences':active,'forward_options_per_row':[len(x) for x in options],
                  'inverse_compatibilities_per_same_numeric_label':[sum(table[d][o]>0 for d in range(32)) for o in active],
                  'enumerated_patterns':len(left)*len(right),'surviving_patterns':surviving,
                  'weighted_sum':str(total),'best_single_weight':str(best),'active_final_rows_histogram':hist},
    'scope':'Exact finite chi DDT, syntactic dependency sets and independent-uniform-row weighted tail model. Not the success probability under the connector sampling law, a global minimal circuit, an attack cost or a new collision.'},indent=2))
