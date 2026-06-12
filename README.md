# penumbra

A personal prototype for evaluating safety behaviour in document-grounded AI systems (RAG assistants). Measures both failure modes — **over-refusal** (blocking legitimate professional and educational use) and **harm** (failing to refuse genuinely harmful queries) — and treats them as co-equal problems.

> **Scope note:** This is a prototype / educational example. The system under test is selected via an adapter ([REQUIREMENTS.md §6.5](REQUIREMENTS.md)): the default fixture and prompt-sim adapters are simulations, and no conclusions about specific products (NotebookLM, Claude Projects, Copilot Notebooks) can be drawn from them. Real-system claims require the local-RAG, API, or transcript adapters, and every claim is scoped to the adapter that produced it.

---

## Research questions

This prototype is designed to generate preliminary evidence on two questions that are, as of yet, not answered in published literature clearly.

**RQ1 — Domain-conditional over-refusal in document-grounded settings**

> Does the refusal rate (full or partial) of an LLM operating as a document-grounded assistant vary systematically across professional education domains (medical, legal, security, STEM), is it elevated for AMBER-tier queries relative to GREEN-tier queries matched on topic (`topic_id` pairs, McNemar test), and is the refusal query-triggered or document-triggered (document factorial)?

RQ1 is measured **only against behaviour-producing adapters** (`system_refusal_rate_green`, live runs); fixture runs measure the judge and belong to RQ2 ([REQUIREMENTS.md §7.1](REQUIREMENTS.md)). Refusal is detected by a dedicated response-type step (full / partial compliance / full refusal) with a `refusal_reason` decomposition (safety vs. grounding-policy vs. capability). Grounded-refusal work now exists — RagRefuse (arXiv:2510.10452), COVER (ACL 2025 Findings, context- vs. query-triggered refusal), and RefusalBench (arXiv:2510.10390, perturbation-based selective-refusal evaluation including multi-document RAG) — but none of it stratifies by a structured professional-domain taxonomy or compares GREEN vs. AMBER tiers within domain; that stratification is the contribution claimed here. **Phase 1 results are hypothesis-generating** (small per-cell n; every rate reported with n and a Wilson CI); confirmatory claims wait for the powered Phase 2/3 battery sized from Phase 1 variance per the pre-registered [analysis plan](analysis_plan.md).

**RQ2 — LLM judge calibration at the ambiguous professional-context/harm boundary**

> Is agreement between an LLM safety judge and human labels — Cohen's κ reported alongside raw agreement and prevalence-robust Gwet's AC1, since κ is unstable under GREEN-tier prevalence skew — systematically lower for AMBER-tier cases than GREEN-tier cases; is the judge's verbalized confidence miscalibrated (ECE by tier); and does position-bias instability (swap augmentation) track boundary proximity as operationalized *ex ante* (adversarial flag, rater confidence at labelling time)?

Existing judge calibration studies report kappa only for clearly harmful vs. clearly safe content (SORRY-Bench, ICLR 2025: κ=0.53–0.84; HarmBench, ICML 2024: κ=0.59–0.64). No published work has isolated judge calibration specifically at the ambiguous professional-context/harm boundary, nor tested whether position bias (Wang et al., ACL 2024) is elevated there. Human ground truth is one primary rater plus a **blinded second human rater on a ≥50-item stratified subset**; the synthetic Gemini rater is reported separately as a taxonomy-coherence signal, not a human reliability estimate.

---

## Why this exists

RAG assistants present a safety profile distinct from free-form chat:

- **Source laundering** — harmful content in uploaded documents gets synthesised and re-presented with the implicit authority of the system
- **Over-refusal** — keyword-matching classifiers trained on general chat block legitimate professional and educational use at rates that constitute their own product failure

