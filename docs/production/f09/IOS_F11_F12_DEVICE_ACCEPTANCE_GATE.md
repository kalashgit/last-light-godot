# F09 V18 — iPhone device gate and F11/F12 visual acceptance

**Status: BLOCKED — NOT DEVICE-VERIFIED / NOT ART-APPROVED**

## Actual evidence available today
- GitHub Actions run 42589400716: real `main.tscn`/house.gd executed in an isolated clone, all three provisional F09 source IDs dropped and picked up through the existing game methods, inventory rows verified, schema-2 save/reload verified.
- Two *genuine OpenGL-rendered* LAST LIGHT house frames at 1280×720, outdoor and indoor, from Xvfb/Mesa. The three candidate dropped tools appear at the real world-size canvas scale.
- CI captures 120 frame intervals and OS static-memory counters in a virtual Linux display. The recorded metrics are **NOT** iPhone measurements.
- True Cycles AO + albedo/roughness/metallic/tangent-normal bakes, 3 embedded-texture GLBs, 48 heading sprites and pixel-exact atlas passed previous verified CI run 42587171156.
- Current F09 source candidates intentionally are **not** in the production inventory or canonical A00 registry.

## Physical iOS execution requirements
1. A macOS/Xcode environment with the matching Godot iOS export templates and an Apple Developer signing team with valid provisioning for an identified device. None of these keys, certificates, device UDIDs, iOS export presets or signed IPA were available for this Ubuntu CI job. Do not commit credentials or pretend unsigned artifacts were installed.
2. An authorized signed iOS build from an explicitly versioned source SHA, with candidate test data only in a QA variant. Preserve production saves and original art.
3. Record iPhone hardware model, iOS build, app bundle and signed IPA SHA-256; collect Xcode device launch logs and in-app screenshots of indoor/outdoor drops and the inventory.
4. Use a 30–60 second repeatable play route: spawn the wrench/ratchet/saw separately; inspect and pick up each; verify inventory count and save/reload; inspect 16 headings, shadow/occlusion, sprite bleed, touch-target overlap and pinch/zoom behavior at indoor/outdoor zoom.
5. Record *on-device* frame-time series and p50/p95 FPS, foreground memory (resident bytes), peak memory, start-to-play time and any crash/thermal warning. The target is **30 FPS or better**, and none of these iPhone measurements can be inferred from Linux CI.
6. Founder/F11/F12 review: side-by-side native-scale ground sprites on the actual house foliage, floor, road and inventory canvas; confirm material roughness/metallic/normal/AO appearance, consistent upper-left light, anchored positions and legibility. Reviewer must sign an explicit approval decision on exact source SHA and atlas hash.

## Unresolved visual defects identified from genuine LAST LIGHT screenshots
- Candidate tools are very small at the current camera scale and can be overwhelmed by grass, debris and floor contrast; world-size images must not be enlarged merely to make inspection look successful.
- The adopted `[48,48]` pivot and ground anchor is a testing assumption, **not** approved F12 canonical placement. Verify against actual F12 ground/held anchor conventions before publishing.
- Real AO is baked but still needs F11 material-art signoff across varying light, and new inventory/held sprite projections must be checked in the production UI.

## Explicit release gates
`IOS_SIGNING`: BLOCKED; `PHYSICAL_IPHONE_INSTALL`: BLOCKED;
`ON_DEVICE_FPS_MEMORY`: BLOCKED; `F11_ART_APPROVAL`: PENDING;
`F12_ART_ANCHOR_APPROVAL`: PENDING; `FOUNDER_GOLDEN`: PENDING;
`A00_CANONICAL`: PENDING; `PRODUCTION_MERGE`: BLOCKED.

The Linux visual fixture and interaction tests are useful technical acceptance evidence. They do **not** authorize canonical identity, a production release, formal art acceptance or iOS deployment.
