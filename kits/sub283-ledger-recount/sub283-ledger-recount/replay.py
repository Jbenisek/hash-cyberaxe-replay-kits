"""Recount retained search ledgers. This is not a solver or proof checker."""
import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
import re

if not __debug__:
    raise SystemExit('Run without -O: this finite verifier requires assertions.')

PINS = {
    'SUB283_ORACLE_1101.tsv':'f30e57365845cc0b3ecfa4becb01b6c67b8b8f7ecdb4e2622b0bab6143d9afae',
    'DRAT266_1101.txt':'487d244db1166840fc6c0e4849517f6b72a3931012ae022b3f17df351a7cfeb5',
    'POCKET266_1101.tsv':'bc47fb3c1016fe491344e2d9ef0e70ddc9208ea22ac79e8a350ac3b23eff9cdd',
    'POCKET268_1101.tsv':'f2c3c989e7fc4c281320a31ce30ead831f51b0e126660168c9d5228edab30606',
    'WIDEMAP283_v2_1101.tsv':'c2a70ed917cd0db5210817cf3db2008a5e3f8795902e98b0157ea063de2cca39',
}
ROW_COUNTS={'SUB283_ORACLE_1101.tsv':24,'POCKET266_1101.tsv':48,
            'POCKET268_1101.tsv':336,'WIDEMAP283_v2_1101.tsv':28}


def recount(folder):
    rows, summaries = [], []
    for name, expected in ROW_COUNTS.items():
        raw = (folder/name).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==PINS[name], 'Original edition changed: '+name
        lines = raw.decode('utf-8-sig').splitlines()
        footer = None
        if lines[-1].startswith('DONE '):
            footer = re.fullmatch(r'DONE jobs (\d+) probed (\d+)',lines.pop())
            assert footer, 'Malformed footer: '+name
        parsed = list(csv.DictReader(io.StringIO('\n'.join(lines)),delimiter='\t'))
        assert len(parsed)==expected
        assert all(None not in row and all(value is not None for value in row.values()) for row in parsed)
        for row in parsed:
            assert re.fullmatch(r'\d+',row['count'])
            assert row['secs']=='-' or re.fullmatch(r'\d+',row['secs'])
        oracle = name.startswith('SUB283')
        statuses = Counter(row['verdict' if oracle else 'probe'] for row in parsed)
        assert set(statuses)<=({'UNSATISFIABLE','HELD'} if oracle else {'-','UNSATISFIABLE','HELD'})
        if footer:
            assert tuple(map(int,footer.groups()))==(len(parsed),sum(v for k,v in statuses.items() if k!='-'))
        summary={'file':name,'rows':len(parsed),'recorded_statuses':dict(sorted(statuses.items())),
                 'count_min':min(int(row['count']) for row in parsed),
                 'count_max':max(int(row['count']) for row in parsed)}
        if not oracle:
            labels=sorted({row['c2'] for row in parsed})
            summary['generator_labels']={label:sum(row['c2']==label for row in parsed) for label in labels}
            summary['min_count_by_generator_label']={label:min(int(row['count']) for row in parsed if row['c2']==label) for label in labels}
        summaries.append(summary)
        start=len(rows)
        rows.extend({'id':start+i+1,'file':name,'recorded':row} for i,row in enumerate(parsed))
    oracle=[row['recorded'] for row in rows if row['file']=='SUB283_ORACLE_1101.tsv']
    labels=Counter(row['find'] for row in oracle)
    summary=(folder/'DRAT266_1101.txt').read_bytes()
    assert hashlib.sha256(summary).hexdigest()==PINS['DRAT266_1101.txt']
    assert summary.decode().splitlines()==['solve: s UNSATISFIABLE 309 s, proof 299M','check: s VERIFIED 527 s']
    return {'format':'hashsmash-sub283-saved-ledgers-v1','source_pins':PINS,
            'row_count':len(rows),'rows':rows,'summaries':summaries,
            'oracle_find_labels':len(labels),
            'repeated_oracle_find_labels':dict(sorted((k,v) for k,v in labels.items() if v>1)),
            'distinct_formula_count':None,'proofs_replayed':0,
            'certificate_collection_verified':False,
            'drat266':{'summary_bytes':len(summary),'reported_solver_seconds':309,
                       'reported_checker_seconds':527,'reported_size_text':'299M',
                       'proof_payload_included':False},
            'count_unit':'Recorded owner_count STATE: value bits plus difference bits over A/E rows, including chaining rows. Not an attack-work exponent.',
            'scope':'Exact recount of retained TSV rows and a 65-byte reported checker summary. No cryptographic execution, complete-characteristic validation or certificate replay.'}


def main():
    folder=Path(__file__).resolve().parent
    manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    for name,item in manifest['files'].items():
        assert Path(name).name==name
        raw=(folder/name).read_bytes()
        assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'], name
    saved=json.loads((folder/'records.json').read_text(encoding='utf-8'))
    actual=recount(folder)
    assert actual==saved, 'Saved projection differs from the retained rows or overstates its evidence'
    assert actual['row_count']==436 and actual['oracle_find_labels']==20
    assert [row['id'] for row in actual['rows']]==list(range(1,437))
    assert actual['summaries'][0]['recorded_statuses']=={'HELD':1,'UNSATISFIABLE':23}
    print(json.dumps({'passed':True,'rows_recounted':actual['row_count'],
                      'tables_recounted':len(actual['summaries']),
                      'oracle_rows':24,'oracle_labels':20,'proofs_replayed':0,
                      'certificate_collection_verified':False,'summaries':actual['summaries'],
                      'scope':actual['scope']},indent=2))


if __name__=='__main__':
    main()
