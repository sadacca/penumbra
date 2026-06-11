# Penumbra — Build Tasks

Phase 1 is the v1 target. Later phases are listed for reference; tasks will be
detailed when each phase starts. Task list reflects REQUIREMENTS.md **v3**
(assessment-informed): metric split, SUT adapters, refusal detection, blinded
labelling, MLCommons AILuminate hazard taxonomy, document factorial, and the
Reddit collector deferred to Phase 3.

---

## Phase 1 — Core eval harness

### Research framing

- [ ] `analysis_plan.md` — pre-registered RQ1/RQ2 analyses (§7.4): primary
      metric, test, minimum effect size, null-result criteria, exploratory
      comparisons; ex-ante boundary-proximity operationalization
- [ ] Generate repo-wide canary GUID; document private held-out split process
      (§12 decision 19)

### Scenario content

- [ ] Draft `scenarios/taxonomy.md` — GREEN/AMBER/RED taxonomy with examples per domain **+ AILuminate v1.0 crosswalk table (§3.0)**
- [ ] Draft `scenarios/risk_guidelines.md` — stub rubric for 6 Phase 1 domains (MED, LEG, SEC, STEM, CBRN, HARM/PH), **keyed by tier × AILuminate hazard slug**; detail after smoke-test
- [ ] Author seed GREEN scenarios (`scenarios/seed/green.json`) — **as topic-matched pairs with AMBER (`topic_id`); every scenario carries `ailuminate_hazards`, `doc_condition`, and `canary`**
  - [ ] MED: ≥8 scenarios (PHARM, CLIN, PATH)
  - [ ] LEG: ≥8 scenarios (PROC, CONT, CRIM)
  - [ ] SEC: ≥6 scenarios (CVE, FORENSIC)
  - [ ] STEM: ≥6 scenarios (CHEM, BIO, PHYS)
  - [ ] CBRN: ≥4 scenarios (TOX, RAD)
  - [ ] HARM/PH: ≥4 scenarios
- [ ] Author seed regular AMBER scenarios (`scenarios/seed/amber.json`) — paired to GREEN via `topic_id`
  - [ ] MED: ≥5 scenarios
  - [ ] LEG: ≥5 scenarios
  - [ ] SEC: ≥4 scenarios
  - [ ] STEM: ≥4 scenarios
  - [ ] CBRN: ≥3 scenarios
  - [ ] HARM/PH: ≥3 scenarios
- [ ] Author seed adversarial AMBER scenarios (MED + LEG only; append to `scenarios/seed/amber.json`)
  - [ ] MED: ≥5 adversarial scenarios (`adversarial: true`, `expected_behavior: FAIL`)
  - [ ] LEG: ≥5 adversarial scenarios
- [ ] Author **synthetic full source documents** (`scenarios/seed/documents/`, 1–3 pp, public-domain-style) — one per scenario; plus `mismatched_benign` and `flagged_terms` variants for the document factorial (§6.12)
- [ ] Write SUT output fixtures for all seed scenarios (`scenarios/seed/fixtures/{scenario_id}.json`)
  - [ ] After first prompt-sim run: freeze a sample of live outputs as fixtures (circularity mitigation, §10.2)

### Infrastructure

- [ ] `requirements.txt` (incl. `statsmodels` for Wilson CIs / McNemar)
- [ ] `.env.example` — API key placeholders; no secrets
- [ ] `.gitignore` — data/results.ndjson, data/labels.ndjson, data/cache/, data/collected/, .env
- [ ] `.devcontainer/devcontainer.json` — Codespaces config; mirrors REQUIREMENTS.md §9
- [ ] `llm_client.py`
  - [ ] Provider chain definitions (PROXY, JUDGE, TRIAGE, SECOND_RATER)
  - [ ] `call_llm(role, system, user)` with rate limiting and retry logic
  - [ ] Daily usage tracking to `data/cache/llm_daily_usage.json`
  - [ ] Context limit warnings (80% warn, 100% raise)
  - [ ] `precompute_blocks(source_dir, out_dir)` — parse risk_guidelines.md into block files keyed by tier × hazard slug
  - [ ] `--precompute` CLI flag
  - [ ] Startup `ConfigError` for cross-family and second-rater chain length violations

### SUT adapters (`systems/`)

- [ ] `systems/base.py` — `RAGSystemAdapter` protocol, `RAGResponse` type, `system_id` / `system_config_hash` logging (REQ-SUT-1)
- [ ] `systems/fixture_adapter.py` — read fixture from `scenarios/seed/fixtures/{scenario_id}.json`
- [ ] `systems/prompt_sim_adapter.py`
  - [ ] `systems/prompts/system_prompt.md` — document-grounded simulation prompt (REQ-SUT-3)
  - [ ] Synthetic-full-document grounding as the norm; `grounding: "description"` fallback marked in results
  - [ ] REQ-SUT-4: AMBER subdomain warning before external calls
- [ ] `--system` CLI flag wiring in harness (`--mode seed` ≡ `--system fixture`)

### Refusal detection + judge + cascade

