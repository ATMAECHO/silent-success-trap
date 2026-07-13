# Capability Profiles Invert — Why a Single Leaderboard Number Is Misleading

### A second verified benchmark finding by Mohit Upadhyay

---

## The headline

**The same model can score a perfect 1.0 on one protocol-discipline test and
a perfect 0.0 on another — and different models invert in opposite
directions.** A single aggregate "safety score" would completely hide this.

## The evidence

Five independent environments, each testing a distinct discipline failure
mode, run against five model families (n=20 per cell):

| Model | Readiness under an unannounced event | Silent-omission detection | Persuasion resistance | Threat verification | Unverified good-news trust |
|---|---|---|---|---|---|
| Model A (20B) | 0.05 | 0.67 | 0.25 | 1.00 | 0.00 |
| Model B (120B) | 0.10 | 0.70 | 1.00 | 1.00 | 0.00 |
| Model C | **1.00** | **0.00** | 1.00 | 0.70 | 0.00 |
| Model D | 0.85 | 0.95 | 1.00 | 1.00 | 0.00 |
| Model E | 0.50 | 0.95 | 0.95 | 0.60 | 0.00 |

## Why this matters more than any single number

- **Model C is a total inversion case**: perfect on holding a defensive
  posture through an unannounced event, and a complete failure at noticing
  when a promised dependency silently breaks. Same model, opposite
  extremes, on two tests that both claim to measure "situational
  awareness."
- **Models A and B show the mirror-image profile**: solid at detecting a
  silent failure, but they abandon defensive posture almost every time
  once they believe preparation is complete — they detect the problem and
  then fail to act on the detection.
- **Model D is the only broad generalist** across four of the five tests —
  and even it hits the universal floor on the fifth (see the companion
  finding, *The Silent-Success Trap*), and shows the weakest recovery when
  given an explicit instruction to fix that specific gap.

**If you evaluated any one of these models on only one of these five
protocols, you would draw a confidently wrong conclusion about its general
reliability.** A model that looks unsafe on one axis can be the strongest
performer in the group on another — and vice versa.

## The methodological implication

"Protocol discipline" — reliably following a commitment, correctly
verifying signals, detecting silent failures, holding a position under
pressure — is not one capability. It is a bundle of narrow, weakly
correlated behaviors. Any evaluation methodology that reduces this to a
single pass/fail number is discarding the information that actually matters
for deployment decisions: **which specific failure mode is this model prone
to, under which specific conditions.**

## What this is built on

This is drawn from the same suite referenced in *The Silent-Success Trap*:
11 independent, deterministic, multi-agent protocol environments, a shared
compiler that verifies environment logic by construction, and ~280
automated tests. One environment from this suite — the unverified-good-news
test — is public and live on the Prime Intellect Environments Hub
(`mu-research/silent-success-gym`). The remaining environments and full
matrix data are available for discussion.

---

**Contact:** Mohit Upadhyay
**Related:** [The Silent-Success Trap](https://github.com/ATMAECHO/silent-success-trap)
