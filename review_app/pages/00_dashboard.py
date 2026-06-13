"""
Dashboard page — read-only preparation + evaluation visualization
(REQ-APP-10). Computes nothing new: reuses the scenario store, the fixture
MANIFEST, and eval/metrics.py over results.ndjson. Every section renders a
friendly placeholder when its data file is missing or empty (REQ-DEV-2).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from eval.metrics import refusal_rate  # noqa: E402

SEED_DIR = REPO_ROOT / "scenarios" / "seed"
FIXTURES_DIR = SEED_DIR / "fixtures"
RESULTS_PATH = REPO_ROOT / "data" / "results.ndjson"
LABELS_PATH = REPO_ROOT / "data" / "labels.ndjson"

GATING_VERDICTS = ("PASS", "FAIL", "UNCERTAIN")


# ---------------------------------------------------------------------------
# Loaders (graceful on missing/empty — REQ-DEV-2)
# ---------------------------------------------------------------------------

def load_scenarios() -> list[dict]:
    scenarios: list[dict] = []
    for name in ("green.json", "amber.json"):
        path = SEED_DIR / name
        if not path.exists():
            continue
        try:
            with open(path) as f:
                data = json.load(f)
            if isinstance(data, list):
                scenarios.extend(data)
        except (json.JSONDecodeError, OSError):
            pass
    return scenarios


def load_ndjson(path: Path) -> pd.DataFrame:
    rows = []
    if path.exists():
        with open(path) as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return pd.DataFrame(rows)


def load_manifest() -> dict:
    path = FIXTURES_DIR / "MANIFEST.json"
    if not path.exists():
        return {}
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def fixture_ids() -> list[str]:
    if not FIXTURES_DIR.is_dir():
        return []
    return sorted(p.stem for p in FIXTURES_DIR.glob("*.json")
                  if p.name != "MANIFEST.json")


# ---------------------------------------------------------------------------
# Preparation section
# ---------------------------------------------------------------------------

def render_preparation(scenarios: list[dict], labels: pd.DataFrame) -> None:
    st.header("Preparation")

    # --- Coverage matrix (domain × tier) -------------------------------
    st.subheader("Coverage matrix — domain × tier")
    if scenarios:
        df = pd.DataFrame(scenarios)
        pivot = (df.groupby(["domain", "tier"]).size().unstack(fill_value=0))
        fig = px.imshow(pivot, text_auto=True, aspect="auto",
                        labels={"x": "tier", "y": "domain", "color": "n"},
                        color_continuous_scale="Blues")
        fig.update_layout(height=max(300, 60 * len(pivot)))
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("No scenarios in the store yet — the coverage matrix will "
                "appear once `scenarios/seed/green.json` / `amber.json` are "
                "populated.")

    # --- Fixture manifest: declared vs actual ---------------------------
    st.subheader("Fixture manifest — declared vs. actual")
    manifest = load_manifest()
    present = fixture_ids()
    declared = manifest.get("scenarios", {})
    if not declared and not present:
        st.info("No fixtures yet — fixtures land in "
                "`scenarios/seed/fixtures/` with a MANIFEST.json "
                "(REQ-FIX-1).")
    else:
        declared_counts = pd.Series(
            [v.get("intended_response_type", "?") for v in declared.values()],
            dtype="object",
        ).value_counts().rename("declared (manifest)")
        st.write(f"Fixture files present: **{len(present)}** · manifest "
                 f"entries: **{len(declared)}**")
        if not declared_counts.empty:
            st.dataframe(declared_counts.to_frame(), width="stretch")
        missing_files = sorted(set(declared) - set(present))
        orphan_files = sorted(set(present) - set(declared))
        if missing_files:
            st.warning("Manifest entries with **no fixture file**: "
                       + ", ".join(missing_files))
        if orphan_files:
            st.warning("Fixture files **not in the manifest**: "
                       + ", ".join(orphan_files))
        if not missing_files and not orphan_files and declared:
            st.success("Manifest and fixture files agree.")

    # --- Labelling progress ---------------------------------------------
    st.subheader("Labelling progress")
    n_fixtures = len(present)
    if n_fixtures == 0:
        st.info("Labelling progress appears once fixtures exist.")
    else:
        labelled = (labels["scenario_id"].nunique()
                    if not labels.empty and "scenario_id" in labels else 0)
        st.progress(min(1.0, labelled / n_fixtures),
                    text=f"{labelled} / {n_fixtures} fixtures labelled "
                         f"(any rater)")
        if not labels.empty and "rater_id" in labels:
            per_rater = (labels.groupby("rater_id")["scenario_id"]
                         .nunique().rename("items labelled"))
            st.dataframe(per_rater.to_frame(), width="stretch")


# ---------------------------------------------------------------------------
# Evaluation section
# ---------------------------------------------------------------------------

def render_evaluation(results: pd.DataFrame) -> None:
    st.header("Evaluation")
    if results.empty:
        st.info("No evaluation results yet — run "
                "`python harness/run_eval.py --mode validate` to produce "
                "`data/results.ndjson`.")
        return

    run_ids = sorted(results["run_id"].dropna().unique(), reverse=True)
    run_id = st.selectbox("Run", run_ids, index=0)
    rows = results[results["run_id"] == run_id]
    st.caption(
        f"judge_prompt_hash: `{str(rows['judge_prompt_hash'].iloc[0])[:16]}…` · "
        f"store hash: `{str(rows['scenario_store_hash'].iloc[0])[:16]}…`"
        if "judge_prompt_hash" in rows else "")

    # --- Response-type distribution -------------------------------------
    st.subheader("Response-type distribution")
    rt = rows.groupby(["tier", "response_type"]).size().reset_index(name="n")
    if rt.empty:
        st.info("No rows in this run.")
    else:
        fig = px.bar(rt, x="response_type", y="n", color="tier",
                     barmode="group")
        st.plotly_chart(fig, width="stretch")

    # --- Over-refusal table with Wilson CI error bars --------------------
    st.subheader("Over-refusal by domain × tier (Wilson 95% CI)")
    gate = rows[~rows["contested"].astype(bool)] if "contested" in rows else rows
    records = []
    for (domain, tier), grp in gate.groupby(["domain", "tier"]):
        stats = refusal_rate(list(grp["response_type"]))
        if stats["n"] == 0:
            continue
        records.append({"domain": domain, "tier": tier, **stats})
    if not records:
        st.info("No non-contested rows to compute over-refusal rates on.")
    else:
        table = pd.DataFrame(records)
        st.dataframe(
            table[["domain", "tier", "n", "k", "rate", "ci_lower",
                   "ci_upper"]],
            width="stretch")
        fig = go.Figure()
        labels_x = table["domain"] + " / " + table["tier"]
        fig.add_trace(go.Scatter(
            x=labels_x, y=table["rate"], mode="markers",
            error_y=dict(
                type="data", symmetric=False,
                array=table["ci_upper"] - table["rate"],
                arrayminus=table["rate"] - table["ci_lower"],
            ),
            marker=dict(size=10),
            name="refusal rate",
        ))
        fig.update_yaxes(range=[-0.05, 1.05], title="refusal rate")
        st.plotly_chart(fig, width="stretch")

    # --- Refusal-calibration frontier ------------------------------------
    st.subheader("Refusal-calibration frontier")
    st.caption("x = refusal rate on GREEN; y = adversarial fail rate. One "
               "point per system_id × run. Fixture points measure the "
               "judge, not a system (REQ-HARNESS-2).")
    frontier = []
    for (sys_id, rid), grp in results.groupby(["system_id", "run_id"]):
        g = grp[~grp["contested"].astype(bool)] if "contested" in grp else grp
        green = g[g["tier"] == "GREEN"]
        x_stats = refusal_rate(list(green["response_type"]))
        adv = g[g["adversarial"].astype(bool)
                & g["verdict"].isin(GATING_VERDICTS)] \
            if "adversarial" in g else g.iloc[0:0]
        k = int((adv["verdict"] == "PASS").sum()) if not adv.empty else 0
        n = len(adv)
        if x_stats["n"] == 0 and n == 0:
            continue
        frontier.append({
            "system_id × run": f"{sys_id} × {rid}",
            "x": x_stats["rate"] if x_stats["n"] else None,
            "y": (k / n) if n else None,
            "n_green": x_stats["n"], "n_adv": n,
        })
    fdf = pd.DataFrame(frontier).dropna(subset=["x", "y"], how="all")
    if fdf.empty:
        st.info("Frontier appears once at least one run has GREEN rows and "
                "judged adversarial rows.")
    else:
        fig = px.scatter(fdf, x="x", y="y", text="system_id × run",
                         labels={"x": "refusal rate on GREEN",
                                 "y": "adversarial fail rate"})
        fig.update_traces(textposition="top center", marker=dict(size=12))
        fig.update_xaxes(range=[-0.05, 1.05])
        fig.update_yaxes(range=[-0.05, 1.05])
        st.plotly_chart(fig, width="stretch")

    # --- Contested-case profile ------------------------------------------
    st.subheader("Contested-case profile (excluded from gates)")
    contested = rows[rows["contested"].astype(bool)] \
        if "contested" in rows else rows.iloc[0:0]
    if contested.empty:
        st.info("No contested scenarios in this run.")
    else:
        st.dataframe(
            contested[["scenario_id", "response_type", "refusal_reason",
                       "verdict"]],
            width="stretch")


# ---------------------------------------------------------------------------

st.set_page_config(page_title="Penumbra — Dashboard", layout="wide")
st.title("Dashboard")
st.caption("Read-only (REQ-APP-10). Phase 0: no calibration gates exist "
           "yet, so all judge verdicts are advisory (REQ-CAL-3).")
st.warning("Advisory mode: no calibration gate JSON exists (REQ-CAL-3) — "
           "judge outputs are advisory only.")

_scenarios = load_scenarios()
_labels = load_ndjson(LABELS_PATH)
_results = load_ndjson(RESULTS_PATH)

render_preparation(_scenarios, _labels)
st.divider()
render_evaluation(_results)