- [ ] `judge/refusal_detector.py` — `response_type` (full/partial compliance, full refusal) + `refusal_reason` (safety / grounding_policy / capability); rules + LLM v1 (REQ-JUDGE-6)
- [ ] `judge/prompts/judge_system.md` — judge system prompt encoding risk guidelines
- [ ] `judge/prompts/judge_user.md` — judge user prompt template
- [ ] `judge/judge.py`
  - [ ] response_type + refusal_reason + verdict + rationale + confidence + flags output
  - [ ] Swap augmentation for AMBER scenarios (skip for GREEN to conserve budget)
  - [ ] `SUSPECT` verdict on swap flip; `swap_verdict_flipped` field
  - [ ] Consistency confidence: m=3 samples on AMBER (swap pair + one extra) — verbalized confidence logged but never gating (§6.6.3)
  - [ ] `output_length` logging for verbosity-bias monitor (REQ-JUDGE-7)
  - [ ] Mandatory rationale validation (raise `JudgeOutputError` on empty)
- [ ] `judge/cascade.py`
  - [ ] Regex screener → refusal detector → LLM judge → human review queue routing
  - [ ] Conformal escalation threshold λ read from `eval/thresholds.json`
- [ ] `judge/calibrate.py`
  - [ ] κ overall/by tier/by domain — with raw agreement + PABAK/Gwet's AC1 and bootstrap CIs
  - [ ] Judge ECE + reliability diagram by tier (named RQ2 output)
  - [ ] Conformal λ + coverage guarantee → `eval/thresholds.json` (REQ-CAS-1)
  - [ ] Gate pass/fail JSON output
  - [ ] Human inter-rater κ/AC1 prerequisite check on the two-human subset (REQ-CAL-5)
  - [ ] Blinded second-rater prompt — excludes all authored-expectation fields (REQ-CAL-4)
  - [ ] Disagreement retention + label-distribution reporting (REQ-CAL-6)

### Eval harness

- [ ] `eval/thresholds.json` — gate thresholds, conformal λ, adversarial AMBER held-out set IDs (data artifact; REQ-CAS-1, REQ-CAL-2)
- [ ] `eval/thresholds.py` — gate logic reading thresholds.json
- [ ] `eval/metrics.py`
  - [ ] `judge_flag_rate_green` (fixture) / `system_refusal_rate_green` + `partial_compliance_rate_green` (live) — metric split per REQ-HARNESS-2
  - [ ] `adversarial_fail_rate`, `uncertain_rate`, `suspect_rate`, κ/AC1, ECE
  - [ ] Every rate emitted with n + 95% Wilson CI (bare percentage = build error)
  - [ ] McNemar paired test over `topic_id` pairs; bootstrap CIs for differences
- [ ] `harness/run_eval.py`
  - [ ] `--mode seed | full | tier | scenario` + `--system` flags
  - [ ] Advisory mode on first run (no calibration gate JSON present)
  - [ ] Append results via `data_utils.append_result()` incl. provenance hashes (`judge_prompt_hash`, `taxonomy_version`, `guideline_block_hash`, `scenario_store_version`) — REQ-HARNESS-1
  - [ ] k≥3 repeats per scenario on behaviour-producing adapters; majority verdict + instability column (REQ-HARNESS-4)
  - [ ] Idempotent on scenario_id + run_id + repeat_index
- [ ] `harness/run_calibration.py`

### Results store + review app

- [ ] `review_app/data_utils.py` — `load_results()`, `load_labels()`, `append_result()`, `append_label()`, `get_review_queue()`
- [ ] `review_app/app.py` — Streamlit entry point and navigation
- [ ] `review_app/pages/01_scenario_browser.py` — filter, table, detail panel, export
- [ ] `review_app/pages/02_judge_inspector.py` — side-by-side; swap augmentation detail inline; response_type + refusal_reason display
- [ ] `review_app/pages/03_human_labels.py` — **blinded** labelling form (REQ-APP-4: hides expected_behavior / rationale / conflation fields / adversarial flag until commit); collects 1–5 rater confidence; writes to labels.ndjson with `blinded: true`
- [ ] `review_app/pages/04_calibration.py` — κ/AC1 table, ECE display, gate badges, disagreement table, trend chart (no trend lines across provenance-hash changes)
- [ ] `review_app/pages/05_review_queue.py` — queue depth, bulk actions, priority sort

### Reports

