"""Independent local-vision component detection -> bounded real-Blender repair.

No manually drawn target box is supplied: a *running* loopback VLM sees the
original source and a fresh Blender baseline image, selects one source-observed
physical part, and proposes its source-image region. The model's output is
untrusted advice. Only a deterministic validator, shape mutation whitelist,
real rendered feature improvements, physical contacts, and raycasts can advance
the candidate. This is not a trained model, quality oracle, or Golden approval.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import re
import urllib.request
from pathlib import Path

from PIL import Image

from .batch import fresh_output
from .component_geometry_optimize import normalize_rect, optimize, recipe_digest
from .contract import sha256, validate
from .local_vlm import NoRedirect, checked_loopback_url
from .pilot import dump, run_blender


MODEL_FIELDS = frozenset({"status", "component", "source_bbox_px", "defect_type",
                          "suggested_parameter", "suggested_direction", "confidence", "explanation"})
DEFECTS = frozenset({"missing_extent", "oversized_extent", "wrong_proportion",
                     "misplaced_silhouette", "occluded"})
PARAMETERS = {
    "box": {"size_x", "size_y", "size_z"},
    "cylinder": {"radius", "depth"},
    "polygon_extrude": {"points_x", "points_y", "depth"},
    "tube": {"radius", "points_x", "points_y", "points_z"},
    "lathe": {"radius", "height"},
    "text": {"size"},
}
SYSTEM_PROMPT = """You are an independent 2D-versus-3D component geometry inspector.
Image 1 is the SOURCE SPRITE. Image 2 is an ACTUAL BLENDER render of its existing
mesh. Compare their visible physical shapes. The listed component names are the
ONLY legal components; measured render projections identify which mesh creates
which pixels. Locate the most important shape mismatch, name its component, and
draw its bounding box on IMAGE 1, in IMAGE 1's actual pixel coordinates.
Do not use or request manually supplied target rectangles. Do not invent hidden
geometry, treat white background as a feature, or copy the sprite as a texture.
If uncertain or no meaningful defect is visible, output no_confident_defect.
Return exactly one JSON object, no markdown, with keys:
status: "defect" or "no_confident_defect";
component: listed component name or null;
source_bbox_px: [left,top,right,bottom] in SOURCE pixel coordinates or null;
defect_type: missing_extent, oversized_extent, wrong_proportion,
misplaced_silhouette, occluded, or null;
suggested_parameter: allowed parameter from the listed component or null;
suggested_direction: increase, decrease, unknown, or null;
confidence: numeric 0..1; explanation: short factual string.
The proposal only chooses which permitted Blender trial to check first; it
cannot approve a mesh, revise unobserved parts or skip source validation."""


def _data_uri(image: Path) -> str:
    raw = image.read_bytes()
    if len(raw) > 1_500_000 or image.suffix.lower() not in (".png", ".jpg", ".jpeg"):
        raise ValueError("source/render must be bounded PNG/JPEG")
    mime = "image/png" if image.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(raw).decode()}"


def _visible_parts(recipe: dict, projections: dict) -> list[dict]:
    if (projections.get("schema") != "last-light.recipe-projections.v1" or
            projections.get("heading") != 0 or
            projections.get("resolution") != recipe["render"]["resolution"]):
        raise ValueError("not source-view measured Blender projections")
    observed = {item["component"] for item in recipe["visual_analysis"]["observations"]}
    parts = []
    for component in recipe["components"]:
        name = component["name"]
        if name not in observed or not component["observed"] or component["op"] not in PARAMETERS:
            continue
        measurement = projections.get("components", {}).get(name)
        if (not isinstance(measurement, dict) or
                measurement.get("bbox_method") != "actual_blender_mesh_vertices_pre_bevel"):
            continue
        parts.append({"name": name, "op": component["op"],
                      "allowed_parameter_hints": sorted(PARAMETERS[component["op"]]),
                      "render_bbox_px": measurement["bbox_px"]})
    if not parts:
        raise ValueError("no physical observed parts with actual Blender measurements")
    return parts


def request_detection(source: Path, render: Path, *, recipe: dict,
                      projections: dict, endpoint: str, model: str) -> tuple[dict, dict]:
    """Only an explicitly running local model receives the two images."""
    checked_loopback_url(endpoint)
    if re.fullmatch(r"[A-Za-z0-9_.:/-]{1,100}", model) is None:
        raise ValueError("explicit local vision model identifier required")
    parts = _visible_parts(recipe, projections)
    with Image.open(source) as im:
        if im.width > 2048 or im.height > 2048 or min(im.size) < 16:
            raise ValueError("invalid source image dimensions")
        dimensions = im.size
    with Image.open(render) as im:
        if im.width != recipe["render"]["resolution"] or im.height != im.width:
            raise ValueError("Blender baseline has wrong image dimensions")
    payload = {"model": model, "temperature": 0, "seed": 0, "stream": False,
               "max_tokens": 950, "response_format": {"type": "json_object"},
               "messages": [
                   {"role": "system", "content": SYSTEM_PROMPT},
                   {"role": "user", "content": [
                       {"type": "text", "text": json.dumps({
                           "source_dimensions_px": dimensions,
                           "source_observed_parts_and_render_measurements": parts,
                           "task": "Find one mismatched physical part in source image 1 vs Blender image 2. No manually specified boxes.",
                       }, separators=(",", ":"))},
                       {"type": "image_url", "image_url": {"url": _data_uri(source)}},
                       {"type": "image_url", "image_url": {"url": _data_uri(render)}},
                   ]},
               ]}
    encoded = json.dumps(payload, separators=(",", ":")).encode()
    if len(encoded) > 3_500_000:
        raise ValueError("local VLM request exceeds byte budget")
    req = urllib.request.Request(endpoint, data=encoded,
                                 headers={"Content-Type": "application/json"}, method="POST")
    # An inherited proxy or HTTP redirect must never exfiltrate private sprites.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open(req, timeout=120) as response:
        raw = response.read(64_001)
    if len(raw) > 64_000:
        raise ValueError("local vision response exceeded byte budget")
    envelope = json.loads(raw)
    output = envelope["choices"][0]["message"]["content"]
    if not isinstance(output, str):
        raise ValueError("local vision must return a JSON string")
    proposal = json.loads(output)
    if not isinstance(proposal, dict) or set(proposal) != MODEL_FIELDS:
        raise ValueError("local vision returned unrecognized component fields")
    return proposal, {"model": model, "source_sha256": sha256(source),
                      "recipe_sha256": recipe_digest(recipe),
                      "baseline_render_sha256": sha256(render),
                      "request_sha256": hashlib.sha256(encoded).hexdigest(),
                      "response_sha256": hashlib.sha256(raw).hexdigest(),
                      "network_scope": "loopback_only", "pixels_supplied": True,
                      "actual_local_vision_request_completed": True,
                      "external_inference": False, "paid_model_calls": 0,
                      "usage_unverified": envelope.get("usage")}


def _source_roi_contains_object(source: Path, rect: list) -> bool:
    with Image.open(source) as im:
        normalize_rect(rect, im)
        x0, y0, x1, y1 = [int(math.floor(rect[0])), int(math.floor(rect[1])),
                          int(math.ceil(rect[2])), int(math.ceil(rect[3]))]
        crop = im.convert("RGBA").crop((x0, y0, x1, y1))
        # Accept true-alpha cutouts or light-background sprites. Reject an
        # arbitrary region containing only blank white/transparent pixels.
        solid = sum(1 for r, g, b, a in crop.get_flattened_data()
                    if a > 48 and min(r, g, b) < 235)
        return solid >= 6 and solid / max(1, crop.width * crop.height) >= .02


def validate_detection(source: Path, recipe: dict, projections: dict,
                       proposal: dict, receipt: dict) -> dict | None:
    if (not isinstance(proposal, dict) or set(proposal) != MODEL_FIELDS or
            receipt.get("source_sha256") != sha256(source) or
            receipt.get("recipe_sha256") != recipe_digest(recipe) or
            receipt.get("network_scope") != "loopback_only" or
            receipt.get("actual_local_vision_request_completed") is not True):
        raise ValueError("unbound local VLM component detection")
    confidence = proposal["confidence"]
    if type(confidence) not in (float, int) or not math.isfinite(confidence) or not 0 <= confidence <= 1:
        raise ValueError("invalid independent feature confidence")
    if (not isinstance(proposal["explanation"], str) or
            not 1 <= len(proposal["explanation"]) <= 500):
        raise ValueError("short factual detection explanation required")
    if proposal["status"] == "no_confident_defect":
        if any(proposal[field] is not None for field in
               ("component", "source_bbox_px", "defect_type", "suggested_parameter", "suggested_direction")):
            raise ValueError("uncertain detection must not smuggle a geometry target")
        return None
    if proposal["status"] != "defect":
        raise ValueError("unknown component-detection decision")
    names = {part["name"]: part for part in _visible_parts(recipe, projections)}
    component = proposal["component"]
    if (not isinstance(component, str) or component not in names or
            not isinstance(proposal["defect_type"], str) or
            proposal["defect_type"] not in DEFECTS):
        raise ValueError("model selected invented, unobserved, or unsupported component")
    parameter = proposal["suggested_parameter"]
    if parameter is not None and (not isinstance(parameter, str) or
                                  parameter not in names[component]["allowed_parameter_hints"]):
        raise ValueError("vision model requested forbidden geometry parameter")
    if (proposal["suggested_direction"] not in ("increase", "decrease", "unknown") or
            (parameter is None and proposal["suggested_direction"] != "unknown")):
        raise ValueError("invalid bounded shape guidance")
    if confidence < .75:
        return None  # Low-confidence detections never create repair orders.
    rect = proposal["source_bbox_px"]
    if (not isinstance(rect, list) or len(rect) != 4 or
            any(type(x) not in (float, int) for x in rect)):
        raise ValueError("model must independently locate source component rectangle")
    if not _source_roi_contains_object(source, rect):
        raise ValueError("source region is outside the sprite or lacks visible object pixels")

    # Contact neighbors come from Blender world bounds, NOT from the model.
    projections_by_name = projections["components"]
    here = projections_by_name[component]["world_bbox_m"]
    contacts = []
    for name in names:
        if name == component:
            continue
        other = projections_by_name[name]["world_bbox_m"]
        gaps = [max(0, here[0][i] - other[1][i], other[0][i] - here[1][i]) for i in range(3)]
        gap = math.sqrt(sum(value * value for value in gaps))
        if gap <= .025:
            contacts.append((gap, name))
    contacts = [name for _, name in sorted(contacts)[:8]]
    target = {"schema": "last-light.vlm-component-geometry-target.v1",
              "source_sha256": sha256(source),
              "candidate_id": recipe["identity"]["candidate_id"],
              "provenance": "local_vlm_component_detection",
              "component": component, "source_bbox_px": rect,
              "defect_type": proposal["defect_type"],
              "suggested_parameter": parameter, "suggested_direction": proposal["suggested_direction"],
              "confidence": confidence, "explanation": proposal["explanation"],
              "required_visible_components": [component] + contacts,
              "contact_neighbors": contacts, "vision_inference": receipt,
              "approval": "NOT_GOLDEN"}
    # The exact same target validation also gates manually annotated regions.
    from .component_geometry_optimize import validate_target
    validate_target(target, recipe, source)
    return target


def inspect_and_repair(recipe_file: Path, source: Path, out: Path, *, endpoint: str,
                       model: str, blender: str = "blender",
                       render_func=run_blender, repair_func=optimize) -> dict:
    checked_loopback_url(endpoint)
    recipe = json.loads(recipe_file.read_text())
    validate(recipe, source, full_schema=True)
    fresh_output(out)
    out.mkdir(parents=True)
    baseline = out / "trusted_baseline"
    render_func(blender, recipe_file, baseline, headings=1, export=False)
    render = baseline / "heading_00.png"
    projections = json.loads((baseline / "component_projections.json").read_text())
    proposal, receipt = request_detection(source, render, recipe=recipe,
                                          projections=projections, endpoint=endpoint, model=model)
    dump(out / "model_proposal_untrusted.json", proposal)
    dump(out / "local_vision_inference_receipt.json", receipt)
    target = validate_detection(source, recipe, projections, proposal, receipt)
    result = {"schema": "last-light.independent-component-repair.v1",
              "candidate_id": recipe["identity"]["candidate_id"],
              "source_sha256": sha256(source), "actual_local_vision_request_completed": True,
              "independent_feature_recognition_attempted": True, "golden_approved": False,
              "automatic_game_admission": False}
    if target is None:
        result.update({"status": "HOLD_NO_CONFIDENT_DETECTED_COMPONENT",
                       "geometry_optimization_run": False})
    else:
        dump(out / "vision_derived_target.json", target)
        repaired = repair_func(recipe_file, source, out / "vision_derived_target.json",
                               out / "geometry_search", blender=blender)
        result.update({"status": repaired["status"], "component": target["component"],
                       "geometry_optimization_run": True,
                       "geometry_correction_report": "geometry_search/geometry_correction_report.json",
                       "measured_feature_gain": repaired["measured_feature_gain"],
                       "shape_changed": repaired["shape_changed"]})
    dump(out / "independent_repair_report.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--recipe", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--endpoint", required=True, help="local 127.0.0.1 VLM server only")
    parser.add_argument("--model", required=True)
    parser.add_argument("--blender", default="blender")
    args = parser.parse_args()
    report = inspect_and_repair(args.recipe, args.source, args.out, endpoint=args.endpoint,
                                model=args.model, blender=args.blender)
    print("LL_INDEPENDENT_COMPONENT_GEOMETRY", report["status"], "NOT_GOLDEN", flush=True)


if __name__ == "__main__":
    main()
