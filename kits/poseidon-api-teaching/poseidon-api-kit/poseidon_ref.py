"""Independent big-int reference for Orchard P128Pow5T3 over Pallas (halo2_poseidon 0.2.0).

Constants and MDS are read as data from the organizer's pinned JSON (never regenerated).
  hash_reduced(nk, rho, r) : target hash, rounds = full 0..3, partial 4..4+r-1, full 60..63
  hash_full(nk, rho)       : complete 64-round ConstantLength<2> hash (r = 56), implemented
                             through a separate straight-line 64-round loop (is_full by index)
Both initialise the width-3 state as [nk, rho, 2^65] and return state[0] after the last MDS.
"""
import json, os

P = 0x40000000000000000000000000000000224698fc094cf91b992d30ed00000001
CAPACITY = 1 << 65          # ConstantLength<2>: L * 2^64 with L = 2
_HERE = os.path.dirname(os.path.abspath(__file__))
CONST_PATH = os.environ.get(
    'ORCHARD_CONSTANTS_JSON',
    os.path.normpath(os.path.join(_HERE, '..', '..', 'pareto_clone', 'pareto', 'orchard-pallas-constants.json')))

with open(CONST_PATH) as f:
    _d = json.load(f)
RC = tuple(tuple(int(x, 16) for x in row) for row in _d['round_constants'])   # 64 x 3
MDS = tuple(tuple(int(x, 16) for x in row) for row in _d['mds'])              # 3 x 3
assert len(RC) == 64 and all(len(r) == 3 for r in RC) and len(MDS) == 3
assert all(0 <= x < P for r in RC for x in r) and all(0 <= x < P for r in MDS for x in r)


def mds_apply(s):
    return [sum(MDS[i][j] * s[j] for j in range(3)) % P for i in range(3)]


def round_full(s, idx):
    s = [(s[i] + RC[idx][i]) % P for i in range(3)]
    s = [pow(x, 5, P) for x in s]
    return mds_apply(s)


def round_partial(s, idx):
    s = [(s[i] + RC[idx][i]) % P for i in range(3)]
    s[0] = pow(s[0], 5, P)
    return mds_apply(s)


def schedule(r):
    """Original round indices used by the reduced target, in order."""
    assert 0 <= r <= 56
    return list(range(0, 4)) + list(range(4, 4 + r)) + list(range(60, 64))


def perm(state, r=56):
    s = list(state)
    for idx in schedule(r):
        s = round_full(s, idx) if (idx < 4 or idx >= 60) else round_partial(s, idx)
    return s


def check_input(x):
    if type(x) is not int or not 0 <= x < P:
        raise ValueError('non-canonical field element')


def hash_reduced(nk, rho, r):
    check_input(nk); check_input(rho)
    return perm([nk, rho, CAPACITY], r)[0]


def hash_full(nk, rho):
    """Complete 64-round hash, written as a plain loop over 64 rounds (no schedule helper)."""
    check_input(nk); check_input(rho)
    s = [nk, rho, CAPACITY]
    for idx in range(64):
        full = idx < 4 or idx >= 60
        s = [(s[i] + RC[idx][i]) % P for i in range(3)]
        for i in (range(3) if full else range(1)):
            s[i] = pow(s[i], 5, P)
        s = mds_apply(s)
    return s[0]


def digest_bytes(msg64, r):
    """Mirror of the organizer's digest(): 64 bytes in (two LE field encodings), 32 bytes LE out."""
    if not isinstance(msg64, bytes) or len(msg64) != 64:
        raise ValueError('need exactly 64 bytes')
    nk = int.from_bytes(msg64[:32], 'little'); rho = int.from_bytes(msg64[32:], 'little')
    return hash_reduced(nk, rho, r).to_bytes(32, 'little')
