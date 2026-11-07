import sys, json, re
# extract.py <file.tmpl> <real-file> <row-key> <out-vals.json> : read one row's slot values out of a real file
# (the template must fit the file: fixed text identical, numbers in the number slots). Exit 1 if it does not fit.
tmpl, real, row, out = sys.argv[1:5]
NUM = r'(?:\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b|\b[0-9a-f]{8}\b|\d[\d,]*(?:\.\d+)?(?:e-?\d+)?)'
parts = []
for line in open(tmpl, encoding='utf-8').read().split('\n'):
    m = re.fullmatch(r'\{\{(B\d+)\}\}', line)
    if m: parts.append('(?P<%s>(?:[^\n]*\n)*?)' % m.group(1)); continue
    m = re.fullmatch(r'\{\{(W\d+)\}\}', line)
    if m: parts.append('(?P<%s>[^\n]*)\n' % m.group(1)); continue
    seg, pos = [], 0
    for x in re.finditer(r'\{\{(s\d+)\}\}', line):
        seg.append(re.escape(line[pos:x.start()])); seg.append('(?P<%s>%s)' % (x.group(1), NUM)); pos = x.end()
    seg.append(re.escape(line[pos:]))
    parts.append(''.join(seg) + '\n')
text = open(real, encoding='utf-8').read() + '\n'
m = re.fullmatch(''.join(parts), text)
if not m: print('DOES NOT FIT', real); sys.exit(1)
v = {}
for k, val in m.groupdict().items():
    v[k] = val.split('\n')[:-1] if k.startswith('B') else val
json.dump({row: v}, open(out, 'w', encoding='utf-8'), indent=0)
print('extracted', len(v), 'values for', row)