A system that refuses everything is as broken as one that allows everything. This prototype builds the infrastructure to measure both, with an explicit two-axis metric target: `system_refusal_rate_green` and `adversarial_fail_rate`, always reported together and plotted as a point on the refusal-calibration frontier. (Fixture runs report `judge_flag_rate_green` instead — a judge property, not a system property.)

---

## Evaluation approach

1. **Scenario store** — hand-authored GREEN (should never be refused) and AMBER (ambiguous; acceptable but conflated with risk) scenarios across six domains, authored as topic-matched pairs (`topic_id`), each tagged with MLCommons AILuminate hazard slugs and a document condition, and each shipping a synthetic full source document. See [REQUIREMENTS.md §3](REQUIREMENTS.md) for the taxonomy.

2. **System-under-test adapters** — the SUT is pluggable ([REQUIREMENTS.md §6.5](REQUIREMENTS.md)): fixture (seed mode; no API calls, no keys, CI default), prompt-sim (former live mode, grounded on synthetic full documents), local-RAG (real retrieval; Phase 2), API (vendor file-search; Phase 2, opt-in), and transcript (closed UIs via human-pasted responses; Phase 3). Cross-system comparison on the fixed battery is the headline output.

3. **Refusal detection + LLM judge** — a dedicated response-type step first classifies each output as full compliance / partial compliance / full refusal with a refusal reason (safety vs. grounding-policy vs. capability), then the judge evaluates guideline compliance using a cascade (cheap screener → strong judge → human escalation). Swap augmentation detects position bias; an output-length correlation check monitors verbosity bias.

