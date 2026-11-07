"""Independently expand two pinned-by-capture numerical B schedule exports.

Reads numerical checker output only. No original encoder, solver or job runs.
"""
import hashlib
import json
import sys
import re
from datetime import datetime,timezone
from pathlib import Path

PUB=Path(__file__).resolve().parent
SHARE=PUB/'originals'
ORIGINAL_PINS={'LIFT_s1.check': '5c23e5d6c2593dc11ffba21b2871a73f7a35b35ed6c11789f1985881466c6747', 'LIFT_s1.check_research': '5c23e5d6c2593dc11ffba21b2871a73f7a35b35ed6c11789f1985881466c6747', 'LIFT_s2.check': 'adcfec1e20440a218d29e0c4064eca9fb81630cd34df6b2130530b04d739b367', 'LIFT_s2.check_research': 'adcfec1e20440a218d29e0c4064eca9fb81630cd34df6b2130530b04d739b367', 'LIFT_s9.check': 'e299a74cc0629b5dbfd467b796a017e6491e532f15c597628b2fc7d096d155f6'}
WANT_INPUT=[8,9,10,11,13,15];WANT_EXPANDED=[16,20,25,28,29]
MASK=(1<<32)-1


def rotate(value,n):return ((value>>n)|(value<<(32-n)))&MASK
def small0(value):return rotate(value,7)^rotate(value,18)^(value>>3)
def small1(value):return rotate(value,17)^rotate(value,19)^(value>>10)


def expand(words):
    result=list(words)
    for t in range(16,40):result.append((small1(result[t-2])+result[t-7]+small0(result[t-15])+result[t-16])&MASK)
    return result


def parse(raw):
    lines=raw.decode('utf-8-sig').splitlines()
    if len(lines)!=3:raise ValueError('Unexpected numerical export shape')
    messages=[]
    for prefix,line in zip(('M1','M2'),lines[:2]):
        if not re.fullmatch(prefix+r'(?: [0-9a-f]{8}){16}',line):raise ValueError('Expected exactly16 32-bit words')
        messages.append([int(word,16) for word in line.split()[1:]])
    support=WANT_INPUT+WANT_EXPANDED
    expected='difference support through word 39 : '+str(support)+' | wanted '+str(support)+' -> VERIFIED'
    if lines[2]!=expected:raise ValueError('Recorded checker label/context differs; reconcile it separately')
    if messages[0]==messages[1]:raise ValueError('Messages must differ')
    return messages


def main():
    if not __debug__:raise SystemExit('Run without -O')
    if sys.argv[1:] not in ([],['--emit-projection']):raise ValueError('Unknown arguments')
    if any(hashlib.sha256((SHARE/name).read_bytes()).hexdigest()!=pin for name,pin in ORIGINAL_PINS.items()):raise ValueError('Original numerical edition changed')
    manifest=json.loads((PUB/'manifest.json').read_text(encoding='utf-8'))
    expected={'originals/'+name for name in ORIGINAL_PINS}|{'replay.py','README.txt','records.json'}
    if set(manifest['files'])!=expected:raise ValueError('Manifest inventory differs')
    if any(hashlib.sha256((PUB/name).read_bytes()).hexdigest()!=pin for name,pin in manifest['files'].items()):raise ValueError('Kit member changed')
    pins={};rows=[];mutations=0
    for seed in (1,2,9):
        name='LIFT_s'+str(seed)+'.check';raw=(SHARE/name).read_bytes()
        names=[name]+([name+'_research'] if seed in (1,2) else [])
        if any((SHARE/n).read_bytes()!=raw for n in names):raise ValueError('Reconcile different checker outputs before interpreting aliases')
        messages=parse(raw);expanded=[expand(words) for words in messages]
        input_support=[i for i in range(16) if messages[0][i]!=messages[1][i]]
        expanded_support=[i for i in range(16,40) if expanded[0][i]!=expanded[1][i]]
        if input_support!=WANT_INPUT or expanded_support!=WANT_EXPANDED:
            raise ValueError('Independent expansion does not match sparse B')
        forced=[]
        for word in (13,20,29):
            a,b=expanded[0][word],expanded[1][word]
            if a^b!=0x80000000 or ((b-a)&MASK)!=0x80000000:
                raise ValueError('Forced half-modulus relation failed')
            forced.append({'word':word,'A':format(a,'08x'),'B':format(b,'08x'),'XOR':'80000000','additive_B_minus_A':'80000000'})
        # Same pair is not accepted after a single-bit change to a common word.
        changed=[list(words) for words in messages];changed[1][0]^=1
        if [i for i in range(16) if changed[0][i]!=changed[1][i]]==WANT_INPUT:
            raise ValueError('Common-word mutation was not detected')
        mutations+=1
        for filename,payload in [(n,raw) for n in names]:
            pins[filename]=hashlib.sha256(payload).hexdigest()
        rows.append({'id':'b32-lift-s'+str(seed),'source_names':names,
            'source_sha256':hashlib.sha256(raw).hexdigest(),
            'M1':[format(v,'08x') for v in messages[0]],'M2':[format(v,'08x') for v in messages[1]],
            'expanded_M1':[format(v,'08x') for v in expanded[0]],'expanded_M2':[format(v,'08x') for v in expanded[1]],
            'input_difference_words':input_support,'expanded_difference_rows':expanded_support,
            'forced_top_bit_words':forced,'W13_bit31_direction':'0-to-1' if messages[0][13]>>31==0 else '1-to-0',
            'CV_supplied':False,'compression_collision_checked':False})
    identities={tuple(sorted((tuple(row['M1']),tuple(row['M2'])))) for row in rows}
    if len(identities)!=3:raise ValueError('Duplicate unordered numerical pair')
    projection={'format':'hashsmash-b32-schedule-exports-v1','word_width':32,'schedule_words':40,
        'source_pins':pins,'source_file_names':5,'distinct_numerical_pairs':3,'records':rows,
        'scope':'Three exact full-width message-schedule pairs for sparse B. No chaining value, compatible full state, legal whole-message padding, compression collision or attack price is established.'}
    raw=(json.dumps(projection,indent=2)+'\n').encode('utf-8')
    if '--emit-projection' in sys.argv:
        print(json.dumps(projection,indent=2));return
    if json.loads((PUB/'records.json').read_text(encoding='utf-8'))!=projection:raise ValueError('Records differ from exact numerical replay')
    report={'passed':True,'checked_at':datetime.now(timezone.utc).isoformat(),'source_root':str(SHARE),
        'source_pins':pins,'source_file_names':5,'distinct_numerical_pairs':3,
        'independent_expansion_checked_words':240,'forced_top_bit_relations_checked':9,
        'W13_orientations':[row['W13_bit31_direction'] for row in rows],
        'common_word_mutations_rejected':mutations,'projection_sha256':hashlib.sha256(raw).hexdigest(),
        'original_encoder_or_solver_executed':False,'production_files_changed':False,
        'scope':projection['scope']}

    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
