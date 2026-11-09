# Foundry AI — canonical Notion work-order bridge V1

## What is implemented

This is a **read-only, sanitized snapshot** of the current Notion asset registries, not a live Notion API connection. It deliberately stores no private Notion briefs, media URLs, third-party sprites, contact details or account tokens in this public GitHub repository.

- 60 semantic original-asset production masters from **LL · Original Asset & Content Production Registry**.
- 118 world/building/room/tile/container specification IDs from **LAST LIGHT — World Tile, Building & Container Registry**.
- 50 research-source file IDs from **LAST LIGHT — Master Item & Model Registry**.
- A separate 360 first-pass Blender sources collection exists in prior GitHub Actions artifacts and durable backups; none is declared Golden.

The broader 4,347/21,025-item source-file research archive is **not** 4,347/21,025 original game models. It must be deduplicated into semantic masters by A00. This V1 snapshot does not claim to have imported all those media records.

## Scheduled use

The read-only daily workflow validates identities and produces **up to four design-work orders** from master records with a canonical semantic identity, a named F01–F12 specialist and a distinct work-order ID. It saves a JSON artifact, but does **not** trigger paid AI or Blender, create issues, change production branches or mark work done. A future authorized coding worker will consume this queue after adding durable job-claim state and per-family recipe contracts. Do not infer continuous execution from repeated identical queue artifacts.

## Strict approval ladder

1. **Reference / research only:** source media identifiers may inform independent anatomy research, but their pixels, meshes, materials and gameplay content must never be copied into LAST LIGHT without rights review.
2. **Canonical identity:** unique original game object ID and named worker; a proposed brief is not an approved recipe.
3. **Original recipe proposal:** an agent may draft Blender/Godot source and an independent design brief on a draft branch.
4. **Technical candidate:** Blender `.blend`, GLB, F11 materials, F12 16-direction rendering, source SHA and real Godot tests have evidence. Passing tests **never** makes a Golden asset.
5. **Founder visual approval:** founder inspects actual native-size 100/220/325% panels, lighting, silhouette, collision, realism and provenance. Approval must be separately attributable; Notion `Stage = Approved` does not confer this.
6. **Godot/iPhone acceptance:** interactions, performance, scene integrity and final release gates are separate.

All 360 first-pass models are **pending Golden**. In the current snapshot, the 60 master records have **zero** positive `Founder Visual Approved` flags; 20 rows have a generic `Approved` workflow stage, which is not an art sign-off. The other 118 world entries are unresolved specifications and the 50 item records are research references.

## Expansion to live autonomous creation

- Maintain the existing deterministic 512-new-source generator and the separate 360-sprite renderer as **technical candidate** engines.
- Add an authorized coding agent capable of authoring and improving family-specific procedural geometry, rigging and recipes. Use a narrowly scoped GitHub token, isolated branches, hard time/cost limits, draft PRs and independent QA. Do not assume GitHub Pro provides Copilot coding-agent entitlement.
- Add a versioned, trusted Notion-to-GitHub export or authenticated sync with change detection, not an unrestricted nightly scrape.
- Add durable job claims/locks and rerun-safe evidence before automatically assigning all four daily work orders; otherwise the same tasks would be repeated.
- Preserve the original 360 source hashes and track each item's explicit `geometry_candidate`, `materials_candidate`, `render_candidate`, `technical_qa_passed`, `founder_visual_approved`, `godot_integrated` and `iphone_verified` states.

This branch is an **integration candidate**, not an authorization to merge or activate paid inference.
