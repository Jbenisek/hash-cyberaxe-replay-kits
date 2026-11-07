# Why this signed word cube has 128 equally sized classes

Extract the archive, enter w11-class-kit, and run:

    python -B replay.py

Requires Python 3.10+ and the standard library. No installation, solver,
network, original workspace or NumPy is required. Do not use Python -O.
The input files are read only. Output is JSON on stdout; no search runs.

Expected: rank 7, 128 classes, 65,536 words per class, 8,388,608 total word
inputs, and all 1,152 distributed representatives checked. The program rejects
changed input bytes. It does not assert that these words extend to full messages
or 39-step collisions.

## Exact argument

Use 32-bit words and modular subtraction. Bit zero is the least significant
bit; the signed row is printed most-significant bit first:

    -----uu-------u---n---nn--nn-u--

On u bits X=0 and Y=1; on n bits X=1 and Y=0; on the 23 dash bits they agree
freely. Therefore Y=X xor D, with D=06022334, and simultaneously
Y=X+delta modulo 2^32, with delta=0601dcd4. This identity follows bit by bit
from the signed assignments, not from an independence approximation for carries.

Let S(x)=ROTR7(x) xor ROTR18(x) xor (x>>3), the SHA-256 small sigma0 map.
It is XOR-linear, so S(Y)=S(X) xor T, with T=S(D)=e00141a0. For any words a,T,

    (a xor T)-a = T-2*(a & T)  modulo 2^32.

The intersection's bit 31 contributes zero after multiplication by 2. Thus the
class c=S(Y)-S(X) depends only on V=S(X)&E, where E=600141a0:

    c = T-2*V  modulo 2^32.

E selects bits 5,7,8,14,16,29,30. The 23 free bits of X map affinely to these
seven coordinates. The following seven free input bits give rank seven:

| Free input bit | S(1<<bit) & E |
| --- | --- |
| 23 | 00010020 |
| 21 | 00004000 |
| 19 | 00010000 |
| 16 | 40000000 |
| 15 | 20000100 |
| 14 | 00000080 |
| 11 | 00000100 |

Columns 23 xor 19 isolate bit 5; columns 15 xor 11 isolate bit 29. The other
columns give bits 14,16,30,7,8, so all seven output coordinates are reachable.
There cannot be a higher rank because E contains only seven bits. Each affine
image value consequently has 2^(23-7)=65,536 preimages.

The class mapping is injective on V: 0<=V<2^31, so 2*(V1-V2) is congruent to
zero modulo 2^32 only when V1=V2. There are exactly 128 classes, all with the
same number of words. Under a uniform choice from this precise signed word
cube, each class has probability 1/128. Conditioning on full-message or
trajectory constraints need not preserve that law.

The recount uses 23 linear columns and an image of size 128 instead of visiting
all 2^23 words. The original project classes.py enumerated the whole domain
with NumPy. This is a transparent reconstruction and shorter verification of
that local class count, not a claim to invent linear algebra or a new hash
attack. No wall-clock speedup or contest operation price is asserted.

## Reading the two tables

CLASSVALS3.tsv has 128 rows: class, mx11, status. It supplies one representative
per class, including the source pair's own X=01003fbb in class 2000bea0.
CLASSVALS3_k8.tsv has 1,024 rows: class, mx11, k, status. Each class has eight
additional distinct values, with stored indices k=2..9. None duplicates a
baseline representative. That index is not a solver seed or a probability.

The 22 seen and 106 UNSEEN class labels refer to membership in an older
VALUE_MAP snapshot used by the producer. They are not SAT, UNSAT or failure
verdicts. The second table repeats those labels eight times. The original
second-table sampling seed/generator is not established by this lesson;
rechecking saved values is distinct from reproducing their random selection.

In the historical cube3 encoder, MX is copy 2 and MY is copy 1. Preserve the
orientation if moving these word values to another representation. A valid
word class or representative does not certify full schedule consistency,
shared chaining state, nontriviality, a solver result or digest equality.

## Scope, credit and integrity

The two numerical tables are existing project research, not new witnesses.
The publication checker and this rank proof explain and independently recount
their local invariant. No original research code is modified or launched.
No paper/PDF, ordinary conversation or operational launcher is bundled.
MANIFEST.json hashes each payload; download metadata hashes the archive.
No blanket reuse license or external scientific novelty claim is invented.
