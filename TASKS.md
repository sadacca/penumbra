# Penumbra — Build Tasks

Task list is the execution view of **REQUIREMENTS.md v4** (consolidated,
illustration-first). Phase 0 is the immediate target; the spec is frozen
until Phase 0 artifacts exist — the next REQUIREMENTS revision is driven by
run artifacts, not further review.

---

## Phase 0 — Walking skeleton + illustration (~2 weeks elapsed, ~8 human-hours; LEG + MED only)

Build order below is normative (REQUIREMENTS §13 Phase 0). No cascade, no
conformal λ, no swap augmentation, no second rater, no prompt-sim, no
factorial in this phase. Division of labour per REQ-HUM-3: the assistant
drafts everything (scenarios, excerpts, fixtures, run sheets, docs, code);
the human reviews, blind-labels, operates the transcript battery, and
decides. Tasks marked **[H]** are the human's; everything else is drafted
by the assistant for human spot-review.

> **Status (2026-06-13):** the entire assistant-drafted skeleton (0.1, 0.3,
> 0.4, plus the authored half of 0.2/0.5/0.6) is built, runs key-free, and is
> committed. Remaining work is the human's: tier sign-off, the networked
> document fetch, blind labelling, and the transcript battery — collected in
> [`docs/HUMAN_REVIEW.md`](docs/HUMAN_REVIEW.md). `[H]` marks human-only tasks.

### 0.1 Validation first — DONE

- [x] `requirements.txt`, `.gitignore`, `.env.example`, `.devcontainer/devcontainer.json`
- [x] `scenarios/schema.md` + JSON Schema (`scenarios/scenario_schema.json`) for
      the v4 record (§4: `contested`, `grounding_type`, `prompt_source`,
      `document_source`; no `doc_condition`; extended `source` enum)
- [x] `eval/validate.py` — schema validator over `scenarios/**` + coverage
      matrix; exits nonzero on any violation; warns on `PENDING_FETCH`
- [x] Golden-value tests for `eval/metrics.py` (Wilson CI, κ, raw agreement) —
      `tests/test_metrics.py` (22 cases)
- [x] `.github/workflows/smoke_test.yml` — validator + imports + golden tests +
      fixture MANIFEST check; **no API keys**
- [x] Extracted scenarios brought to v4 conformance (added `topic_id`,
      `ailuminate_hazards`, `grounding_type`, `prompt_source`, `contested`,
      `canary`); kept in `scenarios/extracted/` with `document_source: null`
      per REQ-EXT-2 (not yet promotable)
- [x] Repo-wide canary GUID (`760abe82-…`) generated + pinned; private
      held-out split documented (§4)

### 0.2 Scenario content (16 scenarios; sourcing per REQ-SRC-1..3)

- [x] Drafted prompts: incidents + curriculum derivation (USMLE/NBME for MED;
      NCBE MBE for LEG); `grounding_type` + `prompt_source` recorded
- [ ] **[H]** Review drafted scenarios + sign off tiers; confirm each
      `[HUMAN-VERIFY citation]` blueprint reference (~1.5 h) — HUMAN_REVIEW §1
- [x] LEG: 4 GREEN + 2 AMBER (topic-paired) + 1 adversarial AMBER + 1 contested
- [x] MED: 4 GREEN + 2 AMBER (topic-paired) + 1 adversarial AMBER + 1 contested
- [x] 2 contested cases (`contested: true`, REQ-CON-1)
- [~] Real PD/CC-BY document excerpt per scenario in
      `scenarios/seed/documents/` with `document_source` citation + license +
      `SOURCES.json` fetch manifest + `eval/fetch_documents.py`. Excerpts are
      **placeholders** + `sha256: PENDING_FETCH` until the networked fetch step.
- [ ] **[H]** Run `eval/fetch_documents.py` (networked), replace placeholders
      with verbatim text, verify license + REQ-SRC-5 (~1 h) — HUMAN_REVIEW §2
- [x] Provenance headers wired (citation, URL, license, retrieval, sha256
      fields present; hashes fill on fetch)
- [x] Coverage matrix generated and CI-checked (REQ-SRC-3)
- [x] `scenarios/risk_guidelines.md` — LEG + MED blocks, keyed by
      tier × AILuminate hazard slug (13 blocks; `--precompute` parses them)

### 0.3 Fixtures as a designed instrument (REQ-FIX-1) — DONE (judge-freeze pending)

- [x] `scenarios/seed/fixtures/{scenario_id}.json` (16) with the stratified
      outcome mix (refusal-reason variety + *bad* adversarial outputs);
      response-text only — design hidden from the labeller (REQ-HUM-3)
- [x] `scenarios/seed/fixtures/MANIFEST.json` — declared mix; validated in CI
- [ ] **[H]** `scenarios/seed/judge_fixtures/` — frozen from the first judged
      run (`--mode seed --freeze-judge-fixtures`, needs a key) — HUMAN_REVIEW §6

### 0.4 Minimal pipeline — DONE

- [x] `llm_client.py` — judge chain (Cerebras→Groq), rate limiting, retries,
      usage log; proxy/second-rater raise `NotImplementedError("Phase 1")`
- [x] `python llm_client.py --precompute` — guideline blocks for LEG/MED
- [x] `systems/base.py` — `RAGSystemAdapter` protocol + `RAGResponse`
- [x] `systems/fixture_adapter.py`
- [x] `systems/transcript_adapter.py` v0 (REQ-TRN-1) + `data/transcripts/`
      TEMPLATE + README
- [x] `judge/refusal_detector.py` — rules-based v0 (`response_type` +
      `refusal_reason` + matched patterns)
