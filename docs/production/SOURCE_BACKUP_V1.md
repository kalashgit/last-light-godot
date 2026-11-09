# LAST LIGHT — 360 Model Source Backup: Exact Location and Recovery V1

## Where the source archive actually is
- [GitHub Actions run 42460745955](https://github.com/kalashgit/last-light-godot/actions/runs/42460745955) -> **Artifacts** -> `last-light-360-editable-3d-masters-geometry-only-v1`.
- GitHub API artifact ID `13609641055`, file size `109843548` bytes, download archive integrity digest `sha256:fc2307651a1d4c3899af70bb2eeae452a4be901f7a308c40cfe1bfe99b5b61d6`.
- GitHub reports `expired=false` and `expires_at=2026-12-08T07:56:45Z` as checked 2026-11-08.
- The artifact contains a compressed bundle with `Last_Light_3D_Masters_All_360.zip` as documented in Notion. Preserve **the complete outer download** and the inner original source archive.
- Source branch: `codex/last-light-geometry-reconstruction-v1-20261108` ; source commit: `d636474a8c2fa89c039cf1a9531b20b521126cf2`.
- [360 source ledger `batch_report.json`](https://github.com/kalashgit/last-light-godot/blob/codex/last-light-geometry-reconstruction-v1-20261108/preview/geometry-first-all-360/batch_report.json) — 360 IDs, recipe hashes, GLB hashes, dimensions and warnings. Report status is **3D SOURCE ONLY**, not Golden/fully textured.
- [Source library instructions](https://github.com/kalashgit/last-light-godot/blob/codex/last-light-geometry-reconstruction-v1-20261108/docs/GEOMETRY_FIRST_SOURCE_LIBRARY_V1.md).

## On an iPhone
1. Open the GitHub Actions run link in Safari while signed in.
2. Under **Artifacts** tap the named artifact ZIP; use Desktop Website if download UI is obscured.
3. Save the downloaded ZIP in the Files app, ideally **iCloud Drive / LAST LIGHT / Backups / 3D_Masters_360 / 2026-11-08**.
4. Verify the complete ZIP is present and opens. Retain the unmodified ZIP and a second backup in a separate storage location.
5. Copy the linked `batch_report.json` and source library instructions into the same backup folder; preserve source branch and commit SHA in a small text note.
6. Do not permanently store source only in a temporary iPhone app folder or rely solely on GitHub's expiring CI artifact.

## Preferred permanent storage
A private storage location such as private cloud drive or an encrypted external drive for full editable archives; GitHub repository tracks **scripts + manifests + approved lightweight runtime assets**. Git LFS or separately managed release/backup storage may be considered if ownership, cost, quota and repository visibility are reviewed.
**The repository currently reports public visibility.** Avoid uploading proprietary raw assets until publication intent is confirmed.

## Verification
- Verify archive count and ability to reopen sample `.blend` and `.glb` files in Blender; use the per-entry SHA manifest.
- Outer artifact digest is supplied by GitHub; checksum tools may measure a different downloaded wrapper/inner ZIP, so record *which file* was hashed. Do not claim the inner archive hash equals the outer artifact hash without checking.
- Check no missing records: source manifest `generated_3d_source_count=360`.
- Mark backup status as VERIFIED only after a downloaded permanent copy is successfully reopened and validated.

## Rebuild
On the source branch, study:
`tools/geometry_first/plan.py`, `golden40_mesh.py`, `export.py`, `qa.py`, `stage2_render.py` and workflow `.github/workflows/geometry-first-all-360-v1.yml`. Re-run the recorded workflow or documented commands on authorized runners with matching tool versions. Regeneration must not be mistaken for exact artistic equivalence or visual approval.

**Backup status at documentation creation: NOT VERIFIED IN PERMANENT STORAGE.**
