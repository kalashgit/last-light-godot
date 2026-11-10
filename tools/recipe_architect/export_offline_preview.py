"""Portable one-file, read-only review preview with *rendered* images only.

No private source pixels, tokens, model inference or server is bundled. This
exports a convenience browser preview, NOT an authenticated approval console.
"""
from __future__ import annotations

import argparse
import base64
import copy
import json
from pathlib import Path

from .mesh_workspace import MAX_ROOMS, SCHEMA
from .serve_workspace import UI


MAX_EMBED_BYTES = 15_000_000


def _encoded(root: Path, relative: str, extension: str) -> str:
    if not isinstance(relative, str) or relative.startswith("/") or "\\" in relative:
        raise ValueError("invalid offline artifact reference")
    path = root / relative
    if not path.resolve().is_relative_to(root.resolve()) or path.suffix != extension or not path.is_file():
        raise ValueError("offline artifact outside bounded workspace")
    mime = {".png": "image/png", ".glb": "model/gltf-binary", ".blend": "application/octet-stream"}[extension]
    return "data:" + mime + ";base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def export(data_root: Path, out: Path) -> dict:
    if out.exists():
        raise FileExistsError("offline preview must not overwrite an existing file")
    manifest = json.loads((data_root / "manifest.json").read_text())
    if manifest.get("schema") != SCHEMA or not 1 <= manifest.get("room_count", 0) <= MAX_ROOMS:
        raise ValueError("unrecognized workspace manifest")
    if manifest.get("automated_golden_approval") or any(r.get("golden_approved") for r in manifest["rooms"]):
        raise ValueError("offline preview cannot carry Golden promotion")
    portable = copy.deepcopy(manifest)
    for room in portable["rooms"]:
        if room.get("source_image_exposed"):
            raise ValueError("private source art cannot enter offline preview")
        cache: dict[str, str] = {}

        def encode(path: str, extension: str) -> str:
            if path not in cache:
                cache[path] = _encoded(data_root, path, extension)
            return cache[path]

        if room.get("preview"):
            room["preview"] = encode(room["preview"], ".png")
        room["headings"] = [encode(relative, ".png") for relative in room.get("headings", [])]
        # Only actual downloadable geometry, no raw production logs or private art.
        room["files"] = {key: encode(value, ".glb" if key == "glb" else ".blend")
                         for key, value in room.get("files", {}).items() if key in ("glb", "blend")}
    template = (UI / "index.html").read_text()
    style = (UI / "style.css").read_text()
    script = (UI / "app.js").read_text()
    if '</style' in style.lower() or '</script' in script.lower():
        raise ValueError("embedded style/script unexpectedly contains closing tag")
    # Prevent a provisional source label from terminating the inline script.
    payload = json.dumps(portable, separators=(",", ":"), ensure_ascii=True).replace("<", "\\u003c")
    result = template.replace('<link rel="stylesheet" href="style.css">', f"<style>{style}</style>")
    result = result.replace('<script src="app.js" defer></script>', "")
    result = result.replace("</body>",
                            f"<script>window.__LL_MESH_OFFLINE_MANIFEST={payload};\n{script}</script>\n</body>")
    if len(result.encode()) > MAX_EMBED_BYTES:
        raise ValueError("portable preview exceeds 15 MB bound")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(result, encoding="utf-8")
    return {"room_count": len(portable["rooms"]), "bytes": out.stat().st_size,
            "contains_reference_pixels": False, "founder_golden_approved": False,
            "standalone_html": str(out)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Export offline local browser preview")
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    print("LL_MESH_OFFLINE_PREVIEW", json.dumps(export(args.data_root, args.out)))


if __name__ == "__main__":
    main()