- [x] `judge/judge.py` — single-prompt judge (verdict + mandatory rationale +
      logged non-gating confidence); `judge/prompts/judge_system.md` +
      `judge_user.md` (tier-conditional framing)
- [x] `harness/run_eval.py` — `--system fixture|transcript`, `--mode validate`
      (key-free, REQ-VAL-1), provenance hashes (REQ-HARNESS-1), idempotent
      appends
- [x] `eval/metrics.py` — rates with n + Wilson CI, raw agreement + κ;
      contested excluded from gate metrics (REQ-CON-1)
- [x] `reports/generate_report.py` v0 — response-type distribution,
      over-refusal table, frontier point, contested section
- [x] `reports/report_card_schema.json` v0 + schema-valid card emission
- [x] `review_app/app.py` + `pages/00_dashboard.py` — read-only prep + results
      viz (REQ-APP-10) with graceful empty states (REQ-DEV-2)

### 0.5 Labels + first real run

- [x] Blinded labelling form (`review_app/pages/01_human_labels.py`; REQ-APP-4
      blinding; 1–5 confidence; `fixture_broken`; writes `labels.ndjson`)
- [x] Assistant-prepared transcript run sheet + paste template
      (`data/transcripts/README.md` + `TEMPLATE.json`)
- [ ] **[H]** Rater_1 blind-labels all 16 fixtures (~1.5 h); raw agreement + κ
      reported (advisory); `fixture_broken` items replaced — HUMAN_REVIEW §3
- [ ] **[H]** Manual transcript battery: 10–15 hardest scenarios through a real
      NotebookLM-class UI (~2 h); emit **first real report card** — HUMAN_REVIEW §4

### 0.6 Illustration deliverables (REQ-ILL-1) — DONE

- [x] `docs/worked_example.md` — `RAG-LEG-CRIM-001` traced end-to-end with real
      validate-run artifacts
- [x] `docs/methodology.md` — practitioner guide (incl. contested-case
      interpretation)
- [x] README quick start already leads with `--mode validate` + honest
      wall-clock note for judged runs (REQ-VAL-1)
- [x] `docs/HUMAN_REVIEW.md` — the human's ordered ~8 h worklist (REQ-HUM-1/3)

### Phase 0 exit criteria

- [ ] Validator + golden-value tests pass in CI on a clean checkout
- [ ] `run_eval.py --mode validate` runs key-free in <5 min (REQ-DEV-1 rescoped)
- [ ] Judged fixture run completes; all rates carry n + Wilson CI
- [ ] All Phase 0 fixtures blind-labelled by rater_1
- [ ] First transcript-adapter report card emitted and schema-valid
- [ ] Dashboard renders coverage matrix, manifest mix, and frontier from
      real run data; graceful on empty data (REQ-APP-10)
- [ ] Worked example + methodology docs accurate against running code
- [ ] Total human time logged ≤ ~8 h (REQ-HUM-1); overrun is a finding, not
      a failure — record where it went

---

## Phase 1 — Hardened harness (LEG, MED, SEC; ~36–40 scenarios)

### Research framing
- [ ] `analysis_plan.md` — pre-registered RQ1/RQ2 analyses (§7.4), committed
      before first prompt-sim battery
- [ ] Validate §8 battery wall-clock and REQ-HUM-1 human-hours estimates
      against Phase 0 actuals; update §8 from logged usage

### Scenario content
- [ ] Expand LEG/MED to ≥8 GREEN + ≥5 AMBER each; SEC ≥6 GREEN + ≥4 AMBER
      (topic-paired; full schema)
- [ ] Adversarial AMBER: MED ≥5, LEG ≥5
- [ ] Contested cases: total 4–6 (REQ-CON-1)
- [ ] Shared `mismatched_benign` document pool (per-domain) +
      `flagged_terms` variants for the ~10-scenario factorial subset (§6.12)
- [ ] Freeze a sample of prompt-sim outputs as fixtures, preserving the
      MANIFEST mix (circularity mitigation)

### Pipeline hardening
- [ ] `systems/prompt_sim_adapter.py` + system prompt (REQ-SUT-3/4);
      full-document grounding norm; k≥3 repeats (REQ-HARNESS-4)
- [ ] Full proxy/second-rater chains in `llm_client.py` + cross-family
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
      run (§6.12)

### Labelling sprint
- [ ] Rater_1 labels full seed set (blinded)
- [ ] Recruit second human rater; ≥50-item stratified subset (REQ-CAL-5);
      human–human κ/AC1 gate
- [ ] Synthetic second rater (blinded prompt, REQ-CAL-4); reported as
      taxonomy-coherence only

### App + reports
- [ ] Review app: dashboard + blinded labelling page (from Phase 0) +
      judge inspector (REQ-APP-2/3); browser/calibration/queue pages
      deferred to Phase 2 (§6.9)
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
      separate promotion of screener and detector (§12 decision 4); document RAM
      requirement + hosted fallback
- [ ] Add `STEM`, `CBRN`, `HARM/PH` scenarios (GREEN + regular AMBER;
      moved from Phase 1 per §12 decision 10); adversarial AMBER for `SEC` + `STEM/PHYS`
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
- [ ] Formalize the quarterly **manual incident sweep** (REQ-SRC-1 layer 1;
      SURVEY_NOTES.md method) with a sweep checklist + extraction template
- [ ] Document-injection scenario class (both directions)
- [ ] Krippendorff's α once raters > 2

**Entry criteria:** Phase 2 complete; domain expert rater available.

---

## Phase 4 — Scale (500+ scenarios) + dataset release

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
