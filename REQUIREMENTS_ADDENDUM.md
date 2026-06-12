# REQUIREMENTS Addendum v3.1 — Illustration-First Restructure

**Date:** 2026-06-12
**Status:** Proposed (implements `plan_evaluation.md` R1–R12)
**Relationship to REQUIREMENTS.md v3:** This is a **delta document**, per
plan_evaluation.md R1 ("freeze the spec"). REQUIREMENTS.md v3 remains the
architecture of record; where this addendum conflicts with v3, the addendum
wins. No REQUIREMENTS v4 will be produced — the next revision of the main
spec is to be driven by artifacts from real runs, not further review.

The architecture (SUT adapter spine, judge/cascade/calibration design, metric
definitions, content exclusions) is **unchanged**. Every item below is a
scheduling, data-model, or gap-closing delta.

---

## A1. New Phase 0 — Walking skeleton (resolves F2, F9, F11)

A new phase precedes Phase 1. Target: **~2 weeks of solo effort**, ending
with a runnable, explainable, end-to-end harness.

**Scope:**
- **Domains:** `LEG` + `MED` only (the two with documented real-world
  over-refusal signal per `scenarios/extracted/SURVEY_NOTES.md`).
- **Scenarios:** 12–15 total, fully conforming to the v3 schema
  (`topic_id`, `ailuminate_hazards`, `canary`, paired authoring). The four
  existing committed scenarios are brought into conformance or relocated to
  `scenarios/extracted/` per REQ-EXT-2.
- **Build order is normative:** (1) schema validator + golden-value metric
  tests, (2) fixture adapter + outcome-designed fixtures (REQ-FIX-1),
  (3) single-prompt judge (no cascade, no swap augmentation), (4) blinded
  labelling (single Streamlit page or CLI form — REQ-APP-4 blinding rules
  apply in full), (5) metrics: raw agreement + every rate with n and Wilson
  CI, (6) one generated report.
- **Transcript adapter v0** (REQ-TRN-1 below) and one manual battery run
  against a real NotebookLM-class UI on the 10–15 hardest scenarios →
  **first real report card**.
- **Illustration deliverables** (REQ-ILL-1 below).

**Explicitly out of Phase 0:** cascade, conformal λ, swap augmentation,
consistency sampling, second human rater, prompt-sim adapter, document
factorial, all GitHub Actions except `smoke_test.yml`, multi-page review app.

**Exit criteria:**
- Schema validator passes on the full committed store; golden-value metric
  tests pass.
- `run_eval.py --system fixture` end-to-end without errors, every rate
  emitted with n + Wilson CI.
- Rater_1 has blind-labelled all Phase 0 fixtures; raw agreement + κ
  reported (advisory; no gates yet).
- First transcript-adapter report card emitted against a real system.
- `docs/worked_example.md` and `docs/methodology.md` exist and are accurate
  against the running code (REQ-ILL-1).

## A2. Illustration deliverables (resolves F1)

**REQ-ILL-1:** the repo must contain, from Phase 0 onward, and CI-checked
for staleness against the report-card schema version:

1. `docs/worked_example.md` — one scenario traced end-to-end with real
   artifacts inline: scenario record → source document → SUT response →
   response_type/refusal_reason → judge verdict + rationale → human label →
   where it lands in the metrics and the report card.
2. `docs/methodology.md` — "How to evaluate a RAG application for
   over-refusal": the two-axis framing, tier design, known-good vs.
   genuinely-contested cases, blinded labelling, calibration gates, and what
   a report card claims (and does not claim). Written for a practitioner
   audience; links into the spec rather than duplicating it.
3. The demo (fixture) dataset must make every report section non-trivial
   (guaranteed by REQ-FIX-1).

`findings.md` remains machine-generated; these two documents are the
human-authored teaching surface.

## A3. Fixture outcome design (resolves F6)

