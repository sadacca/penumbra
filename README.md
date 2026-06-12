# penumbra

A harness for evaluating safety behaviour in document-grounded AI systems (RAG assistants). Measures both failure modes — **over-refusal** (blocking legitimate professional and educational use) and **harm** (failing to refuse genuinely harmful queries) — and treats them as co-equal problems.

The project has two staged ambitions: first, a **legible illustration of how RAG applications like NotebookLM should be evaluated for over-refusal** — runnable by one person, grounded in real incidents and real documents; second, stepping stones that scale that illustration into a serious evaluation framework for open and closed RAG applications.

> **Scope note:** The system under test is selected via an adapter ([REQUIREMENTS.md §6.5](REQUIREMENTS.md)). Fixture runs measure the judge, not any product; prompt-sim runs measure a simulation. Real-system claims come from the transcript adapter (human-operated, small-n, Phase 0) and the local-RAG/API adapters (Phase 2), and every claim is scoped to the adapter that produced it.

---

## Research questions

This harness is designed to generate preliminary evidence on two questions that are, as of yet, not answered clearly in published literature.

**RQ1 — Domain-conditional over-refusal in document-grounded settings**

> Does the refusal rate (full or partial) of an LLM operating as a document-grounded assistant vary systematically across professional education domains (medical, legal, security, …), is it elevated for AMBER-tier queries relative to GREEN-tier queries matched on topic (`topic_id` pairs, McNemar test), and is the refusal query-triggered or document-triggered (document factorial)?

RQ1 is measured **only against behaviour-producing adapters** (`system_refusal_rate_green`); fixture runs measure the judge and belong to RQ2 ([REQUIREMENTS.md §7.1](REQUIREMENTS.md)). Refusal is detected by a dedicated response-type step (full / partial compliance / full refusal) with a `refusal_reason` decomposition (safety vs. grounding-policy vs. capability). Grounded-refusal work now exists — RagRefuse (arXiv:2510.10452), COVER (ACL 2025 Findings), and RefusalBench (EACL 2026, arXiv:2510.10390) — but none of it stratifies by a structured professional-domain taxonomy or compares GREEN vs. AMBER tiers within domain; that stratification is the contribution claimed here. **Phase 0–1 results are hypothesis-generating** (small per-cell n; every rate reported with n and a Wilson CI); confirmatory claims wait for the powered Phase 2/3 battery sized from observed variance per the pre-registered [analysis plan](analysis_plan.md).

**RQ2 — LLM judge calibration at the ambiguous professional-context/harm boundary**

> Is agreement between an LLM safety judge and human labels — Cohen's κ reported alongside raw agreement and prevalence-robust Gwet's AC1, since κ is unstable under GREEN-tier prevalence skew — systematically lower for AMBER-tier cases than GREEN-tier cases; is the judge's verbalized confidence miscalibrated (ECE by tier); and does position-bias instability (swap augmentation) track boundary proximity as operationalized *ex ante* (adversarial flag, rater confidence at labelling time)?

Existing judge calibration studies report kappa only for clearly harmful vs. clearly safe content (SORRY-Bench, ICLR 2025: κ=0.53–0.84; HarmBench, ICML 2024: κ=0.59–0.64). No published work has isolated judge calibration specifically at the ambiguous professional-context/harm boundary. Human ground truth is one primary rater plus a **blinded second human rater on a ≥50-item stratified subset**; the synthetic Gemini rater is reported separately as a taxonomy-coherence signal, not a human reliability estimate.

---

## Why this exists

RAG assistants present a safety profile distinct from free-form chat:

- **Source laundering** — harmful content in uploaded documents gets synthesised and re-presented with the implicit authority of the system
- **Over-refusal** — safety classifiers trained on general chat block legitimate professional and educational use at rates that constitute their own product failure

This is documented, not hypothetical: Google's NotebookLM FAQ concedes that safety flags fire on sources containing violence, sexuality, or obscenity "even in historical contexts," and reported incidents include refusals on publicly released government case records and on peer-reviewed criminology literature ([REQUIREMENTS.md §6.2](REQUIREMENTS.md); cited as motivation only — person-naming case files are excluded from the scenario store, REQ-SRC-5).

A system that refuses everything is as broken as one that allows everything. The harness measures both failure modes, with an explicit two-axis metric target: `system_refusal_rate_green` and `adversarial_fail_rate`, always reported together and plotted as a point on the refusal-calibration frontier. (Fixture runs report `judge_flag_rate_green` instead — a judge property, not a system property.)

---

## Evaluation approach

