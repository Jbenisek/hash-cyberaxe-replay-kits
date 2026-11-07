Historical r39 memory ledger: numerical replay

This is an excerpt of section 6 of the project's r39_proof_s6_s7.md edition,
not a new attack or a certification of that historical submission.
Only the original memory section is included; no participant chats or ebooks.

Run with Python 3, standard library only:
  python -I -B replay.py
  python -I -B replay.py --emit-projection

The 13 declared entries sum to 1,042,624 bytes, leaving 5,952 bytes below
1,048,576. Packed records and instruction-storage arithmetic are also exposed.
The source charges 28,704 bytes for a queue labelled 3,584 pairs x 8 bytes.
The payload product is 28,672: the extra 32 bytes are preserved as an
unexplained allowance, not removed or invented as a proved header layout.

Register arithmetic is reported from the source, not independently proved
from the compiled program. No program, compiler, SAT solver, research driver
or historical attack is executed. The source's hand counts, liveness, aliasing,
scratch reuse, instruction census and actual peak remain outside this replay.
The 32-byte word-storage units are those declared by this historical ledger;
they are not ordinary native CPU register sizes.

Machine-readable records.json separates declared values from computed totals
and explicit unverified properties. Example after a successful replay:
  python -c "import json; print(json.load(open('records.json'))['headroom_bytes'])"
Expected output: 5952

A digest manifest detects accidental changes; the source excerpt's independent
digest pin and exact reconstruction also reject a rehashed fabricated result.
Passing this replay is not evidence that this is a current or accepted price.
