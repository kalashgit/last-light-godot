"""Strict offline-only multimodal recipe proposal interface.

For a *running* local OpenAI-compatible vision server (e.g. llama.cpp with
Qwen2.5-VL). This module never downloads weights, accesses a hosted provider,
runs model-generated Python, or treats a candidate as Golden art.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

from .batch import fresh_output
from .contract import sha256, validate
from .pilot import dump
from .vision import pixel_report


MAX_IMAGE_BYTES = 1_500_000
MAX_RESPONSE_BYTES = 200_000
MAX_TOKENS = 12_000
MAX_SECONDS = 180
_ALLOWED_FIELDS = {
    "category", "function", "observations", "assumptions", "artifacts",
    "confidence", "components", "materials", "expected_silhouette", "footprint_m",
}
_SYSTEM_PROMPT = """You are a physical-object construction architect, NOT an image-to-3D tracer.
Read the actual supplied pixels. Return one JSON object, with exactly these keys:
category (snake_case), function (string), observations (list {component,detail,confidence}),
assumptions (same), artifacts (list of strings), confidence (0..1),
materials (list of {name,class,rgba,metallic,roughness,wear,texture}),
components (list of {name,parent,op,material,location,rotation_deg,geometry,
observed,confidence,modifiers,topology}), expected_silhouette (string), footprint_m ([x,y]).
Output 3-80 genuinely physical component meshes, 2-20 materials, metric proportions.
Permitted ops: box {size:[x,y,z],bevel}, cylinder {radius,depth,vertices,bevel},
lathe {profile:[[radius,z],...],vertices}, tube {points:[[x,y,z],...],radius,closed},
polygon_extrude {points:[[x,y],...],depth,bevel}, text {value,size,extrude},
boolean_cut {target,size:[x,y,z],bevel}. Use allowed material classes:
plastic, metal, rubber, paint, paper, fabric, ceramic, food. Textures: none, fine_noise, scuffed.
Modifiers: weighted_normals, subdivide_1, uv_unwrap. Topology: closed, surface,
text_mesh, cutter. Each component uses 3-vector location and rotation_deg and
parent null or a component name; material must match a named material.
Observed geometry must be supported by the image. Flag hidden components as
assumptions and observed=false. Treat white patches as uncertain image artifacts.
Never add contents to an otherwise empty container. Invent original generic labels.
No source textures, copyrighted designs, arbitrary Python, markdown or commentary.
If you cannot identify useful geometry, return an invalid/incomplete proposal
to force manual review; NEVER silently invent a generic-box replacement."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Do not allow a loopback model server to forward private images."""

    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise ValueError("local inference request attempted redirect")


def checked_loopback_url(endpoint: str) -> str:
    """Only the user's own local model process may receive private pixels."""
    parsed = urllib.parse.urlsplit(endpoint)
    if (parsed.scheme != "http" or parsed.hostname not in ("127.0.0.1", "::1")
            or parsed.username is not None or parsed.password is not None
            or parsed.path not in ("/v1/chat/completions", "/chat/completions")
            or parsed.query or parsed.fragment or parsed.port is None):
        raise ValueError("local VLM must be an explicit HTTP loopback chat/completions endpoint")
    if not 1 <= parsed.port <= 65535:
        raise ValueError("invalid local model port")
    return endpoint