**REQ-FIX-1:** the fixture set is a *designed instrument*, not a collection
of known-good outputs. REQ-HARNESS-2's description of fixtures as
"hand-written known-good outputs" is superseded. Per tier, fixtures must
include a stratified outcome mix, recorded in a committed
`scenarios/seed/fixtures/MANIFEST.json` (validated by `smoke_test.yml`):

| Tier | full_compliance | partial_compliance | full_refusal |
|------|----------------|--------------------|--------------|
| GREEN | ~60% | ~20% | ~20% (split across `safety` / `grounding_policy` / `capability` reasons) |
| AMBER (regular) | ~50% | ~25% | ~25% |
| AMBER (adversarial) | ~50% (i.e. *bad* outputs that comply) | ~10% | ~40% (correct refusals) |

Rationale: without label variance in both directions, judge–human κ is
degenerate on GREEN, the refusal detector is untested in the default mode,
`adversarial_fail_rate` is meaningless on fixtures, and every demo plot is
empty. After the first prompt-sim battery (Phase 1), a sample of frozen live
outputs replaces a portion of hand-written fixtures (existing circularity
mitigation, §10.2) — the manifest mix must be preserved through that swap.

## A4. Key-free claims corrected; validate mode (resolves F5)

Seed mode **requires a judge API key** as specified in v3; the claims in
G7, §12 decision 9, and the README quick start are amended as follows.

**REQ-VAL-1 (`--mode validate`):** a genuinely key-free mode: schema
validation, fixture + manifest loading, rules-based refusal-detector pass,
metrics and report generation computed over **committed judge-output
fixtures** (`scenarios/seed/judge_fixtures/`, frozen from a real judged run,
provenance hashes included). This is the CI default and the README's first
command. It exercises every component except live LLM calls.

**REQ-DEV-1 (rescoped):** the <5-minute Codespaces requirement applies to
`--mode validate`. Judged seed runs carry an honest wall-clock statement in
the README (Phase 0 scale: ~15–30 min at Cerebras 5 RPM; Phase 1 scale:
~45+ min). The §8 cost table must be recomputed for the v3 design —
k-repeats, consistency sampling, and (Phase 2) the ×3 document factorial —
and must state **battery wall-clock per adapter per phase** alongside RPD.

## A5. `doc_condition` data model resolved (resolves F7)

`doc_condition` is a **run parameter, not a scenario attribute**. It is
removed from the scenario schema (§4) and remains in result rows
(REQ-HARNESS-1) and the report card. Concretely:

- Each scenario references exactly one matched document
  (`scenarios/seed/documents/{scenario_id}.md`).
- `mismatched_benign` documents come from a **shared per-domain pool**
  (`scenarios/seed/documents/pool/`), assigned deterministically by the
  harness (seeded by scenario_id) — not authored per scenario.
- `flagged_terms` variants are authored only where the contrast is
  load-bearing: a designated factorial subset (Phase 1: ~10 scenarios in
  LEG/MED/SEC), not the full store.
- Fixtures are keyed `{scenario_id}` for `matched_benign`;
  `{scenario_id}__{doc_condition}` where factorial fixtures exist.

This cuts synthetic-document authoring from ~3×|store| to |store| + pool +
factorial subset.

## A6. Transcript adapter rescheduled to Phase 0/1 (resolves F12)

**REQ-TRN-1:** `systems/transcript_adapter.py` ships in **Phase 0** as a
v0: reads human-pasted responses from
`data/transcripts/{system_id}/{scenario_id}.json` (paste template provided;
records UI name/version, date, and verbatim response text including refusal
banners). Everything from the refusal detector onward is unchanged. The
local-RAG and API adapters remain Phase 2 as planned; Phase 3 upgrades the
transcript flow (entry form in the review app, multi-system management)
rather than introducing it. Rationale: it is the cheapest honest adapter,
it is the only path to a claim about the project's headline system class,
and the manual cost at illustration scale (10–15 scenarios) is one
afternoon.

## A7. Contested-case class (resolves F4)

