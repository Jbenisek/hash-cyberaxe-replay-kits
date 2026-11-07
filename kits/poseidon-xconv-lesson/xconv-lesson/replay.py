"""Finite operation-ledger replay and aliasing certificate; no large transform."""
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

if not __debug__:
    raise SystemExit('Run without -O: assertions are required')
HERE=Path(__file__).resolve().parent
manifest=json.loads((HERE/'MANIFEST.json').read_text())
for row in manifest['files']:
    p=(HERE/row['path']).resolve()
    assert p.is_relative_to(HERE)
    raw=p.read_bytes()
    assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'], 'Changed kit file'
import geo
import xconv
import xconv1

def compositions(n):
    if n==0:
        yield []
    for k in range(1,min(7,n)+1):
        for rest in compositions(n-k):
            yield [k]+rest

split_checks=0
for n in range(1,11):
    candidates=list(compositions(n))
    best,parts=geo.runsplit(12,n,8)
    assert sum(parts)==n and geo.cost(parts,12,8)==best
    assert min(geo.cost(s,12,8) for s in candidates)==best
    split_checks+=len(candidates)

impulses=0
for m in range(1,17):
    for L in (2*m,2*m+1,4*m):
        assert 2*m-1<L and 3*m-2-L<m
        for i in range(m):
            for j in range(1,2*m):
                t=i+j
                # On every requested output coordinate, an impulse contributes
                # identically in linear and cyclic convolution. Bilinearity
                # extends this to arbitrary coefficient arrays over any ring.
                if m<=t%L<2*m:
                    assert t%L==t
                if m<=t<2*m:
                    assert t%L==t
                impulses+=1

rows=[]
for name,K,L,margin,denominator,N0,C0,PFX0,memory,baseline in (
    ('r15',55512,1<<18,1<<20,531,43501369901167003059,27214930117798246188,3079944526115740280,54.76208,90.94721),
    ('r20',173472348,3<<28,1<<27,636,194960897130718429215869,108484490186864073879607,13312881573872943253352,66.37043,114.42508)):
    saved=json.loads((HERE/(name+'-ledger.json')).read_text())
    assert L>=4*K and 6*K-2-L<2*K
    phase=xconv1.phase if name=='r15' else xconv.phase
    amount,group=phase(L,2*K,1<<10,1<<31,margin=margin)
    assert amount==saved['X_NEW'] and group==saved['group']
    delta=31*(saved['X_OLD']-amount)
    assert N0-delta==saved['N1'] and C0-delta==saved['C1'] and PFX0-delta==saved['PFX1']
    log=math.log2(saved['N1']/denominator)
    assert abs(log-saved['t1'])<1e-12
    assert log<=saved['T1'] and saved['T1']-log<1e-5
    assert abs(saved['T1']+memory-20-float(saved['S1']))<1e-10
    rows.append({'profile':name,'K':K,'length':L,'last_output_index':4*K-1,
                 'largest_wrapped_index':6*K-2-L,'first_output_index':2*K,
                 'extension_ops':amount,'total_ops':saved['N1'],'ledger_time_log2':saved['T1'],
                 'ledger_score':saved['S1'],'recorded_baseline_score':baseline,
                 'arithmetic_scope':'Integer accounting identities exactly replayed; floating-point logs cross-checked. Inherited kernel charges, memory law and attack premises are not independently certified.'})
interface=subprocess.run([sys.executable,'-I','-B',str(HERE/'check_interfaces.py')],
                         cwd=HERE,capture_output=True,text=True,check=True,timeout=15)
interface=json.loads(interface.stdout)
assert interface['passed'] and len(interface['cases'])==6
assert interface['results']['boundary_parameter_triples']==360
print(json.dumps({'passed':True,'small_composition_candidates':split_checks,'impulse_cases':impulses,
                  'interface_cases':interface['cases'],'boundary_parameter_triples':360,
                  'rows':rows,'scope':'Fixed historical ledger replay, finite DP checks and alias-free output certificate. No NTT allocation, collision search, imported proof text or submission action.'},indent=2))
