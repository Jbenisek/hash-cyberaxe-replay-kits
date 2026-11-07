"""Offline data-only recount; never import or execute a listed research path."""
import hashlib
import json
from pathlib import Path
import sys

if not __debug__:
    raise SystemExit('Run without -O')
HERE = Path(__file__).resolve().parent
manifest = json.loads((HERE / 'MANIFEST.json').read_text(encoding='utf-8'))
for row in manifest['files']:
    target = (HERE / row['path']).resolve()
    if not target.is_relative_to(HERE) or not target.is_file():
        raise SystemExit('Missing or invalid kit file')
    raw = target.read_bytes()
    if len(raw) != row['bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
        raise SystemExit('Changed kit file: ' + row['path'])
# Only the newly authored checker is imported, after its integrity check.
sys.path.insert(0, str(HERE))
import check
result = check.main(site=HERE, original_root=None, report_path=None, print_summary=False)
assert result['passed'] and result['original_presence_checked'] is False
assert len(result['sparse_records']) == 6 and result['resolver']['rows'] == 112
assert len(result['horizons']) == 5 and len(result['fixed_prefix_scan']) == 9
assert result['malformed_controls_rejected'] == 4
print(json.dumps(result, indent=2))
