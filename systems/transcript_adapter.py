"""
Transcript SUT adapter (REQ-TRN-1; REQUIREMENTS.md §6.5 adapter 2).

Reads human-pasted closed-UI responses from
``data/transcripts/{system_id}/{scenario_id}.json`` (see
``data/transcripts/TEMPLATE.json`` and the README there for the paste
workflow). Slow per item, but the cheapest honest adapter and the only
honest path to claims about closed products (NotebookLM, Copilot
Notebooks). Everything from the refusal detector onward is unchanged.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from systems.base import RAGResponse

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TRANSCRIPTS_DIR = REPO_ROOT / "data" / "transcripts"


class TranscriptAdapter:
    """Replays human-captured transcripts for one closed-UI system."""

    adapter_name = "transcript"

    def __init__(self, system_id: str = "notebooklm",
                 transcripts_dir: Path | str = DEFAULT_TRANSCRIPTS_DIR) -> None:
        self.system_id = system_id
        self.transcripts_dir = Path(transcripts_dir)

    def respond(self, scenario: dict) -> RAGResponse | None:
        scenario_id = scenario["scenario_id"]
        path = self.transcripts_dir / self.system_id / f"{scenario_id}.json"
        if not path.exists():
            return None
        with open(path) as f:
            transcript = json.load(f)
        response = transcript.get("response_text")
        if not isinstance(response, str) or not response.strip():
            return None
        return RAGResponse(
            scenario_id=scenario_id,
            system_id=self.system_id,
            response_text=response,
            adapter=self.adapter_name,
            metadata={
                "operator": transcript.get("operator"),
                "captured_at": transcript.get("captured_at"),
                "ui_notes": transcript.get("ui_notes"),
                "refusal_artifacts": transcript.get("refusal_artifacts"),
                "transcript_path": str(path),
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
