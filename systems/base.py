"""
SUT adapter contract (REQUIREMENTS.md §6.5).

Everything downstream of the system under test — refusal detector, judge,
metrics, review app — is system-agnostic; the SUT sits behind
``RAGSystemAdapter``. Phase 0 adapters (fixture, transcript) replay stored
responses; behaviour-producing adapters arrive in Phase 1+ (prompt_sim,
local_rag, api).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass
class RAGResponse:
    """One SUT response to one scenario (REQ-SUT-1 core fields)."""

    scenario_id: str
    system_id: str
    response_text: str
    adapter: str
    metadata: dict = field(default_factory=dict)
    timestamp: str = ""


@runtime_checkable
class RAGSystemAdapter(Protocol):
    """Protocol every SUT adapter implements.

    ``respond`` returns None when no response is available for a scenario
    (e.g. a fixture or transcript file is missing); the harness skips the
    scenario and counts the skip.
    """

    system_id: str
    adapter_name: str

    def respond(self, scenario: dict) -> RAGResponse | None: ...
