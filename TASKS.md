# Penumbra — Build Tasks

Task list reflects REQUIREMENTS.md **v3** as amended by
**REQUIREMENTS_ADDENDUM.md v3.1** (illustration-first restructure, implementing
`plan_evaluation.md` R1–R12). Phase 0 is the immediate target; the spec is
frozen until Phase 0 artifacts exist (R1).

---

## Phase 0 — Walking skeleton + illustration (~2 weeks; LEG + MED only)

Build order below is normative (A1). No cascade, no conformal λ, no swap
augmentation, no second rater, no prompt-sim, no factorial in this phase.

### 0.1 Validation first

- [ ] `requirements.txt`, `.gitignore`, `.env.example`, `.devcontainer/devcontainer.json`
- [ ] `scenarios/schema.md` + JSON Schema file for the v3 scenario record
      (with v3.1 amendments: no `doc_condition` field; `contested` flag added;
      `source` enum extended to cover `news_extracted` / `academic_extracted`)
- [ ] `eval/validate.py` — schema validator over `scenarios/**`; exits nonzero
      on any violation
- [ ] Golden-value tests for `eval/metrics.py` (hand-checked Wilson CI, κ,
      raw agreement on tiny known inputs) — `tests/test_metrics.py`
- [ ] `.github/workflows/smoke_test.yml` — validator + imports + fixture
      MANIFEST check; **no API keys**
- [ ] Bring the 4 committed scenarios into v3.1 conformance (add `topic_id`,
      `ailuminate_hazards`, `canary`; fix `source` enum) or relocate to
      `scenarios/extracted/` per REQ-EXT-2
- [ ] Generate repo-wide canary GUID; document private held-out split process

### 0.2 Scenario content (12–15 scenarios; sourcing per REQ-SRC-1..3)

- [ ] Prompt sourcing: incidents from the existing survey + curriculum
      derivation (USMLE/NBME outline for MED; NCBE MBE outline for LEG);
      record `grounding_type` + `prompt_source`
- [ ] LEG: 4 GREEN + 2 AMBER (topic-paired), 1 adversarial AMBER
- [ ] MED: 4 GREEN + 2 AMBER (topic-paired), 1 adversarial AMBER
- [ ] 1–2 contested cases (`contested: true`, REQ-CON-1)
- [ ] One **real PD/CC-BY document excerpt** per scenario (1–3 pp) in
      `scenarios/seed/documents/` with `document_source` citation + license
      (REQ-SRC-2: DailyMed/ATSDR for MED, CourtListener/DOJ for LEG);
      synthetic only where no suitable source exists
- [ ] Coverage matrix generated and CI-checked (REQ-SRC-3)
- [ ] `scenarios/risk_guidelines.md` — LEG + MED blocks only, keyed by
      tier × AILuminate hazard slug

### 0.3 Fixtures as a designed instrument (REQ-FIX-1)

- [ ] `scenarios/seed/fixtures/{scenario_id}.json` with the stratified
      outcome mix from addendum A3 (incl. refusal-reason variety and *bad*
      adversarial outputs)
- [ ] `scenarios/seed/fixtures/MANIFEST.json` — declared mix; validated in CI
- [ ] `scenarios/seed/judge_fixtures/` — committed judge outputs frozen from
      the first real judged run (enables `--mode validate`, REQ-VAL-1)

### 0.4 Minimal pipeline

- [ ] `llm_client.py` — judge chain only for Phase 0 (`call_llm(role="judge")`,
      rate limiting, retries, usage log); proxy/triage/second-rater chains stubbed
- [ ] `python llm_client.py --precompute` — guideline blocks for LEG/MED
- [ ] `systems/base.py` — `RAGSystemAdapter` protocol + `RAGResponse`
- [ ] `systems/fixture_adapter.py`
- [ ] `systems/transcript_adapter.py` v0 (REQ-TRN-1) + paste template +
      `data/transcripts/` layout
- [ ] `judge/refusal_detector.py` — rules-based v0 (`response_type` +
      `refusal_reason`)
