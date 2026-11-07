// Finite copied-generator probe. No host imports or filesystem writes.
const fs = require('node:fs');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const raw = fs.readFileSync('gen.wasm');
assert.equal(crypto.createHash('sha256').update(raw).digest('hex'),
  '0918ee3fcc92fb33164ccb9898d2c5b1cf2a28d80e7a3aeee12b031de48648f1');
assert.equal(raw.subarray(0,8).toString('hex'),'0061736d01000000');
function leb(pos) {
  let value = 0, scale = 1;
  for(let n=0;n<5;n++) {
    assert(pos < raw.length);
    const byte=raw[pos++]; value += (byte&127)*scale;
    if(!(byte&128)) return [value,pos];
    scale *= 128;
  }
  throw Error('Oversized u32 LEB');
}
let pos=8, memory=null;
while(pos<raw.length) {
  const id=raw[pos++]; let size; [size,pos]=leb(pos);
  const end=pos+size; assert(end<=raw.length);
  if(id===5) {
    assert.equal(memory,null);
    let count,flags,min,max,j=pos;
    [count,j]=leb(j); assert.equal(count,1);
    [flags,j]=leb(j); assert.equal(flags,1); // bounded, unshared wasm32
    [min,j]=leb(j); [max,j]=leb(j); assert.equal(j,end);
    assert(min<=max && max<=16); memory={min,max};
  }
  pos=end;
}
assert(memory);
const module_ = new WebAssembly.Module(raw);
assert.deepEqual(WebAssembly.Module.imports(module_),[]);
const instance = new WebAssembly.Instance(module_,{});
function snapshot() {
  const ret=instance.exports.run();
  const bytes=Buffer.from(instance.exports.memory.buffer);
  assert(bytes.length<=1048576);
  const ip=instance.exports.info_ptr(), cp=instance.exports.code_ptr();
  assert(ip>=0 && ip+68<=bytes.length);
  const names='ninst nreg nodes calls err sz_code sz_ctr sz_uses sz_state'.split(' ');
  const info=Object.fromEntries(names.map((k,i)=>[k,bytes.readUInt32LE(ip+i*4)]));
  assert(cp>=0 && cp+info.sz_code<=bytes.length);
  assert(info.ninst<=20000);
  const code=bytes.subarray(cp,cp+info.sz_code);
  const lines=[]; let off=0;
  if(ret===0 && info.err===0) {
    for(let i=0;i<info.ninst;i++) {
      const op=String.fromCharCode(code[off++]); assert('^&|?'.includes(op));
      const fields=op==='?'?4:3, size=op==='?'?5:4;
      assert(off+size<=code.length);
      let word=0n;
      for(let j=0;j<size;j++) word |= BigInt(code[off+j])<<BigInt(8*j);
      off+=size; assert.equal(word>>BigInt(10*fields),0n);
      const regs=[];
      for(let j=0;j<fields;j++) regs.push(Number((word>>BigInt(10*j))&1023n));
      assert(regs.every(r=>r<info.nreg));
      lines.push(op+' '+regs.join(' '));
    }
    assert(code.subarray(off).every(x=>x===0));
  }
  const q=Buffer.from(bytes.subarray(ip+36,ip+68)).reverse().toString('hex');
  return {return_code:ret,info,q_hex:q,memory_bytes:bytes.length,used_record_bytes:off,
    instruction_sha256:crypto.createHash('sha256').update(lines.join('\n')+'\n').digest('hex'),lines};
}
const first=snapshot(), second=snapshot();
assert.equal(first.return_code,0); assert.equal(first.info.err,0);
console.log(JSON.stringify({memory_limits:memory,imports:0,first,second}));
