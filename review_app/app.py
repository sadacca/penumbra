"""
Penumbra review app — landing page (REQUIREMENTS.md §6.9).

Run with:  streamlit run review_app/app.py

Phase 0 pages: 00_dashboard (read-only prep + results, REQ-APP-10) and
01_human_labels (blinded labelling, REQ-APP-4). Launches gracefully with
empty/missing data files (REQ-DEV-2).
"""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[1]


def _count_json_list(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        with open(path) as f:
            data = json.load(f)
        return len(data) if isinstance(data, list) else 0
    except (json.JSONDecodeError, OSError):
        return 0


def _count_ndjson(path: Path) -> int:
    if not path.exists():
        return 0
    with open(path) as f:
        return sum(1 for line in f if line.strip())


def _count_fixtures(path: Path) -> int:
    if not path.is_dir():
        return 0
    return len([p for p in path.glob("*.json") if p.name != "MANIFEST.json"])


def main() -> None:
    st.set_page_config(page_title="Penumbra", page_icon="🌗", layout="wide")
    st.title("Penumbra — RAG over-refusal evaluation")
    st.caption(
        "Measuring when document-grounded systems refuse legitimate work. "
        "Phase 0 walking skeleton."
    )

    green = _count_json_list(REPO_ROOT / "scenarios" / "seed" / "green.json")
    amber = _count_json_list(REPO_ROOT / "scenarios" / "seed" / "amber.json")
    fixtures = _count_fixtures(REPO_ROOT / "scenarios" / "seed" / "fixtures")
    results = _count_ndjson(REPO_ROOT / "data" / "results.ndjson")
    labels = _count_ndjson(REPO_ROOT / "data" / "labels.ndjson")

    st.subheader("Repository state")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("GREEN scenarios", green)
    c2.metric("AMBER scenarios", amber)
    c3.metric("Fixtures", fixtures)
    c4.metric("Result rows", results)
    c5.metric("Label rows", labels)

    if green + amber == 0:
        st.info("The scenario store is empty — scenarios are authored in "
                "`scenarios/seed/`. Everything here renders gracefully "
                "until they land (REQ-DEV-2).")

    st.subheader("Where to go")
    st.markdown(
        "- **Dashboard** (sidebar → *dashboard*): read-only preparation & "
        "evaluation state — coverage matrix, fixture manifest mix, "
        "labelling progress, and post-run charts (REQ-APP-10).\n"
        "- **Human labels** (sidebar → *human labels*): the **blinded** "
        "labelling form (REQ-APP-4). Do not read fixture files before "
        "labelling — the blind pass doubles as fixture QA (REQ-HUM-3).\n\n"
        "Useful commands:\n"
        "```bash\n"
        "python harness/run_eval.py --mode validate   # key-free pipeline\n"
        "python reports/generate_report.py            # findings + report card\n"
        "```"
    )


main()