1. **Scenario store** — GREEN (should never be refused), AMBER (acceptable but conflated with risk, including adversarial boundary cases), and **contested** (genuinely ambiguous; reported by label distribution, not pass/fail) scenarios, authored as topic-matched pairs (`topic_id`) and tagged with MLCommons AILuminate hazard slugs. Sourcing is four-layer ([REQUIREMENTS.md §6.2](REQUIREMENTS.md)): real incidents (manual sweeps), professional-curriculum-derived prompts (USMLE/NCBE/Security+ content outlines — the blueprint citation *is* the tier justification), **real public-domain/CC-BY documents** (FDA labels, court opinions, CISA advisories, ATSDR profiles), and curated generation.

2. **System-under-test adapters** — the SUT is pluggable ([REQUIREMENTS.md §6.5](REQUIREMENTS.md)): fixture (outcome-designed fixtures; CI default), **transcript (Phase 0: human-pasted responses from closed UIs — the honest path to NotebookLM-class claims)**, prompt-sim (Phase 1: grounded simulation), local-RAG (real retrieval; Phase 2), and API (vendor file-search; Phase 2, opt-in). Cross-system comparison on the fixed battery is the headline output.

3. **Refusal detection + LLM judge** — a dedicated response-type step first classifies each output as full compliance / partial compliance / full refusal with a refusal reason, then the judge evaluates guideline compliance using a cascade (cheap screener → strong judge → human escalation, with a per-battery review-queue ceiling). Swap augmentation detects position bias; an output-length correlation check monitors verbosity bias.

