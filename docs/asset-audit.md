# Asset audit — 2026-11-04

Repository baseline 6a1bc3c has no imported binary assets. V3.6 uses procedural polygons; asset_lab and house_3d are experiments, not the playable scene. Existing rendering draws characters after every wall/object and therefore has unresolved depth/occlusion defects. Floors are flat diamonds, furniture generic boxes; this is not a completed visual overhaul.

## Quaternius
Connected Google Drive folder 1NKfC95GMWWJquy6rRzwFVkVDoZ_QP7K_ was read using the Google Drive connector. Its FBX folder contains **53 files, 1,355,868 bytes total** by metadata, chiefly tools, containers, medical supplies, weapons, tent/raft/campfire. It supplies neither complete residential architecture nor survivor/zombie animations. License.txt (1nfGeqyrswcs6llH48fr562D8Qt5_bp9U) was read: “CC0 1.0 Universal (CC0 1.0), Public Domain Dedication”, credited to @Quaternius. No raw files downloaded in this checkpoint. Prior manifest's retrieval claims describe an earlier session, not binaries available here.

Use only a small prop subset after calibrated rendering. These are low-poly models; a render does not automatically make them detailed or grounded. Require screenshot review at actual gameplay size before accepting them. Do not use the old manifest's Node3D house strategy; main.tscn remains Node2D.

## Engvee candidate
Creator page fetched 2026-11-04: https://engvee.itch.io/animated-isometric-zombie
Title: FREE Animated Isometric Zombies. Advertises three skins, 16 directions at 22.5 degrees, 13 animations (four attacks, two deaths, left/right hit, idle/lookup, roar, walk, run), separate shadows. Frames are body-centered, **not foot-anchored**. Available sheets use 256px frames; HQ individual frames use 512px. Smallest advertised skin archive is 23 MB; no archive downloaded.

Creator permits commercial/noncommercial projects, unlimited projects and modification; 3D author Panchenko Andrey. Page does not explicitly grant redistribution of raw source files. Verify included license or obtain clarification before committing sheets to public GitHub. This is a promising animation candidate, not accepted production art: inspect silhouettes/palette, projection and foot drift alongside test-room sprites first. Derive stable foot offsets for each animation, downsample to character height around 40–48px at the current scale, select 8 directions and idle/walk/attack/hit/death first, and budget decoded texture memory (RGBA8 is width × height × 4, regardless of ZIP size). Use the project's single shadow system rather than double-baking shadows. Actual animation playback, layer alignment and phone performance remain untested.

## Next visual acceptance
After foundation device validation: render one matching room with floor, wall, window/door frame, roof, bed, sofa, counter, cabinet and a few supplies. Sort sprites and actors by world ground contact, split walls where needed, test near/far occlusion and roof cutaway in actual Godot. No unrelated asset libraries should be added.
