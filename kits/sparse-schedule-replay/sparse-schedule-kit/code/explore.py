import itertools,time,collections,json
MASK=(1<<32)-1

def sigvec(v,which):
 a,b,c=((7,18,3) if which==0 else (17,19,10))
 return [v[(i+a)%32]^v[(i+b)%32]^(v[i+c] if i+c<32 else 0) for i in range(32)]
def vx(*vs): return [__import__('functools').reduce(int.__xor__,b) for b in zip(*vs)]
def symbolic(T,N):
 ts=[t for t in T if t<32]
 W=[[0]*32 for _ in range(N)]
 for i,t in enumerate(ts): W[t]=[1<<(32*i+b) for b in range(32)]
 for t in range(31,15,-1):
  W[t-16]=vx(W[t],sigvec(W[t-2],1),W[t-7],sigvec(W[t-15],0))
 for t in range(32,N):
  W[t]=vx(sigvec(W[t-2],1),W[t-7],sigvec(W[t-15],0),W[t-16])
 return W,32*len(ts)
def basis(rows,n):
 piv={}
 for r in rows:
  while r:
   i=r.bit_length()-1
   if i in piv:r^=piv[i]
   else:piv[i]=r;break
 out=[]
 for f in range(n):
  if f in piv:continue
  x=1<<f
  for i,r in sorted(piv.items()):
   if (r&x).bit_count()%2:x^=1<<i
  out.append(x)
 return out

def apply(v,x):return sum(((r&x).bit_count()%2)<<b for b,r in enumerate(v))
def sweep(N):
 hist=collections.Counter(); surv=[]
 for l in (1,2):
  for T in itertools.combinations(range(16,N),l):
   if min(T)>=32:continue
   W,n=symbolic(T,N)
   B=basis([r for t in range(32,N) if t not in T for r in W[t]],n)
   hist[len(B)]+=1
   if not B:continue
   # Check exact tail support existence, excluding zero coordinate subspaces.
   if any(not any(apply(W[t],x) for x in B) for t in T):continue
   es=[t for t in range(16) if any(apply(W[t],x) for x in B)]
   surv.append((T,len(B),es))
 print(N,'hist',dict(hist),'survivors',len(surv))
 for item in surv:print(item)
 return surv
if __name__=='__main__':
 for N in (37,38,39,40):sweep(N)
