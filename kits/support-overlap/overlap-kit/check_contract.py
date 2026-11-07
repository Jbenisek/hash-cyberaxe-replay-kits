"""Synthetic interface controls for a support-only comparison; no historical recount."""
import ast
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime,timezone
from pathlib import Path

if not __debug__:raise SystemExit('Run without -O')
PUB=Path(__file__).resolve().parents[1];ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'dariia_overlap.py'
PIN='8415c9b129ddd0ab1ad5a16e91564326e7471109e1a0a8e1d2c1c25574eab8dd'
source=SOURCE.read_bytes();assert hashlib.sha256(source).hexdigest()==PIN
header='steps,words,kicks,weight_cap,status\n'
cases=[]
with tempfile.TemporaryDirectory(prefix='library-overlap-controls-') as temp:
    def run(name,ours,external):
        root=Path(temp)/name/'research'
        work=root/'outside/dariia_in';work.mkdir(parents=True)
        (work/'dariia_overlap.py').write_bytes(source)
        if ours is not None:
            target=root/'game/climber/guided/scan40';target.mkdir(parents=True)
            (target/'census_fixture.tsv').write_text(ours,encoding='utf-8')
        if external is not None:
            target=work/'unsat_1027/unsat_data_2026-10-27';target.mkdir(parents=True)
            (target/'screen.csv').write_text(external,encoding='utf-8')
        return subprocess.run([sys.executable,'-I','-B','dariia_overlap.py'],cwd=work,
                              capture_output=True,text=True,timeout=10)
    def check(name,ours,external,summary,extra=()):
        result=run(name,ours,external)
        assert result.returncode==0,(name,result.stderr)
        found=re.search(r'overlap (\d+) agree (\d+) disagree (\d+)',result.stdout)
        assert found and tuple(map(int,found.groups()))==summary,(name,result.stdout)
        for text in extra:assert text in result.stdout,(name,result.stdout)
        cases.append({'name':name,'passed':True,'overlap_agree_disagree':list(summary)})
        return result.stdout
    ours='40\t3,1\t2\tSAT\n'
    external=header+'40,1 3,2,8,SAT\n'
    check('order_is_normalized',ours,external,(1,1,0))
    stdout=check('different_caps_and_conflicting_external_labels_still_agree',ours,
                 header+'40,1 3,2,8,SAT\n40,3 1,2,16,UNSAT\n40,1 3,2,12,HELD\n',
                 (1,1,0),('her decided supports (distinct) 1',))
    counts=ast.literal_eval(stdout.splitlines()[0].split('Dariia rows by status ',1)[1])
    assert counts=={'SAT':1,'UNSAT':1,'HELD':1}
    cases[-1]['warning']='Weight cap is not in the join key. A set containing both SAT and UNSAT agrees with either local label.'
    check('last_local_decided_row_wins',ours+'40\t1,3\t2\tUNSAT\n',external,(1,0,1))
    cases[-1]['warning']='This fixture fixes row order inside one file. Glob order across several files is not specified.'
    check('missing_local_glob_is_not_an_error',None,external,(0,0,0),
          ('ours decided 0','her supports NEW to us 1'))
    check('repeated_external_rows_are_one_support',ours,external+'40,1 3,2,8,SAT\n',(1,1,0),
          ("{'SAT': 2}",'her decided supports (distinct) 1'))
    check('duplicate_word_indices_are_not_set_normalized',ours,header+'40,1 1 3,2,8,SAT\n',
          (0,0,0),('her supports NEW to us 1',))
    check('undecided_labels_are_not_decided_supports','40\t1,3\t2\tHELD\n',
          header+'40,1 3,2,8,UNKNOWN\n',(0,0,0),('her decided supports (distinct) 0',))
    for name,local,foreign,error in (
        ('missing_external_file',ours,None,'FileNotFoundError'),
        ('missing_required_header',ours,'steps,status\n40,SAT\n','KeyError'),
        ('malformed_local_word', '40\tnot-a-number\t2\tSAT\n',external,'ValueError')):
        result=run(name,local,foreign)
        assert result.returncode!=0 and error in result.stderr,(name,result.stdout,result.stderr)
        cases.append({'name':name,'passed':True,'rejected_with':error})
report={'passed':True,'finished_at':datetime.now(timezone.utc).isoformat(),
        'source_sha256':PIN,'cases':cases,
        'scope':'Ten synthetic copied-source interface controls. Historical 3,063 supports are not recounted; equal support labels do not establish equal models, checked UNSAT certificates or collision witnesses.'}
# Report returned through stdout only.
print(json.dumps(report,indent=2))
