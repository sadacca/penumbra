# Penumbra — Implementation Plan Evaluation (Illustration-to-Framework Goal)

**Date:** 2026-06-12
**Brief:** Hard assessment of the implementation plan (REQUIREMENTS.md v3, TASKS.md,
README.md) against this goal:

> Create a harness that effectively **illustrates how RAG applications like
> NotebookLM should be evaluated for over-refusal** (on known-good cases and on
> genuinely ambiguous cases), with **stepping stones** so it can scale from a
> simple illustration of best practices — somewhat fictional data, one human
> supporting data generation and review — to a serious harness usable as a
> framework for actual evaluation.

**Method:** Incremental review; findings are appended to this report as the
assessment proceeds. This deliberately does **not** re-litigate the prior
research-program review (`assessment.md`, 2026-06-11) — those recommendations
were applied in v3 and the measurement-validity layer is now strong. This
review applies a different lens: *illustration value, scaling-path shape, and
one-human feasibility*.

**Repo state at review time:**

- Planning docs: REQUIREMENTS.md (1,856 lines, ~50 named REQ-* requirements),
  TASKS.md (135 checkboxes, **112 in Phase 1, 0 checked**), README.md,
  assessment.md.
- Data: 4 scenarios in `scenarios/seed/` (3 GREEN, 1 AMBER, all
  incident-extracted), 5 survey extractions + notes in `scenarios/extracted/`.
- Code: **none**. No `requirements.txt`, no `llm_client.py`, no harness, no CI.

Findings are tagged `F<n>` with severity **High / Medium / Low** relative to
the stated goal (not to abstract research quality).

---

## Part A — Fit between the plan and the goal

### F1 (High) — The plan has drifted from "illustration that scales" to "research program with a prototype attached"

The goal's primary deliverable is *pedagogical*: a reader should be able to
look at this repo and understand how a NotebookLM-class application ought to
be evaluated for over-refusal. The v3 documents instead frame the project
around two publishable research questions (RQ1/RQ2), pre-registered analyses,
McNemar tests, conformal coverage guarantees, Gwet's AC1, and ECE reliability
diagrams. Each of those is individually defensible — but they are the apparatus
of a *study*, and the plan now optimizes for study validity at the cost of the
thing the goal names first: a **simple, legible illustration**.

Concrete symptom: nowhere in the 112 Phase 1 tasks is there a deliverable
whose purpose is *explanation*. There is no worked example tracing one
scenario end-to-end (authoring → document → SUT response → refusal detection →
judge verdict → calibration → report), no "how to evaluate your RAG app"
methodology document, and no demo dataset crafted so that the plots and report
cards actually show something. `findings.md` is auto-generated metrics, not
teaching material. The README's quick start is four shell commands into a
codebase that does not exist. As specified, a visitor who lands on the
finished Phase 1 repo gets a research instrument they must reverse-engineer —
not an illustration of best practices.

This matters doubly because the illustration *is* the scaling mechanism the
goal envisions: a framework grows past one human only if other people can
understand and adopt it. The plan invests heavily in adoption infrastructure
for Phase 4 (licenses, canary GUIDs, contribution guides) while skipping the
adoption surface that matters in Phase 1 (a worked example and a methodology
narrative).

### F2 (High) — There is no "simple illustration" stage at all: Phase 1 is already the serious harness

The goal describes a progression: simple illustration → serious framework.
The plan's Phase 1 *is* the serious framework minus real systems. Before
anything runs end-to-end, Phase 1 requires: ≥70 scenarios (36 GREEN + 24
AMBER + 10 adversarial) authored as topic-matched pairs; a 1–3 page synthetic
source document per scenario plus `mismatched_benign` and `flagged_terms`
factorial variants (~150–250 pages of synthetic content); a fixture per
scenario; a provider-chain LLM client with daily-usage accounting; a rules+LLM
refusal detector; swap augmentation with consistency sampling; a conformal-
calibrated cascade; a five-page Streamlit app with blinded labelling; four
GitHub Actions workflows; κ/AC1/ECE calibration with a recruited second human
rater; a pre-registered analysis plan; and a machine-readable report-card
schema.

That is months of solo work with **no intermediate point where the project
illustrates anything**. The classic failure mode for a one-person project of
this shape is to die somewhere inside Phase 1 with excellent documents, ~40%
of the checkboxes done, and nothing demonstrable. The phase structure provides
stepping stones *above* Phase 1 (adapters, domains, scale) but none *below*
it — and the goal explicitly asks for the ones below.

