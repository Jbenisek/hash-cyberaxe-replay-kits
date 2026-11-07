#!/bin/bash

# Publication root: stable even when this driver changes working directories.
if [ -z "${HASHCYBERAXE_WORKSPACE:-}" ]; then
  _hca_here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
  while [ ! -d "$_hca_here/research" ] && [ "$_hca_here" != / ]; do _hca_here=$(dirname -- "$_hca_here"); done
  HASHCYBERAXE_WORKSPACE=$_hca_here
fi
export HASHCYBERAXE_WORKSPACE
# run_fullstate_fix.sh : full-state checks REDONE with the state free from the shape's FIRST differing word (not row 8).
# Bug found 10-27 ~22:20: mk_tap state-free start 8 + a differing word < 8 = impossible by construction (A_p must differ when W_p does),
# so the ms41/42/43/41b/43b and sparse42 UNSATs were artifacts. 11 instances (Descent's 41-43 minimal supports + the 6 sparse 42-45 shapes).
# State rows free from min(words) to R-5, require the first word to differ. NO cap (decision runs uncapped); each lane posts a RUNNING
# line every 30 min and its verdict on finish to RESULTS.tsv; a SAT is decoded and checked (outputs equal). nice 10, one lane each.
# Built by HASH$CyberAxe; Luna queues it.
L="$(cd "$(dirname "$0")" && pwd)"; M="${HASHCYBERAXE_WORKSPACE}/research/game/climber/guided/minsup"; OUT=$L/RESULTS.tsv; : >> $OUT
lane() { n=$1; R=$2; w=$3; k=$4; f=${w%%,*}; x=$L/$n
  python3 $M/mk_tap.py $x.xml $R "$w,$k" $f-$((R-5)) >/dev/null && REQUIRE_DIFF=$f python3 $M/sha_cnf.py $x.xml $x.cnf $x.map sfs >/dev/null || { echo -e "$n\t$R\tBUILDFAIL" >> $OUT; return; }
  t0=$(date +%s); nice -n 10 kissat -q $x.cnf > $x.out 2>&1 & k2=$!
  while kill -0 $k2 2>/dev/null; do sleep 1800; kill -0 $k2 2>/dev/null && echo -e "$n\t$R\tRUNNING\t$(( ($(date +%s)-t0)/60 )) min" >> $OUT; done
  wait $k2; rc=$?; case $rc in 10) v=SAT;; 20) v=UNSAT;; *) v=ERR$rc;; esac
  [ $v = SAT ] && { python3 $M/sha_cnf.py --decode $x.map $x.out > $x.chk; grep -q "outputs equal: True" $x.chk || v=SAT_CHECKFAIL; }
  echo -e "$n\t$R\t$v\t$(( ($(date +%s)-t0)/60 )) min" >> $OUT; }
while IFS=$'\t' read -r n R w k; do lane "$n" "$R" "$w" "$k" & done < $L/shapes.tsv
wait; echo "L005 DONE"
