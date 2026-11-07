# Standard-IV prefix examples: replay the actual conditions

> **By Jeremy Benisek ([CyberAxe](https://cyberaxe.dev/))** · part of **[HASH$CyberAxe](https://hashcyberaxe.com/)** open research
>
> Research library: [hashcyberaxe.com](https://hashcyberaxe.com/) · Tools & data: [hashcyberaxe.com/tools.html](https://hashcyberaxe.com/tools.html) · Play the game: [hashcyberaxe.com/game](https://hashcyberaxe.com/game/)

**What this is for.** Standard-IV prefix examples: replay the actual conditions. This kit reproduces it from the saved data and checks the result; see the original instructions linked below.

**Credits.** Author: **Jeremy Benisek (CyberAxe)**: research direction, questions and project lead. Made with AI research and coding agents working under CyberAxe's direction; the agents are tools, not authors. Third-party code keeps its original authors and notices ([../../AUTHORS.md](../../AUTHORS.md)).

**License.** See [LICENSING.md](LICENSING.md). Credit: "Jeremy Benisek (CyberAxe), HASH$CyberAxe, https://hashcyberaxe.com/".

Part of the HASH$CyberAxe research tools and reproducibility collection.

## Start here

Read the included [original instructions](prefix-pairs-kit/README.md) for the scientific method, inputs, examples and expected results.

## Requirements

Python 3.11 or newer runs the included integrity checker.

The finite replay uses Python; see the original instructions for any source-specific dependencies.

## Check and run

From this project root:

```sh
python -B check_project.py
python -B check_project.py --replay
```

The second command checks the files, runs this exact finite entry point and rejects a nonzero exit or mismatched result:

```sh
python -B prefix-pairs-kit/replay.py
```

Current packaging-run results are in `VERIFICATION.json`. The check has a bounded timeout and does not launch historical search campaigns.

## Files, provenance and reuse

`PROJECT.json` records the original archive hash and the exact entry point. `ORIGINAL_FILES.json` maps every preserved payload file to its source identity. A root original README, when present, is named `README_ORIGINAL.md`; scientific code and data bytes are unchanged.

`FILES.sha256.json` pins this prepared edition. [RIGHTS.md](RIGHTS.md) explains retained source credits and licensing. Scientific result scope is documented in the original instructions.

## Source

Prepared from the HASH$CyberAxe research library (https://hashcyberaxe.com/) by its publication process; `PROJECT.json` and `ORIGINAL_FILES.json` record the original archive and file identities.

**Public edition.** 1 file was edited for this edition: agent names replaced with HASH$CyberAxe credit and owner quotes with CyberAxe. [PUBLIC_EDITION_EDITS.json](PUBLIC_EDITION_EDITS.json) lists each file, why, and its original SHA-256.
