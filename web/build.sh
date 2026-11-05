#!/usr/bin/env bash
set -euo pipefail

# PREVIEW ONLY: export the isolated five-building laboratory without changing
# the default startup scene of the actual game in project.godot.
ROOT="$(pwd)"
GODOT_RELEASE="4.3-stable"
GODOT_BIN_NAME="Godot_v4.3-stable_linux.x86_64"
TOOLS_DIR="$(mktemp -d)"
STAGE_DIR="$(mktemp -d)"
cleanup() {
  rm -rf -- "$TOOLS_DIR" "$STAGE_DIR"
}
trap cleanup EXIT

if [[ -n "${GODOT_BIN:-}" && -x "${GODOT_BIN}" ]]; then
  GODOT_EXEC="${GODOT_BIN}"
else
  echo "Installing official Godot ${GODOT_RELEASE} editor"
  curl -fsSL --retry 3 "https://github.com/godotengine/godot/releases/download/${GODOT_RELEASE}/${GODOT_BIN_NAME}.zip" -o "$TOOLS_DIR/godot.zip"
  unzip -q "$TOOLS_DIR/godot.zip" -d "$TOOLS_DIR"
  chmod +x "$TOOLS_DIR/$GODOT_BIN_NAME"
  GODOT_EXEC="$TOOLS_DIR/$GODOT_BIN_NAME"
fi

TEMPLATE_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/godot/export_templates/4.3.stable"
if [[ ! -s "$TEMPLATE_DIR/web_nothreads_release.zip" ]]; then
  echo "Installing official Godot ${GODOT_RELEASE} Web export templates"
  curl -fsSL --retry 3 "https://github.com/godotengine/godot/releases/download/${GODOT_RELEASE}/Godot_v4.3-stable_export_templates.tpz" -o "$TOOLS_DIR/templates.tpz"
  mkdir -p "$TEMPLATE_DIR"
  unzip -jo "$TOOLS_DIR/templates.tpz" 'templates/web_nothreads_release.zip' 'templates/web_nothreads_debug.zip' -d "$TEMPLATE_DIR"
fi

echo "Staging a copy; the repository's main scene remains unchanged"
tar -C "$ROOT" --exclude=.git --exclude=.godot --exclude=public -cf - . | tar -C "$STAGE_DIR" -xf -
sed -i 's|^run/main_scene=.*|run/main_scene="res://scenes/five_building_material_lab.tscn"|' "$STAGE_DIR/project.godot"
if ! grep -q '^run/main_scene="res://scenes/five_building_material_lab.tscn"$' "$STAGE_DIR/project.godot"; then
  echo "Could not select the isolated laboratory scene" >&2
  exit 1
fi

echo "Importing laboratory assets"
"$GODOT_EXEC" --headless --path "$STAGE_DIR" --editor --import --quit
mkdir -p "$ROOT/public"
echo "Exporting playable five-building Web build"
"$GODOT_EXEC" --headless --path "$STAGE_DIR" --export-release Web "$ROOT/public/index.html"
test -s "$ROOT/public/index.html"
test -s "$ROOT/public/index.wasm"
test -s "$ROOT/public/index.pck"
# A selected-scene export can silently omit GDScript preload/inheritance chains.
# The HTML shell still loads, but the actual game never renders. Validate the
# exported pack's directory entries before publishing another broken preview.
for required in \
  'scripts/five_building_material_lab.gdc' \
  'scripts/material_kit_lab.gdc' \
  'scripts/building_material_renderer.gdc' \
  'scripts/lab_survival_state.gdc' \
  'assets/materials/wall_kit_atlas_v1.png' \
  'assets/buildings/five_building_lab_v2.json' \
  'assets/items/lab_items_v1.json'; do
  if ! LC_ALL=C grep -aFq "$required" "$ROOT/public/index.pck"; then
    echo "Export failed: missing required laboratory dependency $required" >&2
    exit 1
  fi
done
echo "LAST LIGHT isolated laboratory Web export complete"
