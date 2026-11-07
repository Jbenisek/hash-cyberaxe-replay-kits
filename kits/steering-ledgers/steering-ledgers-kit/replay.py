"""Check exact kit bytes, then recount saved records without a solver."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

if not __debug__:
    raise SystemExit('Run without -O')
HERE=Path(__file__).resolve().parent
manifest=json.loads((HERE/'MANIFEST.json').read_text(encoding='utf-8'))
for row in manifest['files']:
    target=(HERE/row['path']).resolve()
    if not target.is_relative_to(HERE) or not target.is_file():
        raise SystemExit('Missing or invalid kit file')
    raw=target.read_bytes()
    if len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:
        raise SystemExit('Changed kit file: '+row['path'])
proc=subprocess.run([sys.executable,'-I','-B',str(HERE/'check.py')],cwd=HERE,
                    capture_output=True,text=True,timeout=15)
if proc.returncode:
    raise SystemExit(proc.stderr)
data=json.loads(proc.stdout)
assert data['passed']
assert data['alpha_inventory']['summed_integer_counts']==4194304
assert data['larger_saved_ledger']['inventory_return_codes']=={'20':53,'124':11}
assert data['census_shard']['final_rows']==8 and data['census_shard']['interim_rows']==2
print(json.dumps(data,indent=2))
