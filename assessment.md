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

## Executive summary

**Overall:** The research aims target a real, verifiable gap (domain- and
tier-stratified over-refusal in grounded settings; judge calibration at the
ambiguous boundary), and the engineering plan is unusually disciplined for a
prototype — calibration gates, provider independence, honest limitations.
The dominant risks are *measurement-validity* risks, not engineering risks:
as currently specified, the default (seed) mode measures the judge rather
than any RAG system, the verdict schema cannot distinguish a refusal from a
judged-bad answer, and the calibration labels that gate all automation are
collected through a UI that shows raters the expected answer. All are fixable
with schema fields, metric definitions, and framing — before code exists,
which is the right time.

**Top recommendations, by leverage:**

| # | Recommendation | Part |
|---|---------------|------|
| 1 | Blind the labelling UI and second-rater prompt: hide `expected_behavior`, rationale, and `adversarial` flag from raters | B1 |
| 2 | Split `fp_rate` into `judge_flag_rate` (seed; RQ2) vs `system_refusal_rate` (live; RQ1); scope RQ1 to live mode | A2 |
| 3 | Add a dedicated refusal-detection step with a three-way `response_type` (full/partial compliance, refusal); WildGuard fills this slot | A3, D1 |
| 4 | Add a document-side factorial (matched / off-topic / flagged-terms documents) — the change that makes this a *RAG* eval rather than a chat eval; requires synthetic full documents over description-grounding | A6, B9 |
| 5 | Introduce a system-under-test adapter interface (fixture / prompt-sim / local-RAG / API / human-transcript) — converts the prototype into a framework that can assess open and closed RAG applications | C1 |
| 6 | Reframe Phase 1 as hypothesis-generating; report all rates with n + Wilson CIs; add `topic_id` pairing and paired tests; write a short pre-registered analysis plan | A4, A5, A8 |
| 7 | Replace the verbalized-confidence cascade threshold with consistency-based confidence and conformal calibration of λ; report judge ECE by tier | B4, D4 |
| 8 | Add judge-side provenance (`judge_prompt_hash`, `taxonomy_version`, block hashes) to results so rubric iteration doesn't break trend comparability | B2 |
| 9 | Treat the scenario store as a dataset release: semver, license, canary GUID, private held-out split, contribution guide; crosswalk the taxonomy to MLCommons AILuminate | C2, C4 |
| 10 | Descope the Reddit collector from Phase 1; reinvest in a second human rater on a 50-item subset and the document factorial | B7, A7 |

