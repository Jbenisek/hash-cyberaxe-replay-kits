Six historical tunnel-move tests: transcript and interpretation replay

Python 3.9+ standard library only. Extract the archive, enter
interrupted-move-tests, then run:
  python -I -B replay.py
  python -I -B replay.py --emit-projection

Expected: six rows,18 original table cells,two interrupted partial tests,
ZERO independently replayed solver verdicts,and no minimum-core proof.
The second command emits all original cells,typed reported facts and the
reviewed qualification for each row. It does not run the listed tests.

Example:
  python -c "import json; d=json.load(open('records.json',encoding='utf-8')); print(d['records'][4]['status'])"
Expected: UNKNOWN_NOT_SAT.

T2 and T4 were interrupted after only two planned lanes started. They are
not failed solver queries. T5 reports16 UNKNOWN results at60 seconds; that
does not prove each single-block formula satisfiable or prove that a
contradiction requires multiple blocks. T3's provisional core description
needs the later p9 map corrections. T6's31 recorded UNSAT rotations are
not a general theorem about rotation or new proof-certificate replays.

Data dictionary
- recorded_test,recorded_move,recorded_comparison: exact three source cells.
- source_line: one-based line in the pinned original report.
- status: the publication's qualified interpretation,not a solver verdict.
- reader_group: a navigation category assigned by the reader,not a source fact.
- reported_facts: quantities/labels reported by the historical note. The
  decimals remain strings,and approximate interrupt times remain labelled.
- qualification: what the record does and does not establish.

The original is the project's November1 tunnel-move report; the library
adds exact transcription and qualifications. Later completions have not
been reconciled here. Match exact instances before treating an old row
as closed or requesting a repeat. No new runs are requested by this kit.
Archived proposed tests are historical text,not current operating orders.

No solver,encoder CLI,network,GPU or project checkout is needed. Never use
this six-row transcript as a population estimate,a new collision result,
an attack price,or a universal39/40-step barrier. Do not run with -O.
