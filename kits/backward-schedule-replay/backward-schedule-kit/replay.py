"""Offline backward-schedule numerical audit, without mapped-drive dependencies."""
import hashlib,json,subprocess,sys
from pathlib import Path
if not __debug__:raise SystemExit('Run without -O')
ROOT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/'MANIFEST.json').read_text(encoding='utf-8'))
names=[row['path'] for row in manifest['files']]
assert len(names)==len(set(names))
assert set(names)=={'check.py','reference.py','replay.py','README.md','LESSON.md',
                    'SCHED_TAILLIGHTEST_board_tail.txt','VALUE_SCREEN_PRICED_TRAILS_1031.tsv'}
for row in manifest['files']:
    raw=(ROOT/row['path']).read_bytes()
    assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
result=subprocess.run([sys.executable,'-I','-B',str(ROOT/'check.py')],cwd=ROOT,
                      capture_output=True,text=True,timeout=30)
assert result.returncode==0,result.stderr
data=json.loads(result.stdout)
assert data['passed'] and data['round_trips']==2048 and data['late_xor_weight']==7
assert data['screen_rows']==16 and data['screen_distinct_trails']==8
assert not data['standard_iv_collision'] and not data['original_brief_checked']
print(json.dumps(data,indent=2))