What is missing is a walking skeleton — call it Phase 0: one domain (LEG,
where the survey already found strong real-world signal), ~10 scenarios, the
fixture adapter, a single-prompt judge, raw-agreement calibration against one
human's blinded labels, one metric pair reported with n and CI, and a worked-
example document. That is two weeks of work, it exercises every architectural
seam (scenario schema → adapter → detector → judge → labels → metrics →
report), and it *is* the "simple illustration with somewhat fictional data and
one human" the goal describes. Everything in the current Phase 1 then becomes
hardening of a thing that already works, rather than prerequisites for a thing
that has never run.

### F3 (Medium) — The plan spends half its content budget on domains with no documented over-refusal signal, in the riskiest content areas

The project's own survey (`scenarios/extracted/SURVEY_NOTES.md`) is admirably
honest: real-world over-refusal signal is **strong for LEG, moderate for MED,
weak for SEC, and absent for STEM, CBRN, and HARM/PH**. Yet Phase 1 allocates
six domains, including ≥4 CBRN scenarios, ≥6 STEM, ≥4 HARM/PH — with synthetic
full documents whose `flagged_terms` variants are, by design, the most
delicate content to author (toxicology tables, radiological material). For an
illustration, three domains with documented real-world incidents (LEG, MED,
SEC) are more persuasive than six domains, half of them hypothetical — a real
NotebookLM refusal on public DOJ documents is worth more pedagogically than a
synthetic CBRN quiz scenario, and it carries zero authoring risk. CBRN/STEM
breadth is a Phase 2+ concern; in Phase 1 it consumes the scarcest resource
(one human's authoring and review time) on the lowest-evidence, highest-care
content.

### F4 (Medium) — "Genuinely ambiguous" cases are not a first-class category, despite being named in the goal

The goal asks the harness to illustrate evaluation on "known good cases or
genuinely ambiguous cases." The plan's tiers cover known-good (GREEN) and
known-good-but-conflated (AMBER, `expected_behavior: PASS`) plus adversarial
AMBER (`expected_behavior: FAIL`). Every battery scenario therefore has an
authored *right answer*. Genuinely contested cases — where calibrated humans
legitimately disagree and a refusal is neither clearly right nor clearly
wrong — appear only obliquely: the schema permits `expected_behavior:
UNCERTAIN` but **no metric, task, or report section consumes it**, and
disagreement-retention (REQ-CAL-6) treats disagreement as a calibration
artifact rather than a scenario class. Illustrating *how to handle* the
genuinely ambiguous case — label distributions instead of forced consensus,
abstention as a valid outcome, escalation policy — is arguably the most
instructive part of the whole exercise for a practitioner audience, and the
plan has no authored quota, no metric, and no report section for it.

---

## Part B — Internal consistency and technical findings

These are defects *within* the plan as written — things that will surface as
confusion or rework the week implementation starts.

### F5 (High) — "Seed mode requires no API keys" is impossible as specified

Three places assert key-free seed evaluation: the README quick start ("Run
seed eval (no API keys required)"), §12 decision 9 ("No API keys required for
seed eval, calibration smoke-test, or CI regression runs"), and G7. But seed
mode replaces only the **proxy** call with fixtures; the pipeline still runs
the **LLM judge** (`cerebras/zai-glm-4.7`) on every fixture that the regex
screener doesn't auto-PASS — which is, by design, every AMBER scenario and any
GREEN scenario with risk-signal surface content. A key-free seed run as
specified would produce screener auto-PASSes and nothing else. Either seed
eval needs keys (and the README/G7/decision-9 claims are wrong), or the plan
needs a third artifact — committed judge-output fixtures or a `--no-judge`
schema/plumbing check — to make the key-free claim true. Related contradiction:
REQ-DEV-1 requires the full seed eval to finish in **under 5 minutes**, while
§8's own arithmetic prices a seed-scale judge pass at **~24 minutes** (110+
calls at Cerebras's 13s interval, before swap augmentation). Both cannot hold.
This is the kind of inconsistency that matters disproportionately for an
*illustration*: the very first command in the README is the demo.

### F6 (High) — Fixture outcome design is unspecified, and calibration is degenerate without it

TASKS says only "Write SUT output fixtures for all seed scenarios."
REQ-HARNESS-2 describes fixtures as "hand-written known-good outputs." If
fixtures are uniformly good, then: (a) the refusal detector has nothing to
detect in the default/CI mode and is untested until live runs; (b) human
labels on GREEN fixtures are ~all PASS, so judge–human κ on GREEN is
undefined or degenerate (no label variance — the kappa paradox the plan
worries about, in its most extreme form); (c) `adversarial_fail_rate` in
fixture mode is meaningless unless some adversarial-AMBER fixtures are
deliberately *bad* (complying) outputs; and (d) the illustration's plots and
report cards are empty — a frontier plot with every point at the origin
teaches nothing. The fixture set needs a **designed outcome mix** — full
compliance, partial compliance, refusal (safety-, grounding-, and
capability-reasoned), good and bad — stratified per tier, exactly because it
is the judge-calibration instrument and the demo dataset. This is a one-line
omission in the plan with project-wide consequences; it should be a REQ with
target proportions.

### F7 (Medium) — `doc_condition` is simultaneously a scenario attribute and an experimental manipulation

§4 makes `doc_condition` a **required field of the scenario record**; §6.12
says each query "is run under three `doc_condition` values." Those are two
different data models: either the factorial multiplies the scenario store ×3
(and `scenario_id` needs a condition axis, and fixtures — keyed by bare
`scenario_id` — need one fixture per condition), or the condition is a run
parameter and does not belong in the scenario schema at all. The plan also
never says whether `mismatched_benign`/`flagged_terms` document variants are
authored per scenario (≈140 extra documents) or drawn from a shared pool.
Pick one model before authoring 70 scenarios against the wrong one.

### F8 (Medium) — The cost model was never recomputed for the v3 design

§8's volume table still prices the pre-v3 battery (~200 proxy + ~200 judge
calls/run). The v3 spec it sits inside requires k≥3 repeats (REQ-HARNESS-4),
m=3 consistency sampling on AMBER (§6.6.3), and — in the Phase 2 "standard
live battery" — the ×3 document factorial. At Phase 1 exit scale (≈70
scenarios), one live battery is ≈630 proxy calls and ≈1,200+ judge calls; at
Cerebras's 13-second interval that is **~4.5 hours of judge time per battery
per system**, and the headline Phase 2 deliverable is a *cross-system*
comparison (×N systems). The free-tier RPD budgets survive; the wall-clock
and the single human's attention do not. The plan should state battery
wall-clock per adapter and per phase the same way it states RPD budgets —
this is the number that actually constrains a one-person operation.

