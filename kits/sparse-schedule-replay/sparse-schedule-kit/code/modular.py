MASK=2**32-1

def rotr(x,n):return ((x>>n)|(x<<(32-n)))&MASK
def s0(x):return rotr(x,7)^rotr(x,18)^(x>>3)
def s1(x):return rotr(x,17)^rotr(x,19)^(x>>10)
def expand(m,N=64,linear=False):
 w=list(m)
 for t in range(16,N):
  a,b,c,d=s1(w[t-2]),w[t-7],s0(w[t-15]),w[t-16]
  w.append((a^b^c^d) if linear else ((a+b+c+d)&MASK))
 return w

def from_window(v,N=64,linear=False):
 w=[0]*16+list(v)
 for t in range(31,15,-1):
  a,b,c=s1(w[t-2]),w[t-7],s0(w[t-15])
  w[t-16]=(w[t]^a^b^c) if linear else ((w[t]-a-b-c)&MASK)
 return expand(w[:16],N,linear)

def support(a,b):return [i for i,(x,y) in enumerate(zip(a,b)) if x!=y]
def weight(a,b):return sum((x^y).bit_count() for x,y in zip(a,b))
if __name__=='__main__':
 A=[int(x,16)for x in '4d7f86ff 32ece589 d8accfc4 2cc2e433 068b5b34 eba68a28 2fe12cad 6aa26b0c 9f0d78e1 681b8277 faa9c7e0 56aed439 cc2dbbc2 dd2ba0fc b95d377b 5dd43a81'.split()]
 B=[int(x,16)for x in '4d7f86ff 32ece589 d8accfc4 2cc2e433 068b5b34 eba68a28 0fe12cad 6ee2630c bf0d78e1 6d1a90dd faa1d3e0 56aed439 cc2dbbc2 dd2ba0fc bd1d3f7b 7dd43a81'.split()]
 for N in range(37,42):
  a,b=expand(A,N),expand(B,N)
  print(N,support(a,b),weight(a,b), [(i,hex(x^y),(x^y).bit_count())for i,(x,y) in enumerate(zip(a,b))if x!=y])
