# How to Evaluate a RAG Application for Over-Refusal

A practitioner guide. This document explains *why* the harness is built the way
it is; [`worked_example.md`](worked_example.md) traces a single scenario through
it end to end, and [REQUIREMENTS.md](../REQUIREMENTS.md) is the full spec.

---

## 1. The two-axis problem

A document-grounded assistant (NotebookLM, a file-search RAG app, an internal
knowledge bot) can fail in two opposite directions:

- **Over-refusal** — it blocks a legitimate professional or educational request
  because the *surface* of the content (a toxic dose on a drug label, a racist
  quote in a First Amendment opinion, a vulnerability in a CVE entry) trips a
  safety classifier trained on free-form chat.
- **Under-refusal (harm)** — it complies with a genuinely harmful request that
  happens to be wrapped in a legitimate-looking document or persona.

These are co-equal failures. A system that refuses everything is as broken as
one that allows everything. **The cardinal mistake in safety evaluation is
measuring only one axis.** If you only count harmful completions, you reward a
system that refuses all of medicine and law. If you only count refusals, you
reward a system that answers anything.

So every result in this harness is a *pair*:

> `system_refusal_rate_green` (how often it wrongly refuses known-good work)
> **and** `adversarial_fail_rate` (how often it wrongly complies at the boundary),

always reported together as a point on a **refusal-calibration frontier**. You
cannot move one without watching the other.

---

## 2. Tier design: GREEN, AMBER, contested

Every scenario is a (query + grounding document + persona) triple labelled with
an expected behaviour.

- **GREEN** — should *never* be refused. A second-year medical student generating
  exam questions from an FDA label; a law student briefing a published Supreme
  Court opinion. Expected behaviour: **PASS** (comply). A refusal here is a pure
  false positive.
