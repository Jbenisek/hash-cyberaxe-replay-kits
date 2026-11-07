"""Synthetic copied-source log controls; no solver or real research log access."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

if not __debug__:
    raise SystemExit('Run without -O')
PUB = Path(__file__).resolve().parents[1]
raw = (Path(__file__).resolve().parent/'bitcost.py').read_bytes()
pin = '254dd5cde6663e6f24ed4c1b2ed4a6820934408a3feb5a393b931dce6d2bc814'
assert hashlib.sha256(raw).hexdigest() == pin
fixture = r'''
import json, math, runpy
from pathlib import Path
d=runpy.run_path('bitcost.py')
header='step\tname\tverdict\tsecs\n'
def file(name,rows):
    Path(name).write_text(header+rows,encoding='utf-8')
def get(paths,name='p'):
    return d['load'](paths)[name]
file('first.tsv','1\tp\tSAT\t8\n2\tp\tSAT\t1\n')
assert get(['first.tsv'])==(0,8,1)
file('held.tsv','1\tp\tHELD\t20\n')
file('sat.tsv','1\tp\tSAT\t4\n')
assert get(['held.tsv','sat.tsv'])==(.5,4,2)
file('appended.tsv','1\tp\tHELD\t20\n'+header+'1\tp\tSAT\t4\n')
assert get(['appended.tsv'])==(0,4,1)
assert get(['held.tsv','held.tsv','sat.tsv'])==(2/3,4,3)
file('unsat.tsv','1\tp\tUNSAT\t2\n')
assert get(['unsat.tsv'])==get(['held.tsv'])==(1,1e9,1)
file('later.tsv','1\tp\tUNSAT\t2\n2\tp\tSAT\t6\n')
assert get(['later.tsv'])==(0,6,1)
file('underscore.tsv','1\t_p\tSAT\t3\n')
assert get(['underscore.tsv'])==(1,1e9,1)
file('filter.tsv','1\tbase\tSAT\t1\n2\tswap_p\tSAT\t1\n3\tp\tSAT\tnot-a-number\n')
assert d['load'](['filter.tsv'])=={}
assert d['load'](['missing-*.tsv'])=={}
assert d['key']({})('new')==(.5,1e6)
file('nonfinite.tsv','1\tp\tSAT\tnan\n')
assert math.isnan(get(['nonfinite.tsv'])[1])
file('negative.tsv','1\tp\tSAT\t-3\n')
assert get(['negative.tsv'])==(0,-3,1)
file('noheader.tsv','1\tp\tSAT\t9\n')
# file() added a header; remove it to test the unconditional first-line skip.
Path('noheader.tsv').write_text('1\tp\tSAT\t9\n',encoding='utf-8')
assert d['load'](['noheader.tsv'])=={}
print(json.dumps({'passed':True,'controls':13,
 'first_success_not_fastest':8,'split_files_stall':.5,'appended_runs_stall':0,
 'duplicate_path_stall':'2/3','held_and_unsat_same_score':True,
 'later_sat_overrides_prior_unsat':True,'leading_underscore_sat_becomes_stall':True,
 'malformed_or_missing_skipped':True,'unseen_prior':[.5,1000000],
 'nan_and_negative_times_accepted':True,'headerless_first_observation_lost':True}))
'''
with tempfile.TemporaryDirectory(prefix='library-bitcost-') as tmp:
    work = Path(tmp)
    (work/'bitcost.py').write_bytes(raw)
    proc = subprocess.run([sys.executable,'-I','-B','-c',fixture],cwd=work,
                          capture_output=True,text=True,timeout=15)
    assert proc.returncode == 0,proc.stderr
    result = json.loads(proc.stdout)
    cli = subprocess.run([sys.executable,'-I','-B','bitcost.py','rank','order.txt','missing-*.tsv'],
                         cwd=work,capture_output=True,text=True,timeout=10)
    assert cli.returncode == 0 and (work/'order.txt').read_text() == '\n'
report = {**result,'source_sha256':pin,'empty_rank_writes_newline':True,
          'scope':'Finite synthetic log contracts, not solver performance, probability or attack cost. Only copied bitcost source and temporary fixture files executed; historical logs and solver drivers untouched.'}
# Offline: print report only.
print(json.dumps(report,indent=2))
