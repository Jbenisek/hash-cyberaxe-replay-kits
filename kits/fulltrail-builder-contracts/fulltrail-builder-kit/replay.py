"""Run tiny synthetic CLI fixtures on a disposable, pinned fulltrail builder.

Only XML construction is tested. No encoder, SAT solver, GPU, witness search,
network call or original output file is used.
"""
if not __debug__:
    raise SystemExit("Optimized Python disables expected interpreter controls; run without -O.")
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SOURCE='fulltrail.py'
PIN='1513a08d9ebd015d55070dbac441c9d7bb0be4ddf958ec173bf9cb8ffb979465'
raw=(ROOT/SOURCE).read_bytes()
if hashlib.sha256(raw).hexdigest()!=PIN:
    raise ValueError('Re-read the changed builder edition')
MASK=(1<<32)-1


def reference_expand(words,rounds):
    result=list(words)
    def rot(x,n): return ((x % (1<<n)) << (32-n)) | (x >> n)
    for t in range(16,rounds):
        x,y=result[t-15],result[t-2]
        small0=rot(x,7)^rot(x,18)^(x//8)
        small1=rot(y,17)^rot(y,19)^(y//1024)
        result.append((result[t-16]+small0+result[t-7]+small1) % (1<<32))
    return result


def signed_row(x,y):
    return ''.join('-' if ((x>>i)&1)==((y>>i)&1) else ('u' if ((x>>i)&1) else 'n') for i in range(31,-1,-1))


def parse_rows(raw_xml):
    root=ET.fromstring(raw_xml)
    if root.tag!='config': raise ValueError('Wrong root')
    pattern=r'(-?\d+)\s+A:\s+([?-]{32})\s+E:\s+([?-]{32})(?:\s+W:\s+([un-]{32}))?'
    return root, [(int(t),a,e,w or None) for t,a,e,w in re.findall(pattern,root.find('char').attrib['value'])]


cases=[]
with tempfile.TemporaryDirectory(prefix='hashsmash-fulltrail-audit-') as folder:
    work=Path(folder)
    tool=work/'fulltrail.py'
    shutil.copyfile(ROOT/SOURCE,tool)
    if hashlib.sha256(tool.read_bytes()).hexdigest()!=PIN:
        raise ValueError('Disposable source copy changed')
    def run(label,first,second,rounds):
        pair=work/(label+'.pair'); output=work/(label+'.xml')
        pair.write_text('M1 '+' '.join(f'{x:x}' for x in first)+'\nM2 '+' '.join(f'{x:x}' for x in second)+'\n',encoding='utf-8')
        process=subprocess.run([sys.executable,'-I','-B',str(tool),str(pair),str(rounds),str(output)],cwd=work,
                               capture_output=True,text=True,timeout=10)
        return process, output.read_bytes() if output.is_file() else None
    first=[((i+1)*0x9e3779b9)&MASK for i in range(16)]
    second=first.copy();second[0]^=0x80000001;second[9]^=0x40
    proc,xml=run('valid39',first,second,39)
    if proc.returncode!=0: raise ValueError(proc.stderr)
    root,rows=parse_rows(xml)
    options={o.attrib['name']:o.attrib['value'] for o in root.findall('./options/option')}
    if options!={'f':'sha2','n':'39','w':'32'} or len(rows)!=43:
        raise ValueError('Incorrect declared shape')
    x,y=reference_expand(first,39),reference_expand(second,39)
    for t,a,e,w in rows:
        expected='-'*32 if t<0 or t>=35 else '?'*32
        if a!=expected or e!=expected:
            raise ValueError('Incorrect boundary state row')
        if w!=(signed_row(x[t],y[t]) if t>=0 else None):
            raise ValueError('Expanded W row differs from independent recurrence')
    if signed_row(1,0)[-1]!='u' or signed_row(0,1)[-1]!='n':
        raise ValueError('Source direction changed')
    cases.append({'case':'valid39','exit_code':0,'state_rows_checked':43,'W_rows_checked':39,
                  'W_bit_symbols_checked':1248,'fixture_type':'synthetic, not a collision'})
    proc,xml=run('equal39',[0]*16,[0]*16,39)
    _,rows=parse_rows(xml)
    if proc.returncode or any(w!='-'*32 for t,a,e,w in rows if t>=0):
        raise ValueError('Unexpected equal-pair behavior')
    cases.append({'case':'identical input messages','observed':'Accepted and emits all-equal W rows; builder does not itself reject trivial input.'})
    proc,xml=run('extra_word',[0]*16+[1],[0]*16+[2],39)
    _,rows=parse_rows(xml)
    if proc.returncode or any(w!='-'*32 for t,a,e,w in rows if t>=0):
        raise ValueError('Extra-token behavior changed')
    cases.append({'case':'seventeenth message word','observed':'Silently ignored on both sides.'})
    proc,xml=run('zero_rounds',[0]*16,[0]*16,0)
    _,rows=parse_rows(xml)
    if proc.returncode or len(rows)!=4 or any(t>=0 for t,a,e,w in rows):
        raise ValueError('Zero-round behavior changed')
    cases.append({'case':'R=0','observed':'Accepted; emits the four initial state rows only. No target-profile range check.'})
    wide=[0]*16;wide[1]=1<<32
    proc,xml=run('wide_word',[0]*16,wide,39)
    _,rows=parse_rows(xml)
    if proc.returncode or not any(w!='-'*32 for t,a,e,w in rows if t>=16):
        raise ValueError('Wide-word behavior changed')
    cases.append({'case':'out-of-range 33-bit input word','observed':'Accepted and affects expansion even though the initial printed row shows only low32 bits. Reject such input before use.'})
    proc,xml=run('short',[0]*15,[0]*15,39)
    if proc.returncode==0 or 'IndexError' not in proc.stderr:
        raise ValueError('Short-pair failure behavior changed')
    cases.append({'case':'15-word input','observed':'Fails with IndexError rather than a validated input diagnostic.'})
report={
    'passed':True,'finished_at':datetime.now(timezone.utc).isoformat(),'source':SOURCE,'source_sha256':PIN,'cases':cases,
    'sign_direction':'The inspected writer emits u for first-side bit 1 / second-side bit 0, and n for first-side bit 0 / second-side bit 1. Bind this direction to the chosen encoder; do not assume another tool uses the same convention.',
    'semantic_boundary':'The output fixes schedule difference symbols and asks for common initial and terminal A/E rows. It does not pin the supplied message values, provide a witness, run an encoder or solver, prove the encoding sound, enforce padding, or establish an ordinary standard-IV hash collision.',
    'safe_use_contract':['Supply exactly 16 valid hexadecimal 32-bit words on each M1/M2 line.','Validate a target-supported R externally, and require a nontrivial word difference.','Write only to a fresh output path; the original builder overwrites its destination.','Treat emitted XML as a query specification. Validate the downstream encoder, sign convention and returned numerical pair separately.'],
    'research_search_executed':False,'production_files_changed':False,
    'scope':'Six tiny isolated builder fixtures. A synthetic XML fixture is not a SHA-256 collision or a full-trail feasibility certificate.'
}
print(json.dumps(report,indent=2))
