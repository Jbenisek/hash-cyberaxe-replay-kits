SHA-256 ENCODER SELECTOR GUARDS / FINITE COUNTEREXAMPLE

Extract the complete ZIP. Inside selector-guard-kit run:
    python -I -B replay.py
Python 3.9+ standard library; no installation, solver, network or historical
workspace required. Temporary fixture files are created and removed. No
permanent output file is written. Do not use Python's -O mode.

Expected: passed=true, 12 fixtures, four propagator controls. This means the
counterexample and its controls reproduced, NOT that the encoder is correct.

The fixture uses one real 32-bit SHA-256 step, fixed IV and fully pinned
messages. Both are zero except side B W0=1. The two A0 values are fc08884d and
fc08884e. Only A0 bit zero has a guarded equality condition. With all row
selectors false and EQLINK off, the checker constructs a full satisfying
assignment. EQLINK on makes the same instance unit-contradictory. This is
repeated for row, register and bit selector granularity. Enabling the equality
row gives the expected conflict; equal-message controls remain satisfiable.

Why: apply_shape stores an equality seed but not its guard. Later eqlink
asserts the seed after the guard has been cleared. Thus disabling a row does
not disable its equality seed under this combination of options.

This does not disprove historical experiments without inspecting their exact
versions and options. In particular, the counterexample does not refute the
all-selectors-enabled case or independently verified numerical witnesses.
No attack, collision discovery, probability estimate or full encoder audit
is performed. Source files are unchanged. This edition has no reduced-width
or feedforward-output implementation; do not transfer those claims from the
separate retained b887 edition. The archived --selftest is NOT invoked.

The wrapper verifies kit integrity before loading the new checker. The
checker independently pins the original encoder's SHA-256, then uses only a
disposable copy. Missing or changed sources fail closed. No solver required.
