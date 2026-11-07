"""Exact SHA-256 reference, trace, and reduced-prefix compression (0-based rows)."""
import struct, hashlib, json, re, pathlib
MASK = (1 << 32) - 1
IV = [0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19]
K = [int(x,16) for x in '''428a2f98 71374491 b5c0fbcf e9b5dba5 3956c25b 59f111f1 923f82a4 ab1c5ed5
d807aa98 12835b01 243185be 550c7dc3 72be5d74 80deb1fe 9bdc06a7 c19bf174
e49b69c1 efbe4786 0fc19dc6 240ca1cc 2de92c6f 4a7484aa 5cb0a9dc 76f988da
983e5152 a831c66d b00327c8 bf597fc7 c6e00bf3 d5a79147 06ca6351 14292967
27b70a85 2e1b2138 4d2c6dfc 53380d13 650a7354 766a0abb 81c2c92e 92722c85
a2bfe8a1 a81a664b c24b8b70 c76c51a3 d192e819 d6990624 f40e3585 106aa070
19a4c116 1e376c08 2748774c 34b0bcb5 391c0cb3 4ed8aa4a 5b9cca4f 682e6ff3
748f82ee 78a5636f 84c87814 8cc70208 90befffa a4506ceb bef9a3f7 c67178f2'''.split()]
def ror(x,n): return ((x >> n) | (x << (32-n))) & MASK
def S0(x): return ror(x,2)^ror(x,13)^ror(x,22)
def S1(x): return ror(x,6)^ror(x,11)^ror(x,25)
def s0(x): return ror(x,7)^ror(x,18)^(x>>3)
def s1(x): return ror(x,17)^ror(x,19)^(x>>10)
def ch(x,y,z): return (x&y)^((~x)&z)
def maj(x,y,z): return (x&y)^(x&z)^(y&z)
def schedule(m,rounds=64):
    w=list(m)
    for t in range(16,rounds): w.append((s1(w[t-2])+w[t-7]+s0(w[t-15])+w[t-16]) & MASK)
    return w[:rounds]
def compress(m,iv=IV,rounds=64):
    w=schedule(m,rounds); v=list(iv); states=[]
    for t in range(rounds):
        a,b,c,d,e,f,g,h=v
        T1=(h+S1(e)+ch(e,f,g)+K[t]+w[t])&MASK
        T2=(S0(a)+maj(a,b,c))&MASK
        v=[(T1+T2)&MASK,a,b,c,(d+T1)&MASK,e,f,g]; states.append(v)
    return [(x+y)&MASK for x,y in zip(iv,v)],states,w
def digest(data,rounds=64,iv=IV):
    n=len(data); data+=b'\x80'+bytes((55-n)%64)+struct.pack('>Q',8*n)
    h=list(iv)
    for j in range(0,len(data),64):h=compress(struct.unpack('>16I',data[j:j+64]),h,rounds)[0]
    return struct.pack('>8I',*h).hex()
def read_pair(path):
    text=pathlib.Path(path).read_text()
    return {key:[int(x,16) for x in re.findall(r'0x([0-9a-fA-F]+)',re.search(r'\b'+key+r':(.*?);',text).group(1))] for key in ['IV','MSG1','MSG2']}
def signed(a,b):
    # LLW source notation: u: first=1,second=0; n: first=0,second=1; -: equal.
    return ''.join('-' if ((a^b)>>j)&1==0 else 'u' if (a>>j)&1 else 'n' for j in range(31,-1,-1))
def pair_trace(pair,rounds):
    h,t,w=compress(pair['MSG1'],pair['IV'],rounds)
    hp,tp,wp=compress(pair['MSG2'],pair['IV'],rounds)
    rows=[]
    for j in range(rounds):
        rows.append(dict(row=j,A=signed(t[j][0],tp[j][0]),E=signed(t[j][4],tp[j][4]),W=signed(w[j],wp[j]),
                         dxA=f'{t[j][0]^tp[j][0]:08x}',dxE=f'{t[j][4]^tp[j][4]:08x}',dxW=f'{w[j]^wp[j]:08x}',
                         hw=sum((x^y).bit_count() for x,y in [(t[j][0],tp[j][0]),(t[j][4],tp[j][4]),(w[j],wp[j])])))
    return dict(rounds=rounds,collision=h==hp,hash1=''.join(f'{x:08x}' for x in h),hash2=''.join(f'{x:08x}' for x in hp),rows=rows,
                proxy_weight_16_22=sum(x['hw'] for x in rows[16:23]),pair=pair,trace1=t,trace2=tp,schedule1=w,schedule2=wp)
if __name__=='__main__':
    tests=[b'',b'abc',b'a'*55,b'a'*56,b'a'*64,b'a'*129,bytes(range(256))]
    for d in tests: assert digest(d)==hashlib.sha256(d).hexdigest()
    out=[]
    for name in ['sha256_39_SFS','sha256_39_SFS_Q']:
        pair=read_pair(pathlib.Path(__file__).parent/'llw24/verify_result'/f'{name}.txt')
        for r in [37,38,39]:
            o=pair_trace(pair,r);o['source']=name;out.append(o)
            print(name,r,o['collision'],o['hash1'],'proxy',o['proxy_weight_16_22'])
    pathlib.Path(__file__).with_name('baseline_traces.json').write_text(json.dumps(out,indent=2))
    pathlib.Path(__file__).with_name('reference_validation.json').write_text(json.dumps({'hashlib_crosschecks':len(tests),'all_passed':True},indent=2))