4. **Calibration** — the judge is calibrated against blinded human labels (κ + raw agreement + Gwet's AC1, with judge confidence ECE) before automated results are trusted. A second human rater labels a ≥50-item subset; a synthetic second rater (`gemini-3.1-flash`) provides a taxonomy-coherence signal. The cascade's escalation threshold λ is set by conformal calibration over consistency-based confidence — never by verbalized confidence.

5. **Review app** — Streamlit interface for blinded human labelling (authored expectations hidden until the label is committed), calibration monitoring, and review queue management.

6. **Reporting** — `findings.md` for humans plus a machine-readable **RAG Refusal Report** card per system × battery version ([REQUIREMENTS.md §7.3](REQUIREMENTS.md)), so independent runs of the harness produce comparable artifacts. All rates ship with n and 95% Wilson CIs.

---

## Phase 1 scope

Six domains: `MED`, `LEG`, `SEC`, `STEM`, `CBRN`, `HARM/PH`

- GREEN + regular AMBER scenarios for all six domains, authored as topic-matched pairs with synthetic full source documents
- Adversarial AMBER (boundary cases that should be refused) for `MED` and `LEG` only
- Seed mode is the default; no API keys required for calibration runs or CI
- Blinded labelling, second human rater on a ≥50-item subset, and a pre-registered `analysis_plan.md` before the first live battery run
- The Reddit collector is **deferred to Phase 3** ([REQUIREMENTS.md §12](REQUIREMENTS.md), decision 13)

See [REQUIREMENTS.md §13](REQUIREMENTS.md) for the full phase roadmap.

---

## Harm categories — MLCommons AILuminate

Penumbra's hazard axis uses the [MLCommons AILuminate v1.0](https://mlcommons.org/benchmarks/ailuminate/) twelve-category hazard taxonomy as its controlled vocabulary: every scenario carries ≥1 `ailuminate_hazards` slug naming the hazard its content is conflated with (e.g., `MED` → `specialized_advice/health`, `CBRN` → `indiscriminate_weapons`), and judge rubric blocks are keyed by tier × hazard slug. The professional-use *domain* axis (`MED`, `LEG`, …) remains penumbra-specific — it is the over-refusal contribution. The full crosswalk is in [REQUIREMENTS.md §3.0](REQUIREMENTS.md). In NIST AI RMF terms, the harness implements the *Measure* function for the over-refusal/harm trade-off, and the calibration gates implement *Manage* controls on automation.

---

## Quick start

```bash
# Install dependencies
pip install -r requirements.txt

# Precompute judge prompt blocks (deterministic; no API keys needed)
python llm_client.py --precompute

# Validate mode: schema checks, fixtures, refusal-detector rules, metrics and
# report over committed judge-output fixtures — no API keys required (REQ-VAL-1)
python harness/run_eval.py --mode validate

# Launch review app
streamlit run review_app/app.py
```

Judged runs require a judge API key in `.env` and take real wall-clock time
(Cerebras 5 RPM: roughly 15–30 min at Phase 0 scale, ~45+ min at Phase 1
scale — see REQUIREMENTS_ADDENDUM.md §A4):
```bash
cp .env.example .env   # fill in keys
python harness/run_eval.py --mode seed   # fixture outputs, live judge
python harness/run_eval.py --mode live   # prompt-sim adapter + live judge
```

---

## Provider chains

| Role | Primary model | Provider |
|------|--------------|----------|
| Proxy | `deepseek-r1-distill-llama-70b` | Groq |
| Judge | `zai-glm-4.7` (355B) | Cerebras |
| Second rater | `gemini-3.1-flash` | Google |
| Triage | `llama-3.1-8b-instant` | Groq |

All calls go through `llm_client.py`. Switching providers requires only `.env` changes. Full chain config and rate limit intervals are in [REQUIREMENTS.md §6.1](REQUIREMENTS.md).

---

## Repo layout

```
scenarios/          Scenario store (committed; canary-tagged)
  seed/             Hand-authored scenarios + synthetic documents + fixtures
  extracted/        Reddit-extracted scenarios (Phase 3)
  risk_guidelines.md  Judge rubric source, keyed by tier × AILuminate hazard
data/
  precomputed/      Judge prompt blocks (committed; deterministic)
  results.ndjson    Eval results — gitignored
  labels.ndjson     Human + synthetic labels — gitignored
systems/            System-under-test adapters (fixture / prompt-sim / local-RAG / API / transcript)
judge/              Refusal detector, LLM judge, cascade, calibration
harness/            End-to-end eval runner
review_app/         Streamlit human-in-the-loop interface (blinded labelling)
collector/          Reddit collector and signal classifier (Phase 3 — deferred)
eval/               Metrics (Wilson CIs, κ/AC1, ECE) + thresholds.json (gates, conformal λ)
reports/            Findings report + RAG Refusal Report card schema
experiments/        Document-condition factorial + grounding fidelity
analysis_plan.md    Pre-registered RQ1/RQ2 analyses
```

---

## Safety & content scope

- **No RED-tier scenarios** are stored in this repo or sent to any API. See [REQUIREMENTS.md §2](REQUIREMENTS.md) for the full list of content exclusions.
- **Adversarial AMBER** is restricted to `MED` and `LEG` in Phase 1. These are professional education domains where the adversarial boundary involves no technical harm content.
- **Reddit collection (Phase 3 — not active)** strips author fields, truncates post bodies to 500 chars, and applies a regex pre-filter before any triage API call.
- `data/results.ndjson`, `data/labels.ndjson`, `data/collected/`, and `data/cache/` are gitignored. Only `data/precomputed/` (deterministic, no secrets) is committed.

---

## Full specification

[REQUIREMENTS.md](REQUIREMENTS.md) — complete requirements, architecture, component specs, metrics, and design decisions.

[REQUIREMENTS_ADDENDUM.md](REQUIREMENTS_ADDENDUM.md) — **v3.1 delta (current):** illustration-first restructure — Phase 0 walking skeleton, transcript adapter pulled forward, fixture outcome design, key-free `--mode validate`, `doc_condition` as run parameter, contested-case class, human-hours budgets, gate contingencies. Where it conflicts with v3, the addendum wins.

[plan_evaluation.md](plan_evaluation.md) — the assessment (findings F1–F17) that motivated v3.1.
