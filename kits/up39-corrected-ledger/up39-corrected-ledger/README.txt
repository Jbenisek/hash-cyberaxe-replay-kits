UP39 corrected job ledger: saved receipts, not new verdict proofs

Thirteen recorded jobs include two blank table rows. The original ledger
contains explicit corrections for p5 and p7. This kit retains that table and
both complete saved Kissat logs, including their attribution banners.
No solver executable, source code, CNF formula or proof certificate is bundled.

Original folder: research/game/climber/guided/d6full_head/sat5/up39/.
originals/p5.out and originals/p7.out are byte-identical aliases for
UP39_d1f818b92f02_p5_kissat.out and UP39_d1f818b92f02_p7_kissat.out.
records.json preserves those original paths and all three source fingerprints.

Python 3, standard library only:
  python -I -B replay.py
  python -I -B replay.py --emit-projection

The corrected labels are SAT=1, UNSAT=3, UNKNOWN=9. These are reported solver
labels, not independently certified formula results. The SAT control is not
a verified message collision. Job names are preserved as labels; their text
does not certify the actual encoded round count or the number of distinct
formulas. No condition minimum or construction cost follows from this census.

p5: the explicit correction says UNSAT, 421,013 conflicts, 43s process-time.
The saved log contains the UNSAT response, 421,013 conflicts, 43.36 process
seconds and exit code 20. p7: the correction says UNKNOWN at a 900s cap, with
7,154,632 conflicts at the 879.25s progress line. Its complete saved log has
SIGTERM and 898.67 final process seconds, but no terminal solver-response line.
The blank return-code field remains unrecovered; do not invent 124 from other jobs.
The cap, progress figure and process time are not interchangeable timings.

Example after a successful replay:
  python -c "import json; print(json.load(open('records.json'))['reported_counts'])"
Expected: {'SAT': 1, 'UNSAT': 3, 'UNKNOWN': 9}

Every original is pinned independently of the manifest, and records.json is
reconstructed from the original rows, correction text and saved logs. Changing
a source and merely rehashing the manifest does not make it a reviewed edition.
The replay checks historical transcription and reconciliation only. It never
launches Kissat or any research driver, and does not prove that a named log
was produced from a currently retained formula of a matching filename.
