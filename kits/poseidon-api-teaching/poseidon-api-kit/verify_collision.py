"""Independent check of collision lines printed by lean_attack (reads log files given on the command line).
Uses (1) poseidon_ref.hash_reduced (big-int reference, 11/11 public vectors) and (2) the organizer's verifier.poseidon.digest
from the read-only clone (messages: nk, rho as 32-byte little-endian each)."""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import poseidon_ref as ref
CLONE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'pareto_clone'))
sys.path.insert(0, CLONE)
try:
    from verifier.hash_functions import digest as org_digest
except Exception as e:  # organizer module optional
    org_digest = None; print('organizer verifier not importable:', e)
R = int(os.environ.get('R', '1'))
def parse(path):
    vals = {}
    for line in open(path):
        m = re.match(r'COLLISION (\S+)\s+0x([0-9a-f]{64})', line)
        if m: vals[m.group(1)] = int(m.group(2), 16)
    return vals
ok_all = True
for path in sys.argv[1:]:
    v = parse(path)
    if 'digest' not in v: continue
    nk1, rho1, nk2, rho2, dg = v['nk1'], v['rho1'], v['nk2'], v['rho2'], v['digest']
    d1 = ref.hash_reduced(nk1, rho1, R); d2 = ref.hash_reduced(nk2, rho2, R)
    ok = d1 == d2 == dg and (nk1, rho1) != (nk2, rho2) and all(0 <= x < ref.P for x in (nk1, rho1, nk2, rho2))
    org = None
    if org_digest:
        ma = nk1.to_bytes(32, 'little') + rho1.to_bytes(32, 'little'); mb = nk2.to_bytes(32, 'little') + rho2.to_bytes(32, 'little')
        da = org_digest(ma, 'poseidon-orchard', R); db = org_digest(mb, 'poseidon-orchard', R)
        org = (da == db and ma != mb and int.from_bytes(da, 'little') == dg)
        ok = ok and org
    print(path, 'collision verified' if ok else 'FAILED', 'reference ok' if d1 == d2 == dg else 'ref mismatch', 'organizer ok' if org else org)
    ok_all &= ok
sys.exit(0 if ok_all else 1)