### F9 (Medium) — The committed scenario data already violates the committed schema

The four scenarios in `scenarios/seed/` predate v3 and lack every v3-required
field: `topic_id`, `ailuminate_hazards`, `doc_condition`, `canary`
(REQ-TAX-1, §4). Their `source` values (`news_extracted`,
`academic_extracted`) are not in the §4 enum (`hand_authored |
reddit_extracted | forum_extracted`). And extracted-provenance scenarios sit
in `seed/` although REQ-EXT-2 routes extracted scenarios to
`scenarios/extracted/`. None of this is individually serious — but it is the
third schema version with zero lines of validation code, and the drift has
already begun at n=4. It is direct evidence for building the schema validator
*first* (it is also the cheapest task in the repo) rather than after 70
scenarios exist.

### F10 (Medium) — Conformal λ is presented as a guarantee it cannot deliver at Phase 1 n, and its staleness policy is missing

REQ-CAS-1 has `calibrate.py` write λ "and its coverage-guarantee statement" from
a calibration set that is, at Phase 1, ~50–70 items (≥15 AMBER). A conformal
bound at that n is real but loose, and per-tier λ (which the cascade
implicitly needs — AMBER is where escalation matters) is infeasible. More
importantly: conformal validity assumes exchangeability with the calibration
distribution, and the plan's own provenance discipline (REQ-HARNESS-1, §7.2)
acknowledges that judge-prompt and rubric changes break comparability — yet
**no requirement invalidates or forces recalibration of λ when
`judge_prompt_hash` or `guideline_block_hash` changes**. As written, a rubric
tweak silently keeps gating on a λ calibrated against a judge that no longer
exists. For the illustration goal this is fine to *demonstrate as workflow*;
the documents should stop short of selling the Phase 1 λ as an operative
guarantee, and should tie λ validity to the provenance hashes.

### F11 (Low) — `pytest` is a dependency; testing appears nowhere in 135 tasks

The statistics layer (Wilson, McNemar, bootstrap CIs, κ/AC1, ECE, conformal
λ) is precisely where silent implementation bugs destroy the project's
credibility — a harness that preaches measurement discipline cannot ship an
untested `metrics.py`. There are no test-authoring tasks in any phase. A
small golden-value test suite (known inputs → hand-checked κ/CI values) plus
the schema validator would cost a day and is worth more than several of the
Phase 1 ceremony items.

*(Parts C–E appended below as the assessment proceeds.)*
