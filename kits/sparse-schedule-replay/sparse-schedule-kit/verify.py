"""Offline reproduction entry point. Standard library; C++ compiler for full counts."""
from pathlib import Path
import argparse,collections,csv,itertools,json,subprocess,sys,tempfile,shutil
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'code'))
from modular import expand,support,weight,MASK,s0,s1
from explore import apply

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--recompute-minima',action='store_true');ap.add_argument('--recompute-supports',action='store_true');a=ap.parse_args()
 data=json.loads((ROOT/'data/results.json').read_text())
 checks=0
 for r in data['linear_witnesses'].values():
  w=[int(s,16)for s in r['difference_words_hex']]
  assert expand(w[:16],r['N'],True)==w
  assert sum(x.bit_count()for x in w)==r['weight']
  assert [t for t in range(16,r['N'])if w[t]]==r['late_support'];checks+=1
 for r in data['modular_witnesses'].values():
  aa=r['a'];bb=r['b'];N=r['N'];assert expand(aa[:16],41)==aa and expand(bb[:16],41)==bb
  assert weight(aa[:N],bb[:N])==r['verified_weight'];assert support(aa[:N],bb[:N])==r['verified_support'];checks+=1
 for name,fun in [('sigma0',s0),('sigma1',s1)]:
  inv=[int(v,16)for v in data['sigma_certificates'][name]['inverse_rows_hex']]
  for b in range(32):assert apply(inv,fun(1<<b))==1<<b;checks+=1
 for N in range(37,42):
  groups=collections.defaultdict(list)
  for j in range(16,N):
   mask=sum(1<<(t-32)for t in range(32,N)if j in {t,t-2,t-7,t-15,t-16});groups[mask].append(j)
  got=[]
  for mask,inds in groups.items():
   if not mask:got.extend((j,)for j in inds)
   got.extend(itertools.combinations(inds,2))
  expected=[tuple(map(int,r['late_support'].split(',')))for r in data['late_supports']if r['N']==N]
  assert sorted(got)==sorted(expected);checks+=1
 print(f'PASS: {checks} quick replay/certificate checks. No compression collision claim is being checked.')
 if a.recompute_minima or a.recompute_supports:
  with tempfile.TemporaryDirectory(prefix='sparse-schedule-')as td:
   work=Path(td)
   for f in (ROOT/'code').glob('*.py'):shutil.copy(f,work/f.name)
   shutil.copy(ROOT/'certificates/linear_candidates.json',work/'linear_candidates.json')
   if a.recompute_supports:
    subprocess.run(['g++','-O3',str(ROOT/'code/rank_supports.cpp'),'-o',str(work/'rank_supports')],check=True)
    subprocess.run([sys.executable,str(work/'count_supports.py')],check=True)
    assert (work/'linear_full_supports.csv').read_bytes()==(ROOT/'data/linear_full_supports.csv').read_bytes()
    print('PASS: complete linear exact-support catalogue reproduced.')
   if a.recompute_minima:
    subprocess.run(['g++','-O3','-march=native',str(ROOT/'code/min_enum.cpp'),'-o',str(work/'min_enum')],check=True)
    for mat in sorted((ROOT/'certificates').glob('*.mat')):
     dest=work/(mat.stem+'.json');subprocess.run([str(work/'min_enum'),str(mat),str(dest)],check=True)
     expected=json.loads((ROOT/'certificates'/(mat.stem+'.min.json')).read_text());actual=json.loads(dest.read_text())
     assert actual['examined']==expected['examined'] and actual['minimum']==expected['minimum']
    subprocess.run([sys.executable,str(work/'min_infosets.py')],check=True)
    current=json.loads((work/'linear_min_infosets.json').read_text());saved=json.loads((ROOT/'certificates/linear_min_infosets.json').read_text())
    for x,y in zip(current,saved):assert x['minimum']==y['minimum'] and x['completeness_threshold']==y['completeness_threshold']
    print('PASS: all linear minimum-distance certificates reproduced.')
if __name__=='__main__':main()
