# When the template proves the wrong thing

This is a finite SHA-256 model-audit lesson, not a collision search. It compares
the saved eleven L005 shapes with two state-window recipes. No shell launcher,
encoder or SAT solver is executed. The historical shell files are included for
source inspection only; do not run them.

## Replay

Extract the ZIP into a disposable directory. In `early-state-kit`, run:

```text
python -I -B replay.py
```

Python 3.10 or later, standard library only. No network, compiler or solver is
needed. The replay checks payload identities, copies the tiny XML generator to
a temporary directory, generates 22 small templates, and removes those temporary
files on exit. It does not write to the extracted research files. Do not use `-O`.

Expected: `passed: true`, 11 saved shapes, 22 templates, eight old
first-difference contradictions, three shapes not excluded by that particular
obstruction, and 65,536 toy additive-injectivity controls. The unsorted-input
control also shows that taking the first comma-separated word is not generally
the same as taking the minimum. All eleven saved rows are sorted.

## Why the contradiction is exact

Let p be the first allowed differing schedule word, required to differ. The
initial states and all W rows before p agree, so the states entering step p
agree. At that step both new words have the form

```text
A_p = alpha + W_p  (mod 2^32)
E_p = epsilon + W_p  (mod 2^32)
```

Here alpha and epsilon are identical on the two sides. Addition by a fixed
constant is bijective. Therefore a nonzero word difference at p forces both
A_p and E_p to differ. A template that also forces those words equal is
inconsistent, independently of the late collision conditions.

For eight saved shapes p is below 8, so the old state window starting at 8 has
this contradiction. Starting at p removes it. The other three start at 8 and
are unchanged by this repair. Neither observation proves that a corrected
template is satisfiable or that it yields a full-width collision.

## What the launchers do, and why not to run them here

The old launcher overwrites its summary, can launch one solver per row without
a global cap, and folds missing solver output into UNKNOWN_cap1200 without
distinguishing timeout from error. The corrected launcher uses the first listed
word, launches all rows concurrently without a search cap, and can report a
finished solver almost 30 minutes late. Its elapsed time includes that delay.
A decoder's equal-output text is not a substitute for checking a complete
assignment and independently replaying a nontrivial collision.

The included source bytes are unchanged. This teaching wrapper and checker are
new publication work. Historical attribution and any artifact-specific rights
remain with their sources; this bundle makes no blanket license or novelty claim.
