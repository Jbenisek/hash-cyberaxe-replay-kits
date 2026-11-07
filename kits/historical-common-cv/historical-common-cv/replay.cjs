// Finite historical-data replay only. No network, solver, search or GPU.
'use strict';
const fs=require('node:fs'),crypto=require('node:crypto'),assert=require('node:assert/strict'),path=require('node:path');
assert.equal(process.argv.length,2,'No launch or other arguments are supported');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const source=fs.readFileSync(path.join(__dirname,'sha256-replay.js'));
const raw=fs.readFileSync(path.join(__dirname,'records.json'));
assert.equal(sha(source),'a08df68ee8b4a98949d94896486fc04cabad9e71087f3a0719003088a3fa1b8c','Replay implementation changed');
assert.equal(sha(raw),'6450b6eb77cdfb41ad72d39279f93695aaa55a12e5511ca2819cff46477b7146','Reviewed records changed');
const replay=require('./sha256-replay.js'),data=JSON.parse(raw);
const eq=(a,b)=>a.every((x,i)=>x===b[i]);
function words(a,n){assert(Array.isArray(a)&&a.length===n);return a.map(x=>{assert(typeof x==='string'&&/^[a-f0-9]{8}$/.test(x));return parseInt(x,16);});}
// Standard SHA-256 convention controls, independent of the stored pair claims.
for(const text of ['', 'abc']){
 const input=Buffer.from(text),block=Buffer.alloc(64);input.copy(block);block[input.length]=128;block.writeBigUInt64BE(BigInt(input.length*8),56);
 const w=Array.from({length:16},(_,i)=>block.readUInt32BE(i*4));assert.equal(replay.compress(w).output.map(replay.hex).join(''),sha(input));
}
assert.equal(data.format,'hashsmash-historical-common-cv-pairs-v1');
assert.equal(data.records.length,1286);assert.equal(data.record_count,1286);
const counts={},identities=new Set();let receipts=0;
for(const row of data.records){
 assert(Number.isInteger(row.rounds)&&row.rounds>=36&&row.rounds<=39);
 const cv=words(row.chaining,8);assert.equal(row.messages.length,2);const messages=row.messages.map(m=>words(m,16));
 assert(!eq(cv,replay.IV)&&row.standard_iv===false);
 assert(row.common_input_chaining_value===true&&row.word_bits===32);
 assert(!eq(messages[0],messages[1])&&row.messages_differ===true);
 assert(row.claim_price===null&&row.padding_eligibility==='not-certified');
 const key=JSON.stringify([row.rounds,cv,[...messages].sort((a,b)=>a.join(',').localeCompare(b.join(',')))]);
 assert(!identities.has(key));identities.add(key);
 const a=replay.compress(messages[0],cv,row.rounds),b=replay.compress(messages[1],cv,row.rounds);
 assert(eq(a.state,b.state)&&eq(a.output,b.output)&&row.working_state_equal===true);
 assert.deepEqual(row.working_states,[a.state,b.state].map(s=>s.map(replay.hex)));
 assert.deepEqual(row.outputs,[a.output,b.output].map(s=>s.map(replay.hex)));
 assert(row.source_receipts.length>0);receipts+=row.source_receipts.length;
 counts[row.rounds]=(counts[row.rounds]||0)+1;
}
assert.deepEqual(counts,{'36':179,'37':478,'38':156,'39':473});assert.deepEqual(data.round_counts,counts);assert.equal(receipts,1288);
console.log(JSON.stringify({passed:true,distinct_pairs:identities.size,round_counts:counts,source_receipts:receipts,
 standard_iv_pairs:0,forty_round_pairs:0,solver_runs:0,claim_prices_certified:0,
 scope:'Historical common-nonstandard-CV compression equalities only; not standard-IV hash collisions, legal padding, discovery credit or an attack price.'}));
