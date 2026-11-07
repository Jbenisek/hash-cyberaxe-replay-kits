Full-trail XML builder: finite interface controls

This kit checks a retained HashSmash/HASH$CyberAxe query-construction helper, not a
collision or a solver. It includes the exact fulltrail.py edition and a portable
standard-library harness derived from the publication's tested audit.

Requirements: Python 3.9+ standard library. No network, GPU, SAT solver, encoder,
project checkout or installed package is needed. Do not use optimized -O mode.

Extract the ZIP, enter fulltrail-builder-kit, and run:
  python -I -B replay.py

Expected: passed=true, six cases; valid39 checks 43 state rows, 39 W rows and
1,248 signed W symbols. The five other fixtures document accepted identical
messages, ignored extra words, accepted zero rounds, unvalidated wide words
and the short-message IndexError. Those controls are observations of this
edition, not endorsements of invalid inputs. All files written by replay.py
are in a disposable temporary directory. The original builder is run only on
these tiny fixtures; no research driver, encoder or solver is executed.

For direct use, put exactly 16 hexadecimal 32-bit words on each M1 and M2 line
of a PAIRFILE, choose an externally validated target round count R, and invoke:
  python -I -B fulltrail.py PAIRFILE R fresh-output.xml

The included example.pair is the same synthetic valid39 fixture checked by
replay.py, not a collision. To inspect its query XML in a fresh directory:
  python -I -B fulltrail.py example.pair 39 fresh-output.xml
Expect a rows 43 summary and a printed list of differing expanded W rows.

The original builder overwrites its output path. Validate arguments first and
use a new destination. u means first-side bit 1/second-side bit 0 in THIS writer;
n means first-side bit 0/second-side bit 1. Check the downstream encoder's signed
convention separately. A global pair swap is not automatically an invalid
semi-free-start experiment, but it is not the same ordered input witness.

The XML fixes a schedule difference pattern, not the supplied word values.
Initial and terminal A/E rows are equal; middle state rows are unconstrained.
The builder does not prove feasibility, enforce distinctness or padding, price
the resulting search, or produce a standard-IV ordinary hash collision.

manifest.json binds every included file. The checker additionally pins the
original builder's SHA-256 before executing its disposable copy. Changing that
source and rehashing the manifest does not make a new edition reviewed.
Credit: the retained query helper is attributed to HASH$CyberAxe in its source.
The publication audit supplies independent expansion/shape controls and these
usage limits. No general cryptanalytic method or novelty claim is asserted.
