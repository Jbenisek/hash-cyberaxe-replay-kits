// Finite replay of four recorded objects; no solver and no network.
const assert=require('node:assert/strict'),fs=require('node:fs'),crypto=require('node:crypto'),path=require('node:path');
const dir=__dirname, hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const manifest=JSON.parse(fs.readFileSync(path.join(dir,'MANIFEST.json'),'utf8'));
for(const f of manifest.files){
 assert(!path.isAbsolute(f.path)&&!f.path.split(/[\\/]/).includes('..'));
 const b=fs.readFileSync(path.join(dir,f.path));assert.equal(b.length,f.bytes);assert.equal(hash(b),f.sha256,'Changed kit file: '+f.path);
}
const sha=require('./sha256-replay.js');
const block=Buffer.alloc(64);block.write('abc');block[3]=128;block.writeBigUInt64BE(24n,56);
assert.equal(sha.compress(Array.from({length:16},(_,i)=>block.readUInt32BE(i*4))).output.map(sha.hex).join(''),hash(Buffer.from('abc')));
const data=JSON.parse(fs.readFileSync(path.join(dir,'pairs.json'),'utf8'));
assert.equal(data.records.length,4);
const results=[];
for(const pair of data.records){
 const cv=pair.chaining.map(v=>v.map(x=>parseInt(x,16))),m=pair.messages.map(v=>v.map(x=>parseInt(x,16)));
 assert.notDeepEqual(m[0],m[1]);assert.deepEqual(cv[0],cv[1]);assert.notDeepEqual(cv[0],sha.IV);
 const runs=m.map((v,i)=>sha.compress(v,cv[i],pair.rounds));
 const equal=runs[0].output.every((x,i)=>x===runs[1].output[i]);
 assert.equal(equal,pair.expected_collision);
 assert.deepEqual(runs.map(r=>r.output.map(sha.hex)),pair.expected_outputs);
 const changed=m[1].slice();changed[0]=(changed[0]^1)>>>0;
 if(equal){
  assert.notDeepEqual(sha.compress(changed,cv[1],39).output,runs[0].output);
  assert.notDeepEqual(sha.compress(m[0],cv[0],40).output,sha.compress(m[1],cv[1],40).output);
 }
 results.push({id:pair.id,rounds:pair.rounds,shared_chosen_cv:true,collision:equal});
}
assert.equal(results.filter(r=>r.collision).length,1);
console.log(JSON.stringify({passed:true,known_answer:'SHA-256 abc',candidates:4,collisions:1,noncollisions:3,
 mutation_and_one_step_extension_rejected:true,results,
 scope:'Finite full-width chosen-CV compression replay. The three noncolliding state candidates are not claimed collisions. No standard-IV collision, padding eligibility or discovery-price claim.'},null,2));
