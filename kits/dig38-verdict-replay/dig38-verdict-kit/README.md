# A log, two labels: SHA-256 research provenance

In the extracted dig38-verdict-kit folder, run:

    python -I -B replay.py

Python 3.9+ standard library only. Do not use -O. No installation, network,
solver, original workspace or cryptographic search is needed. Each parser
child has a five-second timeout; temporary fixtures are removed on exit.

The checker pins three historical sources, parses the saved b14R log, and
runs its linked analyzer on a temporary copy. The analyzer prints
NO-VIOLATOR because its final violating class has N=0 and EXACT=0.

The record builder applies a different classifier: if an earlier resampled
stage had surviving violators, it prints NECESSARY even when final N=0.
Extracting only that reviewed verdict function reproduces the exact phrase
recorded in cell C1985. The builder's file-writing top level is NOT run.
Do not run sources/build_records.py as the replay command.

Three small synthetic logs exercise the analyzer's NO-VIOLATOR, NECESSARY
and LEVER? branches. These are parser fixtures, not cryptographic trials.

## What this establishes, and what it does not

The observed label change has a concrete source-level explanation. Preserve
both scripts in the provenance chain instead of treating their labels as
interchangeable. The source label NECESSARY is not itself an exhaustive proof.

The historical log contains counts, probabilities, confidence intervals and
an assertion of independent hashing. This replay checks saved text and the
classifiers; it does not rerun those experiments, verify the historical
message pairs, establish a sampling law or prove the printed 1+3/8032 bound.
The logged process resamples particles. An IID statistical argument needs
its own justification and cannot be assumed from a large raw sample count.

## Files and credit

Project-authored historical sources retain their exact checked bytes and
comments. The publication wrapper and synthetic fixtures are new. The
manifest identifies every member; the private preparation report identifies
the ZIP. No PDF, ebook, ordinary conversation or organizer program is included.
This package makes no claim of a new collision, contest score or blanket
third-party redistribution license. Historical records are not overwritten.
