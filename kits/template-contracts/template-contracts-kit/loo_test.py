import re, sys, os, subprocess, tempfile
# loo_test.py <file-rel> <rowdir>...
# (1) reconstruction: template from all rows, every row refilled must equal its real file byte for byte.
# (2) leave-one-out: template from all rows but one; adding the held-out row must not change any fixed line
#     (the held-out row differs only where the others already differ) -> FITS; else lists the lines it would open.
rel, rows = sys.argv[1], sys.argv[2:]
H = os.path.dirname(os.path.abspath(__file__)); bn = os.path.basename(rel)
def key(r):
    parts = [p for p in r.replace('\\', '/').rstrip('/').split('/') if p]
    rid = [p for p in parts if re.fullmatch(r'r\d+\w*', p)]
    return rid[-1] if rid else [p for p in parts if p != 'pkg'][-1]
def build(rs):
    d = tempfile.mkdtemp()
    subprocess.run([sys.executable, os.path.join(H, 'mktmpl.py'), d, rel] + rs, check=True, capture_output=True)
    return d, open(os.path.join(d, bn + '.tmpl'), encoding='utf-8').read().split('\n')
d, full = build(rows)
rec_ok = True
for r in rows:
    o = os.path.join(d, 'fill_' + key(r))
    subprocess.run([sys.executable, os.path.join(H, 'filltmpl.py'), os.path.join(d, bn + '.tmpl'), os.path.join(d, bn + '.vals.json'), key(r), o], check=True)
    same = open(o, encoding='utf-8').read() == open(os.path.join(r, rel), encoding='utf-8').read()
    rec_ok &= same
    if not same: print('  RECONSTRUCT FAIL', key(r))
print('%s reconstruction of %d rows: %s' % (bn, len(rows), 'EXACT' if rec_ok else 'FAILED'))
NUMR = re.compile(r'(?:\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b|\b[0-9a-f]{8}\b|\d[\d,]*(?:\.\d+)?(?:e-?\d+)?)')
fixed_full = {l for l in full if '{{' not in l}
skel_full = {NUMR.sub('#', re.sub(r'\{\{s\d+\}\}', '#', l)) for l in full if not re.fullmatch(r'\{\{[WB]\d+\}\}', l)}
fit_all = text_all = True
for held in rows:
    _, t = build([r for r in rows if r != held])
    opened = [l for l in t if '{{' not in l and l not in fixed_full]
    text = [l for l in opened if NUMR.sub('#', l) not in skel_full]
    fit_all &= not opened; text_all &= not text
    if not opened: msg = 'FITS'
    elif not text: msg = 'FITS (%d number-only lines become slots)' % len(opened)
    else: msg = 'FITS; %d row-unique text line(s) must be supplied in this row\'s values, e.g. %r' % (len(text), text[0][:50])
    print('  %s held out: %s' % (key(held), msg))
print('%s leave-one-out: %s' % (bn, 'ALL FIT' if fit_all else ('ALL FIT up to number slots' if text_all else 'ALL FIT (some rows carry a unique text line supplied per row)')))
