#!/usr/bin/env python3
"""Evidence-based source intake. Research pixels stay outside the game/repository.

build never infers identity from a filename, a style example, or a similar hash.
fetch caches private research only; successful retrieval never approves a record.
"""
import argparse
import concurrent.futures
import hashlib
import io
import json
import os
import re
import tempfile
import textwrap
import urllib.request
from collections import Counter
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "production/source_identity"
CATALOG = ROOT / "production/sprite_factory/catalog.json"
DISPOSITIONS = {
    "new_original_logical_item", "variant_of_existing_item", "state_of_existing_item",
    "duplicate_reference", "unsupported_or_irrelevant", "deferred_world_or_animation_asset",
    "requires_human_classification",
}
ELIGIBLE = {"new_original_logical_item", "variant_of_existing_item", "state_of_existing_item"}


def digest(value):
    return hashlib.sha256(value).hexdigest()


def atomic(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".identity-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_json(path, value):
    atomic(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def inventory(path=CATALOG):
    data = read_json(path)
    rows = data["rows"]
    if len(rows) != data["reference_count"]:
        raise ValueError("Catalog accounting mismatch")
    for key in ("reference_id", "catalog_index"):
        if len({r[key] for r in rows}) != len(rows):
            raise ValueError("Duplicate source " + key)
    if sorted(r["catalog_index"] for r in rows) != list(range(1, len(rows) + 1)):
        raise ValueError("Catalog indices missing or out of range")
    return sorted(rows, key=lambda r: r["catalog_index"])


def validate_review(review, source, evidence):
    if review["reference_id"] != source["reference_id"]:
        raise ValueError("Review/source ID mismatch")
    if review.get("disposition") not in DISPOSITIONS:
        raise ValueError("Invalid disposition")
    if review.get("status") not in {"identity_verified", "observed_needs_context", "blocked_conflict"}:
        raise ValueError("Invalid classification status")
    image = evidence.get("image", {})
    if (image.get("fetch_status") != "retrieved" or image.get("source_image_url") != source["source_image_url"]
            or not re.fullmatch("[0-9a-f]{64}", image.get("sha256", ""))):
        raise ValueError("Missing exact source-image evidence: " + source["reference_id"])
    if review.get("inspected_image_sha256") != image["sha256"]:
        raise ValueError("Inspected source pixels changed; re-review required")
    if review.get("reviewer_kind") != "assistant_visual_judgment" or not review.get("visual_observation"):
        raise ValueError("An actual attributed visual observation is required")
    if not review.get("reason"):
        raise ValueError("Explicit disposition reason required")
    if review["status"] != "identity_verified":
        if review["disposition"] != "requires_human_classification":
            raise ValueError("Unresolved records cannot receive a final disposition")
        return
    context = evidence.get("context", {})
    if (context.get("fetch_status") != "retrieved" or not context.get("context_url")
            or review.get("inspected_context_sha256") != context.get("context_sha256")
            or not re.fullmatch("[0-9a-f]{64}", context.get("context_sha256", ""))):
        raise ValueError("Missing inspected source context")
    for key in ("context_interpretation", "identity_key", "physical_description", "category", "family", "view", "state"):
        if not review.get(key):
            raise ValueError("Missing reviewed semantic field: " + key)
    if review["disposition"] == "requires_human_classification":
        raise ValueError("Verified status cannot hide an unresolved disposition")
    if review["disposition"] in ELIGIBLE and not re.fullmatch(r"[a-z0-9_]+(?:\.[a-z0-9_]+)*", review.get("logical_item_id", "")):
        raise ValueError("Eligible logical item needs a stable ID")
    if review["disposition"] in {"variant_of_existing_item", "state_of_existing_item", "duplicate_reference"}:
        if not review.get("related_reference_id") or not review.get("relationship_evidence"):
            raise ValueError("Relationships require an explicit reviewed target and evidence")


def build(catalog=CATALOG, home=HOME):
    home = Path(home)
    sources = inventory(catalog)
    reviews = read_json(home / "reviews.json")
    evidence = read_json(home / "evidence.json")
    by_id = {r["reference_id"]: r for r in sources}
    if len({r["reference_id"] for r in reviews}) != len(reviews):
        raise ValueError("Duplicate review ID")
    if any(r["reference_id"] not in by_id for r in reviews) or any(k not in by_id for k in evidence):
        raise ValueError("Unknown source ID in review/evidence")
    reviewed = {r["reference_id"]: r for r in reviews}
    result = []
    for source in sources:
        ref = source["reference_id"]
        row = dict(source)
        # The official Notion intake is authoritative and immutable. All fields
        # below are a separate LAST LIGHT mapping, never a renamed source record.
        row["authoritative_source_record"] = source.copy()
        row["source_authority"] = "Notion official-source archive; exact original record retained"
        row["mapping_scope"] = "proposed_LAST_LIGHT_identity; does_not_replace_official_names_or_information"
        # Preserve legacy semantic proposals/approvals without treating them as pixel inspection.
        row["legacy_semantic_review"] = {k: source.get(k) for k in (
            "logical_item_id", "category", "family", "physical_description", "materials", "states",
            "gameplay_purpose", "priority", "disposition", "reason", "reviewed")}
        row.update({"classification_status": "unverified", "disposition": "requires_human_classification",
            "reason": "Source image and context have not been reviewed together.",
            "identity_key": None, "logical_item_id": None, "category": None, "family": None,
            "physical_description": None, "materials": [], "states": [], "reviewed": False,
            "gameplay_purpose": None, "production_eligible": False, "identity_review": None,
            "evidence": evidence.get(ref, {}), "style_reference_ids": []})
        if ref in reviewed:
            review = reviewed[ref]
            validate_review(review, source, row["evidence"])
            target = review.get("related_reference_id")
            if target:
                if target == ref or target not in reviewed or reviewed[target]["status"] != "identity_verified":
                    raise ValueError("Relationship must point to a separately verified source")
                if reviewed[target].get("related_reference_id"):
                    raise ValueError("Flatten relationships to a primary source; cycles/chains are not accepted")
                if review.get("logical_item_id") != reviewed[target].get("logical_item_id"):
                    raise ValueError("Related references must explicitly agree on logical identity")
            row.update({k: review[k] for k in ("disposition", "reason", "identity_key", "logical_item_id",
                "category", "family", "physical_description", "materials", "gameplay_purpose") if k in review})
            row.update({"classification_status": review["status"], "reviewed": True,
                "identity_review": review, "states": [review["state"]] if review.get("state") else [],
                "production_eligible": review["status"] == "identity_verified" and review["disposition"] in ELIGIBLE})
        result.append(row)
    verified = [r for r in result if r["classification_status"] == "identity_verified"]
    remaining = [r for r in result if r["classification_status"] != "identity_verified"]
    counts = dict(Counter(r["classification_status"] for r in result))
    counts.update({"total_reference_records": len(result), "accounted_reference_records": len(result),
        "images_retrieved": sum(r["evidence"].get("image", {}).get("fetch_status") == "retrieved" for r in result),
        "images_actually_inspected": len(reviews), "identity_verified": len(verified),
        "remaining_identity_reviews": len(remaining), "eligible_source_records": sum(r["production_eligible"] for r in result),
        "verified_unique_logical_items": len({r["logical_item_id"] for r in verified if r["production_eligible"]}),
        "dispositions": dict(Counter(r["disposition"] for r in result)),
        "new_sprites_generated": 0, "catalog_sprite_approvals": 0})
    ledger_text = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in result)
    atomic(home / "ledger.jsonl", ledger_text)
    receipts = {r["reference_id"]: {
        "reference_id": r["reference_id"], "catalog_index": r["catalog_index"],
        "status": "identity_verified", "identity_key": r["identity_key"],
        "logical_item_id": r["logical_item_id"], "disposition": r["disposition"],
        "view": r["identity_review"]["view"], "state": r["identity_review"]["state"],
        "image_sha256": r["evidence"]["image"]["sha256"],
        "context_sha256": r["evidence"]["context"]["context_sha256"],
        "reviewer_kind": r["identity_review"]["reviewer_kind"],
        "review_id": "LL-IDENTITY-%04d" % r["catalog_index"],
        "production_eligible": r["production_eligible"],
    } for r in verified}
    gate = {"schema": "ll_source_identity_gate_v1", "catalog_sha256": digest(Path(catalog).read_bytes()),
        "ledger_sha256": digest(ledger_text.encode()), "total_reference_records": len(result),
        "resolved_reference_records": len(verified), "catalog_review_complete": not remaining,
        "production_enabled": not remaining, "receipts": receipts,
        "reason": "Founder requested mass catalog classification before further production. Style approval is retained separately."}
    write_json(home / "production_gate.json", gate)
    write_json(home / "dashboard.json", counts)
    write_json(home / "next_review_batch.json", {"batch_id": "LL-IDENTITY-B0002", "records": [
        {k: r[k] for k in ("catalog_index", "reference_id", "source_filename", "source_page_url", "source_image_url", "classification_status")}
        for r in remaining[:20]]})
    print(json.dumps(counts, indent=2))
    return result, gate


def fetch(catalog, cache, indices, workers):
    """Resumable research cache; never copies source pixels to production paths."""
    from PIL import Image
    cache = Path(cache).expanduser().resolve()
    if cache == ROOT or ROOT in cache.parents:
        raise ValueError("Research image cache must be outside the game repository")
    if not 1 <= workers <= 8:
        raise ValueError("Use 1–8 workers")
    cache.mkdir(parents=True, exist_ok=True)
    rows = [r for r in inventory(catalog) if r["catalog_index"] in indices]
    def job(row):
        path = cache / (str(row["catalog_index"]) + ".png")
        meta = {k: row[k] for k in ("reference_id", "catalog_index", "source_image_url", "source_page_url")}
        try:
            prior = cache / (str(row["catalog_index"]) + ".json")
            meta_before = read_json(prior) if prior.exists() else {}
            content = path.read_bytes() if path.exists() else None
            if content and (meta_before.get("source_image_url") != row["source_image_url"]
                    or meta_before.get("sha256") != digest(content)):
                content = None
            if content:
                try:
                    with Image.open(io.BytesIO(content)) as im:
                        im.load()
                except Exception:
                    content = None
            if content is None:
                url = quote(row["source_image_url"], safe=":/_%")
                request = urllib.request.Request(url, headers={"User-Agent": "LAST LIGHT source identity research"})
                with urllib.request.urlopen(request, timeout=35) as response:
                    content = response.read(8 * 1024 * 1024 + 1)
                if len(content) > 8 * 1024 * 1024:
                    raise ValueError("Research image exceeds 8 MiB limit")
                with Image.open(io.BytesIO(content)) as im:
                    im.load()
                fd, temp = tempfile.mkstemp(dir=cache)
                try:
                    with os.fdopen(fd, "wb") as stream:
                        stream.write(content)
                    os.replace(temp, path)
                finally:
                    if os.path.exists(temp):
                        os.unlink(temp)
            with Image.open(io.BytesIO(content)) as im:
                meta.update({"sha256": digest(content), "size": list(im.size), "fetch_status": "retrieved"})
        except Exception as error:
            meta.update({"fetch_status": "error", "error": str(error)})
        write_json(cache / (str(row["catalog_index"]) + ".json"), meta)
        return meta
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        result = list(pool.map(job, rows))
    write_json(cache / "fetch_evidence.json", result)
    print(json.dumps({"fetched": sum(r["fetch_status"] == "retrieved" for r in result), "requested": len(rows)}))
    return result


def sheet(catalog, cache, start, count):
    from PIL import Image, ImageDraw
    cache = Path(cache).expanduser().resolve()
    if cache == ROOT or ROOT in cache.parents:
        raise ValueError("Source review sheets must stay outside the game repository")
    if not 1 <= count <= 20:
        raise ValueError("Review at most 20 source records per board")
    rows = [r for r in inventory(catalog) if start <= r["catalog_index"] < start + count]
    board = Image.new("RGB", (1200, 4 * 210 + 42), (43, 49, 53))
    draw = ImageDraw.Draw(board)
    draw.text((8, 8), "SOURCE IDENTITY RESEARCH / NOT GAME ART / OBSERVE IMAGE + READ FILE USAGE + ARTICLE", fill="white")
    for i, row in enumerate(rows):
        x, y = i % 5 * 240, 42 + i // 5 * 210
        path = cache / (str(row["catalog_index"]) + ".png")
        if path.exists():
            with Image.open(path) as im:
                im = im.convert("RGBA")
                im.thumbnail((128, 128), Image.Resampling.NEAREST)
                # Native source pixels and enlarged nearest display, never art input.
                scale = max(1, min(128 // im.width, 128 // im.height))
                im = im.resize((im.width * scale, im.height * scale), Image.Resampling.NEAREST)
                board.paste(im, (x + (240 - im.width) // 2, y), im)
        else:
            draw.text((x + 8, y + 40), "MISSING SOURCE IMAGE", fill=(255, 170, 140))
        text = "%04d %s" % (row["catalog_index"], row["source_filename"])
        draw.multiline_text((x + 6, y + 132), "\n".join(textwrap.wrap(text, 32)[:2]), fill="white")
        draw.text((x + 6, y + 166), row["reference_id"], fill=(190, 199, 192))
    destination = cache / ("review_%04d_%04d.png" % (start, start + count - 1))
    board.save(destination)
    write_json(destination.with_suffix(".json"), [{k: r[k] for k in ("catalog_index", "reference_id", "source_filename", "source_page_url", "source_image_url")} for r in rows])
    print(str(destination))
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["build", "fetch", "sheet"])
    parser.add_argument("--catalog", type=Path, default=CATALOG)
    parser.add_argument("--home", type=Path, default=HOME)
    parser.add_argument("--cache", type=Path)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.command == "build":
        build(args.catalog, args.home)
    else:
        if not args.cache:
            parser.error("--cache outside the repository is required")
        if args.start < 1 or args.count < 1:
            parser.error("Positive --start/--count required")
        if args.command == "fetch":
            fetch(args.catalog, args.cache, set(range(args.start, args.start + args.count)), args.workers)
        else:
            sheet(args.catalog, args.cache, args.start, args.count)


if __name__ == "__main__":
    main()
