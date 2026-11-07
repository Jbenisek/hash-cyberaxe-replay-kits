"""Recount saved family-map editions without running their producers or solvers."""
import collections
import csv
import hashlib
import json
import sys
import re
from datetime import datetime, timezone
from pathlib import Path

PUB=Path(__file__).resolve().parent
BASE=PUB/'originals'
ORIGINAL_PINS={'FAMILY_PLACES.tsv': '5fb090aadd7a3ed09d4eaa990af4bc87e42c448dd593f5f0be4ed237e75b49b9', 'places_summary.tsv': 'f79b6b39d2eed575f333fc9cd72513b722d262e21484d10da9c9546a84f1d5af', 'top_families.tsv': 'fab20a4d290c54b0f17caf05cfce30b5ade547469375602e84b527bceba69c6f'}
DICTIONARY_PIN='d941891224ab244f785c452fd34333711ab9165470be3f5f3ab3bd5913921189'


def number(text):
    return float(text) if text else 1e9


def ranking(row):
    # Independently expressed exact persisted rank policy, not a cost theorem.
    has_value=bool(re.search(r'BASE|char:SAT|stdIV',row['value']))
    kicks=int(row['nk']);shift=int(row['y'])
    return (-int(has_value),kicks or 99,-int(shift>=8),-int(shift>=6),
            -int(row['side']=='R+1 wall'),-int(row['rank']),number(row['t']))


def main():
    if not __debug__:raise SystemExit('Run without -O')
    if sys.argv[1:] not in ([],['--emit-projection']):raise ValueError('Unknown arguments')
    names=tuple(ORIGINAL_PINS)
    pins={name:hashlib.sha256((BASE/name).read_bytes()).hexdigest() for name in names}
    if pins!=ORIGINAL_PINS:raise ValueError('Original table edition changed')
    if hashlib.sha256((PUB/'dictionary.json').read_bytes()).hexdigest()!=DICTIONARY_PIN:raise ValueError('Reviewed dictionary changed')
    manifest=json.loads((PUB/'manifest.json').read_text(encoding='utf-8'))
    expected_files={'originals/'+name for name in names}|{'replay.py','README.txt','dictionary.json','records.json'}
    if set(manifest['files'])!=expected_files:raise ValueError('Manifest inventory differs')
    if any(hashlib.sha256((PUB/name).read_bytes()).hexdigest()!=pin for name,pin in manifest['files'].items()):raise ValueError('Kit member changed')
    families=set();cells=set();status=collections.Counter();layers=collections.Counter();mismatches=[]
    with (BASE/'FAMILY_PLACES.tsv').open(encoding='utf-8',newline='') as stream:
        for line,row in enumerate(csv.DictReader(stream,delimiter='\t'),2):
            if None in row or None in row.values():raise ValueError('Malformed map row '+str(line))
            family=(row['shape_D'],row['shape_L']);key=(*family,int(row['x_R']),int(row['y_shift']))
            if key in cells:raise ValueError('Duplicate family/R/shift cell')
            cells.add(key);families.add(family);status[row['best_verdict']]+=1;layers[row['best_layer']]+=1
            shift=key[-1]
            if int(row['R_minus_y'])!=key[-2]-shift or (row['flag_y6_board']=='Y')!=(shift>=6) or (row['flag_y8_r39pipe']=='Y')!=(shift>=8):
                mismatches.append(line)
    with (BASE/'places_summary.tsv').open(encoding='utf-8',newline='') as stream:
        summary=list(csv.DictReader(stream,delimiter='\t'))
    with (BASE/'top_families.tsv').open(encoding='utf-8',newline='') as stream:
        top=list(csv.DictReader(stream,delimiter='\t'))
    eligible=collections.defaultdict(list)
    for row in summary:
        if int(row['R'])>=40 and int(row['rank'])>=4:eligible[row['D']].append(row)
    expected=[]
    for rows in eligible.values():expected.append(min(rows,key=ranking))
    expected.sort(key=ranking)
    if len(expected)!=len(top):raise ValueError('Word-family ranking count differs')
    for index,(want,got) in enumerate(zip(expected,top),1):
        if int(got['rank_no'])!=index or any(want[k]!=got[k] for k in ('sid','D','L','R','y','rank','value')):
            raise ValueError('Persisted ranking differs at '+str(index))
    candidates=[]
    for row in top:
        shift=int(row['y'])
        if shift>=6:
            candidates.append({'rank':int(row['rank_no']),'normalized_D':row['D'],'normalized_L':row['L'],
                'absolute_D':[int(i)+shift for i in row['D'].split(',')],
                'absolute_L':[int(i)+shift for i in row['L'].split(',')] if row['L'] else [],
                'R':int(row['R']),'shift':shift,'recorded_layer':row['layer'],
                'recorded_verdict':row['v'],'recorded_value_context':row['value']})
    result={'passed':not mismatches,
        'source_root':'originals','source_pins':pins,
        'map_cells':len(cells),'distinct_shape_D_L_families':len(families),'summary_places':len(summary),
        'ranked_word_D_families_at_R_ge40':len(top),
        'ranked_rows_shift_ge6':sum(int(row['y'])>=6 for row in top),
        'ranked_rows_shift_ge8':sum(int(row['y'])>=8 for row in top),
        'shift_flag_and_offset_mismatches':mismatches,'recorded_best_verdicts':dict(status),
        'recorded_best_layers':dict(layers),'persisted_rank_policy_reproduced':True,
        'shift_ge6_candidates':candidates,'proofs_replayed':0,'research_programs_executed':False,
        'scope':'Exact retained-table aggregation and rank-policy reproduction only. A family is not a witness, a rank is not a price, shift flags are not contest acceptance, and saved SAT/UNSAT labels are not independently checked certificates.'}
    # Fail on concurrent edition drift rather than binding a mixed snapshot.
    if any(hashlib.sha256((BASE/name).read_bytes()).hexdigest()!=pin for name,pin in pins.items()):
        raise ValueError('Family-map source changed during audit')
    if mismatches:raise ValueError('Shift flag or offset mismatch')
    if '--emit-projection' in sys.argv:
        print(json.dumps(result,indent=2));return
    if json.loads((PUB/'records.json').read_text(encoding='utf-8'))!=result:raise ValueError('Records differ from the retained tables')
    print(json.dumps({k:v for k,v in result.items() if k not in ('source_pins','shift_ge6_candidates')},indent=2))


if __name__=='__main__':main()
