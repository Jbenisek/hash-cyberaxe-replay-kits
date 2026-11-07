"""Finite counterexamples for the archived predictor; never launch a solver."""
import ast, hashlib, json, re, tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
source=ROOT/'predict_signs.py';raw=source.read_bytes()
tree=ast.parse(raw.decode('utf-8'))
names={'parse_base','build_checks','_rotr','_shr','_reaches','nullspace','classify','predict_variant'}
defs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
assert len(defs)==len(names)
ns={'re':re,'ROW':re.compile(r'^\s*(-?\d+) A: \S+ E: \S+ W: (\S+)',re.M)}
exec(compile(ast.Module(body=defs,type_ignores=[]),str(source),'exec'),ns)
M=2**32-1
def rotate(x,n):return ((x>>n)|(x<<(32-n)))&M
def expand17(words):
    w=list(words)
    s0=rotate(w[1],7)^rotate(w[1],18)^(w[1]>>3)
    s1=rotate(w[14],17)^rotate(w[14],19)^(w[14]>>10)
    w.append((s1+w[9]+s0+w[0])&M)
    return w
def signature(a,b):
    return ''.join('-' if ((a>>i)&1)==((b>>i)&1) else ('u' if (a>>i)&1 else 'n') for i in range(31,-1,-1))
left=expand17([1,1]+[0]*14);right=expand17([0]*16)
assert left[16]==0x02004001 and right[16]==0
rows=[signature(a,b) for a,b in zip(left,right)]
mirrored=[r.translate(str.maketrans('un','nu')) for r in rows]
assert mirrored==[signature(b,a) for a,b in zip(left,right)]
with tempfile.TemporaryDirectory(prefix='publication-sign-model-') as tmp:
    fixture=Path(tmp)/'synthetic.xml'
    fixture.write_text('\n'.join(f'{i} A: '+('?'*32)+' E: '+('?'*32)+' W: '+w for i,w in enumerate(rows)),encoding='utf-8')
    word=ns['classify'](fixture,'word');bit=ns['classify'](fixture,'bit')
    assert word['vars']==[0,1,16] and word['eqs']==[frozenset({0,1,16})]
    assert word['groups']==[[0,1,16]]
    assert word['nullset']({0,1}) and not word['nullset']({0,1,16})
    assert ns['predict_variant']('mirror',word)=='UNSAT'
    assert ns['predict_variant']('mirror',bit)=='UNSAT'
    assert ns['predict_variant']('base',word)=='SAT'
idx,piv,basis=ns['nullspace']([0,1,2],[frozenset({1,2}),frozenset({0,1})])
assert basis==[3]
assert (basis[0]&6).bit_count()%2==1
assert all((7&r).bit_count()%2==0 for r in (6,3))
assert source.read_bytes()==raw
report={'passed':True,'finished_at':datetime.now(timezone.utc).isoformat(),
 'source_sha256':hashlib.sha256(raw).hexdigest(),
 'results':{
  'valid_schedule_fixture':{'message_A':[1,1]+[0]*14,'message_B':[0]*16,'W16_A':'02004001','W16_B':'00000000',
   'A_E_masks':'all wildcard','actual_original_and_mirror_schedules':'both explicitly satisfied',
   'predicted_mirror_word_mode':'UNSAT','predicted_mirror_bit_mode':'UNSAT'},
  'component_counterexample':{'equation':'x0+x1+x16=0 over GF(2)','component':[0,1,16],
   'proper_subset_0_1_satisfies':True,'whole_component_satisfies':False},
  'unused_basis_counterexample':{'row_masks':[6,3],'returned_basis':[3],'correct_nonzero_null_vector':7,
   'scope':'classify discards this returned basis; its direct parity membership check does not use it.'}},
 'scope':'Eight extracted definitions and a disposable synthetic schedule fixture. No historical SAT study, complete state collision, solver certificate, success probability or attack cost certified. The original predictor is unchanged.'}
# Report returned through stdout; no persistent output.
print(json.dumps(report,indent=2))
