"""Replay seven literal-parser fixtures; hash computation is deliberately stubbed."""
import ast
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import re
import tempfile

HERE = Path(__file__).resolve().parent
if not __debug__:
    raise SystemExit('Run without -O')
manifest = json.loads((HERE/'manifest.json').read_text())
for name, entry in manifest['files'].items():
    assert Path(name).name == name
    raw = (HERE/name).read_bytes()
    assert len(raw) == entry['bytes'] and hashlib.sha256(raw).hexdigest() == entry['sha256'], name
data = json.loads((HERE/'decoder-fixtures.json').read_text())
functions = {}
for edition in ('previous', 'current'):
    tree = ast.parse((HERE/(edition+'-decode.txt')).read_text())
    assert len(tree.body) == 1 and isinstance(tree.body[0], ast.FunctionDef) and tree.body[0].name == 'decode'
    namespace = {'json': json, 'IV': [0]*8, 'sha_ref': lambda *args: (0,)*8}
    exec(compile(tree, '<decoder-fixture>', 'exec'), namespace)
    functions[edition] = namespace['decode']
results = []
with tempfile.TemporaryDirectory(prefix='hashsmash-parser-') as directory:
    folder = Path(directory)
    mapping = {'n':1, 'chaining':'iv', 'W1':[[-1]*32 for _ in range(16)], 'W2':[[-1]*32 for _ in range(16)]}
    mapping['W1'][0][0], mapping['W2'][0][0] = 2, 3
    mapfile, modelfile = folder/'control.map', folder/'model.txt'
    mapfile.write_text(json.dumps(mapping))
    for case in data['cases']:
        modelfile.write_text(case['input'])
        observed = {}
        for edition, decoder in functions.items():
            output = io.StringIO()
            with redirect_stdout(output):
                decoder(str(mapfile), str(modelfile))
            observed[edition] = [int(w,16) for w in re.findall(r'^M[12]: W=([0-9a-f]{8}) ', output.getvalue(), re.M)]
        assert observed == case['expected'], case['name']
        results.append({'case':case['name'], 'first_words':observed})
print(json.dumps({'passed':True, 'decoder_calls':len(results)*2, 'hash_reference_stubbed':True,
                  'fixtures':results, 'scope':'Literal parsing and mapped-word reconstruction only; run replay.cjs for independent numeric witness checks.'}, indent=2))
