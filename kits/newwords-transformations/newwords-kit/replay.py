"""Compare three historical text transformations on synthetic data. No solver."""
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
if not __debug__: raise SystemExit('Do not run with Python -O')
BASE='research/game/climber/guided/'
sources={
    'newwords/nw.py':'7f78c0ea2113ad2dad0719073befea20862001ff801c81f456e060b026382a1b',
    'newwords/nw2.py':'ae862e7e76a1c482344337251b51ec7c42e7cf8474fc84f7cfac9ee0d878841f',
    'newwords/nw3.py':'234f7071722859e1fb7d6483dd3fc1f29309f5d53cbf6620c99dc51efda7d628',
    'kit/char_pair_profile.py':'1b9e8011a2104447f9941cc19134a13abd56191c2bd834985f9ef7dc85ee8611'}
child='''import importlib.util,json,sys
from pathlib import Path
root=Path(sys.argv[1]); results=[]
for name in ('nw','nw2','nw3'):
    spec=importlib.util.spec_from_file_location(name,root/'newwords'/f'{name}.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    for band in ('b0811','b1215','b1619'):
        target=root/f'{name}_{band}.xml'
        if name=='nw': n=module.mkchar('hyb38',str(target))
        else: n=module.mkchar('hyb38',str(target),band)
        results.append({'module':name,'band':band,'n':n,'file':target.name})
print(json.dumps(results))
'''
results=[]
with tempfile.TemporaryDirectory(prefix='library-newwords-') as temporary:
    root=Path(temporary)
    for relative,digest in sources.items():
        raw=(ROOT/relative).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==digest
        target=root/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    chars=root/'chars';chars.mkdir()
    rows=[f'{t} A: {"-"*32} E: {"-"*32}'+(f' W: {"-"*32}' if t>=0 else '') for t in range(-4,39)]
    fixture='<config><options><option name="n" value="39"/></options>\n<char value="\n'+'\n'.join(rows)+'\n"/></config>\n'
    (chars/'hyb38_pin38_to_pin38b_s17g5.xml').write_text(fixture)
    proc=subprocess.run([sys.executable,'-B','-c',child,str(root)],capture_output=True,text=True,timeout=10,check=True)
    outputs=json.loads(proc.stdout);assert len(outputs)==9
    for item in outputs:
        rows=re.findall(r'^\s*(-?\d+) A: ([-?]{32}) E: ([-?]{32})(?: W: ([-?]{32}))?$',(root/item['file']).read_text(),re.M)
        assert item['n']==39 and len(rows)==43
        start={'b0811':8,'b1215':12,'b1619':16}[item['band']]
        expected=[] if item['module']=='nw' else list(range(0 if item['module']=='nw2' else start-4,start))
        free=[]
        for t,a,e,w in rows:
            t=int(t);assert a==e
            assert w==('?'*32 if t>=0 else '')
            if a=='?'*32:free.append(t)
            else:assert a=='-'*32
        assert free==expected
        results.append({**item,'freed_state_rows':free,'schedule_rows_free':39,'passed':True})
    for name in ('nw2','nw3'):
        target=root/f'{name}_char.xml'
        proc=subprocess.run([sys.executable,'-B',str(root/'newwords'/f'{name}.py'),'char','hyb38',str(target)],capture_output=True,text=True,timeout=5,check=True)
        assert proc.stdout.strip()=='39'
        parsed=re.findall(r'^\s*(-?\d+) A: ([-?]{32}) E: ([-?]{32})',target.read_text(),re.M)
        assert len(parsed)==43 and all(a==e=='-'*32 for _,a,e in parsed)
report={'passed':True,'finished_at':datetime.now(timezone.utc).isoformat(),
        'input_files':[{'path':BASE+name,'sha256':digest} for name,digest in sources.items()],
        'scope':'Nine synthetic characteristic-text transformations and two char CLI controls. No seed corpus, CNF generation, SAT solve, message collision or success-rate check.',
        'results':{'transformations':results,'char_cli_without_band_leaves_state_rows_unchanged':2}}
print(json.dumps(report,indent=2))
