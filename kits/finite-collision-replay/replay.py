#!/usr/bin/env python3
"""Read adjacent data.json, check finite witnesses, print JSON; never write files.

Independent publication checker, Python standard library only. No archived
participant programs imported. See README.md for target conventions and scope.
"""
import hashlib
import json
from pathlib import Path
import re
import sys
import time

MASK = (1 << 64) - 1
P = 0x40000000000000000000000000000000224698fc094cf91b992d30ed00000001


def rotate(word, count):
    count %= 64
    return ((word << count) | (word >> ((64 - count) % 64))) & MASK


def keccak_parameters():
    offsets = {(0, 0): 0}
    x, y = 1, 0
    for t in range(24):
        offsets[x, y] = ((t + 1) * (t + 2) // 2) % 64
        x, y = y, (2 * x + 3 * y) % 5
    constants, lfsr = [], 1
    for _ in range(24):
        rc = 0
        for j in range(7):
            if lfsr & 1:
                rc ^= 1 << ((1 << j) - 1)
            lfsr = ((lfsr << 1) ^ (0x71 if lfsr & 0x80 else 0)) & 255
        constants.append(rc)
    return offsets, constants


OFFSETS, CONSTANTS = keccak_parameters()


def sha3_prefix(message, rounds):
    if not 1 <= rounds <= 24:
        raise ValueError('unsupported Keccak prefix length')
    padded = bytearray(message) + b'\x06'
    padded += bytes((-len(padded)) % 136)
    padded[-1] ^= 0x80
    state = {(x, y): 0 for y in range(5) for x in range(5)}
    for start in range(0, len(padded), 136):
        for lane in range(17):
            state[lane % 5, lane // 5] ^= int.from_bytes(
                padded[start + 8 * lane:start + 8 * lane + 8], 'little')
        for rc in CONSTANTS[:rounds]:
            columns = [state[x, 0] ^ state[x, 1] ^ state[x, 2] ^ state[x, 3] ^ state[x, 4]
                       for x in range(5)]
            moved = {}
            for x, y in state:
                lane = state[x, y] ^ columns[(x - 1) % 5] ^ rotate(columns[(x + 1) % 5], 1)
                moved[y, (2 * x + 3 * y) % 5] = rotate(lane, OFFSETS[x, y])
            state = {(x, y): moved[x, y] ^ ((~moved[(x + 1) % 5, y]) & moved[(x + 2) % 5, y])
                     for y in range(5) for x in range(5)}
            state[0, 0] ^= rc
    return b''.join(state[x, 0].to_bytes(8, 'little') for x in range(4))


def le(hex_string):
    return int.from_bytes(bytes.fromhex(hex_string), 'little')


def poseidon_state(state, partial, constants, matrix):
    if not 0 <= partial <= 56 or len(state) != 3 or any(not 0 <= x < P for x in state):
        raise ValueError('invalid Orchard state or partial-round count')
    s = list(state)
    for index in list(range(4)) + list(range(4, 4 + partial)) + list(range(60, 64)):
        s = [(s[j] + constants[index][j]) % P for j in range(3)]
        s = [pow(s[j], 5, P) if index < 4 or index >= 60 or j == 0 else s[j] for j in range(3)]
        s = [sum(matrix[i][j] * s[j] for j in range(3)) % P for i in range(3)]
    return s


def run(data):
    started = time.monotonic()
    params = data['parameters']['poseidon']
    constants = [[int(x, 16) for x in row] for row in params['round_constants_hex']]
    matrix = [[int(x, 16) for x in row] for row in params['mds_hex']]
    if int(params['modulus_hex'], 16) != P or int(params['capacity_hex'], 16) != 1 << 65:
        raise ValueError('incorrect Orchard field/capacity')
    if len(constants) != 64 or any(len(row) != 3 for row in constants) or len(matrix) != 3 or any(len(row) != 3 for row in matrix):
        raise ValueError('incorrect parameter dimensions')

    def digest(message, profile):
        match = re.fullmatch(r'(sha3-256|poseidon-orchard)-r(\d+)-prefix-v1', profile)
        if not match:
            raise ValueError('unsupported target profile')
        rounds = int(match[2])
        if match[1] == 'sha3-256':
            return sha3_prefix(message, rounds)
        if len(message) != 64:
            raise ValueError('Orchard input is not 64 bytes')
        a, b = int.from_bytes(message[:32], 'little'), int.from_bytes(message[32:], 'little')
        if a >= P or b >= P:
            raise ValueError('noncanonical Pallas input')
        return poseidon_state([a, b, 1 << 65], rounds, constants, matrix)[0].to_bytes(32, 'little')

    def check_pair(record, message_a=None):
        a = bytes.fromhex(record['message_a_hex']) if message_a is None else message_a
        b = bytes.fromhex(record['message_b_hex'])
        expected = bytes.fromhex(record['expected_digest'])
        da, db = digest(a, record['profile']), digest(b, record['profile'])
        return {'id': record['id'], 'profile': record['profile'], 'distinct': a != b,
                'equal': da == db, 'expected': da == expected,
                'computed_digest_a': da.hex(), 'computed_digest_b': db.hex(),
                'passed': a != b and da == db and da == expected}

    controls = []
    kat = data['known_answers']
    for index, vector in enumerate(kat['sha3']):
        controls.append({'kind': 'sha3_known_answer', 'index': index,
                         'passed': sha3_prefix(bytes.fromhex(vector['message_hex']), 24).hex() == vector['digest_hex']})
    for length in kat['sha3_hashlib_lengths']:
        message = bytes((i * 73 + 19) % 256 for i in range(length))
        controls.append({'kind': 'sha3_hashlib_full24', 'bytes': length,
                         'passed': sha3_prefix(message, 24) == hashlib.sha3_256(message).digest()})
    for index, vector in enumerate(kat['poseidon_permutation_le_hex']):
        words = [le(v) for v in vector]
        controls.append({'kind': 'poseidon_full56_permutation', 'index': index,
                         'passed': poseidon_state(words[:3], 56, constants, matrix) == words[3:]})
    for index, vector in enumerate(kat['poseidon_hash_le_hex']):
        controls.append({'kind': 'poseidon_full56_hash', 'index': index,
                         'passed': digest(bytes.fromhex(vector[0] + vector[1]), 'poseidon-orchard-r56-prefix-v1').hex() == vector[2]})
    for name, values in [('round_constants', constants), ('mds', matrix)]:
        other = [[le(v) for v in row] for row in params['parameter_crosscopy_le_hex'][name]]
        controls.append({'kind': 'parameter_crosscopy', 'parameter': name, 'passed': values == other})

    certificates, mutations, seen, mutated_profiles = [], [], set(), set()
    for record in data['witnesses']:
        if time.monotonic() - started > 28:
            raise TimeoutError('28-second finite audit deadline exceeded')
        key = (record['profile'], *sorted([record['message_a_hex'], record['message_b_hex']]))
        if key in seen:
            raise ValueError('duplicate unordered witness pair')
        seen.add(key)
        certificates.append(check_pair(record))
        if record['profile'] not in mutated_profiles:
            # One deterministic single-bit alteration per target, preserving length.
            changed = bytearray.fromhex(record['message_a_hex'])
            changed[0] ^= 1
            try:
                result = check_pair(record, bytes(changed))
                rejected = not result['passed']
                reason = 'digest/equality check rejected mutation' if rejected else 'mutation unexpectedly accepted'
            except ValueError as exc:
                rejected, reason = True, str(exc)
            mutations.append({'profile': record['profile'], 'witness_id': record['id'],
                              'mutation': 'message_a byte 0 XOR 0x01', 'rejected': rejected, 'detail': reason})
            mutated_profiles.add(record['profile'])
    expected_shape = (len(controls) == 41 and len(certificates) == 49 and len(mutations) == 6
                      and sum(r['profile'].startswith('sha3-') for r in certificates) == 16
                      and sum(r['profile'].startswith('poseidon-') for r in certificates) == 33)
    passed = expected_shape and all(r['passed'] for r in controls + certificates) and all(r['rejected'] for r in mutations)
    return {'passed': passed, 'expected_shape': expected_shape, 'controls': controls,
            'certificates': certificates, 'mutation_negative_controls': mutations,
            'counts': {'controls': len(controls), 'witnesses': len(certificates), 'negative_controls': len(mutations)},
            'elapsed_seconds': time.monotonic() - started,
            'scope': 'Finite reduced-round collision validity only; not success probability, algorithm cost, attribution or full-round security.'}


def main():
    try:
        folder = Path(__file__).resolve().parent
        raw = (folder / 'data.json').read_bytes()
        report = run(json.loads(raw.decode('utf-8-sig')))
        report['data_sha256'] = hashlib.sha256(raw).hexdigest()
        report['checker_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        print(json.dumps(report, indent=2))
        return 0 if report['passed'] else 1
    except Exception as exc:
        print(json.dumps({'passed': False, 'error': str(exc)}))
        return 1


if __name__ == '__main__':
    sys.exit(main())
