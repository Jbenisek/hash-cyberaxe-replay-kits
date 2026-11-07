"""Replay a historical table's arithmetic, not program memory liveness."""
import hashlib
import json
import re
import sys
from pathlib import Path

SOURCE_SHA = '9aadb937a355c4836db1ef3ee267c5029f50e3875bd1b48863ac3a934bb41cf0'
SIZES = [8192, 7100, 146052, 833664, 8192, 1024, 192, 28704,
         1024, 4096, 128, 4096, 160]
SCOPE = ('Historical table arithmetic only. Not a liveness proof, compiler census, '
         'current filing price, success bound or collision replay.')


def projection(raw):
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA:
        raise ValueError('Historical excerpt changed; re-review it')
    text = raw.decode('utf-8')
    block = text.split('| item | bytes |', 1)[1].split('\n\n', 1)[0]
    rows = []
    total = None
    for line in block.splitlines():
        if not line.startswith('|') or '---' in line:
            continue
        cells = [s.strip() for s in line.strip('|').split('|')]
        if len(cells) != 2:
            raise ValueError('Unexpected memory-table row')
        if cells[0] == '**total**':
            match = re.fullmatch(r'\*\*([\d,]+) = 2\^19\.9918\*\* '
                                 r'\(2\^20 = 1,048,576; ([\d,]+) bytes spare\)', cells[1])
            if not match:
                raise ValueError('Unexpected declared total')
            total, spare = [int(x.replace(',', '')) for x in match.groups()]
        else:
            if not re.fullmatch(r'[\d,]+', cells[1]):
                raise ValueError('Non-numeric byte count')
            rows.append({'source_label': cells[0], 'declared_bytes': int(cells[1].replace(',', ''))})
    if [r['declared_bytes'] for r in rows] != SIZES or total is None:
        raise ValueError('Historical row inventory differs')
    computed = sum(r['declared_bytes'] for r in rows)
    if computed != total or (1 << 20) - computed != spare:
        raise ValueError('Historical total or headroom differs')
    return {
        'format': 'hashsmash-r39-memory-ledger-v1',
        'source_sha256': SOURCE_SHA, 'rows': rows,
        'declared_total_bytes': total, 'computed_total_bytes': computed,
        'ceiling_bytes': 1 << 20, 'headroom_bytes': spare,
        'instruction_bytes': (1192 + 1100 + 1765) * 36,
        'packed_record_bytes': 171008 * 39 // 8,
        'packed_record_bits_divisible_by_eight': (171008 * 39) % 8 == 0,
        'table_word_bytes': 26052 * 32,
        'queue_payload_bytes': 3584 * 8,
        'queue_declared_bytes': rows[7]['declared_bytes'],
        'queue_unexplained_allowance_bytes': rows[7]['declared_bytes'] - 3584 * 8,
        'reported_live_base_scalars': 3 + 4 + 10 + 7,
        'reported_deepest_scalars_with_links': 24 + 12 + 3 + 3,
        'reported_scalar_allowance': 48,
        'reported_register_total_with_allowance': 206 + 48,
        'program_liveness_verified': False, 'current_price_verified': False,
        'queue_allowance_origin_verified': False, 'scope': SCOPE,
    }


def main():
    if sys.flags.optimize:
        raise ValueError('Optimized interpreter unsupported')
    if sys.argv[1:] not in ([], ['--emit-projection']):
        raise ValueError('Only --emit-projection is supported; no launch operation')
    root = Path(__file__).resolve().parent
    manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
    expected = {'originals/section6.txt', 'records.json', 'README.txt', 'replay.py'}
    if set(manifest.get('files', {})) != expected:
        raise ValueError('Unexpected manifest inventory')
    for name, wanted in manifest['files'].items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != wanted:
            raise ValueError('File digest differs: ' + name)
    data = projection((root / 'originals/section6.txt').read_bytes())
    if sys.argv[1:] == ['--emit-projection']:
        print(json.dumps(data, indent=2))
        return
    if json.loads((root / 'records.json').read_text(encoding='utf-8')) != data:
        raise ValueError('Records differ from independently reconstructed arithmetic')
    print(json.dumps({'passed': True, 'table_rows': len(data['rows']),
                      'computed_total_bytes': data['computed_total_bytes'],
                      'headroom_bytes': data['headroom_bytes'],
                      'queue_unexplained_allowance_bytes': 32,
                      'program_liveness_verified': False, 'scope': SCOPE}))


if __name__ == '__main__':
    main()
