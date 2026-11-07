"""Read four saved numerical summaries; no generation, pricing or solver runs."""
import csv
import hashlib
import io
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path
from datetime import datetime, timezone

PUB = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parent
directory = ROOT/'research/game/climber/guided/pairfactory'
pins = {
    'CLASS_SUMMARY.tsv':'bb79a1ad081dfa51a7f88864e39125bad0968fc5772839c39791d9cff1f1976d',
    'RESULTS.tsv':'19eeb4e5456544ca27c75df0fcff769db5757219230a4ca2fd6894120af53edc',
    'RESULTS2.tsv':'1aee1325f47de2fc4b669544bead85a0178394b3138ea951b27f5f63e69223c5',
    'TAILS_B.tsv':'f0ed76f70b78778889f3172a15b1b03cd9067804f287822ba78ae3580b2fe5a2',
}
tables = {}
sources = []
for name,pin in pins.items():
    path = directory/name
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != pin:
        raise ValueError('Source changed: '+name)
    rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8')),delimiter='\t'))
    if not rows or any(None in r or any(v is None for v in r.values()) for r in rows):
        raise ValueError('Invalid table: '+name)
    tables[name] = rows
    relative = path.relative_to(ROOT).as_posix()
    sources.append({'path':relative,'sha256':pin,'rows':len(rows),'columns':list(rows[0])})
classes = tables['CLASS_SUMMARY.tsv']
if len({r['#class'] for r in classes}) != len(classes):
    raise ValueError('Duplicate class')
priced = [r for r in classes if int(r['n_priced']) > 0]
for row in priced:
    if not Decimal(row['bestA']) >= Decimal(row['meanA']) >= Decimal(row['worstA']):
        raise ValueError('Rounded summary order disagrees')
tails = {r['#sig']:r for r in tables['TAILS_B.tsv']}
stageb_matches = 0
for row in classes:
    if row['stageB(sig)'] == '-' or row['stageB(sig)'].startswith('impossible'):
        continue
    for item in row['stageB(sig)'].split(';'):
        name,mean = item.split()
        if name not in tails or Decimal(mean) != Decimal(tails[name]['mean_lin']):
            raise ValueError('Stage-B summary does not match tail table')
        stageb_matches += 1
results = {}
for name in ('RESULTS.tsv','RESULTS2.tsv'):
    rows = tables[name]
    ids = Counter(r['#job'] for r in rows)
    results[name] = {'rows':len(rows),'verdicts':dict(Counter(r['verdict'] for r in rows)),
                     'distinct_job_numbers':len(ids),'reused_job_numbers':sum(n>1 for n in ids.values()),
                     'distinct_nonempty_result_labels':len({r['result'] for r in rows if r['result'] != '-'}),
                     'indep_labels':dict(Counter(r['indep'] for r in rows))}
report = {'passed':True,'sources':sources,
          'classes':{'rows':len(classes),'priced_classes':len(priced),
                     'sum_n_priced':sum(int(r['n_priced']) for r in classes),
                     'rule_good_labels':dict(Counter(r['rule_good'] for r in classes)),
                     'impossible_labels':sum(r['stageB(sig)'].startswith('impossible') for r in classes)},
          'results':results,'stage_b_rows':len(tails),'stage_b_summary_entries_matched':stageb_matches,
          'scope':'Exact saved-table parsing, internal rounded-value consistency and identities only. Reported INDEP_VERIFIED is a historical verifier label, not statistical independence. UNSAT/impossible labels are not replayed proof certificates. Tail estimates and confidence labels are not exact success laws.'}
print(json.dumps(report,indent=2))