**Literature additions that change the design** (Part D): RefusalBench
(grounded selective refusal via document perturbation — also requires
narrowing RQ1's novelty claim), WildGuard (refusal detection), Zheng et al.'s
verbosity-bias check, conformal/selective-evaluation methods for the cascade,
prevalence-robust agreement statistics and IRT difficulty for RQ2, and
AILuminate's private-split and taxonomy practices.

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

## Part B — Assessment of the evaluation / implementation plan

### B0. Engineering strengths worth preserving

The plan shows discipline most prototypes lack: seed/live separation keeping
CI key-free and deterministic; three-way provider independence between proxy,
judge, and second rater (with the correlated-error rationale for excluding
Gemini from the judge chain spelled out — this is textbook-correct); mandatory
judge rationales; calibration gates that block automation rather than decorate
it; an advisory-mode bootstrap; a held-out adversarial split; swap
augmentation with a SUSPECT verdict that routes to humans; and a limitations
section that anticipates most reviewer objections. These should survive any
refactor.

### B1. The labelling UI leaks ground truth to the rater (highest-severity implementation bug)

REQ-APP-4 requires the labelling page to "display the full scenario record"
— which includes `expected_behavior`, `classification_rationale`,
`conflation_mechanism`, and the `adversarial` flag. A rater who sees the
authored expected label before labelling is not producing an independent
label; they are confirming the author's prior. Since judge calibration (RQ2)
is computed against these labels, this single UI requirement quietly
invalidates the calibration measurement.

**Fix:** the labelling form must show the rater what the *judge* sees
(persona, doc description, query, proxy output) and **hide** the authored
expectation fields until after the label is committed. Amend REQ-APP-4
accordingly. The same blinding applies to the synthetic second-rater prompt —
its input must exclude `expected_behavior` and the rationale fields
(worth stating as an explicit REQ, since "send the scenario record" is the
natural implementation).

### B2. Results provenance is half-built

REQ-PROXY-2 hashes the proxy system prompt, but judge results carry no
`judge_prompt_hash`, `taxonomy_version`, or `guideline_block_hash`. When the
rubric or judge prompt is tightened (which findings.md's "tighten rubric"
loop explicitly anticipates), κ and rate trends across runs become
uninterpretable without knowing which prompt produced which verdicts.

**Fix:** add `judge_prompt_hash`, `taxonomy_version`, and
`guideline_block_hash` to every `results.ndjson` record, and have
`generate_report.py` refuse to draw trend lines across records with differing
hashes (or annotate the discontinuity). Likewise version the scenario store
(`scenario_store_version`) so fixture edits are visible in trends.

### B3. The metrics layer needs a statistics pass

`eval/metrics.py` as specced computes point rates only. Concrete additions:

- Wilson (or Jeffreys) intervals on every rate; never emit a rate without n.
- Bootstrap-over-scenarios CIs for κ and for rate *differences* between
  domains/tiers; McNemar for the `topic_id`-paired GREEN/AMBER comparisons
  (A5).
- κ reported with its CI, alongside raw agreement and a prevalence-robust
  statistic (A7).
- Judge calibration outputs: ECE / reliability diagram on the calibration set
  (A7), emitted by `calibrate.py` next to κ.
- In live mode, k≥3 repeats per scenario; report per-scenario verdict
  instability as its own column (this doubles as a free judge-consistency
  signal — see B4).

### B4. The cascade thresholds on a quantity the plan itself shouldn't trust

The cascade accepts verdicts when verbalized `confidence ≥ λ`. Two issues:

1. **Verbalized confidence is poorly calibrated** (A7). The cited Cascaded
   Selective Evaluation work (Jung et al.) does not threshold raw verbalized
   confidence — its contribution is a calibrated abstention policy with
   coverage guarantees. Adopting the citation should mean adopting the method:
   either (a) derive confidence from agreement across m sampled judge runs
   (self-consistency — the swap-augmentation pair already gives m=2 for
   free on AMBER), or (b) calibrate λ via conformal prediction on the human-
   labelled calibration set, which yields a distribution-free guarantee like
   "≤10% of auto-accepted verdicts are wrong at 90% coverage" — a far more
   defensible automation gate than a κ threshold plus a confidence cutoff.
2. **REQ-CAS-1 writes the recommended λ into `eval/thresholds.py`** — i.e.,
   calibration output overwrites source code. Make thresholds a versioned
   data artifact (`eval/thresholds.json`, committed) so λ changes are
   diffable and auditable, and code stays code.

### B5. Circularity: one person authors scenarios, fixtures, labels, and rubric

In Phase 1 the same individual writes the scenario, writes the "proxy output"
fixture, writes the risk guidelines the judge applies, and supplies
human_label_r1. Judge–human κ then partially measures "does the judge prompt,
written by X, reproduce X's labels on X's fixtures" — a self-agreement loop.
§10 discloses the synthetic-rater half of this but not the author-rater half.

**Mitigations (cheap to moderate):** blind labelling (B1); a second human on
a 50-item subset (A7); generate some fixtures via live-mode proxy runs and
freeze them as fixtures (so fixture text isn't authored by the labeller);
and where possible have scenario authoring and guideline-clause authoring
reviewed in separate passes.

### B6. CI alert thresholds are below measurement resolution

`regression.yml` alerts when `fp_rate` moves >5pp and reports changes >2pp.
With ~36 GREEN seed scenarios, one scenario is ~2.8pp — the 2pp reporting
threshold is sub-resolution, and a single flipped verdict (judge
nondeterminism, provider model update) trips the 5pp alert. Tie thresholds to
scenario counts (e.g., alert on ≥2 scenario flips), or gate alerts on the
flip persisting across a re-run, otherwise the alarm fatigues and gets
ignored — the standard failure mode of regression alerting.

### B7. The Reddit collector should be descoped from Phase 1

PM judgment call: the collector + signal classifier + extractor is roughly a
quarter of the Phase 1 task list, carries the project's largest external-risk
surface (Reddit ToS, PII handling, committing third-party content to a public
repo — author-stripping doesn't address deleted-post persistence), and
contributes **nothing** to answering RQ1 or RQ2 in Phase 1 (extracted
scenarios require human adjudication before entering the harness, and the
calibration set is seed-only). G1 is a fine goal, but it is a separate
workstream with separate review needs. Recommend: move collector to its own
phase (or repo), keep `source: reddit_extracted` in the schema so the design
stays ready, and spend the freed Phase 1 effort on the second human rater and
the document-condition factorial (A6) — both of which *do* move the RQs.

### B8. Absolute thresholds without a baseline; comparison is the more useful design

`fp_rate < 10%` is arbitrary without a reference system — no published
baseline exists for this exact setting (that's the point of the project). The
harness is already provider-agnostic via `PROXY_MODEL`; leaning into
**comparative** reporting (same scenario battery across 2–3 proxy models, or
across judge versions) produces findings that are interpretable without an
absolute threshold and are far more useful to the community (Part C). Keep
the thresholds as *regression* gates (vs. the project's own last run), not as
*quality* claims.

### B9. The description-grounding proxy removes the variable RQ1 cares about most

Grounding on `source_doc_description` rather than document text means the
proxy never *sees* the surface-level flagged content (LD50 tables, case-law
violence descriptions) that triggers real over-refusal. A live proxy run on a
description of a toxicology chapter measures refusal on the *description* —
plausibly a large underestimate of refusal on the chapter itself, and the
doc-fidelity experiment (n=10, 15pp trigger) is too small to bound this. Since
fixtures must be written anyway, recommend: make **synthetic full documents**
(1–3 pages, public-domain-style, written alongside each scenario) the Phase 1
norm for live mode, demote description-grounding to a fallback, and grow the
fidelity experiment into the A6 factorial. This also unblocks the
`flagged_terms` document condition, which is impossible under
description-grounding.

### Interim summary 2 — implementation plan

The infrastructure design is genuinely strong — gates, provenance instincts,
provider independence, and honest limitations put it above most published
eval harnesses. The issues are concentrated where measurement meets
implementation: **(1)** the labelling UI shows raters the expected answer,
contaminating the calibration labels that everything downstream gates on —
the single most important fix in this document; **(2)** judge-side provenance
(prompt/taxonomy hashes) is missing, so rubric iteration will silently break
trend comparability; **(3)** the metrics layer has no uncertainty
quantification, and CI alert thresholds sit below what ~36 scenarios can
resolve; **(4)** the cascade thresholds on verbalized confidence, which the
cited literature says not to trust — conformal calibration or
consistency-based confidence would make the automation gate defensible;
**(5)** a single person authors scenarios, fixtures, rubric, and labels —
blinding plus one additional human rater breaks the loop cheaply; **(6)** the
Reddit collector is a large, risk-bearing Phase 1 line item that doesn't
advance either RQ and should be descoped; **(7)** description-grounding
removes the document-content variable that RAG over-refusal is *about* —
synthetic full documents are the fix and enable the document factorial from
Part A.

---

## Part C — From personal prototype to a framework of general value

The brief asks where this could become "a framework of general value to the
open source community in assessing closed and open RAG based applications."
The current scope note explicitly disclaims that ambition ("conclusions about
specific products cannot be drawn"). That disclaimer is correct *for the
prompt-simulated proxy* — but it is a property of one component, not of the
architecture. The pieces below would convert the disclaimer from a design
ceiling into a configuration choice.

### C1. The single biggest change: a system-under-test (SUT) adapter interface

Everything in the harness downstream of the proxy — judge, cascade,
calibration, metrics, review app — is already system-agnostic. The proxy is
the only hardwired component. Replace `rag_proxy/proxy.py`'s two modes with
an adapter interface:

```python
class RAGSystemAdapter(Protocol):
    def ingest(self, documents: list[Document]) -> SessionHandle: ...
    def query(self, session: SessionHandle, query: str) -> RAGResponse: ...
    # RAGResponse: raw text + optional metadata (citations, refusal signal,
    #              moderation flags if the system surfaces them)
```

with five adapters, in rough order of effort:

1. **Fixture adapter** — current seed mode, unchanged.
2. **Prompt-sim adapter** — current live mode, unchanged (now honestly named
   as one simulated SUT among many).
3. **Local-RAG adapter** — LlamaIndex/LangChain pipeline with a real
   embedding retriever over the synthetic documents (B9). This adds the
   missing retrieval dimension (multi-doc, distractor passages) and tests
   *open* RAG stacks people actually deploy.
4. **API adapter** — OpenAI file-search / Anthropic Files-based assistants:
   real closed systems testable programmatically, within their ToS.
5. **Transcript adapter** — a manual mode where a human runs the scenario
   battery against a closed UI (NotebookLM, Copilot Notebooks), pastes
   responses, and the harness handles everything from the judge onward. Slow,
   but it is the *only* honest path to claims about closed products, and the
   review app already has the UI bones for it.

Results records gain a `system_id`, and the headline deliverable becomes a
**comparison across systems on a fixed battery** — which resolves B8's
arbitrary-absolute-threshold problem at the same time. This is the difference
between "a prototype that simulates a RAG app" and "the harness you point at
a RAG app."

### C2. The scenario store is the durable community artifact — treat it like a dataset release

The schema's `conflation_mechanism` and `distinguishing_signal` fields are
the most original intellectual contribution in the repo: no existing
over-refusal benchmark documents *why* each case fools classifiers and what
signal separates it from real harm. That structure is what makes the dataset
usable for guideline-writing and classifier improvement, not just scoring.
To make it a community artifact:

- **Version it like software:** semver on the scenario store; changelog;
  releases. (B2's `scenario_store_version` feeds this.)
- **License it explicitly:** e.g., CC-BY-4.0 for scenarios, Apache-2.0 for
  code. Unlicensed data doesn't get reused.
- **Contamination protection:** embed a canary GUID (BIG-bench convention) in
  every scenario file so future model-training contamination is detectable,
  and hold back a private split (the MLCommons AILuminate practice — see D6)
  so headline numbers can't be gamed by training on the public set. This
  matters more here than for most benchmarks: an over-refusal benchmark that
  leaks into RLHF data stops measuring anything.
- **Contribution pipeline:** an authoring guide (the conflation-mechanism
  discipline is teachable), schema validation already in `smoke_test.yml`,
  and a review checklist — this is how the store grows past what one author
  can write, and how deferred domains (CRIS, EXTR) eventually get covered by
  people with the right domain expertise.

### C3. A standardized, machine-readable "RAG Refusal Report"

`findings.md` is designed for the project's own iteration loop. For external
value, define a fixed report card emitted per (system × battery-version):
per-domain × tier table of `response_type` distributions,
`system_refusal_rate_green` and `adversarial_fail_rate` with n and Wilson
CIs, judge version + calibration status (κ, ECE, gate pass/fail), and the
two-axis summary plotted as a point on the **refusal-calibration frontier**
(fp on x, adversarial-fail on y). Publish the JSON schema for this card so
third parties running the harness produce comparable artifacts — the
HELM/model-card lesson: the *reporting standard* is what makes independent
results composable into a literature.

### C4. Taxonomy interoperability

The nine-domain taxonomy is well-motivated but bespoke. Map each domain (and
each RED reference category) to the MLCommons AILuminate hazard taxonomy
(12 hazard categories; now the closest thing to an industry-standard hazard
vocabulary) and, where applicable, AIR-Bench's regulation-derived categories.
A simple crosswalk table in `taxonomy.md` lets anyone translate penumbra
results into the vocabulary their org or regulator already uses — cheap to
write, large interop payoff.

### C5. Ship the judge harness as a separable artifact

The calibrated-judge machinery (rubric blocks, swap augmentation, cascade,
calibration gates, review app) is independently useful to anyone evaluating
*anything* against a rubric — arguably more reusable than the RAG framing.
Keeping `judge/` + `eval/` + `review_app/` cleanly importable (no scenario-
store assumptions baked in) costs little now and creates a second adoption
path for the project.

### Interim summary 3 — generalization

The architecture is one abstraction away from being the community framework
the brief envisions: everything downstream of the proxy is already
system-agnostic, so introducing a SUT adapter interface (fixture / prompt-sim
/ local-RAG / API / human-transcript) converts "cannot draw conclusions about
real products" from a permanent disclaimer into a per-adapter caveat, and
makes cross-system comparison — not absolute thresholds — the headline
output. The scenario store, with its conflation-mechanism documentation, is
the durable artifact and should be versioned, licensed, canary-tagged, and
opened to contribution with a private held-out split. A machine-readable
report card and an AILuminate taxonomy crosswalk make independent results
composable and legible to the broader T&S world.

---

## Part D — Integrating the trust & safety and ML literature

The repo's citations (XSTest, OR-Bench, COVER, RagRefuse, SORRY-Bench,
HarmBench, Wang et al., Jung et al.) are well-chosen. The gaps are below,
ordered by how much they would change the design.

### D1. Refusal detection: WildGuard and the three-way compliance taxonomy

[WildGuard](https://proceedings.neurips.cc//paper_files/paper/2024/hash/0f69b4b96a46f284b726fbd70f74fb3b-Abstract-Datasets_and_Benchmarks_Track.html)
(Han et al., NeurIPS 2024 Datasets & Benchmarks) is an open moderation model
that jointly classifies prompt harmfulness, response harmfulness, and —
critically for this project — **whether the response is a refusal**, with
~25% better refusal detection than prior open tools. It directly fills the
missing-refusal-detector gap (A3) and is a stronger Phase 2 screener
candidate than the currently planned Llama Guard 3, which classifies harm
categories but is not a refusal detector. Adopt XSTest/OR-Bench's three-way
`full_compliance / partial_compliance / full_refusal` labelling as the
`response_type` vocabulary so penumbra numbers are comparable to the
chat-domain over-refusal literature.

### D2. Grounded-refusal evaluation: RefusalBench's generative method

[RefusalBench](https://arxiv.org/abs/2510.10390) (arXiv 2510.10390) evaluates
*selective* refusal in grounded LMs by **programmatically perturbing
documents** across defined uncertainty categories, including multi-document
settings — and finds frontier models identify the correct *reason* for
refusal <50% of the time in multi-doc RAG. Three direct adoptions:

1. Its perturbation-based generation is a scalable complement to hand
   authoring for Phase 4 — perturb a GREEN scenario's document, not its
   query, to populate the A6 document factorial systematically.
2. Its finding motivates adding a `refusal_reason` field to the judge output
   (safety vs. grounding-policy vs. capability), which is exactly the
   mechanism decomposition RQ1 needs (A1).
3. It should be cited in the README's RQ1 novelty claim, which currently
   says no grounded-refusal work uses structured comparisons — the claim
   needs narrowing to the professional-domain/tier stratification, which
   does remain unclaimed territory.

### D3. Judge biases beyond position: the MT-Bench bias triad

Swap augmentation handles position bias, but Zheng et al. (NeurIPS 2023,
MT-Bench) established a triad: position bias, **verbosity bias** (longer
outputs judged more favorably), and **self-enhancement bias** (judges
preferring their own family's outputs — already mitigated by the cross-family
requirement; the design should *cite this as the reason*, turning an
engineering choice into a literature-grounded control). Verbosity bias is
cheap to monitor: log proxy-output length and report the correlation between
length and verdict within tier in `findings.md`. §10 item 6 already names
length bias as unaddressed — this closes it for one line of pandas.

### D4. Selective evaluation done properly: conformal calibration

The cascade cites Cascaded Selective Evaluation (Jung et al.) but implements
a simpler verbalized-confidence threshold the cited work specifically
improves upon (B4). Two literature-grounded upgrades: derive judge confidence
from **agreement across sampled runs** (self-consistency), and set λ by
**conformal prediction** over the human-labelled calibration set, yielding a
distribution-free guarantee on the auto-accepted error rate. On verbalized
confidence specifically: Tian et al. (EMNLP 2023) and Xiong et al. (ICLR
2024) document systematic overconfidence; reporting the judge's ECE by tier
(A7) turns this from a design risk into an RQ2 finding.

### D5. Measurement science: disagreement as signal, prevalence-robust agreement, IRT

- **Human label variation** (Plank, EMNLP 2022; Gordon et al.'s jury
  learning, CHI 2022): at the AMBER boundary, rater disagreement is often
  legitimate value disagreement, not noise. The schema's `UNCERTAIN` label
  gestures at this; the upgrade is to *retain* disagreeing labels rather
  than force adjudication to a single `adjudicated_label`, and report
  judge agreement against the label distribution. This reframes RQ2's
  premise — at the boundary the right target may be matching the human
  *distribution*, not a forced consensus.
- **Agreement statistics:** PABAK / Gwet's AC1 alongside κ (A7);
  Krippendorff's α when raters exceed two (Phase 3 domain experts).
- **Item Response Theory:** fitting a simple IRT model over (scenario ×
  rater/judge) outcomes yields per-scenario difficulty estimates — a
  principled, non-circular operationalization of "proximity to the boundary"
  for RQ2, and a quality filter for Phase 4 scenario scaling (flag items
  with negative discrimination).

### D6. T&S practice: standard taxonomies, private splits, and the injection gap

- **MLCommons AILuminate** ([benchmark](https://mlcommons.org/benchmarks/ailuminate/),
  [arXiv 2503.05731](https://arxiv.org/html/2503.05731v1)): beyond the C4
  taxonomy crosswalk, two practices transfer directly — the
  **public-practice / private-official split** for contamination resistance
  (C2), and the use of an **ensemble evaluator** rather than a single judge
  model, which is where the judge chain could evolve once calibration data
  exists (ensemble disagreement is another non-verbalized confidence signal).
- **Indirect prompt injection** (Greshake et al., 2023; OWASP LLM Top 10,
  LLM01): the problem statement lists document-borne injection as a core
  RAG failure mode, but no phase ever tests it. Either add an injection
  scenario class in a later phase (documents containing instructions that
  attempt to flip the assistant's refusal behaviour — *in both directions*:
  jailbreak-via-document and induced-over-refusal-via-document, the latter
  being a novel and safe-to-test angle highly aligned with this project's
  thesis) or trim the problem statement to what the program will measure.
- **NIST AI RMF / GenAI profile:** worth a one-paragraph mapping in the
  README for T&S-practitioner legibility (measurement function, "manage"
  gates), not a design change.

### D7. Scaling scenario generation with curation

OR-Bench's contribution is a *method* (LLM-generated seemingly-toxic prompts
at scale, filtered by ensemble moderation) as much as a dataset; FalseReject
(2025) extends this with context-rich over-refusal cases. For Phase 4, the
defensible pipeline is literature-standard: generate candidates with these
methods (plus D2's document perturbations), then require human curation with
the conflation-mechanism documentation that makes penumbra scenarios
distinctive. Generation scales; the schema's analytical fields are where
human effort should concentrate.

---

## Closing note

Sources consulted during this review:
[RefusalBench](https://arxiv.org/abs/2510.10390) ·
[Steering Over-refusals in RAG (RagRefuse)](https://arxiv.org/pdf/2510.10452) ·
[COVER (ACL 2025 Findings)](https://aclanthology.org/2025.findings-acl.1243.pdf) ·
[WildGuard (NeurIPS 2024)](https://proceedings.neurips.cc//paper_files/paper/2024/hash/0f69b4b96a46f284b726fbd70f74fb3b-Abstract-Datasets_and_Benchmarks_Track.html) ·
[AILuminate v1.0 (arXiv 2503.05731)](https://arxiv.org/html/2503.05731v1) ·
[AILuminate benchmark](https://mlcommons.org/benchmarks/ailuminate/) ·
[AILuminate suite (GitHub)](https://github.com/mlcommons/ailuminate)

---

## Implementation log — v3 documentation update (2026-06-11)

All recommendations above were applied to the planning documentation
(REQUIREMENTS.md v3, README.md, TASKS.md). Disposition map:

| Rec | Assessment ref | Applied in |
|-----|----------------|-----------|
| R1 — RQ1 construct named; novelty claim narrowed (RefusalBench cited) | A1, D2 | README RQ1 |
| R2 — metric split `judge_flag_rate_green` / `system_refusal_rate_green`; RQ1 live-only | A2 | REQUIREMENTS §0, §7.1, REQ-HARNESS-2, REQ-SUT-5; README |
| R3 — refusal detector; three-way `response_type` + `refusal_reason`; WildGuard P2 | A3, D1, D2 | REQ-JUDGE-6, §12 decision 4, judge output schema, tree |
| R4 — Phase 1 hypothesis-generating; n + Wilson CI everywhere; k≥3 repeats; power calc P2 | A4 | §7.1 rules, REQ-HARNESS-4, §13 |
| R5 — `topic_id` pairing; McNemar; shared templates | A5 | §4 schema + pairing rule, §7.1 |
| R6 — document factorial (`doc_condition`); synthetic full documents as norm | A6, B9 | §4, §6.5 adapter 2, §6.12 rewrite, §12 decision 16 |
| R7 — second human rater ≥50-item subset; raw agreement + PABAK/AC1 | A7 | REQ-CAL-5, §6.7 outputs, §7.1 |
| R8 — ex-ante boundary proximity (adversarial flag, rater confidence, IRT P4) | A7, D5 | §7.4, REQ-APP-4, labels schema |
| R9 — judge ECE as named output; consistency confidence; conformal λ | A7, B4, D4 | §6.6.3, REQ-CAS-1, §6.7, §12 decision 18 |
| R10 — pre-registered `analysis_plan.md` | A8 | §7.4, tree, TASKS, Phase 1 exit criteria |
| R11 — blinded labelling UI + blinded second-rater prompt | B1 | REQ-APP-4 rewrite, REQ-CAL-4, §12 decision 17 |
| R12 — judge-side provenance hashes; trend-integrity guard | B2 | REQ-HARNESS-1, §6.11 record, §7.2 |
| R13 — statistics in metrics.py (Wilson, bootstrap, McNemar, κ CI) | B3 | §7.1 rules, TASKS eval section |
| R14 — thresholds as data artifact `eval/thresholds.json` | B4 | REQ-CAS-1, REQ-CAL-2, tree |
| R15 — circularity mitigations (frozen live fixtures, blinding, 2nd human) | B5 | §10 item 2, TASKS scenario content |
| R16 — CI alerts in scenario flips, persist across re-run | B6 | §6.10 regression.yml |
| R17 — Reddit collector deferred to Phase 3 | B7 | G1, §2, §5 tree, §6.10 collect.yml, §12 decision 13, §13, TASKS |
| R18 — thresholds = regression gates; comparative reporting headline | B8 | §7.1 rules, §6.5 purpose, §12 decision 15 |
| R19 — SUT adapter interface (5 adapters, `system_id`) | C1 | §6.5 rewrite, REQ-SUT-1..5, tree, README |
| R20 — dataset release: semver, licences, canary GUID, private split, contribution guide | C2 | §4 contamination note, §12 decision 19, §13 Phase 4 |
| R21 — machine-readable RAG Refusal Report + frontier | C3 | §7.3, §7.2 findings sections, tree |
| R22 — **MLCommons AILuminate v1.0 hazard taxonomy adopted as the harm-category standard** | C4 + user request | new §3.0 (12 categories + domain crosswalk + REQ-TAX-1), `ailuminate_hazards` schema field, RED table restated, guideline blocks keyed by tier × hazard slug, README section |
| R23 — judge harness separable | C5 | implicit in §6.5 system-agnostic framing (no scenario-store imports in judge/) |
| R24 — verbosity-bias monitor; Zheng et al. cited for cross-family | D3 | REQ-JUDGE-7, §10 item 6, §7.2 |
| R25 — disagreement retention; label-distribution reporting; Krippendorff's α | D5 | REQ-CAL-6 |
| R26 — injection scenario class (both directions) Phase 3; problem statement scoped; NIST AI RMF mapping | D6 | §0 scope note, §13 Phase 3, README AILuminate section |
| R27 — ensemble evaluator exploration | D6 | §13 Phase 4 |
| R28 — generation-with-curation pipeline (OR-Bench / RefusalBench methods) | D7 | §13 Phase 4, TASKS Phase 4 |
