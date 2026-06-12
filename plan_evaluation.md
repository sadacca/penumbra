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

*(Parts B–D appended below as the assessment proceeds.)*
