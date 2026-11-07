"""Private copied-source width-boundary controls; never invoke a SAT solver."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

if not __debug__:
    raise SystemExit('Run without -O')
PUB = Path(__file__).resolve().parents[1]
source = Path(__file__).resolve().parent/'schedcnf.py'
raw = source.read_bytes()
pin = 'f442b063a19cb413bd3d96698395b5ca44a32ef3e9942f1096446a048399d7a4'
assert hashlib.sha256(raw).hexdigest() == pin
fixture = r'''
import json, runpy, sys
d=runpy.run_path(sys.argv[1])
w=d['WB']
def rank(f):
    basis={}
    for bit in range(w):
        v=f(1<<bit)
        while v:
            p=v.bit_length()-1
            if p not in basis:
                basis[p]=v
                break
            v ^= basis[p]
    return len(basis)
a=[0]*16;b=a.copy();b[1]=1
ea=d['expand'](a,17);eb=d['expand'](b,17)
support=[i for i in range(17) if ea[i]!=eb[i]]
c,_=d['build_relax'](17,{1},set())
counterexamples=[]
if w <= 8:
    for sigma,index in (('s0',1),('s1',14)):
        kernel=next((x for x in range(1,1<<w) if d[sigma](x)==0),None)
        if kernel is None:continue
        ma=[0]*16;mb=ma.copy();mb[index]=kernel
        ea0=d['expand'](ma,17);eb0=d['expand'](mb,17)
        actual=[t for t in range(17) if ea0[t]!=eb0[t]]
        relax,_=d['build_relax'](17,{index},set())
        full,words=d['build'](17,{index},set())
        values={}
        for side,msg in enumerate((ma,mb)):
            for i in range(16):
                for bit,var in enumerate(words[side][i]):
                    value=bool(msg[i]&(1<<bit))
                    assert var not in values or values[var]==value
                    values[var]=value
        # Fixed-input propagation only: no decision or search step.
        while True:
            changed=False
            for clause in full.cl:
                if any(abs(lit) in values and values[abs(lit)]==(lit>0) for lit in clause):continue
                free=[lit for lit in clause if abs(lit) not in values]
                assert free,'Numerical witness contradicted by the direct CNF'
                if len(free)==1:
                    lit=free[0];values[abs(lit)]=lit>0;changed=True
            if not changed:break
        assert len(values)==full.n
        assert all(any(values[abs(lit)]==(lit>0) for lit in clause) for clause in full.cl)
        assert actual==[index] and [] in relax.cl
        counterexamples.append({'sigma':sigma,'word_index':index,'kernel_word':kernel,
            'numerical_support':actual,'full_cnf_satisfied':True,'full_cnf_variables':full.n,
            'full_cnf_clauses_checked':len(full.cl),'relaxation_has_empty_clause':True})
print(json.dumps({'word_bits':w,'sigma0_rank':rank(d['s0']),'sigma1_rank':rank(d['s1']),
    'numerical_support':support,'relaxation_has_empty_clause':[] in c.cl,
    'message_a':a,'message_b':b,'expanded_word16':[ea[16],eb[16]],'counterexamples':counterexamples}))
'''
rows = []
with tempfile.TemporaryDirectory(prefix='library-sched-width-') as tmp:
    work = Path(tmp)
    target = work/'schedcnf.py'
    target.write_bytes(raw)
    for width in (2,8,16,32):
        env = {k:v for k,v in os.environ.items() if k not in ('SHARE','DSUB','LSUB','HW','HWSET','HWSOFT','WB','PINXOR')}
        env['WB'] = str(width)
        proc = subprocess.run([sys.executable,'-I','-B','-c',fixture,str(target)],cwd=work,
                              env=env,capture_output=True,text=True,timeout=15)
        assert proc.returncode == 0,proc.stderr
        rows.append(json.loads(proc.stdout))
    assert rows[0]['numerical_support'] == [1]
    assert rows[0]['expanded_word16'] == [0,0]
    assert rows[0]['sigma0_rank'] == 1 and rows[0]['relaxation_has_empty_clause']
    assert rows[-1]['sigma0_rank'] == rows[-1]['sigma1_rank'] == 32
    assert len(rows[0]['counterexamples'])==2 and len(rows[1]['counterexamples'])==1
    assert rows[1]['counterexamples'][0]['sigma']=='s1'
    # Missing assignments decode as zero. MISMATCH is text, not a failing exit.
    empty = work/'empty.model'
    empty.write_text('',encoding='utf-8')
    env['WB'] = '32'
    proc = subprocess.run([sys.executable,'-I','-B',str(target),'--check','17','1','',str(empty)],
                          cwd=work,env=env,capture_output=True,text=True,timeout=15)
    assert proc.returncode == 0 and 'MISMATCH' in proc.stdout
report = {'passed':True,'source_sha256':pin,'fixtures':rows,
    'empty_model_mismatch_exit_code':proc.returncode,
    'finding':'The lone-term rejection is unsound for scaled sigmas with nonzero kernels: two WB=2 controls and one WB=8 control give explicit valid message pairs and satisfy every direct-CNF clause, while the relaxation inserts an empty clause.',
    'scope':'Exact finite reduced-width counterexamples and source behavior only. The standard 32-bit small sigmas are full-rank in the checked linear algebra; no 32-bit unsoundness, historical false verdict or collision is established. Only fixed-input clause propagation, no branching search, external solver, compiler or persistent process.'}
# Offline replay prints only.
print(json.dumps(report,indent=2))
