"""Recount the signed-W11 class map by rank, and check 1,152 saved representatives.

No SHA-256 collision search, solver, third-party module or network access.
"""
import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

EXPECTED = {
    'CLASSVALS3.tsv': 'f60a2431780b58f284e40ed8b66bb1ea9cd361d5184bae1b4998782bcab32e54',
    'CLASSVALS3_k8.tsv': '29e85248691ee3237b5ba708a578dc01bfdbfc7287bc01462a803f236699b7cc',
}
MASK = (1 << 32) - 1


def rotate(x, n):
    return ((x >> n) | (x << (32-n))) & MASK


def sigma0(x):
    return rotate(x, 7) ^ rotate(x, 18) ^ (x >> 3)


def basis(vectors):
    pivots = {}
    for value in vectors:
        while value:
            pivot = value.bit_length()-1
            if pivot in pivots:
                value ^= pivots[pivot]
            else:
                pivots[pivot] = value
                break
    return [pivots[key] for key in sorted(pivots, reverse=True)]


def replay(folder):
    data = {}
    texts = {}
    for name, expected in EXPECTED.items():
        raw = (folder/name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError('Changed or wrong input: '+name)
        texts[name] = raw.decode('utf-8')
        data[name] = list(csv.reader((line for line in texts[name].splitlines()
                                    if line and not line.startswith('#')), delimiter='\t'))
    header = texts['CLASSVALS3.tsv'].splitlines()[0]
    match = re.search(r'W11 row ([-un]{32}), DL ([0-9a-f]{8})', header)
    assert match
    row = match.group(1)
    fixed_one = sum(1 << (31-j) for j, ch in enumerate(row) if ch == 'n')
    fixed_zero = sum(1 << (31-j) for j, ch in enumerate(row) if ch == 'u')
    free = [31-j for j, ch in enumerate(row) if ch == '-']
    free_mask = sum(1 << i for i in free)
    flip = fixed_one | fixed_zero
    delta = (fixed_zero-fixed_one) & MASK
    assert delta == int(match.group(2), 16) == 0x0601dcd4
    assert len(free) == 23 and flip == 0x06022334

    # On this signed cube, Y=X xor flip = X+delta (mod 2^32).
    # Sigma0 is XOR-linear. For T=sigma0(flip):
    #   sigma0(Y)-sigma0(X) = T-2*(sigma0(X)&T) (mod 2^32).
    # Bit 31 of the intersection vanishes when multiplied by 2.
    toggle = sigma0(flip)
    effective = toggle & 0x7fffffff
    columns = [sigma0(1 << i) & effective for i in free]
    independent = basis(columns)
    image = {sigma0(fixed_one) & effective}
    for column in independent:
        image |= {value ^ column for value in tuple(image)}
    # Independently span all 23 columns; no enumeration of 2^23 input words.
    all_columns_image = {sigma0(fixed_one) & effective}
    for column in columns:
        all_columns_image |= {value ^ column for value in tuple(all_columns_image)}
    assert image == all_columns_image
    assert toggle == 0xe00141a0 and effective == 0x600141a0
    assert len(independent) == effective.bit_count() == 7
    certificate = {23:0x00010020,21:0x00004000,19:0x00010000,
                   16:0x40000000,15:0x20000100,14:0x00000080,11:0x00000100}
    assert all(i in free and sigma0(1 << i)&effective == value for i,value in certificate.items())
    assert len(basis(certificate.values())) == 7
    assert len(image) == 128
    classes = {(toggle-2*value) & MASK for value in image}
    assert len(classes) == len(image)
    multiplicity = 1 << (len(free)-len(independent))
    assert multiplicity == 65536 and len(classes)*multiplicity == 1 << 23

    baseline = data['CLASSVALS3.tsv']; additional = data['CLASSVALS3_k8.tsv']
    assert len(baseline) == 128 and all(len(r) == 3 for r in baseline)
    assert len(additional) == 1024 and all(len(r) == 4 for r in additional)
    assert Counter(r[-1] for r in baseline) == {'UNSEEN':106, 'seen':22}
    assert Counter(r[-1] for r in additional) == {'UNSEEN':848, 'seen':176}
    label_by_class = {int(c,16): label for c, x, label in baseline}
    assert set(label_by_class) == classes
    assert next(x for c,x,label in baseline if c == '2000bea0') == '01003fbb'
    assert Counter(int(r[0],16) for r in additional) == {c:8 for c in classes}
    for c in classes:
        assert {int(r[2]) for r in additional if int(r[0],16) == c} == set(range(2,10))
    seen = set()
    for record in baseline+additional:
        c, x = (int(value,16) for value in record[:2])
        assert 0 <= x <= MASK and x & (MASK ^ free_mask) == fixed_one
        assert x not in seen
        seen.add(x)
        y = (x+delta) & MASK
        assert y == x ^ flip
        assert ((sigma0(y)-sigma0(x)) & MASK) == c
        assert c == (toggle-2*(sigma0(x)&effective)) & MASK
        assert record[-1] == label_by_class[c]
    assert len(seen) == 1152
    return {
        'passed':True,
        'scope':'Exact rank-based recount on the specified signed word cube, plus all saved representatives. No full-schedule reachability, collision or attack-rate claim.',
        'source_files':[{'name':name,'sha256':digest} for name,digest in EXPECTED.items()],
        'signed_row':row, 'modular_delta':f'{delta:08x}', 'xor_delta':f'{flip:08x}',
        'sigma_xor_delta':f'{toggle:08x}', 'effective_mask':f'{effective:08x}',
        'free_input_bits':len(free), 'rank':len(independent),
        'basis_hex':[f'{value:08x}' for value in independent],
        'rank_certificate':[{'input_bit':i,'column_hex':f'{value:08x}'} for i,value in certificate.items()],
        'classes':len(classes), 'members_per_class':multiplicity,
        'total_word_inputs':1 << len(free), 'representatives_checked':len(seen),
        'class_hex':sorted(f'{c:08x}' for c in classes),
        'historical_labels':{'seen_classes':22,'UNSEEN_classes':106},
        'label_scope':'Membership in the producer\'s prior VALUE_MAP snapshot, not a solver verdict.'
    }


def main():
    if not __debug__:
        raise RuntimeError('Run without -O: assertions are required')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data',type=Path,default=Path(__file__).resolve().parent,
                        help='Directory containing the two exact TSV files; read only')
    args=parser.parse_args()
    print(json.dumps(replay(args.data),indent=2))


if __name__ == '__main__':
    main()