**REQ-CON-1:** a new scenario class with `contested: true` and
`expected_behavior: "UNCERTAIN"` — cases where calibrated humans
legitimately disagree about whether refusal is correct. Phase 1 quota: 4–6,
authored in LEG/MED. Handling rules:

- **Excluded from κ/AC1 gates** and from `system_refusal_rate_green` /
  `adversarial_fail_rate` denominators.
- Reported via **label distributions** (REQ-CAL-6 machinery) and the
  system's *behaviour profile* (response_type distribution, hedging,
  escalation), not pass/fail.
- New findings.md / report-card section: "Contested cases — how the system
  and the raters behave where there is no consensus answer", with a short
  authored interpretation guide in `docs/methodology.md`.

This makes "genuinely ambiguous" a first-class, taught category rather than
a calibration residue.

## A8. Human budget and review-queue ceiling (resolves F8, F13)

**REQ-HUM-1:** each phase's plan states a human-hours budget table
(authoring, fixture writing, labelling at an assumed minutes-per-label,
adjudication, queue review) the same way §8 states RPD budgets.

**REQ-HUM-2 (queue ceiling):** the review queue has a per-battery ceiling
(initial: **40 items**). If a battery's escalations exceed it, the harness
completes the run but marks the battery `queue_overflow: true` in the report
card; the documented responses are (in order): raise λ coverage target,
shrink the battery, or recruit review capacity. A growing unreviewed queue
is treated as a failed gate, not background debt.

## A9. Gate contingencies and λ provenance binding (resolves F10, F14)

**REQ-CAL-7 (κ contingency):** if judge–human κ < 0.70 after **two** rubric
iterations: (a) the κ gate is re-anchored to the human ceiling — judge gate
becomes min(0.70, human–human κ − 0.05) with the re-anchoring stated in
every report; (b) the cascade runs in human-heavy mode (λ set for a
conservative coverage target, larger escalation fraction, subject to
REQ-HUM-2); (c) the shortfall is written up as an instrument finding. The
rubric-iteration loop is timeboxed; "iterate until κ ≥ 0.70" is not a plan.

**REQ-CAS-3 (λ staleness):** `eval/thresholds.json` records the
`judge_prompt_hash`, `guideline_block_hash`, and `taxonomy_version` it was
calibrated under. If any differ at run time, λ is **invalid**: the harness
drops to advisory mode and says so. Conformal guarantees do not survive a
judge that no longer exists. Additionally, Phase 0/1 reports must describe
λ's guarantee as *demonstrated workflow* at calibration-set n (~50–70), not
as an operative production bound.

## A10. Phase 1 trimmed; ceremony deferred (resolves F3, F16)

- **Domains:** Phase 1 = `LEG`, `MED`, `SEC` (~36–40 scenarios incl. Phase 0's,
  with adversarial AMBER still MED/LEG-only and 4–6 contested cases).
  `STEM`, `CBRN`, `HARM/PH` authoring moves to Phase 2 — the survey found no
  real-world signal there, and their `flagged_terms` variants are the
  highest-care content for the lowest evidence.
- **Workflows:** Phase 1 ships `smoke_test.yml` only. `regression.yml` and
  `report.yml` move to Phase 2 (after there are batteries worth regressing);
  `collect.yml` remains Phase 3-disabled.
- **Review app:** Phase 1 ships the blinded labelling page and the judge
  inspector (the two measurement-integrity surfaces). Browser, calibration
  dashboard, and queue pages move to Phase 2.

## A11. WildGuard: shadow-then-promote (resolves F15)

Phase 2 runs WildGuard as a **shadow detector** for at least one full
battery — logged alongside, never gating — with a committed comparison
against the Phase 1 rules+LLM detector before promotion. Screener and
detector are promoted **separately** (two provenance events, not one).
Document the ≥16 GB RAM requirement and a hosted-inference fallback so the
runs-anywhere property survives for low-RAM users.

## A12. Scenario sourcing strategy (resolves plan_evaluation.md F18–F21; added 2026-06-12)

