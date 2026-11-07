"""Reconcile saved table/log receipts. Never invoke a solver or check a proof."""
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

PINS = {
    'originals/RESULTS.tsv': '9c0cddd3bfb7fb389a7575cc990c3232f2ab5567d27d4848f6b61d03b19102ee',
    'originals/p5.out': 'fe28418aee02b1045ad2d67528d1d71186a755d170ff51ed7112c835dfcfd4e8',
    'originals/p7.out': '1b56b6eafcc058c89901771523bebcfb766338b5e167474f0df1191ea329fa90'}
P5 = 'UP39_d1f818b92f02_p5'
P7 = 'UP39_d1f818b92f02_p7'
ORIGINAL_BASE = 'research/game/climber/guided/d6full_head/sat5/up39/'
ORIGINAL_NAMES = {'originals/RESULTS.tsv': 'RESULTS.tsv',
                  'originals/p5.out': P5 + '_kissat.out', 'originals/p7.out': P7 + '_kissat.out'}
SCOPE = ('Recorded job outcomes and two restored table rows, not fresh SAT/UNSAT '
         'certification, collision verification, a condition minimum or attack pricing.')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def one(lines, pattern):
    found = [{'line': i + 1, 'text': line} for i, line in enumerate(lines) if re.search(pattern, line)]
    if len(found) != 1:
        raise ValueError('Unique log receipt required: ' + pattern)
    return found[0]


