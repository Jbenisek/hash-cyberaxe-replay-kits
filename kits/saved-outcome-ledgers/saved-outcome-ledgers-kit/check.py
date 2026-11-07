"""Recount retained ledger bytes, never execute historical code or solver inputs."""
import csv
import hashlib
import io
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

PUB = Path(__file__).resolve().parents[1]
ROOT = PUB.parents[1]
SITE = PUB / 'site'
PINS = {
    'research/levers_1021/oracle_results.tsv': 'bc7666aae1d5cc6bbbdb236bd8e0e48cff8e3ec562b0223684984431bc658db1',
    'research/luna/L002/SPARSE42_RESULTS.tsv': '72bec6cc2004e27cff29b6cedc7f8e100fc19194064bda86515d5158eaac9c91',
    'research/luna/audit_packets/RESOLVE_1028.tsv': '2f864931bfd85c558309bcc2586484d201359fcaf4cfb304c9566ccce7ceb37c',
    'research/runs_1101/s42/HORIZON.tsv': '97c95887d154af936d3d0f5b768cfe8df81439b06d9f25beb37cac49e4ec6261',
    'research/runs_1101/s42/design/FIX_SCAN.tsv': '89f589ecd009dc656955d37cde7b8307d0b64fe0cefdc1fedb021b0169912128',
}

def require(condition, message):
    if not condition:
        raise ValueError(message)

def sparse_records(text):
    lines = text.splitlines()
    require(len(lines) % 2 == 0, 'Unpaired sparse-result line')
    rows = []
    for i in range(0, len(lines), 2):
        fields = lines[i].split('\t')
        require(len(fields) == 4, 'Expected four descriptor fields')
        require(lines[i + 1] == '\tUNSATISFIABLE', 'Unexpected saved result line')
        job, steps = map(int, fields[:2])
        words, kicks = ([int(v) for v in field.split(',')] for field in fields[2:])
        require(words == sorted(set(words)) and all(0 <= w < 16 for w in words), 'Invalid word support')
        require(kicks == sorted(set(kicks)) and all(0 <= k < steps for k in kicks), 'Invalid kick support')
        rows.append({'job': job, 'steps': steps, 'words': words, 'kicks': kicks,
                     'saved_verdict': 'UNSATISFIABLE'})
    require(len({r['job'] for r in rows}) == len(rows), 'Duplicate job')
    return rows

def resolve_records(text):
    lines = text.splitlines()
    require(lines[0] == 'page\tsource\tkind\tn\tverdict', 'Unexpected resolver header')
    require(lines[-1].startswith('# count:'), 'Missing resolver summary')
    rows = list(csv.DictReader(io.StringIO('\n'.join(lines[:-1])), delimiter='\t'))
    require(all(len(row) == 5 and None not in row and None not in row.values() for row in rows), 'Malformed resolver row')
    require(len({r['page'] for r in rows}) == len(rows), 'Duplicate page identity')
    require(len({r['source'] for r in rows}) == len(rows), 'Duplicate source path')
    require(all(r['verdict'] == 'VERIFIED' or r['verdict'].startswith('NOT_A_PAIR ') for r in rows), 'Unknown outcome')
    return rows, lines[-1]