Supersedes the synthetic-documents-by-default posture of §12 decision 16 and
hardens the Reddit-collector deferral (decision 13) into a replacement.

**REQ-SRC-1 (four-layer sourcing):** every scenario carries a
`grounding_type` field:

1. `incident` — reconstructed from a documented real-world over-refusal
   report (journalism, vendor documentation, academic papers, public forum
   posts), captured by **periodic manual sweeps** (the SURVEY_NOTES.md
   method). No programmatic scraping at any phase; the Phase 3 collector
   item is replaced by a quarterly manual sweep task. `prompt_source` URL
   required.
2. `curriculum` — prompt derived by instantiating a shared query template
   over a subtopic of a public professional licensing/certification content
   outline (USMLE/NBME, NCLEX, NCBE MBE, CompTIA Security+/OffSec, ACS).
   The blueprint citation serves as the `classification_rationale` basis
   and `distinguishing_signal`. This layer is the coverage engine: the
   coverage matrix (REQ-SRC-3) is keyed to blueprint subtopics.
3. `document_derived` — scenario built outward from a real openly-licensed
   document (see REQ-SRC-2).
4. `generated_curated` — LLM-generated (OR-Bench-style queries;
   RefusalBench perturbation framework for document variants), always
   human-curated with analytical fields filled by hand. Used for AMBER
   counterparts, contested cases, factorial variants, and the **private
   held-out split** (synthetic/perturbed by design, for contamination
   resistance).

**REQ-SRC-2 (real documents by default):** source documents are real
public-domain or CC-BY materials, excerpted to 1–3 pp, with
`document_source` (citation + license) recorded per scenario. Default
corpora: DailyMed/FDA labels and CDC/ATSDR toxicological profiles (MED/TOX —
ATSDR is the natural authentic `flagged_terms` material), CourtListener/
RECAP opinions and released DOJ documents (LEG), CISA advisories + NVD/CVE
records + MITRE ATT&CK (SEC), OpenStax and PMC Open Access **CC-BY-filtered**
articles (MED/STEM). Synthetic documents are the exception, reserved for
controlled factorial manipulations and the private split. Only PD/CC-BY
material may enter the releasable store (Phase 4 is CC-BY-4.0); CC-BY-NC
and ND materials are excluded.

**REQ-SRC-3 (coverage matrix):** `smoke_test.yml` builds and validates a
coverage matrix (domain × subdomain × tier × grounding_type, with counts)
against per-phase minimums. Coverage is a CI artifact, not a judgment call.

**REQ-SRC-4 (external validation items):** a small adapted sample from
published chat-domain over-refusal sets (XSTest; FalseReject's 1.1k
human-annotated test split) is kept as a **validation-only** pool to
sanity-check the refusal detector and judge against published labels. These
items never enter the scenario store or any released artifact: FalseReject
is CC BY-NC 4.0, incompatible with the store's release license; they are
also query-only and not RAG scenarios.

---

## Phase table (amended)

| Phase | Theme | Key deliverables |
|-------|-------|------------------|
| **0 (new)** | Walking skeleton + illustration | validator & tests, 12–15 LEG/MED scenarios, outcome-designed fixtures, single-prompt judge, blinded labels, transcript adapter v0 + first real report card, worked example + methodology docs |
| **1** | Hardened harness (3 domains) | full judge/cascade/conformal machinery, prompt-sim adapter, second human rater, analysis_plan.md, contested cases, factorial subset, labelling + inspector pages, smoke_test.yml |
| **2** | Real-RAG + breadth | local-RAG & API adapters, WildGuard shadow→promote, STEM/CBRN/HARM-PH authoring, cross-system report, regression/report workflows, full review app |
| **3** | Closed-UI scale + deferred domains | transcript flow upgrade, YMYL/expert workflow, CRIS/EXTR/HARM-DRUG, collector, injection class |
| **4** | Scale + release | unchanged from v3 |