def projection(root):
    raw = {name: (root / name).read_bytes() for name in PINS}
    if any(sha(raw[name]) != pin for name, pin in PINS.items()):
        raise ValueError('Original source edition changed')
    ledger = raw['originals/RESULTS.tsv'].decode('utf-8').splitlines()
    logs = {tag: raw['originals/' + tag + '.out'].decode('utf-8').splitlines() for tag in ('p5', 'p7')}
    records, corrections = [], []
    for number, line in enumerate(ledger, 1):
        if line.startswith('CORRECTION '):
            corrections.append({'line': number, 'text': line})
            continue
        fields = line.split('\t')
        if len(fields) != 5:
            raise ValueError('Unexpected ledger row shape')
        job, status, duration, conflicts, rc = fields
        if not re.fullmatch(r'(?:UP39_d1f818b92f02_p\d+|control_R38_p8)', job) or status not in ('SAT', 'UNSAT', 'UNKNOWN', ''):
            raise ValueError('Unexpected recorded job or status')
        if not re.fullmatch(r'(?:\d+s|s)', duration) or not re.fullmatch(r'conflicts=(?:\d+|NA)', conflicts) or not re.fullmatch(r'rc=\d*', rc):
            raise ValueError('Unexpected ledger quantities')
        records.append({'id': job, 'source_line': number, 'original_fields': fields,
                        'job_group_from_name': 'UP39' if job.startswith('UP39') else 'control_R38',
                        'status_as_recorded': status or None, 'reported_status': status or None,
                        'reported_time_label': duration, 'time_basis': 'Unspecified seconds in the original ledger',
                        'reported_conflicts': int(conflicts[10:]) if conflicts[10:] != 'NA' else None,
                        'reported_exit_code': int(rc[3:]) if rc[3:] else None,
                        'restoration': 'As recorded', 'correction': None, 'log_receipts': [],
                        'evidence_limit': 'Source-reported label only; original formula and proof/model are not revalidated.'})
    if len(records) != 13 or len({r['id'] for r in records}) != 13 or len(corrections) != 2:
        raise ValueError('Expected thirteen job records and two corrections')
    if {r['id'] for r in records if r['reported_status'] is None} != {P5, P7}:
        raise ValueError('Blank-row inventory changed')
    by_id = {r['id']: r for r in records}
    c5, c7 = corrections
    m5 = re.search(r'UNSAT, (\d+) conflicts, (\d+)s process-time[.]$', c5['text'])
    m7 = re.search(r'UNKNOWN at the (\d+)s cap, (\d+) conflicts at ([\d.]+)s[.]$', c7['text'])
    if P5 not in c5['text'] or P7 not in c7['text'] or not m5 or not m7:
        raise ValueError('Explicit correction format changed')
    conflict5, rounded5 = map(int, m5.groups())
    cap7, conflict7, progress7 = int(m7[1]), int(m7[2]), float(m7[3])
    receipts5 = [one(logs['p5'], pattern) for pattern in (
        r'^s UNSATISFIABLE$', r'^c conflicts:\s+' + str(conflict5) + r'\s',
        r'^c process-time:', r'^c exit 20$')]
    process5 = re.search(r'([\d.]+) seconds$', receipts5[2]['text'])
    if not process5 or int(float(process5[1])) != rounded5:
        raise ValueError('Rounded process time does not match the correction')
    if any(line.startswith('s ') for line in logs['p7']):
        raise ValueError('The retained p7 log contains a terminal solver response')
    receipts7 = [one(logs['p7'], pattern) for pattern in (
        r'^c - ' + re.escape(m7[3]) + r'\s.*\s' + str(conflict7) + r'\s',
        r'^c caught signal 15 [(]SIGTERM[)]$', r'^c process-time:',
        r'^c raising signal 15 [(]SIGTERM[)]$')]
    process7 = re.search(r'([\d.]+) seconds$', receipts7[2]['text'])
    if not process7:
        raise ValueError('Missing final process-time field')
    by_id[P5].update(reported_status='UNSAT', reported_conflicts=conflict5, reported_exit_code=20,
                     reported_time_label=str(rounded5) + 's process-time (correction)',
                     time_basis='Rounded process time from correction; log reports ' + process5[1] + ' seconds',
                     restoration='Restored from explicit correction and saved log', correction=c5,
                     log_receipts=receipts5, logged_final_process_seconds=float(process5[1]))
    by_id[P7].update(reported_status='UNKNOWN', reported_conflicts=conflict7, reported_exit_code=None,
                     reported_time_label=str(cap7) + 's cap (correction)',
                     time_basis='Reported cap, not an elapsed time; final log process time is ' + process7[1] + ' seconds',
                     restoration='Restored from explicit correction and saved log', correction=c7,
                     log_receipts=receipts7, reported_cap_seconds=cap7,
                     progress_seconds_as_printed=progress7, logged_final_process_seconds=float(process7[1]),
                     terminal_signal_as_printed='SIGTERM', terminal_solver_response_present=False)
    counts = Counter(r['reported_status'] for r in records)
    if counts != {'SAT': 1, 'UNSAT': 3, 'UNKNOWN': 9}:
        raise ValueError('Corrected label census differs')
    return {'format': 'hashsmash-up39-corrected-ledger-v1', 'records': records,
            'count': 13, 'reported_counts': {'SAT': counts['SAT'], 'UNSAT': counts['UNSAT'], 'UNKNOWN': counts['UNKNOWN']},
            'restored_rows': 2, 'full_solver_logs_included': 2,
            'source_editions': [{'file': name, 'original_path': ORIGINAL_BASE + ORIGINAL_NAMES[name],
                                 'sha256': PINS[name], 'bytes': len(data)} for name, data in raw.items()],
            'formula_log_bindings_verified': False, 'validated_collision_pairs': 0,
            'certificate_replays': 0, 'fresh_solver_runs': 0, 'minimum_condition_bound_proved': False,
            'scope': SCOPE}


def main():
    if sys.flags.optimize:
        raise ValueError('Optimized interpreter unsupported')
    if sys.argv[1:] not in ([], ['--emit-projection']):
        raise ValueError('Only --emit-projection is supported; no solver launch')
    root = Path(__file__).resolve().parent
    manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
    wanted = set(PINS) | {'replay.py', 'records.json', 'README.txt'}
    if set(manifest['files']) != wanted:
        raise ValueError('Unexpected manifest inventory')
    for name, pin in manifest['files'].items():
        if sha((root / name).read_bytes()) != pin:
            raise ValueError('File digest differs: ' + name)
    data = projection(root)
    if sys.argv[1:] == ['--emit-projection']:
        print(json.dumps(data, indent=2))
        return
    saved = json.loads((root / 'records.json').read_text(encoding='utf-8'))
    if json.dumps(saved, sort_keys=True) != json.dumps(data, sort_keys=True):
        raise ValueError('Records differ from independently reconstructed receipts')
    print(json.dumps({'passed': True, 'records': 13, 'restored_rows': 2,
                      'reported_counts': data['reported_counts'], 'full_logs_checked': 2,
                      'certificate_replays': 0, 'formula_log_bindings_verified': False, 'scope': SCOPE}))


if __name__ == '__main__':
    main()
