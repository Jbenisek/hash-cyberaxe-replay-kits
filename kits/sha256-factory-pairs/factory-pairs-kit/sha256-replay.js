/* Independent, inspectable SHA-256 compression replay for the published specimen.
 * The input is already 16 words. This function does not add message padding.
 * Word arithmetic is modulo 2^32, and feed-forward adds the common input CV.
 */
(function (root) {
  'use strict';
  const K=[0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2];
  const IV=[0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];
  const rr=(x,n)=>(x>>>n)|(x<<(32-n));
  const hex=x=>(x>>>0).toString(16).padStart(8,'0');
  const pop=x=>{x>>>=0;let n=0;while(x){x=(x&(x-1))>>>0;n++;}return n;};
  function compress(message,cv=IV,rounds=64){
    if(message.length!==16||cv.length!==8||!Number.isInteger(rounds)||rounds<1||rounds>64)throw Error('Expected 16 message words, 8 CV words, and 1–64 steps');
    const w=message.map(x=>x>>>0);
    for(let i=16;i<rounds;i++){const a=w[i-15],b=w[i-2];w[i]=(w[i-16]+(rr(a,7)^rr(a,18)^(a>>>3))+w[i-7]+(rr(b,17)^rr(b,19)^(b>>>10)))>>>0;}
    let [a,b,c,d,e,f,g,h]=cv.map(x=>x>>>0);const trace=[];
    for(let i=0;i<rounds;i++){
      const t1=(h+(rr(e,6)^rr(e,11)^rr(e,25))+((e&f)^(~e&g))+K[i]+w[i])>>>0;
      const t2=((rr(a,2)^rr(a,13)^rr(a,22))+((a&b)^(a&c)^(b&c)))>>>0;
      [a,b,c,d,e,f,g,h]=[(t1+t2)>>>0,a,b,c,(d+t1)>>>0,e,f,g];
      trace.push([a,b,c,d,e,f,g,h]);
    }
    const state=[a,b,c,d,e,f,g,h];return {state,output:state.map((x,i)=>(x+cv[i])>>>0),trace};
  }
  const api={compress,IV,hex,pop};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  root.SHA256Replay=api;
  if(typeof document==='undefined'||!document.querySelector('#verify-witness'))return;
  const $=s=>document.querySelector(s);
  fetch('data/witnesses.json').then(r=>{if(!r.ok)throw Error('Witness family could not be loaded');return r.json();}).then(family=>{
    const label=document.createElement('label');label.textContent='Choose an audited specimen (54 pairs replayed independently)';
    const select=document.createElement('select');select.id='witness-select';
    family.forEach(w=>{const option=document.createElement('option');option.value=w.id;option.textContent=w.id+' · 39 steps · 32-bit words';select.append(option);});
    label.append(select);$('#witness-inputs').before(label);
    function load(w){
    const messages=w.messages.map(m=>m.map(x=>parseInt(x,16))),cv=w.chaining.map(x=>parseInt(x,16));
    function renderInputs(m){$('#witness-inputs').innerHTML='<div class="message-grid">'+m.map((row,s)=>'<section class="message-panel"><h2>Message '+(s?'B':'A')+'</h2><div class="word-grid">'+row.map((word,i)=>'<div class="word-cell '+(m[0][i]!==m[1][i]?'changed':'')+'"><small>W'+i+'</small>'+hex(word)+'</div>').join('')+'</div></section>').join('')+'</div>';}
    function verify(mutation){
      const input=messages.map(m=>m.slice());if(mutation)input[1][0]=(input[1][0]^1)>>>0;renderInputs(input);
      const a=compress(input[0],cv,w.rounds),b=compress(input[1],cv,w.rounds);
      const different=input[0].some((v,i)=>v!==input[1][i]),equal=a.output.every((v,i)=>v===b.output[i]);
      // The source witness calls the final working state "out" (pre-feed-forward).
      const expected=a.state.map(hex).every((v,i)=>v===w.expected_output[i]);
      const result=$('#witness-result');result.className='verification'+(mutation?' changed':(!equal||!expected?' error':''));
      result.textContent=mutation?(equal?'The modified pair also collides.':'One bit changed: the modified pair does not collide.'):(different&&equal&&expected?'Verified in your browser: distinct messages, identical 256-bit output, and an exact match to the recorded witness.':'Verification failed. The computed output does not match the recorded witness.');
      const distances=a.trace.map((row,i)=>row.reduce((sum,v,j)=>sum+pop(v^b.trace[i][j]),0));
      const peak=Math.max(1,...distances);
      $('#witness-trace').innerHTML='<span class="trace-scale">Peak: '+peak+' of 256 state bits · chart scaled to this run</span>'+distances.map((n,i)=>'<div class="trace-bar '+(n===0?'zero':'')+'" tabindex="0" role="img" aria-label="Step '+(i+1)+': '+n+' differing state bits" title="Step '+(i+1)+': '+n+' differing bits" style="height:'+Math.max(2,n/peak*130)+'px"><span>'+(i+1)+'</span></div>').join('');
      $('#witness-details').innerHTML='<p>The archived “out” field is the working state before feed-forward. We check that exact field, then add the common chaining value to both states.</p><h3>Common input chaining value</h3><pre>'+cv.map(hex).join(' ')+'</pre><h3>Working state A (matches the archived out field)</h3><pre>'+a.state.map(hex).join(' ')+'</pre><h3>Working state B</h3><pre>'+b.state.map(hex).join(' ')+'</pre><h3>Output A (with feed-forward)</h3><pre>'+a.output.map(hex).join(' ')+'</pre><h3>Output B (with feed-forward)</h3><pre>'+b.output.map(hex).join(' ')+'</pre>';
    }
    renderInputs(messages);$('#witness-result').textContent='The archived inputs are loaded. Specimen '+w.id+'. Select “Compute both messages” to verify the pair.';
    $('#witness-trace').replaceChildren();$('#witness-details').replaceChildren();
    const sourceLink=document.querySelector('.witness-lab .actions a');sourceLink.href='record.html?id='+w.record_id;sourceLink.textContent='Read specimen '+w.id+' ↗';
    $('#verify-witness').onclick=()=>verify(false);$('#mutate-witness').onclick=()=>verify(true);
    }
    select.onchange=()=>load(family.find(w=>w.id===select.value));load(family[0]);
  }).catch(error=>{$('#witness-result').textContent=error.message;$('#witness-result').className='verification error';});
})(typeof globalThis!=='undefined'?globalThis:this);
