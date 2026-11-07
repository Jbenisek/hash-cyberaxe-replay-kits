SHA-256 family placements: inspect the saved data, keep the evidence layers apart

Python 3.9+ standard library. No encoder, solver, network, GPU or project checkout.
Extract the ZIP, enter family-places-recount, then run:
  python -I -B replay.py
For the full independently reconstructed projection:
  python -I -B replay.py --emit-projection

Expected saved-data totals:
  map_cells = 344539
  distinct_shape_D_L_families = 205176
  summary_places = 4344
  ranked_word_D_families_at_R_ge40 = 177
  ranked_rows_shift_ge6 = 28
  ranked_rows_shift_ge8 = 22
  proofs_replayed = 0

This kit streams all saved table rows, checks unique cell keys and shift flags,
then reproduces the saved ranking policy. It does NOT regenerate the source
game/search merge, certify source-to-formula identities, run the original
producer programs or independently verify any saved SAT/UNSAT label.
The printed counts describe this pinned edition, not every possible family.

Files
  originals/FAMILY_PLACES.tsv: 344539 saved family/R/shift cells, 22 columns.
  originals/places_summary.tsv: 4344 selected places, 18 columns.
  originals/top_families.tsv: 177 ranked word-support groups, 21 columns.
  dictionary.json: every original column, its interpretation and evidence limits.
  records.json: the exact finite recount and selected shift>=6 context rows.
  replay.py: a standalone copy of the library's independent parser/ranker.
  manifest.json: file hashes. The checker also hard-pins all three original
                 tables and the reviewed dictionary before interpreting them.

There are two different denominators. A D/L shape family uses BOTH normalized
input-word support D and expanded-word support L. A ranked word-D family groups
several such families by D alone. n_trails counts eligible SUMMARY ROWS in that
D group; it is not a number of numerical collision witnesses.

To recover absolute word indices, add y_shift (or y in the summary) to each
normalized support index. The historical flags named board and r39pipe only
test shift>=6 or shift>=8. They are not complete contest-admissibility checks.

Preserve MIXED, CONFLICT, implied labels, CAP, UNK and HELD. The full map has
68 MIXED and 11 CONFLICT cells; the ranked table has 176 SAT and one MIXED row.
A schedule SAT is not a state-level collision. A state-model SAT is not
automatically a value-level pair under the intended initial-state law.
Value-context fields can concern one particular characteristic, not its whole
family. Some are truncated by the original producer.

The ordering favors saved value context, kick count, shift screens, a next-row
wall label, internal evidence tier and recorded runtime. It is not an attack
cost frontier or a proof of maximal height. Solver times and the descriptive
runtime slope must not be read as attack exponents or complexity laws.

For example, inspect at most twelve recorded R40, shift>=8 cells without
loading the full table into a spreadsheet (run from the extracted directory):

python -c "import csv,itertools; f=open('originals/FAMILY_PLACES.tsv',encoding='utf-8',newline=''); rows=csv.DictReader(f,delimiter='\t'); print(list(itertools.islice((r for r in rows if r['x_R']=='40' and r['flag_y8_r39pipe']=='Y'),12)))"

This example does not filter to SAT or assert that any row is a collision.
The full table is about 33 MB uncompressed; the checker uses one process and
memory for unique family/cell keys. No research campaign is launched.

Credit: the HASH$CyberAxe team's family-placement merge and ranking, retaining the attributed
game, schedule and state layers it combines. The publication audit supplies
the standalone recount, field dictionary and explicit interpretation limits.
No novelty, new collision, attack price or complete search-space census claimed.
