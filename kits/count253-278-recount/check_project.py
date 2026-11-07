"""Check this project's exact publication files; optionally run its finite replay."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent

def replay():
    if sys.flags.optimize:
        raise SystemExit('Run without Python -O so scientific assertions remain enabled.')
    spec = json.loads((ROOT / 'PROJECT.json').read_text(encoding='utf8'))
    command = spec.get('replay_command')
    if not command:
        raise SystemExit('No automatic replay for this source collection. Read README.md.')
    command = [sys.executable if x == '{python}' else x for x in command]
    environment = os.environ.copy()
    environment.pop('PYTHONOPTIMIZE', None)
    environment['PYTHONDONTWRITEBYTECODE'] = '1'
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                            timeout=spec['timeout_seconds'], env=environment)
    if result.returncode:
        sys.stderr.write(result.stderr)
        sys.stderr.write(result.stdout)
        raise SystemExit(result.returncode)
    expected = spec.get('expected')
    if spec.get('text_output'):
        if spec['text_output'] not in result.stdout:
            raise SystemExit('Expected replay output missing')
    else:
        data = json.loads(result.stdout)
        if data.get('passed') is False:
            raise SystemExit('Replay reported passed=false')
        if isinstance(expected, str) and 'summary' in data and isinstance(data['summary'], str) and data['summary'] != expected:
            raise SystemExit('Replay summary mismatch')
        if isinstance(expected, str) and data.get('passed') is not True and data.get('summary') != expected:
            raise SystemExit('Replay did not explicitly pass or match its named summary')
        if isinstance(expected, dict):
            summary = data.get('summary', {})
            if any(summary.get(k) != v for k, v in expected.items()):
                raise SystemExit('Replay numerical summary mismatch')
        if expected is None and spec.get('require_passed') and data.get('passed') is not True:
            raise SystemExit('Replay did not explicitly pass')
    return result.stdout

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replay', action='store_true')
    args = parser.parse_args()
    manifest = json.loads((ROOT / 'FILES.sha256.json').read_text(encoding='utf8'))
    for name, row in manifest['files'].items():
        path = ROOT / name
        if not path.is_file() or path.stat().st_size != row['bytes']:
            raise SystemExit('Missing or changed file: ' + name)
        if hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:
            raise SystemExit('SHA-256 mismatch: ' + name)
    print(json.dumps({'integrity_passed': True, 'files': len(manifest['files'])}))
    if args.replay:
        print(replay())
