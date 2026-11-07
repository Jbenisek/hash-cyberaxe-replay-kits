/* Run with Node.js: node examples/replay.cjs. No external modules or network. */
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const replay = require('../sha256-replay.js');
const family = JSON.parse(fs.readFileSync(path.join(__dirname, '../data/witnesses.json'), 'utf8'));
for (const text of ['', 'abc', 'The quick brown fox jumps over the lazy dog', 'a'.repeat(55)]) {
  const message = Buffer.from(text), block = Buffer.alloc(64);
  message.copy(block); block[message.length] = 128;
  block.writeBigUInt64BE(BigInt(message.length * 8), 56);
  const words = Array.from({length:16}, (_, i) => block.readUInt32BE(i*4));
  assert.equal(replay.compress(words).output.map(replay.hex).join(''),
    crypto.createHash('sha256').update(message).digest('hex'));
}
for (const w of family) {
  const cv = w.chaining.map(x => parseInt(x, 16));
  const inputs = w.messages.map(a => a.map(x => parseInt(x, 16)));
  const outputs = inputs.map(a => replay.compress(a, cv, w.rounds));
  assert.notDeepEqual(inputs[0], inputs[1], w.id);
  assert.deepEqual(outputs[0].state.map(replay.hex), w.expected_output, w.id);
  assert.deepEqual(outputs[0].output, outputs[1].output, w.id);
}
const first = family[0], cv = first.chaining.map(x => parseInt(x, 16));
const a = first.messages[0].map(x => parseInt(x, 16));
const b = first.messages[1].map(x => parseInt(x, 16));
b[0] ^= 1;
assert.notDeepEqual(replay.compress(a, cv, 39).output, replay.compress(b, cv, 39).output);
console.log(`PASS: 4 standard SHA-256 vectors; ${family.length} 39-step semi-free-start pairs; 1 negative control.`);
console.log('Scope: chosen common chaining value; full 32-bit words; not fixed-IV SHA-256 collision evidence.');