4. **Calibration** — the judge is calibrated against blinded human labels (κ + raw agreement + Gwet's AC1, with judge confidence ECE) before automated results are trusted. A second human rater labels a ≥50-item subset. The cascade's escalation threshold λ is set by conformal calibration over consistency-based confidence — never by verbalized confidence — and is invalidated automatically when the judge prompt or rubric changes (REQ-CAS-3). If κ stalls below the gate, a documented contingency applies instead of an unbounded iteration loop (REQ-CAL-7).

5. **Review app** — from Phase 0: a read-only **dashboard** visualizing preparation (coverage matrix, fixture manifest mix, labelling progress) and evaluation (response-type distributions, over-refusal tables with CIs, the refusal-calibration frontier per system), plus blinded human labelling (authored expectations hidden until the label is committed). Judge inspection arrives in Phase 1; browser/calibration/queue pages in Phase 2.

6. **Reporting & teaching** — `findings.md` plus a machine-readable **RAG Refusal Report** card per system × battery version ([REQUIREMENTS.md §7.3](REQUIREMENTS.md)), so independent runs produce comparable artifacts. Two human-authored documents make the repo an illustration, not just an instrument: [`docs/worked_example.md`](docs/worked_example.md) (one scenario traced end-to-end) and [`docs/methodology.md`](docs/methodology.md) (how to evaluate a RAG app for over-refusal).

---

## Phase roadmap (summary)

| Phase | Theme | Scope highlights |
|-------|-------|------------------|
| **0 — Walking skeleton (~2 weeks elapsed, ~8 human-hours)** | Smallest end-to-end illustration | LEG + MED, 12–15 scenarios, validator + golden-value tests first, outcome-designed fixtures, single-prompt judge, blinded labels, **transcript adapter + first real report card against a NotebookLM-class UI**, dashboard + labelling app pages, worked example + methodology docs. The assistant drafts everything; the human reviews, labels, operates, decides (REQ-HUM-3) |
| **1 — Hardened harness** | Full measurement machinery | + SEC (~36–40 scenarios), cascade + conformal λ, swap augmentation, prompt-sim adapter, second human rater, pre-registered analysis plan, contested-case quota, factorial subset |
| **2 — Real RAG + breadth** | Framework | local-RAG + API adapters, cross-system report, WildGuard shadow→promote, STEM/CBRN/HARM-PH scenarios, regression CI |
| **3 — Closed-UI scale + deferred domains** | Coverage | transcript workflow upgrade, YMYL/domain experts, CRIS/EXTR/HARM-DRUG, document-injection class |
| **4 — Scale + release** | Community dataset | generation-with-curation, IRT difficulty, public dataset v1.0 (CC-BY-4.0 / Apache-2.0, canary, private split) |

Adversarial AMBER is restricted to `MED` and `LEG` through Phase 1. Full roadmap and entry/exit criteria: [REQUIREMENTS.md §13](REQUIREMENTS.md); execution checklist: [TASKS.md](TASKS.md).

---

## Harm categories — MLCommons AILuminate

Penumbra's hazard axis uses the [MLCommons AILuminate v1.0](https://mlcommons.org/benchmarks/ailuminate/) twelve-category hazard taxonomy as its controlled vocabulary: every scenario carries ≥1 `ailuminate_hazards` slug naming the hazard its content is conflated with (e.g., `MED` → `specialized_advice/health`), and judge rubric blocks are keyed by tier × hazard slug. The professional-use *domain* axis (`MED`, `LEG`, …) remains penumbra-specific — it is the over-refusal contribution. Full crosswalk: [REQUIREMENTS.md §3.0](REQUIREMENTS.md). In NIST AI RMF terms, the harness implements the *Measure* function for the over-refusal/harm trade-off, and the calibration gates implement *Manage* controls on automation.

---

## Quick start

```bash
# Install dependencies
pip install -r requirements.txt

# Precompute judge prompt blocks (deterministic; no API keys needed)
python llm_client.py --precompute

# Validate mode: schema + coverage matrix, fixtures, refusal-detector rules,
# metrics and report over committed judge-output fixtures — no API keys (REQ-VAL-1)
python harness/run_eval.py --mode validate

# Launch review app
streamlit run review_app/app.py
```

Judged runs require a judge API key in `.env` and take real wall-clock time
(Cerebras 5 RPM: roughly 15–30 min at Phase 0 scale, ~45+ min at Phase 1
scale — [REQUIREMENTS.md §8](REQUIREMENTS.md)):
```bash
cp .env.example .env   # fill in keys
python harness/run_eval.py --mode seed                    # fixture outputs, live judge
python harness/run_eval.py --system transcript            # human-pasted closed-UI battery
python harness/run_eval.py --mode live                    # prompt-sim adapter (Phase 1)
```

---

## Provider chains

| Role | Primary model | Provider |
|------|--------------|----------|
| Proxy (prompt-sim) | `deepseek-r1-distill-llama-70b` | Groq |
| Judge | `zai-glm-4.7` (355B) | Cerebras |
| Second rater | `gemini-3.1-flash` | Google |

Three-way provider independence by design; all calls go through `llm_client.py`; switching providers requires only `.env` changes. Full chain config and rate-limit intervals: [REQUIREMENTS.md §6.1](REQUIREMENTS.md).

---

## Repo layout

```
docs/               Worked example + methodology guide (the teaching surface)
scenarios/          Scenario store (committed; canary-tagged)
  seed/             Scenarios + real PD/CC-BY document excerpts + outcome-designed
                    fixtures (MANIFEST.json) + frozen judge fixtures
  extracted/        Manual incident-sweep extractions + survey notes
  risk_guidelines.md  Judge rubric source, keyed by tier × AILuminate hazard
data/
  precomputed/      Judge prompt blocks (committed; deterministic)
  transcripts/      Human-pasted closed-UI responses, per system
  results.ndjson    Eval results — gitignored
  labels.ndjson     Human labels — gitignored
systems/            SUT adapters (fixture / transcript / prompt-sim / local-RAG / API)
judge/              Refusal detector, LLM judge, cascade, calibration
harness/            End-to-end eval runner
review_app/         Streamlit human-in-the-loop interface (blinded labelling)
eval/               Validator + coverage matrix, metrics (Wilson CIs, κ/AC1, ECE),
                    thresholds.json (gates, conformal λ + provenance binding)
reports/            Findings report + RAG Refusal Report card schema
experiments/        Document-condition factorial + grounding fidelity
tests/              Golden-value metric tests + validator tests
analysis_plan.md    Pre-registered RQ1/RQ2 analyses (Phase 1)
```

---

## Safety & content scope

- **No RED-tier scenarios** are stored in this repo or sent to any API. See [REQUIREMENTS.md §2](REQUIREMENTS.md) for the full list of content exclusions.
- **Adversarial AMBER** is restricted to `MED` and `LEG` through Phase 1 — professional education domains where the adversarial boundary involves no technical harm content.
- **No social-media scraping at any phase.** Incident grounding is manual-sweep only, from public journalism, vendor documentation, and academic sources, with provenance URLs ([REQUIREMENTS.md §6.2](REQUIREMENTS.md)).
- **Documents are public-domain or CC-BY only** in the releasable store; NC/ND-licensed material is confined to a never-released validation pool. Committed excerpts carry provenance headers (citation, license, retrieval date, sha256). **Documents naming real private or uncharged individuals are excluded from the scenario store entirely** — not committed, not linked, even when public domain; incidents involving them are cited as motivation only, and substitute documents (published opinions, statutes, agency reports) are used instead ([REQUIREMENTS.md §6.2](REQUIREMENTS.md), REQ-SRC-5).
- `data/results.ndjson`, `data/labels.ndjson`, and `data/cache/` are gitignored. Only `data/precomputed/` and frozen judge fixtures (deterministic, no secrets) are committed.

---

## Full specification

[REQUIREMENTS.md](REQUIREMENTS.md) — **v4 (consolidated)**: complete requirements, architecture, component specs, sourcing strategy, metrics, budgets, design decisions, and the phase roadmap. [TASKS.md](TASKS.md) is the execution checklist. (The interim assessment documents that drove v3/v4 are retired; they remain in git history.)
