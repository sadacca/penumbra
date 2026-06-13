"""
Fetch + hash the public-domain / CC-BY source documents referenced by the
scenario store, and fill in document_source.sha256 (REQ-SRC-2, REQ-SRC-5).

This script is the one Phase 0 step that requires outbound network access.
The sandbox in which scenarios are authored has no network egress, so every
committed scenario starts with document_source.sha256 == "PENDING_FETCH" and
a placeholder excerpt file under scenarios/seed/documents/. Running this
script on a networked machine:

  1. reads scenarios/seed/documents/SOURCES.json (the fetch manifest),
  2. downloads each source document,
  3. writes/refreshes the excerpt markdown file (operator trims to the cited
     sections — the script saves the full fetched text alongside for diffing),
  4. computes the SHA-256 of the *full* fetched document, and
  5. rewrites document_source.sha256 + retrieved in green.json / amber.json
     for every scenario that points at that source.

REQ-SRC-5 GUARD: this script refuses to write any document flagged
person_naming: true in SOURCES.json. Such sources must be substituted or
dropped, never committed.

Usage:
    python eval/fetch_documents.py            # fetch all PENDING_FETCH sources
    python eval/fetch_documents.py --check    # report status, fetch nothing
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = REPO_ROOT / "scenarios" / "seed" / "documents"
SOURCES_MANIFEST = DOCS_DIR / "SOURCES.json"
SEED_FILES = [
    REPO_ROOT / "scenarios" / "seed" / "green.json",
    REPO_ROOT / "scenarios" / "seed" / "amber.json",
]

USER_AGENT = "penumbra-eval-harness/0.1 (research; contact via repo)"


def load_sources() -> list[dict]:
    if not SOURCES_MANIFEST.exists():
        print(f"ERROR: {SOURCES_MANIFEST} not found.", file=sys.stderr)
        sys.exit(1)
    return json.loads(SOURCES_MANIFEST.read_text())


def fetch(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=60) as resp:  # noqa: S310 (trusted gov/court URLs)
        return resp.read()


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def update_scenarios(citation_url: str, new_hash: str, retrieved: str) -> int:
    """Rewrite sha256 + retrieved for every scenario whose document_source.url
    matches citation_url. Returns the number of scenarios updated."""
    updated = 0
    for path in SEED_FILES:
        if not path.exists():
            continue
        scenarios = json.loads(path.read_text())
        changed = False
        for s in scenarios:
            ds = s.get("document_source") or {}
            if ds.get("url") == citation_url:
                ds["sha256"] = new_hash
                ds["retrieved"] = retrieved
                changed = True
                updated += 1
        if changed:
            path.write_text(json.dumps(scenarios, indent=2, ensure_ascii=False) + "\n")
    return updated


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Report status only; fetch nothing.")
    args = parser.parse_args(argv)

    sources = load_sources()
    today = date.today().isoformat()
    errors = 0

    for src in sources:
        sid_label = src.get("source_id", src.get("url", "<unknown>"))

        if src.get("person_naming"):
            print(
                f"REFUSED: {sid_label} is flagged person_naming — excluded "
                f"per REQ-SRC-5. Substitute or drop.",
                file=sys.stderr,
            )
            errors += 1
            continue

        if args.check:
            excerpt = DOCS_DIR / src["excerpt_file"]
            status = "excerpt present" if excerpt.exists() else "excerpt MISSING"
            print(f"{sid_label}: {src['license']}; {status}; url={src['url']}")
            continue

        try:
            print(f"Fetching {sid_label} ...")
            raw = fetch(src["url"])
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR fetching {sid_label}: {exc}", file=sys.stderr)
            errors += 1
            continue

        new_hash = sha256_hex(raw)
        # Save the full fetched payload for operator trimming + diffing.
        full_path = DOCS_DIR / (Path(src["excerpt_file"]).stem + ".full.txt")
        try:
            full_path.write_bytes(raw)
        except Exception as exc:  # noqa: BLE001
            print(f"WARNING: could not save full text for {sid_label}: {exc}", file=sys.stderr)

        n = update_scenarios(src["url"], new_hash, today)
        print(f"  sha256={new_hash[:12]}…  updated {n} scenario(s)")
        print(f"  full text saved to {full_path.name}; trim to the cited "
              f"sections in {src['excerpt_file']} and verify license + REQ-SRC-5.")

    if errors:
        print(f"\n{errors} source(s) had errors or were refused.", file=sys.stderr)
        return 1
    print("\nDone. Re-run 'python eval/validate.py' to confirm no PENDING_FETCH remains.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
