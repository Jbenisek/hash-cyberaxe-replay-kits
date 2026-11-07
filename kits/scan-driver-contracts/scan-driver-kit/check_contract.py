"""Bounded driver control-flow fixtures. No encoder, solver or research job runs."""
import ast
from collections import deque
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace

if not __debug__:raise SystemExit('Run without -O')
PUB=Path(__file__).resolve().parents[1]
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'scan_driver.py'
PIN='67ec37d0470e8677bf54f4addaefe4e2dd2720a55a43d780946b4e8e8db6f9fa'
raw=SOURCE.read_bytes()
assert hashlib.sha256(raw).hexdigest()==PIN
tree=ast.parse(raw.decode('utf-8'))
names={'arg','neighbours','build_queries','fmt','main'}
functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
assert {n.name for n in functions}==names
code=compile(ast.Module(body=functions,type_ignores=[]),'pinned-scan-driver-functions','exec')
cases=[]

def environment(argv=()):
    def fail(code=0):raise SystemExit(code)
    env={'sys':SimpleNamespace(argv=['scan_driver.py',*argv],exit=fail)}
    exec(code,env)
    return env

def target(name='x',R=19,words=(0,),kicks=(16,)):
    return {'name':name,'R':R,'words':list(words),'kicks':list(kicks)}

normal=environment()
q=normal['build_queries']([target(R=44)])
assert {r[2] for r in q}=={44,45}
cases.append({'name':'round-cap-is-45-not-header-41','passed':True})
q=normal['build_queries']([target(R=46)])
assert {r[2] for r in q}=={45,46}
cases.append({'name':'above-cap-also-generates-lower-round','passed':True})
q=normal['build_queries']([target(kicks=(18,))])
assert next(r for r in q if r[2]==19 and r[0]==0)[4]==frozenset()
q=environment(['--self-only'])['build_queries']([target(kicks=(18,))])
assert q[0][4]==frozenset({18})
cases.append({'name':'final-kick-normal-versus-self-only','passed':True})
q=normal['build_queries']([target('first',kicks=(16,)),target('second',kicks=(17,))])
selected=[r for r in q if r[2]==19 and r[4]==frozenset({17})]
assert len(selected)==1 and selected[0][0]==1 and selected[0][-1]=='first'
cases.append({'name':'earlier-neighbour-can-suppress-later-exact-target','passed':True})
try:normal['build_queries']([target(words=())])
except ValueError:pass
else:raise AssertionError('Empty support accepted')
cases.append({'name':'empty-message-support-fails-before-encoding','passed':True})

def exercise(targets,replies,*,existing=None,base=None,ladder=(1,3),extra=()):
    """Run the exact extracted main with confined I/O and explicit stand-ins."""
    with tempfile.TemporaryDirectory(prefix='library-scan-driver-') as folder:
        work=Path(folder).resolve()
        (work/'targets.json').write_text(json.dumps(targets),encoding='utf-8')
        if existing is not None:(work/'census_9.tsv').write_text(existing,encoding='utf-8')
        if base is not None:(work/'base_R19.cnf').write_text(base,encoding='utf-8')
        def confined(path):
            path=Path(path)
            if path.name.startswith('scan40_q_'):
                path=work/path.name
            path=path.resolve()
            assert path==work or work in path.parents,('I/O outside fixture',str(path))
            return path
        def opened(path,*args,**kwargs):return open(confined(path),*args,**kwargs)
        def replace(src,dst):confined(src).replace(confined(dst))
        def remove(path):confined(path).unlink()
        def build_base(R):
            build_base.evars=[[2+t] for t in range(R)]
            return [[1]],{t:R+2+t for t in range(16)},R+18
        runs=[]
        remaining=list(replies)
        class TimeoutExpired(Exception):pass
        def run(cmd,**kwargs):
            text=confined(cmd[-1]).read_text(encoding='utf-8')
            runs.append({'command':cmd,'cnf':text,'timeout':kwargs.get('timeout')})
            assert remaining,'Unexpected solver request'
            reply=remaining.pop(0)
            if reply=='timeout':raise TimeoutExpired()
            label,rc=reply
            output=('c conflicts: 50\nc decisions: 70\nc propagations: 90\nc restarts: 2\ns '+label+'\n').encode()
            return SimpleNamespace(stdout=output,returncode=rc)
        tick=[0]
        def now():tick[0]+=0.01;return tick[0]
        env=environment(['--self-only','--targets',str(work/'targets.json'),*extra])
        env.update(HERE=str(work),LADDER=list(ladder),json=json,deque=deque,open=opened,
            os=SimpleNamespace(path=SimpleNamespace(join=lambda *p:str(Path(*p)),
                exists=lambda p:confined(p).exists(),isdir=lambda p:False),
                getpid=lambda:123,replace=replace,remove=remove),
            glob=SimpleNamespace(glob=lambda pattern:[str(p) for p in work.glob('census_*.tsv')]),
            time=SimpleNamespace(time=now,strftime=lambda fmt:'fixture-time'),
            sched_scan=SimpleNamespace(build_base=build_base),
            subprocess=SimpleNamespace(run=run,PIPE=-1,STDOUT=-2,TimeoutExpired=TimeoutExpired))
        exitcode=0
        # Keep the fixture driver's progress out of the report's JSON stdout.
        env['print']=lambda *a,**kw:None
        try:env['main']()
        except SystemExit as exc:exitcode=exc.code
        ledger=(work/'census_0.tsv').read_text(encoding='utf-8')
        assert not remaining,remaining
        return ledger,runs,exitcode

