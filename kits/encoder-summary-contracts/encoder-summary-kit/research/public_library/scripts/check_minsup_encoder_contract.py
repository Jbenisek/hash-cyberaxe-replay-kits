"""Finite gate/trace and decoder-contract checks; no SAT solver or research writes."""
import contextlib,hashlib,importlib.util,io,itertools,json,os,struct,tempfile
from datetime import datetime,timezone
from pathlib import Path
if not __debug__: raise SystemExit('Run without -O')
PUB=Path(__file__).resolve().parents[1];ROOT=PUB.parents[1]
source=ROOT/'research/game/climber/guided/minsup/sha_cnf.py'
reference=ROOT/'research/tools/indep_sha256_check.py'
digest=hashlib.sha256(source.read_bytes()).hexdigest()
assert digest=='5a6b7373b8aac2312a9c017436c17ed4d29caed27343d959af76de687e33f1aa'
assert hashlib.sha256(reference.read_bytes()).hexdigest()=='b241e3c742b9f345fc7a049897a6dfd6342573a2d899fa05876134eb40b5fc61'
# This process owns only its own environment; all generated files are temporary.
for key in ('WBITS','DIFFVARS','BITORDER','CHAINREV','SIGNED','KOFF','EXTRAW','MODDIFF',
            'SCHED_ONLY','NEAR_K','NEAR_ENC','NEAR_OUTS','REQUIRE_DIFF','SYMBREAK','XORMODE','XOR3'):
    os.environ.pop(key,None)
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
C=load('publication_minsup_contract',source);H=load('publication_independent_sha',reference)
for msg in (b'',b'abc',bytes(range(32)),bytes(range(55))):
    block=msg+b'\x80'+b'\0'*(55-len(msg))+struct.pack('>Q',8*len(msg))
    assert struct.pack('>8I',*H.compress(H.IV0,struct.unpack('>16I',block)))==hashlib.sha256(msg).digest()
def sat(c,v):
    lit=lambda x: v[abs(x)] if x>0 else not v[abs(x)]
    return all(any(lit(x) for x in cl) for cl in c.cl) and all(sum(lit(x) for x in cl)%2==1 for cl in c.xcl)
gates=0
for mode in (False,True):
    C.XORMODE=mode
    for name,arity,truth in (('xor2',2,lambda a,b:a^b),('maj',3,lambda a,b,c:(a+b+c)>=2),('ch',3,lambda a,b,c:b if a else c)):
        for inp in itertools.product((False,True),repeat=arity):
            c=C.CNF();ids=[c.var() for _ in inp];out=getattr(c,name)(*ids)
            for candidate in (False,True):
                val={1:True,**dict(zip(ids,inp)),out:candidate}
                assert sat(c,val)==(candidate==truth(*inp)),(mode,name,inp,candidate)
                gates+=1
class Tracked(C.CNF):
    def __init__(self,words):super().__init__();self.values={1:True};self.words=iter(words)
    def bit(self,x):return self.values[abs(x)] if x>0 else not self.values[abs(x)]
    def assign(self,x,v):
        if abs(x)==1:assert self.bit(x)==bool(v)
        else:self.values[abs(x)]=bool(v) if x>0 else not bool(v)
        return x
    def word(self):
        ids=super().word();v=next(self.words)
        for i,x in enumerate(ids):self.assign(x,(v>>i)&1)
        return ids
    def xor2(self,a,b):return self.assign(super().xor2(a,b),self.bit(a)^self.bit(b))
    def maj(self,a,b,c):return self.assign(super().maj(a,b,c),sum((self.bit(a),self.bit(b),self.bit(c)))>=2)
    def ch(self,a,b,c):return self.assign(super().ch(a,b,c),self.bit(b) if self.bit(a) else self.bit(c))
    def value(self,bits):return sum(int(self.bit(x))<<i for i,x in enumerate(bits))
