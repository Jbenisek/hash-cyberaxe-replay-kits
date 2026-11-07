# derive-sched-inverse-expansion-B: exact checks for cells (3,19) (4,19) (4,20) (5,20) (5,21) (10,17)
import re
M=0xffffffff
rotr=lambda x,n:((x>>n)|(x<<(32-n)))&M
s0=lambda x:rotr(x,7)^rotr(x,18)^(x>>3)
s1=lambda x:rotr(x,17)^rotr(x,19)^(x>>10)
chi=open('../../chi/chi37.txt').read().splitlines()
W={}
for ln in chi:
    m=re.match(r'row\s+(\d+)\s+(\S{32})\s+(\S{32})\s+(\S{32})',ln)
    if m: W[int(m.group(1))]=m.group(4)
def moddiff(cells):  # x - y ; n=(x,y)=(0,1) u=(1,0)
    d=0
    for i,c in enumerate(cells):
        b=31-i
        if c=='u': d+=1<<b
        elif c=='n': d-=1<<b
        elif c not in '=01+?': raise ValueError(c)
    return d&M
for i in (3,4,5):
    cells=W.get(i,'='*32)
    print(f"W{i} cells {cells} (row {'printed' if i in W else 'not printed = no difference'}) dMOD={moddiff(cells):08x} dXOR=0 -> dW{i}=0 so d(W{i}) and d s0(W{i}) are identically 0")
dW10=moddiff(W[10]); print(f"W10 cells {W[10]} dMOD(x-y)={dW10:08x}  (signed cells fix it: constant over every consistent pair)")
print(f"W15 cells {W[15]} dMOD(x-y)={moddiff(W[15]):08x}")
L=[int(v,16) for v in next(l for l in chi if l.startswith('var W15 list')).split('#')[0].split()[3:]]
assert len(L)==32
ok=0
for l in L:
    assert (l>>29)&1==1  # u at bit 29: x member has 1
    x=l; y=l^0x20000000
    ds1=(s1(x)-s1(y))&M
    tot=(ds1+dW10)&M
    ok+= tot==0
    print(f"l={l:08x} ds1(W15)={ds1:08x} + dW10={dW10:08x} = dW17 {tot:08x} {'CANCELS' if tot==0 else 'NONZERO'}")
print(f"cancel on {ok}/32 l (exact enumeration)")
# free-model rate (cell view with W15 free, bit29=u): s1 XOR diff bits {19,12,10}; signs are 3 independent linear bits of W15
import itertools
cnt=0;tot_=0
# exact: s1 bits 19,12,10 of x are linear in W15; enumerate only the bits that feed them (rotr17,rotr19,shr10)
feed=set()
for b in (19,12,10):
    feed|={(b+17)%32,(b+19)%32} | ({b+10} if b+10<32 else set())
feed-= {29}
feed=sorted(feed)
for bits in itertools.product((0,1),repeat=len(feed)):
    x=1<<29
    for f,v in zip(feed,bits): x|=v<<f
    y=x^0x20000000
    tot_+=1; cnt+= ((s1(x)-s1(y)+dW10)&M)==0
print(f"free W15 (bit29 u, other bits free): Pr[dW17=0] = {cnt}/{tot_} (exact over the {len(feed)} bits that feed s1 bits 19,12,10) -- the 32 l carry this at Pr 1")
# numeric confirmation on the example pair: expand mx/my
def words(tag): 
    ln=next(l for l in chi if l.startswith(tag+' ')); return [int(v,16) for v in ln.split()[1:17]]
for tag in ('mx','my'):
    pass
mx,my=words('mx'),words('my')
def expand(w):
    w=list(w)
    for t in range(16,37): w.append((s1(w[t-2])+w[t-7]+s0(w[t-15])+w[t-16])&M)
    return w
ex,ey=expand(mx),expand(my)
for t in (3,4,5,10,15,17,19,20,21):
    print(f"example pair W{t} dMOD={(ex[t]-ey[t])&M:08x}")
print("W15 of example x member in list:", ex[15] in L, f"{ex[15]:08x}")
