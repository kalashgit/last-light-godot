# Foundry Copilot coding-agent pilot — NO execution before budget attestation

This integrates Copilot **cloud coding agent** for genuine editable Blender
recipe work, distinct from the deterministic 512-source procedural factory.

## Ownership and spending gates

1. Owner sets a **personal GitHub AI/Copilot additional-usage budget to $0**
   (or an explicit affordable amount) with an actual hard stop, and enables
   included-usage alerts. This is a GitHub billing setting, not a repository
   variable. GitHub AI-credit usage inside the plan is not necessarily free
   or unlimited; the plan allowance still applies.
2. Owner creates a short-lived user-to-server GitHub token with the documented
   fine-grained repository permissions for Copilot issue assignment and stores
   it **only** as Actions secret `FOUNDRY_COPILOT_USER_TOKEN`. Never paste it
   into issues, a public PR, or chat. OAuth app user tokens also work where
   supported. The standard installation `GITHUB_TOKEN` cannot start this API.
3. After billing is set, owner sets repo Actions variable
   `FOUNDRY_COPILOT_OWNER_BUDGET_CONFIRMED=true` (owner attestation, **not**
   a machine verification of GitHub billing). No job infers this on its own.
4. Workflow `Foundry Copilot single-issue pilot` is manual-dispatch only,
   default `apply=false`; billable `apply=true` is restricted to `kalashgit`
   dispatching from reviewed `main`, a valid user token, and issue #83.
5. The pilot chooses the default model with no forced premium model. It cannot
   auto-assign any other issue, repeatedly assign an already assigned issue,
   or merge any PR. After inspecting its real draft PR, costs, and model output,
   commission a separate security-reviewed, serialized daily dispatcher.

## Pilot acceptance

- Copilot agent profile is `.github/agents/foundry-modeler.agent.md`.
- Work order `A00-B001-F01-ll_furniture_refrigerator-r1` has a real, original
  Blender recipe with editable `.blend`, exported `.glb`, 16 actual renders,
  provenance and technical QA in a **draft PR**.
- Golden approval stays false for the new model and all 360 legacy masters.
- Independent F11/F12/Godot/iPhone QA and founder signoff are later gates.

This is a safe one-issue proving stage, **not yet unattended F01–F12 mass
production**. The next stage links the Notion candidate queue, failure-to-issue
monitor and agent review with bounded daily concurrency.
