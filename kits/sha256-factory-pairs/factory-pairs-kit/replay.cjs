// Finite numerical replay only; no solver, network, search or mutable project state.
const assert=require('node:assert/strict'), fs=require('node:fs'), path=require('node:path'), crypto=require('node:crypto');
const root=__dirname, hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const manifest=JSON.parse(fs.readFileSync(path.join(root,'MANIFEST.json'),'utf8'));
const names=new Set(['pairs.json','sha256-replay.js','replay.cjs','README.md']);
assert.equal(manifest.files.length,names.size);
assert.deepEqual(new Set(manifest.files.map(x=>x.path)),names);
for(const f of manifest.files){const b=fs.readFileSync(path.join(root,f.path));assert.equal(b.length,f.bytes);assert.equal(hash(b),f.sha256);}
const sha=require('./sha256-replay.js'), data=JSON.parse(fs.readFileSync(path.join(root,'pairs.json'),'utf8'));
const parse=(a,n)=>{assert(Array.isArray(a)&&a.length===n);return a.map(x=>{assert(typeof x==='string'&&/^[0-9a-f]{8}$/.test(x));return parseInt(x,16);});};
for(const msg of [Buffer.alloc(0),Buffer.from('abc'),Buffer.from(Array.from({length:32},(_,i)=>i)),Buffer.from(Array.from({length:55},(_,i)=>i))]){
 const b=Buffer.alloc(64);msg.copy(b);b[msg.length]=128;b.writeBigUInt64BE(BigInt(msg.length*8),56);
 assert.equal(sha.compress(Array.from({length:16},(_,i)=>b.readUInt32BE(i*4))).output.map(sha.hex).join(''),hash(msg));
}
assert.equal(data.factory_records.length,33);assert.equal(data.silent_schedule_records.length,5);
assert.equal(data.chosen_cv_schedule_records.length,4);
const identities=new Set(),cvs=new Set();
for(const r of data.factory_records){
 assert.equal(r.rounds,39);const cv=parse(r.chaining,8),ms=r.messages.map(x=>parse(x,16));
 assert.notDeepEqual(ms[0],ms[1]);assert.notDeepEqual(cv,sha.IV);
 const a=sha.compress(ms[0],cv,39),b=sha.compress(ms[1],cv,39);
 assert.deepEqual(a.state,b.state);assert.deepEqual(a.output,b.output);assert.deepEqual(a.output.map(sha.hex),r.output);
 const changed=ms[1].slice();changed[0]=(changed[0]^1)>>>0;
 assert.notDeepEqual(sha.compress(changed,cv,39).output,a.output);
 for(const n of [40,64])assert.notDeepEqual(sha.compress(ms[0],cv,n).output,sha.compress(ms[1],cv,n).output);
 identities.add(JSON.stringify([39,cv,ms.map(x=>x.map(sha.hex).join('')).sort()]));cvs.add(cv.map(sha.hex).join(''));
}
assert.equal(identities.size,33);assert.equal(cvs.size,33);
const rr=(x,n)=>(x>>>n)|(x<<(32-n));
function expand(m,n){const w=m.slice();for(let t=16;t<n;t++){const a=w[t-15],b=w[t-2];w.push((w[t-16]+(rr(a,7)^rr(a,18)^(a>>>3))+w[t-7]+(rr(b,17)^rr(b,19)^(b>>>10)))>>>0);}return w;}
const scheduleIdentities=new Set();
for(const [rows,standard] of [[data.silent_schedule_records,true],[data.chosen_cv_schedule_records,false]])for(const r of rows){
 assert(Number.isInteger(r.rounds)&&r.rounds>=40&&r.rounds<=44);
 assert(Array.isArray(r.messages)&&r.messages.length===2);
 assert.equal(r.standard_iv,standard);assert.equal(r.compression_collision,false);
 const cv=parse(r.chaining,8),ms=r.messages.map(x=>parse(x,16));
 if(standard)assert.deepEqual(cv,sha.IV);else assert.notDeepEqual(cv,sha.IV);
 assert.notDeepEqual(ms[0],ms[1]);
 const runs=ms.map(m=>sha.compress(m,cv,r.rounds));assert.notDeepEqual(runs[0].state,runs[1].state);assert.notDeepEqual(runs[0].output,runs[1].output);
 const w=ms.map(m=>expand(m,r.rounds));assert.deepEqual(w[0].map((x,i)=>x===w[1][i]?null:i).filter(x=>x!==null),r.lit_schedule_rows);
 if(!standard){
  assert.deepEqual(runs.map(x=>x.output.map(sha.hex)),r.outputs);
  assert.deepEqual(runs.map(x=>x.state.map(sha.hex)),r.printed_working_states);
 }
 scheduleIdentities.add(JSON.stringify([r.rounds,cv,ms.map(x=>x.map(sha.hex).join('')).sort()]));
}
assert.equal(scheduleIdentities.size,9);
console.log(JSON.stringify({passed:true,hashlib_equivalent_controls:4,chosen_cv_collisions:33,distinct_common_cvs:33,
 standard_iv_schedule_examples:5,chosen_cv_schedule_examples:4,distinct_schedule_examples:9,
 standard_iv_collisions:0,mutation_and_extension_controls:99,
 scope:'Finite 39-step chosen-CV compression collisions and nine noncolliding schedule objects (five standard-IV, four chosen-CV). No padded-message eligibility, full-round collision, discovery cost, sampler law or claim of new round records.'},null,2));