cal=('UNSATISFIABLE',20)
ledger,runs,rc=exercise([target()],[cal,('SATISFIABLE',1)])
assert rc==0 and '\tSAT\t0\t' in ledger and len(runs)==2
clauses=runs[1]['cnf'].splitlines()[1:]
assert '21 0' in clauses  # required message word 0 (19+2)
assert '-3 0' in clauses and '-18 0' not in clauses # silence row 1, allow row 16
cases.append({'name':'units-and-label-parsing-do-not-check-solver-exit-code','passed':True})
ledger,runs,rc=exercise([target()],[('SATISFIABLE',10)])
assert rc==2 and '# calib FAILED' in ledger
cases.append({'name':'positive-calibration-result-aborts','passed':True})
ledger,runs,rc=exercise([target()],[cal,'timeout','timeout'])
assert rc==0 and '#u\t' in ledger and '\tUNDECIDED\t1\t' in ledger
assert len(runs)==3
cases.append({'name':'timeouts-climb-ladder-and-stay-undecided','passed':True})
ledger,runs,rc=exercise([target()],[cal],existing='19\t0\t16\tPENDING\t0\t1\told\n')
assert len(runs)==1 and 'mine_left=0' in ledger
cases.append({'name':'resume-skips-any-non-undecided-label','passed':True})
ledger,runs,rc=exercise([target('small'),target('large',kicks=(16,17))],[cal,('SATISFIABLE',10)])
rows=[r.split('\t') for r in ledger.splitlines() if r and not r.startswith('#')]
assert len(runs)==2 and rows[1][3]=='SAT' and rows[1][6].startswith('pruned(')
assert rows[0][8:]==rows[1][8:]  # LAST metrics are copied, not a second solve.
cases.append({'name':'sat-superset-pruning-reuses-last-solver-statistics','passed':True})
ledger,runs,rc=exercise([target('large',kicks=(16,17)),target('small')],[cal,('UNSATISFIABLE',20)])
assert len(runs)==2 and '\tUNSAT\t0\t0.0\tpruned(' in ledger
cases.append({'name':'unsat-subset-pruning','passed':True})
ledger,runs,rc=exercise([target()],[cal,('SATISFIABLE',10)],base='p cnf 3 1\n1 0\n')
assert runs[1]['cnf'].startswith('p cnf 3 ') and '21 0' in runs[1]['cnf']
cases.append({'name':'stale-base-can-be-combined-with-new-literal-map','passed':True})
report={'passed':True,'source_sha256':PIN,'finished_at':datetime.now(timezone.utc).isoformat(),'cases':cases,
        'source_functions_extracted':sorted(names),'actual_encoder_or_solver_executed':False,
        'scope':'Twelve bounded fixtures of pinned query generation and driver control flow. Encoder, SAT/UNSAT truth, operating-system process management and historical campaign coverage are not certified.'}
# Results returned through stdout only.
print(json.dumps(report,indent=2))
