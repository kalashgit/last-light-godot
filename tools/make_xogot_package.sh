#!/usr/bin/env bash
# Builds an iPhone/Xogot test package of the committed tree (git archive HEAD).
# The ONLY change inside the zip: project.godot boots the GM00 sandbox scene, so
# the founder can press Play in Xogot without switching scenes. The repository's
# own project.godot keeps run/main_scene="res://main.tscn" (protected).
set -euo pipefail
cd "$(dirname "$0")/.."
out="build/xogot"
rm -rf "$out/stage" && mkdir -p "$out/stage"
git archive HEAD | tar -x -C "$out/stage"
rm -rf "$out/stage/.github" "$out/stage/tests" "$out/stage/tools" "$out/stage/build"
sed -i 's#run/main_scene="res://main.tscn"#run/main_scene="res://scenes/gm00_world_sandbox.tscn"#' "$out/stage/project.godot"
grep -q 'gm00_world_sandbox.tscn' "$out/stage/project.godot"
sha=$(git rev-parse --short HEAD)
cat > "$out/stage/XOGOT_PACKAGE_README.txt" <<TXT
LAST LIGHT — GM00 developer sandbox package (commit $sha)
Open this folder in Xogot and press Play: it boots scenes/gm00_world_sandbox.tscn.
The original playable game is unchanged at res://main.tscn (run it via its scene).
All art is PROVISIONAL procedural placeholder. Follow docs/gm00/IPHONE_TEST_CHECKLIST.md.
TXT
name="LAST_LIGHT_GM00_xogot_${sha}.zip"
(cd "$out/stage" && zip -qr "../$name" .)
echo "$out/$name"