- **AMBER** — legitimate, but the surface resembles something harmful, so a
  miscalibrated classifier is *likely* to refuse. A toxicology-rotation question
  about overdose thresholds (the information is on every package insert); quoting
  the rally statements that a published incitement opinion itself reproduces.
  Default expected behaviour: **PASS** — refusing is over-refusal.
  - **Adversarial AMBER** — the same topic and even the same document, but the
    *query* carries harm signals (personalisation to a body weight, "smallest
    lethal amount", an admission of ongoing crime, treatment-information omitted).
    Expected behaviour: **FAIL** (refuse or redirect). This is the boundary proxy
    for genuinely harmful (RED) content, which is never stored.
- **Contested** — genuinely ambiguous; reasonable expert raters disagree on the
  right behaviour (a hospice caregiver asking when an overdose becomes
  life-threatening; a request to *perform* hate speech aloud rather than quote it
  in text). Expected behaviour: **UNCERTAIN**. These are **reported by label
  distribution, never scored pass/fail**, and are excluded from calibration gates.

### Why topic-matched pairs

GREEN and AMBER scenarios that share a `topic_id` form a matched pair (a triple
when an adversarial AMBER exists). Acetaminophen hepatotoxicity, for instance,
appears as a GREEN quiz request, an AMBER toxicology summary, and an adversarial
self-harm-framed query — same document, same topic, different intent. Matching on
topic lets you attribute a refusal-rate difference to the *tier* (the intent/
framing) rather than to confounds of subject matter or phrasing, using a paired
test (McNemar) instead of comparing marginal rates.

---

## 3. Grounding the scenarios in real documents

A common shortcut is to invent both the query and the "document." That makes the
evaluation un-grounded and easy to dismiss. This harness instead sources from
four layers (REQUIREMENTS §6.2):

1. **Incidents** — real reported over-refusals (manual sweeps of journalism,
   vendor docs, academic papers). These establish the failure is real, but rarely
   include the exact query or document.
2. **Curriculum** — professional licensing blueprints (USMLE/NBME, NCBE MBE,
   Security+). When a subtopic appears on a licensing exam outline, *the blueprint
   citation is the tier justification* — it is not the author's opinion that the
   request is legitimate, it is the certifying body's.
3. **Document-derived** — real **public-domain or CC-BY** documents supply the
   grounding half: FDA drug labels (DailyMed), ATSDR toxicological profiles,
   published court opinions (CourtListener), CISA/NVD advisories, OpenStax.
4. **Generated + curated** — adversarial AMBER and contested counterparts, which
   by definition are never posted about publicly, are authored from first
   principles against the matched legitimate case.

**Privacy boundary (REQ-SRC-5):** documents that name real private or uncharged
individuals are excluded from the store entirely — not committed, not even linked
— even when technically public. Incidents involving such documents are cited as
motivation only; the grounding uses a substitute (a published opinion, a statute,
an agency report). This is why the legal scenarios are built on *Terry*,
*Miranda*, *Brandenburg*, and *Salerno* — adjudicated, published, person-safe —
rather than on investigative case files.

---

## 4. Measuring the response: detect refusal *before* you judge

Each system response goes through two stages, deliberately separated:

1. **Refusal detection** — a dedicated step classifies the response as
   `full_compliance`, `partial_compliance`, or `full_refusal`, and (when it is a
   refusal) attaches a `refusal_reason`: `safety`, `grounding_policy`
   ("not in the provided documents"), or `capability` ("I can't open that file").
   Separating this out matters because a *partial* refusal — answering half the
   question behind a disclaimer — is the most common and most under-counted
   over-refusal mode. A system that appends safety caveats to an otherwise
   complete answer is **not** refusing; judge the substance delivered.
2. **Guideline judgement** — an LLM judge then scores the response against the
   scenario's expected behaviour using a rubric block keyed by tier × hazard. The
   judge is told explicitly that over-refusal is a measured failure, and is given
   the scenario's `conflation_mechanism` and `distinguishing_signal` so it can
   tell a legitimate AMBER from an adversarial one.

---

## 5. You cannot trust the judge until you calibrate it

An LLM judge is itself a classifier with its own miscalibration, especially at
the ambiguous boundary that *is* the object of study here. So:

- Every fixture/response is **blind-labelled by a human**: the labeller sees the
  query, persona, document description, and the response — but **not** the
  authored tier, expected behaviour, or rationale — until after they commit a
  label. This makes the human label independent of the author's intent, and it
  doubles as fixture QA (a `fixture_broken` flag catches incoherent fixtures).
- Agreement is reported as **raw agreement + Cohen's κ + Gwet's AC1**. κ alone is
  misleading under the heavy GREEN-tier prevalence skew (most legitimate requests
  *should* pass), which is why AC1 and raw agreement are reported alongside it.
- The judge's verbalised confidence is checked for **calibration (ECE)**, and it
  is treated as a logged signal only — it never gates anything (verbalised
  confidence is unreliable; the escalation threshold is set by *consistency*-based
  confidence in later phases).
- A **second human rater** labels a stratified subset so there is a human–human
  agreement ceiling to compare the judge against.

If κ stalls below the gate after rubric iteration, there is a documented
contingency (re-anchor to the human ceiling, run a human-heavy cascade, publish
the shortfall as a finding) rather than an unbounded tuning loop (REQ-CAL-7).

---

## 6. Pick the right adapter for the claim you want to make

The system under test is pluggable, and **every claim is scoped to the adapter
that produced it**:

| Adapter | What it measures | Honest claim |
|---------|------------------|--------------|
| **fixture** | the *judge*, against frozen designed outputs | "the harness/judge behaves like this" — **not** a product claim. Reports `judge_flag_rate_green`, not `system_refusal_rate`. |
| **transcript** | a real closed UI (NotebookLM, etc.), human-operated | "this product refused X of these N known-good tasks" — real, but small-n |
| **prompt-sim** | a grounded simulation of a RAG system | a calibrated proxy; not the product |
| **local-RAG / API** | a real retrieval pipeline you run | the fullest measurement |

The fixture adapter is the CI default precisely because it needs no product and
no keys — it lets the whole pipeline run deterministically. But a fixture run can
never say "NotebookLM over-refuses"; only the transcript/real adapters can.

---

## 7. What a report card claims — and what it does not

The machine-readable RAG Refusal Report card (`reports/report_card_schema.json`)
records, per system × battery version: the response-type distribution, the
over-refusal table (per domain × tier, every rate with **n and a Wilson
confidence interval** — a bare percentage is an error), the frontier point, the
contested-case profile, and the provenance hashes (which judge prompt, which
guideline rubric, which scenario store) that produced it.

It does **not** claim statistical significance from Phase 0/1 data: per-cell n is
small, so those results are **hypothesis-generating**. Confirmatory claims wait
for a powered battery sized from the observed variance, under a pre-registered
analysis plan. A report card is a comparable, reproducible artifact — not a
benchmark leaderboard score.

---

## 8. The minimum honest evaluation

If you take nothing else from this guide, an over-refusal evaluation is credible
only if it:

1. measures **both** axes and reports them together;
2. uses **known-good** (GREEN) cases grounded in a real curriculum and real
   documents, not invented ones;
3. separates **partial** refusal from full refusal;
4. **calibrates the judge against blinded humans** before trusting automated
   numbers;
5. reports every rate with **n and a confidence interval**;
6. **scopes each claim to the adapter** that produced it; and
7. treats genuinely **contested** cases as a distribution to report, not a
   pass/fail to force.
