Two full-width sparse-B schedules: exact numerical replay

Requirements: Python 3.9+ standard library. Extract the archive, enter
b32-schedule-pairs and run:
  python -I -B replay.py
To emit the complete independently reconstructed numerical projection:
  python -I -B replay.py --emit-projection

Expected: four original export names, TWO distinct unordered numerical pairs,
160 expanded words checked, six forced top-bit relations and two rejected
common-input-word mutations. W13's high bit changes 0-to-1 in the first pair
and 1-to-0 in the second. Both are allowed by the sign-free lemma.

Each message has exactly sixteen hexadecimal 32-bit words. The replay uses
the standard unscaled SHA-256 message expansion through W39. Both pairs have:
  differing input words: 8,9,10,11,13,15
  differing expanded rows: 16,20,25,28,29
All other words through W39 agree. The additive B-minus-A differences and
XOR differences at W13,W20,W29 are exactly 80000000 in each pair.

What is included

originals/ contains the four exact numerical checker outputs from the team's
HASH$CyberAxe export. Each .check_research file is byte-identical to its .check file.
Those aliases are not four independent witnesses or proof of checker independence.
records.json retains both messages, all expanded words, supports, directions
and original hashes. replay.py reconstructs those data independently, rather
than accepting the printed VERIFIED label. It pins the originals in code as
well as in manifest.json. Rehashing a manifest does not substitute a new edition.

To print the second input message of the first pair from the retained projection:
  python -c "import json; d=json.load(open('records.json',encoding='utf-8')); print(' '.join(d['records'][0]['M2']))"
This prints sixteen eight-digit hexadecimal words, not a claimed collision.

What this does NOT establish

The exports contain no chaining value and no compression-state trajectory.
They prove full-width SCHEDULE feasibility, not a compatible full state,
standard-IV collision, legal whole-message padding, trial probability or attack
price. No original encoder, solver, GPU, network or research campaign runs.
The program rejects optimized -O execution. Its temporary-directory packaging
tests are separate from the original research and do not reclassify solver runs.

The associated mathematical lemma forces the top-bit-only relation under exact
sparse-B support. It fixes no u/n sign orientation. The actual numeric examples
illustrate both directions; two examples do not price an attack or prove a
sampler's distribution. Keep original source editions, state feasibility and
complete charging evidence separate.

Credit: the HASH$CyberAxe team's numerical full-width lift exports from the team's sparse-B
research, building on the HASH$CyberAxe team's schedule family. The publication audit supplies
the independent expansion, unordered-pair deduplication, explicit evidence
boundary and portable replay. No novelty or compression-collision claim.
