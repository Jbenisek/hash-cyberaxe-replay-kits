"""Replay two historical SHA-256 controls; optionally inspect four generated CNFs.

Python standard library only. No SAT solver, network access or campaign launch.
Run from the extracted kit: python -B replay.py [--encode]
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(arguments, directory, environment, timeout=15):
    started = time.monotonic()
    proc = subprocess.run([sys.executable, '-B', *map(str, arguments)], cwd=directory,
                          env=environment, text=True, capture_output=True, timeout=timeout)
    require(proc.returncode == 0, 'Child failed: ' + proc.stderr[-800:])
    return proc.stdout, round(time.monotonic() - started, 4)


def decoded(seed):
    return ''.join('M' + side + ': W=' + ' '.join(seed['M' + side]) +
                   '\n   chain=' + ' '.join(seed['cv']) + '\n' for side in ('1', '2'))


def cnf_parts(path):
    lines = path.read_text().splitlines()
    fields = lines[0].split()
    require(fields[:2] == ['p', 'cnf'] and len(fields) == 4, 'Not plain DIMACS')
    nv, nc = map(int, fields[2:])
    clauses = [line for line in lines[1:] if line.strip()]
    require(len(clauses) == nc, 'Incorrect clause count')
    for line in clauses:
        values = list(map(int, line.split()))
        require(values[-1] == 0 and all(0 < abs(v) <= nv for v in values[:-1]),
                'Invalid clause literal')
    return nv, clauses


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--encode', action='store_true', help='Also encode ctl/real at 37 and 38 steps; no solving')
    args = parser.parse_args()
    require(__debug__, 'Do not run the historical encoder with Python -O')
    root = Path(__file__).resolve().parent
    manifest = json.loads((root/'MANIFEST.json').read_text())
    for item in manifest['files']:
        path = (root/item['path']).resolve()
        require(path.is_relative_to(root), 'Manifest path escapes kit')
        require(hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256'],
                'Source hash mismatch: ' + item['path'])
    env = dict(os.environ)
    for key in ('WBITS','BITORDER','CHAINREV','SIGNED','KOFF','EXTRAW','MODDIFF',
                'SCHED_ONLY','NEAR_K','NEAR_ENC','NEAR_OUTS','REQUIRE_DIFF',
                'SYMBREAK','XORMODE','XOR3','DIFFVARS','PYTHONPATH','PYTHONOPTIMIZE'):
        env.pop(key, None)
    env.update(WBITS='32', SIGNED='1', PYTHONDONTWRITEBYTECODE='1')
    cpp = load_module('boardpair_profile', root/'kit/char_pair_profile.py')
    cv = [0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
          0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19]
    padded = b'abc' + b'\x80' + b'\0'*52 + (24).to_bytes(8, 'big')
    words = [int.from_bytes(padded[i:i+4], 'big') for i in range(0, 64, 4)]
    a, e = cpp.states(cv, cpp.expand(words, 64), 64)
    out = [a[t] for t in range(63,59,-1)] + [e[t] for t in range(63,59,-1)]
    digest = b''.join(((x+y)&0xffffffff).to_bytes(4,'big') for x,y in zip(cv,out)).hex()
    require(digest == hashlib.sha256(b'abc').hexdigest(), 'SHA-256 abc control failed')
    report = {'passed': False, 'standard_abc': True, 'cases': [], 'encodings': [],
              'scope': 'Two finite shared-chosen-CV controls, three negative controls per seed. Optional encoder checks verify serialization, pin units and exclusion clause, not full CNF equivalence or a solver result.'}
    with tempfile.TemporaryDirectory(prefix='boardpair-replay-') as temporary:
        work = Path(temporary)
        for name, n in (('r37_tab17',37), ('r38_s102',38)):
            seed_path = root/'boardpairs/wit'/f'{name}.json'
            seed = json.loads(seed_path.read_text())
            require(len(seed['cv'])==8 and len(seed['M1'])==len(seed['M2'])==16, 'Seed dimensions')
            values = [[int(word,16) for word in seed[key]] for key in ('cv','M1','M2')]
            require(all(0<=v<2**32 for group in values for v in group), 'Out-of-range word')
            profile = cpp.profile(*values, n)
            require(profile['collision'], 'Seed is not a collision')
            check_file, map_file = work/'pair.chk', work/'pair.map'
            checks=[]
            for control in ('positive','one_more_step','mutated_message','identical_messages'):
                candidate = json.loads(json.dumps(seed))
                rounds = n + (control == 'one_more_step')
                if control == 'mutated_message':
                    candidate['M2'][0] = f"{int(candidate['M2'][0],16)^1:08x}"
                if control == 'identical_messages':candidate['M2']=list(candidate['M1'])
                check_file.write_text(decoded(candidate))
                map_file.write_text(json.dumps({'n':rounds,'wbits':32,'chaining':'sfs'}))
                stdout, elapsed = run([root/'kit/indep_verify.py', map_file, check_file], work, env)
                verified = 'INDEP VERIFIED' in stdout.splitlines()
                require(verified == (control=='positive'), name + ': ' + control + ' unexpected verdict')
                checks.append({'control':control,'rounds':rounds,'verified':verified,'elapsed_seconds':elapsed})
            report['cases'].append({'seed':name,'rounds':n,'raw_C1_count':profile['total']['cond'],
                                    'checks':checks})
            if args.encode:
                bases={}
                for mode in ('ctl','real'):
                    base=work/(name+'-'+mode)
                    stdout, elapsed=run([root/'boardpairs/gen_boardpair.py',seed_path,'SELF',n,
                                         16,4,'none',mode,base],work,env,timeout=60)
                    require(f'OK pins=512 extra_clauses={512+(mode=="real")}' in stdout, 'Pin diagnostic')
                    mp=json.loads(base.with_suffix('.map').read_text())
                    require(mp['n']==n and mp.get('wbits',32)==32, 'Unexpected target')
                    nv, clauses=cnf_parts(base.with_suffix('.cnf'))
                    bases[mode]=(nv,clauses,mp)
                    report['encodings'].append({'seed':name,'mode':mode,'variables':nv,
                       'clauses':len(clauses),'pins':512,'elapsed_seconds':elapsed,
                       'cnf_sha256':hashlib.sha256(base.with_suffix('.cnf').read_bytes()).hexdigest()})
                nv, ctl, mp=bases['ctl']; rnv, real, rmp=bases['real']
                require(nv==rnv and mp==rmp and real[:-1]==ctl, 'real differs beyond its exclusion clause')
                def pin(bits, value):return [v if (value>>i)&1 else -v for i,v in enumerate(bits)]
                units=[]
                for t in range(16,20):
                    for field in ('A1','A2','E1','E2'):
                        units.extend(pin(mp[field+'all'][str(t)],profile[field][t]))
                require(ctl[-512:]==[f'{value} 0' for value in units], 'Wrong middle-band pins')
                exclusion=[]
                for i in range(4):
                    for reg, value in (('A',values[0][i]),('E',values[0][i+4])):
                        for side in ('1','2'):
                            exclusion.extend(-v for v in pin(mp[reg+side][str(-1-i)],value))
                for w in range(16):
                    for side, message in (('1',values[1]),('2',values[2])):
                        exclusion.extend(-v for v in pin(mp['W'+side][w],message[w]))
                require(len(exclusion)==1536 and real[-1]==' '.join(map(str,exclusion))+' 0', 'Wrong seed exclusion')
    report['passed']=True
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
