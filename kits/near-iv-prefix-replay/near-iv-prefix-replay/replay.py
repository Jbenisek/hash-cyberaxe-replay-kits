"""Replay retained near-IV raw-block examples. No search or network."""
import hashlib
import importlib.util
import json
import re
import struct
import xml.etree.ElementTree as ET
from pathlib import Path

if not __debug__:
    raise SystemExit('Run without -O: this finite verifier requires assertions.')
HERE=Path(__file__).resolve().parent
manifest=json.loads((HERE/'manifest.json').read_text(encoding='utf-8'))
for name,item in manifest['files'].items():
    assert Path(name).name==name
    raw=(HERE/name).read_bytes()
    assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'],name
data=json.loads((HERE/'records.json').read_text(encoding='utf-8'))
reference=HERE/'sha256_reference.py'
assert hashlib.sha256(reference.read_bytes()).hexdigest()==data['reference_sha256']=='b241e3c742b9f345fc7a049897a6dfd6342573a2d899fa05876134eb40b5fc61'
spec=importlib.util.spec_from_file_location('near_iv_reference',reference)
H=importlib.util.module_from_spec(spec);spec.loader.exec_module(H)
ALLOWED={'?':{(0,0),(0,1),(1,0),(1,1)},'-':{(0,0),(1,1)},'x':{(0,1),(1,0)},
         'u':{(1,0)},'n':{(0,1)},'0':{(0,0)},'1':{(1,1)}}
assert ALLOWED['u']=={(1,0)} and ALLOWED['n']=={(0,1)}


def words(text,length):
    tokens=text.strip().split()
    assert len(tokens)==length and all(re.fullmatch(r'[0-9a-fA-F]{8}',token) for token in tokens)
    return [int(token,16) for token in tokens]


def trace(message,cv):
    W=H.expand(message,64);state=tuple(cv);states=[]
    values={'A':{-i-1:cv[i] for i in range(4)},'E':{-i-1:cv[i+4] for i in range(4)},'W':dict(enumerate(W))}
    for t in range(64):
        state=H.step(state,t,W[t]);states.append(list(state))
        values['A'][t]=state[0];values['E'][t]=state[4]
    return values,states


def check(first,second,rows):
    result=[]
    for row in rows:
        t=row['row']
        if not 0<=t<=18:continue
        bad={}
        for field in ('A','E','W'):
            if field not in row:continue
            bad[field]=[31-i for i,c in enumerate(row[field])
                        if ((first[field][t]>>(31-i))&1,(second[field][t]>>(31-i))&1) not in ALLOWED[c]]
        result.append({'row':t,'violations':bad})
    assert [row['row'] for row in result]==list(range(19))
    return result


masks=[]
for source in data['mask_sources']:
    name=source['file'];assert Path(name).name==name
    raw=(HERE/name).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==source['sha256']
    assert b'<!DOCTYPE' not in raw.upper() and b'<!ENTITY' not in raw.upper()
    root=ET.fromstring(raw)
    options={item.attrib['name']:item.attrib['value'] for item in root.findall('./options/option')}
    assert options.get('f')=='sha2' and options.get('w')=='32' and options.get('n')=='39'
    chars=root.findall('char');assert len(chars)==1
    value=chars[0].attrib['value']
    pattern=r'(-?\d+)\s+A:\s*([^\s]+)\s+E:\s*([^\s]+)(?:\s+W:\s*([^\s]+))?'
    rows=[]
    for match in re.finditer(pattern,value):
        row={'row':int(match[1]),'A':match[2],'E':match[3]}
        if match[4]:row['W']=match[4]
        assert all(len(row[field])==32 and set(row[field])<=ALLOWED.keys() for field in ('A','E','W') if field in row)
        rows.append(row)
    assert not re.sub(pattern,'',value).strip() and len({row['row'] for row in rows})==len(rows)
    prefix_sha=hashlib.sha256(json.dumps([row for row in rows if 0<=row['row']<=18],sort_keys=True,separators=(',',':')).encode()).hexdigest()
    assert prefix_sha==source['rows0_through18_projection_sha256']
    masks.append({'name':name,'rows':rows,'prefix_sha256':prefix_sha})
assert len(masks)==7 and len({mask['prefix_sha256'] for mask in masks})==data['distinct_prefix_projections']==2

for message in (b'',b'abc',bytes(range(55))):
    block=message+b'\x80'+b'\0'*(55-len(message))+struct.pack('>Q',8*len(message))
    assert struct.pack('>8I',*H.compress(H.IV0,struct.unpack('>16I',block)))==hashlib.sha256(message).digest()

