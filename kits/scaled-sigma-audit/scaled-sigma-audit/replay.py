"""Finite AST-isolated audit of scaled sigma assumptions; no solver or file output by the encoder."""
import ast
import contextlib
import hashlib
import io
import json
import sys
import tempfile
from datetime import datetime,timezone
from pathlib import Path
from types import SimpleNamespace

PUB=Path(__file__).resolve().parent;ROOT=PUB
SOURCE='original/schedcnf3.py'
PIN='89083bdf81f33c236d94f4b253218789ac6a147cf700de7b643a8601b58b293f'


def reference(width,kind,x):
    mask=(1<<width)-1
    a,b,shift=(7,18,3) if kind==0 else (17,19,10)
    a,b,shift=(max(1,(n*width+16)//32) for n in (a,b,shift))
    def rotate(n):return ((x>>n)|(x<<(width-n)))&mask
    return rotate(a)^rotate(b)^(x>>shift)


def rank_and_kernel(columns):
    basis={};kernel=None
    for bit,value in enumerate(columns):
        combination=1<<bit
        while value:
            pivot=value.bit_length()-1
            if pivot not in basis:
                basis[pivot]=(value,combination);break
            old,old_combination=basis[pivot];value^=old;combination^=old_combination
        if not value and kernel is None:kernel=combination
    return len(basis),kernel


def propagate(clauses,initial):
    values=dict(initial)
    while True:
        changed=False
        for clause in clauses:
            if any(abs(x) in values and values[abs(x)]==(x>0) for x in clause):continue
            unset=[x for x in clause if abs(x) not in values]
            if not unset:return {'conflict':True,'all_clauses_satisfied':False}
            if len(unset)==1:
                x=unset[0];values[abs(x)]=x>0;changed=True
        if not changed:
            return {'conflict':False,'all_clauses_satisfied':all(any(values.get(abs(x))==(x>0) for x in c if abs(x) in values) for c in clauses)}


def main():
    controls=[([],{},False,True),([[]],{},True,False),([[1],[-1]],{},True,False),
              ([[1,2]],{1:False,2:True},False,True),([[1,2]],{},False,False),
              ([[1],[-1,2]],{},False,True)]
    for clauses,pins,conflict,satisfied in controls:
        if propagate(clauses,pins)!={'conflict':conflict,'all_clauses_satisfied':satisfied}:
            raise ValueError('Independent propagation control failed')
    raw=(ROOT/SOURCE).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=PIN:raise ValueError('Re-read changed encoder')
    if not __debug__:raise SystemExit('Run without -O')
    if sys.argv[1:] not in ([],['--emit-projection']):raise ValueError('Unknown arguments')
    manifest=json.loads((PUB/'manifest.json').read_text(encoding='utf-8'))
    if set(manifest['files'])!={'original/schedcnf3.py','replay.py','README.txt','records.json'}:raise ValueError('Wrong manifest inventory')
    if any(hashlib.sha256((PUB/name).read_bytes()).hexdigest()!=pin for name,pin in manifest['files'].items()):raise ValueError('Kit member changed')
    names={'sc','rotr','s0','s1','expand','CNF','build','add_lemmas','build_relax','main'}
    nodes=[node for node in ast.parse(raw.decode('utf-8')).body if isinstance(node,(ast.FunctionDef,ast.ClassDef)) and node.name in names]
    if {n.name for n in nodes}!=names:raise ValueError('AST interface changed')
    code=compile(ast.Module(body=nodes,type_ignores=[]),'<isolated-schedcnf3-definitions>','exec')
    ranks=[];fixtures=[];sigma_controls=0
    for width in range(1,33):
        env={'WB':width,'M':(1<<width)-1,'SHARE':True,'DSUB':False,'LSUB':False,'LALLOW':set(),
             'HW':None,'HWSET':None,'LEMMA':False,'LIN':False,'os':SimpleNamespace(environ={})}
        exec(code,env)
        for kind in (0,1):
            sigma=env['s0' if kind==0 else 's1']
            for value in [0,(1<<width)-1,*[1<<bit for bit in range(width)]]:
                if sigma(value)!=reference(width,kind,value):raise ValueError('Scalar/reference sigma mismatch')
                sigma_controls+=1
            rank,kernel=rank_and_kernel([reference(width,kind,1<<bit) for bit in range(width)])
            ranks.append({'width':width,'sigma':kind,'rank':rank,'injective':rank==width,
                          'nonzero_kernel':None if kernel is None else format(kernel,'08x')})
            if kernel is None:continue
            if not kernel or sigma(kernel)!=0:raise ValueError('Bad kernel certificate')
            # At R17, a differing W1 enters only sigma0; W14 only sigma1.
            word=1 if kind==0 else 14
            messages=[[0]*16,[0]*16];messages[1][word]=kernel
            expanded=[env['expand'](m,17) for m in messages]
            support=[i for i in range(17) if expanded[0][i]!=expanded[1][i]]
            if support!=[word] or expanded[0][16]!=expanded[1][16]:raise ValueError('One-step fixture invalid')
            outcomes=[]
            for lemma,linear in ((False,False),(True,False),(True,True)):
                env['LEMMA']=lemma;env['LIN']=linear
                cnf,words=env['build'](17,{word},set())
                pinned={}
                for side in (0,1):
                    for index in range(16):
                        for bit,variable in enumerate(words[side][index]):
                            value=bool((messages[side][index]>>bit)&1)
                            if variable in pinned and pinned[variable]!=value:raise ValueError('Shared-input pin mismatch')
                            pinned[variable]=value
                outcome=propagate(cnf.cl,pinned)
                if lemma and not outcome['conflict']:raise ValueError('Expected invalid-lemma rejection absent')
                if not lemma and (outcome['conflict'] or not outcome['all_clauses_satisfied']):raise ValueError('Base CNF fixture failed')
                outcomes.append({'LEMMA':lemma,'LIN':linear,**outcome})
            relax,_=env['build_relax'](17,{word},set())
            if [] not in relax.cl:raise ValueError('Expected lone-sigma shortcut absent')
            fixtures.append({'width':width,'sigma':kind,'different_message_word':word,'kernel':format(kernel,'08x'),
                'direct_schedule_support':support,'expanded_W16_equal':True,'full_encoder_outcomes':outcomes,
                'relax_contains_empty_clause_despite_real_schedule_pair':True})
    if any(r['rank']!=32 for r in ranks if r['width']==32):raise ValueError('Standard-width assumption failed')
    # Check only the small --check branch of the extracted main function.
    # No encoder module top level or CNF-writing branch is executed.
    with tempfile.TemporaryDirectory(prefix='hashsmash-schedcnf-contract-') as temporary:
        model=Path(temporary)/'incomplete.model';model.write_text('s SATISFIABLE\n',encoding='utf-8')
        env['sys']=SimpleNamespace(argv=[SOURCE,'--check','17','14','',str(model)])
        env['LEMMA']=False;env['LIN']=False
        output=io.StringIO()
        with contextlib.redirect_stdout(output):returned=env['main']()
        if returned is not None or '-> MISMATCH' not in output.getvalue():raise ValueError('Checker-return control changed')
        mismatch={'incomplete_model_deliberately_supplied':True,'required_support':[14],
                  'decoded_support':[],'printed_MISMATCH':True,'function_returned_normally':True,
                  'CLI_zero_status_on_normal_return':'DERIVED from the normal return of main, not a separate process measurement',
                  'stdout':output.getvalue(),
                  'scope':'Exit-status-only wrappers must not accept this checker as a success gate. This does not show that any historical wrapper did so.'}
    report={'passed':True,
        'source':SOURCE,'source_sha256':PIN,'scalar_sigma_controls':sigma_controls,'sigma_rank_table':ranks,
        'unit_propagation_controls':len(controls),
        'singular_width_sigma_cases':len(fixtures),'one_step_schedule_counterexamples':fixtures,
        'both_standard_32bit_sigmas_injective':True,'source_module_top_level_executed':False,
        'checker_mismatch_contract':mismatch,
        'external_solver_executed':False,'production_files_changed':False,
        'scope':'Exact GF(2) rank/kernel calculations and tiny one-step schedule/CNF controls. Proves reduced-width soundness failures in two pruning shortcuts for this source edition. Does not invalidate 32-bit sigma injectivity, certify the whole encoder, rerun any historical case or settle a 40-step family.'}
    if '--emit-projection' in sys.argv:
        print(json.dumps(report,indent=2));return
    if json.loads((PUB/'records.json').read_text(encoding='utf-8'))!=report:raise ValueError('Records differ from exact finite controls')
    print(json.dumps({'passed':True,'singular_width_sigma_cases':len(fixtures),
        'singular_widths_by_sigma':{str(kind):[r['width'] for r in ranks if r['sigma']==kind and not r['injective']] for kind in (0,1)},
        'both_standard_32bit_sigmas_injective':True,'source_sha256':PIN,
        'external_solver_executed':False,'production_files_changed':False},indent=2))


if __name__=='__main__':main()
