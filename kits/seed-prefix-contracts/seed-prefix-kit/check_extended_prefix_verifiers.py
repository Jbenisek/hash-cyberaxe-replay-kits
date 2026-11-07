"""Bounded CLI controls for two historical prefix verifiers; originals unchanged."""
import hashlib,importlib.util,json,subprocess,sys,tempfile
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sources={n:(ROOT/n).read_bytes() for n in ('verify_full.py','verify_cv.py')}
ref=ROOT/'indep_sha256_check.py'
spec=importlib.util.spec_from_file_location('extended_prefix_reference',ref)
H=importlib.util.module_from_spec(spec);spec.loader.exec_module(H)
def signature(a,b):
    return ''.join('-' if ((a^b)>>i)&1==0 else 'u' if (a>>i)&1 else 'n' for i in range(31,-1,-1))
def rows_for(m1,m2,cv):
    w1,w2=H.expand(m1,41),H.expand(m2,41);s1=s2=tuple(cv);rows=[]
    for t in range(41):
        s1,s2=H.step(s1,t,w1[t]),H.step(s2,t,w2[t])
        rows.append((signature(s1[0],s2[0]),signature(s1[4],s2[4]),signature(w1[t],w2[t])))
    return rows
cases=[]
with tempfile.TemporaryDirectory(prefix='publication-prefix-verifiers-') as tmp:
    work=Path(tmp)
    for n,raw in sources.items():(work/n).write_bytes(raw)
    def pair(m1,m2,c1,c2):
        text='\n'.join('M'+str(i)+': W='+' '.join(f'{x:08x}' for x in m)+'\nchain='+' '.join(f'{x:08x}' for x in c) for i,m,c in ((1,m1,c1),(2,m2,c2)))
        (work/'pair.txt').write_text(text,encoding='utf-8')
    def trail(rows,omit_w=False):
        (work/'trail.xml').write_text('\n'.join(f'{t} A: {a} E: {e}'+('' if omit_w else f' W: {w}') for t,(a,e,w) in enumerate(rows)),encoding='utf-8')
    def run(name,k,*flags):
        return subprocess.run([sys.executable,'-B',name,'pair.txt','trail.xml',str(k),*flags],cwd=work,capture_output=True,text=True,timeout=5)
    m1=[0]*16;m2=[1]+[0]*15;iv=list(H.IV0);correct=rows_for(m1,m2,iv)
    pair(m1,m2,iv,iv);trail(correct)
    for name,k in (('verify_full.py',39),('verify_cv.py',38)):
        p=run(name,k);assert p.returncode==0 and 'VERIFIED' in p.stdout
        cases.append({'tool':name,'case':'reference-generated maximum supported CLI prefix','exit_code':0,'endpoint':k})
        wrong=list(correct);wrong[0]=('0'*32,wrong[0][1],wrong[0][2]);trail(wrong)
        p=run(name,0);assert 'INVALID' in p.stdout and p.returncode==0
        cases.append({'tool':name,'case':'invalid A condition still exits zero','exit_code':0})
        trail([('z'*32,'z'*32,'z'*32)]*41)
        p=run(name,0);assert p.returncode==0 and 'VERIFIED' in p.stdout
        cases.append({'tool':name,'case':'unknown symbol z treated as unconstrained','exit_code':0})
        p=run(name,-1);assert p.returncode==0 and 'VERIFIED' in p.stdout
        cases.append({'tool':name,'case':'negative endpoint vacuous pass','exit_code':0})
        trail(correct)
        p=run(name,k+1);assert p.returncode!=0 and 'IndexError' in p.stderr
        cases.append({'tool':name,'case':'above implemented CLI range raises IndexError','exit_code':p.returncode,'endpoint':k+1})
    wrong=list(correct);wrong[0]=(wrong[0][0],wrong[0][1],'-'*32);trail(wrong)
    p=run('verify_full.py',0);assert 'INVALID' in p.stdout and 'W part 1' in p.stdout and p.returncode==0
    q=run('verify_cv.py',0);assert 'VERIFIED' in q.stdout and q.returncode==0
    cases.append({'tool':'both','case':'full checks W; cv ignores the contradictory W row'})
    trail(correct,omit_w=True)
    p=run('verify_full.py',0);assert p.returncode==0 and 'VERIFIED' in p.stdout
    cases.append({'tool':'verify_full.py','case':'absent W field has zero W violations'})
    changed=list(iv);changed[0]^=1;pair(m1,m1,iv,changed)
    trail([('-'*32,'-'*32,'-'*32)]*41)
    actual1,actual2=H.step(tuple(iv),0,0),H.step(tuple(changed),0,0)
    assert (actual1[0],actual1[4])!=(actual2[0],actual2[4])
    for name in sources:
        p=run(name,0);assert p.returncode==0 and 'VERIFIED' in p.stdout
        cases.append({'tool':name,'case':'second chaining value ignored; both runs use first'})
    pair(m1,m2,changed,changed);trail(correct)
    p=run('verify_full.py',0,'--iv')
    assert p.returncode==0 and 'VERIFIED' in p.stdout and 'differs from the IV in 1/256 bits' in p.stdout
    cases.append({'tool':'verify_full.py','case':'--iv overrides declared chain and reports mismatch without rejecting'})
    for name,raw in sources.items():assert (work/name).read_bytes()==raw
for name,raw in sources.items():assert (ROOT/name).read_bytes()==raw
report={'passed':True,'finished_at':datetime.now(timezone.utc).isoformat(),
 'source_files':[{'path':'research/tools/kepler_tools/'+n,'sha256':hashlib.sha256(raw).hexdigest()} for n,raw in sources.items()],
 'input_files':[{'path':'research/tools/indep_sha256_check.py','sha256':hashlib.sha256(ref.read_bytes()).hexdigest()}],
 'results':cases,
 'scope':'Fifteen disposable CLI fixtures against independent SHA-256 rows. These are prefix predicates, not digest equality or domain certification. No production source, old verdict or witness was modified; independently replayed pairs are not invalidated by these interface limits.'}
print(json.dumps(report,indent=2))
