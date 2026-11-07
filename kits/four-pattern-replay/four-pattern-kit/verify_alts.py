
# Publication path adapter: resolve data paths from the extracted source tree.
def _hca_public_path_text(value):
    if "__HCA_WORKSPACE__/" not in value:
        return value
    import os as _hca_os
    from pathlib import Path as _hca_Path
    root = _hca_os.environ.get("HASHCYBERAXE_WORKSPACE")
    if root is None:
        here = _hca_Path(__file__).resolve().parent
        root = next((str(p) for p in (here, *here.parents) if (p / "research").is_dir()), None)
    if root is None:
        raise FileNotFoundError("Extract the research source tree, or set HASHCYBERAXE_WORKSPACE to its archive directory.")
    return value.replace("__HCA_WORKSPACE__/", str(_hca_Path(root).resolve()).replace("\\", "/") + "/")

import sys,json
sys.path.insert(0,_hca_public_path_text('__HCA_WORKSPACE__/research/tighten/r37_unforced_files'))
import sha256_ref as R
d=_hca_public_path_text('__HCA_WORKSPACE__/research/tighten/r37_unforced_files/')
for n in ['alt_G1','alt_G2','alt_G12','i_all52']:
    j=json.load(open(d+n+'_verify.json'))
    iv=[int(x,16) for x in j['CV']]
    mx=[int(x,16) for x in j['MX']]; my=[int(x,16) for x in j['MY']]
    ox,sx,_=R.compress(mx,iv,37); oy,sy,_=R.compress(my,iv,37)
    e=lambda s,t,b:(s[t][4]>>b)&1
    print(n,'37-step equal:',ox==oy,'E18[1],E18[10] (row18 0-based idx?)',[(t,e(sx,t,1),e(sx,t,10),e(sx,t,29)) for t in (17,18)])
