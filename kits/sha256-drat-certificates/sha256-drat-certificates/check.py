"""Check distributed identities, then optionally replay two bounded CNF proofs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

if not __debug__:
    raise SystemExit('Assertions are part of verification; run without -O')
BASE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--checker', help='Explicit path to a locally built drat-trim executable; no download or build is performed')
parser.add_argument('--rebuild', action='store_true', help='Re-emit both formulas from the bundled XML/encoder in a temporary directory; no solver')
args = parser.parse_args()
manifest = json.loads((BASE/'manifest.json').read_text(encoding='utf-8'))
def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()
for name, row in manifest['files'].items():
    assert Path(name).name == name and name not in ('.', '..')
    assert (BASE/name).stat().st_size == row['bytes'] and digest(BASE/name) == row['sha256'], name
report = {'identities_checked': len(manifest['files']), 'proof_replay_performed': False,
          'scope': 'Exact CNF/proof objects. No claim of full encoder correctness, novelty, a universal round barrier or an attack price.'}
if args.rebuild:
    controls = manifest['reconstruction']['cleared_optional_controls']
    env = {k: v for k, v in os.environ.items() if k not in controls}
    env.update(SIGNED='1', BITORDER='msb')
    report['formula_reconstruction'] = []
    with tempfile.TemporaryDirectory(prefix='sha256-formula-rebuild-') as directory:
        folder = Path(directory)
        for row in manifest['proofs']:
            result = subprocess.run([sys.executable, '-I', '-B', str(BASE/'encoder.py'), str(BASE/row['xml']),
                                     str(folder/'out.cnf'), str(folder/'out.map'), row['context']['chaining']],
                                    capture_output=True, text=True, env=env, timeout=30, check=True)
            assert (folder/'out.cnf').read_text(encoding='ascii') == (BASE/row['formula']).read_text(encoding='ascii')
            original_map = json.loads((BASE/row['map']).read_text(encoding='utf-8'))
            generated_map = json.loads((folder/'out.map').read_text(encoding='utf-8'))
            assert all(generated_map.get(k) == v for k, v in original_map.items())
            report['formula_reconstruction'].append({'id': row['id'], 'clauses_identical_up_to_newlines': True,
                                                     'retained_map_fields_identical': True})
if args.checker:
    checker = Path(args.checker).resolve(strict=True)
    assert checker.is_file()
    report['checker_sha256'] = digest(checker)
    report['matches_audited_binary'] = report['checker_sha256'] == manifest['audited_checker_sha256']
    def run(formula, proof):
        start = time.monotonic()
        result = subprocess.run([str(checker), str(formula), str(proof), '-t', '40'],
                                capture_output=True, text=True, timeout=55)
        output = result.stdout+'\n'+result.stderr
        verified = result.returncode == 0 and bool(re.search(r'^s VERIFIED\s*$', output, re.M))
        return {'verified': verified, 'exit_code': result.returncode, 'wall_seconds': time.monotonic()-start,
                'warning_lines': sum('WARNING:' in line for line in output.splitlines()),
                'checker_output_sha256': hashlib.sha256(output.encode()).hexdigest()}
    # All writes are isolated; the supplied research files are read-only.
    with tempfile.TemporaryDirectory(prefix='sha256-proof-replay-') as directory:
        folder = Path(directory)
        formula, proof = folder/'formula.cnf', folder/'proof.drat'
        formula.write_text('p cnf 2 4\n1 2 0\n1 -2 0\n-1 2 0\n-1 -2 0\n', encoding='ascii')
        proof.write_text('1 0\n0\n', encoding='ascii')
        positive = run(formula, proof)
        assert positive['verified'], positive
        formula.write_text('p cnf 1 1\n1 0\n', encoding='ascii')
        proof.write_text('0\n', encoding='ascii')
        negative = run(formula, proof)
        assert not negative['verified'], negative
        report['checker_controls'] = {'positive': positive, 'invalid_proof_rejected': True}
        report['proofs'] = []
        for row in manifest['proofs']:
            shutil.copyfile(BASE/row['formula'], formula)
            shutil.copyfile(BASE/row['proof'], proof)
            outcome = run(formula, proof)
            assert outcome['verified'], (row['id'], outcome)
            assert digest(formula) == manifest['files'][row['formula']]['sha256']
            assert digest(proof) == manifest['files'][row['proof']]['sha256']
            report['proofs'].append({'id': row['id'], **outcome})
    report['proof_replay_performed'] = True
else:
    report['next_step'] = 'Identity verification only. Supply --checker /absolute/path/to/drat-trim to replay proofs.'
print(json.dumps(report, indent=2))
