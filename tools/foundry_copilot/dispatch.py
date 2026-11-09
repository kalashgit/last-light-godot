"""Fail-closed Copilot issue assignment for ONE reviewed Foundry pilot.

No inference calls are performed by this module. Assignment is a billable
Copilot cloud-agent activation, so application is off unless the repository
owner explicitly attests to a GitHub billing hard stop and opts into the run.
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request

REPOSITORY = "kalashgit/last-light-godot"
ISSUE_NUMBER = 83
WORK_ORDER = "A00-B001-F01-ll_furniture_refrigerator-r1"
ASSIGNEE = "copilot-swe-agent[bot]"
AGENT = "foundry-modeler"
API = "https://api.github.com"


def prepare(issue: dict, issue_number: int) -> dict:
    """Prepare the exact REST assignment contract, without any side effects."""
    if issue_number != ISSUE_NUMBER or issue.get("number") != ISSUE_NUMBER:
        raise ValueError("Only reviewed first pilot issue #83 is allowlisted")
    if issue.get("state") != "open":
        raise ValueError("Pilot must be an open issue")
    if not isinstance(issue.get("body"), str) or WORK_ORDER not in issue["body"]:
        raise ValueError("Canonical original-design work order missing")
    if "0/360 Golden" not in issue["body"] or "No auto-merge" not in issue["body"]:
        raise ValueError("Human approval or merge safeguards missing from issue")
    if issue.get("pull_request"):
        raise ValueError("Cannot assign a pull request as a work order")
    assignments = [a.get("login", "") for a in issue.get("assignees", [])]
    if assignments:
        raise ValueError("Pilot already assigned; prevent repeat paid executions")
    return {
        "assignees": [ASSIGNEE],
        "agent_assignment": {
            "target_repo": REPOSITORY,
            "base_branch": "main",
            "custom_instructions": (
                "Use the foundry-modeler agent. Work only on F01 refrigerator "
                "original source geometry and rigorous QA. Draft PR only; no "
                "merge, no Golden promotion, no other agent invocation."
            ),
            "custom_agent": AGENT,
            # Use user's default/included Copilot model; no premium override.
            "model": "",
        },
    }


def reject_repeat_assignment(events: list[dict]) -> None:
    """An unassigned issue must not be used to buy another agent run."""
    if not isinstance(events, list):
        raise ValueError("Missing issue assignment history")
    if len(events) >= 100:
        raise ValueError("Assignment history exceeds inspected page")
    if any(e.get("event") == "assigned" and
           (e.get("assignee") or {}).get("login") == ASSIGNEE for e in events):
        raise ValueError("Copilot was assigned before; lifetime pilot quota exhausted")


def preflight(env: dict[str, str]) -> None:
    if env.get("GITHUB_EVENT_NAME") != "workflow_dispatch":
        raise ValueError("Not a trusted manual dispatch")
    if env.get("GITHUB_REF") != "refs/heads/main":
        raise ValueError("Only reviewed default-branch code may assign agents")
    if env.get("GITHUB_ACTOR") != "kalashgit":
        raise ValueError("Only the repository owner may initiate paid pilot")
    if env.get("FOUNDRY_COPILOT_OWNER_BUDGET_CONFIRMED") != "true":
        raise ValueError("Owner has not attested to GitHub billing hard stop")
    if not env.get("FOUNDRY_COPILOT_USER_TOKEN"):
        raise ValueError("Missing limited, user-scoped Copilot assignment token")


def request(method: str, path: str, token: str, payload: dict | None = None) -> dict:
    body = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        API + path,
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "Foundry-Copilot-Pilot-V1",
        },
    )
    with urllib.request.urlopen(req, timeout=25) as response:
        return json.loads(response.read())


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--issue-number", type=int, choices=[ISSUE_NUMBER], default=ISSUE_NUMBER)
    p.add_argument("--apply", action="store_true")
    args = p.parse_args()
    reader = os.environ.get("GITHUB_TOKEN") or os.environ.get("FOUNDRY_COPILOT_USER_TOKEN")
    if not reader:
        raise SystemExit("Missing read-only GitHub API token")
    issue_path = f"/repos/{REPOSITORY}/issues/{args.issue_number}"
    try:
        issue = request("GET", issue_path, reader)
        payload = prepare(issue, args.issue_number)
        events = request("GET", issue_path + "/events?per_page=100", reader)
        reject_repeat_assignment(events)
        if not args.apply:
            # Do not print issue body, credential, or unsanitized API content.
            print("FOUNDRY_COPILOT_DRY_RUN issue=83 agent=foundry-modeler billable=false")
            return
        preflight(os.environ)
        request("POST", issue_path + "/assignees", os.environ["FOUNDRY_COPILOT_USER_TOKEN"], payload)
        verified = request("GET", issue_path, reader)
        if ASSIGNEE not in {x.get("login") for x in verified.get("assignees", [])}:
            raise ValueError("Assignment API returned, but Copilot assignee not verified")
        print("FOUNDRY_COPILOT_ASSIGNED issue=83 agent=foundry-modeler billable=true")
    except (urllib.error.HTTPError, urllib.error.URLError, ValueError) as exc:
        # No token data or untrusted body printed in errors.
        kind = type(exc).__name__
        raise SystemExit(f"FOUNDRY_COPILOT_BLOCKED {kind}") from None


if __name__ == "__main__":
    main()
