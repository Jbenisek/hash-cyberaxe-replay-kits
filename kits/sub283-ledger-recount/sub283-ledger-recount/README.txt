SUB-283 SAVED-LEDGER RECOUNT

Extract sub283-ledger-recount, then run:
  python -I -B replay.py

Python 3.9 or newer; standard library only. No installation, network, solver,
GPU or proof checker is required. The program reads this directory only.
Do not use -O; optimized execution is explicitly rejected.
Expect passed=true, rows_recounted=436, tables_recounted=4, oracle_rows=24,
oracle_labels=20 and proofs_replayed=0. Failures exit nonzero.

The four original TSVs contain 24 oracle rows and 412 generation/probe rows.
Trailing DONE lines are counters, not extra data rows. The checker reconciles
them and preserves every recorded status. Incomplete, gen and ok are saved
generator labels; this kit does not certify their cryptographic meaning.

The source's owner_count STATE unit adds value and difference-bit conditions
over A/E state rows, including chaining rows. It is not log2 attack work, a
success probability or a literature security measure. Counts from incomplete
and unprobed rows must not be promoted to feasible-characteristic records.

SUB283_ORACLE_1101.tsv records 23 UNSATISFIABLE labels and one HELD label.
Those labels are not independently checked proofs. Four find names recur
under different maps; the same name need not identify the same formula.
The manifest proves byte identity only. Its hashes are not signatures.

DRAT266_1101.txt is a 65-byte historical summary. It reports a 309-second solve,
a 527-second check and a proof size written as 299M. No matching CNF or proof
is in this kit. This summary cannot resolve which exact formula was checked,
supersede the oracle's HELD row, or establish a 54-certificate collection.

records.json is a readable projection of the retained rows and exact recounts.
Each input is pinned in replay.py as well as the manifest. The independent
publication audit also tests edited projections with correctly rehashed
manifests: changing a HELD label, an incomplete marker or the certificate
claims is rejected. No historical search is rerun.
