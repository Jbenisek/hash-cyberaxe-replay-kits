"""Run the reviewed family writer only in a disposable synthetic library."""
import csv,hashlib,json,subprocess,sys,tempfile
from datetime import datetime,timezone
from pathlib import Path
if not __debug__:raise SystemExit('Run without -O')
ROOT=Path(__file__).resolve().parent
source=ROOT/'trail_families.py';raw=source.read_bytes()
source_sha=hashlib.sha256(raw).hexdigest()
assert source_sha=='f495094752339b75ee721fca0d68a902acc2ab8abb7fa23841c6a6e20706b934'
cases=[]
with tempfile.TemporaryDirectory(prefix='library-trail-family-') as tmp:
    root=Path(tmp);script=root/'research/tools/profile/trail_families.py';script.parent.mkdir(parents=True);script.write_bytes(raw)
    library=root/'research/game/climber/guided/chars/library';library.mkdir(parents=True)
    gate=library/'IV_GATE.tsv'
    def characteristic(name,rows,steps=7,state='-'):
        text='<options><option name="n" value="'+str(steps)+'"/></options>\n'
        text+='\n'.join(str(i)+' A: '+state*32+' E: '+state*32+' W: '+mask for i,mask in rows)+'\n'
        (library/name).write_text(text,encoding='utf-8')
    characteristic('r39_a.xml',[(2,'u'+'-'*31)])
    characteristic('r39_b.xml',[(2,'n'+'-'*31)],steps=8,state='?')
    characteristic('r39_x.xml',[(2,'x'+'-'*31)])
    characteristic('r40_alias.xml',[(2,'u'+'-'*31)],steps=39)
    def run(lines,ok=True):
        gate.write_text(lines,encoding='utf-8')
        p=subprocess.run([sys.executable,'-I','-B',str(script)],cwd=root,capture_output=True,text=True,timeout=10)
        assert (p.returncode==0)==ok,p.stderr
        if ok:
            with (library/'FAMILIES.tsv').open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f,delimiter='\t'))
        return p.stderr
    result=run('r39_a\tSAT\t5.0 seconds\nr39_b\tSAT\t3.0 seconds\n')
    indexed={(r['steps'],r['W_diff_rows']):r for r in result}
    assert len(result)==3
    assert indexed[('r39','2')]['representative']=='r39_b' and indexed[('r39','2')]['members']=='2'
    assert indexed[('r39','')]['representative']=='r39_x'
    assert ('r40','2') in indexed
    cases.append({'case':'filename-not-content-step-key; signs-and-state-ignored; x-only-support-omitted','passed':True})
    result=run('r39_a\tSAT\t5\nr39_b\tSAT\t3\nr39_b\tUNSAT\t1\n')
    row=next(r for r in result if r['steps']=='r39' and r['W_diff_rows']=='2')
    assert row['representative']=='r39_a' and row['sat_at_row12']=='1'
    cases.append({'case':'last-duplicate-gate-row-replaces-earlier-SAT','passed':True})
    result=run('r39_a\tSAT\t5\nr39_b\tSAT\t1e-3\n')
    assert next(r for r in result if r['steps']=='r39' and r['W_diff_rows']=='2')['representative']=='r39_a'
    cases.append({'case':'scientific-notation-time-is-not-counted-as-numeric','passed':True})
    result=run('r39_a\tSAT\t3\nr39_b\tSAT\t3\n')
    assert next(r for r in result if r['steps']=='r39' and r['W_diff_rows']=='2')['representative']=='r39_a'
    cases.append({'case':'equal-SAT-times-use-lexical-member-tiebreak','passed':True})
    before=(library/'FAMILIES.tsv').read_bytes()
    assert 'ValueError' in run('r39_a\tSAT\t1.2.3\n',False)
    assert (library/'FAMILIES.tsv').read_bytes()==before
    cases.append({'case':'multiple-decimal-points-pass-prefilter-then-crash-float; old-output-retained','passed':True})
    assert 'IndexError' in run('r39_a\tSAT\t\n',False)
    cases.append({'case':'empty-third-gate-field-crashes-before-output','passed':True})
    characteristic('r39_reordered.xml',[(2,'u'+'-'*31),(1,'n'+'-'*31)])
    result=run('r39_a\tSAT\t5\n')
    assert next(r for r in result if r['representative']=='r39_reordered')['W_diff_rows']=='2,1'
    cases.append({'case':'source-row-order-preserved-in-signature-not-canonicalized','passed':True})
report={'passed':True,'source_sha256':source_sha,'finished_at':datetime.now(timezone.utc).isoformat(),
        'cases':cases,'scope':'Seven disposable writer fixtures. No full historical-library regeneration, solver verdict, equivalence or representative-transfer proof.'}
print(json.dumps(report,indent=2))
