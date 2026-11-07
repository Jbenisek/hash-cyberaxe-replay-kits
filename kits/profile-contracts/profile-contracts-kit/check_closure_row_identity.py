"""Finite controls for the first possible difference below a common end state.

Uses a pinned independent scalar step inverse, not GPU code or a search run.
Rows here follow a zero-based step index: after step C, the register shifts
contain A_C..A_(C-3), E_C..E_(C-3).
"""
import hashlib,importlib.util,json,random,tempfile
from datetime import datetime,timezone
from pathlib import Path
if not __debug__:raise SystemExit('Run without -O')
ROOT=Path(__file__).resolve().parent
source=ROOT/'indep_sha256_check.py';raw=source.read_bytes()
sha=hashlib.sha256(raw).hexdigest()
assert sha=='b241e3c742b9f345fc7a049897a6dfd6342573a2d899fa05876134eb40b5fc61'
rng=random.Random(20261101);M=(1<<32)-1;checks=0
with tempfile.TemporaryDirectory(prefix='library-closure-row-') as tmp:
    target=Path(tmp)/'reference.py';target.write_bytes(raw)
    spec=importlib.util.spec_from_file_location('closure_reference',target)
    ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)
    for C in (26,27,28):
        for gap in range(5):
            j=C-gap
            for trial in range(8):
                terminal=tuple(rng.getrandbits(32) for _ in range(8))
                words=[rng.getrandbits(32) for _ in range(64)]
                delta=rng.randrange(1,1<<32)
                a=b=terminal
                # Equal suffix words preserve complete equality under inversion.
                for t in range(C,j,-1):
                    a=ref.back(a,t,words[t]);b=ref.back(b,t,words[t]);assert a==b
                before=a
                a=ref.back(a,j,words[j]);b=ref.back(b,j,(words[j]+delta)&M)
                assert a[:7]==b[:7]
                assert (b[7]-a[7])&M==(-delta)&M
                assert tuple(ref.step(a,j,words[j]))==tuple(before)
                assert tuple(ref.step(b,j,(words[j]+delta)&M))==tuple(before)
                checks+=1
report={'passed':True,'source_sha256':sha,'finished_at':datetime.now(timezone.utc).isoformat(),
        'cases':checks,'closures':[26,27,28],'equal_suffix_lengths':[0,1,2,3,4],
        'result':'A common terminal state fixes four A/E rows. The first unequal expanded word encountered backward at j introduces Delta E_(j-4)=-Delta W_j; it need not occur at C-4.',
        'scope':'Finite inverse-step controls accompanying an algebraic identity. Words are local step inputs; full message-schedule consistency, initial-state eligibility, GPU patch behavior and attack cost are not certified.'}
print(json.dumps(report,indent=2))
