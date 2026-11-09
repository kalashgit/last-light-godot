"""Deterministic, non-billable Foundry correction and Golden-review gate.

The controller reads a *frozen* Notion-approved work-order snapshot, a draft
candidate PR, one completed GitHub Actions run, and optional independent visual
review evidence. It never dispatches AI, merges, or grants Golden approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

REPOSITORY = "kalashgit/last-light-godot"
SHA = re.compile(r"[a-f0-9]{40}\Z")
ALLOWED_EVENTS = {"pull_request", "workflow_dispatch", "push"}
ALLOWED_RESULTS = {"success", "failure", "timed_out", "cancelled"}
REQUIRED_VISUAL_CATEGORIES = frozenset({
    "sixteen_headings", "silhouette", "proportions", "door_structure",
    "handles", "materials", "transparency", "shadows", "sprite_readability",
})


def _reject(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _candidate_record(catalog: dict, work_order: str) -> dict:
    _reject(catalog.get("schema_version") == 1 and
            catalog.get("status") == "NOTION_READ_ONLY_SNAPSHOT_NOT_LIVE_SYNC",
            "Not a verified frozen Notion work-order snapshot")
    matches = [row for row in catalog.get("production_masters", [])
               if row.get("work_order") == work_order]
    _reject(len(matches) == 1, "Work order missing or ambiguous")
    row = matches[0]
    _reject(row.get("semantic_verification") == "Canonical Verified" and
            re.fullmatch(r"F(?:0[1-9]|1[0-2])", str(row.get("queue"))) is not None,
            "Unverified identity or missing worker")
    _reject(row.get("founder_visual_approved") is False,
            "Cannot automatically process an approval status")
    return row


def _review_state(review: dict | None, sha: str) -> tuple[str, list[str]]:
    if review is None:
        return "AWAIT_INDEPENDENT_VISUAL_REVIEW", []
    _reject(review.get("schema_version") == 1 and
            review.get("candidate_sha") == sha, "Visual review is not for this exact candidate")
    _reject(review.get("golden_approved") is False and
            review.get("founder_visual_approved") is False,
            "Visual reviewer cannot confer Golden status")
    reviewer = review.get("reviewer")
    _reject(isinstance(reviewer, str) and 3 <= len(reviewer) <= 100 and
            reviewer not in {"Copilot", "copilot-swe-agent[bot]", "foundry-modeler"},
            "Review must be attributed to an independent person")
    categories = review.get("categories")
    _reject(isinstance(categories, dict) and set(categories) == REQUIRED_VISUAL_CATEGORIES and
            all(v in ("pass", "fail", "unverified") for v in categories.values()),
            "Review must cover all nine visual categories")
    defects = review.get("defects")
    _reject(isinstance(defects, list) and len(defects) <= 30 and
            all(isinstance(d, str) and 5 <= len(d) <= 240 for d in defects),
            "Invalid visual defects")
    _reject(review.get("heading_count") == 16 and
            bool(re.fullmatch(r"[a-f0-9]{64}", str(review.get("contact_sheet_sha256")))),
            "A reviewed 16-heading contact sheet with SHA256 is required")
    if any(x == "fail" for x in categories.values()) or defects:
        _reject(bool(defects), "Failing review requires actionable defect descriptions")
        return "REQUEST_ARTISTIC_REWORK", defects
    if any(x == "unverified" for x in categories.values()) or not review.get("gameplay_scale_checked"):
        return "AWAIT_INDEPENDENT_VISUAL_REVIEW", []
    if not review.get("f11_materials_checked") or not review.get("f12_atlas_checked"):
        return "AWAIT_F11_F12_ACCEPTANCE", []
    return "AWAIT_FOUNDER_GOLDEN_DECISION", []


def assess(catalog: dict, pr: dict, run: dict, review: dict | None,
           ledger: dict | None = None) -> tuple[dict, dict]:
    _reject(isinstance(pr, dict) and isinstance(run, dict), "Missing PR or CI evidence")
    work_order = pr.get("work_order")
    row = _candidate_record(catalog, work_order)
    _reject(pr.get("draft") is True and pr.get("state") == "open" and
            pr.get("merged") is False, "Candidate is not an open draft PR")
    _reject(pr.get("repo") == REPOSITORY and pr.get("head_repo") == REPOSITORY,
            "Untrusted PR repository")
    _reject(pr.get("base") == "main" and pr.get("head") != "main", "Invalid branch ownership")
    sha = pr.get("head_sha")
    _reject(isinstance(sha, str) and SHA.fullmatch(sha) is not None, "Invalid candidate SHA")
    _reject(run.get("head_sha") == sha and run.get("event") in ALLOWED_EVENTS and
            run.get("status") == "completed" and run.get("conclusion") in ALLOWED_RESULTS and
            type(run.get("id")) is int and run["id"] > 0,
            "CI run must be complete and match exact PR SHA")
    _reject(run.get("head_branch") == pr.get("head"), "CI branch mismatch")
    _reject(row.get("content_id") == pr.get("asset_id") and
            work_order == pr.get("work_order"), "Notion identity mismatch")
    if run["conclusion"] != "success":
        outcome, defects = "REQUEST_TECHNICAL_REWORK", [f"GitHub CI: {run['conclusion']}"]
    else:
        outcome, defects = _review_state(review, sha)
    key = hashlib.sha256(f"{work_order}:{sha}:{run['id']}:{outcome}:"
                         f"{json.dumps(defects, sort_keys=True)}".encode()).hexdigest()
    if ledger is None:
        ledger = {"schema_version": 1, "events": []}
    _reject(ledger.get("schema_version") == 1 and isinstance(ledger.get("events"), list),
            "Invalid persistent audit ledger")
    entries = ledger["events"]
    _reject(len(entries) <= 10000 and all(isinstance(x, dict) and isinstance(x.get("key"), str)
                                         for x in entries), "Invalid or overlarge audit ledger")
    replay = any(e["key"] == key for e in entries)
    decision = {
        "schema_version": 1, "work_order": work_order, "asset_id": row["content_id"],
        "worker": row["queue"], "candidate_pr": pr["number"], "candidate_sha": sha,
        "run_id": run["id"], "technical_ci": run["conclusion"], "next_action": outcome,
        "defects": defects, "dedupe_key": key, "already_recorded": replay,
        "automated_copilot_dispatch": False, "automatic_merge": False,
        "golden_approved": False, "founder_review_required": outcome == "AWAIT_FOUNDER_GOLDEN_DECISION",
        "snapshot_is_live": False,
    }
    if not replay:
        ledger = {"schema_version": 1, "events": [*entries, {
            "key": key, "work_order": work_order, "candidate_sha": sha,
            "run_id": run["id"], "outcome": outcome,
        }]}
    return decision, ledger


def main() -> None:
    p = argparse.ArgumentParser()
    for name in ("catalog", "pr", "run"):
        p.add_argument(f"--{name}", type=Path, required=True)
    p.add_argument("--review", type=Path)
    p.add_argument("--state", type=Path)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--next-state", type=Path, required=True)
    args = p.parse_args()
    read = lambda path: json.loads(path.read_text()) if path and path.exists() else None
    decision, state = assess(read(args.catalog), read(args.pr), read(args.run),
                             read(args.review), read(args.state))
    for path, obj in ((args.output, decision), (args.next_state, state)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")
    print(f"FOUNDRY_AUTONOMY_DECISION {decision['next_action']} "
          f"run={decision['run_id']} replay={decision['already_recorded']}")


if __name__ == "__main__":
    main()
