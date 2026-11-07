"""Reproduce a pinned generator example, not a SHA-256 collision or SAT result."""
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

PINS = {
    'originals/lawbase.py': 'a6e1cf0c62710affe52a7f46640e0892cfeac7b23b2a13f0a3824112a7425d2f',
    'originals/LIFT_s9.check': 'e299a74cc0629b5dbfd467b796a017e6491e532f15c597628b2fc7d096d155f6',
    'originals/example-R40-E29.xml': '7a61f9afcb5609c30bd5afb5b661c453fe3ec7dbc837cb577bdb032c053ccdcf',
    'golden-b32-records.json': 'be99263dfcb05708a7354c8e71aa24bf56f019a960474132714510d7ca48b734'
}
SCOPE = 'One pinned R40/E29 source-generator example against previously replayed schedule data. No solver, state completion, collision, independent-condition rank or attack price is certified.'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def projection(root):
    for name, pin in PINS.items():
        if sha((root / name).read_bytes()) != pin:
            raise ValueError('Original edition changed: ' + name)
    data = json.loads((root / 'golden-b32-records.json').read_text(encoding='utf-8'))
    reference = next(r for r in data['records'] if r['id'] == 'b32-lift-s9')
    word = lambda value: int(value, 16) if isinstance(value, str) else value
    incoming = {line.split()[0]: [int(v, 16) for v in line.split()[1:]]
                for line in (root / 'originals/LIFT_s9.check').read_text(encoding='utf-8').splitlines()
                if line.startswith(('M1 ', 'M2 '))}
    if any(incoming[k] != [word(v) for v in reference[k]] or len(incoming[k]) != 16 for k in ('M1', 'M2')):
        raise ValueError('Pinned input differs from the published golden pair')
    expected_w = [''.join('-' if a == b else 'u' if a == '1' else 'n'
                         for a, b in zip(format(word(left), '032b'), format(word(right), '032b')))
                  for left, right in zip(reference['expanded_M1'], reference['expanded_M2'])]
    if len(expected_w) != 40 or max(i for i, value in enumerate(expected_w) if value != '-' * 32) != 29:
        raise ValueError('Golden schedule shape differs')
    with tempfile.TemporaryDirectory(prefix='lawbase-replay-') as folder:
        work = Path(folder)
        destination = work / 'base.xml'
        command = [sys.executable, '-I', '-B', str((root / 'originals/lawbase.py').resolve()),
                   str((root / 'originals/LIFT_s9.check').resolve()), str(destination), '40', '29']
        run = subprocess.run(command, cwd=work, capture_output=True, timeout=10)
        if run.returncode or run.stdout or run.stderr:
            raise ValueError('Source-generator example failed')
        output = destination.read_bytes()
        if output.replace(b'\r\n', b'\n') != (root / 'originals/example-R40-E29.xml').read_bytes().replace(b'\r\n', b'\n'):
            raise ValueError('Generated XML differs beyond platform newline encoding')
        tree = ET.fromstring(output)
        if {e.attrib['name']: e.attrib['value'] for e in tree.findall('./options/option')} != {'f': 'sha2', 'n': '40', 'w': '32'}:
            raise ValueError('Generated options differ')
        rows = re.findall(r'(-?\d+)\s+A:\s+([?-]{32})\s+E:\s+([?-]{32})(?:\s+W:\s+([un-]{32}))?', tree.find('char').attrib['value'])
        if len(rows) != 44 or [int(r[0]) for r in rows] != list(range(-4, 40)):
            raise ValueError('Generated row identities differ')
        for index, a, e, w in rows:
            index = int(index)
            expected = ('?' * 32 if 0 <= index < 22 else '-' * 32,
                        '?' * 32 if 0 <= index < 26 else '-' * 32,
                        expected_w[index] if index >= 0 else '')
            if (a, e, w) != expected:
                raise ValueError('Generated relation differs from the golden example')
        mismatch = subprocess.run(command[:-1] + ['28'], cwd=work, capture_output=True, timeout=10)
        if mismatch.returncode or mismatch.stdout or mismatch.stderr:
            raise ValueError('Observed caller-validation behavior changed')
    return {'passed': True, 'source_sha256': PINS['originals/lawbase.py'],
            'source_generator_invocations': 2, 'example_R': 40, 'example_E': 29,
            'state_rows': 44, 'negative_index_rows': 4, 'signed_schedule_words_checked': 40,
            'A_free_rows': [0, 21], 'E_free_rows': [0, 25], 'A_equal_from': 22, 'E_equal_from': 26,
            'last_schedule_difference_row': 29, 'mismatched_E_argument_also_accepted': True,
            'explicit_complete_message_or_IV_value_assignments_emitted': False,
            'solver_runs': 0, 'collision_checks': 0, 'independent_condition_rank_proved': False,
            'normalized_example_xml_sha256': sha(output.replace(b'\r\n', b'\n')), 'scope': SCOPE}


def main():
    if sys.flags.optimize:
        raise ValueError('Optimized interpreter unsupported')
    if sys.argv[1:] not in ([], ['--emit-projection']):
        raise ValueError('Only --emit-projection is supported; no solver or campaign launch')
    root = Path(__file__).resolve().parent
    manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
    wanted = set(PINS) | {'replay.py', 'README.txt', 'records.json'}
    if set(manifest['files']) != wanted:
        raise ValueError('Unexpected kit inventory')
    for name, pin in manifest['files'].items():
        if sha((root / name).read_bytes()) != pin:
            raise ValueError('Manifest digest differs: ' + name)
    result = projection(root)
    if sys.argv[1:] == ['--emit-projection']:
        print(json.dumps(result, indent=2))
        return
    if result != json.loads((root / 'records.json').read_text(encoding='utf-8')):
        raise ValueError('Recorded contract differs from the observed generator example')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
