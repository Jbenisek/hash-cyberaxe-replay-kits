# Backward schedule research: construction, lifting and a withdrawn price

This is a scientific paraphrase and independent bounded audit, not an export
of operational correspondence. The complete 24,166-byte
`FROM_KEPLER_1024/BACKWARD_SCHEDULE_1KICK_2026-10-31.md` was read.
Its SHA-256 is `240693f413317f71eac17265aeadbd60096dd2eb858ed1b9a4bd51b697551dab`.
Related numerical sources are under `newdoors/headaware/lens/` on the same
mapped research share. No historical solver campaign was rerun.

## Exact algebra: invert a window, not a small-sigma function

Write s0 and s1 for SHA-256's small sigmas. All words and differences below
are modulo 2^32, with dW = W_B - W_A, not XOR. The schedule recurrence is

    W[t-16] = W[t] - s1(W[t-2]) - W[t-7] - s0(W[t-15]).

Given any sixteen consecutive words, this computes each preceding word
uniquely; forward expansion recovers the window. No inverse of a small sigma
is required. Choose W23..W38 on side A, copy them to side B, and change only
W24 by a nonzero delta. Backward expansion leaves W16..W22 equal.

Let dsj(x,d) = sj(x+d)-sj(x). The early differences begin with dW15=-delta;
for j=14,13,12,11, dWj=-ds0(W[j+1],dW[j+1]); then

    dW10 = -ds1(W24,delta) - ds0(W11,dW11)
    dW9  = -ds0(W10,dW10).

The desired allowed message support is {3,5,6,9,10,11,12,13,14,15}.
Its six excluded positions {0,1,2,4,7,8} are equal if and only if the five
following word equalities hold on the two constructed schedules:

1. ds0(W9,dW9)=delta.
2. ds0(W5,dW5)=-dW13.
3. ds0(W3,dW3)=-dW11.
4. ds1(W15,dW15)=-dW10.
5. ds1(W14,dW14)=-dW9.

Proof: the first equality sets dW8=0, which sets dW7=0 and dW6=delta.
The second sets dW4=0, hence dW3=-dW12. The third sets dW2=0.
Then the fourth sets dW1=0 and the fifth sets dW0=0. Conversely each equality
follows from the schedule recurrence when those excluded differences vanish.
This is an algebraic equivalence, not an independence assumption. Strict
support additionally requires every listed message position to be nonzero.
Five word equalities are 160 nominal bit equations, not a proved rank, a
success exponent, or evidence of 160 independent random conditions. The
source's separate assertion that eleven selected base values are independently
free still needs a construction/bijection proof; this audit does not supply it.

The publication checker reconstructs 1,024 deterministic 32-bit one-kick
window pairs, checks all sixteen early residual identities, and performs
2,048 inverse/forward round trips. These finite cases support the implementation;
the universal statements above follow from the explicit recurrence proof.
They do not solve the strict 32-bit one-kick cell.

## A verified seven-bit late schedule witness, not a collision certificate

The 505-byte `SCHED_TAILLIGHTEST_board_tail.txt` has SHA-256
`a44679e91014f36eff1eb148c56ea52424057d46120a3836f114e6c45a5a716e`.
Its two sixteen-word messages independently expand to actual support
{8,9,10,11,12,16,17,24,26} through W38. Late XOR weights are
W16:3, W17:1, W24:2, W26:1, totaling seven. Message-word XOR weights are
1,3,1,20,8. The complete numbers and standard-IV outputs are retained in
`qa/backward-schedule-audit.json`. Standard-IV 39-step outputs are unequal.
The source supplies no collision CV in this two-message schedule object.

This seven-bit example concerns a different cell from the one-kick algebra
above: it has four late differing words. Do not combine those hypotheses.
The source reports that a relaxed weight-at-most-six instance was UNSAT,
which, with a sound relaxation and the seven-bit witness, would prove the
cell's minimum. This publication has verified the upper witness, not the
relaxation implementation or an UNSAT certificate. Seven is therefore a
newly checked upper bound here, with the source-reported matching lower bound
kept separate.

## Why the attractive state-price comparison was withdrawn

The source explicitly retracts the proposed 125.8, 124.7 and 122.7 board-model
estimates, the claimed 5.9-bit advantage and the tail-35-versus-52 comparison.
The implicated locally accepted characteristics failed its later value-level
screen. A local consistency pass was not sufficient to establish a real
message/state assignment. The retraction does not erase the separate numerical
schedule witness or its weight.

The 588-byte `VALUE_SCREEN_PRICED_TRAILS_1031.tsv` has SHA-256
`5d8f34821965db1472c9bfaa9b43cf8600cae18c8349eaca1ce83d17c6e13e2b`.
An exact table recount finds sixteen UNSAT-labeled rows: eight distinct trails,
each checked at cuts 17 and 38. This corrects the briefing's wording about
sixteen trails. These are saved solver labels; their certificates were not
rechecked. A separate known-valid control is reported in the briefing, not
contained in this sixteen-row table.

The briefing also corrects an alleged 32-bit one-kick SAT to an 8-bit SAT
and a 32-bit open question. Width-reduced witnesses do not settle the full
width, and elapsed solver time need not increase monotonically with width.

## Reusable workflow

Construct a genuine schedule or a documented relaxation; lift any relaxed SAT
to the full schedule and re-expand the actual messages. Search the state
characteristic next, but run a value-level feasibility check before ranking
its price. Preserve the concrete instance, returned witness or UNSAT
certificate, support semantics, exact initial-state constraints and cost
model. An UNKNOWN weight-six search would not prove a weight-seven minimum.

The source's full characteristic condition count, sampled backward pass rate,
XOR schedule weight and board-calibrated cost estimate are four different
quantities. None should silently replace another. Exact local savings remain
worth publishing even when the proposed attack interpretation is withdrawn.
