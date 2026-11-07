#!/bin/bash

# Publication root: stable even when this driver changes working directories.
if [ -z "${HASHCYBERAXE_WORKSPACE:-}" ]; then
  _hca_here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
  while [ ! -d "$_hca_here/research" ] && [ "$_hca_here" != / ]; do _hca_here=$(dirname -- "$_hca_here"); done
  HASHCYBERAXE_WORKSPACE=$_hca_here
fi
export HASHCYBERAXE_WORKSPACE
# build_sparse42.sh : full-state check on the 6 sparse 42-45-step schedule SATs (research/luna/L002/sparse42_fix4.tsv).
# Exact minsup recipe (research/game/climber/guided/minsup/build_run.sh): mk_tap.py writes the xml (W rows lit = words+kicks,
# every other W row equal, state rows 8..R-5 free), sha_cnf.py encodes the full-state SFS instance, kissat decides it.
# These are the second lock on the 82 schedule SATs at 42+: a SAT here = a 42+ step semi-free-start path, beyond the published 39.
# Runs in WSL, nice 10, one lane per shape, 20-min cap each (owner-approved L002 window). Writes SPARSE42_FIX4_RESULTS.tsv.
set -u
M="${HASHCYBERAXE_WORKSPACE}/research/game/climber/guided/minsup"
L="${HASHCYBERAXE_WORKSPACE}/research/luna/L002"
cd "$M" || exit 1
OUT="$L/SPARSE42_FIX4_RESULTS.tsv"; : > "$OUT"
i=0
while IFS=$'\t' read -r R words kicks; do
  [ -n "$R" ] || continue
  n="sp42fix_$i"; lit="$words,$kicks"; rows="8-$((R-5))"
  python3 mk_tap.py "$L/$n.xml" "$R" "$lit" "$rows" || { echo -e "$i\t$R\t$words\t$kicks\tMK_FAIL" >> "$OUT"; i=$((i+1)); continue; }
  REQUIRE_DIFF="${words%%,*}" python3 sha_cnf.py "$L/$n.xml" "$L/$n.cnf" "$L/$n.map" sfs || { echo -e "$i\t$R\t$words\t$kicks\tCNF_FAIL" >> "$OUT"; i=$((i+1)); continue; }
  ( v=$(timeout 1200 nice -n 10 kissat "$L/$n.cnf" 2>/dev/null | awk '/^s /{print $2}'); \
    echo -e "$i\t$R\t$words\t$kicks\t${v:-UNKNOWN_cap1200}" >> "$OUT" ) &
  i=$((i+1))
done < "$L/sparse42_fix4.tsv"
wait
echo "DONE $(wc -l < "$OUT") rows -> $OUT"
