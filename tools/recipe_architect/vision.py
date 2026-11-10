"""Replaceable, bounded, opt-in vision model interface.

No network call is made unless explicitly enabled by a human with a provider
configuration AND billing authorization. Offline archived observations are
kept distinct from autonomous model output.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import urllib.request
from pathlib import Path

from PIL import Image

from .contract import sha256, validate
from .seed_recipes import SEEDS, SHA


def pixel_report(source: Path) -> dict:
    with Image.open(source) as image:
        rgba = image.convert("RGBA")
        alpha = rgba.getchannel("A")
        bbox = alpha.getbbox()
        if not bbox or alpha.getextrema()[1] == 0:
            raise ValueError("reference missing visible pixels")
        if rgba.width > 2048 or rgba.height > 2048:
            raise ValueError("source image too large for bounded pilot")
        return {"size": list(rgba.size), "alpha_bbox": list(bbox),
                "alpha_pixel_count": sum(x >= 128 for x in (alpha.get_flattened_data() if hasattr(alpha, "get_flattened_data") else alpha.getdata())),
                "sha256": sha256(source), "actual_pixels_examined": True}


def archived_inspection(source: Path, family: str) -> dict:
    """Known inspected real source; not an autonomous inference result."""
    metrics = pixel_report(source)
    if family not in SEEDS or metrics["sha256"] != SHA[family]:
        raise ValueError("no pixel-inspected seed for source checksum")
    seed = SEEDS[family]()
    if metrics["size"] != seed["visual_analysis"]["image_dimensions"]:
        raise ValueError("source dimensions mismatch")
    validate(seed, source, full_schema=True)
    return {"analysis": seed["visual_analysis"], "pixel_report": metrics,
            "method": "stored_session_pixel_inspection_NOT_autonomous_model"}


def model_inspection(source: Path, *, approved_paid_inference: bool = False) -> dict:
    """An OpenAI-compatible vision endpoint, replaceable with local VLM later.

    This is deliberately opt-in. No implicit model name, endpoint, token, retries,
    batch work, or unlimited requests. Max one request with fixed output cap.
    """
    if not approved_paid_inference:
        raise PermissionError("Founder approval of provider/billing required before vision inference")
    base = os.getenv("LL_VISION_BASE_URL", "")
    model = os.getenv("LL_VISION_MODEL", "")
    token = os.getenv("LL_VISION_API_KEY", "")
    if not base.startswith("https://") or not base.endswith("/chat/completions") or not model or not token:
        raise ValueError("explicit HTTPS provider endpoint, model, and API key required")
    metrics = pixel_report(source)
    mime = "image/png" if source.suffix.lower() == ".png" else "image/jpeg"
    payload = {
        "model": model, "temperature": 0, "max_tokens": 1150,
        "messages": [
            {"role": "system", "content": "Analyze only visible object pixels. Return strictly JSON object: category (snake_case), function, observations array of {component,detail,confidence}, assumptions array same schema, artifacts array, confidence 0..1. Distinguish observed from inferred; do not hallucinate hidden parts. Never return Python code."},
            {"role": "user", "content": [
                {"type": "text", "text": "Inspect this isolated founder-provided game sprite and report physical construction. White patches may be missing/background artifacts."},
                {"type": "image_url", "image_url": {"url": "data:" + mime + ";base64," + base64.b64encode(source.read_bytes()).decode()}}
            ]}
        ]
    }
    request = urllib.request.Request(base, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + token}, method="POST")
    with urllib.request.urlopen(request, timeout=60) as response:
        result = json.loads(response.read(300_000))
    content = result["choices"][0]["message"]["content"]
    observation = json.loads(content)
    if set(observation) != {"category", "function", "observations", "assumptions", "artifacts", "confidence"}:
        raise ValueError("provider returned unexpected analysis structure")
    return {"analysis": observation, "pixel_report": metrics, "method": "model_pixel_inference",
            "provider": {"model": model, "endpoint_host_only": base.split("/")[2], "usage": result.get("usage"),
                         "max_requests": 1, "provider_bill_may_apply": True}}


def recipe_from_analysis(source: Path, result: dict) -> dict:
    """Use only proven family templates; unknown shapes fail closed rather than boxes."""
    visual = result["analysis"]
    category = visual["category"]
    if result["method"] != "model_pixel_inference":
        raise ValueError("use archived_inspection to reproduce the hand-inspected pilot")
    if category not in SEEDS:
        raise ValueError("unrecognized geometry family; requires new reviewed family template")
    recipe = SEEDS[category]()
    recipe["identity"]["source_sha256"] = sha256(source)
    recipe["identity"]["source_reference_id"] = "external_user_input_" + sha256(source)[:16]
    recipe["identity"]["generation_method"] = "vision_model_proposed"
    recipe["visual_analysis"] = {
        "provider": result["provider"]["model"], "pixels_inspected": True,
        "image_dimensions": result["pixel_report"]["size"],
        "probable_function": visual["function"], "category": category,
        "observations": visual["observations"], "assumptions": visual["assumptions"],
        "artifacts": visual["artifacts"], "confidence": visual["confidence"]}
    validate(recipe, source, full_schema=True)
    return recipe
