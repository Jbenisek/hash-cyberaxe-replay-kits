"""Finite masked-walk compiler/allocation/retained-wasm replay. No searches."""
import ast
import builtins
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
from unittest.mock import patch

if not __debug__:
    raise SystemExit('Run without -O; assertions are verification checks.')
HERE=Path(__file__).resolve().parent
manifest=json.loads((HERE/'MANIFEST.json').read_text(encoding='utf-8'))
for row in manifest['files']:
    path=HERE/row['path']
    assert path.resolve().is_relative_to(HERE.resolve())
    raw=path.read_bytes()
    assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'],row['path']
SOURCE_PIN='b72dd6a3705e844959fdff8ed4f4805484f3d24ae068fd6a9f06992d6cd8a8c1'
WASM_PIN='0918ee3fcc92fb33164ccb9898d2c5b1cf2a28d80e7a3aeee12b031de48648f1'
assert hashlib.sha256((HERE/'bsrho.py').read_bytes()).hexdigest()==SOURCE_PIN
assert hashlib.sha256((HERE/'gen.wasm').read_bytes()).hexdigest()==WASM_PIN
verify=runpy.run_path(str(HERE/'allocation_check.py'))['verify_allocated']
loaded=runpy.run_path(str(HERE/'bsrho.py'),run_name='bounded_copy')
m=loaded['serve'].__globals__
chunks=[]
def capture(source,filename,mode,*args,**kwargs):
    chunks.append(source)
    return builtins.compile(source,filename,mode,*args,**kwargs)
with patch.dict(m,{'compile':capture}):
    step=m['Step'](256)
code,registers=m['allocate'](step)
assert verify(step,code,registers,chunks)==11718 and registers==771
changed=list(code)
row=list(changed[0]);row[2]=registers+1;changed[0]=tuple(row)
try: verify(step,changed,registers,chunks)
except AssertionError: pass
else: raise AssertionError('Changed operand accepted')
changed_chunks=list(chunks);tree=ast.parse(changed_chunks[0])
op=next(n for n in tree.body[0].body if isinstance(n,ast.Assign) and isinstance(n.value,ast.BinOp))
op.value.op=ast.BitAnd() if not isinstance(op.value.op,ast.BitAnd) else ast.BitOr()
changed_chunks[0]=ast.unparse(tree)
try: verify(step,code,registers,changed_chunks)
except AssertionError: pass
else: raise AssertionError('Changed generated operator accepted')
expected=[' '.join([step.opsym[nm][0],str(dst),*(str(r) for r in rs)]) for nm,dst,*rs in code]
proc=subprocess.run(['node','--max-old-space-size=128','probe.cjs'],cwd=HERE,
                    capture_output=True,text=True,timeout=20,check=True)
result=json.loads(proc.stdout)
for run in ('first','second'):
    row=result[run]
    assert row['return_code']==0 and row['info']['err']==0
    assert row['lines']==expected and row['q_hex']==f'{step.qint:064x}'
    assert row['info']['ninst']==11718 and row['info']['nreg']==771
    assert row['memory_bytes']<=1048576
print(json.dumps({'passed':True,'source_sha256':SOURCE_PIN,'wasm_sha256':WASM_PIN,
 'compiled_chunks':len(chunks),'instructions_checked':len(code),'register_extent':registers,
 'negative_controls_rejected':2,'wasm_calls_compared':2,'memory_limits':result['memory_limits'],
 'memory_bytes':result['first']['memory_bytes'],'q_hex':f'{step.qint:064x}',
 'instruction_sha256':result['first']['instruction_sha256'],
 'scope':'Generated allocation and retained wasm program/mask identity only. No new C compilation, independent hash-reference replay, target-machine pricing, native host-memory bound, collision search or success-probability proof.'},indent=2))
