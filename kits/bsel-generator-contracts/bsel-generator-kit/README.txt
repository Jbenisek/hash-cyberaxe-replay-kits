BLAKE3 / MASKED WALK AND RETAINED GENERATOR REPLAY

Extract the entire ZIP. Open a terminal inside bsel-generator-kit and run:
    python -I -B replay.py
Requirements: Python 3.9+ and Node.js with WebAssembly support on PATH.
No installation, network, historical workspace or original research run is
performed. Do not use -O. The source and wasm are unchanged pinned bytes.

Expected: passed=true, instructions_checked=11718, register_extent=771,
compiled_chunks=6, negative_controls_rejected=2, wasm_calls_compared=2.
The wasm declares minimum 3 / maximum 16 pages; tested linear memory is
196608 bytes. Every emitted record and the mask q must match the fresh
Python program on both calls. The module has no imports. A subprocess
deadline bounds the generator replay. The original source's selftest,
stats and plan search are NOT called.

The structural check validates each generated expression and every register
operand/output, plus the connections between compiler chunks. Induction over
these instructions proves that this generated straight-line program and its
allocation agree for arbitrary plane inputs. The wasm emits the same records.
Select is interpreted as b XOR (s AND (a XOR b)); a one-operation select price
is a separate machine convention, not measured by this replay.

This is not a fresh C-to-wasm build or a universal proof of the hash generator.
It is not an independent digest-reference replay, a native host-RSS bound,
fuel/instruction-price certificate, collision search or success-law proof.
The larger library documents separate finite independent digest comparisons.
The organizer reference and external papers are not bundled.

Credit: the archived source attributes g=f XOR q to jungjipdo's 6ae36351
proof 3.4 and implements its own select-adder variation. All original source
credits remain intact. No external implementation is included by this kit.

File hashes and hardcoded source/wasm pins reject missing/altered payloads.
Integrity is not authorship authentication: use the library's archive SHA-256.
The replay prints JSON and creates no permanent output file.