- [ ] `judge/judge.py` — single-prompt judge: verdict + mandatory rationale +
      logged (non-gating) confidence; `judge/prompts/judge_system.md` +
      `judge_user.md` (tier-conditional framing incl. GREEN/AMBER blocks)
- [ ] `harness/run_eval.py` — `--system fixture|transcript`,
      `--mode validate` (key-free, REQ-VAL-1), provenance hashes
      (REQ-HARNESS-1), idempotent appends
- [ ] `eval/metrics.py` — rates with n + Wilson CI (bare percentage = error),
      raw agreement + κ; contested cases excluded from gate metrics (REQ-CON-1)
- [ ] `reports/generate_report.py` v0 — response-type distribution,
      over-refusal table, frontier point, contested-case section
- [ ] `reports/report_card_schema.json` v0 + first card emission

### 0.5 Labels + first real run

- [ ] Blinded labelling form (single Streamlit page **or** CLI; REQ-APP-4
      blinding rules in full; 1–5 rater confidence; writes `labels.ndjson`)
- [ ] Rater_1 blind-labels all Phase 0 fixtures; raw agreement + κ reported
      (advisory)
- [ ] Manual transcript battery: run the 10–15 hardest scenarios through a
      real NotebookLM-class UI; emit **first real report card**

### 0.6 Illustration deliverables (REQ-ILL-1)

- [ ] `docs/worked_example.md` — one scenario traced end-to-end with real
      artifacts
- [ ] `docs/methodology.md` — practitioner guide to RAG over-refusal
      evaluation (incl. contested-case interpretation)
- [ ] README quick start updated to lead with `--mode validate` and the
      worked example; honest wall-clock note for judged runs (A4)

### Phase 0 exit criteria

- [ ] Validator + golden-value tests pass in CI on a clean checkout
- [ ] `run_eval.py --mode validate` runs key-free in <5 min (REQ-DEV-1 rescoped)
- [ ] Judged fixture run completes; all rates carry n + Wilson CI
- [ ] All Phase 0 fixtures blind-labelled by rater_1
- [ ] First transcript-adapter report card emitted and schema-valid
- [ ] Worked example + methodology docs accurate against running code

---

## Phase 1 — Hardened harness (LEG, MED, SEC; ~36–40 scenarios)

### Research framing
- [ ] `analysis_plan.md` — pre-registered RQ1/RQ2 analyses (§7.4), committed
      before first prompt-sim battery
- [ ] Recompute §8 cost table for the v3 design; add battery wall-clock per
      adapter and the human-hours budget table (REQ-HUM-1)

### Scenario content
- [ ] Expand LEG/MED to ≥8 GREEN + ≥5 AMBER each; SEC ≥6 GREEN + ≥4 AMBER
      (topic-paired; full schema)
- [ ] Adversarial AMBER: MED ≥5, LEG ≥5
- [ ] Contested cases: total 4–6 (REQ-CON-1)
- [ ] Shared `mismatched_benign` document pool (per-domain) +
      `flagged_terms` variants for the ~10-scenario factorial subset (A5)
- [ ] Freeze a sample of prompt-sim outputs as fixtures, preserving the
      MANIFEST mix (circularity mitigation)

### Pipeline hardening
- [ ] `systems/prompt_sim_adapter.py` + system prompt (REQ-SUT-3/4);
      full-document grounding norm; k≥3 repeats (REQ-HARNESS-4)
- [ ] Full proxy/triage/second-rater chains in `llm_client.py` + cross-family
      `ConfigError` checks
- [ ] Swap augmentation + SUSPECT verdict; consistency confidence m=3 on AMBER
- [ ] `judge/cascade.py` — screener → detector → judge → queue; λ from
      `eval/thresholds.json`; queue ceiling (REQ-HUM-2)
- [ ] `judge/calibrate.py` — κ/AC1 + bootstrap CIs, ECE by tier, conformal λ
      with provenance binding (REQ-CAS-3) and gate JSON; κ contingency policy
      (REQ-CAL-7)
- [ ] `eval/thresholds.json` + `eval/thresholds.py`; held-out adversarial set
      (REQ-CAL-2)
