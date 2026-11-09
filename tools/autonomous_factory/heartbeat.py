"""M02 read-only audit with an optional single managed GitHub issue dashboard.

Never dispatches work, edits source, approves a candidate, or promotes an asset.
"""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO = "kalashgit/last-light-godot"
TITLE = "[M02] Autonomous asset factory — 30-minute status"
WORKFLOWS = ("m02-autonomous-factory-v1.yml", "m02-cross-family-calibration.yml",
             "m02-specialist-contracts.yml", "m02-family-coordinator.yml")


def request(path, *, method="GET", payload=None):
    token = os.environ.get("GH_TOKEN", "")
    if not token:
        raise RuntimeError("GH_TOKEN required")
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        "https://api.github.com" + path, data=data, method=method,
        headers={"Authorization": "Bearer " + token,
                 "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.load(response)


def render(registry, runs, run_url):
    families = registry["families"]
    if len(families) != 12 or {f["id"] for f in families} != {f"F{i:02d}" for i in range(1, 13)}:
        raise ValueError("invalid or incomplete family registry")
    lines = ["M02 protected factory status (generated automatically)", "",
             f"Monitor: {run_url}", "",
             "**No automatic Golden approval, merge, deployment or canonical promotion.**", "",
             "| Family | Admission | Candidate source |", "|---|---|---|"]
    for item in families:
        if item.get("canonical_promotion") is not False:
            raise ValueError("canonical promotion must be explicitly false")
        lines.append(f"| {item['id']} | {item['readiness']} | `{item.get('source_branch') or 'UNVERIFIED'}` |")
    lines += ["", "### Recent CI (latest matching runs)", ""]
    for name in WORKFLOWS:
        matches = [r for r in runs if r.get("path", "").endswith("/" + name)]
        if not matches:
            lines.append(f"- {name}: no recent run found")
            continue
        last = matches[0]
        lines.append(f"- {name}: {last['status']} / {last.get('conclusion') or 'pending'} — {last['html_url']}")
    lines += ["", "**Automation status:** monitoring only. Full-loop AI repair requires a separately approved, budgeted model-worker identity.",
              "**Review status:** technical CI PASS is not Golden. Founder signoff stays mandatory."]
    return "\n".join(lines) + "\n"


def main():
    registry = json.loads(Path("tools/autonomous_factory/family_registry.json").read_text())
    runs = request(f"/repos/{REPO}/actions/runs?per_page=100")["workflow_runs"]
    url = os.environ.get("GITHUB_SERVER_URL", "https://github.com") + "/" + REPO + "/actions/runs/" + os.environ.get("GITHUB_RUN_ID", "unknown")
    report = render(registry, runs, url)
    Path("m02-heartbeat.md").write_text(report)
    if os.environ.get("M02_WRITE_DASHBOARD", "false").lower() != "true":
        print(report)
        return
    issues = request(f"/repos/{REPO}/issues?state=open&per_page=100")
    managed = [i for i in issues if i.get("title") == TITLE and "pull_request" not in i]
    if len(managed) > 1:
        raise RuntimeError("duplicate dashboard issues: refusing ambiguous update")
    if managed:
        request(f"/repos/{REPO}/issues/{managed[0]['number']}", method="PATCH", payload={"body": report})
    else:
        request(f"/repos/{REPO}/issues", method="POST", payload={"title": TITLE, "body": report})


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, urllib.error.URLError, RuntimeError) as exc:
        print(f"M02_HEARTBEAT_FAIL_CLOSED: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
