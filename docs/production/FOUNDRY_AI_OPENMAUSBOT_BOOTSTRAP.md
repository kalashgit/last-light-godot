# OpenMausBot ↔ Foundry AI — optional headless controller

**Current truth:** OpenMausBot has **not been installed, authenticated, or run** for LAST LIGHT. GitHub Actions currently executes the Blender/Godot jobs. This contribution prepares a portable **OpenMausBot team** in its upstream `openmaus.team` v1 format without activating any bots.

## Verified upstream reference

- Upstream: https://github.com/milind-soni/OpenMausBot (package version 0.1.150 at inspection)
- Portable-team schema: https://github.com/milind-soni/openmausbot-teams/blob/main/schema/team.schema.json
- Deployment docs: https://github.com/milind-soni/OpenMausBot/blob/main/docs/self-hosting.md
- Headless service requires Node 24+ **and an always-on Linux/Windows/Mac machine** or a supported container environment.
- Your iPhone can pair to the server but **cannot be the always-on headless host**.
- Separate Codex/Claude/Grok authentication is required on the remote host. ChatGPT Plus/Pro/GitHub Pro must not be presented as unlimited agent tokens or compute.

## Prepared asset

`docs/production/foundry-ai-last-light.mausteam.json` can be imported into an eligible OpenMausBot installation as a starting roster. It has five original roles: Director, Blender asset engineer, F11/F12 sprite engineer, independent QA, and archive keeper.

The package does not carry tokens, model logins, GitHub write permissions, computers, approval levels, or scheduled routines. **After import, explicitly set every bot to Ask before connecting tools** (OpenMausBot's personal-workspace import can default to Full access); inspect each capability grant before enabling.

## Deferred deployment gate

1. Approve an always-on host and its recurring cost; do not repurpose temporary GitHub Actions runners as persistent OpenMausBot hosts.
2. Pin the trusted OpenMausBot package version and establish isolated unprivileged Linux user, HTTPS pairing, SSH restrictions, encrypted backups and egress controls.
3. Sign in a permitted Codex/Claude/Grok engine with explicit budget and token limits; install GitHub connector with repo-scoped **read-only access first**.
4. Import the team file and test reading issue #77 and a single unapproved Blender/CI run. No PR writes until security acceptance.
5. Add repository scoped bot permissions and a dry-run of creating *only a draft PR* from a controlled CI issue; no autonomous merge, deployment or Golden approval.

## What stays on GitHub

M02's version-controlled Blender/F12/Godot workflows, immutable run hashes and issue coordination remain authoritative. OpenMausBot will be an optional UI/agent **orchestrator**, not the source of asset truth. A hard outage of the OpenMausBot server must not delete or alter any source archives.
