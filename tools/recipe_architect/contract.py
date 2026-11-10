"""Reject untrusted operations, malformed geometry, non-finite numbers and source drift.

This module uses only Python stdlib so Blender can run the same checks. The host
also runs full Draft 2020-12 JSON Schema validation when jsonschema is present.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

OPS = {"box", "cylinder", "lathe", "tube", "polygon_extrude", "text", "boolean_cut"}
MATERIAL_CLASSES = {"plastic", "metal", "rubber", "paint", "paper", "fabric", "ceramic", "food"}
GEOM_KEYS = {
    "box": {"size", "bevel"}, "cylinder": {"radius", "depth", "vertices", "scale_xy", "bevel"},
    "lathe": {"profile", "vertices", "scale_xy"}, "tube": {"points", "radius", "closed"},
    "polygon_extrude": {"points", "depth", "bevel"}, "text": {"value", "size", "extrude"},
    "boolean_cut": {"target", "size", "bevel"},
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def finite(value: object, label: str, minimum: float = -100, maximum: float = 100) -> float:
    if type(value) not in (int, float) or not math.isfinite(value) or not minimum <= value <= maximum:
        raise ValueError(f"invalid numeric {label}: {value}")
    return float(value)


def vector(value: object, label: str, length: int, minimum: float = -100, maximum: float = 100) -> list[float]:
    if not isinstance(value, list) or len(value) != length:
        raise ValueError(f"invalid {label} dimension")
    return [finite(v, label, minimum, maximum) for v in value]


def validate(recipe: dict, source: Path | None = None, full_schema: bool = False) -> dict:
    if full_schema:
        from jsonschema import Draft202012Validator
        schema_path = Path(__file__).with_name("recipe.schema.json")
        schema = json.loads(schema_path.read_text())
        Draft202012Validator(schema).validate(recipe)
    if recipe.get("schema") != "last-light.recipe-architect.v1":
        raise ValueError("wrong recipe version")
    identity = recipe["identity"]
    if identity["canonical_id"] is not None or identity["source_rights"] == "unresolved":
        raise ValueError("unapproved canonical identity or rights status")
    if recipe["quality"].get("golden_approved") is not False or recipe["quality"].get("founder_review") != "NOT_GOLDEN":
        raise ValueError("recipe cannot grant Golden status")
    if not recipe["visual_analysis"].get("pixels_inspected"):
        raise ValueError("image pixels were not inspected")
    if source is not None and (not source.is_file() or sha256(source) != identity["source_sha256"]):
        raise ValueError("source image missing or SHA mismatch")
    names, materials = set(), set()
    for material in recipe["materials"]:
        name = material["name"]
        if name in materials or material["class"] not in MATERIAL_CLASSES:
            raise ValueError("duplicate/unknown material")
        materials.add(name)
        vector(material["rgba"], "rgba", 4, 0, 1)
        for key in ("metallic", "roughness", "wear"):
            finite(material[key], key, 0, 1)
    for c in recipe["components"]:
        op, g, name = c["op"], c["geometry"], c["name"]
        if name in names or op not in OPS or c["material"] not in materials:
            raise ValueError("duplicate component/unknown operator or material")
        names.add(name)
        vector(c["location"], "location", 3)
        vector(c["rotation_deg"], "rotation", 3, -3600, 3600)
        if set(g) - GEOM_KEYS[op]:
            raise ValueError("unknown operator arguments")
        if op in ("box", "boolean_cut"):
            vector(g["size"], "box.size", 3, 0.0001, 10)
        if op == "boolean_cut" and (g["target"] == name or not isinstance(g["target"], str)):
            raise ValueError("bad boolean target")
        if op == "cylinder":
            finite(g["radius"], "radius", 0.001, 10)
            finite(g["depth"], "depth", 0.001, 10)
        if op == "tube":
            vector(g["points"][0], "tube.points", 3)
            if not 2 <= len(g["points"]) <= 200:
                raise ValueError("tube has invalid point count")
            for point in g["points"]: vector(point, "tube.point", 3)
            finite(g["radius"], "tube.radius", 0.001, 2)
        if op == "lathe":
            if not 3 <= len(g["profile"]) <= 64: raise ValueError("lathe profile length")
            for pair in g["profile"]: vector(pair, "lathe.rz", 2, 0, 10)
        if op == "polygon_extrude":
            if not 3 <= len(g["points"]) <= 80: raise ValueError("polygon size")
            for point in g["points"]: vector(point, "polygon.point", 2)
            finite(g["depth"], "polygon.depth", 0.001, 10)
        if op == "text":
            if not isinstance(g["value"], str) or len(g["value"]) > 64 or any(ord(ch) < 32 for ch in g["value"]):
                raise ValueError("untrusted text")
            finite(g["size"], "text.size", .001, 2)
        if "vertices" in g and (type(g["vertices"]) is not int or not 12 <= g["vertices"] <= 96):
            raise ValueError("invalid geometry resolution")
        if "scale_xy" in g: vector(g["scale_xy"], "scale_xy", 2, .1, 3)
        if "bevel" in g: finite(g["bevel"], "bevel", 0, .25)
        if "extrude" in g: finite(g["extrude"], "extrude", 0, .04)
    for c in recipe["components"]:
        if c["parent"] is not None and c["parent"] not in names: raise ValueError("missing parent")
        if c["op"] == "boolean_cut" and c["geometry"]["target"] not in names: raise ValueError("unknown boolean target")
        chain, p = set(), c
        while p["parent"]:
            if p["name"] in chain: raise ValueError("parent cycle")
            chain.add(p["name"])
            p = next(x for x in recipe["components"] if x["name"] == p["parent"])
    landmark_names = set()
    for landmark in recipe["visual_analysis"].get("landmarks", []):
        name = landmark["component"]
        if name in landmark_names or name not in names:
            raise ValueError("landmark must name one unique existing component")
        part = next(c for c in recipe["components"] if c["name"] == name)
        if part["op"] == "boolean_cut" or not part["observed"]:
            raise ValueError("landmark must refer to visible, non-cutter geometry")
        landmark_names.add(name)
        vector(landmark["xy"], "landmark.xy", 2, 0, 1)
        finite(landmark["confidence"], "landmark.confidence", .5, 1)
    vector(recipe["render"]["assembly_scale"], "assembly_scale", 3, .5, 1.5)
    return recipe


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("recipe", type=Path)
    p.add_argument("--source", type=Path)
    a = p.parse_args()
    document = json.loads(a.recipe.read_text())
    validate(document, a.source, full_schema=True)
    print("LL_RECIPE_SCHEMA_AND_ALLOWLIST_PASS", document["identity"]["candidate_id"])
