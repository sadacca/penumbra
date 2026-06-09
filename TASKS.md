# Penumbra — Build Tasks

Phase 1 is the v1 target. Later phases are listed for reference; tasks will be
detailed when each phase starts.

---

## Phase 1 — Core eval harness

### Scenario content

Approach: extraction-first, then hand-author to fill gaps.
See `scenarios/extracted/SURVEY_NOTES.md` for gap analysis from the 2026-06-09 survey.

#### Step 1 — Complete extracted scenario records (do first)
- [x] Hand-complete `scenarios/extracted/survey_2026-06-09.json` — fill `query` and
  `source_doc_description` fields for all 5 partial records; write `classification_rationale`
  where missing; move records that pass review into `scenarios/seed/`
  - 4 GREEN records → `scenarios/seed/green.json`
  - 1 AMBER record → `scenarios/seed/amber.json`
  - All `query` fields completed; `adjudicated_label` null pending calibration run
- [ ] Add RED taxonomy examples from survey harm reports to `scenarios/taxonomy.md`
  (EchoLeak/AgentFlayer prompt injection, Reddit Answers source laundering)

#### Step 2 — Taxonomy and guidelines stubs (do before hand-authoring)
- [ ] Draft `scenarios/taxonomy.md` — GREEN/AMBER/RED taxonomy with domain examples;
  include real extracted cases for LEG and MED
- [ ] Draft `scenarios/risk_guidelines.md` — stub rubric for 6 Phase 1 domains
  (MED, LEG, SEC, STEM, CBRN, HARM/PH); detail after smoke-test

#### Step 3 — Hand-author to fill gaps (extraction left these empty)

Survey signal: **LEG and MED have real-world over-refusal evidence; SEC has one
structural case; STEM, CBRN, HARM/PH have none.** Adversarial AMBER for all domains
must be hand-authored (users never post publicly about cases that correctly fail).

- [ ] Author seed GREEN scenarios (`scenarios/seed/green.json`)
  - [ ] MED: ≥6 additional scenarios (PHARM, CLIN, PATH) — 2 extracted; need ~6 more
  - [ ] LEG: ≥5 additional scenarios (PROC, CONT, CRIM) — 2 extracted; need ~5 more
  - [ ] SEC: ≥6 scenarios (CVE, FORENSIC) — 1 structural case extracted; need ~6 fresh
  - [ ] STEM: ≥6 scenarios (CHEM, BIO, PHYS) — fully hand-authored; no signal found
  - [ ] CBRN: ≥4 scenarios (TOX, RAD) — fully hand-authored; no signal found
  - [ ] HARM/PH: ≥4 scenarios — fully hand-authored; no signal found
- [ ] Author seed regular AMBER scenarios (`scenarios/seed/amber.json`)
  - [ ] MED: ≥5 scenarios
  - [ ] LEG: ≥5 scenarios (1 criminology case extracted; needs completion + 4 more)
  - [ ] SEC: ≥4 scenarios
  - [ ] STEM: ≥4 scenarios
  - [ ] CBRN: ≥3 scenarios
  - [ ] HARM/PH: ≥3 scenarios
- [ ] Author seed adversarial AMBER scenarios (MED + LEG only; append to `scenarios/seed/amber.json`)
  - [ ] MED: ≥5 adversarial scenarios (`adversarial: true`, `expected_behavior: FAIL`)
- [ ] Write proxy fixtures for all seed scenarios (`scenarios/seed/fixtures/{scenario_id}.json`)

### Infrastructure

- [ ] `requirements.txt`
- [ ] `.env.example` — API key placeholders; no secrets
- [ ] `.gitignore` — data/results.ndjson, data/labels.ndjson, data/cache/, data/collected/, .env
- [ ] `.devcontainer/devcontainer.json` — Codespaces config; mirrors REQUIREMENTS.md §9
- [ ] `llm_client.py`
  - [ ] Provider chain definitions (PROXY, JUDGE, TRIAGE, SECOND_RATER)
  - [ ] `call_llm(role, system, user)` with rate limiting and retry logic
  - [ ] Daily usage tracking to `data/cache/llm_daily_usage.json`
  - [ ] Context limit warnings (80% warn, 100% raise)
  - [ ] `precompute_blocks(source_dir, out_dir)` — parse risk_guidelines.md into block files
  - [ ] `--precompute` CLI flag
  - [ ] Startup `ConfigError` for cross-family and second-rater chain length violations

### RAG proxy

- [ ] `rag_proxy/prompts/system_prompt.md` — RAG assistant simulation prompt
- [ ] `rag_proxy/proxy.py`
  - [ ] Seed mode: read fixture from `scenarios/seed/fixtures/{scenario_id}.json`
  - [ ] Live mode: call `call_llm(role="proxy")` with source_doc_description grounding
  - [ ] REQ-PROXY-4: AMBER subdomain warning before live API call
  - [ ] Result logging: scenario_id, system_prompt_hash, user_turn, raw_response, model_used, timestamp

### Judge + cascade

