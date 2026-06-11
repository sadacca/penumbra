# Penumbra — Research Program Assessment

**Role:** Research program manager review of the research aims (README.md) and
implementation plan (REQUIREMENTS.md v2, TASKS.md).
**Date:** 2026-06-11
**Method:** Staged review with interim summaries — Part A (research aims),
Part B (evaluation/implementation plan), Part C (generalizable framework
potential), Part D (literature integration). An executive summary at the top
consolidates the highest-leverage recommendations.

> **Note on document structure:** This assessment was written incrementally;
> each part closes with an *interim summary* capturing the state of the
> assessment at that point, per the review brief.

---

## Part A — Assessment of the research aims

### A0. What the project gets right

Before critique: the framing is unusually strong for a prototype. Treating
over-refusal and harm as co-equal failure modes with a paired metric
(`fp_rate` + `adversarial_fail_rate`, never reported alone) is the correct
two-axis framing and is still rare in published work. The RQs cite the
relevant 2024–2025 literature (XSTest, OR-Bench, COVER, RagRefuse,
SORRY-Bench, HarmBench) and correctly identify a genuine gap: domain-stratified,
tier-stratified over-refusal measurement in RAG settings, and judge calibration
specifically at the ambiguous boundary. The "Honest Scope & Limitations"
section (§10) is exemplary. The critiques below are about making the RQs
*answerable as stated*, not about their motivation.

### A1. RQ1's construct is ambiguous: whose refusal is being measured?

RQ1 asks about "the false-positive refusal rate of **AI safety classifiers**"
— but the harness contains no safety classifier as a system under test. In a
real RAG product, a refusal can originate from at least three distinct
mechanisms:

1. **The base model's safety training** (the model itself declines),
2. **An external guardrail classifier** (input or output moderation layer),
3. **A grounding-policy refusal** ("this isn't in your documents") that is
   RAG-specific and not safety-motivated at all.

These have different causes, different fixes, and different research
literatures. The current design measures a fourth thing entirely in its
default mode (see A2), and mechanism (1) only in live mode — and even then
the refusal behaviour of a free-tier `deepseek-r1-distill` proxy. The RQ
should be rewritten to name its actual construct, e.g.:

> *"Does the refusal rate of an instruction-following LLM operating under a
> document-grounded system prompt vary systematically across professional
> domains and tiers?"*

…and the eventual generalization path (Part C) is what lets the same harness
later target mechanisms (2) and (3) on real systems.

### A2. Seed mode cannot answer RQ1 — and it is the default and CI mode

In seed mode, proxy outputs are **hand-written fixtures**. A judge `FAIL` on
a GREEN fixture measures *the judge's propensity to flag a known-good output*
— a property of the judge, not a refusal rate of any RAG system. Yet
`fp_rate` is defined once (§7.1) and computed identically in both modes, and
the regression workflow alerts on `fp_rate` movements from seed runs.

This is the most important conceptual fix in the plan:

- **Split the metric by what it measures:** `judge_flag_rate_green` (seed
  mode; a judge-calibration metric belonging to RQ2) vs.
  `system_refusal_rate_green` (live mode; the RQ1 metric).
- Scope RQ1 explicitly to live-mode runs.
- Seed mode remains valuable — but as the *judge calibration instrument*
  (RQ2), not the over-refusal instrument (RQ1). The current docs conflate
  the two, and the conflation will propagate into findings.md and any
  published claims.

### A3. There is no refusal detector, and the verdict schema conflates two judgments

`PASS`/`FAIL` bundles together "the output complies with the risk guidelines"
and "the system behaved as expected for this tier." For GREEN scenarios the
failure mode is *refusal*; for adversarial AMBER it is *compliance*. These
require the judge to first determine **what kind of response occurred**, then
**whether it was appropriate** — and the literature treats these as separate
classification tasks for good reason: partial/hedged compliance ("soft
refusal" — answering with heavy disclaimers, or answering 3 of 10 requested
quiz questions) is the dominant real-world behaviour at the boundary and is
invisible to a binary verdict.

**Recommendation:** add a `response_type` field — `full_compliance` /
`partial_compliance` / `full_refusal` (the XSTest/OR-Bench three-way
taxonomy) — produced by a dedicated refusal-detection step, separate from the
guideline-compliance verdict. WildGuard (NeurIPS 2024 D&B) is an open,
purpose-built refusal detector and would slot directly into the Phase 2
screener slot currently reserved for Llama Guard 3 (see D1). Without this,
`fp_rate` cannot distinguish "refused outright" from "complied but the judge
disliked the content," which are different findings with different audiences.

### A4. Statistical power: the Phase 1 design cannot support "vary systematically"

Phase 1 targets ≥4–8 GREEN scenarios per domain. With n=8 and zero observed
refusals, the 95% Wilson interval is roughly [0%, 32%] — far wider than the
<5–10% thresholds the plan sets, and per-domain *comparisons* at these n are
essentially uninformative. RQ1's phrase "vary systematically" implies a
confirmatory claim the design cannot deliver.

**Recommendations:**
- Reframe Phase 1 explicitly as **hypothesis-generating / instrument
  validation**, and say so in the README's RQ section (the scope note gestures
  at this but the RQs read as confirmatory).
- Report every rate with its n and a Wilson interval; never report a bare
  percentage (add this to `eval/metrics.py` requirements).
- Use Phase 1 variance estimates to compute the scenario counts a
  confirmatory Phase 2/3 needs (likely 50–100+ per domain×tier cell for the
  effect sizes implied by the thresholds).
- In live mode, run k≥3 repeats per scenario and report between-run variance;
  a single stochastic sample per scenario makes rates unstable at small n.

