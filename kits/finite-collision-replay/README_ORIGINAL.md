# Finite collision replay kit

This kit checks 49 distinct `(target profile, unordered message pair)` records:
16 SHA3-256 five-round-prefix pairs and 33 reduced-partial-round Orchard Poseidon
pairs. Repeated snapshots of the same result are not counted as new discoveries.
It is a finite correctness check, not a proof of attack cost, success rate,
historical priority, contest acceptance, or a full-round cryptographic break.

## Run

Use Python 3.9 or newer. Keep `replay.py` and `data.json` together, then run:

```text
python replay.py
```

No installation, network, original workspace, imported participant code, or
third-party Python dependency is required. The checker reads its adjacent data
file and prints JSON to standard output. It creates no files or worker processes.
Exit code **0** means every check passed; **1** means a mismatch, malformed input,
missing file, or exception. Do not ignore a nonzero exit code or a false `passed`.
The internal deadline is 28 seconds; this finite set normally takes under a second.

Expected output: 49 passing witnesses, 41 passing controls, and six rejected
single-bit mutations (one per target profile). Source and checker SHA-256 values
are printed so a published run can be tied to its exact inputs.

## Exact target conventions

SHA3 uses a zero 1600-bit state, 1088-bit rate, 512-bit capacity, SHA3 suffix
`0x06`, and the final padding bit `0x80`. A 135-byte message therefore becomes
one 136-byte block ending in `0x86`. Lanes are little-endian, indexed `x + 5*y`.
The selected permutation executes **rounds 0 through 4**, not the last five
rounds of Keccak-p. The output is the first 32 sponge bytes. All witness messages
are distinct 135-byte strings and the entire 256-bit outputs are compared.

Poseidon is Orchard P128Pow5T3 over the Pallas base field
`0x40000000000000000000000000000000224698fc094cf91b992d30ed00000001`.
Each message is exactly two canonical 32-byte little-endian field elements;
aliases at or above the modulus are rejected, not reduced. Initial state is
`[m0, m1, 2^65]`. A profile's `r` counts **partial rounds**, plus eight fixed full
rounds: original indices `0..3`, `4..(3+r)`, and `60..63`. Constants are never
regenerated for reduced `r`. Each round adds constants, applies fifth powers to
all three coordinates in full rounds or coordinate zero in partial rounds, then
multiplies by the pinned dense MDS. The entire final coordinate zero, serialized
as canonical 32-byte little-endian data, is the digest. This is not the complete
Orchard nullifier and does not permit a chosen capacity/IV.

## Controls and independence

The fresh checker implements the equations directly and imports no historical
experiment or reference program. Keccak rotations and round constants are
generated algorithmically. Two fixed SHA3 known answers and 15 comparisons with
Python's standard-library `hashlib.sha3_256` test the full 24-round implementation,
including the 135/136/137-byte padding boundary and multiple blocks.

Poseidon uses numerical parameter data pinned to `halo2_poseidon-0.2.0`; eleven
full-56-partial-round permutation vectors and eleven corresponding hash vectors
check its arithmetic and encoding. Two further controls compare the constants
and MDS with a second historical fixture representation. This is a consistency
check, not an independent proof of that fixture's provenance. Finally, the
checker flips bit zero of one message for each of the six reduced targets and
requires the resulting certificate to be rejected.

## Provenance and limits

`data.json` contains only numerical parameters, finite witness strings,
known-answer vectors, provenance hashes, citations, and authored explanations.
It contains no imported executable, full external proof, PDF, or conversation.
Paths in provenance identify historical records only; they are never opened at
runtime. SHA3's witnesses are inherited v20/R7 data: the first fifteen successful
R7 outputs plus `r5-v6-000038`. Later accounting derivatives and duplicate snapshots
are not new witness generators. Source/derivative attribution must travel with
the data. Historical upstream fixtures were not freshly downloaded for this kit.

References: [Keccak specifications summary](https://keccak.team/keccak_specs_summary.html),
[pinned Halo2 Poseidon source tag](https://github.com/zcash/halo2/tree/halo2_poseidon-0.2.0/halo2_poseidon),
and the [historically pinned Zcash test-vector repository](https://github.com/zcash/zcash-test-vectors/tree/78321be).

The test does not assess any claimed statistical success probability or work
ledger. A valid witness can coexist with an invalid or withdrawn attack-price
claim. Publish those distinctions rather than promoting historical package
status from this finite check.
