# Three ways to free a trajectory

Inside the extracted newwords-kit directory, run:

    python -B replay.py

Requires Python 3.9+ and the standard library. No installation, original
workspace, network or solver is needed. Do not use Python -O.

The recipe checks four source digests, creates a synthetic 39-step equal-row
template in a temporary directory and invokes only the mkchar transformation.
Nine transformation cases and two char CLI controls must pass. Temporary
fixtures are removed afterwards. Each child has a bounded timeout.

## What changed between versions

All three versions replace every nonnegative W row with question marks.
For a band beginning at row b, they differ in the A/E state rows they free:

| Version | State rows changed by mkchar |
| --- | --- |
| nw.py | None: keep the original A/E characteristic |
| nw2.py | Every nonnegative row before b |
| nw3.py | Only the four rows immediately before b |

Negative initial-state rows and rows at/after the band are retained. The test
uses starts 8, 12 and 16. For b=16, the three free-state sets are respectively
empty, 0..15 and 12..15. The third version retains the second version's opening
comment, but its actual condition is max(0,b-4)<=t<b. Read the implemented
predicate rather than treating copied comments as a specification.

The char CLI branch supplies no band to either nw2 or nw3, so both leave all
A/E rows unchanged. Use the API with an explicit band to obtain those state
relaxations. A question mark permits a difference; it never requires one.

## What this lesson does not do

No synthetic fixture is claimed to be a collision, viable characteristic,
solver result or performance measurement. The full build methods are present
in the unchanged source but are not run. They additionally require attributed
real seed data, characteristic files and sha_cnf.py, none supplied here as a
complete campaign. The profiler module is included only because the scripts
import it; the transformation test does not call its collision profiler.

Historical build methods pin both sides' A/E values across four middle rows
and, in real mode, exclude the ordered pair of sixteen-word messages. Unlike
the board-pair teaching kit, that exclusion does not include the CV. The
chaining label sfs alone does not enforce a shared CV; the input shape must.
Inherited encoder environment settings also matter. Do not run a historical
build method and mistake this finite text test for its full validation.

## Attribution and reproducibility

These are project-authored archived tools with their original comments and
numerical constants preserved. The publication wrapper and fixture are new.
No imported paper, PDF, ordinary conversation or organizer executable is
included, and no blanket reuse license is asserted. MANIFEST.json hashes each
member; download metadata separately hashes the ZIP. This tests source-text
transformation semantics, not discovery novelty or an attack price.
