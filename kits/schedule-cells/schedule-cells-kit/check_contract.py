"""Pinned small enumeration and adversarial input controls; no search campaign."""
import hashlib
import itertools
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

if not __debug__:
    raise SystemExit('Run without -O')
PUB=Path(__file__).resolve().parents[1]
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'check_cells.py'
CHAR=ROOT/'chi37.txt'
PINS={
    'check_cells.py':'870a069cdbca5398fc157248b4b0c7a9e3eaef2ade87e988692d329e4e9cd27e',
    'chi37.txt':'a13112c78c9a088c50c281c00d4d3a1acb1dda6ce1dd56aac434da87a3dc67f4'}
source,characteristic=SOURCE.read_bytes(),CHAR.read_bytes()
assert hashlib.sha256(source).hexdigest()==PINS['check_cells.py']
assert hashlib.sha256(characteristic).hexdigest()==PINS['chi37.txt']
text=characteristic.decode('utf-8-sig')
line=next(l for l in text.splitlines() if l.startswith('var W15 list'))
members=[int(v,16) for v in line.split('#')[0].split()[3:]]
assert len(members)==len(set(members))==32

# Independent bit-index form of sigma1, rather than importing the source.
def sigma1(x):
    return sum((((x>>((bit+17)%32))^(x>>((bit+19)%32))^
                 (x>>(bit+10) if bit+10<32 else 0))&1)<<bit for bit in range(32))

delta=sigma1(1<<29)
changed=[bit for bit in range(32) if delta>>bit&1]
assert changed==[10,12,19]
feed=[bit for bit in range(32) if bit!=29 and sigma1(1<<bit)&delta]
assert feed==[4,6,20,22,27,31]
columns=[sigma1(1<<bit)&delta for bit in feed]
basis={}
for column in columns:
    while column:
        top=column.bit_length()-1
        if top in basis:
            column^=basis[top]
        else:
            basis[top]=column
            break
assert len(basis)==3
mask=(1<<32)-1
dW10=0xfff80c00
assert all(((sigma1(x)-sigma1(x^(1<<29)))&mask)==0x7f400 for x in members)
assert all(((x>>4)^(x>>6))&1==0 and ((x>>20)^(x>>27))&1==0
           and ((x>>22)^(x>>31))&1==1 for x in members)
successes=0
for assignment in itertools.product((0,1),repeat=len(feed)):
    x=(1<<29)|sum(value<<bit for bit,value in zip(feed,assignment))
    successes+=((sigma1(x)-sigma1(x^(1<<29))+dW10)&mask)==0
assert successes==8
cases=[]
with tempfile.TemporaryDirectory(prefix='library-schedule-cells-') as temporary:
    root=Path(temporary)
    def run(label,char_text=text,omit=False,wrong_cwd=False):
        base=root/label
        work=base/'atlas_runs/derive'
        work.mkdir(parents=True)
        (base/'chi').mkdir()
        (work/'check_cells.py').write_bytes(source)
        if not omit:
            (base/'chi/chi37.txt').write_text(char_text,encoding='utf-8')
        result=subprocess.run([sys.executable,'-I','-B',str(work/'check_cells.py')],
                              cwd=base if wrong_cwd else work,capture_output=True,text=True,timeout=10)
        return result
    good=run('pinned')
    assert good.returncode==0,good.stderr
    assert good.stdout.count(' CANCELS')==32
    assert 'cancel on 32/32 l (exact enumeration)' in good.stdout
    assert 'Pr[dW17=0] = 8/64' in good.stdout
    assert 'example pair W17 dMOD=00000000' in good.stdout
    assert 'W15 of example x member in list: True 7dd43a81' in good.stdout
    cases.append({'name':'pinned_32_member_and_64_assignment_enumerations','passed':True,
                  'members':32,'distinct_members':32,'cancelling_members':32})
    cases.append({'name':'independent_bit_formula_and_rank','passed':True,'changed_output_bits':changed,
                  'free_input_bits':feed,'rank':len(basis),'successful_assignments':8,'assignments':64,
                  'independent_uniform_word_count':1<<28,'uniform_word_domain':1<<31})
    missing=run('missing',omit=True)
    assert missing.returncode!=0 and 'FileNotFoundError' in missing.stderr
    cases.append({'name':'missing_characteristic_rejected','passed':True})
    wrong=run('wrong-directory',wrong_cwd=True)
    assert wrong.returncode!=0 and 'FileNotFoundError' in wrong.stderr
    cases.append({'name':'cwd_not_script_location_controls_input_path','passed':True})
    short='var W15 list '+' '.join(f'{x:08x}' for x in members[:-1])
    truncated=run('short',text.replace(line,short))
    assert truncated.returncode!=0 and 'AssertionError' in truncated.stderr
    cases.append({'name':'31_member_list_rejected','passed':True})
    clear='var W15 list '+' '.join(f'{x&~(1<<29):08x}' for x in members)
    badsign=run('wrong-sign',text.replace(line,clear))
    assert badsign.returncode!=0 and 'AssertionError' in badsign.stderr
    cases.append({'name':'wrong_bit29_orientation_rejected','passed':True})
    repeated='var W15 list '+' '.join(f'{members[0]:08x}' for _ in members)
    duplicates=run('duplicates',text.replace(line,repeated))
    assert duplicates.returncode==0 and 'cancel on 32/32 l' in duplicates.stdout
    cases.append({'name':'duplicate_list_members_are_not_rejected_by_original','passed':True,
                  'warning':'The original counts iterations, not distinct admitted members; this wrapper separately verifies the pinned list has 32 distinct values.'})
    modified=text+'\nrow 3 '+'='*32+' '+'='*32+' '+'='*31+'u\n'
    early=run('nonzero-early-word',modified)
    assert early.returncode==0
    assert 'dMOD=00000001 dXOR=0 -> dW3=0' in early.stdout
    cases.append({'name':'edited_early_word_exposes_unvalidated_zero_label','passed':True,
                  'warning':'The original prints a contradictory hard-coded zero statement on this modified input. Do not treat its prose as validation of arbitrary characteristics.'})
report={'passed':True,'finished_at':datetime.now(timezone.utc).isoformat(),'source_sha256':PINS['check_cells.py'],
        'input_files':[{'path':CHAR.relative_to(ROOT).as_posix(),'sha256':PINS['chi37.txt']}],
        'source_files':[{'path':SOURCE.relative_to(ROOT).as_posix(),'sha256':PINS['check_cells.py']},
                        {'path':CHAR.relative_to(ROOT).as_posix(),'sha256':PINS['chi37.txt']}],
        'cases':cases,'admitted_members':32,'admitted_distinct_members':32,
        'free_model_fraction':'1/8','rank':3,'stdout_sha256':hashlib.sha256(good.stdout.encode()).hexdigest(),
        'scope':'Exact local schedule cancellation for the pinned characteristic plus adversarial interface controls. No full compression replay, new probability for the complete attack, or general characteristic parser certification.'}
# Report returned through stdout only.
print(json.dumps(report,indent=2))
