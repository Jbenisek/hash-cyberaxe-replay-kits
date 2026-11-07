"""Recount six retained exports; never run an encoder, solver or proof checker."""
import collections
import csv
import hashlib
import io
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

PINS={
 'TRAIL39_CD_COUNT278_w8-12_s23.xml':'7728f48c1ad7166c8e5298a60b958b3f77595fb4798b4a307400585e2f152b0e',
 'TRAIL39_CD_COUNT253_w8-12_s23.xml':'245b6f2780e8c4808bb32d9191ba862dfbd7e8fd5052dbd207138851c2e7a56d',
 'TRAIL39_CD_COUNT253_39cd_w8-12_s3.xml':'245b6f2780e8c4808bb32d9191ba862dfbd7e8fd5052dbd207138851c2e7a56d',
 'FAN39_COUNT278_1101.tsv':'c706b596033cd5b2ae4a9e595118f6e249e06aac3c297aeba0c6904d4e7f96c9',
 'FAN39_COUNT253_1101.tsv':'c3aa48ff7aa0e69a5c0f3dfae77e60e783a4bdaf738d75383a3d7ea9aab73942',
 'FAN39_COUNT253_39cd_w8-12_s3_1101.tsv':'76f8fefff0f38e812b01013fa695379f2197ecb5f3b6ce78ec869ca0030e5fc0',
}


def xml_count(raw):
    if b'<!' in raw:raise ValueError('Declarations/entities are not allowed')
    root=ET.fromstring(raw)
    options={o.attrib['name']:o.attrib['value'] for o in root.findall('./options/option')}
    if root.tag!='config' or options!={'f':'sha2','n':'39','w':'32'} or len(root.findall('char'))!=1:
        raise ValueError('Unexpected XML structure/options')
    text=root.find('char').attrib['value'];last=0;rows=[]
    pattern=re.compile(r'(-?\d+)\s+A:\s+(\S{32})\s+E:\s+(\S{32})(?:\s+W:\s+(\S{32}))?')
    for match in pattern.finditer(text):
        if text[last:match.start()].strip():raise ValueError('Unparsed row text')
        t,a,e,w=match.groups();rows.append((int(t),a,e,w));last=match.end()
    if text[last:].strip() or [r[0] for r in rows]!=list(range(-4,39)):
        raise ValueError('Missing, duplicate, unsorted or trailing rows')
    if any((w is not None)!=(t>=0) for t,a,e,w in rows):raise ValueError('Wrong W row coverage')
    state=collections.Counter(''.join(a+e for t,a,e,w in rows))
    words=collections.Counter(''.join(w for t,a,e,w in rows if 0<=t<16))
    all_words=collections.Counter(''.join(w for t,a,e,w in rows if t>=0))
    value=sum(state[c] for c in '01');diff=sum(state[c] for c in 'unx');wc=sum(words[c] for c in '01unx')
    return {'state_value_bits':value,'state_difference_bits':diff,'STATE':value+diff,
            'input_W':wc,'TOTAL':value+diff+wc,'row_records':43,
            'whole_query_question_marks':state['?']+all_words['?'],
            'legacy_question_marks':state['?']+words['?'],
            'extended_state_symbols_not_interpreted':{c:n for c,n in state.items() if c not in '-unx01?'},
            'extended_W_symbols_not_interpreted':{c:n for c,n in all_words.items() if c not in '-unx01?'}}


def project(folder):
    exports=[];fans=[];fan_rows=[];groups=collections.defaultdict(list)
    for name,pin in PINS.items():
        raw=(folder/'originals'/name).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=pin:raise ValueError('Original export changed: '+name)
        if name.endswith('.xml'):
            row=xml_count(raw);nominal=278 if 'COUNT278' in name else 253
            exports.append({'file':name,'sha256':pin,'filename_count':nominal,**row,
                            'filename_equals_STATE':row['STATE']==nominal,
                            'filename_equals_TOTAL':row['TOTAL']==nominal})
            groups[pin].append(name)
        else:
            rows=list(csv.reader(io.StringIO(raw.decode('utf-8-sig')),delimiter='\t'))
            if len(rows)!=10 or any(len(row)!=4 for row in rows) or len({r[0] for r in rows})!=10:
                raise ValueError('Wrong seed-log shape')
            for seed,status,seconds,registry in rows:
                if not re.fullmatch('seed[0-9]+',seed) or status not in ('UNSATISFIABLE','HELD') or registry!='-':
                    raise ValueError('Unexpected recorded log fields')
                fan_rows.append({'file':name,'seed':seed,'recorded_status':status,'recorded_seconds':int(seconds),'registry':registry})
            fans.append({'file':name,'sha256':pin,'rows':10,'recorded_labels':dict(collections.Counter(r[1] for r in rows))})
    return {'format':'hashsmash-count253-278-recount-v1','source_pins':PINS,'xml_exports':exports,
            'distinct_XML_byte_editions':len(groups),'byte_alias_groups':[names for names in groups.values() if len(names)>1],
            'fan_tables':fans,'fan_rows':fan_rows,
            'recorded_label_totals':dict(collections.Counter(r['recorded_status'] for r in fan_rows)),
            'proofs_replayed':0,
            'scope':'Literal counts and retained labels only. Filename totals are not STATE counts; these masks have question marks. Extended relation symbols are not interpreted, and log filenames do not establish CNF/run identities.'}


def main():
    if not __debug__:raise SystemExit('Run without -O')
    folder=Path(__file__).resolve().parent
    expected=project(folder)
    records=json.loads((folder/'records.json').read_text(encoding='utf-8'))
    if records!=expected:raise ValueError('Records do not match the exact retained exports')
    print(json.dumps({'passed':True,'source_files_recounted':6,'xml_files':3,
                      'distinct_XML_byte_editions':expected['distinct_XML_byte_editions'],
                      'STATE_counts':[r['STATE'] for r in expected['xml_exports']],
                      'TOTAL_counts':[r['TOTAL'] for r in expected['xml_exports']],
                      'whole_query_question_marks':[r['whole_query_question_marks'] for r in expected['xml_exports']],
                      'fan_rows':len(expected['fan_rows']),'recorded_label_totals':expected['recorded_label_totals'],
                      'proofs_replayed':0,'scope':expected['scope']},indent=2))


if __name__=='__main__':main()
