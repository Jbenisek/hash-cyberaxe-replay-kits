"""Finite conditional ledger replay; no source workspace or research run needed."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
if not __debug__:
    raise SystemExit('Run without -O')
manifest=json.loads((HERE/'manifest.json').read_text())
for name,entry in manifest['files'].items():
    assert Path(name).name==name
    raw=(HERE/name).read_bytes()
    assert len(raw)==entry['bytes'] and hashlib.sha256(raw).hexdigest()==entry['sha256'],name
from recount import integer_ledger, log2_enclosure, C
data=json.loads((HERE/'ledger.json').read_text())
rows=[]
for expected in data['rows']:
    row=integer_ledger(expected['WALK'])
    assert all(row[key]==expected[key] for key in row),expected['WALK']
    log=log2_enclosure(row['N'],C)
    assert log==expected['time_log2']
    rows.append({'WALK':row['WALK'],'N':row['N'],'time_log2_up':log['rounded_up']})
for subset in range(64):
    flags=sum(1<<(38+42*j) for j in range(6) if (subset>>j)&1)
    expected=[42*j for j in range(6) if (subset>>j)&1]
    actual=[]
    while flags:
        p=(flags&-flags).bit_length()-1
        actual.append(p-38)
        flags &= flags-1
    assert actual==expected
print(json.dumps({'passed':True,'integer_rows':len(rows),'guard_patterns':64,'rows':rows,
                  'scope':'Exact arithmetic under the explicit inherited budget. No new success law, primitive-price authorization, full port or memory proof.'},indent=2))
