"""Replay four archived chosen-CV pairs and the historical CLI's weak contract.

Only copied scripts and disposable JSON fixtures execute. Two literal hardcoded
path roots are relocated; cryptographic expressions are unchanged.
"""

# Publication path adapter: resolve data paths from the extracted source tree.
def _hca_public_path_text(value):
    if "__HCA_WORKSPACE__/" not in value:
        return value
    import os as _hca_os
    from pathlib import Path as _hca_Path
    root = _hca_os.environ.get("HASHCYBERAXE_WORKSPACE")
    if root is None:
        here = _hca_Path(__file__).resolve().parent
        root = next((str(p) for p in (here, *here.parents) if (p / "research").is_dir()), None)
    if root is None:
        raise FileNotFoundError("Extract the research source tree, or set HASHCYBERAXE_WORKSPACE to its archive directory.")
    return value.replace("__HCA_WORKSPACE__/", str(_hca_Path(root).resolve()).replace("\\", "/") + "/")

import hashlib,importlib.util,json,subprocess,sys,tempfile
from pathlib import Path
from datetime import datetime,timezone
if not __debug__:raise SystemExit('Run without -O')
ROOT=Path(__file__).resolve().parent
PATHS={
 'verify_alts.py':('research/retest/four_pattern_contradiction/verify_alts.py','697fc57c17b2be84b34ccb90b23e16fb121cdd8e2f796f8cd1319e9a1b55b8d3'),
 'sha256_ref.py':('research/tighten/r37_unforced_files/sha256_ref.py','7c500e4aa1bb30b8da994faf72a889dfa53d82b6cf114812429b7f91e7559a5d'),
 'indep_sha256_check.py':('research/tools/indep_sha256_check.py','b241e3c742b9f345fc7a049897a6dfd6342573a2d899fa05876134eb40b5fc61'),
 'alt_G1_verify.json':('research/tighten/r37_unforced_files/alt_G1_verify.json','ea7f0632a981822b2f66fae3384a087ea44f8d467814dac96177f2295f1517d2'),
 'alt_G2_verify.json':('research/tighten/r37_unforced_files/alt_G2_verify.json','735911cc91f8aa585bfd3008b9d650a7eac36f033c0c8553b27ff5026d8235d4'),
 'alt_G12_verify.json':('research/tighten/r37_unforced_files/alt_G12_verify.json','b64eaaea8c378c815a50ea1bd652fba06a909e2d15c9f62e80a52080690e1fea'),
 'i_all52_verify.json':('research/tighten/r37_unforced_files/i_all52_verify.json','413aeb74d54ca64fe60131d82de5596ce9e27eadf0c2b96448591559016a327b'),
}
raws={name:(ROOT/name).read_bytes() for name,(rel,_) in PATHS.items()}
for name,raw in raws.items():assert hashlib.sha256(raw).hexdigest()==PATHS[name][1],name
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
cases=[];pairs=[]
with tempfile.TemporaryDirectory(prefix='library-four-pattern-') as tmp:
    work=Path(tmp)
    for name,raw in raws.items():(work/name).write_bytes(raw)
    original=raws['verify_alts.py'].decode('utf-8-sig')
    old='__HCA_WORKSPACE__/research/tighten/r37_unforced_files'
    assert original.count(old)==2
    (work/'verify_alts.py').write_text(original.replace(old,work.as_posix()),encoding='utf-8')
    ref=load(work/'sha256_ref.py','four_pattern_ref')
    independent=load(work/'indep_sha256_check.py','four_pattern_independent')
    known=[b'',b'abc',b'a'*55,b'a'*56,b'a'*64,b'a'*129,bytes(range(256))]
    for msg in known:assert ref.digest(msg)==hashlib.sha256(msg).hexdigest()
    cases.append({'case':'seven-standard-hashlib-controls','passed':True})
    names=['alt_G1','alt_G2','alt_G12','i_all52']
    for name in names:
        j=json.loads(raws[name+'_verify.json'])
        cv,mx,my=([int(x,16) for x in j[key]] for key in ('CV','MX','MY'))
        assert len(cv)==8 and len(mx)==len(my)==16 and mx!=my and cv!=ref.IV
        assert all(0<=x<2**32 for x in cv+mx+my)
        ox,sx,wx=ref.compress(mx,cv,37);oy,sy,wy=ref.compress(my,cv,37)
        assert ox==oy and ''.join(f'{x:08x}' for x in ox)==j['digest']
        assert tuple(ox)==independent.compress(cv,mx,37)==independent.compress(cv,my,37)
        assert wx==independent.expand(mx,37) and wy==independent.expand(my,37)
        pairs.append({'name':name,'steps':37,'standard_iv':False,'distinct_messages':True,
                      'digest':j['digest'],'row_bits_side_a':[
                          {'zero_based_row':t,'e_bits_1_10_29':[(sx[t][4]>>b)&1 for b in (1,10,29)]}
                          for t in (17,18)]})
    cases.append({'case':'four-nontrivial-chosen-cv-collisions-two-references-and-saved-digests','passed':True})
    def run():return subprocess.run([sys.executable,'-I','-B',str(work/'verify_alts.py')],
                                   cwd=work,capture_output=True,text=True,timeout=10)
    p=run();assert p.returncode==0 and p.stdout.count('37-step equal: True')==4,p.stderr
    cases.append({'case':'relocated-original-cli-four-positive-lines','passed':True})
    target=work/'alt_G1_verify.json';j=json.loads(raws[target.name]);original_json=dict(j)
    j['MY']=list(j['MY']);j['MY'][0]=f'{int(j["MY"][0],16)^1:08x}'
    target.write_text(json.dumps(j),encoding='utf-8')
    assert independent.compress([int(x,16) for x in j['CV']],[int(x,16) for x in j['MX']],37)!=independent.compress([int(x,16) for x in j['CV']],[int(x,16) for x in j['MY']],37)
    p=run();assert p.returncode==0 and 'alt_G1 37-step equal: False' in p.stdout
    cases.append({'case':'mutated-message-fails-equality-but-original-cli-still-exits-zero','passed':True})
    j=json.loads(raws[target.name]);j['MY']=j['MX'];target.write_text(json.dumps(j),encoding='utf-8')
    p=run();assert p.returncode==0 and 'alt_G1 37-step equal: True' in p.stdout
    cases.append({'case':'identical-messages-accepted-as-equal-no-nontriviality-check','passed':True})
    j=json.loads(raws[target.name]);j.update(collision=False,digest='invalid',flipped_values_ok=False,violations_with_flips_applied=['synthetic'])
    target.write_text(json.dumps(j),encoding='utf-8');p=run()
    assert p.returncode==0 and p.stdout.count('37-step equal: True')==4
    cases.append({'case':'saved-verdict-digest-and-constraint-fields-ignored-by-cli','passed':True})
    j.pop('CV');target.write_text(json.dumps(j),encoding='utf-8');p=run()
    assert p.returncode!=0 and 'KeyError' in p.stderr
    cases.append({'case':'missing-required-key-fails','passed':True})
    target.write_bytes(raws[target.name]);(work/'alt_G2_verify.json').unlink();p=run()
    assert p.returncode!=0 and p.stdout.count('37-step equal: True')==1
    cases.append({'case':'missing-second-fixture-leaves-partial-positive-output-before-failure','passed':True})
report={'passed':True,'finished_at':datetime.now(timezone.utc).isoformat(),'source_sha256':PATHS['verify_alts.py'][1],'source_pins':{n:p[1] for n,p in PATHS.items()},
        'cases':cases,'pairs':pairs,'hashlib_controls':7,'path_literal_relocations':2,
        'scope':'Four finite 37-step chosen-CV collisions and historical CLI behavior. Not standard-IV collisions, a full-cell constraint audit, a success probability, the missing P11 witness, or an attack-cost proof.'}
# Report returned through stdout only.
print(json.dumps(report,indent=2))
