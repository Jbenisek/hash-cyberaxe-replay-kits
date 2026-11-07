# Query generation and restart semantics: bounded scan-driver lesson

Extract the ZIP, enter `scan-driver-kit`, and run `python -I -B replay.py`.
Python 3.10+ and its standard library suffice. Do not use `-O`.

The kit includes the pinned historical `scan_driver.py` and twelve fixtures.
It extracts five unchanged function definitions with Python's AST and supplies
explicit stand-ins for the encoder, solver, clock and confined filesystem.
It does not import the original schedule encoder, run Kissat, allocate real
research jobs, manage processes or use an existing census. All fixture writes
are inside a newly created temporary directory.

## What is established

- Normal generation uses R and min(R+1,45), not the header's old cap of 41.
  R greater than 45 also generates 45. Validate target ranges before reuse.
- Normal neighbours omit kick R-1; `--self-only` retains it. They are different
  query families, not interchangeable ways to replay an identical experiment.
- Deduplication happens while visiting each target, before global distance
  sorting. An earlier neighbour can therefore displace a later exact target.
- A query permits differences inside W union K and requires only the smallest
  message word to differ. It does not require every listed word to differ.
- With one fixed base and required word, allowed-support SAT transfers upward
  to supersets, and UNSAT downward to subsets. Those directions do not apply
  to a different exact-support problem or a changed base formula.
- Resume skips every stored verdict other than `UNDECIDED`, even `PENDING` in
  a synthetic fixture. Its key omits encoder/environment identity. Use only a
  validated, same-model ledger; this kit does not endorse arbitrary labels.
- A base CNF cached by R can be combined with freshly generated literal maps
  without an identity check. The fixture demonstrates a header/map mismatch.
- The driver trusts status text without requiring a matching process exit
  code. It does not independently check a SAT assignment or UNSAT certificate.
- Pruned rows reuse the preceding solver's statistics fields; they are not
  independent solver measurements. Calibration must report UNSAT and a nonzero
  conflict count. Timeouts remain undecided and climb the configured ladder.

These are interface/control-flow observations, not new cryptographic results
or a recount of historical census verdicts. The stand-in formula is deliberately
tiny and is not SHA-256. A passing replay does not prove encoder equivalence,
solver soundness, campaign completeness or an attack success probability.

## Original environment and reuse boundary

The original imports sibling `sched_scan.py`, which imports `kit/sha_cnf.py`.
The sibling forces schedule-only mode but preserves a pre-existing WBITS value;
it does not unconditionally force width 32. Its historical main uses writable
local base/census files, a Unix temporary location and an installed Kissat.
Those dependencies are not included or executed by this bounded kit.

For a real campaign, preserve the target JSON, exact encoder and dependency
hashes, all effective settings, literal maps, formula identities, solver version
and checked outcome evidence together. Do not treat the old directory cache as
valid for changed code or settings. The publication does not modify or restart
the historical driver or any research process.

The manifest protects the distributed bytes; preparation additionally checks
that changed source bytes and optimized execution fail. It is not a blanket
redistribution license for other tools or external papers.
