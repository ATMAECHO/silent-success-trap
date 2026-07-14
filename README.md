# The Silent-Success Trap

### A verified benchmark finding by Mohit

---

## The headline

**Every frontier-class open model tested — 5 model families, 20B to
trillion-parameter scale — failed the same verification trap 200 times out
of 200.**

Not once. Not a majority. **Zero survivors, across every model, in every
condition tested.**

## The trap, in one sentence

Models will double-check a threat before acting on it — but they will act
on good news immediately, without checking it, even when checking would
have taken one extra step.

This is not a minor quirk. It is a **structural blind spot**, and it is
consistent, measurable, and — critically — **fixable in a single sentence**.

---

## The numbers

| Model | Verifies threats correctly | Verifies good news correctly |
|---|---|---|
| gpt-oss-20b | 100% | **0%** |
| gpt-oss-120b | 100% | **0%** |
| qwen3-30b | 70% | **0%** |
| kimi-k2 | 100% | **0%** |
| glm-4.6 | 60% | **0%** |

Every single model shows the same asymmetry: skeptical of bad news,
credulous of good news. This pattern holds regardless of vendor, scale, or
architecture.

## Why it happens (the root cause, not just the symptom)

We didn't just measure the failure — we diagnosed it. Behavioral analysis
of 200 failed attempts shows:

- **95% of the time, models attempt a verification action** — so this is
  not laziness or a missing capability.
- **97% of the time, they act on the unverified signal anyway.**
- **0% of the time do they verify in the correct order** — they check
  before there's anything to check, then act without ever checking the
  thing that mattered.

**The plain-language finding: verification behavior is present, but
timed wrong. Models perform the ritual of checking without the substance
of it.**

## The fix — and why it matters more than the failure

One added sentence to the system instructions:

> *"Before acting on any signal that would end your vigilance — including
> good news — verify it through an independent channel first."*

Result: **failure rate drops from 100% to as low as 0%,** with most models
recovering to 90–100% success.

This means the gap is **not a capability limitation** — models can do this
correctly. It is a **default behavior gap**. In real-world deployment,
nobody guarantees the right instruction will be present. The vulnerability
is real precisely because the default is unsafe and the fix is invisible
unless you know to look for it.

## Why this is a rigorous finding, not a cherry-picked demo

- **n=20 per condition**, not a handful of anecdotal runs.
- **A controlled ablation** ruled out the obvious alternative explanations
  (label wording, prompt framing) before the finding was finalized — an
  earlier hypothesis was tested and explicitly discarded when the data
  contradicted it.
- **Cross-model replication**: the same failure, independently, across five
  unrelated model families.
- **A companion result** shows models are asymmetric the other way too —
  they hold firm against persuasion in threat scenarios, but a subset break
  down under social pressure to accept a "generous" settlement in place of
  what they're actually owed — confirming this is about *signal valence*,
  not a one-off scenario quirk.

## What this is built on

This finding comes from a purpose-built evaluation system: deterministic,
auditable, multi-agent protocol environments, each modeling a distinct
failure mode (silent-omission blindness, susceptibility to persuasion,
manufactured-evidence exploitation, and this one — false-positive trust). The
environments are fully reproducible, produce verifiable pass/fail outcomes
with no ambiguity, and were built from the ground up specifically to expose
these failure classes rather than measure generic task competence.

The system currently spans **11 independent environments**, a shared
compiler that verifies environment logic by construction, and **~280
automated tests** confirming correctness of every scored outcome.

**Related finding:** [Capability Profiles Invert Across Protocol-Discipline
Tests](FINDING-2-CAPABILITY-PROFILES.md) — why a single leaderboard number
hides the failure patterns that actually matter.

---

**Contact:** Mohit Upadhyay
**Status:** Private evaluation suite. Full methodology, environment source,
and additional findings available under discussion.

**License:** shared publicly for review only — no license is granted for
reuse, redistribution, or commercial use. See [LICENSE](LICENSE). For
licensing or acquisition inquiries, contact the address above.
