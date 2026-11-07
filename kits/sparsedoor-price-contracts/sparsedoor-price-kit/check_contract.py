"""Copied historical price script, synthetic window statistics only."""

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

import hashlib,json,re,subprocess,sys,tempfile
from datetime import datetime,timezone
from pathlib import Path
if not __debug__:raise SystemExit('Run without -O')
PUB=Path(__file__).resolve().parents[1];ROOT=PUB.parents[1]
source=Path(__file__).resolve().parent/'price.py'
raw=source.read_bytes();pin='e3a88e025bc3fd6cbd80d37f37c249288d3303a5510cb557c381ec408f2324a2'
assert hashlib.sha256(raw).hexdigest()==pin
cases=[];positive=[]
with tempfile.TemporaryDirectory(prefix='library-sparsedoor-price-') as tmp:
    work=Path(tmp)
    def run(rows):
        # Every test gets a fresh tree: old window files cannot contaminate n.
        case=work/str(len(cases));led=case/'led';led.mkdir(parents=True)
        for i,row in enumerate(rows):
            (led/f'win_{i:03d}.json').write_text(json.dumps(row),encoding='utf-8')
        original=raw.decode('utf-8-sig')
        old='__HCA_WORKSPACE__/research/pkg_r39_combined/work'
        assert original.count(old)==1
        script=case/'price.py';script.write_text(original.replace(old,case.as_posix()),encoding='utf-8')
        return subprocess.run([sys.executable,'-I','-B',str(script)],cwd=case,capture_output=True,text=True,timeout=10)
    def check(name):cases.append({'case':name,'passed':True})
    base={'ops':100,'distinct_claws':10,'distinct_groups':5}
    outputs=[]
    for n in (24,73):
        p=run([[base] for _ in range(n)]);assert p.returncode==0,p.stderr
        assert f'n={n} mu+=100 c-=10.00 r-=0.500000' in p.stdout
        board=[float(x) for x in re.findall(r'board=([0-9.]+)',p.stdout)]
        assert len(board)==2 and board[1]>board[0]
        outputs.append(p.stdout.splitlines()[1:]);positive.append({'windows':n,'printed_board_times':board})
        check(f'synthetic-{n}-window-zero-variance-statistics-and-q-ordering')
    assert outputs[0]==outputs[1]
    p=run([[base,{'ops':10**100,'distinct_claws':0}] for _ in range(24)])
    assert p.returncode==0 and p.stdout.splitlines()[1:]==outputs[0]
    check('only-first-json-array-entry-used-extra-entries-ignored')
    p=run([[base] for _ in range(25)]);assert p.returncode!=0 and 'KeyError: 24' in p.stderr
    check('unsupported-window-count-25-fails-hardcoded-factor-lookup')
    p=run([]);assert p.returncode!=0 and 'KeyError: -1' in p.stderr
    check('empty-input-glob-fails-before-price')
    p=run([[dict(base,distinct_claws=0)] for _ in range(24)])
    assert p.returncode!=0 and 'ZeroDivisionError' in p.stderr
    check('zero-claw-denominator-fails')
    p=run([[] for _ in range(24)]);assert p.returncode!=0 and 'IndexError' in p.stderr
    check('empty-window-array-fails')
    skew=[[dict(base,distinct_claws=1,distinct_groups=1)] for _ in range(23)]
    skew.append([dict(base,distinct_claws=10**12,distinct_groups=10**12)])
    p=run(skew);assert p.returncode!=0 and ('math domain error' in p.stderr or 'ValueError: expected a ' in p.stderr)
    assert 'c-=-' in p.stdout
    check('negative-estimated-claw-lower-bound-prints-stats-then-domain-error')
report={'passed':True,'finished_at':datetime.now(timezone.utc).isoformat(),'source_sha256':pin,
        'cases':cases,'synthetic_outputs':positive,'path_literal_relocations':1,
        'scope':'Eight synthetic interface controls, not historical window recounts. Floating statistical estimates and inherited q are not exact success bounds; Fraction wraps already-rounded work. No sparse-head cost or new attack price is proved.'}
# Report returned through stdout only.
print(json.dumps(report,indent=2))
