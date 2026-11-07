'use strict';
// Offline replay of numeric specimens; no solver, network or original campaign.
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const {compress,IV,hex,eq}=require('./reference.cjs');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const read=n=>fs.readFileSync(path.join(__dirname,n));
const manifest=JSON.parse(read('manifest.json'));
for(const [name,pin] of Object.entries(manifest.files)){
  if(path.basename(name)!==name)throw Error('Unsafe manifest path');
  const b=read(name);if(b.length!==pin.bytes||sha(b)!==pin.sha256)throw Error('Changed artifact: '+name);
}
const data=JSON.parse(read('pairs.json')), known=[];
for(const length of [0,3,55,56,64,135,256]){
  const message=Buffer.from(Array.from({length},(_,i)=>(i*73+19)&255));
  const suffix=Buffer.alloc((64-(length+9)%64)%64+9);suffix[0]=128;suffix.writeBigUInt64BE(BigInt(length)*8n,suffix.length-8);
  const padded=Buffer.concat([message,suffix]);let cv=Array.from(IV);
  for(let i=0;i<padded.length;i+=64)cv=compress(Array.from({length:16},(_,j)=>padded.readUInt32BE(i+4*j)),cv,64).output;
  if(cv.map(hex).join('')!==sha(message))throw Error('Reference gate failed');known.push(length);
}
const keys=new Set(),byRound={},rows=[];let sourceFiles=0;
for(const r of data.records){
  if(!Number.isInteger(r.rounds)||r.rounds<1||r.rounds>63)throw Error('Invalid round count');
  function words(a,n){if(!Array.isArray(a)||a.length!==n||a.some(w=>typeof w!=='string'||! /^[0-9a-f]{8}$/.test(w)))throw Error('Invalid words');return a.map(w=>parseInt(w,16));}
  const cv=words(r.chaining,8),m1=words(r.messages[0],16),m2=words(r.messages[1],16);
  if(eq(m1,m2)||eq(cv,IV))throw Error('Expected distinct messages and a nonstandard common CV');
  const key=JSON.stringify([r.rounds,r.chaining,r.messages.map(m=>m.join(' ')).sort()]);
  if(keys.has(key)||sha(Buffer.from(key))!==r.id)throw Error('Identity mismatch');keys.add(key);
  const a=compress(m1,cv,r.rounds),b=compress(m2,cv,r.rounds);
  if(!eq(a.output,b.output)||!eq(a.state,b.state))throw Error('Not a collision '+r.id);
  if(JSON.stringify([a.output.map(hex),b.output.map(hex)])!==JSON.stringify(r.outputs))throw Error('Stored output drift');
  const mutant=m2.slice();mutant[0]=(mutant[0]^1)>>>0;
  const mutation=eq(a.output,compress(mutant,cv,r.rounds).output);
  const extension=eq(compress(m1,cv,r.rounds+1).output,compress(m2,cv,r.rounds+1).output);
  if(mutation!==r.one_bit_control_equal||extension!==r.one_step_control_equal)throw Error('Control changed');
  sourceFiles+=r.provenance.length;byRound[r.rounds]=(byRound[r.rounds]||0)+1;
  rows.push({id:r.id,rounds:r.rounds,verified:true,mutation_equal:mutation,one_step_equal:extension});
}
if(rows.length!==125||sourceFiles!==155)throw Error('Collection count mismatch');
const report={passed:true,source_file_rows:sourceFiles,distinct_unordered_pairs:rows.length,distinct_round_counts:byRound,
  standard_iv_pairs:0,known_answer_lengths:known,one_bit_equal_controls:rows.filter(r=>r.mutation_equal).length,
  one_step_equal_controls:rows.filter(r=>r.one_step_equal).length,
  scope:'Finite common-chosen-CV compression collisions with feedforward, not standard-IV hashes, original SAT-model verification, attack probabilities or new round records.'};
console.log(JSON.stringify(report,null,2));
