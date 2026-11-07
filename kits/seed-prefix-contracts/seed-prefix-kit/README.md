# Seed writer and prefix-checker teaching kit

Python 3.10 or later, standard library only. Extract the ZIP, then run:

```text
python -I -B seed-prefix-kit/replay.py
```

Expected: `passed: true`, four SHA-256/hashlib controls, twelve writer cases
covering 288 rows, fifteen prefix-checker cases, and eight characteristic/meter
cases (with 10-, 17-, 39- and 64-step characteristic fixtures). No solver, network,
GPU or project installation is required. The checks finish in seconds on
the publication machine; no cross-machine timing guarantee is asserted.
Do not use Python's `-O` option: the replay rejects disabled assertions.

## What you learn

The writer converts agreeing pair bits to actual values at selected rows.
Selected or fixed rows take precedence over final-four-row equality.
The nonempty environment value `NOZERO=0` also disables the closing branch.
Different chaining values are accepted; the output is not a common-IV
certificate. A descending selected range is empty, and negative indices
cannot be expressed by the writer's range parser.

`verify_full` adds a useful W-mask check that `verify_cv` lacks. However,
both use the first chaining value for both messages, even when a second
unequal value is present. Unknown symbols are skipped; negative endpoints
pass an empty loop; violated masks print INVALID but still return zero.
The tested maximum inclusive endpoint is 39 for `verify_full` and 38 for
`verify_cv`. The first lacks further round constants; the second CLI always
computes only 39 steps despite its longer constant table.

The suite checks both positive and deliberate negative controls. Therefore
`passed: true` means these interface behaviors were reproduced, not that
the historical checkers rejected all bad inputs. No tested pair is presented
as a new collision, and no archived solver verdict is relabeled.

## Files and safety

The additional `pair2char` checks distinguish signed prefix rows from final
zero-tail requests. Prefix pins win if they overlap the closure window;
`NOZERO=0` disables the tail despite a printed summary still saying zero.
The meter's numerical counts agree with the separate reference in its tested
fixture, but its record handling has limits: rejected different-chain records
reserve IDs, missing IDs collapse, and tied rows with mixed missing/string IDs
can crash sorting. Repeated runs append the same observations to history.
These are reproduced behaviors, not fixes to the historical scripts.

The manifest binds every payload file. The replay also pins the six original
source hashes independently. The three adapted publication tests create and
remove their own temporary directories. They do not change the source files,
write live project tables or run nldtool. The meter's main driver runs only
from an isolated temporary research-tree mirror with synthetic inputs.
`nld_seed` does load the reviewed prefix of `mine_meter.py` up to its sentinel;
that limited behavior is part of the historical contract under test.

Run `replay.py`, not the archived scripts blindly. Original scripts retain
historical defaults and writing entry points for provenance. A standalone
seed-writer call must use an explicit setup and disposable output path.

The independent reference is the project's October 30 SHA-256 implementation;
this kit imports its functions, not its randomized main program. Four known
answers check the reference against `hashlib`; finite agreement is not an
exhaustive implementation proof. See the library's pin/horizon and prefix
checker accounts for domain rules and the exact scientific interpretation.
