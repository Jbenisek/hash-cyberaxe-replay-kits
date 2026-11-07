"""Replay saved-label provenance, not a SHA-256 experiment or necessity proof."""
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

if not __debug__:
    raise SystemExit('Run without -O')
ROOT=Path(__file__).resolve().parent
PINS={
    'sources/analyze.py':'457bdde652008dfbce2389eeb123b38d3b3cc11a8d2f5a43084234a5154ef843',
    'sources/build_records.py':'af1679d1a0d28726eb36347a1a0ee516bd05805c78b4390d4e0aaef3c5cc2eee',
    'sources/b14R.txt':'2eaedf117163154bd8fe95e972fab07eea418cbd7b4322ee777f0948462c033d'}
payloads={}
for name,pin in PINS.items():
    raw=(ROOT/name).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=pin:
        raise SystemExit('Source hash differs: '+name)
    payloads[name]=raw
log=payloads['sources/b14R.txt'].decode('utf-8')
tags=[tuple(map(int,parts)) for parts in re.findall(
    r'VTAG class (\d) .*? N (\d+) CELLS (\d+) EXACT (\d+)',log)]
assert tags==[(0,201326592,3117,8032),(1,0,0,0)]
assert len(re.findall(r'prefix log2 P\(rows 6\.\.21\)',log))==6
stages={}
for row,count in re.findall(r'VSTAGE row (\d+) violators alive after resampling (\d+) of',log):
    stages.setdefault(int(row),[]).append(int(count))
assert stages[16]==[2418,2409,2460,2493,2449,2478]
assert all(stages[row]==[0]*6 for row in range(17,22))

with tempfile.TemporaryDirectory(prefix='dig38-label-replay-') as temporary:
    tmp=Path(temporary);(tmp/'out').mkdir()
    (tmp/'analyze.py').write_bytes(payloads['sources/analyze.py'])
    (tmp/'tests.txt').write_text('b14R|finite copied-log check\n',encoding='utf-8')
    (tmp/'out/b14R.txt').write_bytes(payloads['sources/b14R.txt'])
    def run():
        p=subprocess.run([sys.executable,'-I','-B','analyze.py'],cwd=tmp,
            capture_output=True,text=True,timeout=5,check=True)
        assert not p.stderr
        return p.stdout.strip()
    output=run()
    assert 'NO-VIOLATOR' in output and 'N1 0 EX1 0' in output
    assert 'UBgain 1.0004' in output
    data={key:re.search(r'\b'+key+r' (\d+)',output).group(1) for key in ('N1','EX1')}
    data['alive']=re.search(r'alive_rows (\[[^\]]*\])',output).group(1)
    data['die']=re.search(r'die_at (\d+)',output).group(1)
    tree=ast.parse(payloads['sources/build_records.py'])
    functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='verdict']
    assert len(functions)==1
    scope={'res':{'b14R':data}}
    exec(compile(ast.Module(body=functions,type_ignores=[]),'<reviewed-verdict-only>','exec'),scope)
    label,lever=scope['verdict']('b14R')
    assert label=='NECESSARY (violators alive rows [16], die at row 17, never reach the window)'
    assert lever is False
    controls=[]
    for n1,ex1,want in [(0,0,'NO-VIOLATOR'),(1,0,'NECESSARY'),(1,1,'LEVER?')]:
        fixture=('prefix log2 P(rows 6..21) = -1.0\n'
          'VTAG class 0 (base prefix holds) N 10 CELLS 2 EXACT 2\n'
          f'VTAG class 1 (violates base prefix) N {n1} CELLS {ex1} EXACT {ex1}\nexit 0\n')
        (tmp/'out/b14R.txt').write_text(fixture,encoding='utf-8')
        assert want in run()
        controls.append({'N1':n1,'EX1':ex1,'printed_label':want})
print(json.dumps({'passed':True,'source_hashes_checked':len(PINS),
    'historical_parser_output':output,'record_builder_label':label,
    'synthetic_controls':controls,'builder_top_level_executed':False,
    'scope':'Copied-log parsing and extracted classifier only. No sampler, solver, collision verification, necessity proof or validation of the printed statistical bound.'},indent=2))
