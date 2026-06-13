"""
End-to-end evaluation harness: scenario → adapter → refusal detector →
judge → results log (REQUIREMENTS.md §6.8).

Phase 0 modes:

* ``--mode validate`` (default; REQ-VAL-1, key-free): schema validation,
  fixture loading, rules-based refusal detection, frozen judge fixtures
  from ``scenarios/seed/judge_fixtures/`` when present (else
  ``SKIPPED_NO_JUDGE_FIXTURE``), metrics + console report. Zero network
  calls; runs with no .env.
* ``--mode seed``: same pipeline with a live judge via
  ``call_llm(role="judge")``. ``--freeze-judge-fixtures`` writes the judge
  outputs to ``scenarios/seed/judge_fixtures/`` so future validate runs
  replay them.

A future ``--mode full`` will additionally skip scenarios with
``adjudicated_label: null`` (REQ-EXT-3); validate/seed include all records.

Results append to ``data/results.ndjson`` with provenance hashes
(REQ-HARNESS-1) and are idempotent on (scenario_id, run_id, system_id)
(REQ-HARNESS-3). Contested scenarios are included as rows but tagged
``contested: true`` — downstream gate metrics exclude them (REQ-CON-1).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from eval.metrics import refusal_rate, wilson_ci  # noqa: E402
from judge.refusal_detector import classify  # noqa: E402
from systems.fixture_adapter import FixtureAdapter  # noqa: E402
from systems.transcript_adapter import TranscriptAdapter  # noqa: E402

RESULTS_PATH = REPO_ROOT / "data" / "results.ndjson"
JUDGE_FIXTURES_DIR = REPO_ROOT / "scenarios" / "seed" / "judge_fixtures"
GUIDELINE_BLOCKS_PATH = REPO_ROOT / "data" / "precomputed" / "guideline_blocks.json"

SKIPPED_VERDICT = "SKIPPED_NO_JUDGE_FIXTURE"


# ---------------------------------------------------------------------------
# Loading + provenance
# ---------------------------------------------------------------------------

def load_seed_scenarios(scenarios_dir: Path) -> list[dict]:
    """Load green + amber seed scenarios; empty store is fine (REQ-DEV-2)."""
    scenarios: list[dict] = []
    for name in ("green.json", "amber.json"):
        path = scenarios_dir / "seed" / name
        if not path.exists():
            continue
        try:
            with open(path) as f:
                data = json.load(f)
        except json.JSONDecodeError as exc:
            print(f"WARNING: could not parse {path}: {exc}", file=sys.stderr)
            continue
        if isinstance(data, list):
            scenarios.extend(data)
    return scenarios


def scenario_store_hash(scenarios: list[dict]) -> str:
    """sha256 over the sorted scenario JSON (battery version, REQ-HARNESS-1)."""
    canonical = json.dumps(
        sorted(scenarios, key=lambda s: s.get("scenario_id", "")),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def guideline_block_hash() -> str | None:
    """_sha256 from guideline_blocks.json; None pre-precompute."""
    if not GUIDELINE_BLOCKS_PATH.exists():
        return None
    try:
        with open(GUIDELINE_BLOCKS_PATH) as f:
            return json.load(f).get("_sha256")
    except (json.JSONDecodeError, OSError):
        return None


def get_git_sha() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT,
            capture_output=True, text=True, timeout=10,
        )
        return out.stdout.strip() or None if out.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


# ---------------------------------------------------------------------------
# Idempotent NDJSON append (REQ-HARNESS-3; factored for tests)
# ---------------------------------------------------------------------------

def existing_result_keys(path: Path) -> set[tuple[str, str, str]]:
    """(scenario_id, run_id, system_id) keys already in the results file.

    Malformed lines are skipped with a stderr warning (REQ-STORE-2).
    """
    keys: set[tuple[str, str, str]] = set()
    if not path.exists():
        return keys
    with open(path) as f:
        for i, line in enumerate(f):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                print(f"WARNING: skipping malformed results line {i + 1}",
                      file=sys.stderr)
                continue
            keys.add((row.get("scenario_id", ""), row.get("run_id", ""),
                      row.get("system_id", "")))
    return keys


def append_result_rows(path: Path, rows: list[dict]) -> int:
    """Append rows whose (scenario_id, run_id, system_id) is new; return
    the number written."""
    keys = existing_result_keys(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with open(path, "a") as f:
        for row in rows:
            key = (row.get("scenario_id", ""), row.get("run_id", ""),
                   row.get("system_id", ""))
            if key in keys:
                continue
            f.write(json.dumps(row) + "\n")
            keys.add(key)
            written += 1
    return written


# ---------------------------------------------------------------------------
# Judge verdict sources
# ---------------------------------------------------------------------------

def _frozen_judge_verdict(scenario_id: str) -> dict | None:
    """Load a frozen judge fixture (REQ-VAL-1) if one exists."""
    path = JUDGE_FIXTURES_DIR / f"{scenario_id}.json"
    if not path.exists():
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"WARNING: bad judge fixture {path}: {exc}", file=sys.stderr)
        return None


def _freeze_judge_fixture(scenario_id: str, verdict: dict) -> None:
    JUDGE_FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    with open(JUDGE_FIXTURES_DIR / f"{scenario_id}.json", "w") as f:
        json.dump({"scenario_id": scenario_id, **verdict}, f, indent=2)
        f.write("\n")


# ---------------------------------------------------------------------------
# Console summary
# ---------------------------------------------------------------------------

def _fmt_rate(stats: dict) -> str:
    if stats["n"] == 0:
        return "n=0 (no data)"
    return (f"{stats['rate']:.1%} (k={stats['k']}, n={stats['n']}, "
            f"95% CI [{stats['ci_lower']:.1%}, {stats['ci_upper']:.1%}])")


def print_summary(console: Console, rows: list[dict],
                  n_skipped_no_response: int) -> None:
    """Rich console summary (every rate ships with n + Wilson CI, §7.1)."""
    if not rows:
        console.print("[yellow]No result rows produced — scenario store or "
                      "fixtures are empty. This is fine pre-population "
                      "(REQ-DEV-2).[/yellow]")
        if n_skipped_no_response:
            console.print(f"Scenarios skipped (no response available): "
                          f"{n_skipped_no_response}")
        return

    tier_table = Table(title="Scenarios by tier")
    tier_table.add_column("Tier")
    tier_table.add_column("n", justify="right")
    tiers: dict[str, int] = {}
    for row in rows:
        tiers[row["tier"]] = tiers.get(row["tier"], 0) + 1
    for tier, n in sorted(tiers.items()):
        tier_table.add_row(tier, str(n))
    console.print(tier_table)

    rt_table = Table(title="Response-type distribution")
    rt_table.add_column("response_type")
    rt_table.add_column("n", justify="right")
    rts: dict[str, int] = {}
    for row in rows:
        rts[row["response_type"]] = rts.get(row["response_type"], 0) + 1
    for rt, n in sorted(rts.items()):
        rt_table.add_row(rt, str(n))
    console.print(rt_table)

    # GREEN refusal rate — gate metric, contested excluded (REQ-CON-1)
    green_rts = [r["response_type"] for r in rows
                 if r["tier"] == "GREEN" and not r["contested"]]
    console.print(f"[bold]Refusal rate on GREEN[/bold] "
                  f"(full + partial, contested excluded): "
                  f"{_fmt_rate(refusal_rate(green_rts))}")

    # Adversarial fail rate: adversarial AMBER (expected FAIL) judged PASS
    adv = [r for r in rows
           if r["adversarial"] and not r["contested"]
           and r["verdict"] in ("PASS", "FAIL", "UNCERTAIN")]
    k = sum(r["verdict"] == "PASS" for r in adv)
    lo, hi = wilson_ci(k, len(adv))
    adv_stats = {"n": len(adv), "k": k,
                 "rate": k / len(adv) if adv else float("nan"),
                 "ci_lower": lo, "ci_upper": hi}
    console.print(f"[bold]Adversarial fail rate[/bold] "
                  f"(adversarial AMBER judged PASS): {_fmt_rate(adv_stats)}")

    contested = [r for r in rows if r["contested"]]
    if contested:
        c_table = Table(title="Contested-case profile (excluded from gates)")
        c_table.add_column("scenario_id")
        c_table.add_column("response_type")
        c_table.add_column("verdict")
        for r in contested:
            c_table.add_row(r["scenario_id"], r["response_type"],
                            str(r["verdict"]))
        console.print(c_table)
    else:
        console.print("Contested-case profile: (no contested scenarios)")

    n_judge_skipped = sum(r["verdict"] == SKIPPED_VERDICT for r in rows)
    if n_judge_skipped:
        console.print(f"[yellow]{n_judge_skipped} row(s) have no frozen "
                      f"judge fixture (verdict={SKIPPED_VERDICT}). Run "
                      f"--mode seed --freeze-judge-fixtures to create "
                      f"them.[/yellow]")
    if n_skipped_no_response:
        console.print(f"Scenarios skipped (no response available): "
                      f"{n_skipped_no_response}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@click.command()
@click.option("--system", "system_kind",
              type=click.Choice(["fixture", "transcript"]),
              default="fixture", show_default=True)
@click.option("--system-id", default="notebooklm", show_default=True,
              help="Closed-UI system id for --system transcript.")
@click.option("--mode", type=click.Choice(["validate", "seed"]),
              default="validate", show_default=True)
@click.option("--run-id", default=None,
              help="Defaults to YYYYMMDD-HHMMSS-{mode}.")
@click.option("--scenarios-dir", default=None,
              help="Override the scenarios/ directory (default: repo).")
@click.option("--freeze-judge-fixtures", is_flag=True,
              help="(seed mode) Write judge outputs to "
                   "scenarios/seed/judge_fixtures/ for future validate runs.")
@click.option("--strict", is_flag=True,
              help="Treat scenario schema-validation errors as fatal.")
def main(system_kind: str, system_id: str, mode: str, run_id: str | None,
         scenarios_dir: str | None, freeze_judge_fixtures: bool,
         strict: bool) -> None:
    """Run the Phase 0 evaluation pipeline."""
    console = Console()
    scenarios_root = Path(scenarios_dir) if scenarios_dir else (
        REPO_ROOT / "scenarios")
    run_id = run_id or datetime.now(timezone.utc).strftime(
        f"%Y%m%d-%H%M%S-{mode}")

    # 1. Schema validation (REQ-SRC-3) — key-free, no network.
    import eval.validate as validate_mod
    console.rule("[bold]Schema validation")
    validation_rc = validate_mod.main([])
    if validation_rc != 0:
        msg = ("Scenario schema validation FAILED "
               f"(exit {validation_rc}).")
        if strict:
            console.print(f"[red]{msg}[/red]")
            sys.exit(validation_rc)
        console.print(f"[yellow]{msg} Continuing (non-strict) — the "
                      f"scenario store may be mid-edit.[/yellow]")

    # 2. Load scenarios + provenance.
    scenarios = load_seed_scenarios(scenarios_root)
    store_hash = scenario_store_hash(scenarios)
    console.print(f"Loaded {len(scenarios)} seed scenario(s); "
                  f"store hash {store_hash[:12]}…")

    # 3. Adapter.
    if system_kind == "fixture":
        adapter = FixtureAdapter(
            fixtures_dir=scenarios_root / "seed" / "fixtures")
    else:
        adapter = TranscriptAdapter(system_id=system_id)

    # 4. Judge setup (live only in seed mode — REQ-VAL-1).
    from judge.judge import judge_prompt_hash
    prompt_hash = judge_prompt_hash()
    block_hash = guideline_block_hash()
    git_sha = get_git_sha()

    judge_one = None
    guideline_blocks: dict[str, str] = {}
    if mode == "seed":
        from judge.judge import judge_one  # noqa: F811
        from llm_client import load_guideline_blocks
        guideline_blocks = load_guideline_blocks()
        if not guideline_blocks:
            console.print("[yellow]No precomputed guideline blocks — run "
                          "`python llm_client.py --precompute` first; using "
                          "the generic fallback block.[/yellow]")

    # 5. Evaluate.
    console.rule(f"[bold]Evaluation — mode={mode}, system={adapter.system_id}, "
                 f"run_id={run_id}")
    rows: list[dict] = []
    n_skipped_no_response = 0
    for scenario in scenarios:
        sid = scenario.get("scenario_id", "?")
        response = adapter.respond(scenario)
        if response is None:
            n_skipped_no_response += 1
            console.print(f"  [dim]{sid}: no response available — "
                          f"skipped[/dim]")
            continue

        detection = classify(response.response_text)

        verdict: str | None
        rationale: str | None = None
        confidence: float | None = None
        judge_model: str | None = None
        if mode == "validate":
            frozen = _frozen_judge_verdict(sid)
            if frozen is not None:
                verdict = frozen.get("verdict")
                rationale = frozen.get("rationale")
                confidence = frozen.get("confidence")
                judge_model = frozen.get("judge_model")
            else:
                verdict = SKIPPED_VERDICT
        else:  # seed: live judge
            try:
                jv = judge_one(scenario, response,
                               guideline_blocks=guideline_blocks)
            except Exception as exc:  # noqa: BLE001 — keep the battery going
                console.print(f"  [red]{sid}: judge failed — {exc}[/red]")
                verdict = "JUDGE_ERROR"
            else:
                verdict = jv["verdict"]
                rationale = jv["rationale"]
                confidence = jv["confidence"]
                judge_model = jv["judge_model"]
                if freeze_judge_fixtures:
                    _freeze_judge_fixture(sid, jv)

        rows.append({
            "result_id": str(uuid.uuid4()),
            "scenario_id": sid,
            "run_id": run_id,
            "system_id": adapter.system_id,
            "adapter": adapter.adapter_name,
            "mode": mode,
            "tier": scenario.get("tier"),
            "domain": scenario.get("domain"),
            "contested": bool(scenario.get("contested")),
            "adversarial": bool(scenario.get("adversarial")),
            "output_length": len(response.response_text),
            "response_type": detection["response_type"],
            "refusal_reason": detection["refusal_reason"],
            "matched_patterns": detection["matched_patterns"],
            "verdict": verdict,
            "rationale": rationale,
            "confidence": confidence,
            "judge_model": judge_model,
            "response_timestamp": response.timestamp,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "judge_prompt_hash": prompt_hash,
            "guideline_block_hash": block_hash,
            "scenario_store_hash": store_hash,
            "git_sha": git_sha,
        })

    # 6. Persist (idempotent — REQ-HARNESS-3).
    written = append_result_rows(RESULTS_PATH, rows)
    if rows:
        console.print(f"Wrote {written}/{len(rows)} row(s) to "
                      f"{RESULTS_PATH} (duplicates skipped).")

    # 7. Summary.
    console.rule("[bold]Summary")
    print_summary(console, rows, n_skipped_no_response)
    console.print(f"\nProvenance: judge_prompt_hash={prompt_hash[:12]}… "
                  f"guideline_block_hash="
                  f"{(block_hash or 'null')[:12]} "
                  f"git_sha={(git_sha or 'null')[:12]}")


if __name__ == "__main__":
    main()
