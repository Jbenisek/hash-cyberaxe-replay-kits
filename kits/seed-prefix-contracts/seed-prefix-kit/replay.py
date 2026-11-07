"""Finite seed-writer and prefix-verifier controls; no solver or network calls."""
import hashlib
import importlib.util
import json
import struct
import subprocess
import sys
from pathlib import Path

if not __debug__:
    raise SystemExit('Run without -O: these finite checks use assertions.')
ROOT = Path(__file__).resolve().parent
PINNED = {
    'pair2char.py': '88133bed956eaefad6f519b1e8afd9adb1faabff48ad84a0e93db64c1c0a3855',
    'nld_seed.py': '7a490fd7af31dddceff8c760e376eef6e56b50e11d4e2eda9f408ed40b19c56e',
    'mine_meter.py': '2c144dd2c3ee1e96720bb678f24ca52f62321fa5179ee1f1978fcbfcf385f036',
    'verify_full.py': '9ff45f77094f60f4def7a6b2e8a661abd4b3f852f7eb42331b45862bdd03e476',
    'verify_cv.py': '14c13e6fd869b2bbe6a11ce1bca888961da413064f3bcbd726ac9405c4e9b14a',
    'indep_sha256_check.py': 'b241e3c742b9f345fc7a049897a6dfd6342573a2d899fa05876134eb40b5fc61',
}
expected = {*PINNED, 'README.md', 'replay.py', 'check_value_seed_contract.py',
            'check_extended_prefix_verifiers.py','check_pair_characteristic_contract.py'}
manifest = json.loads((ROOT / 'MANIFEST.json').read_text(encoding='utf-8'))
assert len(manifest['files']) == len(expected)
assert {r['path'] for r in manifest['files']} == expected
assert {p.name for p in ROOT.iterdir() if p.is_file()} == expected | {'MANIFEST.json'}
for row in manifest['files']:
    raw = (ROOT / row['path']).read_bytes()
    assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256']
for name, digest in PINNED.items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name

spec = importlib.util.spec_from_file_location('seed_prefix_reference', ROOT / 'indep_sha256_check.py')
H = importlib.util.module_from_spec(spec)
spec.loader.exec_module(H)
for message in (b'', b'abc', bytes(range(32)), bytes(range(55))):
    block = message + b'\x80' + b'\x00' * (55 - len(message)) + struct.pack('>Q', len(message) * 8)
    actual = struct.pack('>8I', *H.compress(H.IV0, struct.unpack('>16I', block)))
    assert actual == hashlib.sha256(message).digest()

results = {}
for name in ('value_seed_contract', 'extended_prefix_verifiers','pair_characteristic_contract'):
    process = subprocess.run([sys.executable, '-I', '-B', str(ROOT / ('check_' + name + '.py'))],
                             cwd=ROOT, capture_output=True, text=True, check=True, timeout=15)
    result = json.loads(process.stdout)
    assert result['passed']
    results[name] = result['cases'] if name=='pair_characteristic_contract' else result['results']
assert results['value_seed_contract']['total_rows_checked'] == 288
assert len(results['extended_prefix_verifiers']) == 15
assert len(results['pair_characteristic_contract'])==8
print(json.dumps({'passed': True, 'hashlib_controls': 4, 'results': results,
                  'scope': 'Finite writer and prefix-predicate controls on disposable fixtures, including deliberate failures. No solver, feasibility, collision, attack-price or success-law certification.'}, indent=2))
