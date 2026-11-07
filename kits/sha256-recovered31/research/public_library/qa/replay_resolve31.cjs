// Finite SHA-256 witness replay. Project publication audit, 2026-10-29.
// No solver, sampling, network, or writes. Run from workspace root:
// node research/public_library/qa/replay_resolve31.cjs
// stdout is normalized JSON. Compression context is common free CV (SFS),
// 32-bit words, n steps, big-endian words; NOT padded standard-IV message hashing.
'use strict';
const fs = require('fs'), path = require('path'), crypto = require('crypto');
const root = path.resolve(process.argv[2] || '.');
const registry = 'research/luna/audit_packets/RESOLVE_1028.tsv';
const read = p => fs.readFileSync(path.join(root,p),'utf8');
const sha256 = p => crypto.createHash('sha256').update(fs.readFileSync(path.join(root,p))).digest('hex');
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
const rows=read(registry).trim().split(/\r?\n/).slice(1).filter(l=>!l.startsWith('#')).map(l=>l.split('\t')).filter(r=>r[4]==='VERIFIED');
if(rows.length!==31)throw Error('Registry changed: expected 31 VERIFIED rows');
const records=rows.map(r=>{
  const source=r[1],kind=r[2],rounds=Number(r[3]),raw=read(source);
  let m1,m2,cv1,cv2,width=32,id;
  if(kind.startsWith('json')){
    const j=JSON.parse(raw);
    width=j.w||j.width||32; id=j.name||path.basename(source);
    if(j.R!==undefined&&j.R!==rounds)throw Error('Registry round mismatch: '+source);
    m1=words(j.M1);m2=words(j.M2);cv1=words(j.cv);cv2=words(j.cv2||j.cv);
  }else{
    const ms=[...raw.matchAll(/M[12]: W=([0-9a-f ]+)\r?\n\s*chain=([0-9a-f ]+)/g)];
    if(ms.length!==2)throw Error('Text pair parse: '+source);
    [m1,m2]=ms.map(m=>words(m[1].trim().split(/\s+/)));
    [cv1,cv2]=ms.map(m=>words(m[2].trim().split(/\s+/)));
    id=path.basename(source,path.extname(source));
  }
  if(width!==32||!eq(cv1,cv2))throw Error('Not common-CV 32-bit model: '+source);
  const x=compress(m1,cv1,rounds),y=compress(m2,cv2,rounds);
  const xp=compress(m1,cv1,rounds+1),yp=compress(m2,cv2,rounds+1);
  const verified=!eq(m1,m2)&&eq(x.state,y.state)&&eq(x.output,y.output);
  return {id,source,source_sha256:sha256(source),registry_page:r[0],registry_kind:kind,
    rounds,word_bits:width,model:'semi-free-start compression, shared chosen CV',
    word_order:'a b c d e f g h; message words in algorithm order',
    messages:[m1.map(hex),m2.map(hex)],chaining:cv1.map(hex),
    messages_differ:!eq(m1,m2),differing_words:m1.map((v,i)=>v===m2[i]?-1:i).filter(i=>i>=0),
    standard_iv:eq(cv1,IV),internal_state_equal:eq(x.state,y.state),feedforward_equal:eq(x.output,y.output),
    expected_state:x.state.map(hex),expected_output:x.output.map(hex),
    output_convention:'feed-forward included: working_state[i] + common_cv[i] mod 2^32',
    one_step_control:{rounds:rounds+1,output_equal:eq(xp.output,yp.output),outputs:[xp.output.map(hex),yp.output.map(hex)]},
    verified};
});
if(records.some(r=>!r.verified||r.one_step_control.output_equal))throw Error('Witness/control replay failure');
console.log(JSON.stringify({schema_version:1,registry,registry_sha256:sha256(registry),
  checker:'research/public_library/qa/replay_resolve31.cjs',checker_sha256:sha256('research/public_library/qa/replay_resolve31.cjs'),
  method:'Fresh finite replay; plain JavaScript SHA-256 compression. No solver or project encoder imports. Constants agree with canonical SHA-256; abc control checks 64 rounds.',
  known_answer:{message:'abc',rounds:64,standard_iv:true,expected,digest:abc,pass:true},
  summary:{verified:records.length,r38:records.filter(r=>r.rounds===38).length,r39:records.filter(r=>r.rounds===39).length,standard_iv:records.filter(r=>r.standard_iv).length,one_step_collisions:records.filter(r=>r.one_step_control.output_equal).length},
  limits:['These are fixed finite witnesses, not collision probability estimates or work-factor proofs.','Free shared CV is not standard-IV hashing. No padding/domain eligibility is asserted.','One-step failure only concerns these concrete pairs.','No signed characteristic, minimum support, solver model, generation-time claim or all-solutions statement is reverified.'],
  records},null,2));

