# penumbra

A personal prototype for evaluating safety behaviour in document-grounded AI systems (RAG assistants). Measures both failure modes — **over-refusal** (blocking legitimate professional and educational use) and **harm** (failing to refuse genuinely harmful queries) — and treats them as co-equal problems.

> **Design intent:** The harness is system-agnostic. The RAG proxy is a pluggable slot — any system that accepts a (source document, query) pair and returns text satisfies the interface. Phase 1 fills that slot with a prompt-engineered simulation so the harness can be calibrated without vendor API keys or production system access. Substituting a real RAG assistant (NotebookLM, Claude Projects, Copilot Notebooks) in that slot turns the same harness into a direct measurement instrument against that system's actual safety behaviour. No conclusions about specific products can be drawn from Phase 1 results, which use the simulated proxy only.

---

## Research questions

This prototype is designed to generate preliminary evidence on two questions that are, as of yet, not answered in published literature clearly.

**RQ1 — Domain-conditional over-refusal in professional RAG contexts**

> Does the false-positive refusal rate of AI safety classifiers vary systematically across professional education domains (medical, legal, security, STEM) in RAG settings, and is the rate elevated for AMBER-tier queries relative to GREEN-tier queries matched on topic?

Existing over-refusal benchmarks operate on general LLMs without a RAG grounding context and do not decompose results by professional domain (OR-Bench, ICML 2025; XSTest, NAACL 2024). RAG-specific over-refusal work has only emerged in 2025 — RagRefuse (arXiv:2510.10452) covers medical/chemical domains, and COVER (ACL 2025 Findings) distinguishes context- vs. query-triggered refusal — but neither uses a structured professional domain taxonomy or compares GREEN vs. AMBER tiers within the same domain. This prototype provides initial `fp_rate` estimates stratified by domain and tier across a hand-authored scenario store.

**RQ2 — LLM judge calibration at the ambiguous professional-context/harm boundary**

> Is Cohen's κ between an LLM safety judge and human labels systematically lower for AMBER-tier cases (professionally legitimate but superficially harm-resembling) than for GREEN-tier cases, and does position-bias instability (swap augmentation) correlate with proximity to the AMBER/RED decision boundary?

Existing judge calibration studies report kappa only for clearly harmful vs. clearly safe content (SORRY-Bench, ICLR 2025: κ=0.53–0.84; HarmBench, ICML 2024: κ=0.59–0.64). No published work has isolated judge calibration specifically at the ambiguous professional-context/harm boundary, nor tested whether position bias (Wang et al., ACL 2024) is elevated there. This prototype provides preliminary κ-by-tier estimates and a direct test of whether swap-augmentation instability rate tracks AMBER-tier classification difficulty.

---

## Why this exists

RAG assistants present a safety profile distinct from free-form chat:

- **Source laundering** — harmful content in uploaded documents gets synthesised and re-presented with the implicit authority of the system
- **Over-refusal** — keyword-matching classifiers trained on general chat block legitimate professional and educational use at rates that constitute their own product failure

A system that refuses everything is as broken as one that allows everything. This prototype builds the infrastructure to measure both, with an explicit two-axis metric target: `fp_rate` and `adversarial_fail_rate`, always reported together.

---

## Evaluation approach

1. **Scenario store** — hand-authored GREEN (should never be refused) and AMBER (ambiguous; acceptable but conflated with risk) scenarios across six domains. See [REQUIREMENTS.md §3](REQUIREMENTS.md) for the taxonomy.

2. **RAG proxy** — the system under evaluation. A pluggable slot: any RAG assistant that accepts (source document, query) and returns text satisfies the interface. Phase 1 fills this slot with a simulated LLM-backed proxy. Seed mode (`--mode seed`) reads pre-written fixture outputs for judge calibration — no API calls, no keys. Live mode (`--mode live`) calls the simulated proxy via the provider chain. Swapping in a real RAG assistant here measures that system's actual safety behaviour against the same scenario store and judge.

3. **LLM judge** — evaluates proxy outputs against per-domain risk guidelines using a cascade (cheap screener → strong judge → human escalation). Swap augmentation detects position bias.

4. **Calibration** — judge is calibrated against human labels (Cohen's κ) before automated results are trusted. A synthetic second rater (`gemini-3.1-flash`) provides inter-rater reliability signal.

5. **Review app** — Streamlit interface for human labelling, calibration monitoring, and review queue management.

---

## Phase 1 scope

Six domains: `MED`, `LEG`, `SEC`, `STEM`, `CBRN`, `HARM/PH`

- GREEN + regular AMBER scenarios for all six domains
- Adversarial AMBER (boundary cases that should be refused) for `MED` and `LEG` only
- Seed mode is the default; no API keys required for calibration runs or CI

See [REQUIREMENTS.md §13](REQUIREMENTS.md) for the full phase roadmap.

---

## Quick start

```bash
# Install dependencies
pip install -r requirements.txt

# Precompute judge prompt blocks (deterministic; no API keys needed)
python llm_client.py --precompute

# Run seed eval (no API keys required)
python harness/run_eval.py --mode seed

# Launch review app
streamlit run review_app/app.py
```

For live mode (requires API keys in `.env`):
```bash
cp .env.example .env   # fill in keys
python harness/run_eval.py --mode live
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
scenarios/          Scenario store (committed)
  seed/             Hand-authored scenarios + proxy fixtures
  extracted/        Reddit-extracted scenarios (auto-populated)
  risk_guidelines.md  Per-domain judge rubric source
data/
  precomputed/      Judge prompt blocks (committed; deterministic)
  results.ndjson    Eval results — gitignored
  labels.ndjson     Human + synthetic labels — gitignored
judge/              LLM judge, cascade, calibration
harness/            End-to-end eval runner
review_app/         Streamlit human-in-the-loop interface
collector/          Reddit collector and signal classifier
eval/               Metrics and gate thresholds
reports/            Auto-generated findings report
experiments/        Doc fidelity experiment
```

---

## Safety & content scope

- **No RED-tier scenarios** are stored in this repo or sent to any API. See [REQUIREMENTS.md §2](REQUIREMENTS.md) for the full list of content exclusions.
- **Adversarial AMBER** is restricted to `MED` and `LEG` in Phase 1. These are professional education domains where the adversarial boundary involves no technical harm content.
- **Reddit collection** strips author fields, truncates post bodies to 500 chars, and applies a regex pre-filter before any triage API call.
- `data/results.ndjson`, `data/labels.ndjson`, `data/collected/`, and `data/cache/` are gitignored. Only `data/precomputed/` (deterministic, no secrets) is committed.

---

## Full specification

[REQUIREMENTS.md](REQUIREMENTS.md) — complete requirements, architecture, component specs, metrics, and design decisions.
