COUNT253 / COUNT278: raw exports and exact saved-data recount

Requirements: Python 3.9+ standard library. No encoder, SAT solver, proof checker,
network, GPU or project checkout is required. This is not an attack program.

Extract the archive, enter count253-278-recount, then run:
  python -I -B replay.py

Expected:
  passed: true
  source_files_recounted: 6
  xml_files: 3
  distinct_XML_byte_editions: 2
  STATE_counts: [261, 236, 236]
  TOTAL_counts: [278, 253, 253]
  whole_query_question_marks: [1, 3, 3]
  fan_rows: 30
  recorded_label_totals: UNSATISFIABLE=24, HELD=6
  proofs_replayed: 0

The original XML and TSV bytes are in originals/. records.json is a derived,
machine-readable projection, not a replacement for the originals. manifest.json
lists the included file hashes; replay.py additionally pins all six originals
before parsing them. The checker is read-only and refuses optimized -O mode.

What the numbers mean

STATE is the literal count of 0/1 value symbols plus u/n/x difference symbols
over all A/E rows, including the four initial rows. Input-W counts those same
symbols in W0..W15. TOTAL = STATE + input-W. Each of these exports has input-W=17.
The filename numbers therefore equal TOTAL, not STATE. No filename declaration
is taken as a formal definition of the historical counter's intended unit.

All three XMLs parse as sha2, n=39, w=32, with 43 row records covering -4..38.
The two differently named COUNT253 XMLs are byte-identical. Each contains three
question marks; COUNT278 contains one. They are not complete masks with no
question marks. The state rows also contain B and/or 7. Their exact backend
relation meanings and costs are not interpreted by this literal counter.
The checker does not declare these extended symbols intrinsically invalid.

What the logs do not prove

The three seed tables have ten rows each: ten recorded UNSAT labels, ten more,
then four UNSAT and six HELD. These are saved labels, not checked certificates.
HELD is undecided. A log filename does not prove which XML, encoder options or
CNF produced the run. Repeated seeds and differently named files are not an
independent-formula or independent-theorem count. No contradiction between the
two COUNT253-name logs is inferred without the exact query identities.

No CNF or proof payload is supplied here. This is not the claimed 54-certificate
collection, and it establishes no feasible characteristic, collision, sampler
yield, attack exponent, global minimum or current contest score.

Credit: the retained numerical exports come from the HASH$CyberAxe team's
research share. The publication audit adds the independent parser/recount,
portable packaging and explicit unit/identity boundaries. No novelty claim.
