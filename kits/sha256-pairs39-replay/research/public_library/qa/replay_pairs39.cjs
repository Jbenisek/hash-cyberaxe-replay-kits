// Finite PAIRS_39.tsv replay. Run from repository root:
// node research/public_library/qa/replay_pairs39.cjs
// Built-ins only; stdout JSON; no writes, network, solvers or sampling.
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

const input='research/game/climber/guided/PAIRS_39.tsv';
const existing54='research/public_library/site/data/witnesses.json';
const existing31='research/public_library/qa/resolve31-normalized.json';
const old54=JSON.parse(read(existing54)),old31=JSON.parse(read(existing31)).records;
const key=(cv,messages,n)=>JSON.stringify([n,cv,messages.map(m=>m.join(' ')).sort()]);
const prior=new Map([...old54,...old31].map(r=>[key(r.chaining,r.messages,r.rounds),r.id]));
const lines=read(input).trim().split(/\r?\n/);
if(lines[0]!=='#sig\tcv\tM1\tM2\tsigma0_W11_class\ttail_mean_log2\tsource')throw Error('Unexpected TSV schema');
const groups=new Map();
for(const [index,line] of lines.slice(1).entries()){
  const c=line.split('\t');if(c.length!==7)throw Error('Wrong columns at '+(index+2));
  const cv=words(c[1].split(' ')),m1=words(c[2].split(' ')),m2=words(c[3].split(' '));
  const ident=key(cv.map(hex),[m1.map(hex),m2.map(hex)],39);
  const alias={name:c[0],source_line:index+2,sigma0_W11_class:c[4],historical_tail_mean_log2:c[5]==='nan'?null:Number(c[5]),historical_source:c[6]};
  if(groups.has(ident)){groups.get(ident).aliases.push(alias);continue;}
  const x=compress(m1,cv,39),y=compress(m2,cv,39),xp=compress(m1,cv,40),yp=compress(m2,cv,40);
  const verified=!eq(m1,m2)&&eq(x.state,y.state)&&eq(x.output,y.output);
  groups.set(ident,{id:c[0],aliases:[alias],rounds:39,word_bits:32,model:'semi-free-start compression; common chosen CV; no padding eligibility asserted',chaining:cv.map(hex),messages:[m1.map(hex),m2.map(hex)],messages_differ:!eq(m1,m2),standard_iv:eq(cv,IV),internal_state_equal:eq(x.state,y.state),feedforward_equal:eq(x.output,y.output),states:[x.state.map(hex),y.state.map(hex)],outputs:[x.output.map(hex),y.output.map(hex)],expected_state:verified?x.state.map(hex):null,expected_output:verified?x.output.map(hex):null,output_convention:'feed-forward included: state[i] + common_cv[i] mod 2^32',verified,already_published_id:prior.get(ident)||null,one_step_control:{rounds:40,internal_state_equal:eq(xp.state,yp.state),output_equal:eq(xp.output,yp.output),states:[xp.state.map(hex),yp.state.map(hex)],outputs:[xp.output.map(hex),yp.output.map(hex)]}});
}
const records=[...groups.values()];
const checker='research/public_library/qa/replay_pairs39.cjs';
console.log(JSON.stringify({schema_version:1,source:input,source_sha256:sha256(input),checker,checker_sha256:sha256(checker),method:'Finite independent SHA-256 compression replay; same plain-JavaScript arithmetic as replay_resolve31.cjs, not a project solver or encoder. All 61 source rows are examined and deduplicated by rounds, common CV and unordered messages.',known_answer:{message:'abc',rounds:64,standard_iv:true,expected,digest:abc,pass:abc===expected},comparison_baseline:[existing54,existing31].map(p=>({path:p,sha256:sha256(p)})),summary:{source_rows:lines.length-1,distinct_pairs:records.length,verified:records.filter(r=>r.verified).length,failed:records.filter(r=>!r.verified).length,previously_published:records.filter(r=>r.already_published_id).length,new_verified:records.filter(r=>r.verified&&!r.already_published_id).length,standard_iv:records.filter(r=>r.standard_iv).length,one_step_collisions:records.filter(r=>r.one_step_control.output_equal).length},limits:['Finite witnesses, not a success-probability or work-factor proof.','Table tail estimates and sigma-class fields are copied as historical metadata, not re-estimated or certified.','Chosen-CV compression collisions are not ordinary standard-IV hashes.','One-step controls concern only these same messages and chaining values.','Comparison to the existing 85 uses numeric identities, not filenames.'],records},null,2));

