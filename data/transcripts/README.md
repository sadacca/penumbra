# Transcript paste workflow (REQ-TRN-1)

This directory holds human-captured responses from **closed-UI** RAG
products (NotebookLM, Copilot Notebooks, …) — the only honest path to
claims about systems we cannot call programmatically. The transcript
adapter (`systems/transcript_adapter.py`) replays these files; everything
from the refusal detector onward is identical to other adapters.

## Layout

```
data/transcripts/
├── TEMPLATE.json                 # copy this per capture
├── README.md                     # this file
└── {system_id}/                  # e.g. notebooklm/
    └── {scenario_id}.json        # one file per scenario
```

## Per-scenario workflow (~10–15 min/scenario)

1. Open the target UI and start a fresh session/notebook.
2. Upload/attach the scenario's source document (see the scenario's
   `document_source` in `scenarios/seed/*.json`).
3. Paste the scenario's `query` field **verbatim** — no rephrasing.
4. Copy `data/transcripts/TEMPLATE.json` to
   `data/transcripts/{system_id}/{scenario_id}.json`.
5. Fill it in:
   - `response_text` — the full response, verbatim, even if truncated or
     partial. If the UI refused outright with no response body, leave the
     refusal message itself here too.
   - `refusal_artifacts` — the **verbatim** text of any refusal banner,
     safety-flag message, or blocked-content notice the UI displayed.
     This is load-bearing: banner text distinguishes safety refusals from
     grounding/capability declines.
   - `ui_notes` — UI name + version/build date and anything odd
     (latency, retries, partial rendering).
   - `operator` / `captured_at` — who captured it, ISO 8601 timestamp.
6. Run the battery:

   ```bash
   python harness/run_eval.py --system transcript --system-id {system_id} --mode seed
   ```

   (or `--mode validate` for a key-free detector-only pass).

Notes: do **not** edit or "clean up" responses; capture exactly what the
UI showed. One file per scenario; missing files are skipped and counted
by the harness.
