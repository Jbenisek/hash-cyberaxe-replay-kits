"""Run the reviewed sign writer only on disposable fixtures and destinations."""
import hashlib,json,os,re,subprocess,sys,tempfile
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent
source=ROOT/'mirror.py';raw=source.read_bytes()
sha=hashlib.sha256(raw).hexdigest();assert sha=='cdbe0d9d811a6b88b1ac0b18fbb8473e97b149ef77d343bbf57a7c37a2fb8f23'
rows=[(-1,'-'*32,'-'*32,None),(0,'u'+'-'*31,'n'+'-'*31,'u'+'-'*31),
      (1,'0'+'-'*31,'1'+'-'*31,'n'+'-'*31),(16,'-'*32,'-'*32,'u'+'-'*31)]
text='<config><char value="\n'+'\n'.join(f' {r} A: {a} E: {e}'+(' W: '+w if w else '') for r,a,e,w in rows)+'\n"/></config>'
def parse(t):
    return {int(m[1]):(m[2],m[3],m[4]) for m in re.finditer(r'^\s*(-?\d+) A: (\S+) E: (\S+)(?: W: (\S+))?',t,re.M)}
cases=[]
with tempfile.TemporaryDirectory(prefix='library-sign-variants-') as tmp:
    base=Path(tmp);tool=base/'mirror.py';tool.write_bytes(raw);fixture=base/'base.xml';fixture.write_text(text)
    for sched,statex in ((False,False),(True,False),(False,True),(True,True)):
        env=os.environ.copy();env.pop('SCHED',None);env.pop('STATEX',None)
        if sched:env['SCHED']='1'
        if statex:env['STATEX']='1'
        for optional in (False,True):
            out=base/f'case-{sched}-{statex}-{optional}'
            cmd=[sys.executable,str(tool),str(fixture),str(out)]+(['0,1'] if optional else [])
            proc=subprocess.run(cmd,cwd=base,env=env,capture_output=True,text=True,check=True,timeout=5)
            names=(out/'list.txt').read_text().splitlines()
            assert names==(['xexp','flip0','flip1','flip0_1'] if optional else ['base','mirror','xexp','flip0','flip1'])
            variants={n:parse((out/(n+'.xml')).read_text()) for n in names}
            for n,rs in variants.items():
                for row,a,e,w in rows:
                    expected_a='?'*32 if sched else a.replace('u','x').replace('n','x') if statex else a
                    expected_e='?'*32 if sched else e.replace('u','x').replace('n','x') if statex else e
                    assert rs[row][:2]==(expected_a,expected_e)
            if not optional:
                assert variants['mirror'][0][2]=='n'+'-'*31
                assert variants['mirror'][1][2]=='u'+'-'*31
                assert variants['mirror'][16][2]=='n'+'-'*31
                if not sched and not statex:
                    assert variants['mirror'][0][0]=='u'+'-'*31 # Signed state was NOT mirrored.
            assert variants['xexp'][16][2]=='x'+'-'*31
            assert variants['flip0'][0][2]=='n'+'-'*31
            assert variants['flip0'][1][2]=='n'+'-'*31
            assert variants['flip0'][16][2]=='x'+'-'*31
            assert variants['flip1'][0][2]=='u'+'-'*31
            if optional:
                assert variants['flip0_1'][0][2]=='n'+'-'*31 and variants['flip0_1'][1][2]=='u'+'-'*31
            cases.append({'schedule_only':sched,'state_sign_relaxation':statex,'explicit_combo_list':optional,'outputs':len(names)})
    assert fixture.read_text()==text and tool.read_bytes()==raw
assert hashlib.sha256(source.read_bytes()).hexdigest()==sha
report={'passed':True,'finished_at':datetime.now(timezone.utc).isoformat(),'source_sha256':sha,
        'results':{'flag_cases':cases,'generated_variants':sum(r['outputs'] for r in cases),
                   'default_mirror_changes_only_W_signs':True,'signed_state_pins_preserved_not_mirrored':True,
                   'partial_flip_expanded_rows_relaxed_to_x':True,'source_untouched':True},
        'scope':'Eight disposable CLI cases and 36 generated text variants. No solver, schedule feasibility, collision, sign-space rank or runtime-gain claim. Default W-only mirror is not a full pair-swap equivalence when asymmetric signed A/E pins remain.'}
# Report returned through stdout; no persistent output.
print(json.dumps(report,indent=2))
