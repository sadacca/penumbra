# Manual Survey Notes — 2026-06-09

Manual extraction from public reports, journalism, academic papers, and community forums.
Reddit thread indexing via web search proved unreliable; results are from secondary sources.

## What was found

### Over-refusal reports (FP_REPORT)

| Scenario ID | Domain | Signal strength | Source type |
|-------------|--------|----------------|-------------|
| RAG-MED-CLIN-EXT-001 | MED/CLIN | Moderate | Academic paper (arXiv:2505.01955, Nature) |
| RAG-SEC-CVE-EXT-001 | SEC/CVE | Moderate | Community forum (Cloudflare) |
| RAG-LEG-CRIM-EXT-002 | LEG/CRIM | Weak | Substack (source returned 403, quote from snippet) |

> **Removed 2026-06-12 (REQ-SRC-5):** two DOJ-investigative-file-derived
> scenarios (RAG-LEG-CRIM-EXT-001, RAG-LEG-PROC-EXT-001) were removed
> entirely. Source documents name real private/uncharged individuals (one
> also referenced CSAM charges); that document class is excluded from the
> store — not committed, not linked. The incident class (refusals on public
> case records) remains documented motivation; LEG scenarios are built on
> published court opinions instead.

Google's own support FAQ explicitly confirms safety-flag over-refusal on source material
containing violence, sexuality, or obscenity "even in historical contexts":
https://support.google.com/notebooklm/answer/16269187

### Harm reports (HARM_REPORT) — taxonomy evidence only, not operational scenarios

| Incident | Domain | Relevance |
|----------|--------|-----------|
| Reddit Answers / heroin recommendation | HARM/MH | RED taxonomy: source laundering via RAG over UGC |
| NotebookLM hallucination (fabricated contract clauses) | LEG | Faithfulness failure, not safety classifier failure |
| NotebookLM fake podcasts | Misinformation | Content authenticity, not safety |
| EchoLeak (Copilot prompt injection) | SEC | RED taxonomy: XPIA via document |
| AgentFlayer (ChatGPT Connectors injection) | SEC | RED taxonomy: XPIA via document |
| Gemini memory poisoning | SEC | RED taxonomy: XPIA via persistent memory |
| ChatGPT-4o suicide advice | CRIS/MH | RED taxonomy: safe-messaging failure (conversational, not RAG) |

The three prompt-injection incidents (EchoLeak, AgentFlayer, Gemini) are strong
evidence for including prompt-injection-via-document in the RED taxonomy reference.

---

## Gap analysis

### Domains with real-world over-refusal signal
- **LEG** — strong. Criminal defense, public records, criminology research all documented.
- **MED** — moderate. Clinical literature synthesis documented; query details sparse.
- **SEC** — weak. Structural domain-block found, not query-level safety refusal.

### Domains with NO confirmed real-world over-refusal signal
- **STEM** (CHEM, BIO, PHYS) — nothing found
- **CBRN** (TOX, RAD) — nothing found
- **HARM/PH** — nothing found

These domains need entirely hand-authored scenarios. The absence of signal could mean:
(a) over-refusal is less common there, (b) users in those domains don't post about it,
or (c) web search indexing gaps. Hypothesis (b) is most likely for CBRN/TOX (small
professional population) and HARM/PH (stigmatised topic, users less likely to post).

### Fields missing from all extracted scenarios
- `query` — exact query text unknown for 4 of 5 records; needs hand-completion
- `source_doc_description` — approximated for all records; needs hand-completion
- `adjudicated_label` — requires human review before entering eval harness

---

## Implications for scenario authoring plan

1. **LEG and MED are grounded** — the extracted records confirm these domains have
   real over-refusal friction. Hand-author to fill: (a) exact query text for
   extracted records, (b) additional GREEN scenarios with richer persona/doc detail,
   (c) regular AMBER and adversarial AMBER (these are never posted about publicly).

2. **SEC, STEM, CBRN, HARM/PH need full hand-authoring** — no extracted signal.
   Prioritise GREEN scenarios first (demonstrate the over-refusal point), then regular AMBER.

3. **RED taxonomy** — the prompt-injection incidents (EchoLeak, AgentFlayer, Gemini)
   and Reddit Answers heroin case are strong examples for the RED taxonomy reference
   in `scenarios/taxonomy.md`. Encode them there, not as operational scenarios.

4. **Adversarial AMBER is always hand-authored** — by definition, users don't post
   publicly about cases that correctly should have been refused. All adversarial AMBER
   for MED and LEG needs to be crafted from first principles.

---

## Source quality notes
- Brian Chase (lawyer) incident: high confidence — named, confirmed by Google reinstatement
- Epstein DOJ files refusal: high confidence — explicit test methodology, comparison to other tools
- Clinical healthcare paper: high confidence — peer-reviewed, arXiv + Nature publication
- Security domain block: moderate — community forum post, not independently confirmed
- Social science researcher: low — source URL returned 403, content from search snippet only
