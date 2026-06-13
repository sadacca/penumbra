"""
Single gateway for all LLM API calls (REQ-LLM-1).

Phase 0 implements the judge chain only:

    JUDGE_CHAIN:
      cerebras/zai-glm-4.7            (primary;  env CEREBRAS_API_KEY)
      groq/llama-3.3-70b-versatile    (fallback; env GROQ_API_KEY)

Roles "proxy" and "second_rater" are stubbed until Phase 1 (§6.1 phase
scoping). Provider SDKs are imported lazily inside the provider functions so
the module imports cleanly without them (e.g. in `--mode validate`, which is
key-free per REQ-VAL-1).

Every successful call appends a usage row to ``data/cache/usage.ndjson``
(gitignored; REQ-LLM-2 — a call that succeeds but fails to log is a soft
error on stderr).

CLI:
    python llm_client.py --precompute
        Parse scenarios/risk_guidelines.md (H2 headings of the exact form
        ``## {TIER} × {hazard_slug}``) into
        data/precomputed/guideline_blocks.json. Deterministic, no API calls
        (REQ-JUDGE-5 / §6.6.2).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
RISK_GUIDELINES_PATH = REPO_ROOT / "scenarios" / "risk_guidelines.md"
GUIDELINE_BLOCKS_PATH = REPO_ROOT / "data" / "precomputed" / "guideline_blocks.json"
USAGE_LOG_PATH = REPO_ROOT / "data" / "cache" / "usage.ndjson"

# Per-provider minimum interval between calls, in seconds (§6.1 rate limits).
# Cerebras free tier is ~5 RPM ⇒ 12 s between calls.
MIN_INTERVAL_S: dict[str, float] = {
    "cerebras": 12.0,
    "groq": 6.0,
}

MAX_ATTEMPTS_PER_PROVIDER = 3  # exponential backoff: 2s, 4s between attempts

# Judge chain, in priority order: (provider, model).
JUDGE_CHAIN: list[tuple[str, str]] = [
    ("cerebras", "zai-glm-4.7"),
    ("groq", "llama-3.3-70b-versatile"),
]

_last_call_at: dict[str, float] = {}


class LLMChainExhaustedError(RuntimeError):
    """Raised when every provider in the chain failed for a call."""


# ---------------------------------------------------------------------------
# Provider calls (SDKs imported lazily — REQ-VAL-1 key-free imports)
# ---------------------------------------------------------------------------

def _call_cerebras(model: str, system: str, user: str,
                   temperature: float, max_tokens: int) -> dict:
    from cerebras.cloud.sdk import Cerebras  # lazy: may be missing in CI

    api_key = os.environ.get("CEREBRAS_API_KEY")
    if not api_key:
        raise RuntimeError("CEREBRAS_API_KEY not set")
    client = Cerebras(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    usage = getattr(resp, "usage", None)
    return {
        "text": resp.choices[0].message.content or "",
        "usage": dict(usage) if isinstance(usage, dict) else (
            usage.model_dump() if hasattr(usage, "model_dump") else {}
        ),
    }


def _call_groq(model: str, system: str, user: str,
               temperature: float, max_tokens: int) -> dict:
    from groq import Groq  # lazy: may be missing in CI

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set")
    client = Groq(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    usage = getattr(resp, "usage", None)
    return {
        "text": resp.choices[0].message.content or "",
        "usage": usage.model_dump() if hasattr(usage, "model_dump") else {},
    }


_PROVIDER_FUNCS = {
    "cerebras": _call_cerebras,
    "groq": _call_groq,
}


# ---------------------------------------------------------------------------
# Rate limiting / retries / usage log
# ---------------------------------------------------------------------------

def _respect_rate_limit(provider: str) -> None:
    """Sleep until the per-provider minimum interval has elapsed."""
    min_interval = MIN_INTERVAL_S.get(provider, 6.0)
    last = _last_call_at.get(provider)
    if last is not None:
        wait = min_interval - (time.monotonic() - last)
        if wait > 0:
            time.sleep(wait)


def _log_usage(row: dict) -> None:
    """Append a usage row to data/cache/usage.ndjson (REQ-LLM-2; soft error)."""
    try:
        USAGE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(USAGE_LOG_PATH, "a") as f:
            f.write(json.dumps(row) + "\n")
    except OSError as exc:  # soft error per REQ-LLM-2
        print(f"WARNING: failed to log LLM usage: {exc}", file=sys.stderr)


def call_llm(role: str, system: str, user: str, *,
             temperature: float = 0.0, max_tokens: int = 2048) -> dict:
    """Route a call through the chain for ``role``.

    Args:
        role: "judge" (Phase 0). "proxy" / "second_rater" raise
            NotImplementedError until Phase 1.
        system / user: prompt parts.

    Returns:
        dict with keys: text, model, provider, usage.

    Raises:
        LLMChainExhaustedError: every chain member failed.
    """
    if role in ("proxy", "second_rater"):
        raise NotImplementedError("Phase 1")
    if role != "judge":
        raise ValueError(f"Unknown role: {role!r}")

    errors: list[str] = []
    for provider, model in JUDGE_CHAIN:
        func = _PROVIDER_FUNCS[provider]
        for attempt in range(MAX_ATTEMPTS_PER_PROVIDER):
            _respect_rate_limit(provider)
            try:
                _last_call_at[provider] = time.monotonic()
                result = func(model, system, user, temperature, max_tokens)
            except Exception as exc:  # noqa: BLE001 — provider SDKs vary
                errors.append(f"{provider}/{model} attempt {attempt + 1}: {exc}")
                if not _is_transient(exc):
                    break  # auth/config errors: skip remaining attempts
                if attempt < MAX_ATTEMPTS_PER_PROVIDER - 1:
                    time.sleep(2 ** (attempt + 1))  # 2s, 4s
                continue
            _log_usage({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "role": role,
                "provider": provider,
                "model": model,
                "prompt_chars": len(system) + len(user),
                "completion_chars": len(result["text"]),
                "usage": result.get("usage", {}),
            })
            return {
                "text": result["text"],
                "model": model,
                "provider": provider,
                "usage": result.get("usage", {}),
            }
    raise LLMChainExhaustedError(
        "All judge-chain providers failed:\n  " + "\n  ".join(errors)
    )


def _is_transient(exc: Exception) -> bool:
    """Heuristic: retry on 429/5xx/connection errors; skip on auth/config."""
    status = getattr(exc, "status_code", None) or getattr(exc, "status", None)
    if isinstance(status, int):
        return status == 429 or status >= 500
    if isinstance(exc, (ConnectionError, TimeoutError)):
        return True
    msg = str(exc).lower()
    if "api_key" in msg or "api key" in msg or "unauthorized" in msg:
        return False
    return "rate limit" in msg or "timeout" in msg or "connection" in msg


# ---------------------------------------------------------------------------
# --precompute: risk_guidelines.md → guideline_blocks.json (deterministic)
# ---------------------------------------------------------------------------

# Heading form: ## {TIER} × {hazard_slug}  (accepts × or x as the separator)
_HEADING_RE = re.compile(r"^##\s+(GREEN|AMBER)\s*[×x]\s*(\S+)\s*$")


def parse_guideline_blocks(source_path: Path) -> dict[str, str]:
    """Parse risk_guidelines.md into {"{TIER}|{hazard_slug}": guidance, ...}.

    Adds a top-level "_sha256" key with the hash of the source file bytes
    (provenance for guideline_block_hash, REQ-HARNESS-1 / REQ-CAS-3).
    Deterministic — no API calls (REQ-JUDGE-5).
    """
    raw = source_path.read_bytes()
    blocks: dict[str, str] = {"_sha256": hashlib.sha256(raw).hexdigest()}

    current_key: str | None = None
    current_lines: list[str] = []

    def _flush() -> None:
        if current_key is not None:
            blocks[current_key] = "\n".join(current_lines).strip()

    for line in raw.decode("utf-8").splitlines():
        m = _HEADING_RE.match(line)
        if m:
            _flush()
            current_key = f"{m.group(1)}|{m.group(2)}"
            current_lines = []
        elif line.startswith("## "):
            _flush()
            current_key = None  # non-block H2: stop collecting
        elif current_key is not None:
            current_lines.append(line)
    _flush()
    return blocks


def precompute(source_path: Path = RISK_GUIDELINES_PATH,
               out_path: Path = GUIDELINE_BLOCKS_PATH) -> int:
    """CLI entry for --precompute. Returns a process exit code."""
    if not source_path.exists():
        print(
            f"ERROR: {source_path} not found — cannot precompute guideline "
            f"blocks. Author scenarios/risk_guidelines.md first (§6.6.2).",
            file=sys.stderr,
        )
        return 1
    blocks = parse_guideline_blocks(source_path)
    n_blocks = len(blocks) - 1  # minus "_sha256"
    if n_blocks == 0:
        print(
            f"ERROR: no '## {{TIER}} × {{hazard_slug}}' headings found in "
            f"{source_path}.",
            file=sys.stderr,
        )
        return 1
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(blocks, f, indent=2, sort_keys=True)
        f.write("\n")
    print(f"Wrote {n_blocks} guideline block(s) to {out_path}")
    return 0


def load_guideline_blocks(path: Path = GUIDELINE_BLOCKS_PATH) -> dict[str, str]:
    """Load precomputed blocks; empty dict if not yet generated."""
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--precompute", action="store_true",
        help="Parse scenarios/risk_guidelines.md into guideline_blocks.json",
    )
    args = parser.parse_args(argv)
    if args.precompute:
        return precompute()
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
