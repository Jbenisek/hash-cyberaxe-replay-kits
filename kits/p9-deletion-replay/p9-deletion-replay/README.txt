P9 row deletion: replay what the saved evidence actually says
===========================================================

Run: python -I -B replay.py
Python 3.9+ standard library. One process, no network, no solver.
The checker reads about 40 MB of saved DIMACS data. It checks structure,
not satisfiability. Do not run with -O, which disables assertions.

Contents
--------
base.xml: the exact retained 40-step, 32-bit p9_f28 source.
t001.xml through t018.xml: the eighteen saved deletion queries.
Seven v_*.xml / v_*.out pairs: saved peel inputs and recorded verdicts.
Five SHA-256-named .cnf files: deduplicated original DIMACS bytes.
records.json: the numeric/source-identity projection linking these artifacts.
manifest.json: byte counts and SHA-256 identities for the archive contents.
replay.py: new finite reconciliation code, not the original experiment driver.

What is corrected
-----------------
The core-map column is the set of FREED rows, not retained rows. t012 retains
0..5; t013 retains1..5. The final greedy result is1..5, relative to all
unchanged W rows and negative-index chaining constraints. The last five
single-row deletions are UNKNOWN. This does not establish minimality.

v_0x27, v_0x31 and v_0x5_6x27 are byte-identical XML and DIMACS. They are
aliases, not three independent formulas. v_0x5_28x31 actually retains0..5:
the starting source already has rows28..31 free. Read content, not names.

What the check does not establish
--------------------------------
The historical UNSAT labels are transcribed, NOT independently certified.
No SAT solver, proof checker, historical encoder or new research run is
executed. Matching a saved XML and CNF inventory does not establish that
the encoder faithfully encoded the intended cryptographic query. These
files do not prove a general 40-step impossibility or attack score.

To upgrade the claim: recover the exact encoder/options/solver identities
and matching proof certificates. To establish a deletion-minimal core,
obtain checked SAT witnesses for each necessary proper deletion, with the
same background constraints. Do not change UNKNOWN to UNSAT.

Rights/scope: project-owned saved numerical research artifacts and a new
reconciliation script. No external paper payload, private chat, deployment
recipe or remote-control script is included. Preserve these evidence limits.
