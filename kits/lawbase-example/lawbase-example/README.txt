LAWBASE: FROM A MESSAGE PAIR TO A SEARCH BASE

Purpose
This kit documents an existing project helper, not a new collision or attack.
The original lawbase.py comes from the FROM_HENSEL_1102_B32 research delivery.
Its exact bytes and the existing public seed-9 schedule input are fingerprinted.
No raw agent/user conversation, solver, external ebook or project credentials
are included.

Requirements and replay
Python 3.9+ and its standard library. No network, mapped drive, solver or GPU.
From the extracted lawbase-example directory, run:

    python -I -B replay.py

Expected JSON includes passed=true, state_rows=44,
signed_schedule_words_checked=40, source_generator_invocations=2,
mismatched_E_argument_also_accepted=true, solver_runs=0 and collision_checks=0.
The harness writes generated files only inside a fresh temporary directory.
To print the independently reconstructed contract, use --emit-projection.
Optimized Python (-O) and other arguments, including --launch, are refused.

Original interface
Use a fresh output destination: the original writer overwrites that file.
For example, from the kit directory with no existing fresh-base.xml:

    python -I -B originals/lawbase.py originals/LIFT_s9.check fresh-base.xml 40 29

The pair file supplies M1 and M2, each with sixteen hexadecimal 32-bit words.
The last two arguments select the requested row count R and a caller-supplied E.
This example has its last differing expanded W word at row 29.

What the example checks
The XML options are f=sha2, n=40 and w=32. Rows -4..-1 have equal A/E relations.
On nonnegative rows, A is free on 0..21 and equal from 22; E is free on 0..25
and equal from 26. All forty signed W words match the previously replayed public
seed-9 schedule. '-' denotes equality, '?' leaves a state relation free, and
u/n distinguish the two directions of an active schedule bit.

The original writer accepts E=28 for the same input. It does not check that E
is the intended last-active-row parameter. That caller obligation must not be
silently promoted into a validated finish-law theorem.

Boundaries
The output is a query template, not a solved state or numerical collision.
The source does not explicitly supply complete message or standard-IV value
assignments. Signed active bits constrain values; the remaining equations and
downstream encoder/profile still need their own checks. This replay does not
establish legal padding, satisfiability, a condition rank, success probability
or attack price. Printed equal/free symbols are not independent conditions.

originals/example-R40-E29.xml preserves the captured Windows byte edition.
Generated newline bytes can differ on another operating system. The harness
normalizes CRLF/LF for comparison and also checks every parsed row and symbol.
The golden-b32-records.json file is the exact previously published three-pair
record edition; only its seed-9 pair is used here. Its other pairs do not become
new tests of lawbase or new collision results merely by being present.

Inventory
replay.py, README.txt, records.json, manifest.json, golden-b32-records.json,
originals/lawbase.py, originals/LIFT_s9.check and originals/example-R40-E29.xml.
The manifest covers every file except itself. Original source/input/golden
edition pins are also enforced independently inside replay.py.