cases=[]
msg=[(0x9e3779b9*(i+1)+0x1020304)&H.M for i in range(16)]
cv=[x^0xa5a5a5a5 for x in H.IV0]
for mode in (False,True):
    C.XORMODE=mode
    for n,law,offset in ((1,'iv',0),(4,'free',0),(17,'iv',0),(39,'free',0),(3,'iv',7)):
        C.KOFF=offset;chain=H.IV0 if law=='iv' else cv
        chain_words=[x for pair in zip(chain[:4],chain[4:]) for x in pair]
        c=Tracked(msg+([] if law=='iv' else chain_words));c.add(1)
        p=C.sha_instance(c,n,law)
        assert sat(c,c.values),(mode,n,law,offset)
        state=tuple(c.value(p[reg][n-1-i]) for reg in ('A','E') for i in range(4))
        expected=tuple(chain);expanded=H.expand(msg,n)
        for t in range(n):expected=H.step(expected,t+offset,expanded[t])
        assert state==expected,(mode,n,law,offset)
        assert [c.value(x) for x in p['W']]==expanded
        if offset:assert C.sha_ref(n,chain,msg)!=state, 'Expected historical KOFF decoder mismatch not reproduced'
        else:assert C.sha_ref(n,chain,msg)==state
        cases.append({'steps':n,'chaining':law,'constant_offset':offset,'native_xor':mode,
                      'variables':c.nv,'cnf_clauses':len(c.cl),'xor_clauses':len(c.xcl),
                      'all_generated_clauses_satisfied':True,'independent_state_matches':True,
                      'decoder_reference_matches':offset==0})
        del c,p
C.KOFF=0;C.XORMODE=False
shapes=0
for signed in (False,True):
    C.SIGNED=signed
    for symbol in '-xun01?Z':
        for a,b in itertools.product((False,True),repeat=2):
            c=C.CNF();x=c.word();y=c.word();v={1:True,**{i:False for i in x+y}};v[x[-1]]=a;v[y[-1]]=b
            C.apply_shape(c,x,y,symbol,[])
            expected={'-':a==b,'x':a!=b,'u':a and not b if signed else a!=b,
                      'n':not a and b if signed else a!=b,'0':not a and not b,'1':a and b,'?':True,'Z':True}[symbol]
            assert sat(c,v)==expected,(signed,symbol,a,b)
            shapes+=1
with tempfile.TemporaryDirectory(prefix='publication-minsup-contract-') as tmp:
    work=Path(tmp);xml=work/'shape.xml'
    xml.write_text('<options><option name="n" value="1"/></options>\n0 A: - E: ? W: ?\n0 A: x E: ? W: ?\n',encoding='utf-8')
    n,rows=C.parse_xml(xml);assert n==1 and rows[0][0]=='x'
    xml.write_text('<options><option name="n" value="1"/></options>\n0 A: ? E: ? W: ?\n',encoding='utf-8')
    with contextlib.redirect_stdout(io.StringIO()):C.encode(xml,work/'pair.cnf',work/'pair.map','iv')
    (work/'empty.model').write_text('',encoding='utf-8')
    stdout=io.StringIO()
    with contextlib.redirect_stdout(stdout):C.decode(work/'pair.map',work/'empty.model')
    assert 'messages differ: False  outputs equal: True' in stdout.getvalue()
report={'passed':True,'finished_at':datetime.now(timezone.utc).isoformat(),'source_sha256':digest,
        'input_files':[{'path':reference.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(reference.read_bytes()).hexdigest()}],
        'results':{'standard_hashlib_controls':4,'gate_truth_assignments':gates,'shape_truth_assignments':shapes,
                   'complete_trace_fixtures':cases,'duplicate_rows_keep_last':True,
                   'empty_model_decodes_trivial_equal_pair':True,'nonzero_KOFF_is_not_honored_by_decoder_reference':True},
        'scope':'Finite 32-bit CNF/native-XOR gate and trace fixtures, shape semantics and decoder negative controls. No solver, complete-model validation, reduced-width certification or proof of all optional modes.'}
(PUB/'qa/minsup-encoder-runtime-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
