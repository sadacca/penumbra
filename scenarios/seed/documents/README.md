# Source document excerpts

Each `*.md` file here is a 1–3 page excerpt of a **public-domain or CC-BY**
source document, used as the grounding corpus for one or more scenarios
(REQ-SRC-2). Every file carries a provenance header (citation, URL, license,
retrieval date, sha256).

## Status: PLACEHOLDERS pending fetch

The scenarios were authored in a no-network sandbox. Each excerpt below is a
**PLACEHOLDER** describing the cited sections; it is *not* the verbatim source
text. Before any judged run that depends on real document grounding:

1. On a networked machine, run `python eval/fetch_documents.py`. It downloads
   each source in `SOURCES.json`, hashes the full document, and fills
   `document_source.sha256` + `retrieved` in the scenario files.
2. Replace each placeholder excerpt with the verbatim cited sections, trimmed
   from the saved `*.full.txt`.
3. **[H] Human verification (REQ-SRC-5):** confirm license AND that the
   excerpt names no private or uncharged individuals. The court opinions here
   involve only charged/adjudicated parties — the sanctioned substitute for
   person-naming investigative files.
4. Re-run `python eval/validate.py` — no `PENDING_FETCH` should remain.

Fixture runs (`--mode validate`) and the transcript battery do **not** require
the verbatim excerpts: the SUT/transcript already contains the response, and
the fixture judge fixtures are frozen. The verbatim excerpts matter for the
prompt-sim adapter (Phase 1) and the worked example's grounding fidelity.

## Sources (all public domain)

| File | Source | Sections |
|------|--------|----------|
| `fda_acetaminophen_injection.md` | FDA label, acetaminophen injection (DailyMed) | boxed warning + overdosage |
| `fda_warfarin_label.md` | FDA label, warfarin sodium (DailyMed) | boxed warning + interactions |
| `fda_naloxone_label.md` | FDA label, naloxone nasal spray (DailyMed) | indications + administration |
| `atsdr_lead_profile.md` | ATSDR Toxicological Profile for Lead | health-effects chapter |
| `terry_v_ohio.md` | Terry v. Ohio, 392 U.S. 1 (1968) | facts, standard, holding |
| `miranda_v_arizona.md` | Miranda v. Arizona, 384 U.S. 436 (1966) | safeguards, reasoning |
| `brandenburg_v_ohio.md` | Brandenburg v. Ohio, 395 U.S. 444 (1969) | test, holding, rally footnote |
| `us_v_salerno.md` | United States v. Salerno, 481 U.S. 739 (1987) | detention holding |
