import sys, json, re
# filltmpl.py <file.tmpl> <file.vals.json> <row-key> <out-file> : fill a template with one row's values
tmpl, vals, row, out = sys.argv[1:5]
v = json.load(open(vals, encoding='utf-8'))[row]
res = []
for line in open(tmpl, encoding='utf-8').read().split('\n'):
    m = re.fullmatch(r'\{\{(B\d+)\}\}', line)
    if m:
        res.extend(v[m.group(1)])
        continue
    res.append(re.sub(r'\{\{(\w+)\}\}', lambda x: v[x.group(1)], line))
open(out, 'w', encoding='utf-8', newline='\n').write('\n'.join(res))
