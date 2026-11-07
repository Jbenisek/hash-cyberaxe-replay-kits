"""Recount two retained sampled q pools; never generate new samples."""
import argparse
from array import array
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
MASK = (1 << 32)-1
if not __debug__:
    raise SystemExit('Run without -O.')
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--scalar',action='store_true',help='Force standard-library scalar recount of all70 rows (slower).')
args = parser.parse_args()
manifest = json.loads((HERE/'manifest.json').read_text())
for name,pin in manifest['files'].items():
    assert Path(name).name == name
    raw = (HERE/name).read_bytes()
    assert len(raw) == pin['bytes'] and hashlib.sha256(raw).hexdigest() == pin['sha256'],name
data = json.loads((HERE/'records.json').read_text())
literals = data['reference_literals']
assert len(literals['K']) == 38 and len(literals['PCV']) == 8
assert len(literals['PMX']) == len(literals['PMY']) == 16
assert all(type(x) is int and 0 <= x <= MASK for words in literals.values() for x in words)


def rotate(x,n):
    return ((x>>n)|(x<<(32-n)))&MASK


def sigma(x):
    return rotate(x,7)^rotate(x,18)^(x>>3)


def big0(x):
    return rotate(x,2)^rotate(x,13)^rotate(x,22)


def big1(x):
    return rotate(x,6)^rotate(x,11)^rotate(x,25)


def trace(words):
    a,b,c,d,e,f,g,h = literals['PCV']
    aa,ee = [],[]
    for k,w in zip(literals['K'][:16],words):
        t1 = (h+big1(e)+((e&f)^((~e)&g))+k+w)&MASK
        t2 = (big0(a)+((a&b)^(a&c)^(b&c)))&MASK
        a,b,c,d,e,f,g,h = (t1+t2)&MASK,a,b,c,(d+t1)&MASK,e,f,g
        aa.append(a)
        ee.append(e)
    return aa,ee


ax,ex = trace(literals['PMX'])
ay,ey = trace(literals['PMY'])
constant = (ex[7]-2*ax[3]+big0(ax[2])-big1(ex[6])-literals['K'][7])&MASK
delta = (ey[7]-ex[7])&MASK
target = (sigma(literals['PMY'][7])-sigma(literals['PMX'][7]))&MASK
assert (constant,delta,target) == (0x40b794c4,0x20000000,0x03bff800)
assert data['derived_constants'] == {'KK7c':'40b794c4','D7c':'20000000','F7d':'03bff800'}


def scalar(q,cv):
    w = (constant-cv+q)&MASK
    return ((sigma((w+delta)&MASK)-sigma(w))&MASK) == target


np = None
if not args.scalar:
    try:
        import numpy as np
    except ImportError:
        pass
pools = {}
for name in ('cv0pick2','cv0fresh1'):
    raw = (HERE/(name+'.bin')).read_bytes()
    assert len(raw) == 4*1048576
    if np is not None:
        pools[name] = np.frombuffer(raw,dtype='<u4')
    else:
        words = array('I')
        assert words.itemsize == 4
        words.frombytes(raw)
        if sys.byteorder != 'little':
            words.byteswap()
        pools[name] = words


def vector(values,cv):
    w = values+np.uint32((constant-cv)&MASK)
    v = w+np.uint32(delta)
    def s(x):
        return ((x>>7)|(x<<25))^((x>>18)|(x<<14))^(x>>3)
    return s(v)-s(w) == np.uint32(target)


assert len(data['rows']) == 70
assert len({(r['pool'],r['cv0']) for r in data['rows']}) == 70
observed = []
controls = 0
for row in data['rows']:
    assert row['members'] == 1048576 and row['pool'] in pools
    values = pools[row['pool']]
    cv = int(row['cv0'],16)
    assert 0 <= cv <= MASK and 0 <= row['passed'] <= row['members']
    if np is None:
        count = sum(scalar(int(q),cv) for q in values)
    else:
        count = int(np.count_nonzero(vector(values,cv)))
        fixtures = [int(q) for q in values[::8191]] + [0,1,MASK,MASK-1,(cv-constant)&MASK,(cv-constant-delta)&MASK]
        assert vector(np.array(fixtures,dtype=np.uint32),cv).tolist() == [scalar(q,cv) for q in fixtures]
        controls += len(fixtures)
    assert count == row['passed'],(row['pool'],row['cv0'],count,row['passed'])
    observed.append(count)
assert sum(r['pool']=='cv0pick2' for r in data['rows']) == 64
assert next(r['passed'] for r in data['rows'] if r['cv0']=='4d2f1627') == 136827
print(json.dumps({'passed':True,'rows_recounted':70,'pool_words':2097152,
    'backend':'numpy' if np is not None else 'stdlib-scalar','scalar_vector_comparisons':controls,
    'new_samples':0,'population_success_law_proved':False,
    'scope':'Exact count on two retained sampled pools, not a certified population probability or attack price.'},indent=2))
