#!/usr/bin/env python3
"""LAST LIGHT — Unified Reproducible Factory, executable foundation V1.

Runs locally on iPhone Python/CodePad or desktop, without a paid API.
Python standard library required; Pillow optional for actual PNG creation.

ONE-FILE RUN SETTINGS: Change ACTION near the top and press Run in CodePad.
  neighborhood: generates 3 original houses + street as a standalone Godot debug project
  sync_catalog: syncs GitHub Notion reference metadata (23 batches) via HTTPS
  demo   : sample original recipes, 3x3 chunk world, textures/icons, QA, ZIP
  import : import supplied approved/reference JSON, JSONL or CSV into catalog DB
  audit  : coverage and unresolved-work reports
  batch  : next original-approved icon recipes (does not repaint source art)
  world  : generate an arbitrary chunk rectangle from a deterministic world seed
  verify : validate world-output manifests and generated content
  export : zip generated candidates/metadata

This is an OPEN, REPRODUCIBLE FRAMEWORK, not a general AI painter. Original
object families not yet implemented remain pending_renderer, never falsely passed.
Neither PZwiki reference images nor proprietary artwork are copied into outputs.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
import sqlite3
import sys
import tempfile
import time
import zipfile
from collections import Counter, deque
from typing import Any

# ========================== CODEPAD RUN BUTTON =============================
ACTION = "neighborhood"            # neighborhood | sync_catalog | demo | import | audit | batch | world | verify | export
ROOT_FOLDER = ""                  # Optional writable full directory; empty = auto-discover
WORLD_SEED = 20261106
WORLD_ORIGIN_CHUNK = (0, 0)         # Can be negative. Change for other regions.
WORLD_CHUNK_GRID = (3, 3)          # e.g., (12, 12) for 144 chunks; no world-size limit
BATCH_SIZE = 200                   # For approved original icon recipes
GENERATE_PREVIEWS = True           # Pillow optional
GENERATE_TEXTURES = True
EXPORT_ZIP = True
# ===========================================================================

VERSION = "ll-ucf-master-2.0"
WORLD_SCHEMA = "last_light.world_chunks.v1"
CATALOG_SCHEMA = "last_light.reference_catalog.v1"
CHUNK_SIZE = 48                    # world tiles per chunk (prototype; profile on phone)
TILE_PX = (80, 40)                  # isometric 2:1 ground diamond contract
ICON_PX = 64
RECIPE_KINDS = {"item", "tile", "building", "vehicle", "animal", "animation", "texture", "prop"}
SUPPORTED_ICONS = {"can", "bottle", "bandage", "hammer", "axe", "flashlight", "backpack", "crate", "medkit"}
ART_MATERIALS = {
    "steel": {"highlight":"abb5b3","base":"666f70","shadow":"394144","outline":"272b2c"},
    "wood": {"highlight":"bc956c","base":"85603f","shadow":"513a2a","outline":"332b24"},
    "glass": {"highlight":"d4e0da","base":"80a3ad","shadow":"4c717d","outline":"354c54"},
    "fabric": {"highlight":"a2a88a","base":"667057","shadow":"3d4838","outline":"292f28"},
    "cardboard": {"highlight":"c6ae86","base":"9e7d53","shadow":"6e5439","outline":"40372c"},
    "plastic": {"highlight":"b6b9aa","base":"777f77","shadow":"474e49","outline":"303532"},
    "leather": {"highlight":"b78962","base":"79523c","shadow":"50392e","outline":"332d28"},
    "rock": {"highlight":"b5aea2","base":"89847c","shadow":"575a57","outline":"383b3a"},
}

# Notion/PZwiki category-size audit targets, not unique asset counts. Some sets
# overlap, and deeper nested gallery counts are publisher/API memberships only.
REFERENCE_SET_TARGETS = {
    "pzwiki_item_icons": {"count": 4347, "basis": "2026-11-05 archived file listing, 23 Notion shards"},
    "pzwiki_vehicle_models": {"count": 251, "basis": "reported direct category memberships"},
    "pzwiki_vehicle_screenshots": {"count": 61, "basis": "reported direct category memberships"},
    "pzwiki_animated_images": {"count": 92, "basis": "reported direct category memberships"},
    "pzwiki_animal_images": {"count": 32, "basis": "reported direct category memberships"},
    "pzwiki_tile_images": {"count": 514, "basis": "reported direct category memberships"},
    "pzwiki_furniture_tiles": {"count": 443, "basis": "reported child category memberships"},
    "pzwiki_vegetation_tiles": {"count": 2178, "basis": "reported child category memberships"},
    "pzwiki_floor_tiles": {"count": 201, "basis": "reported child category memberships"},
    "pzwiki_appliance_tiles": {"count": 158, "basis": "reported child category memberships"},
    "pzwiki_animated_tiles": {"count": 53, "basis": "reported child category memberships"},
}

TERRAIN_MATERIALS = ["grass_sparse", "asphalt_worn", "dirt", "forest_floor", "gravel", "water", "farmland", "concrete_stained", "rock", "dry_grass"]
PALETTE = {
    "grass_sparse": (73, 98, 70), "asphalt_worn": (63, 67, 68),
    "dirt": (117, 94, 69), "forest_floor": (53, 76, 53),
    "gravel": (115, 112, 101), "water": (54, 106, 121),
    "farmland": (117, 105, 72), "concrete_stained": (122, 125, 113),
    "rock": (115, 116, 110), "dry_grass": (136, 132, 88),
    "bridge": (99, 102, 94), "highway": (61, 65, 69),
    "street": (77, 80, 79), "path": (146, 139, 120),
}
SAMPLE_ITEMS = [
    ("can", "Canned beans", "original food tin with cylindrical metal body, rolled rim and paper label", "food"),
    ("bottle", "Water bottle", "original clear plastic bottle with a molded cap", "food"),
    ("bandage", "Sterile bandage", "sealed cloth medical dressing package", "medical"),
    ("hammer", "Claw hammer", "forged steel hammer head and shaped wooden handle", "tools"),
    ("axe", "Wood axe", "forged steel edge and wooden handle", "tools"),
    ("flashlight", "Pocket flashlight", "black flashlight with head, body and switch", "electronics"),
    ("backpack", "Day backpack", "olive fabric backpack with straps and pocket", "clothing"),
    ("crate", "Supply crate", "wooden shipping crate with plank joins", "containers"),
    ("medkit", "Medical kit", "compact red hard-sided first-aid case with handle", "medical"),
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(data: Any) -> bytes:
    return (json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf8")


def pretty(data: Any) -> bytes:
    return (json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf8")


def seed_for(world_seed: int, *parts: Any) -> int:
    # A child only depends on its own stable identity. New neighbors do not reroll it.
    value = canonical([VERSION, world_seed, *parts])
    return int.from_bytes(hashlib.sha256(value).digest()[:8], "big")


def stable01(world_seed: int, *parts: Any) -> float:
    return seed_for(world_seed, *parts) / ((1 << 64) - 1)


def write_atomic(path: Path, content: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    with temp.open("wb") as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp, path)
    return sha256(content)


def writable_root(explicit: str = "") -> Path:
    candidates = ([Path(explicit)] if explicit else []) + [
        Path.home() / "Documents" / "LAST_LIGHT_FACTORY",
        Path.cwd() / "LAST_LIGHT_FACTORY",
        Path(__file__).resolve().parent / "LAST_LIGHT_FACTORY",
        Path(tempfile.gettempdir()) / "LAST_LIGHT_FACTORY_TEMP",
    ]
    errors = []
    for path in candidates:
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe = path / "__writable_probe__"
            probe.write_text("yes", encoding="utf-8")
            probe.unlink()
            return path
        except (OSError, PermissionError) as exc:
            errors.append(f"{path}: {exc}")
    raise OSError("No writable path; " + "; ".join(errors))


def optional_pillow():
    try:
        from PIL import Image, ImageDraw
        return Image, ImageDraw
    except ImportError:
        return None, None


def valid_id(item: Any) -> bool:
    return isinstance(item, str) and bool(re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._:/-]{1,160}", item))


class Catalog:
    """Persistent reference and *original-design* recipe registry; safe to rerun."""
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path), timeout=25)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA busy_timeout=15000")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS sources (
                id TEXT PRIMARY KEY, title TEXT NOT NULL, kind TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT '', description TEXT NOT NULL DEFAULT '',
                image_url TEXT NOT NULL DEFAULT '', source_url TEXT NOT NULL DEFAULT '',
                provenance TEXT NOT NULL DEFAULT 'external_reference',
                rights TEXT NOT NULL DEFAULT 'unknown', approved INTEGER NOT NULL DEFAULT 0,
                archetype TEXT NOT NULL DEFAULT '', status TEXT NOT NULL,
                metadata_json TEXT NOT NULL, fingerprint TEXT NOT NULL,
                authoritative_source_json TEXT NOT NULL DEFAULT '{}'
            );
            CREATE TABLE IF NOT EXISTS outputs (
                id TEXT PRIMARY KEY, source_id TEXT NOT NULL, role TEXT NOT NULL,
                generator_version TEXT NOT NULL, recipe_fingerprint TEXT NOT NULL,
                path TEXT NOT NULL, sha256 TEXT NOT NULL,
                status TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
                error TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS classifications (
                source_id TEXT PRIMARY KEY, source_index INTEGER NOT NULL,
                original_filename TEXT NOT NULL, proposed_category TEXT NOT NULL,
                family_candidate TEXT NOT NULL, variant_clues TEXT NOT NULL,
                confidence TEXT NOT NULL, notion_page TEXT NOT NULL,
                review_state TEXT NOT NULL DEFAULT 'keyword_provisional',
                metadata_json TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_source_status ON sources(status);
            CREATE INDEX IF NOT EXISTS idx_outputs_source ON outputs(source_id);
        """)
        # Older local databases can be opened without losing any saved work.
        cols={row[1] for row in self.db.execute("PRAGMA table_info(sources)")}
        if "authoritative_source_json" not in cols:
            self.db.execute("ALTER TABLE sources ADD COLUMN authoritative_source_json TEXT NOT NULL DEFAULT '{}'")
        self.db.commit()

    @staticmethod
    def normalize(row: dict) -> dict:
        # Catalog readiness exports may wrap the archived source record.
        raw=dict(row)
        nested=row.get("authoritative_source_record")
        if isinstance(nested,dict):
            row={**nested,**{k:v for k,v in row.items() if k!="authoritative_source_record"}}
        def get(*keys: str) -> str:
            for key in keys:
                val = row.get(key)
                if val is not None and str(val).strip():
                    return str(val).strip()
            return ""
        rid = get("id", "source_id", "item_id", "file_id", "reference_id")
        if not rid and get("index").isdigit() and get("source_filename", "reference_file"):
            rid = f"pzwiki.icon.{int(get('index')):06d}"
        if not rid and get("reference_file"):
            index=get("source_index", "index", "catalog_index", "#")
            if index.isdigit(): rid=f"pzwiki.icon.{int(index):06d}"
            else: rid="ref."+hashlib.sha256(get("reference_source_url", "reference_file").encode("utf8")).hexdigest()[:20]
        if not rid:
            raise ValueError("source record missing stable ID (id/source_id/item_id)")
        if not valid_id(rid):
            raise ValueError(f"source ID contains unsupported characters: {rid[:80]}")
        kind = get("kind", "type", "asset_kind") or "item"
        approved = row.get("approved_original_recipe", False)
        approved = (approved is True) or (str(approved).lower() in {"true", "1", "yes"})
        art_recipe = row.get("art_recipe")
        if not isinstance(art_recipe,dict):art_recipe=None
        return {
            "id": rid, "title": get("title", "name", "item_name", "source_filename", "reference_file") or rid,
            "kind": kind, "category": get("category", "family", "object_family", "proposed_category"),
            "description": get("description", "physical_description", "art_description"),
            "image_url": get("reference_image", "reference_image_url", "image_url", "source_image_url", "original_image"),
            "source_url": get("source_url", "source_file_page", "reference_source_url", "url", "wiki_url"),
            "provenance": get("provenance", "source_type") or "external_reference",
            "rights": get("rights", "asset_rights", "license") or "unknown",
            "approved": approved,
            "archetype": get("archetype", "original_art_recipe", "shape_family"),
            "art_recipe":art_recipe,
            "source_index": get("source_index", "index", "catalog_index", "#"),
            "source_dimensions": get("source_dimensions", "reported_dimensions"),
            "identity_status": get("identity_status", "confidence", "visual_spec_status"),
            "source_collection": get("source_collection", "reference_collection", "source_category") or (
                "pzwiki_item_icons" if rid.startswith("pzwiki.icon.") else "original_demo" if rid.startswith("ll.demo.") else "unspecified"),
        }

    @staticmethod
    def readiness(r: dict) -> str:
        if r["kind"] not in RECIPE_KINDS:
            return "needs_classification"
        if r["provenance"] != "original_internal" or not r["approved"]:
            return ("reference_only_needs_description_and_original_recipe" if not r["description"]
                    else "reference_only_needs_original_recipe")
        if not r["description"]:
            return "needs_description"
        if r["kind"] == "item" and r["archetype"] not in SUPPORTED_ICONS and not r.get("art_recipe"):
            return "pending_renderer"
        if r["kind"] != "item":
            return "pending_specialized_factory"
        return "ready_for_generation"

    def upsert(self, row: dict) -> str:
        record = self.normalize(row)
        state = self.readiness(record)
        fingerprint = sha256(canonical(record))
        previous = self.db.execute("SELECT fingerprint FROM sources WHERE id=?", (record["id"],)).fetchone()
        if previous and previous[0] != fingerprint:
            # Changes must be explicit, not silently overwrite source identity.
            raise ValueError("Conflicting source ID: " + record["id"] + "; use a new versioned ID")
        self.db.execute("""INSERT OR IGNORE INTO sources
            (id,title,kind,category,description,image_url,source_url,provenance,
             rights,approved,archetype,status,metadata_json,fingerprint,authoritative_source_json)
             VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
            record["id"],record["title"],record["kind"],record["category"],
            record["description"],record["image_url"],record["source_url"],
            record["provenance"],record["rights"],int(record["approved"]),
            record["archetype"],state,json.dumps(record,sort_keys=True),fingerprint,
            json.dumps(row,sort_keys=True,ensure_ascii=False)))
        return state

    @staticmethod
    def parse_reference_markdown(markdown:str)->list[dict]:
        """Parse existing 23 Notion PZwiki icon catalog Markdown exports.

        Reference rows preserve original file name, URL and reported dimensions;
        no generated art, visual identification or legal rights are implied.
        """
        records=[];inside=False
        for line in markdown.splitlines():
            if (line.startswith("| # | Reference filename | Reference image | Source file page |")
                    or line.startswith("| # | Reference filename | Image URL | Wiki file page |")):
                inside=True;continue
            if not inside or not line.startswith("|"):continue
            parts=[cell.strip() for cell in re.split(r"(?<!\\)\|",line.strip().strip("|"))]
            if len(parts)<5 or not parts[0].isdigit():continue
            index=int(parts[0]);file=parts[1]
            image_match=re.search(r"\[Image\]\((https?://[^)]+)\)",parts[2])
            source_match=re.search(r"\[Source\]\((https?://[^)]+)\)",parts[3])
            records.append({"id":f"pzwiki.icon.{index:06d}","source_index":index,
                    "reference_file":file,"name":file,
                    "reference_image_url":image_match.group(1) if image_match else "",
                    "reference_source_url":source_match.group(1) if source_match else "",
                    "reported_dimensions":parts[4],"kind":"item","category":"unclassified",
                    "provenance":"external_reference","asset_rights":"third_party_reference_only",
                    "description":"", "identity_status":"source_listing_only",
                    "source_collection":"pzwiki_item_icons"})
        return records

    def _ingest_iterator(self, items, filename: str) -> tuple[int,int,list[str]]:
        ok=0;total=0;errors=[]
        for index,row in enumerate(items,1):
            total=index
            try:
                if not isinstance(row,dict): raise ValueError("record must be an object")
                if "__parse_error__" in row:raise ValueError(row["__parse_error__"])
                self.upsert(row);ok+=1
            except (ValueError,TypeError,sqlite3.DatabaseError) as exc:
                if len(errors)<200:errors.append(f"{filename}:{index}: {exc}")
            if index%500==0:self.db.commit()  # interruption-safe import checkpoints
        self.db.commit()
        return ok,total,errors

    def import_file(self, path: Path) -> tuple[int,int,list[str]]:
        ext=path.suffix.lower()
        if ext==".jsonl":
            def safe_records(lines):
                for line_number,line in enumerate(lines,1):
                    if not line.strip():continue
                    try:yield json.loads(line)
                    except ValueError as exc:yield {"__parse_error__":f"JSONL source line {line_number}: {exc}"}
            with path.open(encoding="utf-8-sig") as f:
                return self._ingest_iterator(safe_records(f),path.name)
        if ext==".csv":
            with path.open(encoding="utf-8-sig",newline="") as f:
                return self._ingest_iterator(csv.DictReader(f),path.name)
        if ext==".md":
            return self._ingest_iterator(self.parse_reference_markdown(path.read_text(encoding="utf-8-sig")),path.name)
        if ext==".json":
            data=json.loads(path.read_text(encoding="utf-8-sig"))
            records=data if isinstance(data,list) else data.get("records",data.get("items",data.get("sources",[])))
            if not isinstance(records,list):raise ValueError("Expected records array in "+str(path))
            return self._ingest_iterator(records,path.name)
        return 0,0,[f"Unsupported catalog type: {path}"]

    def import_dir(self, directory: Path) -> dict:
        files = sorted(x for x in directory.rglob("*") if x.is_file() and x.suffix.lower() in (".csv", ".json", ".jsonl", ".md") and "notion_classification_batches" not in x.parts) if directory.exists() else []
        total=0;ok=0;errors=[]
        for path in files:
            a,b,e=self.import_file(path);ok+=a;total+=b;errors.extend(e)
        return {"files":len(files),"records_seen":total,"records_accepted":ok,"errors":errors[:200],"error_count":len(errors)}

    def import_classifications(self, directory: Path) -> dict:
        count=0; already=0; mismatches=[]; unmatched=[]; seen=set(); files=sorted(directory.glob("batch_*.jsonl")) if directory.exists() else []
        for file in files:
            with file.open(encoding="utf-8") as fp:
                for line_num,line in enumerate(fp,1):
                    if not line.strip():continue
                    try:
                        obj=json.loads(line);index=int(obj["index"])
                        rid=f"pzwiki.icon.{index:06d}"
                        if rid in seen:raise ValueError("Duplicate classification index")
                        seen.add(rid)
                        existing=self.db.execute("SELECT title FROM sources WHERE id=?",(rid,)).fetchone()
                        if not existing:
                            unmatched.append(index);continue
                        name=str(obj["source_filename"])
                        if existing[0]!=name:
                            mismatches.append({"index":index,"source_filename":existing[0],"classification_filename":name})
                        old=self.db.execute("SELECT metadata_json FROM classifications WHERE source_id=?",(rid,)).fetchone()
                        payload=json.dumps(obj,ensure_ascii=False,sort_keys=True)
                        if old and old[0]!=payload:raise ValueError("Conflicting immutable classifier snapshot")
                        if old: already+=1
                        else:
                            self.db.execute("INSERT INTO classifications(source_id,source_index,original_filename,proposed_category,family_candidate,variant_clues,confidence,notion_page,review_state,metadata_json) VALUES (?,?,?,?,?,?,?,?,?,?)",
                                (rid,index,name,str(obj.get("proposed_category","")),str(obj.get("family_candidate","")),str(obj.get("variant_clues","")),str(obj.get("classification_confidence","")),str(obj.get("notion_page","")),"keyword_provisional",payload))
                            count+=1
                    except (KeyError,ValueError,TypeError,json.JSONDecodeError) as exc:
                        unmatched.append(f"{file.name}:{line_num}: {exc}")
            self.db.commit()
        result={"files":len(files),"classifications_added":count,"classifications_already_present":already,
                "records_seen":len(seen),"filename_mismatches":mismatches[:200],
                "unmatched":unmatched[:200],"issue_count":len(mismatches)+len(unmatched)}
        return result

    def report(self) -> dict:
        state=Counter();categories=Counter();indexed=Counter()
        total=present_images=present_descriptions=unknown_rights=external=0
        for r in self.db.execute("SELECT status,kind,category,description,image_url,rights,provenance,metadata_json FROM sources"):
            total+=1;state[r[0]]+=1;categories[r[2] or r[1]]+=1
            present_images+=bool(r[4]);present_descriptions+=bool(r[3])
            unknown_rights+=r[5]=="unknown";external+=r[6]!="original_internal"
            indexed[json.loads(r[7]).get("source_collection","unspecified")]+=1
        output_state=Counter(r[0] for r in self.db.execute("SELECT status FROM outputs"))
        source_sets={key:{"indexed":indexed.get(key,0),"expected":spec["count"],
                          "coverage_percent":round(100*indexed.get(key,0)/spec["count"],2),
                          "complete":indexed.get(key,0)==spec["count"],
                          "basis":spec["basis"]}
                     for key,spec in REFERENCE_SET_TARGETS.items()}
        return {
            "catalog_schema":CATALOG_SCHEMA,"total_unique_records":total,
            "records_with_any_original_art_not_proven":True,
            "by_disposition":dict(sorted(state.items())),
            "by_category":dict(sorted(categories.items())),
            "image_references_present":present_images,
            "descriptions_present":present_descriptions,
            "unknown_source_rights":unknown_rights,
            "external_references":external,
            "by_generated_asset_status":dict(sorted(output_state.items())),
            "reference_source_sets":source_sets,
            "reference_counts_are_not_distinct_artwork":True,
            "all_sources_accounted_for":sum(state.values())==total,
            "coverage_note":"This count is imported records only, not the complete Notion/workshop/PZwiki universe. Technical output is not Golden 40 visual approval.",
        }

    def pending(self, limit:int) -> list[dict]:
        pending=[]
        for row in self.db.execute("""
            SELECT s.metadata_json,s.fingerprint,o.path,o.sha256,o.status,o.recipe_fingerprint,o.generator_version
            FROM sources s LEFT JOIN outputs o ON o.source_id=s.id AND o.role='icon'
            WHERE s.status='ready_for_generation' ORDER BY s.id"""):
            record=json.loads(row[0]);needs_render=True
            if row[4]=='technical_qa_passed' and row[5]==row[1] and row[6]==VERSION and row[2]:
                try:
                    file=Path(row[2]);needs_render=not (file.is_file() and sha256(file.read_bytes())==row[3])
                except OSError:needs_render=True
            if needs_render:pending.append(record)
            if len(pending)>=limit:break
        return pending

    def record_output(self, source:dict, output:Path, file_hash:str, role:str="icon", status:str="technical_qa_passed", error:str="") -> None:
        f=sha256(canonical(source))
        self.db.execute("""INSERT INTO outputs(id,source_id,role,generator_version,
           recipe_fingerprint,path,sha256,status,attempts,error)
           VALUES(?,?,?,?,?,?,?,?,1,?) ON CONFLICT(id) DO UPDATE SET
           recipe_fingerprint=excluded.recipe_fingerprint,path=excluded.path,
           sha256=excluded.sha256,status=excluded.status,
           attempts=outputs.attempts+1,error=excluded.error""",
           (source["id"]+"|"+role,source["id"],role,VERSION,f,str(output),file_hash,status,error))
        self.db.commit()

    def close(self): self.db.close()


def sample_original_catalog(path:Path) -> None:
    if path.exists(): return
    records=[]
    for family,name,desc,category in SAMPLE_ITEMS:
        records.append({"id":"ll.demo."+family,"name":name,"kind":"item", "category":category,
         "source_collection":"original_demo",
         "description":desc,"archetype":family,"provenance":"original_internal","rights":"original",
         "approved_original_recipe":True})
    records.append({"id":"ll.demo.compass","name":"Pocket compass","kind":"item",
      "category":"outdoor","source_collection":"original_demo",
      "description":"Original round metal compass case with a central cardinal pointer",
      "provenance":"original_internal","rights":"original",
      "approved_original_recipe":True,
      "art_recipe":{"canvas":[64,64],"layers":[
        {"op":"ellipse","box":[9,9,55,55],"material":"steel","shade":"shadow"},
        {"op":"ellipse","box":[14,14,50,50],"material":"steel","shade":"highlight"},
        {"op":"ellipse","box":[19,19,45,45],"material":"plastic","shade":"base"},
        {"op":"polygon","points":[[33,22],[27,39],[32,35],[37,39]],"material":"steel","shade":"highlight"},
        {"op":"line","points":[[32,18],[32,23]],"material":"steel","shade":"shadow","width":2}
      ]}})
    write_atomic(path,b"".join(canonical(rec) for rec in records))


# --------------------------- ORIGINAL PIXEL DRAWERS ----------------------
# These are review candidates; complex new objects must add their own original
# semantic renderer, not be processed by copying third-party source pixels.

def make_icon(archetype:str, seed:int, output:Path) -> str:
    Image, ImageDraw=optional_pillow()
    if Image is None: raise RuntimeError("Pillow required for PNG generation; install Pillow or skip images")
    if archetype not in SUPPORTED_ICONS: raise ValueError("No original geometry renderer for "+archetype)
    im=Image.new("RGBA",(ICON_PX,ICON_PX),(0,0,0,0)); d=ImageDraw.Draw(im)
    rng=random.Random(seed)
    outline=(36,35,32,255)
    steel=(95,103,102,255); steel_hi=(173,181,174,255); steel_shadow=(62,68,69,255)
    wood=(114,79,49,255); wood_hi=(155,116,75,255); cloth=(80,92,65,255)
    if archetype=="can":
        d.ellipse((17,9,46,19),fill=steel_shadow,outline=outline,width=2)
        d.rectangle((17,14,46,47),fill=(143,69,53),outline=outline,width=2)
        d.polygon([(19,15),(25,11),(25,44),(19,47)],fill=(178,104,78))
        d.rectangle((20,21,44,36),fill=(180,157,117),outline=(86,75,64))
        d.line((25,24,40,24),fill=(83,78,66),width=2)
        d.ellipse((17,43,46,51),fill=steel,outline=outline,width=2)
        d.arc((19,10,44,17),180,360,fill=steel_hi,width=2)
    elif archetype=="bottle":
        d.polygon([(25,8),(38,8),(38,20),(44,25),(44,49),(40,54),(23,54),(20,49),(20,25),(25,20)],fill=(116,165,174,140),outline=outline)
        d.rectangle((25,5,38,13),fill=(74,100,111),outline=outline)
        d.polygon([(23,30),(42,29),(42,43),(23,45)],fill=(170,180,158,255))
        d.line((26,25,26,47),fill=(208,226,219),width=2)
        d.line((30,9,35,9),fill=(161,190,188),width=2)
    elif archetype=="bandage":
        d.polygon([(11,23),(45,13),(55,34),(19,49)],fill=(186,183,169),outline=outline)
        d.polygon([(13,24),(45,16),(48,21),(16,30)],fill=(235,228,201))
        d.line((19,29,45,21),fill=(117,132,124),width=2)
        d.line((25,40,47,33),fill=(138,132,119),width=2)
        d.rectangle((32,25,37,32),fill=(135,79,72))
    elif archetype in ("hammer","axe"):
        d.line((17,52,43,17),fill=outline,width=10)
        d.line((17,52,43,17),fill=wood,width=7)
        d.line((20,47,41,18),fill=wood_hi,width=2)
        for k in range(3):d.line((17+k,48-k*3,21+k,45-k*3),fill=(66,52,44),width=1)
        if archetype=="hammer":
            d.polygon([(30,12),(46,10),(54,13),(55,21),(39,23),(33,20)],fill=steel,outline=outline)
            d.polygon([(32,12),(46,10),(48,13),(36,17)],fill=steel_hi)
            d.line((37,19,53,20),fill=steel_shadow,width=3)
        else:
            d.polygon([(31,9),(43,6),(55,9),(57,21),(49,28),(37,20)],fill=steel,outline=outline)
            d.polygon([(37,10),(50,8),(54,11),(43,14)],fill=steel_hi)
            d.line((56,11,53,22),fill=steel_hi,width=2)
    elif archetype=="flashlight":
        d.polygon([(13,36),(36,13),(47,21),(25,46)],fill=(58,66,61),outline=outline)
        d.polygon([(36,13),(46,6),(57,17),(47,24)],fill=steel,outline=outline)
        d.line((39,11,48,20),fill=steel_hi,width=3)
        d.ellipse((44,7,56,19),fill=(178,171,122),outline=outline,width=2)
        d.line((15,36,23,43),fill=(121,130,119),width=2)
    elif archetype=="backpack":
        d.rounded_rectangle((18,15,48,53),radius=7,fill=cloth,outline=outline,width=2)
        d.arc((23,5,44,24),170,360,fill=(124,110,83),width=4)
        d.polygon([(20,20),(46,20),(43,33),(23,33)],fill=(96,108,75),outline=outline)
        d.rounded_rectangle((23,36,44,49),radius=3,fill=(75,82,58),outline=outline)
        d.line((23,20,23,50),fill=(127,133,96),width=2)
        d.line((44,24,44,46),fill=(47,56,44),width=2)
        d.rectangle((30,32,35,37),fill=(168,151,100),outline=outline)
    elif archetype=="crate":
        d.polygon([(11,22),(33,12),(55,22),(33,34)],fill=(156,122,75),outline=outline)
        d.polygon([(11,22),(33,34),(33,53),(11,39)],fill=(104,73,47),outline=outline)
        d.polygon([(33,34),(55,22),(55,39),(33,53)],fill=(120,86,54),outline=outline)
        for i in (25,37):d.line((13,i,32,i+12),fill=(65,53,42),width=2)
        d.line((39,31,39,48),fill=(74,57,42),width=2)
        d.line((17,23,38,14),fill=(213,174,113),width=2)
    elif archetype=="medkit":
        d.rounded_rectangle((11,22,53,49),radius=5,fill=(147,55,52),outline=outline,width=2)
        d.polygon([(17,20),(43,20),(43,25),(17,25)],fill=(185,79,65),outline=outline)
        d.arc((26,12,40,28),180,360,fill=(65,63,55),width=4)
        d.rectangle((28,30,37,43),fill=(214,213,181))
        d.rectangle((24,35,41,39),fill=(214,213,181))
        d.line((14,27,49,27),fill=(205,106,84),width=2)
    # Tiny physically localized wear without uncontrolled whole-image noise.
    for _ in range(4):
        x=rng.randrange(20,44);y=rng.randrange(28,47)
        if im.getpixel((x,y))[3]>0:
            d.point((x,y),fill=(115,111,90,230))
    output.parent.mkdir(parents=True,exist_ok=True)
    tmp=output.with_suffix(".png.tmp")
    im.save(tmp,format="PNG",optimize=True)
    os.replace(tmp,output)
    return sha256(output.read_bytes())


def render_art_recipe(recipe:dict,seed:int,output:Path)->str:
    """Render original layered pixel geometry without writing new Python functions.

    Each layer supports polygon, rectangle, ellipse, rounded_rectangle and line;
    named material/shade values give consistent upper-left lighting palettes.
    This renderer is a drawing language, not an automatic semantic AI painter.
    """
    Image,ImageDraw=optional_pillow()
    if Image is None:raise RuntimeError("Pillow required for drawing recipe")
    layers=recipe.get("layers",[])
    if not isinstance(layers,list) or not 1<=len(layers)<=512:
        raise ValueError("Art recipe needs 1..512 layers")
    size=recipe.get("canvas",[64,64])
    if size!=[64,64]:raise ValueError("Only native 64x64 inventory canvases supported")
    im=Image.new("RGBA",(64,64),(0,0,0,0));d=ImageDraw.Draw(im)
    def point(v):
        if not isinstance(v,(list,tuple)) or len(v)!=2 or not all(isinstance(t,(int,float)) for t in v):
            raise ValueError("Expected numeric [x,y] point")
        if not all(-64<=t<=128 for t in v):raise ValueError("Point outside allowable margin")
        return tuple(int(round(t)) for t in v)
    def fill(layer):
        material=layer.get("material","steel")
        shade=layer.get("shade","base")
        if material not in ART_MATERIALS or shade not in ART_MATERIALS[material]:
            raise ValueError("Unknown material or shade")
        return "#"+ART_MATERIALS[material][shade]
    def outline(layer):
        return "#"+ART_MATERIALS[layer.get("material","steel")]["outline"]
    for layer in layers:
        if not isinstance(layer,dict):raise ValueError("Layer must be an object")
        op=layer.get("op");color=fill(layer)
        stroke=outline(layer) if layer.get("outline",True) else None
        width=int(layer.get("width",1))
        if not 0<=width<=12:raise ValueError("Stroke outside 0..12")
        if op in ("rectangle","ellipse","rounded_rectangle"):
            box=layer.get("box",[])
            if not isinstance(box,list) or len(box)!=4:raise ValueError("Shape requires box [x1,y1,x2,y2]")
            xy=point(box[:2])+point(box[2:])
            if op=="rectangle":d.rectangle(xy,fill=color,outline=stroke,width=max(1,width))
            elif op=="ellipse":d.ellipse(xy,fill=color,outline=stroke,width=max(1,width))
            else:d.rounded_rectangle(xy,radius=max(0,min(20,int(layer.get("radius",4)))),
                                     fill=color,outline=stroke,width=max(1,width))
        elif op=="polygon":
            pts=layer.get("points",[])
            if not isinstance(pts,list) or not 3<=len(pts)<=120:raise ValueError("Polygon has invalid points")
            xy=[point(t) for t in pts];d.polygon(xy,fill=color)
            if stroke:d.line(xy+[xy[0]],fill=stroke,width=max(1,width),joint="curve")
        elif op=="line":
            pts=layer.get("points",[])
            if not isinstance(pts,list) or not 2<=len(pts)<=120:raise ValueError("Line has invalid points")
            d.line([point(t) for t in pts],fill=color,width=max(1,width),joint="curve")
        else:raise ValueError("Unsupported drawing operation: "+str(op))
    if not im.getchannel("A").getbbox():raise ValueError("Empty art recipe")
    output.parent.mkdir(parents=True,exist_ok=True)
    tmp=output.with_suffix(".png.tmp")
    im.save(tmp,format="PNG",optimize=True);os.replace(tmp,output)
    return sha256(output.read_bytes())


def produce_original_icons(catalog:Catalog,root:Path,batch_size:int) -> dict:
    Image,_=optional_pillow()
    if Image is None:return {"generated":0,"error":"Pillow missing; catalog/geometry/manifest functions remain available"}
    todo=catalog.pending(batch_size);results=[];errors=[]
    for source in todo:
        path=root/"assets"/"original_candidates"/"icons"/(source["id"].replace(":","_").replace("/","_")+".png")
        try:
            if source.get("art_recipe"):
                hash_=render_art_recipe(source["art_recipe"],seed_for(0,source["id"],"art_recipe"),path)
            else:
                hash_=make_icon(source["archetype"],seed_for(0,source["id"],source["archetype"]),path)
            check=Image.open(path)
            check.load()
            if check.size!=(ICON_PX,ICON_PX) or check.mode!="RGBA" or not check.getchannel("A").getbbox():
                raise ValueError("PNG validation failed")
            catalog.record_output(source,path,hash_)
            results.append({"id":source["id"],"path":str(path.relative_to(root)),"sha256":hash_,
                            "status":"technical_qa_passed_visual_review_required"})
        except (ValueError,OSError,RuntimeError) as exc:
            errors.append({"id":source["id"],"error":str(exc)})
            catalog.record_output(source,path,"",status="technical_qa_failed",error=str(exc))
    write_atomic(root/"reports"/"last_icon_batch.json",pretty({"generated":len(results),"assets":results,"errors":errors,
           "note":"Basic original procedural candidates; none automatically Golden 40 approved."}))
    return {"generated":len(results),"failures":len(errors),"items":results,"errors":errors}


def generate_texture(material:str,seed:int,path:Path,size:int=64) -> str:
    Image, ImageDraw=optional_pillow()
    if Image is None:raise RuntimeError("Pillow required")
    if material not in TERRAIN_MATERIALS:raise ValueError("Unsupported material "+material)
    base=PALETTE[material]; rng=random.Random(seed)
    im=Image.new("RGBA",(size,size),base+(255,)); d=ImageDraw.Draw(im)
    # Tileable periodic marks; each opposite edge is matched explicitly.
    for _ in range(size*5):
        x=rng.randrange(size);y=rng.randrange(size)
        r=rng.randrange(-14,15)
        col=tuple(max(0,min(255,c+r)) for c in base)+(255,)
        d.point((x,y),fill=col)
    if material in ("farmland","asphalt_worn","concrete_stained"):
        for x in range(4,size,12 if material=="farmland" else 24):
            c=tuple(max(0,v-22) for v in base)+(255,)
            d.line((x,0,x,size-1),fill=c,width=1)
    if material=="water":
        for y in range(6,size,16):d.line((5,y,20,y),fill=(80,133,146,255),width=2)
    if material in ("grass_sparse","forest_floor","dry_grass"):
        for _ in range(22):
            x=rng.randrange(size);y=rng.randrange(size)
            d.line((x,y,x+1 if x<size-1 else x,y-2 if y>=2 else y),fill=tuple(max(0,min(255,c+28)) for c in base)+(255,))
    # Constant wraps make periodic-boundary equality machine-checkable.
    pix=im.load()
    for x in range(size): pix[x,size-1]=pix[x,0]
    for y in range(size): pix[size-1,y]=pix[0,y]
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+".tmp"); im.save(temp,format="PNG",optimize=True);os.replace(temp,path)
    return sha256(path.read_bytes())


# ----------------------- HIERARCHICAL WORLD COMPILER ----------------------
# All geography is fictional, original, deterministic and stable across chunk
# boundaries. This prototype does NOT ingest USGS/TIGER/OSM yet.

def smooth(a:float,b:float,v:float)->float:
    z=max(0.0,min(1.0,(v-a)/(b-a)))
    return z*z*(3-2*z)


def lattice(seed:int,x:int,y:int,tag:str)->float:
    return stable01(seed,tag,x,y)*2-1


def noise(seed:int,x:float,y:float,step:int,tag:str)->float:
    fx=x/step;fy=y/step;ix=math.floor(fx);iy=math.floor(fy)
    tx=smooth(0,1,fx-ix);ty=smooth(0,1,fy-iy)
    a=lattice(seed,ix,iy,tag);b=lattice(seed,ix+1,iy,tag)
    c=lattice(seed,ix,iy+1,tag);d=lattice(seed,ix+1,iy+1,tag)
    return (a+(b-a)*tx)*(1-ty)+(c+(d-c)*tx)*ty


def region_at(x:int,y:int,seed:int) -> dict:
    # Seeded large-scale anchors: can later be replaced with versioned approved
    # public geographic data without changing the downstream world schemas.
    metropolis=(72,72)
    town=(280,110)
    d_m=math.hypot(x-metropolis[0],y-metropolis[1])
    d_t=math.hypot(x-town[0],y-town[1])
    elev=noise(seed,x,y,256,"mountain")*.35+noise(seed,x,y,96,"relief")*.20
    elev+=0.65*max(0,1-math.hypot(x+220,y-100)/260)
    moisture=noise(seed,x,y,190,"rain")*.5+0.5
    if elev>0.57:zone="mountain"
    elif d_m<27:zone="downtown"
    elif d_m<60:zone="urban"
    elif d_m<116:zone="suburb"
    elif d_t<35:zone="small_town"
    elif d_m<160 or d_t<70:zone="rural"
    elif moisture>.58:zone="forest"
    elif moisture>.33:zone="farmland"
    else:zone="plains"
    return {"zone":zone,"elevation":round(elev,4),"moisture":round(moisture,4)}


def river_at(x:int,y:int)->bool:
    river_x=192 + round(10*math.sin(y/31.0)+7*math.sin(y/73.0))
    return abs(x-river_x)<=2


def road_kind(x:int,y:int,zone:str)->str:
    # Same global coordinates guarantee continuous segments on chunk borders.
    if x%96 in (0,1,2) or y%96 in (0,1,2):return "highway"
    spacing={"downtown":12,"urban":16,"suburb":24,"small_town":20,
             "rural":48,"farmland":48,"industrial":24}.get(zone,0)
    if spacing and (x%spacing in (0,1) or y%spacing in (0,1)):
        return "street"
    return ""


def terrain_kind(x:int,y:int,seed:int)->str:
    region=region_at(x,y,seed);zone=region["zone"]
    road=road_kind(x,y,zone)
    if river_at(x,y):return "bridge" if road else "water"
    if road:return road
    if zone=="mountain":return "rock"
    if zone in ("downtown","urban","small_town"):return "concrete_stained" if stable01(seed,x//9,y//9,"pave")>.40 else "grass_sparse"
    if zone=="suburb":return "grass_sparse"
    if zone in ("rural","farmland"):return "farmland" if (x//16+y//16)%3 else "grass_sparse"
    if zone=="forest":return "forest_floor"
    return "dry_grass"


def house_rooms(building_id:str,rect:list[int],seed:int)->dict:
    bx,by,w,h=rect
    # Main archetype geometry: central hall with 4 rooms, real connectivity.
    half=w//2;hall_w=2;left_w=max(2,half-1);right_x=bx+left_w+hall_w
    right_w=w-left_w-hall_w
    if right_w<2 or h<6:raise ValueError("House footprint too small")
    h_top=h//2
    arrangement=["kitchen","bedroom","living","bathroom"]
    rng=random.Random(seed)
    rng.shuffle(arrangement)
    r_rects=[[bx,by,left_w,h_top],[right_x,by,right_w,h_top],
             [bx,by+h_top,left_w,h-h_top],[right_x,by+h_top,right_w,h-h_top]]
    hall_id=building_id+".hall";rooms=[];doors=[];furniture=[]
    for i,(name,rr) in enumerate(zip(arrangement,r_rects)):
        rid=building_id+f".room{i+1}"
        rooms.append({"id":rid,"type":name,"rect":rr,"loot_tags":[name]})
        doors.append({"id":rid+".door","pos":[bx+left_w if i%2==0 else right_x,rr[1]+rr[3]//2],
                      "connects":[rid,hall_id]})
        furniture.append({"id":rid+".fixture","room_id":rid,"type":name,
                          "pos":[rr[0]+1,rr[1]+1],"art_status":"placeholder"})
    return {"hall":{"id":hall_id,"rect":[bx+left_w,by,hall_w,h]},
            "rooms":rooms,"doors":doors,"furniture":furniture}


def simple_rooms(building_id:str,rect:list[int],kind:str)->dict:
    bx,by,w,h=rect
    first="workshop" if kind=="garage" else "sales_floor"
    second="stockroom" if kind=="grocery_store" else "storage"
    rid1=building_id+".room1";rid2=building_id+".room2"
    hall_id=building_id+".hall"
    return {"hall":{"id":hall_id,"rect":[bx+w//2,by,1,h]},
            "rooms":[{"id":rid1,"type":first,"rect":[bx,by,w//2,h]},
                     {"id":rid2,"type":second,"rect":[bx+w//2+1,by,w-w//2-1,h]}],
            "doors":[{"id":rid1+".door","pos":[bx+w//2,by+h//2],"connects":[rid1,hall_id]},
                     {"id":rid2+".door","pos":[bx+w//2+1,by+h//2],"connects":[rid2,hall_id]}],
            "furniture":[]}


def building_for_lot(lot:dict,seed:int)->dict:
    rng=random.Random(seed_for(seed,lot["id"],"shell"))
    lx,ly,lw,lh=lot["rect"]
    archetype=lot["archetype_id"]
    w=min(lw-2,8+rng.randrange(0,3));h=min(lh-2,8+rng.randrange(0,2))
    w=max(7,w);h=max(7,h)
    bx=lx+(lw-w)//2;by=ly+1
    footprint=[bx,by,w,h]
    bid=lot["id"]+".building"
    interior=house_rooms(bid,footprint,seed_for(seed,bid,"interior")) if archetype=="house_small" else simple_rooms(bid,footprint,archetype)
    entry=[bx+w//2,by]
    door={"id":bid+".front_door","pos":entry,"connects":[interior["hall"]["id"],"outside"]}
    roof=rng.choice(["gable","hip","offset_gable"]) if archetype=="house_small" else "flat"
    mats={"floor":rng.choice(["wood_oak","tile_ceramic"]),
          "wall":rng.choice(["plaster_cream","brick_aged","timber_painted"]),
          "roof":rng.choice(["shingle_asphalt","standing_seam_metal"])}
    return {"id":bid,"lot_id":lot["id"],"seed":seed_for(seed,bid),"archetype_id":archetype,
            "bounds":footprint,"entry":entry,"roof_profile":roof,"materials":mats,
            **interior,"doors":interior["doors"]+[door],"path_to_road":{"from":entry,"to":[entry[0],ly-1]},
            "art_status":"layout_only_needs_original_world_sprites"}


def rect_overlap(a:list,b:list)->bool:
    return a[0]<b[0]+b[2] and a[0]+a[2]>b[0] and a[1]<b[1]+b[3] and a[1]+a[3]>b[1]


def generate_chunk(cx:int,cy:int,seed:int,sz:int=CHUNK_SIZE)->dict:
    ox=cx*sz;oy=cy*sz
    mid=region_at(ox+sz//2,oy+sz//2,seed)
    # Original terrain palette, represented as small integer-coded grid.
    terrain=[];codes={name:i for i,name in enumerate(sorted(set(TERRAIN_MATERIALS+["bridge","highway","street"]))) }
    for local_y in range(sz):
        terrain.append([codes[terrain_kind(ox+x,oy+local_y,seed)] for x in range(sz)])
    lots=[];buildings=[];used=[]
    # Parcels use a stable, independent global lattice. Skip incompatible lots.
    for gy in range((oy//16-1)*16,oy+sz+16,16):
        for gx in range((ox//16-1)*16,ox+sz+16,16):
            lx=gx+2;ly=gy+2;lot=[lx,ly,12,12]
            if not (ox<=lx and oy<=ly and lx+12<=ox+sz and ly+12<=oy+sz):continue
            center=(lx+6,ly+6)
            zone=region_at(*center,seed)["zone"]
            if zone not in ("downtown","urban","suburb","small_town","rural","farmland"):continue
            # A finite global road right-of-way must exist on the north side.
            if road_kind(center[0],ly-1,zone)=="":continue
            if any(terrain_kind(xx,yy,seed) in ("water","rock","bridge","highway") for xx,yy in
                   ((lx,ly),(lx+11,ly),(lx,ly+11),(lx+11,ly+11))):continue
            chance={"downtown":.93,"urban":.84,"suburb":.76,"small_town":.78,"rural":.23,"farmland":.15}[zone]
            if stable01(seed,lx,ly,"occupancy")>chance:continue
            if any(rect_overlap(lot,p) for p in used):continue
            archetype=("grocery_store" if zone in ("downtown","urban","small_town") and stable01(seed,lx,ly,"business")>.82
                       else "garage" if zone in ("suburb","rural","farmland") and stable01(seed,lx,ly,"garage")>.82
                       else "house_small")
            lid=f"ll.world.{seed}.lot.{lx}.{ly}"
            lot_info={"id":lid,"rect":lot,"zone":zone,"archetype_id":archetype}
            b=building_for_lot(lot_info,seed)
            # Prevent placing a building on actual road/water, even when zoning shifts.
            x0,y0,w,h=b["bounds"]
            if any(terrain_kind(xx,yy,seed) in ("water","bridge","street","highway","rock")
                   for yy in range(y0,y0+h) for xx in range(x0,x0+w)):continue
            lots.append(lot_info);buildings.append(b);used.append(lot)
    result={"schema":WORLD_SCHEMA,"version":VERSION,"chunk_id":f"ll.chunk.{cx}.{cy}",
            "chunk_xy":[cx,cy],"global_origin_tile":[ox,oy],"chunk_size_tiles":sz,"seed":seed_for(seed,"chunk",cx,cy),
            "world_seed":seed,"center_region":mid,"material_keys":{str(v):k for k,v in codes.items()},
            "terrain_codes":terrain,"lots":lots,"buildings":buildings,
            "status":"original_layout_candidate_unverified_in_godot"}
    validate_chunk(result)
    return result


def validate_chunk(chunk:dict)->None:
    if chunk.get("schema")!=WORLD_SCHEMA:raise ValueError("Bad chunk schema")
    sz=chunk["chunk_size_tiles"];cells=chunk["terrain_codes"]
    if len(cells)!=sz or any(len(r)!=sz for r in cells):raise ValueError("Wrong terrain grid dimensions")
    seen=set();lots=[]
    ox,oy=chunk["global_origin_tile"]
    for lot in chunk["lots"]:
        if lot["id"] in seen:raise ValueError("Duplicate lot id")
        seen.add(lot["id"])
        r=lot["rect"]
        if not (ox<=r[0] and oy<=r[1] and r[0]+r[2]<=ox+sz and r[1]+r[3]<=oy+sz):raise ValueError("Lot crosses chunk")
        if any(rect_overlap(r,p) for p in lots):raise ValueError("Overlapping lots")
        lots.append(r)
    if len(chunk["buildings"])!=len(chunk["lots"]):raise ValueError("Lot/building cardinality mismatch")
    for b in chunk["buildings"]:
        if b["id"] in seen:raise ValueError("Duplicate building id")
        seen.add(b["id"])
        if b["lot_id"] not in {q["id"] for q in chunk["lots"]}:raise ValueError("Orphan building")
        lid=next(q for q in chunk["lots"] if q["id"]==b["lot_id"])
        r=lid["rect"];br=b["bounds"]
        if not (r[0]<=br[0] and r[1]<=br[1] and br[0]+br[2]<=r[0]+r[2] and br[1]+br[3]<=r[1]+r[3]):raise ValueError("Building outside lot")
        if sum("outside" in d["connects"] for d in b["doors"])!=1:raise ValueError("No unique exit")
        if any(sum(room["id"] in d["connects"] and b["hall"]["id"] in d["connects"] for d in b["doors"])<1 for room in b["rooms"]):
            raise ValueError("Unreachable room")
        all_obj=[b["hall"],*b["rooms"],*b["doors"],*b["furniture"]]
        for obj in all_obj:
            if obj["id"] in seen:raise ValueError("Duplicate instance ID")
            seen.add(obj["id"])


def render_map(chunks:list[dict],root:Path,seed:int)->str|None:
    Image,ImageDraw=optional_pillow()
    if Image is None or not chunks:return None
    coords=[c["chunk_xy"] for c in chunks]
    minx=min(c[0] for c in coords);miny=min(c[1] for c in coords)
    maxx=max(c[0] for c in coords);maxy=max(c[1] for c in coords)
    w=(maxx-minx+1)*CHUNK_SIZE;h=(maxy-miny+1)*CHUNK_SIZE
    scale=4 if w<250 else 2
    if w*scale*h*scale>24_000_000:
        scale=1
    # Limit phone memory; avoid rendering oversized world map previews.
    if w*h>12_000_000:return None
    im=Image.new("RGB",(w,h),(39,57,43));d=ImageDraw.Draw(im)
    for c in chunks:
        dx=(c["chunk_xy"][0]-minx)*CHUNK_SIZE
        dy=(c["chunk_xy"][1]-miny)*CHUNK_SIZE
        lut={int(k):PALETTE.get(v,(80,80,80)) for k,v in c["material_keys"].items()}
        for iy,row in enumerate(c["terrain_codes"]):
            for ix,code in enumerate(row):d.point((dx+ix,dy+iy),fill=lut[code])
        for b in c["buildings"]:
            x,y,bw,bh=b["bounds"]
            x=x-minx*CHUNK_SIZE;y=y-miny*CHUNK_SIZE
            col={"house_small":(193,184,154),"garage":(154,152,129),"grocery_store":(168,140,123)}.get(b["archetype_id"],(180,180,180))
            d.rectangle((x,y,x+bw-1,y+bh-1),fill=col,outline=(39,38,35),width=1)
    if scale>1:im=im.resize((w*scale,h*scale),Image.Resampling.NEAREST)
    out=root/"review"/"region_overview.png"
    out.parent.mkdir(parents=True,exist_ok=True);im.save(out,optimize=True)
    return str(out.relative_to(root))


def render_macro_atlas(root:Path,seed:int,area:tuple[int,int,int,int]=(-320,-110,720,460))->str|None:
    """Big-picture region overview; not a geographic map of real America."""
    Image,ImageDraw=optional_pillow()
    if Image is None:return None
    x0,y0,w,h=area
    width=360;height=230
    im=Image.new("RGB",(width,height));draw=ImageDraw.Draw(im)
    colors={"downtown":(169,157,136),"urban":(142,144,126),"suburb":(130,160,114),
      "small_town":(172,162,118),"rural":(143,161,105),"farmland":(181,173,114),
      "forest":(59,99,67),"plains":(190,169,108),"mountain":(127,124,116)}
    for py in range(height):
        y=y0+py*h//height
        for px in range(width):
            x=x0+px*w//width
            if river_at(x,y):color=(49,112,137)
            else:color=colors[region_at(x,y,seed)["zone"]]
            draw.point((px,py),fill=color)
    # Highways are shared, deterministic corridors. Draw separately at macro scale.
    for px in range(width):
        gx=x0+px*w//width
        if gx%96<3:draw.line((px,0,px,height-1),fill=(91,85,77),width=1)
    for py in range(height):
        gy=y0+py*h//height
        if gy%96<3:draw.line((0,py,width-1,py),fill=(91,85,77),width=1)
    for center in ((72,72),(280,110)):
        px=round((center[0]-x0)*width/w);py=round((center[1]-y0)*height/h)
        draw.ellipse((px-3,py-3,px+3,py+3),fill=(199,66,45),outline=(230,219,164))
    im=im.resize((width*2,height*2),Image.Resampling.NEAREST)
    path=root/"review"/"macro_region_preview.png";path.parent.mkdir(parents=True,exist_ok=True)
    im.save(path,optimize=True)
    return str(path.relative_to(root))


def compile_region(root:Path,seed:int,start:tuple[int,int],shape:tuple[int,int],preview:bool=True)->dict:
    sx,sy=start;nx,ny=shape
    if nx<1 or ny<1 or nx*ny>50000:raise ValueError("Choose 1..50,000 chunks per invocation; process larger worlds in shards")
    t0=time.monotonic();records=[];preview_chunks=[];failed=[];counts=Counter()
    prev_path=root/"manifests"/"world_manifest.json"
    prior_hashes={}
    if prev_path.exists():
        try:
            prev=json.loads(prev_path.read_text(encoding="utf8"))
            if prev.get("world_seed")==seed and prev.get("factory_version")==VERSION:
                prior_hashes={row["file"]:row["sha256"] for row in prev.get("chunks",[])}
        except (ValueError,OSError,KeyError,TypeError):
            pass
    for dy in range(ny):
        for dx in range(nx):
            cx=sx+dx;cy=sy+dy
            target=root/"world"/f"seed_{seed}"/"chunks"/f"chunk_{cx}_{cy}.json"
            try:
                chunk=None;status="written"
                key=str(target.relative_to(root))
                if target.exists():
                    try:
                        existing=target.read_bytes()
                        same_as_manifest=(not prior_hashes or prior_hashes.get(key)==sha256(existing))
                        candidate=json.loads(existing)
                        if (same_as_manifest and candidate.get("version")==VERSION and
                           candidate.get("chunk_xy")==[cx,cy] and candidate.get("world_seed")==seed):
                            validate_chunk(candidate)
                            chunk=candidate;status="reused"
                    except (ValueError,OSError,TypeError,KeyError):
                        pass
                if chunk is None:
                    chunk=generate_chunk(cx,cy,seed)
                    raw=pretty(chunk);h=write_atomic(target,raw)
                else:
                    h=sha256(target.read_bytes())
                records.append({"chunk_id":chunk["chunk_id"],"file":str(target.relative_to(root)),"sha256":h,
                                "buildings":len(chunk["buildings"]),"status":status})
                counts["buildings"]+=len(chunk["buildings"])
                counts["rooms"]+=sum(len(b["rooms"]) for b in chunk["buildings"])
                if preview and nx*ny<=144:preview_chunks.append(chunk)
            except (OSError,ValueError,KeyError,TypeError) as exc:                failed.append({"chunk_xy":[cx,cy],"error":str(exc)})
    manifest={"schema":"last_light.world_manifest.v1","factory_version":VERSION,"world_seed":seed,
              "grid":CHUNK_SIZE,"tile_px":list(TILE_PX),"mode":"fictional_seeded",
              "origin_chunk":list(start),"chunk_grid":list(shape),"chunks":records,
              "generated_chunks":len(records),"failed_chunks":failed,
              "total_buildings":counts["buildings"],"total_rooms":counts["rooms"],
              "performance":{"seconds":round(time.monotonic()-t0,3)},
              "godot_tested":False,"iphone_verified":False,"art_status":"layout_candidates_only"}
    manifest_path=root/"manifests"/"world_manifest.json"
    write_atomic(manifest_path,pretty(manifest))
    if preview_chunks:
        manifest["review_preview"]=render_map(preview_chunks,root,seed)
        write_atomic(manifest_path,pretty(manifest))
    return manifest


def verify_world(root:Path)->dict:
    path=root/"manifests"/"world_manifest.json"
    if not path.exists():raise FileNotFoundError("No world manifest yet")
    manifest=json.loads(path.read_text("utf8"));verified=0;errors=[]
    for entry in manifest["chunks"]:
        file=root/entry["file"]
        try:
            raw=file.read_bytes()
            if sha256(raw)!=entry["sha256"]:raise ValueError("Output hash mismatch")
            chunk=json.loads(raw);validate_chunk(chunk);verified+=1
        except (OSError,ValueError,KeyError) as exc:errors.append({"file":str(file),"error":str(exc)})
    result={"verified_chunks":verified,"total_chunks":len(manifest["chunks"]),"failures":errors,
            "technical_qa_passed":not errors and manifest["generated_chunks"]==verified,
            "godot_tested":False,"iphone_verified":False}
    write_atomic(root/"reports"/"world_validation.json",pretty(result))
    return result


def zip_outputs(root:Path,batch_tag:str="latest",max_files:int=3000)->list[str]:
    """Chunked, deterministic, integrity-tested ZIPs. Never include source JPGs or DB."""
    include=[]
    for folder in ("assets/original_candidates","assets/original_textures","world","manifests","review","reports","godot_export","imports/notion_item_icon_batches","imports/notion_classification_batches","imports/notion_media_shards"):
        sub=root/folder
        if sub.exists():include.extend(x for x in sub.rglob("*") if x.is_file() and ".tmp" not in x.name)
    include.sort(key=lambda x:str(x.relative_to(root)))
    paths=[]
    for ix in range(0,len(include),max_files):
        group=include[ix:ix+max_files]
        path=root/"exports"/f"LAST_LIGHT_{batch_tag}_{1+ix//max_files:03d}.zip"
        path.parent.mkdir(parents=True,exist_ok=True)
        temp=path.with_suffix(".zip.tmp")
        with zipfile.ZipFile(temp,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for file in group:
                name=str(file.relative_to(root)).replace(os.sep,"/")
                info=zipfile.ZipInfo(name,date_time=(2020,1,1,0,0,0))
                info.compress_type=zipfile.ZIP_DEFLATED
                z.writestr(info,file.read_bytes())
        os.replace(temp,path)
        with zipfile.ZipFile(path,"r") as z:
            corrupt=z.testzip()
            if corrupt:raise ValueError("Invalid ZIP member: "+corrupt)
        paths.append(str(path))
    return paths




# ----------------------- ORIGINAL VEGETATION CANDIDATES ------------------
# Light direction upper-left. Original small-scale layered pixel clusters.
# No external imagery or reference pixel sampling. Not Golden 40 approved.
def generate_vegetation_pack(root:Path, seed:int) -> dict:
    Image, Draw=optional_pillow()
    if Image is None:return {"generated":0,"error":"Pillow unavailable"}
    variants=[("oak",0),("oak",1),("pine",0),("pine",1),
              ("bush",0),("bush",1),("dry_bush",0),("dry_bush",1)]
    output=[]
    panel=Image.new("RGBA",(4*132,2*154),(25,37,31,255))
    for n,(kind,variant) in enumerate(variants):
        rr=random.Random(seed_for(seed,"vegetation",kind,variant))
        w,h=96,104
        im=Image.new("RGBA",(w,h),(0,0,0,0));d=Draw.Draw(im)
        # Contact shadow at the grounded base, with no baked white background.
        cx=48;ground=92
        d.ellipse((cx-24,ground-5,cx+27,ground+4),fill=(16,22,16,105))
        is_tree=kind in ("oak","pine")
        base=(56,87,55) if kind!="dry_bush" else (111,102,69)
        if is_tree:
            # Trunk and physical taper: warm lit upper-left, shadow right edge.
            if kind=="oak":
                trunk=[(43,ground),(44,45),(47,36),(52,38),(54,ground)]
            else:
                trunk=[(45,ground),(47,27),(51,27),(52,ground)]
            d.polygon(trunk,fill=(69,51,37,255))
            d.line((45,ground-3,46,45),fill=(133,106,68,255),width=2)
            d.line((53,ground-3,50,42),fill=(39,31,27,255),width=2)
            for dy in range(47,87,7):
                d.line((48,dy,51,dy+3),fill=(48,38,31,255),width=1)
            if kind=="oak":
                clusters=[(34,42,19,17),(57,40,21,19),(49,26,21,20),(31,56,16,15),(63,55,16,15),(47,56,23,17)]
            else:
                clusters=[(48,29,10,20),(48,41,14,20),(48,54,20,20),(48,68,24,19)]
        else:
            # Small woody branch structure under the visible canopy.
            for k in range(6):
                ox=rr.randint(-20,19)
                d.line((cx,ground, cx+ox, ground-rr.randint(13,27)),fill=(83,66,46,255),width=2)
            clusters=[(cx+rr.randint(-18,18),ground-rr.randint(12,27),rr.randint(11,19),rr.randint(9,16)) for _ in range(6)]
        # Large directional clusters before fine leaves. Dark underside, lit upper-left.
        for tx,ty,rx,ry in clusters:
            dx=rr.randint(-2,3);dy=rr.randint(-2,3)
            x=tx+dx;y=ty+dy
            light=tuple(max(0,min(255,int(v*1.19))) for v in base)
            dark=tuple(int(v*.62) for v in base)
            mid=tuple(int(v*.91) for v in base)
            d.ellipse((x-rx,y-ry,x+rx,y+ry),fill=dark+(255,))
            d.ellipse((x-rx+2,y-ry-1,x+rx-4,y+ry-5),fill=mid+(255,))
            d.ellipse((x-rx+3,y-ry+2,x+rx-8,y+ry-10),fill=light+(255,))
            # Small fixed pixel cluster highlights & internal shade spots.
            for k in range(int(rx*ry*.15)):
                px=rr.randint(x-rx+2,x+rx-3);py=rr.randint(y-ry+2,y+ry-2)
                # reject points outside ellipse
                if ((px-x)/max(1,rx))**2+((py-y)/max(1,ry))**2>.86:continue
                shade=light if px<x and py<y else dark if px>x+3 and py>y else mid
                if rr.random()<.34:
                    d.rectangle((px,py,px+rr.choice((0,1,2)),py+rr.choice((0,1))),fill=shade+(255,))
        target=root/"assets"/"original_textures"/"vegetation"/f"{kind}_{variant:02d}.png"
        target.parent.mkdir(parents=True,exist_ok=True)
        im.save(target,optimize=True)
        thumb=im.resize((120,130),Image.Resampling.NEAREST)
        panel.alpha_composite(thumb,((n%4)*132+6,(n//4)*154+6))
        output.append({"id":f"vegetation.{kind}.{variant:02d}","path":str(target.relative_to(root)),
                       "sha256":sha256(target.read_bytes()),"status":"visual_review_required"})
    sheet=root/"review"/"vegetation_candidates.png"
    sheet.parent.mkdir(parents=True,exist_ok=True);panel.save(sheet,optimize=True)
    write_atomic(root/"manifests"/"vegetation_manifest.json",pretty({"schema":"last_light.vegetation_preview.v1","assets":output,"approved":False}))
    return {"generated":len(output),"preview":str(sheet),"golden_40_approved":False}

# ------------------ RESEARCH MIRROR AND CATALOG RECONCILIATION ------------
# Notion exports are versioned to GitHub by the research worker. We download
# metadata JSONL only. Source image files are NEVER mirrored, transformed or
# included in exports. This uses ordinary HTTPS, no paid or secret API key.
RESEARCH_GITHUB_BRANCH = "feature/unified-factory-v2-research-neighborhood"
RESEARCH_GITHUB_ROOT = "https://raw.githubusercontent.com/kalashgit/last-light-godot/"
EXPECTED_ICON_RECORDS = 4347
EXPECTED_ICON_BATCHES = 23
MEDIA_SHARD_NAMES = [
    "vehicle_models_01.jsonl","vehicle_models_02.jsonl", "vehicle_screenshots_01.jsonl",
    "animated_images_01.jsonl","animal_images_01.jsonl",
    "tile_images_01.jsonl","tile_images_02.jsonl","tile_images_03.jsonl","tile_images_04.jsonl",
    "screenshots_01.jsonl","screenshots_02.jsonl",
    "devblog_images_01.jsonl","devblog_images_02.jsonl","devblog_images_03.jsonl",
    "exceptional_parentheses_links.jsonl"
]


def sync_reference_catalog(root: Path) -> dict:
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError, URLError
    inbox = root / "imports" / "notion_item_icon_batches"
    inbox.mkdir(parents=True, exist_ok=True)
    count = 0
    existing = 0
    failures = []
    for family, folder in (("sources", "notion_item_icon_batches"), ("classifications", "notion_classification_batches")):
      dest = root / "imports" / folder
      dest.mkdir(parents=True,exist_ok=True)
      for number in range(1, EXPECTED_ICON_BATCHES + 1):
        name = f"batch_{number:02d}.jsonl"
        target = dest / name
        if target.is_file() and target.stat().st_size > 0:
            existing += 1
            count += 1
            continue
        url = (RESEARCH_GITHUB_ROOT + RESEARCH_GITHUB_BRANCH +
               "/data/research/" + folder + "/" + name)
        try:
            req = Request(url, headers={"User-Agent": "LAST-LIGHT-factory/2"})
            with urlopen(req, timeout=20) as response:
                raw = response.read(1_000_001)
            if len(raw) > 1_000_000:
                raise ValueError("Metadata batch exceeds safe 1 MB cap")
            lines = [json.loads(x) for x in raw.decode("utf-8").splitlines() if x.strip()]
            if len(lines) not in (100, 147, 200):
                raise ValueError(f"Unexpected batch count {len(lines)}")
            for row in lines:
                if not row.get("source_file_page") or not row.get("source_filename"):
                    raise ValueError("Invalid source/classification metadata")
            write_atomic(target, raw)
            count += 1
        except (OSError, ValueError, UnicodeError, HTTPError, URLError, TimeoutError) as exc:
            failures.append({"family":family,"batch": number, "error": str(exc)})
    for name in MEDIA_SHARD_NAMES:
        target=root/"imports"/"notion_media_shards"/name
        target.parent.mkdir(parents=True,exist_ok=True)
        if target.is_file() and target.stat().st_size>0:
            existing+=1;count+=1;continue
        url=RESEARCH_GITHUB_ROOT+RESEARCH_GITHUB_BRANCH+"/data/research/notion_media_shards/"+name
        try:
            with urlopen(Request(url,headers={"User-Agent":"LAST-LIGHT-factory/2"}),timeout=20) as response:
                raw=response.read(1_000_001)
            if len(raw)>1_000_000:raise ValueError("Shard exceeds cap")
            records=[json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
            if not records or not all(x.get("mediawiki_id") and x.get("source_file_page") for x in records):
                raise ValueError("Invalid universal source shard")
            write_atomic(target,raw);count+=1
        except (OSError,ValueError,UnicodeError,HTTPError,URLError,TimeoutError) as exc:
            failures.append({"media_shard":name,"error":str(exc)})
    # Import the independent LAST LIGHT building-archetype identities as
    # *proposed* specifications. This does not mark any building playable.
    building_path = root / "imports" / "notion_building_archetypes_60.json"
    building_present = building_path.is_file()
    if not building_present:
        building_url = (RESEARCH_GITHUB_ROOT + RESEARCH_GITHUB_BRANCH +
                        "/data/research/notion_building_archetypes_60.json")
        try:
            req = Request(building_url, headers={"User-Agent": "LAST-LIGHT-factory/2"})
            with urlopen(req, timeout=20) as response:
                raw = response.read(250_001)
            if len(raw) > 250_000:
                raise ValueError("Building archetype metadata exceeds safe size cap")
            building_data = json.loads(raw.decode("utf-8"))
            archetypes = building_data.get("records", [])
            if len(archetypes) != 60 or len({x.get("archetype_id") for x in archetypes}) != 60:
                raise ValueError("Building archetype index must contain 60 unique IDs")
            if any(x.get("approved_original_recipe") for x in archetypes):
                raise ValueError("Unexpected production approval in research-only snapshot")
            write_atomic(building_path, raw)
            building_present = True
        except (OSError, ValueError, UnicodeError, HTTPError, URLError, TimeoutError) as exc:
            failures.append({"family": "building_archetypes", "error": str(exc)})
    result = {"available_batches": count, "expected_batches": EXPECTED_ICON_BATCHES * 2 + len(MEDIA_SHARD_NAMES),
              "building_archetype_snapshot_available": building_present,
              "preexisting_batches": existing, "errors": failures,
              "note": "Research metadata only, not original approved art"}
    write_atomic(root / "reports" / "source_sync.json", pretty(result))
    return result


def reconcile_item_icons(catalog: Catalog, root: Path) -> dict:
    by_index = {}
    duplicates = []
    for (rid, metadata) in catalog.db.execute(
        "SELECT id,metadata_json FROM sources WHERE id LIKE 'pzwiki.icon.%'"):
        info = json.loads(metadata)
        idx = info.get("source_index")
        try:
            idx = int(idx)
        except (ValueError, TypeError):
            continue
        if idx in by_index:
            duplicates.append({"index": idx, "ids": [rid, by_index[idx]]})
        by_index[idx] = rid
    missing = [i for i in range(1, EXPECTED_ICON_RECORDS + 1) if i not in by_index]
    extras = sorted(i for i in by_index if i < 1 or i > EXPECTED_ICON_RECORDS)
    classification_count=catalog.db.execute("SELECT COUNT(*) FROM classifications").fetchone()[0]
    result = {"schema": "last_light.notion_coverage.v2", "expected": EXPECTED_ICON_RECORDS,
              "classification_records":classification_count,"classification_complete":classification_count==EXPECTED_ICON_RECORDS,
              "present_indexed_records": len(by_index), "missing_indices": missing,
              "duplicate_indices": duplicates, "out_of_range_indices": extras,
              "full_reference_coverage": not missing and not duplicates and not extras,
              "asset_quality_approved": False, "image_licensing_cleared": False}
    write_atomic(root / "reports" / "notion_icon_reconciliation.json", pretty(result))
    return result


GODOT_PILOT_SCRIPT = 'extends Node2D\n## LAST LIGHT UCF V2 — generated neighborhood test; original debug art only.\n## An opt-in scene. Does NOT replace main.tscn or modify the survival-house save.\nconst DATA_PATH := "res://data/generated/neighborhood_v2.json"\nconst SAVE_PATH := "user://ll_ucf_v2_neighborhood_save.json"\nconst TX := 40.0\nconst TY := 20.0\nvar neighborhood: Dictionary = {}\nvar player: Vector2 = Vector2(8, 40)\nvar move_vector: Vector2 = Vector2.ZERO\nvar touch_id: int = -1\nvar touch_start: Vector2 = Vector2.ZERO\nvar roofs_visible: bool = true\nvar zoom_factor: float = 1.0\nvar open_doors: Dictionary = {}\nvar message: String = "Explore the generated street"\nvar save_accumulator: float = 0.0\n\nfunc _ready() -> void:\n    var raw: String = FileAccess.get_file_as_string(DATA_PATH)\n    var parsed: Variant = JSON.parse_string(raw)\n    if parsed is Dictionary and parsed.get("schema", "") == "last_light.playable_neighborhood.v2":\n        neighborhood = parsed\n        player = _vec(neighborhood.get("player_spawn", [8, 40]))\n        _load_game()\n    else:\n        push_error("Missing valid generated neighborhood JSON: " + DATA_PATH)\n    set_process(true)\n    queue_redraw()\n\nfunc _exit_tree() -> void:\n    _save_game()\n\nfunc _vec(arr: Array) -> Vector2:\n    return Vector2(float(arr[0]), float(arr[1]))\n\nfunc _iso(point: Vector2) -> Vector2:\n    return Vector2((point.x - point.y) * TX, (point.x + point.y) * TY)\n\nfunc _camera_offset() -> Vector2:\n    var size: Vector2 = get_viewport_rect().size\n    return size * Vector2(0.5, 0.52) - _iso(player) * zoom_factor\n\nfunc _stick_center() -> Vector2:\n    var size: Vector2 = get_viewport_rect().size\n    return Vector2(108.0, size.y - 130.0)\n\nfunc _button_center() -> Vector2:\n    var size: Vector2 = get_viewport_rect().size\n    return Vector2(size.x - 105.0, size.y - 118.0)\n\nfunc _indoor_building() -> Dictionary:\n    for entry in neighborhood.get("buildings", []):\n        var b: Dictionary = entry\n        var bounds: Array = b["footprint"]\n        var origin: Vector2 = Vector2(float(bounds[0]), float(bounds[1]))\n        var rect: Rect2 = Rect2(origin, Vector2(float(bounds[2]), float(bounds[3])))\n        if rect.has_point(player):\n            return b\n    return {}\n\nfunc _process(delta: float) -> void:\n    if neighborhood.is_empty():\n        queue_redraw()\n        return\n    var direction: Vector2 = Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")\n    if move_vector.length_squared() > 0.001:\n        direction = move_vector\n    var next: Vector2 = player + direction.normalized() * delta * 4.1\n    if next.x >= 0.5 and next.x <= 65.0 and next.y >= 0.5 and next.y <= 45.5:\n        player = next\n    # Smooth automatic zoom while the player occupies an interior.\n    var wanted_zoom: float = 1.65 if not _indoor_building().is_empty() else 1.0\n    zoom_factor = lerpf(zoom_factor, wanted_zoom, 1.0 - exp(-5.0 * minf(delta, 0.15)))\n    save_accumulator += delta\n    if save_accumulator >= 12.0:\n        save_accumulator = 0.0\n        _save_game()\n    queue_redraw()\n\nfunc _input(event: InputEvent) -> void:\n    if event is InputEventScreenTouch:\n        var p: Vector2 = event.position\n        if event.pressed:\n            if p.distance_to(_stick_center()) <= 105.0 and touch_id == -1:\n                touch_id = event.index\n                touch_start = _stick_center()\n                move_vector = (p - touch_start).limit_length(64.0) / 64.0\n            elif p.distance_to(_button_center()) <= 92.0:\n                _interact()\n        elif event.index == touch_id:\n            touch_id = -1\n            move_vector = Vector2.ZERO\n    elif event is InputEventScreenDrag:\n        if event.index == touch_id:\n            move_vector = (event.position - touch_start).limit_length(64.0) / 64.0\n    elif event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:\n        if event.position.distance_to(_button_center()) < 100.0:\n            _interact()\n    elif event is InputEventKey and event.pressed and not event.echo:\n        if event.keycode == KEY_E or event.keycode == KEY_SPACE:\n            _interact()\n        elif event.keycode == KEY_R:\n            roofs_visible = not roofs_visible\n\nfunc _interact() -> void:\n    if neighborhood.is_empty():\n        return\n    var interior: Dictionary = _indoor_building()\n    if not interior.is_empty():\n        var entry: Vector2 = _vec(interior["entry"]["pos"])\n        player = entry + Vector2(0.0, 1.2)\n        message = "Exited " + str(interior["id"])\n        _save_game()\n        return\n    var nearest: Dictionary = {}\n    var nearest_distance: float = 3.4\n    for b in neighborhood["buildings"]:\n        var entry: Vector2 = _vec(b["entry"]["pos"])\n        var distance: float = entry.distance_to(player)\n        if distance < nearest_distance:\n            nearest = b\n            nearest_distance = distance\n    if not nearest.is_empty():\n        var entry: Vector2 = _vec(nearest["entry"]["pos"])\n        player = entry + Vector2(0.0, -1.5)\n        open_doors[str(nearest["entry"]["id"])] = true\n        message = "Entered " + str(nearest["id"])\n        _save_game()\n    else:\n        message = "Move to a front door"\n\nfunc _save_game() -> void:\n    if neighborhood.is_empty():\n        return\n    var payload: Dictionary = {\n        "schema": "last_light.neighborhood_save.v2",\n        "seed": neighborhood["seed"],\n        "position": [player.x, player.y],\n        "doors_open": open_doors\n    }\n    var file: FileAccess = FileAccess.open(SAVE_PATH, FileAccess.WRITE)\n    if file != null:\n        file.store_string(JSON.stringify(payload))\n        file.close()\n\nfunc _load_game() -> void:\n    if not FileAccess.file_exists(SAVE_PATH):\n        return\n    var payload: Variant = JSON.parse_string(FileAccess.get_file_as_string(SAVE_PATH))\n    if payload is Dictionary and payload.get("schema", "") == "last_light.neighborhood_save.v2" and payload.get("seed", -1) == neighborhood["seed"]:\n        var p: Variant = payload.get("position", [])\n        if p is Array and p.size() == 2:\n            var point: Vector2 = _vec(p)\n            if point.x >= 0 and point.x <= 66 and point.y >= 0 and point.y <= 46:\n                player = point\n        if payload.get("doors_open", {}) is Dictionary:\n            open_doors = payload["doors_open"]\n\nfunc _quad(rect: Array, color: Color) -> void:\n    var x: float = float(rect[0]); var y: float = float(rect[1])\n    var w: float = float(rect[2]); var h: float = float(rect[3])\n    draw_colored_polygon(PackedVector2Array([\n        _iso(Vector2(x,y)), _iso(Vector2(x+w,y)),\n        _iso(Vector2(x+w,y+h)), _iso(Vector2(x,y+h))]), color)\n\nfunc _line(a: Vector2, b: Vector2, color: Color, width: float = 3.0) -> void:\n    draw_line(_iso(a), _iso(b), color, width, true)\n\nfunc _draw_house(b: Dictionary) -> void:\n    var bounds: Array = b["footprint"]\n    var x: float = float(bounds[0]); var y: float = float(bounds[1])\n    var w: float = float(bounds[2]); var h: float = float(bounds[3])\n    _quad(bounds, Color("9b947f"))\n    for room in b["rooms"]:\n        var tint: Color = Color("a8997b")\n        match str(room["type"]):\n            "kitchen": tint = Color("a7aaa0")\n            "bedroom": tint = Color("a8927d")\n            "living": tint = Color("9e947d")\n            "bathroom": tint = Color("9caeaf")\n        _quad(room["rect"],tint)\n    _quad(b["hall"]["rect"],Color("c4bca6"))\n    for f in b["furnishings"]:\n        var p: Vector2 = _vec(f["pos"])\n        _quad([p.x,p.y,0.7,0.7], Color("5a5145"))\n    var wall: Color = Color("d1ccba")\n    _line(Vector2(x,y),Vector2(x+w,y),wall,5)\n    _line(Vector2(x,y),Vector2(x,y+h),wall,5)\n    _line(Vector2(x+w,y),Vector2(x+w,y+h),wall,5)\n    var entry: Vector2 = _vec(b["entry"]["pos"])\n    _line(Vector2(x,y+h),entry-Vector2(0.6,0),wall,5)\n    _line(entry+Vector2(0.6,0),Vector2(x+w,y+h),wall,5)\n    draw_circle(_iso(entry),5,Color("eac27e"))\n    for door in b["interior_doors"]:\n        draw_circle(_iso(_vec(door["pos"])),4,Color("e4bd83"))\n    if roofs_visible and _indoor_building().get("id","") != b["id"]:\n        var roof: Color = Color("5d686b")\n        roof.a = 0.94\n        _quad(bounds,roof)\n        _line(Vector2(x,y),Vector2(x+w,y+h),Color("889597"),2)\n\nfunc _draw() -> void:\n    var viewport: Vector2 = get_viewport_rect().size\n    draw_rect(Rect2(Vector2.ZERO,viewport),Color("15231d"))\n    if neighborhood.is_empty():\n        draw_string(ThemeDB.fallback_font, Vector2(20,45), "Generated neighborhood data missing", HORIZONTAL_ALIGNMENT_LEFT,-1,22,Color.WHITE)\n        return\n    draw_set_transform(_camera_offset(),0,Vector2.ONE * zoom_factor)\n    # Low-cost ground cell rendering within a radius of the player.\n    for yy in range(maxi(0,int(player.y)-19),mini(45,int(player.y)+19)):\n        for xx in range(maxi(0,int(player.x)-19),mini(65,int(player.x)+19)):\n            var variation: int = posmod((xx*37+yy*19+xx*yy*7),5)\n            var tint: Color = Color("456249").lightened(float(variation)*0.025)\n            _quad([xx,yy,1,1],tint)\n    for rd in neighborhood["road"]:\n        _quad(rd["rect"],Color("4c5052"))\n        var road: Array = rd["rect"]\n        for i in range(int(road[0])+2,int(road[0])+int(road[2]),7):\n            _line(Vector2(i,float(road[1])+2.5),Vector2(i+3,float(road[1])+2.5),Color("b1a97d"),3)\n    for b in neighborhood["buildings"]:\n        var path: Array = b["road_access_path"]\n        _line(_vec(path[0]),_vec(path[1]),Color("a6a18a"),12)\n        _draw_house(b)\n    var p: Vector2 = _iso(player)\n    draw_circle(p+Vector2(0,4),7,Color(0,0,0,0.6))\n    draw_rect(Rect2(p+Vector2(-4,-18),Vector2(8,17)),Color("6898ab"))\n    draw_circle(p+Vector2(0,-22),6,Color("d8bfa0"))\n    draw_set_transform(Vector2.ZERO,0,Vector2.ONE)\n    draw_circle(_stick_center(),70,Color(0.08,0.14,0.12,0.7))\n    draw_arc(_stick_center(),70,0.0,TAU,40,Color("b8c9ac"),3,true)\n    draw_circle(_stick_center()+move_vector*52.0,23,Color("d6bd84"))\n    draw_circle(_button_center(),58,Color("d1b481"))\n    draw_string(ThemeDB.fallback_font,_button_center()+Vector2(-36,6),"ENTER",HORIZONTAL_ALIGNMENT_LEFT,-1,17,Color("1b2923"))\n    draw_string(ThemeDB.fallback_font,Vector2(16,32),"LAST LIGHT / GENERATED NEIGHBORHOOD V2",HORIZONTAL_ALIGNMENT_LEFT,-1,17,Color("ebead9"))\n    draw_string(ThemeDB.fallback_font,Vector2(16,55),"3 original house layouts / debug art only",HORIZONTAL_ALIGNMENT_LEFT,-1,13,Color("c2c7b9"))\n    draw_string(ThemeDB.fallback_font,Vector2(16,78),message,HORIZONTAL_ALIGNMENT_LEFT,-1,14,Color("efcb8b"))\n'
GODOT_PILOT_SCENE = '[gd_scene load_steps=2 format=3]\n\n[ext_resource type="Script" path="res://scripts/unified_factory_neighborhood_v2.gd" id="1_neighborhood"]\n\n[node name="UnifiedFactoryNeighborhoodV2" type="Node2D"]\nscript = ExtResource("1_neighborhood")\n'
GODOT_PILOT_PROJECT = '; LAST LIGHT generated-neighborhood opt-in demo, not the existing survival house.\nconfig_version=5\n\n[application]\nconfig/name="LAST LIGHT — Generated Neighborhood V2 (Pilot)"\nrun/main_scene="res://scenes/unified_factory_neighborhood_v2.tscn"\n\n[display]\nwindow/size/viewport_width=1152\nwindow/size/viewport_height=720\nwindow/stretch/mode="canvas_items"\n\n[rendering]\nrenderer/rendering_method="gl_compatibility"\nrenderer/rendering_method.mobile="gl_compatibility"\ntextures/default_filters/use_nearest_mipmap_filter=false\n'

# ------------------- THREE-HOUSE PLAYABLE NEIGHBORHOOD DATA ---------------
# These are original deterministic architectural recipes, *not* real-world
# geography or third-party building floor-plan reproductions.
def produce_neighborhood(root: Path, world_seed: int) -> dict:
    rng = random.Random(seed_for(world_seed,"prototype_three_house_street"))
    materials = ["wood_oak", "tile_ceramic", "vinyl_check"]
    buildings=[]; lot_rects=[]; roads=[]
    for i in range(3):
        x = 6 + 17*i
        y = 12 + (i%2)*3
        w = [10, 11, 12][i]
        h = 9 + rng.randrange(0,3)
        bid = f"ll.neighborhood.h{i+1:02d}"
        lot = [x-2, y-3, 15, 17]
        if any(rect_overlap(lot, p) for p in lot_rects):
            raise ValueError("Neighborhood lots overlap")
        lot_rects.append(lot)
        shell = [x,y,w,h]
        split = w//2
        top = h//2
        roomnames=["kitchen","living","bedroom","bathroom"]
        rng.shuffle(roomnames)
        rs = [[x,y,split,top], [x+split,y,w-split,top],
              [x,y+top,split,h-top], [x+split,y+top,w-split,h-top]]
        rooms=[];furnish=[];doors=[]
        for j,rect in enumerate(rs):
            rid=f"{bid}.room{j+1:02d}"
            name=roomnames[j]
            rooms.append({"id":rid,"type":name,"rect":rect})
            furnish.append({"id":rid+".fixture", "type":name, "pos": [rect[0]+1.3,rect[1]+1.2],"status":"placeholder"})
            doors.append({"id":rid+".door", "pos":[x+split,rect[1]+max(1,rect[3]//2)],"room_id":rid})
        entry = [x+split,y+h]
        buildings.append({"id":bid,"archetype_id":"house_small", "lot_id":bid+".lot",
            "footprint":shell,"lot":lot,"seed":seed_for(world_seed,bid),
            "roof":["gable","hip","offset_gable"][i],
            "materials":{"wall":rng.choice(["plaster_cream","brick_aged","timber_painted"]),
                         "floor":materials[i], "roof":"shingle_asphalt"},
            "rooms":rooms,"furnishings":furnish,"interior_doors":doors,
            "entry":{"id":bid+".entry","pos":entry,"connects":["outside","hall"]},
            "hall":{"id":bid+".hall", "rect":[x+split-1,y,2,h]},
            "road_access_path":[entry,[entry[0],35]]})
    roads.append({"id":"ll.neighborhood.road.main", "rect":[0,35,66,5], "material":"asphalt_worn"})
    for b in buildings:
        if b["road_access_path"][0][1] >=35:raise ValueError("House entrance faces away from road")
    record={"schema":"last_light.playable_neighborhood.v2","version":VERSION,
        "seed":world_seed,"tile_px":list(TILE_PX),"road":roads,
        "ground_bounds":[0,0,66,46],"buildings":buildings,"player_spawn":[8,40],
        "roof_occlusion":"hide_near_player", "asset_stage":"debug_original_geometry_only",
        "godot_verified":False,"iphone_verified":False}
    result_path=root/"world"/f"seed_{world_seed}"/"neighborhood_v2.json"
    digest=write_atomic(result_path,pretty(record))
    # The Godot scene can read this path by copying it into its res://data dir.
    godot_target=root/"godot_export"/"data"/"generated"/"neighborhood_v2.json"
    write_atomic(godot_target,pretty(record))
    write_atomic(root/"godot_export"/"scripts"/"unified_factory_neighborhood_v2.gd", GODOT_PILOT_SCRIPT.encode("utf-8"))
    write_atomic(root/"godot_export"/"scenes"/"unified_factory_neighborhood_v2.tscn", GODOT_PILOT_SCENE.encode("utf-8"))
    write_atomic(root/"godot_export"/"project.godot", GODOT_PILOT_PROJECT.encode("utf-8"))
    preview = render_neighborhood(root,record)
    return {"buildings":len(buildings),"rooms":sum(len(b["rooms"]) for b in buildings),
            "file":str(result_path),"sha256":digest,"preview":preview,
            "status":"candidate_not_yet_godot_or_iphone_verified"}


def render_neighborhood(root: Path, neighborhood: dict) -> str | None:
    Image, Draw = optional_pillow()
    if Image is None:return None
    s=13; im=Image.new("RGB",(66*s,46*s),(60,86,61));d=Draw.Draw(im)
    rng=random.Random(seed_for(neighborhood["seed"],"review_ground"))
    for y in range(46):
        for x in range(66):
            n=rng.randrange(-12,13)
            c=(max(0,74+n), max(0,98+n), max(0,68+n))
            d.rectangle((x*s,y*s,(x+1)*s-1,(y+1)*s-1),fill=c)
    for rd in neighborhood["road"]:
        x,y,w,h=rd["rect"]
        d.rectangle((x*s,y*s,(x+w)*s-1,(y+h)*s-1),fill=(70,74,74))
        for tx in range(x+2,x+w,7):d.line((tx*s,(y+2.5)*s,(tx+3)*s,(y+2.5)*s),fill=(195,181,118),width=2)
    for b in neighborhood["buildings"]:
        lx,ly,lw,lh=b["lot"]
        d.rectangle((lx*s,ly*s,(lx+lw)*s,(ly+lh)*s),outline=(114,136,92),width=2)
        (a,c),(p,q)=b["road_access_path"]
        d.line((a*s,c*s,p*s,q*s),fill=(165,157,134),width=7)
        for j,room in enumerate(b["rooms"]):
            x,y,w,h=room["rect"]
            col={"kitchen":(160,159,144),"living":(149,132,109),
                 "bedroom":(162,144,129),"bathroom":(146,166,169)}[room["type"]]
            d.rectangle((x*s,y*s,(x+w)*s,(y+h)*s),fill=col,outline=(64,64,57),width=3)
        for f in b["furnishings"]:
            px,py=f["pos"]
            d.rectangle((px*s,py*s,px*s+9,py*s+9),fill=(81,64,48))
    out=root/"review"/"playable_neighborhood_layout.png"
    out.parent.mkdir(parents=True,exist_ok=True);im.save(out,optimize=True)
    return str(out)

def main(argv:list[str]|None=None)->int:
    argv=[] if argv is None else list(argv)
    parser=argparse.ArgumentParser(description="LAST LIGHT Unified Python Factory V2")
    parser.add_argument("--action",choices=["demo","import","sync_catalog","neighborhood","audit","batch","world","verify","export"],default=ACTION)
    parser.add_argument("--root",default=ROOT_FOLDER)
    parser.add_argument("--seed",type=int,default=WORLD_SEED)
    parser.add_argument("--origin",nargs=2,type=int,default=list(WORLD_ORIGIN_CHUNK))
    parser.add_argument("--chunks",nargs=2,type=int,default=list(WORLD_CHUNK_GRID))
    parser.add_argument("--batch",type=int,default=BATCH_SIZE)
    parser.add_argument("--no-preview",action="store_true")
    args=parser.parse_args(argv)
    root=writable_root(args.root);started=time.monotonic()
    print("LAST LIGHT MASTER FACTORY",VERSION,"| action:",args.action)
    print("DATA FOLDER:",root)
    if any(part.lower() in {"tmp","temp","private"} for part in root.parts):
        print("WARNING: TEMP storage may be erased by iOS; copy the export ZIP into Files/iCloud.")
    for sub in ("imports","reports","world","assets","manifests","review","exports"):(root/sub).mkdir(exist_ok=True)
    catalog=Catalog(root/"database"/"production.sqlite3")
    try:
        if args.action=="demo":
            example=root/"example_original_recipes.jsonl";sample_original_catalog(example)
            catalog.import_file(example);catalog.db.commit()
        if args.action=="sync_catalog":
            sync = sync_reference_catalog(root)
            print("GITHUB NOTION MIRROR:",sync)
        if args.action in ("import","sync_catalog"):
            stats = catalog.import_dir(root/"imports")
            write_atomic(root/"reports"/"import_results.json",pretty(stats))
            print("IMPORT:",stats)
            classifiers=catalog.import_classifications(root/"imports"/"notion_classification_batches")
            write_atomic(root/"reports"/"classification_results.json",pretty(classifiers))
            print("CLASSIFICATION:",classifiers["records_seen"],"records; issues:",classifiers["issue_count"])
            building_count=catalog.db.execute("SELECT COUNT(*) FROM sources WHERE id LIKE 'll.archetype.%'").fetchone()[0]
            print("BUILDING ARCHETYPES:",building_count,"proposed definitions; no playable renderers implied")
        if args.action in ("demo","batch"):
            result=produce_original_icons(catalog,root,max(1,args.batch))
            print("ICONS:",result["generated"],"candidate icons, errors:",len(result.get("errors",[])))
        if args.action=="neighborhood":
            preview = produce_neighborhood(root,args.seed)
            print("NEIGHBORHOOD:",preview)
            if GENERATE_TEXTURES:
                trees=generate_vegetation_pack(root,args.seed)
                print("VEGETATION CANDIDATES:",trees)
        if args.action in ("demo","world"):
            manifest=compile_region(root,args.seed,tuple(args.origin),tuple(args.chunks),
                                     preview=GENERATE_PREVIEWS and not args.no_preview)
            print("WORLD:",manifest["generated_chunks"],"chunks;",manifest["total_buildings"],
                  "buildings;",manifest["total_rooms"],"rooms")
            print("REGION PREVIEW:",manifest.get("review_preview","Pillow disabled or preview size too large"))
            if args.action=="demo":
                print("MACRO PREVIEW:",render_macro_atlas(root,args.seed))
        if args.action=="demo" and GENERATE_TEXTURES:
            img,_=optional_pillow()
            if img:
                mats=[]
                for material in TERRAIN_MATERIALS:
                    path=root/"assets"/"original_textures"/(material+".png")
                    hash_=generate_texture(material,seed_for(args.seed,"tile",material),path)
                    mats.append({"id":material,"path":str(path.relative_to(root)),"sha256":hash_,
                                 "status":"procedural_preview_needs_visual_approval"})
                write_atomic(root/"manifests"/"texture_manifest.json",pretty({"textures":mats,"schema":"last_light.texture_manifest.v1"}))
                print("TILES:",len(mats),"original preview textures")
        if args.action in ("demo","world","verify") and (root/"manifests"/"world_manifest.json").exists():
            v=verify_world(root)
            print("WORLD QA:",v["verified_chunks"],"verified; failures:",len(v["failures"]))
        if args.action in ("demo","audit","batch","import","sync_catalog","neighborhood"):
            report=catalog.report()
            if args.action in ("sync_catalog","import","audit"):
                reconciliation=reconcile_item_icons(catalog,root)
                print("ITEM RECONCILIATION:",reconciliation["present_indexed_records"],"of",EXPECTED_ICON_RECORDS,
                      "missing",len(reconciliation["missing_indices"]))
            write_atomic(root/"reports"/"coverage.json",pretty(report))
            print("SOURCE COVERAGE:",report["total_unique_records"],"imported; statuses:",report["by_disposition"])
        if args.action in ("demo","export","neighborhood","sync_catalog") and EXPORT_ZIP:
            exported=zip_outputs(root,"demo" if args.action=="demo" else args.action)
            print("EXPORTS:",*[str(x) for x in exported],sep="\n  ")
        print("COMPLETE in",round(time.monotonic()-started,2),"s; no paid API called")
    finally:catalog.close()
    return 0


if __name__=="__main__":
    raise SystemExit(main(sys.argv[1:]))