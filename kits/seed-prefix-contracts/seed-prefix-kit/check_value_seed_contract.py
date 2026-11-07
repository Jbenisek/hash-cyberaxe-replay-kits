"""Check the value-pinning writer on disposable inputs; no nldtool execution."""
import hashlib,importlib.util,json,os,re,subprocess,sys,tempfile
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sources={name:(ROOT/name).read_bytes() for name in ('nld_seed.py','mine_meter.py')}
refpath=ROOT/'indep_sha256_check.py'
spec=importlib.util.spec_from_file_location('publication_value_seed_reference',refpath)
H=importlib.util.module_from_spec(spec);spec.loader.exec_module(H)
def trace(words,cv):
    w=H.expand(words,20);s=tuple(cv)
    result={-1:(s[0],s[4]),-2:(s[1],s[5]),-3:(s[2],s[6]),-4:(s[3],s[7])}
    for t in range(20):s=H.step(s,t,w[t]);result[t]=(s[0],s[4])
    return result,w
def mask(a,b,values=False):
    return ''.join(('1' if (a>>i)&1 else '0') if values and ((a^b)>>i)&1==0
                   else '-' if ((a^b)>>i)&1==0 else 'u' if (a>>i)&1 else 'n' for i in range(31,-1,-1))
words1=[1,1]+[0]*14;words2=[0]*16;cv1=list(H.IV0)
cases=[]
with tempfile.TemporaryDirectory(prefix='publication-value-pins-') as tmp:
    work=Path(tmp)
    for name,raw in sources.items():(work/name).write_bytes(raw)
    setup=work/'setup.xml';setup.write_text('<config><char value=""/><search marker="retained"/></config>',encoding='utf-8')
    for distinct in (False,True):
        cv2=list(cv1);cv2[0]^=int(distinct)
        pair=work/'pair.txt';pair.write_text('\n'.join('W='+' '.join(f'{x:08x}' for x in w)+' chain='+' '.join(f'{x:08x}' for x in cv) for w,cv in ((words1,cv1),(words2,cv2))),encoding='utf-8')
        pair_raw=pair.read_bytes();s1,w1=trace(words1,cv1);s2,w2=trace(words2,cv2)
        for fix,values,nozero in ((4,'7-8',None),(4,'18',None),(19,'',None),(4,'','1'),(4,'','0'),(4,'5-3',None)):
            env=os.environ.copy();env.pop('NOZERO',None)
            if nozero is not None:env['NOZERO']=nozero
            target=work/'out.xml'
            proc=subprocess.run([sys.executable,'-B',str(work/'nld_seed.py'),str(pair),'20',str(fix),str(target),values,str(setup)],cwd=work,env=env,capture_output=True,text=True,check=True,timeout=5)
            txt=target.read_text();rows={int(r):(a,e,w) for r,a,e,w in re.findall(r'^\s*(-?\d+) A: (\S+) E: (\S+)(?:[ \t]+W: (\S+))?',txt,re.M)}
            selected={7,8} if values=='7-8' else {18} if values=='18' else set()
            assert set(rows)==set(range(-4,20)) and '<search marker="retained"/>' in txt
            for t in range(-4,20):
                if t<=fix or t in selected:
                    a,e=(mask(s1[t][j],s2[t][j],t in selected) for j in (0,1))
                elif t>=16 and not nozero:a=e='-'*32
                else:a=e='?'*32
                assert rows[t][:2]==(a,e),(t,fix,values,nozero)
                if t>=0:assert rows[t][2]==mask(w1[t],w2[t],t in selected)
            if values=='18':assert set(rows[18][0]+rows[18][1])&set('un')
            assert pair.read_bytes()==pair_raw
            cases.append({'distinct_chaining_values':distinct,'fix':fix,'value_rows':values,'NOZERO':nozero,'rows_checked':24})
        bad=subprocess.run([sys.executable,'-B',str(work/'nld_seed.py'),str(pair),'20','4',str(work/'bad.xml'),'-1',str(setup)],cwd=work,capture_output=True,text=True,timeout=5)
        assert bad.returncode!=0 and not (work/'bad.xml').exists()
    assert {name:(work/name).read_bytes() for name in sources}==sources
for name,raw in sources.items():assert (ROOT/name).read_bytes()==raw
report={'passed':True,'finished_at':datetime.now(timezone.utc).isoformat(),
 'source_sha256':hashlib.sha256(sources['nld_seed.py']).hexdigest(),
 'input_files':[{'path':'research/tools/funnel/mine_meter.py','sha256':hashlib.sha256(sources['mine_meter.py']).hexdigest()},
                {'path':'research/tools/indep_sha256_check.py','sha256':hashlib.sha256(refpath.read_bytes()).hexdigest()}],
 'results':{'cases':cases,'total_rows_checked':len(cases)*24,'negative_row_argument_rejected':2,
            'value_or_fixed_rows_override_closing_pins':True,'NOZERO_string_zero_disables_closing_pins':True,
            'descending_range_silently_empty':True,'distinct_chaining_values_accepted':True},
 'scope':'Twelve disposable writer cases with independent SHA-256 row comparison. No nldtool, solver, original meter writer, characteristic feasibility, standard-IV domain certificate or collision claim.'}
print(json.dumps(report,indent=2))
