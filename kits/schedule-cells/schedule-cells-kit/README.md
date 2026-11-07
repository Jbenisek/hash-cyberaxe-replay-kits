# When a condition has already been paid

Extract this archive, enter `schedule-cells-kit`, and run:

```text
python -I -B replay.py
```

Python 3.10+ and the standard library suffice. No solver, network, compiler or
original project drive is needed. The wrapper checks pinned payload bytes and
runs the copied script in temporary directories with ten-second limits. Do not
use `-O`: assertions are part of this finite replay, and the wrapper rejects it.

## The exact local object

The SHA-256 schedule recurrence is

```text
W17 = sigma1(W15) + W10 + sigma0(W2) + W1  (mod 2^32).
```

Use the source's orientation: difference means x minus y, `u` means (1,0), and
`n` means (0,1). When W1 and W2 agree, W10 has difference `fff80c00`, and W15
differs only by changing x's bit 29 from one to zero in y, cancellation requires

```text
sigma1(x) - sigma1(y) = 0007f400.
```

The pinned characteristic admits 32 distinct x values for W15. Every one
satisfies this equation. The source prints 32/32; the wrapper separately checks
distinctness and uses an independent bit-index implementation of sigma1.

## Why the broader word model gives exactly one eighth

Flipping input bit 29 changes only sigma1 output bits 10, 12 and 19. The
required modular difference has signs + at bit 19, - at bit 12 and + at bit 10.
With x29=1, these requirements reduce to three disjoint parity equations:

| Changed output bit | Required sign | Condition on free input bits |
| --- | --- | --- |
| 19 | + | x4 = x6 |
| 12 | - | x22 != x31 |
| 10 | + | x20 = x27 |

Six free input bits determine the signs. The three equations have rank three,
so eight of their 64 assignments work. The other 25 free word bits do not
change the signed difference: the unchanged output bits cancel numerically.
Thus exactly 2^28 of the 2^31 words with x29=1 meet this local cancellation.

The admitted 32-word list is already inside that successful set. Its conditional
cancellation rate is one, not a fresh factor-eight improvement. This proves
only the local schedule statement under the displayed conditions, not a full
compression collision or the success law of a complete attack.

## Eight controls and two important interface warnings

The replay checks the original enumeration, an independent bit-formula/rank
calculation, a missing characteristic, an incorrect working directory, a
31-member list, the wrong bit-29 orientation, duplicate list members, and a
deliberately modified early word.

The last two are tests of limitations, not claims that the original rejects
them. A list containing one value repeated 32 times still prints 32/32. And a
modified early row with nonzero W3 difference still receives the source's
hard-coded zero-difference prose. Those inputs show why this script is not a
general characteristic verifier. The pinned original input passes the stronger
wrapper checks; changing a source file is not a supported way to extend its proof.

The original reads `../../chi/chi37.txt` relative to the current working
directory, not its own filename. Run the wrapper to avoid accidentally reading
another experiment's characteristic. It never modifies research originals.

## Provenance and limits

Project sources: `research/tools/traillab/atlas_runs/derive-sched-inverse-expansion-B/check_cells.py`
and `research/tools/traillab/chi/chi37.txt`. The characteristic file credits the
published chi37 lineage and records its erratum; its source comments remain
part of the exact edition. This lesson documents the project's local dependency
check, not discovery of the underlying characteristic or a new SHA-256 record.
No external PDF is included and no blanket third-party license is asserted.

The early-word statements concern contributions to W19/W20/W21, not all possible
values of those complete rows. The saved example expansion is finite evidence;
no compression replay, sampling experiment or attack-price proof is performed.
Match the ZIP hash to library metadata as well: its internal manifest is an
integrity check, not an external signature.
