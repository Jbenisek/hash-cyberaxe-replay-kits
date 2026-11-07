"""Offline replay of six saved files representing two chosen-CV identities."""
import hashlib
import importlib.util
import json
import re
import struct
from pathlib import Path

if not __debug__:
    raise SystemExit('Run without -O; this finite replay uses assertions.')
ROOT = Path(__file__).resolve().parent
manifest = json.loads((ROOT / 'MANIFEST.json').read_text(encoding='utf-8'))
names = [r['path'] for r in manifest['files']]
assert len(names) == len(set(names))
assert set(names) == {'replay.py', 'README.md', 'records.json', 'indep_sha256_check.py'} | {
    'pairs/' + name for name in (
        '37_d28_651af2505f0f_s40000.pair.txt', '37_d28_6da90fa8c6a7_s40000.pair.txt',
        '37_d28_f17a31bfeb3e_s40000.pair.txt', '38_d29_0035a4af6a77_s40000.pair.txt',
        '38_d29_50257c47044f_s40000.pair.txt', '38_d29_d1f818b92f02_s40000.pair.txt')}
for row in manifest['files']:
    raw = (ROOT / row['path']).read_bytes()
    assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256'], row['path']
spec = importlib.util.spec_from_file_location('finite_factory_reference', ROOT / 'indep_sha256_check.py')
H = importlib.util.module_from_spec(spec)
spec.loader.exec_module(H)
for msg in (b'', b'abc', bytes(range(32)), bytes(range(55))):
    block = msg + b'\x80' + b'\0' * (55 - len(msg)) + struct.pack('>Q', 8 * len(msg))
    assert struct.pack('>8I', *H.compress(H.IV0, struct.unpack('>16I', block))) == hashlib.sha256(msg).digest()

records = json.loads((ROOT / 'records.json').read_text(encoding='utf-8'))
assert len(records) == 6
assert {r['member'] for r in records} == {n for n in names if n.startswith('pairs/')}
identities = {}
results = []
for row in records:
    raw = (ROOT / row['member']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == row['sha256']
    text = raw.decode('utf-8-sig')
    sides = []
    for side in (1, 2):
        matches = re.findall(r'M' + str(side) + r': W=([^\r\n]+)\r?\n\s+chain=([^\r\n]+)\r?\n\s+out=([^\r\n]+)', text)
        assert len(matches) == 1
        fields = []
        for words, count in zip(matches[0], (16, 8, 8)):
            words = words.split()
            assert len(words) == count and all(re.fullmatch('[0-9a-f]{8}', x) for x in words)
            fields.append(tuple(int(x, 16) for x in words))
        sides.append(fields)
    (a, cv, printed_a), (b, cv_b, printed_b) = sides
    n = row['rounds']
    assert n in (37, 38) and int(Path(row['member']).name[:2]) == n
    assert a != b and cv == cv_b and list(cv) != H.IV0
    out_a, out_b = H.compress(cv, a, n), H.compress(cv, b, n)
    assert out_a == out_b
    assert ''.join(f'{x:08x}' for x in out_a) == row['digest']
    assert tuple((x - y) & H.M for x, y in zip(out_a, cv)) == printed_a == printed_b
    mutation = list(b)
    mutation[0] ^= 1
    assert H.compress(cv, mutation, n) != out_a
    assert H.compress(cv, a, n + 1) != H.compress(cv, b, n + 1)
    assert H.compress(cv, a, 64) != H.compress(cv, b, 64)
    identity = (n, cv, *sorted((a, b)))
    duplicate_of = identities.get(identity)
    assert duplicate_of == row['duplicate_of']
    identities.setdefault(identity, row['member'])
    results.append({'member': row['member'], 'rounds': n, 'duplicate_of': duplicate_of,
                    'feedforward_digest': row['digest'], 'standard_iv': False})
assert len(identities) == 2 and sum(r['duplicate_of'] is not None for r in results) == 4
print(json.dumps({'passed': True, 'records': results, 'distinct_identities': 2,
                  'duplicate_files': 4, 'hashlib_controls': 4, 'mutation_controls': 6,
                  'one_step_noncollisions': 6, 'full_64_step_noncollisions': 6,
                  'scope': 'Finite numerical replay of six saved files, two chosen-CV identities. No solver, launcher, attack rate, standard-IV collision or global novelty claim.'}, indent=2))