- [ ] `judge/prompts/judge_system.md` — judge system prompt encoding risk guidelines
- [ ] `judge/prompts/judge_user.md` — judge user prompt template
- [ ] `judge/judge.py`
  - [ ] Verdict + rationale + confidence + flags output
  - [ ] Swap augmentation for AMBER scenarios (skip for GREEN to conserve budget)
  - [ ] `SUSPECT` verdict on swap flip; `swap_verdict_flipped` field
  - [ ] Mandatory rationale validation (raise `JudgeOutputError` on empty)
- [ ] `judge/cascade.py`
  - [ ] Regex screener → LLM judge → human review queue routing
  - [ ] Escalation threshold λ read from `eval/thresholds.py`
- [ ] `judge/calibrate.py`
  - [ ] Cohen's κ: overall, by tier, by domain
  - [ ] Recommended λ at target agreement level
  - [ ] Gate pass/fail JSON output
  - [ ] Human inter-rater κ prerequisite check

### Eval harness

- [ ] `eval/thresholds.py` — gate thresholds; adversarial AMBER held-out set IDs
- [ ] `eval/metrics.py` — fp_rate, adversarial_fail_rate, uncertain_rate, suspect_rate, kappa
- [ ] `harness/run_eval.py`
  - [ ] `--mode seed | full | tier | scenario` flags
  - [ ] Advisory mode on first run (no calibration gate JSON present)
  - [ ] Append results via `data_utils.append_result()`
  - [ ] Idempotent on scenario_id + run_id
- [ ] `harness/run_calibration.py`

### Results store + review app

- [ ] `review_app/data_utils.py` — `load_results()`, `load_labels()`, `append_result()`, `append_label()`, `get_review_queue()`
- [ ] `review_app/app.py` — Streamlit entry point and navigation
- [ ] `review_app/pages/01_scenario_browser.py` — filter, table, detail panel, export
- [ ] `review_app/pages/02_judge_inspector.py` — side-by-side; swap augmentation detail inline
- [ ] `review_app/pages/03_human_labels.py` — labelling form; writes to labels.ndjson
- [ ] `review_app/pages/04_calibration.py` — κ table, gate badges, disagreement table, trend chart
- [ ] `review_app/pages/05_review_queue.py` — queue depth, bulk actions, priority sort

### Collector

- [ ] `collector/redaction_patterns.py` — regex patterns for triage pre-filter
- [ ] `collector/reddit_collector.py` — PRAW scraper; strip author; 500-char body truncation
- [ ] `collector/signal_classifier.py` — triage call; regex pre-filter before API; route by SignalType
- [ ] `collector/scenario_extractor.py` — partial scenario record from classified post

### Reports

- [ ] `reports/generate_report.py` — produces findings.md from results.ndjson
- [ ] `reports/findings.md` — initial empty/placeholder (auto-generated thereafter)

### GitHub Actions

- [ ] `.github/workflows/smoke_test.yml` — schema validation, import check, block count check; no API keys
- [ ] `.github/workflows/regression.yml` — `run_eval.py --mode seed`; commit findings.md on metric change; open issue on threshold breach
- [ ] `.github/workflows/collect.yml` — weekly Reddit collection cron
- [ ] `.github/workflows/report.yml` — monthly report generation

### Experiments

- [ ] `experiments/doc_fidelity.py` — description-vs-real-doc proxy fidelity comparison
- [ ] `experiments/fixtures/` — public domain / openly licensed sample documents

---

### Phase 1 exit criteria

- [ ] `smoke_test.yml` passes on a clean Codespaces launch
- [ ] `run_eval.py --mode seed` completes end-to-end without errors in advisory mode
- [ ] `calibrate.py` runs and produces a gate JSON
- [ ] Streamlit app launches and shows "No results yet" gracefully on empty data files
- [ ] Full seed eval runs in under 5 minutes in Codespaces (REQ-DEV-1)
- [ ] First manual fidelity experiment run completed; results in `experiments/results/`

---

## Phase 2 — Llama Guard screener + adversarial AMBER expansion

- [ ] Replace regex screener with Llama Guard 3 (`llama-cpp-python`)
- [ ] Add `OFFSEC/PENTEST` scenarios (GREEN + regular AMBER only)
- [ ] Add adversarial AMBER for `SEC` and `STEM/PHYS`

**Entry criteria:** Phase 1 exit criteria met; calibration gates passing (κ ≥ 0.70 overall).

---

## Phase 3 — YMYL AMBER + deferred high-scrutiny domains

- [ ] YMYL AMBER scenarios (MED, LEG, MH) with domain expert review workflow
- [ ] Add deferred domains: `CRIS`, `EXTR`, `HARM/DRUG` (GREEN + regular AMBER only)
- [ ] `STEM/CHEM` adversarial AMBER (non-CBRN chemistry constraint)
- [ ] Updated `risk_guidelines.md` rubric clauses for new domains

**Entry criteria:** Phase 2 complete; domain expert rater available.

---

## Phase 4 — Scale (500+ scenarios)

- [ ] Swap augmentation sampling strategy for AMBER at scale
- [ ] Scenario deduplication pipeline
- [ ] Automated scenario quality filter

**Entry criteria:** Phase 3 complete; scenario store approaching 300+.
