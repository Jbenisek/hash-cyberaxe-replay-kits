"""Finite saved-row and DIMACS reconciliation. Does not run a SAT solver."""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
if not __debug__:
    raise SystemExit('Run without -O: assertions are part of this checker.')
manifest = json.loads((HERE/'manifest.json').read_text())
for name, pin in manifest['files'].items():
    assert Path(name).name == name
    raw = (HERE/name).read_bytes()
    assert len(raw) == pin['bytes'] and hashlib.sha256(raw).hexdigest() == pin['sha256'], name
data = json.loads((HERE/'records.json').read_text())


def parse(name):
    raw = (HERE/name).read_bytes()
    assert b'<!DOCTYPE' not in raw and b'<!ENTITY' not in raw
    root = ET.fromstring(raw)
    assert root.tag == 'config' and {c.tag for c in root} == {'options','char'}
    assert len(root) == 2 and len(root.findall('char')) == 1
    assert {r.attrib['name']:r.attrib['value'] for r in root.findall('./options/option')} == {'f':'sha2','n':'40','w':'32'}
    value = root.find('char').attrib['value']
    pattern = r'(-?\d+) A: ([?xun01-]{32}) E: ([?xun01-]{32})(?: W: ([?xun01-]{32}))?'
    matches = list(re.finditer(pattern,value))
    assert re.sub(pattern,'',value).strip() == ''
    rows = {int(m[1]):(m[2],m[3],m[4]) for m in matches}
    assert len(matches) == len(rows) == 44 and set(rows) == set(range(-4,40))
    assert all(rows[r][2] is not None for r in range(40))
    return rows


base = parse('base.xml')
active = {r for r,(a,e,w) in base.items() if r >= 0 and set(a+e)-{'?'}}
assert active == set(range(28)) | set(range(32,40))
records = data['deletion_records']
assert len(records) == 18
for record in records:
    tag = record['test']
    assert re.fullmatch(r't\d{3}',tag)
    rows = parse(tag+'.xml')
    freed = set(record['freed_rows'])
    assert freed <= active and len(freed) == len(record['freed_rows'])
    for r in rows:
        assert rows[r][2] == base[r][2]
        assert rows[r][:2] == (('?'*32,'?'*32) if r in freed else base[r][:2]), (tag,r)
    kept = sorted(r for r,(a,e,w) in rows.items() if r >= 0 and set(a+e)-{'?'})
    assert kept == record['retained_state_rows']
assert records[0]['freed_rows'] == [] and records[0]['recorded_verdict'] == 'UNSAT'
free = set()
cursor = 1
for size in (8,4,2,1):
    keep = sorted(active-free)
    for i in range(0,len(keep),size):
        block = set(keep[i:i+size])-free
        if not block:
            continue
        saved = records[cursor]
        assert saved['freed_rows'] == sorted(free|block)
        assert saved['recorded_verdict'] in ('SAT','UNSAT','UNKNOWN')
        if saved['recorded_verdict'] == 'UNSAT':
            free |= block
        cursor += 1
assert cursor == 18 and sorted(active-free) == data['final_retained_state_rows'] == [1,2,3,4,5]
assert Counter(r['recorded_verdict'] for r in records) == {'UNSAT':7,'UNKNOWN':11}
assert data['minimality_proved'] is False and data['solver_verdicts_independently_certified'] is False

aliases = defaultdict(list)
checked_cnfs = {}
for peel in data['peels']:
    label = peel['label']
    assert re.fullmatch(r'v_[0-9x_]+',label)
    rows = parse(label+'.xml')
    assert all(rows[r][2] == base[r][2] for r in rows)
    assert all(rows[r] == base[r] for r in range(-4,0))
    assert all(rows[r][:2] in (base[r][:2],('?'*32,'?'*32)) for r in range(40))
    assert sorted(r for r,(a,e,w) in rows.items() if r >= 0 and set(a+e)-{'?'}) == peel['retained_state_rows']
    assert (HERE/(label+'.out')).read_text().strip() == peel['recorded_verdict']
    assert peel['recorded_verdict'] in ('s UNSATISFIABLE','s UNKNOWN')
    digest = peel['cnf_sha256']
    assert re.fullmatch(r'[a-f0-9]{64}',digest)
    aliases[digest].append(label)
    if digest not in checked_cnfs:
        raw = (HERE/(digest+'.cnf')).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == digest
        variables = clauses = None
        ended = True
        count = 0
        for line in raw.splitlines():
            tokens = line.split()
            if not tokens or tokens[0] == b'c':
                continue
            if tokens[0] == b'p':
                assert variables is None and len(tokens) == 4 and tokens[1] == b'cnf'
                variables, clauses = map(int,tokens[2:])
                assert variables > 0 and clauses >= 0
                continue
            assert variables is not None
            for token in tokens:
                lit = int(token)
                assert abs(lit) <= variables
                ended = lit == 0
                count += int(ended)
        assert ended and count == clauses
        checked_cnfs[digest] = (variables,clauses)
    assert checked_cnfs[digest] == (peel['variables'],peel['clauses'])
assert len(data['peels']) == 7 and len(checked_cnfs) == 5
assert sorted(v for v in aliases.values() if len(v)>1) == [['v_0x27','v_0x31','v_0x5_6x27']]
print(json.dumps({'passed':True,'deletion_rows_checked':18,'peel_rows_checked':7,
    'unique_dimacs_structurally_checked':5,'final_retained_state_rows':[1,2,3,4,5],
    'minimality_proved':False,'solver_run':False,'proof_certificate_checked':False,
    'scope':'Recorded row transformations, greedy policy, aliases and DIMACS structure only; not independent SAT/UNSAT certification.'},indent=2))
