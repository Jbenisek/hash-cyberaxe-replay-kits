import sys, os, json, shutil, subprocess, time
# newrow.py <template-dir> <values.json> <row-key> <base-pkg-dir> <out-pkg-dir> [file-rel=template-name ...]
# Builds a package for one row: copies the base package, then fills every template in <template-dir> from the row's
# values. Each template <name>.tmpl is written to the package path given as file-rel=<name> (default: same name at the
# package root, or under the one family folder if the base has one). Prints the wall time.
t0 = time.time()
tdir, vals, row, base, out = sys.argv[1:6]
maps = dict(a.split('=', 1)[::-1] for a in sys.argv[6:])   # name -> file-rel
H = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(out): sys.exit('exists: ' + out)
shutil.copytree(base, out)
fam = [d for d in os.listdir(out) if os.path.isdir(os.path.join(out, d))]
v = json.load(open(vals, encoding='utf-8'))
for t in sorted(f for f in os.listdir(tdir) if f.endswith('.tmpl')):
    name = t[:-5]
    rel = maps.get(name) or (name if os.path.exists(os.path.join(out, name)) or len(fam) != 1 else os.path.join(fam[0], name))
    vf = os.path.join(tdir, name + '.vals.json')
    allv = json.load(open(vf, encoding='utf-8'))
    allv[row] = v[name] if name in v else v
    tmp = os.path.join(out, '.vals_tmp.json'); json.dump(allv, open(tmp, 'w', encoding='utf-8'))
    subprocess.run([sys.executable, os.path.join(H, 'filltmpl.py'), os.path.join(tdir, t), tmp, row, os.path.join(out, rel)], check=True)
    os.remove(tmp)
    print('filled', rel)
print('row %s built in %.2f s -> %s' % (row, time.time() - t0, out))