- [ ] `reports/generate_report.py` — produces findings.md from results.ndjson
  - [ ] Response-type distribution + refusal_reason breakdown sections
  - [ ] Verbosity-bias check (output_length × verdict correlation, REQ-JUDGE-7)
  - [ ] Refusal-calibration frontier plot
  - [ ] Trend-integrity guard: annotate (don't connect) runs with differing provenance hashes
- [ ] `reports/report_card_schema.json` — machine-readable RAG Refusal Report schema (§7.3)
- [ ] Report card JSON emission per system_id × battery version
- [ ] `reports/findings.md` — initial empty/placeholder (auto-generated thereafter)

### Labelling sprint

- [ ] Rater_1 labels full seed set (blinded form)
- [ ] Recruit second human rater; label ≥50-item stratified subset (≥20 GREEN, ≥15 AMBER incl. ≥5 adversarial) — REQ-CAL-5
- [ ] Run `calibrate.py`; record human–human κ/AC1, judge κ/AC1, ECE, conformal λ

### GitHub Actions

- [ ] `.github/workflows/smoke_test.yml` — schema validation (incl. `topic_id`, `ailuminate_hazards`, `doc_condition`, `canary` required fields), import check, block count check; no API keys
- [ ] `.github/workflows/regression.yml` — `run_eval.py --mode seed`; commit findings.md on ≥1-scenario-equivalent change; **flip-based alerts** (any adversarial flip to PASS; ≥2 GREEN flips persisting across re-run) — §6.10
- [ ] `.github/workflows/report.yml` — monthly report generation
- [ ] `.github/workflows/collect.yml` — committed but **disabled** (Phase 3; §12 decision 13)

### Experiments

- [ ] `experiments/doc_fidelity.py` — document-condition factorial (matched_benign / mismatched_benign / flagged_terms) + full-doc vs description grounding-fidelity comparison (§6.12)
- [ ] `experiments/fixtures/` — public domain / openly licensed / synthetic sample documents

---

### Phase 1 exit criteria

- [ ] `smoke_test.yml` passes on a clean Codespaces launch
- [ ] `run_eval.py --mode seed` completes end-to-end without errors in advisory mode
- [ ] `calibrate.py` runs and produces a gate JSON incl. κ, AC1, ECE, conformal λ
- [ ] Blinded labelling verified — no authored-expectation fields visible pre-commit
- [ ] Second human rater subset labelled; human–human κ/AC1 reported
- [ ] `analysis_plan.md` committed before first prompt-sim battery run
- [ ] First RAG Refusal Report card emitted and schema-valid
- [ ] Streamlit app launches and shows "No results yet" gracefully on empty data files
- [ ] Full seed eval runs in under 5 minutes in Codespaces (REQ-DEV-1)
- [ ] First document-factorial / grounding-fidelity run completed; results in `experiments/results/`

---

## Phase 2 — WildGuard screener, real-RAG adapters + adversarial AMBER expansion

- [ ] Replace regex screener **and** rules+LLM refusal detector with WildGuard (`llama-cpp-python`) — §12 decision 4; validate against Phase 1 implementations on seed scenarios
- [ ] `systems/local_rag_adapter.py` — real retrieval (LlamaIndex/LangChain): multi-document + distractor passages
- [ ] `systems/api_adapter.py` — vendor file-search APIs (opt-in; per-vendor ToS review)
- [ ] First cross-system comparative report on the fixed battery (§7.3)
- [ ] Document factorial in the standard live battery
- [ ] Confirmatory per-cell n from Phase 1 variance → expand scenario store (`analysis_plan.md`)
- [ ] Add `OFFSEC/PENTEST` scenarios (GREEN + regular AMBER only)
- [ ] Add adversarial AMBER for `SEC` and `STEM/PHYS`

**Entry criteria:** Phase 1 exit criteria met; calibration gates passing (κ ≥ 0.70 overall).

---

## Phase 3 — YMYL + deferred domains, collector, injection class, transcript adapter

- [ ] YMYL AMBER scenarios (MED, LEG, MH) with domain expert review workflow
- [ ] Add deferred domains: `CRIS`, `EXTR`, `HARM/DRUG` (GREEN + regular AMBER only)
- [ ] `STEM/CHEM` adversarial AMBER (non-CBRN chemistry constraint)
- [ ] **Reddit collector ships** (§§6.2–6.4): `collector/redaction_patterns.py`, `reddit_collector.py`, `signal_classifier.py`, `scenario_extractor.py`; enable `collect.yml`
- [ ] **Document-injection scenario class** (both directions: jailbreak-via-document and induced-over-refusal-via-document; Greshake et al. 2023 / OWASP LLM01 framing)
- [ ] `systems/transcript_adapter.py` — closed-UI battery via human-pasted transcripts
- [ ] Krippendorff's α reporting once raters > 2 (REQ-CAL-6)
- [ ] Updated `risk_guidelines.md` rubric clauses for new domains

**Entry criteria:** Phase 2 complete; domain expert rater available.

---

## Phase 4 — Scale (500+ scenarios) + dataset release

- [ ] Generation-with-curation pipeline: OR-Bench-style query generation + RefusalBench-style document perturbation; human curation fills `conflation_mechanism` / `distinguishing_signal`
- [ ] IRT item-difficulty model: boundary-proximity measure for RQ2 + negative-discrimination quality filter
- [ ] Ensemble evaluator exploration (AILuminate practice; ensemble disagreement as confidence signal)
- [ ] Swap augmentation sampling strategy for AMBER at scale
- [ ] Scenario deduplication pipeline
- [ ] Automated scenario quality filter
- [ ] **Public dataset release v1.0:** semver, CC-BY-4.0 (scenarios) / Apache-2.0 (code), canary verified, private split maintained, contribution + authoring guides, stable report-card schema

**Entry criteria:** Phase 3 complete; scenario store approaching 300+.