### A5. Domain comparisons are confounded; the topic-matching idea should be formalized

Scenarios are hand-authored per domain, so domain differences are confounded
with author phrasing, topic difficulty, and query style. RQ1's GREEN-vs-AMBER
comparison "matched on topic" is the right instinct but appears nowhere in the
schema or tasks.

**Recommendations:**
- Add a `topic_id` field to the scenario schema and author GREEN/AMBER pairs
  (and where possible GREEN/AMBER/adversarial-AMBER triples) sharing a
  `topic_id`. Analyze tier effects with paired tests (McNemar) rather than
  comparing marginal rates.
- Hold query *templates* constant across domains where feasible ("Generate 10
  MCQ questions on {topic} from {doc}") so domain is the manipulated variable,
  not the prose style.

### A6. The distinctly-RAG variable — the document — is never manipulated

The problem statement's RAG-specific failure modes (source laundering,
prompt injection via document, trust calibration) motivate the project, but
the harness varies only the *query*. The document enters as a static
description. COVER's core contribution is decomposing context-triggered vs.
query-triggered refusal, and RefusalBench (arXiv 2510.10390, found in review
— not currently cited in the repo) evaluates *selective* refusal in grounded
models by perturbing the documents. Penumbra is positioned as a RAG eval but
currently has no document-side manipulation, no retrieval, no multi-document
condition.

**Recommendation:** add a small factorial dimension even in Phase 1:
`doc_condition ∈ {matched_benign, mismatched_benign, flagged_terms}` — same
GREEN query run against (a) the appropriate document, (b) an off-topic benign
document, (c) a document containing surface-level flagged terminology (e.g.,
the toxicology textbook chapter itself). This is cheap (reuses queries),
directly tests whether refusals are query- or context-triggered, and is the
single change that most strengthens the claim to be a *RAG* over-refusal eval
rather than a chat over-refusal eval with set dressing. Prompt injection can
stay out of scope, but then remove it from the problem statement or mark it
explicitly as motivating-context-only (see D6).

### A7. RQ2: "human labels" overstates the ground truth, and κ has known pathologies here

- **One human.** Labels are rater_1 (the author) plus a synthetic Gemini
  second rater. §10 discloses this honestly, but RQ2 as written ("between an
  LLM safety judge and human labels") promises human ground truth the design
  doesn't have. With a single human you cannot separate judge miscalibration
  from rater idiosyncrasy. Even 50 items dual-labelled by one additional
  human would materially harden RQ2; this is the cheapest high-value addition
  to the plan.
- **κ is prevalence-sensitive.** GREEN labels will be nearly all PASS; under
  extreme prevalence skew, Cohen's κ becomes unstable and can be near-zero
  despite high raw agreement (the "kappa paradox"). A GREEN-vs-AMBER κ
  comparison is therefore partially an artifact of base-rate differences,
  which is exactly the comparison RQ2 makes. Report raw agreement, PABAK
  and/or Gwet's AC1 alongside κ, and per-class F1; pre-commit to which is
  primary.
- **"Proximity to the AMBER/RED boundary" is not operationalized.** If
  boundary proximity ends up defined via judge confidence, the RQ2 claim
  (swap instability correlates with boundary proximity) risks circularity —
  judge confidence and judge position-instability are both judge-internal
  quantities. Define proximity ex ante from non-judge signals: the
  `adversarial` flag, human rater confidence collected at labelling time, or
  an item-difficulty estimate (IRT; see D5).
- **Verbalized confidence is itself untrustworthy.** The cascade thresholds
  on the judge's self-reported confidence, but LLM verbalized confidence is
  known to be poorly calibrated (Tian et al., EMNLP 2023; Xiong et al., ICLR
  2024). Measuring the judge's ECE / reliability diagram on the calibration
  set should be a *named output* of `calibrate.py` — it is publishable signal
  for RQ2 and a prerequisite for trusting λ (see B4).

### A8. Make the hypotheses falsifiable before data arrives

Both RQs are framed as "is X lower/elevated…" without directional
predictions, effect sizes, or analysis commitments. For a project whose
explicit pitch is generating evidence not in the literature, a lightweight
pre-registration goes a long way: add an `analysis_plan.md` stating, per RQ,
the primary metric, the test, the minimum effect size of interest, what
outcome would count as a null result, and which comparisons are exploratory.
The held-out adversarial-AMBER split (REQ-CAL-2) shows the team already
thinks this way; extend the discipline to the RQs themselves.

### Interim summary 1 — research aims

The two RQs target a real, well-cited gap, and the two-axis metric framing is
the right one. But as stated, neither RQ is answerable by the Phase 1 design:
**RQ1** names a construct (safety classifiers) the harness doesn't test, is
unanswerable in the default seed mode (which measures the judge, not the
system), lacks a refusal detector to distinguish refusal from judged
non-compliance, and lacks the statistical power for "systematic" domain
claims. **RQ2** rests on one human rater, a prevalence-confounded κ
comparison, and an unoperationalized notion of boundary proximity, with a
cascade thresholding on untrusted verbalized confidence. The highest-leverage
fixes: (1) split `fp_rate` into a judge-calibration metric (seed) and a
system-refusal metric (live); (2) add a three-way `response_type` refusal
detector; (3) add `topic_id` pairing and a document-side factorial condition;
(4) reframe Phase 1 as hypothesis-generating with CIs and n's everywhere;
(5) add a second human on a subset and prevalence-robust agreement statistics;
(6) write a short pre-registered analysis plan. None of these require new
infrastructure beyond what is already planned — they are mostly schema fields,
metric definitions, and framing.

---

*Parts B–D follow.*