def main(site=SITE, original_root=ROOT, report_path=PUB / 'qa/saved-outcome-ledgers-audit.json', print_summary=True):
    catalogue = {r['path']: r for r in json.loads((site / 'data/catalog.json').read_text(encoding='utf-8'))}
    sources, texts = [], {}
    for path, digest in PINS.items():
        record = catalogue[path]
        retained = site / record['href']
        raw = retained.read_bytes()
        require(hashlib.sha256(raw).hexdigest() == digest == record['sha256'], 'Retained source changed: ' + path)
        original = original_root / path if original_root is not None else None
        present = original.is_file() if original is not None else None
        if present:
            require(original.read_bytes() == raw, 'Original edition differs: ' + path)
        sources.append({'path': path, 'sha256': digest, 'bytes': len(raw),
                        'source_url': record['href'], 'original_present': present,
                        'tested_edition': 'retained publication bytes'})
        texts[Path(path).name] = raw.decode('utf-8')

    oracle = dict(line.split('\t') for line in texts['oracle_results.tsv'].splitlines())
    require(len(oracle) == 8, 'Oracle field count')
    require(oracle['R'] == '39' and oracle['best_mismatch'] == '781', 'Oracle values')
    require(all(oracle[k] == 'False' for k in ('weight0_inconsistent', 'fixed_point_from_weight0', 'fixed_point_from_any_weight1')), 'Oracle flags')

    sparse = sparse_records(texts['SPARSE42_RESULTS.tsv'])
    require([r['job'] for r in sparse] == [0, 1, 2, 3, 5, 4], 'Sparse job order')
    require(Counter(r['steps'] for r in sparse) == {42: 3, 43: 1, 44: 1, 45: 1}, 'Sparse step counts')
    resolver, trailer = resolve_records(texts['RESOLVE_1028.tsv'])
    verified = [r for r in resolver if r['verdict'] == 'VERIFIED']
    require(len(resolver) == 112 and len(verified) == 31, 'Resolver totals')
    require(Counter(r['n'] for r in verified) == {'38': 29, '39': 2}, 'Resolver step counts')
    require('rows=112 VERIFIED=31 FAILS=0 NOT_A_PAIR=81' in trailer, 'Trailer mismatch')

    horizons = []
    for line in texts['HORIZON.tsv'].splitlines():
        matched = re.fullmatch(r'S42_w([0-9-]+)_k([0-9-]+)\tR42\thorizon=(\d+)', line)
        require(matched is not None, 'Malformed horizon row')
        words, kicks, cutoff = matched.groups()
        horizons.append({'words': list(map(int, words.split('-'))),
                         'kicks': list(map(int, kicks.split('-'))), 'recorded_horizon': int(cutoff)})
    require(Counter(r['recorded_horizon'] for r in horizons) == {17: 2, 15: 3}, 'Horizon counts')
    fix = []
    for line in texts['FIX_SCAN.tsv'].splitlines():
        matched = re.fullmatch(r'fix_to (\d+)\tupdate all\.\.\. (failed|ok)!', line)
        require(matched is not None, 'Malformed fixed-prefix row')
        cutoff, status = matched.groups()
        fix.append({'fix_to': int(cutoff), 'propagation_marker': status})
    require([r['fix_to'] for r in fix] == list(range(31, 14, -2)), 'Tested cutoff grid')
    require([r['propagation_marker'] for r in fix] == ['failed'] * 6 + ['ok'] * 3, 'Propagation labels')

    # Parser controls: row counts must not silently absorb malformed records.
    rejected = 0
    controls = [(sparse_records, texts['SPARSE42_RESULTS.tsv'].splitlines()[0]),
                (sparse_records, texts['SPARSE42_RESULTS.tsv'].replace('\tUNSATISFIABLE', '\tSATISFIABLE', 1)),
                (resolve_records, texts['RESOLVE_1028.tsv'].replace('page\tsource', 'source\tpage', 1)),
                (resolve_records, '\n'.join(texts['RESOLVE_1028.tsv'].splitlines()[:-1]))]
    for parser, value in controls:
        try:
            parser(value)
        except ValueError:
            rejected += 1
    require(rejected == len(controls), 'Negative parser control accepted')
    report = {'passed': True, 'finished_at': datetime.now(timezone.utc).isoformat(),
              'sources': sources, 'oracle_recorded_fields': oracle,
              'sparse_records': sparse, 'resolver': {'rows': len(resolver), 'verified_labels': len(verified),
                'not_pair_labels': len(resolver) - len(verified), 'verified_steps': dict(Counter(r['n'] for r in verified))},
              'horizons': horizons, 'fixed_prefix_scan': fix, 'malformed_controls_rejected': rejected,
              'scope': 'Retained-byte identity and finite saved-ledger parsing only. No solver, generator, oracle or proof certificate executed. VERIFIED and UNSAT labels remain historical labels; existing independent witness replays are separate evidence. Propagation markers and recorded horizons are not complete solver decisions. Missing original oracle source remains explicitly unavailable.'}
    report['original_presence_checked'] = original_root is not None
    if report_path is not None:
        report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    if print_summary:
        print(json.dumps({'passed': True, 'sources': len(sources), 'originals_present': sum(bool(s['original_present']) for s in sources),
                      'sparse_cases': len(sparse), 'resolver_rows': len(resolver), 'horizon_rows': len(horizons),
                      'cutoff_rows': len(fix), 'malformed_controls_rejected': rejected}, indent=2))
    return report

if __name__ == '__main__':
    main()
