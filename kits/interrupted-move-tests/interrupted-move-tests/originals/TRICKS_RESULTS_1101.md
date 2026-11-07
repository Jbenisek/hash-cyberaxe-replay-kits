# Tunnel-move trick tests, 2026-11-01 (MST)

## Which moves gave a better option
None beat baseline. Scoreboard:

| test | move | verdict vs baseline |
|---|---|---|
| T1 work-in R39 core | re-complete rows 10-15 | WORSE: no char in 3x180 s (baseline trail = 276 s); two value checks UNKNOWN 119.6 s |
| T2 word tunnel 39->40 | shift {W0,W4} door | INCOMPLETE: 2 of 16 lanes started, both cut mid-solve (~18 s), no verdict. Launch verified only (s1_w0_4 reproduces HASH$CyberAxe door byte-for-byte). RERUN NEEDED |
| T3 core-pin on p9 (value-UNSAT) | CAP-20 deletion map, then work-in | DARKNESS MAPPED: 18-probe core map done; work-in has no completion (base is value-UNSAT). Signal below |
| T4 lightning head/tail | junction sweep J=8..32 | INCOMPLETE: 2 of 14 lanes started, both cut mid-solve (~13 s), no verdict. RERUN NEEDED |
| T5 keep-one-block 39 | one 4-row block only | SAME: 16/16 UNKNOWN 60 s; no single block fails fast. Signal below |
| T6 snap sweep door40 | rotate r=0..31 | SAME: only r0 undecided; r1-r31 UNSAT 0.6-0.7 s, 0 conflicts. Rotation is not the lever |

## Real signals (diagnostic, not gains)
- T3 core map: the p9 impossibility concentrates. With core rows 8-35 kept, adding rows {6,7} stays fast UNSAT (t012 7.0 s, t013 13.2 s); adding {0-7} alone is UNKNOWN 20 s (t002). Minimal fast-UNSAT core ~= rows 6-27,32-39.
- T5 conflict gradient: late kept blocks reach far fewer conflicts in 60 s (k32/k36 ~113k-205k vs k8-k28 ~340k-497k). The solver stalls hardest on the tail blocks; the contradiction, if any, needs >1 block.

## Next 3 tests, built from the best lead (T3 core map + T5 tail gradient)
1. FAIL HARDER: shrink the T3 core - keep only rows 6-27,32-39 then peel row pairs from the tail (32/33, 34/35, 36/37, 38/39) at CAP 20, find the smallest set that still UNSATs < 10 s (the minimal unsat core = the real wall).
2. INVERT: free ONLY the T5 low-conflict tail blocks together (k32+k36, 8 rows) on S39_CTL/S39_char, 120 s - if freeing the hardest-to-stall region flips to SAT or fast UNSAT, that is the binding region.
3. NEIGHBOURS: finish T2 and T4 first (they never produced a verdict), then word-tunnel the s1_w0_4 HASH$CyberAxe door to its 13 untried free-word neighbours at 120 s (not 60 s - the door needs > 60 s to decide, per T6 r0).

## LEVERS.md
No real gain -> no line appended. All moves were same-or-worse than baseline; T2/T4 unresolved.
