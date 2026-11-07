"""Reconcile retained numeric histograms; this is not a GPU sweep."""
import hashlib
import json
import math
from pathlib import Path

HERE=Path(__file__).resolve().parent
if not __debug__:
    raise SystemExit('Run without -O')
manifest=json.loads((HERE/'manifest.json').read_text())
for name,record in manifest['files'].items():
    assert Path(name).name==name
    payload=(HERE/name).read_bytes()
    assert len(payload)==record['bytes'] and hashlib.sha256(payload).hexdigest()==record['sha256'],name
data=json.loads((HERE/'tables.json').read_text())
N=1<<32
assert len(data['histograms'])==7 and len(data['leak_rows'])==61
lookup={row['key']:row for row in data['leak_rows']}
assert len(lookup)==61
for row in data['histograms']:
    hist={int(k):v for k,v in row['histogram'].items()}
    assert all(type(n) is int and n>=0 and 0<=k<=row['steps'] for k,n in hist.items())
    assert sum(hist.values())==N
    assert hist[row['steps']]==1 and row['reported_hit_shifts']==['00000000']
    nonzero={k:v for k,v in hist.items() if k<row['steps'] and v}
    other=lookup[row['key']]
    assert (other['h'],other['delta'])==(row['steps'],row['delta'])
    assert max(nonzero)==other['deepest_row']
    assert sum(v for k,v in nonzero.items() if k>=19)==other['shifts_to_19plus']
    passing=sum(v for k,v in nonzero.items() if k>16)
    assert abs(math.log2(passing/N)-other['pass16_log2'])<1e-12
groups={}
for row in data['leak_rows']:
    assert type(row['shifts_to_19plus']) is int and row['shifts_to_19plus']>=0
    assert 16<=row['deepest_row']<min(20,row['h'])
    key=(row['h'],row['family'],row['delta'])
    group=groups.setdefault(key,[0,0])
    group[0]+=1
    group[1]+=row['shifts_to_19plus']
assert len(groups)==7 and sum(v[1] for v in groups.values())==48
assert all(k[0]==37 and k[2]=='d29' for k,v in groups.items() if v[1])
print(json.dumps({'passed':True,'histograms_checked':7,'leak_rows_checked':61,
    'groups':7,'shifts_reaching_row19':48,'nonzero_full_predicate_passes_in_seven_histograms':0,
    'scope':'Saved count reconciliation only. No GPU rerun, independent collision check, timing certification or general round barrier.'},indent=2))