prefixes=bcd=printed_count=mutation_controls=0
distances=[]
for saved in data['records']:
    name=saved['file'];assert Path(name).name==name
    raw=(HERE/name).read_bytes();text=raw.decode('utf-8-sig')
    assert hashlib.sha256(raw).hexdigest()==saved['source_sha256']
    messages=[words(re.search(r'^M'+str(side)+r': W=([^\r\n]+)$',text,re.M)[1],16) for side in (1,2)]
    chains=[words(value,8) for value in re.findall(r'^\s*chain=([^\r\n]+)$',text,re.M)]
    assert len(chains) in (1,2) and all(cv==chains[0] for cv in chains)
    cv=chains[0]
    assert len(chains)==saved['printed_chain_occurrences']
    assert [[f'{x:08x}' for x in message] for message in messages]==saved['messages']
    assert [f'{x:08x}' for x in cv]==saved['chaining'] and messages[0]!=messages[1]
    ordered=sorted(messages)
    assert hashlib.sha256(struct.pack('>40I',*(cv+ordered[0]+ordered[1]))).hexdigest()==saved['identity_sha256']
    word_distances=[bin(x^y).count('1') for x,y in zip(cv,H.IV0)]
    assert word_distances==saved['cv_word_hamming_distances'] and sum(word_distances)==saved['cv_total_hamming_distance']
    assert (cv[1:4]==H.IV0[1:4])==saved['b_c_d_equal_standard_iv']
    assert (cv==H.IV0)==saved['standard_iv']
    traces=[trace(message,cv) for message in messages]
    matches=[]
    for mask,expected in zip(masks,saved['mask_comparisons']):
        checks=check(traces[0][0],traces[1][0],mask['rows'])
        bad=[row['row'] for row in checks if any(row['violations'].values())]
        actual={'mask':mask['name'],'first_bad_row':min(bad) if bad else None,
                'bad_bits_through_row18':sum(len(bits) for row in checks for bits in row['violations'].values()),'row_checks':checks}
        assert actual==expected
        if not bad:
            matches.append(mask['name'])
            mutation=messages[0].copy();mutation[0]^=1
            assert any(any(row['violations'].values()) for row in check(trace(mutation,cv)[0],traces[1][0],mask['rows']))
            mutation_controls+=1
    assert len(saved['mask_comparisons'])==7 and matches==saved['matching_masks_rows0_through18']
    printed=[words(value,8) for value in re.findall(r'^\s*out=([^\r\n]+)$',text,re.M)]
    assert len(printed) in (0,2)
    assert (bool(printed) and printed==[result[1][38] for result in traces])==saved['printed_out_matches_39_step_working_state']
    if printed:assert printed==[result[1][38] for result in traces]
    outputs=[H.compress(cv,message,39) for message in messages]
    assert sum(a==b for a,b in zip(*outputs))==saved['equal_feedforward_output_words_at39']==0
    assert (outputs[0]==outputs[1])==saved['collision_at39']==False
    assert [i+1 for i in range(64) if traces[0][1][i]==traces[1][1][i]]==saved['equal_working_states_step_counts']
    if 'set_c_to_standard_iv_control' in saved:
        fixed=cv.copy();fixed[2]=H.IV0[2]
        altered=[trace(message,fixed)[0] for message in messages]
        control=saved['set_c_to_standard_iv_control']
        assert cv[2]^fixed[2]==1<<control['changed_initial_bit']
        checks=check(altered[0],altered[1],masks[0]['rows'])
        bad=[row['row'] for row in checks if any(row['violations'].values())]
        assert checks==control['row_checks'] and min(bad)==control['first_bad_row']==7
        assert sum(bin(x^y).count('1') for x,y in zip(fixed,H.IV0))==control['cv_hamming_distance_after_change']==23
    prefixes+=bool(matches);bcd+=saved['b_c_d_equal_standard_iv'];printed_count+=bool(printed)
    distances.append(sum(word_distances))
assert len(data['records'])==5 and prefixes==4 and bcd==1 and printed_count==4
assert sorted(distances)==[22,24,25,46,57] and data['eight_pair_historical_population_recovered'] is False
print(json.dumps({'passed':True,'saved_examples':5,'prefixes_through_row18':4,
                  'b_c_d_at_standard_iv':1,'collisions_at39':0,'equal_digest_words_at39':0,
                  'mask_editions':7,'distinct_prefix_projections':2,'hashlib_controls':3,
                  'mutated_message_mask_rejections':mutation_controls,'c_bit14_restore_first_bad_row':7,
                  'scope':'Finite raw-block chosen-CV prefix checks, not standard-IV or padded-message collisions, an eight-pair population or an attack price.'},indent=2))
