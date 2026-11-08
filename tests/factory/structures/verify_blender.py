"""True Blender source-reopen and GLB reimport QA for F02 calibration.

Usage: PYTHONHOME=/usr blender -b --factory-startup -t 2 --python \
  tests/factory/structures/verify_blender.py -- --output-dir build/f02_calibration
"""
import argparse
import json
from pathlib import Path
import sys
import bpy


def main():
    p = argparse.ArgumentParser()
    argv = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p.add_argument("--output-dir", type=Path, required=True)
    args = p.parse_args(argv)
    checks = []
    for subject in ("small_house", "garage", "shopfront", "door_window", "roof_corner"):
        target = args.output_dir / subject
        manifest = json.loads((target / "manifest.json").read_text())
        assert manifest["status"] == "NONCANONICAL_CALIBRATION_ONLY"
        count = len(manifest["parts"])
        bpy.ops.wm.open_mainfile(filepath=str((target / f"{subject}_calibration.blend").resolve()))
        source_meshes = [o for o in bpy.data.objects if o.type == "MESH"]
        assert len(source_meshes) == count, (subject, len(source_meshes), count)
        assert bpy.context.scene.camera and bpy.context.scene.camera.data.type == "ORTHO"
        assert all(o.data.materials for o in source_meshes)
        assert all(abs(o.scale[0]) > 0 for o in source_meshes)
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=str((target / f"{subject}_calibration.glb").resolve()))
        imported_meshes = [o for o in bpy.data.objects if o.type == "MESH"]
        assert len(imported_meshes) == count, (subject, len(imported_meshes), count)
        assert all(len(o.data.polygons) >= 6 for o in imported_meshes)
        checks.append({"subject": subject, "blend_meshes": len(source_meshes),
                       "glb_meshes": len(imported_meshes), "result": "PASS"})
        print("F02_BLEND_REOPEN_GLB_IMPORT_PASS", subject, count, flush=True)
    (args.output_dir / "reopen_qa.json").write_text(json.dumps(checks, indent=2)+"\n")


if __name__ == "__main__":
    main()
