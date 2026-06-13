"""
Fixture SUT adapter (REQ-FIX-1; REQUIREMENTS.md §6.5 adapter 1).

Reads outcome-designed fixtures from
``scenarios/seed/fixtures/{scenario_id}.json``, each shaped::

    {"scenario_id": "...", "response": "<full SUT response text>"}

Fixture files deliberately carry NO design metadata (blinding —
intended outcomes live only in MANIFEST.json). Fixture runs measure the
*judge*, not a system: their metrics are judge-calibration metrics
(REQ-HARNESS-2, REQ-SUT-5).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from systems.base import RAGResponse

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURES_DIR = REPO_ROOT / "scenarios" / "seed" / "fixtures"


class FixtureAdapter:
    """Replays committed fixture responses. The only SUT in CI."""

    system_id = "fixture"
    adapter_name = "fixture"

    def __init__(self, fixtures_dir: Path | str = DEFAULT_FIXTURES_DIR) -> None:
        self.fixtures_dir = Path(fixtures_dir)

    def respond(self, scenario: dict) -> RAGResponse | None:
        scenario_id = scenario["scenario_id"]
        path = self.fixtures_dir / f"{scenario_id}.json"
        if not path.exists():
            return None
        with open(path) as f:
            fixture = json.load(f)
        response = fixture.get("response")
        if not isinstance(response, str):
            return None
        return RAGResponse(
            scenario_id=scenario_id,
            system_id=self.system_id,
            response_text=response,
            adapter=self.adapter_name,
            metadata={"fixture_path": str(path)},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
