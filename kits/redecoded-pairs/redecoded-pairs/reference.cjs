'use strict';
// Arithmetic extracted from the pinned project-independent publication verifier.
const K=[0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2];
const IV=[0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];
const rr=(x,n)=>(x>>>n)|(x<<(32-n)), hex=x=>(x>>>0).toString(16).padStart(8,'0');
const eq=(a,b)=>a.length===b.length&&a.every((x,i)=>x===b[i]);
const words = a => {
  if (!Array.isArray(a) || a.some(x=>typeof x!=='string'||!/^[0-9a-f]{8}$/i.test(x))) throw Error('Bad hex words');
  return a.map(x=>parseInt(x,16));
};
function compress(m,cv,n) {
  if(m.length!==16||cv.length!==8||!Number.isInteger(n)||n<1||n>64)throw Error('Invalid shape/rounds');
  const w=m.slice();
  for(let i=16;i<n;i++){
    const x=w[i-15],y=w[i-2];
    w[i]=(w[i-16]+(rr(x,7)^rr(x,18)^(x>>>3))+w[i-7]+(rr(y,17)^rr(y,19)^(y>>>10)))>>>0;
  }
  let [a,b,c,d,e,f,g,h]=cv;
  for(let i=0;i<n;i++){
    const t1=(h+(rr(e,6)^rr(e,11)^rr(e,25))+((e&f)^((~e)&g))+K[i]+w[i])>>>0;
    const t2=((rr(a,2)^rr(a,13)^rr(a,22))+((a&b)^(a&c)^(b&c)))>>>0;
    [a,b,c,d,e,f,g,h]=[(t1+t2)>>>0,a,b,c,(d+t1)>>>0,e,f,g];
  }
  const state=[a,b,c,d,e,f,g,h];
  return {state,output:state.map((x,i)=>(x+cv[i])>>>0)};
}
const abc=compress([0x61626380,...Array(14).fill(0),24],IV,64).output.map(hex).join('');
const expected='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad';
if(abc!==expected)throw Error('abc known-answer failed');


module.exports={compress,IV,hex,eq};
