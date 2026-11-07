# One convolution: a finite accounting lesson

Extract this archive, enter `xconv-lesson`, then run:

    python -B replay.py

Python 3.10+ and its standard library are sufficient. Do not use `-O`.
No solver, transform allocation, network, original workspace, package build or
submission is invoked. The wrapper reads the kit and prints JSON; it does not
alter the input files. Expected: `passed: true`, 1,011 small composition
candidates, 8,568 impulse cases, and two historical accounting rows.
It also runs six interface controls, including 360 boundary-stage parameter
triples compared against per-index sums under the same charge model.

## The exact local statement

Put m=2K. An input supported on 0..m-1 and a kernel on 1..2m-1 have a
linear product supported within 1..3m-2. We only need coefficients m..2m-1.
For cyclic length L>=2m, all requested coordinates exist, and every wrapped
term lands at most at 3m-2-L<=m-2. It cannot land in the requested window.
Since 3m-2<2L, there is at most one wrap. Consequently cyclic and linear
convolution agree on that window over any coefficient ring.

The index proof is general. The 8,568 small impulse cases are a regression
check, not the sole justification. The weaker condition L>=2m-1 would allow
the final requested coordinate to equal L; this lesson explicitly uses the
stronger condition, satisfied by both historical layouts.

| Profile | K | L | Requested output indices | Largest wrapped index |
| --- | ---: | ---: | --- | ---: |
| r15 | 55,512 | 262,144 | 111,024..222,047 | 70,926 |
| r20 | 173,472,348 | 805,306,368 | 346,944,696..693,889,391 | 235,527,718 |

## What is counted

`geo.py` supplies a finite dynamic program over pass widths 1..7.
`xconv1.py` supplies the power-of-two historical extension count for r15;
`xconv.py` supplies the mixed-radix count for r20. The two project directories
contained byte-identical copies of these three files at review time.

The replay compares the dynamic program to exhaustive compositions for small
inputs. Its optimality is only within that supplied cost table and allowed
widths, not over all possible transform implementations.

### Reusing the counters safely

The fixed historical calls satisfy the layout constraints. The raw APIs do
not fully validate arbitrary new inputs. The added copied-source tests show:

- `geo.runsplit(3,-1,8)` returns an empty plan instead of rejecting the domain.
- Both `phase` functions use `pos//cnt`; a partial final group is uncharged.
  Require positive `cnt` and exact divisibility of `pos` by `cnt`.
- The mixed-radix `xconv.group` accepts both lengths 48 and 49 in the tested
  example because its first step is floor division by three. Require exact
  `L=3*2^a` independently. The power-of-two model needs `L=2^a`, `a>=4`.
- Require positive K and `2*K<=L`, and validate layer counts. Assertions are
  not an input-validation policy when Python can run with `-O`.
- A twiddle subtraction can have a negative coefficient at small batch sizes.
  Historical savings/bound arguments must retain their parameter assumptions.

Run `python -B check_interfaces.py` to inspect these six cases separately.
They are deliberate reproductions of unsupported-input behavior, not repairs
to the historical sources. No large transform or research output is produced.

The ledger fields are:

- `X_OLD`, `X_NEW`: previous and replacement integer extension charges.
- `group`: the pass grouping returned by the supplied counter.
- `N1`, `C1`, `PFX1`: total, stage-C and prefix charges after subtracting
  31 times `(X_OLD-X_NEW)` from their historical baselines.
- `t1`: numerical logarithm of the total charge divided by the profile's
  normalization denominator (531 for r15, 636 for r20).
- `T1`: the saved rounded-up logarithm.
- `S1`: saved time-plus-memory score, using historical memory and score rule.

| Profile | X_NEW | N1 | Saved T1 | Saved S1 | Previous saved score |
| --- | ---: | ---: | ---: | ---: | ---: |
| r15 | 38798611185121190 | 42874961544213795950 | 56.16421 | 90.92629 | 90.94721 |
| r20 | 192142231084688695830 | 191900093359099308848156 | 68.03182 | 114.40225 | 114.42508 |

The integer accounting identities are checked exactly. Floating-point logs
are consistency checks, not independent certified-rounding proofs.

## Lineage and limits

The source dependency records credit akki-rock05's r15 `289da54b` and r20
`6c691173` entries for inherited algorithm, Graeffe prefix and premises;
bradcush's `1aa56884` entry for the one-convolution extension; and earlier
Jbenisek baselines for the underlying ledger. These identifiers are historical
references, not a fresh statement about acceptance or ownership.

The project adaptation recounts the extension under inherited charges.
This publication adds a bounded replay and explanation. It does not claim
invention of Toeplitz embedding, independent proof of inherited attack rates,
kernel implementation, memory law or a route through additional rounds.
Neither baseline proof prose nor papers, PDFs, chats, credentials or package
builders are included. No blanket reuse license is asserted.

`MANIFEST.json` identifies each other file. Altered payloads and disabled
assertions are rejected. A manifest checks identity, not third-party trust:
verify the archive digest against the library's download metadata separately.