def request_proposal(source: Path, *, endpoint: str, model: str) -> tuple[dict, dict]:
    checked_loopback_url(endpoint)
    if re.fullmatch(r"[A-Za-z0-9_.:/-]{1,100}", model) is None:
        raise ValueError("model identifier required; no implicit endpoint or provider")
    metrics = pixel_report(source)
    raw = source.read_bytes()
    if len(raw) > MAX_IMAGE_BYTES or source.suffix.lower() not in (".jpg", ".jpeg", ".png"):
        raise ValueError("pilot accepts only bounded PNG/JPEG inputs")
    mime = "image/png" if source.suffix.lower() == ".png" else "image/jpeg"
    payload = {
        "model": model, "temperature": 0, "seed": 0, "stream": False,
        "max_tokens": MAX_TOKENS, "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": [
                {"type": "text", "text": "Analyze this one object; design original editable 3D components, not flat image planes."},
                {"type": "image_url", "image_url": {"url": "data:" + mime + ";base64," + base64.b64encode(raw).decode()}},
            ]},
        ],
    }
    request = urllib.request.Request(endpoint, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
    # Inherited cloud proxy settings must never route private image pixels to
    # a remote proxy. A local socket is the only accepted destination.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open(request, timeout=MAX_SECONDS) as response:
        body = response.read(MAX_RESPONSE_BYTES + 1)
    if len(body) > MAX_RESPONSE_BYTES:
        raise ValueError("VLM response exceeds bound")
    result = json.loads(body)
    content = result["choices"][0]["message"]["content"]
    if not isinstance(content, str):
        raise ValueError("VLM must return a JSON string, not tool calls")
    proposal = json.loads(content)
    if not isinstance(proposal, dict) or set(proposal) != _ALLOWED_FIELDS:
        raise ValueError("VLM returned incomplete or unauthorized geometry fields")
    return proposal, {"model": model, "source_sha256": metrics["sha256"],
                      "pixels_supplied": True, "response_sha256": hashlib.sha256(body).hexdigest(),
                      "usage": result.get("usage"), "network_scope": "loopback_only",
                      "paid_model_calls": 0, "external_inference": False}


def seal_proposal(source: Path, proposal: dict, *, reference_id: str,
                  source_rights: str, model: str) -> dict:
    """Host, not VLM, assigns identity, source rights, QA, and approval gates."""
    if not isinstance(proposal, dict) or set(proposal) != _ALLOWED_FIELDS:
        raise ValueError("model must provide exact proposed construction fields")
    if source_rights not in ("founder_original_pending_review", "verified_reusable"):
        raise ValueError("source rights need an explicit reviewed status")
    if not isinstance(reference_id, str) or not 6 <= len(reference_id) <= 200:
        raise ValueError("verified reference identifier required")
    if re.fullmatch(r"[A-Za-z0-9_.:/-]{1,100}", model) is None:
        raise ValueError("invalid provider model")
    metrics = pixel_report(source)
    visible = {c["name"] for c in proposal["components"] if c.get("observed") is True}
    if len(visible) < 2 or not all(obs["component"] in visible for obs in proposal["observations"]):
        raise ValueError("observed descriptions must refer to visible mesh components")
    recipe = {
        "schema": "last-light.recipe-architect.v1",
        "identity": {
            "candidate_id": "candidate_" + metrics["sha256"][:16],
            "source_reference_id": reference_id, "source_sha256": metrics["sha256"],
            "source_rights": source_rights, "asset_family": proposal["category"],
            "recipe_version": 1, "generation_method": "vision_model_proposed",
            "canonical_id": None,
        },
        "visual_analysis": {
            "provider": "local_vlm_" + model, "pixels_inspected": True,
            "image_dimensions": metrics["size"], "probable_function": proposal["function"],
            "category": proposal["category"], "observations": proposal["observations"],
            "assumptions": proposal["assumptions"], "artifacts": proposal["artifacts"],
            "confidence": proposal["confidence"],
        },
        "components": proposal["components"], "materials": proposal["materials"],
        "gameplay": {
            "collision": "box", "movable": True, "interactable_parts": [],
            "container_openings": [], "damage_states": [],
            "footprint_m": proposal["footprint_m"], "animations": [], "attachment_points": [],
        },
        "render": {
            "headings": 16, "resolution": 128, "camera_azimuth_deg": 315,
            "camera_elevation_deg": 35.264, "orthographic_scale": 2.35,
            "key_light": "upper_left", "assembly_scale": [1, 1, 1],
        },
        "quality": {
            "expected_silhouette": proposal["expected_silhouette"],
            "qa_checks": ["schema", "editable_blend", "glb_mesh_count", "render_comparison"],
            "technical_status": "CANDIDATE_PENDING_QA", "golden_approved": False,
            "founder_review": "NOT_GOLDEN",
        },
        "tuning": {"scale_step": 0.07, "max_corrections": 2},
    }
    # A remote/open-weight model is untrusted data. Normalize both schema and
    # procedural validator failures into one fail-closed contract error.
    from jsonschema.exceptions import ValidationError
    try:
        validate(recipe, source, full_schema=True)
    except (ValidationError, ValueError, KeyError, TypeError) as exc:
        raise ValueError("VLM construction proposal failed safe recipe validation") from exc
    return recipe


def main() -> None:
    p = argparse.ArgumentParser(description="Opt-in local image-to-editable-Blender-recipe proposal")
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--reference-id", required=True)
    p.add_argument("--source-rights", choices=("founder_original_pending_review", "verified_reusable"), required=True)
    p.add_argument("--endpoint", required=True, help="explicit local llama-server http://127.0.0.1:PORT/v1/chat/completions")
    p.add_argument("--model", required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    checked_loopback_url(args.endpoint)
    fresh_output(args.out)
    proposal, audit = request_proposal(args.source, endpoint=args.endpoint, model=args.model)
    recipe = seal_proposal(args.source, proposal, reference_id=args.reference_id,
                           source_rights=args.source_rights, model=args.model)
    args.out.mkdir(parents=True, exist_ok=True)
    dump(args.out / "candidate_recipe.json", recipe)
    dump(args.out / "inference_audit.json", {**audit, "candidate_id": recipe["identity"]["candidate_id"],
            "schema_valid": True, "golden_approved": False, "human_review_required": True})
    print("LL_LOCAL_VLM_RECIPE_CANDIDATE", recipe["identity"]["candidate_id"],
          "VALIDATED_NOT_GOLDEN", flush=True)


if __name__ == "__main__":
    main()
