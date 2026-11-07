"""Recalculate a pinned numeric projection, not the underlying experiment."""
import csv
import hashlib
import io
import json
import math
from pathlib import Path

if not __debug__:
    raise SystemExit('Run without -O')
HERE = Path(__file__).resolve().parent
raw = (HERE / 'tail-observations.json').read_bytes()
assert hashlib.sha256(raw).hexdigest() == 'dcdf20639ca7f91ce237d77ffbe9ba7994aa6babdbc880af4f8adbb0d2985d3a'
data = json.loads(raw)
table = (HERE / 'research/game/climber/guided/pairfactory/TAILS_B.tsv').read_bytes()
assert hashlib.sha256(table).hexdigest() == data['summary_source_sha256']
rows = list(csv.DictReader(io.StringIO(table.decode()), delimiter='\t'))
assert len(rows) == len(data['groups']) == 7
seen_sources = set()
results = []
for group, row in zip(data['groups'], rows):
    assert group['signature'] == row['#sig']
    seeds = group['seeds']
    assert [o['seed_file_index'] for o in seeds] == list(range(1, 15))
    q = []
    hits_total = 0
    for ob in seeds:
        assert ob['source'] not in seen_sources
        seen_sources.add(ob['source'])
        assert len(ob['source_sha256']) == 64
        assert ob['kat'] == 1 and ob['mask_viol'] == 0
        assert ob['message_fields_all_null']
        assert ob['source_trial_records'] == ob['unused_trial_records'] + 21
        chains = ob['chains']
        assert len(chains) == 20
        for chain in chains:
            assert all(type(v) is int and v >= 0 for v in chain.values())
            assert chain['n'] == 80 * 2048
            assert chain['hits'] == chain['verified'] == sum(chain[k] for k in ('c00', 'c01', 'c10', 'c11'))
        hits = sum(c['hits'] for c in chains)
        hits_total += hits
        assert hits == ob['recorded_hits']
        value = 2.0 ** ob['log2_carrier'] * hits / sum(c['n'] for c in chains)
        assert math.isfinite(value) and value > 0 and value == ob['derived_q']
        q.append(value)
    mean = sum(q) / 14
    sd = math.sqrt(sum((value - mean) ** 2 for value in q) / 13)
    lower = mean - 3.852 * sd / math.sqrt(14)
    assert lower > 0
    mean_text, lower_text = f'{math.log2(mean):.4f}', f'{math.log2(lower):.4f}'
    assert mean_text == row['mean_lin'] == group['recalculated_mean_log2']
    assert lower_text == row['lcb999'] == group['recalculated_lcb999_log2']
    results.append({'signature': group['signature'], 'recorded_hits': hits_total,
                    'mean_log2': mean_text, 'lcb999_log2': lower_text})
assert len(seen_sources) == 98
print(json.dumps({'passed': True, 'seed_files': 98, 'chain_observations': 1960,
                  'groups': results, 'rounded_pairs_matched': 7,
                  'scope': 'Arithmetic replay of a hash-pinned numeric projection. Original full JSON files are not in this kit. Source hashes identify them; projection identity is verified, not derivable without those originals. No generator, collision witness, independence law, confidence coverage or attack probability certified.'}, indent=2))
