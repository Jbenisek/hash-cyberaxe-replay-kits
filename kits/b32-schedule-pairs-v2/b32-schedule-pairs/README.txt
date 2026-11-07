Three full-width sparse-B schedule pairs: independent numerical replay

Requirements: Python 3.9+ standard library. Extract the archive, enter
b32-schedule-pairs and run:
  python -I -B replay.py
  python -I -B replay.py --emit-projection

Expected: five original export names, THREE distinct unordered pairs,
240 schedule words recomputed, nine forced top-bit relations and three
rejected common-word mutations. Both W13 high-bit directions occur.
The first two pairs each have a byte-identical _research alias; seed9 has
one exported name. Aliases are not independent witnesses or independent
checker evidence.

Every message contains sixteen 32-bit hexadecimal words. The standard
SHA-256 expansion is recomputed through W39. Each pair differs at exactly:
  Input words: 8,9,10,11,13,15
  Expanded rows: 16,20,25,28,29
The XOR and modular M2-minus-M1 differences at W13,W20,W29 are 80000000.

Example, after running the replay:
  python -c "import json; d=json.load(open('records.json',encoding='utf-8')); print(' '.join(d['records'][2]['M2']))"
The third record is the HASH$CyberAxe team's seed9 pair. records.json preserves all three
input pairs, all expanded words, source hashes and both orientation labels.

No solver, encoder CLI, GPU, network or project checkout is required.
The replay reads numerical exports and uses its own schedule expansion.
It checks manifest/member hashes and reconstructs records rather than
trusting the exported VERIFIED text. Do not run with -O.

Limits: no chaining value or complete state trajectory was supplied. This
does not establish a compression collision, legal padded message, successful
state sampler, independent-condition count or attack price. Finding a schedule
does not price its discovery or prove that compatible states exist.

Credit: the HASH$CyberAxe team's full-width numerical lift exports, using the HASH$CyberAxe team's sparse-B
family. The publication audit adds independent arithmetic replay, deduplication
and this portable edition. The original two-pair edition remains separate.
