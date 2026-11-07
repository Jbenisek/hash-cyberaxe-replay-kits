"""Finite saved-ledger joins. No UNSAT proof, sampler or solver is executed."""
import csv
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import re

if not __debug__:
    raise SystemExit('Run without -O')
PUB=Path(__file__).resolve().parents[1]
ROOT=Path(__file__).resolve().parent
BASE='research/game/climber/guided/'
pins={
 'scan40_topslide/census_0.tsv':'8e564903a5f58ab7b8e6b0ccd0a47404db05b2736b2371029c4646f601bdfad3',
 'w38p/steer/classmap/alpha_set_W10_64.tsv':'34d192cb862e5ae0a90d31b6b7c5a9140776d85da69900e62c0e9036b1182797',
 'w38p/steer/classmap/CLASS_MAP_38.tsv':'e796d8bd8940a4535c203a4d9fa2e011793562bb0cd962dbcd62823712fc7dbf',
 'w38p/steer/classmap/RES.txt':'d9652f3e4bb2184a35d63ef518075851e9acc977cd38d35b21f297d9239260f9'}
raw={name:(ROOT/BASE/name).read_bytes() for name in pins}
assert all(hashlib.sha256(raw[n]).hexdigest()==sha for n,sha in pins.items())
alpha_rows=list(csv.reader(io.StringIO(raw['w38p/steer/classmap/alpha_set_W10_64.tsv'].decode()),delimiter='\t'))
assert len(alpha_rows)==64 and all(len(r)==2 and re.fullmatch('[0-9a-f]{8}',r[0]) for r in alpha_rows)
counts={a:int(n) for a,n in alpha_rows}
assert len(counts)==64 and all(n>0 for n in counts.values()) and sum(counts.values())==4194304
assert list(counts.values())==sorted(counts.values(),reverse=True)
classes=list(csv.DictReader(io.StringIO(raw['w38p/steer/classmap/CLASS_MAP_38.tsv'].decode()),delimiter='\t'))
assert len(classes)==21 and len({r['alpha'] for r in classes})==21
assert {r['beta'] for r in classes}=={'03011296'}
old_unsat=[r for r in classes if r['verdict'].startswith('UNSAT')]
assert len(old_unsat)==15
outside=[r['alpha'] for r in classes if r['alpha'] not in counts]
assert outside==['8fff9f70','cfffa070','f0005f70']
logs=[]
for line in raw['w38p/steer/classmap/RES.txt'].decode().splitlines():
    match=re.fullmatch(r'steer_([0-9a-f]{8})_([0-9a-f]{8}) rc=(\d+) sec=(\d+)(?: s (UNSATISFIABLE))?\s*',line)
    assert match,line
    a,b,rc,sec,status=match.groups()
    assert b=='03011296' and int(rc) in (20,124)
    assert (rc=='20')==(status=='UNSATISFIABLE')
    logs.append({'alpha':a,'rc':int(rc),'seconds':int(sec),'label':status or 'NO_VERDICT_TIMEOUT_CODE'})
assert len(logs)==67 and len({r['alpha'] for r in logs})==67
assert {r['alpha'] for r in logs}==set(counts)|set(outside)
events=[]
for line in raw['scan40_topslide/census_0.tsv'].decode().splitlines():
    if line.startswith('#') and not line.startswith('#u\t'): continue
    parts=line.split('\t')
    interim=parts[0]=='#u'
    if interim: parts=parts[1:]
    assert len(parts)==(8 if interim else 12)
    rounds,words,kicks,verdict,level,seconds,how,name=parts[:8]
    assert verdict==('UNDECIDED' if interim else 'UNSAT')
    events.append({'rounds':int(rounds),'words':words,'kicks':kicks,'verdict':verdict,
                   'budget_level':int(level),'seconds':float(seconds),'how':how,'target':name,'interim':interim})
final=[r for r in events if not r['interim']]
assert len(events)==10 and len(final)==8 and len({r['target'] for r in final})==8
ladder=[r for r in events if r['target']=='top_rec_d+2_R38']
assert [r['budget_level'] for r in ladder]==[0,1,2]
assert [r['verdict'] for r in ladder]==['UNDECIDED','UNDECIDED','UNSAT']
assert len({(r['rounds'],r['words'],r['kicks']) for r in ladder})==1
report={'passed':True,'sources':[{'path':BASE+n,'sha256':h} for n,h in pins.items()],
        'alpha_inventory':{'distinct_values':64,'summed_integer_counts':4194304,'minimum':min(counts.values()),'maximum':max(counts.values()),
            'count_generation_law':'Not identified from the table; neither exhaustive weighting nor sampled frequencies certified.'},
        'class_snapshot':{'rows':21,'unsat_labels':15,'unresolved_labels':6,'outside_inventory':outside},
        'larger_saved_ledger':{'rows':67,'unique_alpha_labels':67,'covers_all_64_inventory_values':True,
            'return_codes':dict(Counter(r['rc'] for r in logs)),
            'inventory_return_codes':dict(Counter(r['rc'] for r in logs if r['alpha'] in counts)),
            'unresolved_inventory_labels':[r['alpha'] for r in logs if r['rc']==124],
            'same_hashed_instances_as_snapshot_proved':False},
        'census_shard':{'final_rows':8,'interim_rows':2,'distinct_target_labels':8,'recorded_rung_sequence':ladder},
        'scope':'Exact saved-record counts and joins only. No UNSAT certificate replay, CNF identity equivalence, exhaustive alpha-domain proof, sampling-law proof or attack-price claim. Timeout return codes remain unresolved. No original program executed.'}
# Offline replay prints only.
print(json.dumps({k:v for k,v in report.items() if k!='sources'},indent=2))
