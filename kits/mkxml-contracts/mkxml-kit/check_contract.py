"""Bounded copied-source XML generation; no nldtool, SAT solver or research writes."""
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

if not __debug__:
    raise SystemExit('Run without -O')
PUB = Path(__file__).resolve().parents[1]
REL = 'research/levers_1021/s256_r40_search/nldtool/mkxml.py'
SOURCE = Path(__file__).resolve().parent / 'mkxml.py'
PIN = '5bb0481f32e86ddc83e7b02624c0ff437e31dd4785d3233510b28cf931528b4b'
raw = SOURCE.read_bytes()
assert hashlib.sha256(raw).hexdigest() == PIN
FOUND = Path(__file__).resolve().parent / 'control.found.txt'
CONTROL = Path(__file__).resolve().parent / 'control.xml'
found_raw, control_raw = FOUND.read_bytes(), CONTROL.read_bytes()
assert hashlib.sha256(found_raw).hexdigest() == '18cf11691ee46513b857d1221676285c7b1c2b8775c758450b373e40d1660a15'
assert hashlib.sha256(control_raw).hexdigest() == '4f78d53cc1fe6cd9909e9aea753e2afda386bc51c2d2abd0f8959ac5b3bcb6b9'
cases = []
with tempfile.TemporaryDirectory(prefix='library-mkxml-contract-') as temp:
    work = Path(temp)
    script = work / 'mkxml.py'
    script.write_bytes(raw)
    def run(label, *args, create=True):
        out = work / label
        if create:
            out.mkdir()
        proc = subprocess.run([sys.executable, '-I', '-B', str(script), str(out), *args],
                              cwd=work, capture_output=True, text=True, timeout=10)
        return proc, out
    def parse(path):
        tree = ET.parse(path).getroot()
        options = {x.attrib['name']: x.attrib['value'] for x in tree.findall('options/option')}
        assert options['f'] == 'sha2' and options['w'] == '32'
        rows = {}
        for match in re.finditer(r'(-?\d+)\s+A:\s+([?xun-]+)\s+E:\s+([?xun-]+)(?:\s+W:\s+([?xun-]+))?', tree.find('char').attrib['value']):
            index = int(match[1])
            assert index not in rows
            rows[index] = {'A': match[2], 'E': match[3], 'W': match[4]}
        n = int(options['n'])
        assert set(rows) == set(range(-4, n))
        assert all(len(v) == 32 for row in rows.values() for v in row.values() if v is not None)
        assert all((rows[t]['W'] is None) == (t < 0) for t in rows)
        return rows, tree
    good, base = run('ordinary')
    assert good.returncode == 0, good.stderr
    files = sorted(base.glob('*.xml'))
    assert len(files) == 31, len(files)
    for path in files:
        parse(path)
    cases.append({'name': 'ordinary_generator', 'passed': True, 'files': 31, 'all_xml_parsed': True})
    control_path = base / 's224_r40_LLW_control.xml'
    # File bytes stay pinned; compare generated text across host newline styles.
    assert control_path.read_bytes().replace(b'\r\n', b'\n') == control_raw.replace(b'\r\n', b'\n')
    inputs, _ = parse(control_path)
    found = {}
    counts = dict(A=0, E=0, W=0)
    signed = dict(A=0, E=0, W=0)
    for line in found_raw.decode('utf-8').splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r'\s*(-?\d+)\s+A:\s+([01unx?-]+)\s+E:\s+([01unx?-]+)(?:\s+W:\s+([01unx?-]+))?\s*', line)
        assert match, line
        row = int(match[1]); assert row not in found
        found[row] = dict(zip(('A', 'E', 'W'), match.groups()[1:]))
        for word, mask in found[row].items():
            if mask is None:
                assert row < 0 and word == 'W'
                continue
            assert len(mask) == 32 and '?' not in mask and 'x' not in mask
            counts[word] += sum(c in '01un' for c in mask)
            signed[word] += sum(c in 'un' for c in mask)
    assert set(found) == set(range(-4, 40))
    assert counts == {'A': 60, 'E': 283, 'W': 37}
    assert signed == {'A': 59, 'E': 82, 'W': 26}
    # Abstract atoms suffice for inclusion, without choosing u/n side orientation.
    atoms = {'-': set('01'), '?': set('01un'), 'x': set('un'),
             '0': set('0'), '1': set('1'), 'u': set('u'), 'n': set('n')}
    def fits(result):
        return all(len(mask) == 32 and all(atoms[c] <= atoms[q] for c, q in zip(mask, inputs[row][word]))
                   for row, fields in result.items() for word, mask in fields.items() if mask is not None)
    assert fits(found)
    altered = {row: dict(fields) for row, fields in found.items()}
    altered[-4]['E'] = '-' * 32
    assert not fits(altered)
    altered[-4]['E'] = found[-4]['E'][:-1]
    assert not fits(altered)
    cases.append({'name': 'historical_control_recount_and_input_mask_inclusion', 'passed': True,
                  'rows': 44, 'word_masks': 128, 'single_bit_conditions': counts,
                  'signed_differences': signed, 'total_single_bit_conditions': 380,
                  'total_signed_differences': 167, 'question_marks': 0,
                  'input_mask_and_width_mutations_rejected': True,
                  'scope': 'Symbol recount and input-mask refinement only, not modular state feasibility, solver proof, a concrete pair or success probability.'})
    old, _ = parse(base / 's256_r43_release_T1314_pinned.xml')
    fix, _ = parse(base / 's256_r43_release_T1314_fix.xml')
    fix2, _ = parse(base / 's256_r43_release_T1314_fix2.xml')
    zero = {24, 26, 39, 40, 41, 42}
    assert all(old[t]['W'] == '-' * 32 for t in range(16, 43))
    assert all(fix[t]['W'] == ('-' * 32 if t in zero else '?' * 32) for t in range(16, 43))
    assert all(fix2[t]['W'] == fix[t]['W'] for t in range(43))
    assert all(fix2[t]['A'] == fix2[t]['E'] == '?' * 32 for t in range(8, 43))
    assert fix[19]['A'] == '-' * 32 and fix[23]['E'] == '-' * 32
    assert all(old[t]['W'] == fix[t]['W'] == fix2[t]['W'] for t in range(16))
    cases.append({'name': 'two_documented_template_corrections', 'passed': True,
                  'expanded_words_released': 21, 'forced_zero_expanded_rows': sorted(zero),
                  'fix2_free_A_E_rows': [8, 42],
                  'scope': 'Corrected masks differ as stated. No feasibility or historical UNSAT proof is checked.'})
    two, two_dir = run('two', 'twoblock')
    assert two.returncode == 0 and len(list(two_dir.glob('*.xml'))) == 33
    b1, tree1 = parse(two_dir / 's256_r40_twoblock_B1.xml')
    b2, tree2 = parse(two_dir / 's256_r40_twoblock_B2.xml')
    assert b1[36]['E'] == b2[-4]['E'] == '---u' + '-' * 28
    assert b2[36]['E'] == '---n' + '-' * 28
    assert all(b1[t]['A'] == b1[t]['E'] == '-' * 32 for t in range(-4, 0))
    assert {x.attrib['name'] for x in tree1.findall('options/option')} == {'f', 'n', 'w'}
    cases.append({'name': 'two_block_masks', 'passed': True, 'files': 33,
                  'caution': 'B1 text says standard IV, but generator emits equal-input difference masks, not eight standard-IV value pins. Establish absolute initial values in the consuming model separately.'})
    regs, regs_dir = run('registers', 'twoblock_reg', 'e0', 'f31', 'g15', 'h28')
    assert regs.returncode == 0 and len(list(regs_dir.glob('*.xml'))) == 39
    for reg, bit, entry, end in [('e', 0, -1, 39), ('f', 31, -2, 38), ('g', 15, -3, 37), ('h', 28, -4, 36)]:
        r1, _ = parse(regs_dir / f's256_r40_twoblock_B1_{reg}{bit}.xml')
        r2, _ = parse(regs_dir / f's256_r40_twoblock_B2_{reg}{bit}.xml')
        u = '-' * (31 - bit) + 'u' + '-' * bit
        n = '-' * (31 - bit) + 'n' + '-' * bit
        assert r1[end]['E'] == r2[entry]['E'] == u and r2[end]['E'] == n
    cases.append({'name': 'four_register_row_mappings', 'passed': True, 'files': 39})
    unknown, unknown_dir = run('unknown', 'not-a-mode')
    assert unknown.returncode == 0 and len(list(unknown_dir.glob('*.xml'))) == 31
    cases.append({'name': 'unknown_mode_is_ignored', 'passed': True})
    missing, _ = run('missing', create=False)
    assert missing.returncode != 0 and 'FileNotFoundError' in missing.stderr
    cases.append({'name': 'output_directory_must_exist', 'passed': True})
    invalid, invalid_dir = run('invalid', 'twoblock_reg', 'z1')
    assert invalid.returncode != 0 and 'KeyError' in invalid.stderr
    assert len(list(invalid_dir.glob('*.xml'))) == 31
    cases.append({'name': 'invalid_register_leaves_partial_output', 'passed': True, 'files_left': 31})
    badbit, badbit_dir = run('badbit', 'twoblock_reg', 'e32')
    assert badbit.returncode == 0 and len(list(badbit_dir.glob('*.xml'))) == 33
    malformed = ET.parse(badbit_dir / 's256_r40_twoblock_B2_e32.xml').getroot().find('char').attrib['value']
    assert re.search(r'-1\s+A:\s+-{32}\s+E:\s+u-{32}', malformed)
    cases.append({'name': 'out_of_range_bit_not_validated', 'passed': True, 'mask_width': 33})
    victim = base / 's256_r40_join16.xml'
    victim.write_text('test sentinel', encoding='utf-8')
    again = subprocess.run([sys.executable, '-I', '-B', str(script), str(base)], cwd=work, capture_output=True, timeout=10)
    assert again.returncode == 0 and victim.read_text(encoding='utf-8') != 'test sentinel'
    parse(victim)
    cases.append({'name': 'rerun_overwrites_existing_named_outputs', 'passed': True})
report = {'passed': True, 'source': REL, 'source_sha256': PIN,
          'source_edition': 'Exact missing original recovered from attached source text; no live-source substitution',
          'cases': cases, 'finished_at': datetime.now(timezone.utc).isoformat(),
          'scope': 'Ten bounded generator/interface and characteristic-recount controls. No solver, compression replay, concrete 40-step pair, completeness proof or attack-price certification.'}
# Report returned through stdout only.
print(json.dumps(report, indent=2))