- [ ] McNemar over `topic_id` pairs; bootstrap difference CIs
- [ ] `experiments/doc_fidelity.py` — factorial subset + grounding-fidelity
      run (§6.12, scoped per A5)

### Labelling sprint
- [ ] Rater_1 labels full seed set (blinded)
- [ ] Recruit second human rater; ≥50-item stratified subset (REQ-CAL-5);
      human–human κ/AC1 gate
- [ ] Synthetic second rater (blinded prompt, REQ-CAL-4); reported as
      taxonomy-coherence only

### App + reports
- [ ] Review app: blinded labelling page (from Phase 0) + judge inspector
      (REQ-APP-2/3); other pages deferred to Phase 2 (A10)
- [ ] `generate_report.py`: refusal_reason breakdown, verbosity-bias check
      (REQ-JUDGE-7), trend-integrity guard, full report card (§7.3)

### Phase 1 exit criteria
- [ ] Phase 0 criteria still green
- [ ] `calibrate.py` produces gate JSON (κ, AC1, ECE, λ + provenance binding)
- [ ] Second human rater subset labelled; human–human κ/AC1 reported
- [ ] First prompt-sim battery + factorial-subset run complete, within the
      stated human-hours and queue ceiling
- [ ] `analysis_plan.md` committed before that battery

---

## Phase 2 — Real-RAG adapters, WildGuard, domain breadth

- [ ] `systems/local_rag_adapter.py` (real retrieval, multi-doc, distractors)
- [ ] `systems/api_adapter.py` (opt-in, per-vendor ToS)
- [ ] First cross-system comparative report on the fixed battery
- [ ] WildGuard **shadow** detector for ≥1 full battery; committed comparison;
      separate promotion of screener and detector (A11); document RAM
      requirement + hosted fallback
- [ ] Add `STEM`, `CBRN`, `HARM/PH` scenarios (GREEN + regular AMBER;
      moved from Phase 1 per A10); adversarial AMBER for `SEC` + `STEM/PHYS`
- [ ] `OFFSEC/PENTEST` (GREEN + regular AMBER only)
- [ ] Document factorial in the standard live battery
- [ ] Confirmatory per-cell n from Phase 1 variance → expand store
- [ ] Remaining review-app pages (browser, calibration dashboard, queue)
- [ ] `.github/workflows/regression.yml` (flip-based alerts) + `report.yml`

**Entry criteria:** Phase 1 exit met; calibration gates passing **or**
REQ-CAL-7 contingency mode formally adopted and documented.

---

## Phase 3 — Closed-UI scale, YMYL + deferred domains, collector, injection

- [ ] Transcript flow upgrade: entry form in review app, multi-system
      transcript management (adapter itself shipped in Phase 0)
- [ ] YMYL AMBER (MED, LEG, MH) with domain-expert workflow
- [ ] Deferred domains: `CRIS`, `EXTR`, `HARM/DRUG` (GREEN + regular AMBER)
- [ ] `STEM/CHEM` adversarial AMBER (non-CBRN constraint)
- [ ] ~~Reddit collector~~ → replaced by quarterly **manual incident sweep**
      (REQ-SRC-1 layer 1; SURVEY_NOTES.md method); `collect.yml` removed
- [ ] Document-injection scenario class (both directions)
- [ ] Krippendorff's α once raters > 2

**Entry criteria:** Phase 2 complete; domain expert rater available.

---

## Phase 4 — Scale (500+ scenarios) + dataset release

Unchanged from v3:

- [ ] Generation-with-curation pipeline (OR-Bench-style queries +
      RefusalBench-style document perturbation; human curation fills
      analytical fields)
- [ ] IRT item-difficulty model; negative-discrimination filter
- [ ] Ensemble evaluator exploration
- [ ] Swap-augmentation sampling strategy at scale; dedup; quality filter
- [ ] Public dataset release v1.0 (semver, CC-BY-4.0 / Apache-2.0, canary
      verified, private split, contribution + authoring guides, stable
      report-card schema)

**Entry criteria:** Phase 3 complete; store approaching 300+.
