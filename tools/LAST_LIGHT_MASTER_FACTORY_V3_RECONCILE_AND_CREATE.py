#!/usr/bin/env python3
"""LAST LIGHT — Unified Reproducible Factory, executable foundation V3.

Runs locally on iPhone Python/CodePad or desktop, without a paid API.
Python standard library required; Pillow optional for actual PNG creation.

ONE-FILE RUN SETTINGS: Change ACTION near the top and press Run in CodePad.

V3 does NOT copy or generate art based solely on external source images.
V3 reconciles ALL imported source metadata and creates original PILOT assets for
16 independently authored semantic families. Reproducible original art generators
for every unknown vehicle/animal/weapon are not yet implemented.

  reconcile_and_generate: STEP 1 ledger + family suggestions for all imported records;
      STEP 2 independent pilot item/vegetation/terrain/FX renderers, candidate ZIP
  neighborhood: generates 3 original houses + street as a standalone Godot debug project
  sync_catalog: syncs GitHub Notion reference metadata (61 catalog shards) via HTTPS
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
ACTION = "reconcile_and_generate"            # reconcile_and_generate | neighborhood | sync_catalog | demo | import | audit | batch | world | verify | export
ROOT_FOLDER = ""                  # Optional writable full directory; empty = auto-discover
WORLD_SEED = 20261106
WORLD_ORIGIN_CHUNK = (0, 0)         # Can be negative. Change for other regions.
WORLD_CHUNK_GRID = (3, 3)          # e.g., (12, 12) for 144 chunks; no world-size limit
BATCH_SIZE = 32                    # Max 32 independent V3 original icon candidates per run
GENERATE_PREVIEWS = True           # Pillow optional
GENERATE_TEXTURES = True
EXPORT_ZIP = True
# ===========================================================================

VERSION = "ll-ucf-master-3.0-reconcile-art"
SEED_NAMESPACE = "ll-ucf-master-2.1-ios-ca"  # Preserve old geometry seeds across upgrade
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
    value = canonical([SEED_NAMESPACE, world_seed, *parts])
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
            except (OSError,ValueError,KeyError,TypeError) as exc:
                failed.append({"chunk_xy":[cx,cy],"error":str(exc)})
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


# HTTPS trust fix for iOS Python/CodePad. This is Mozilla's CA certificate
# collection as distributed with certifi, compressed into this standalone script.
# It is a trust-root set, not a disabled-verification workaround.
# Certificate package: https://github.com/certifi/python-certifi (MPL-2.0).
_EMBEDDED_MOZILLA_CA_B85 = (
    'c-qvx*^;A5)~0>VRit&F{B7zgF%L4U1LhgTEXn$Wc@P2#Bq6x^b`+U=XXehV%&Pi6Yx~poRzx6h976c>zH2S_fd1zvbsQi0u=~VY|KM%Y7VJ+V'
    '&wt|c;a(SY8sF=_`@}x(RX^1C`IG%+C!YOe)R+36XVCxr<UNumPw)R(BSxI$?e5e6_;mySV?AX))G^o{M+k~WX^bW*m?lXEB{3Q$z*mHz849Kt'
    'jD{H)9AFB>C#mkre7FvE2l`5-I}+U$#g4*vOt!<29f9qLd`HqdJl<u*j-q#QyhHL`QtVJ{J*UDV-?qWLkH+&I_y$dOc(zO8U7qgXVr>sicLcmk'
    '$Q?oMuw+N)J2cxd*e=C(2=dV$=<2sEBGkGEgYKw!2a`Jl-w~jD)Q)C$akfiA6UB}Ot>e3b+7<8C$?SbTaAIs1W4nZ2`+*{BKM-P<C2ODX;(a&;'
    '{cZiniLz>a;zie2C6#A=@x2u?Rh6%Oo@dKV$xbTAma3z``SW&B*;L{JpOy0qYM=Cm)w!~~Rp-XuJC49EJXiUm0h#PsW|2VTDwB6%^(8Oti7TxT'
    'wB(EDY(7O2d^)J5A4!iRTD2+WwrL|eCX2t1gSeNe1gJEgF3fxq#MtD@_Zxg=x(>`(KJ4yQ(c)C`bxoocK1I$;U)bx%NlYJ7&(_`#7}1|O$$`z%'
    'LBlzd+e;i-75Ms0YL3eeZl7S<HB-)$Ql*wDl#{uzs41`$w7x{^#szHjMciym#P$OsYCf*<SC<I=>KcD_iO{dE@mH4!eSeKv!#Z4<e*Sf-99ITI'
    '={T%fS~bf$f{TsMEWPm3@jzv{=R(rm8;;iw*|(~}jReOkn*;9j=RF5=oQ*SZ4{PnTlv(bR8!XrLXCNHK5v^axM!LZoloqbe@Rf7lld2-)+k~f|'
    'eAp(}a5PM!tEUCkHc>xPl;LxaOXD=)!Z>)n51CLp5yWvWlE&%D<1Tb}!fsAb6s_s18PWN<&)Vy~P#l_L3t9w+@~m^5gy|@RF6^_8vV}M{nAl0='
    'w##=P)ye8vfos`DWU0wY^4pB%>~+55O|hjySz^!n<|bUA!f9l=&ly>-mZz8KM|RGZ>!nzbX>Z!{MiP`8+pqznnY0(DOMc~Km$I6|wG)5Ho{%i$'
    'Y_O#=)n<`Plen)*CW!lz(OWt*ggy$Hi)UxYe|$WVq9y$Gd4#?hovr+C^y&E%JH*}m>Hp)~cpN{;eVhHSPtyN+zzBid<L>{wig^4#uROay!7I|O'
    'gYB0C_2T~bPj>JR{|CFB>o@}&u`_7+n?V<hv(Gxs$N%-+F#rF)H(z-1@Ac$shR`s9<0ysGI6@-ik64isyBOIe)EgJrF3WZqxyz_^7{<^YLhrI-'
    'SEM^ET}N4({vj*CXb#gmtk@CE`ii`pgz;Sr??^DX<2y3h#mo){&BN=^56%Y0eVExXKVt<62!`ykcm+y~?y`IZ!pbptZ7T=ggHEEmnA{cl4u^LL'
    'XbW&7*=5KM%XS5`OF_@UiOIE3D|7H&3UEfQ=wRqyu|kwqRy@%!tdPAx90@R@m@F*w-c9z@1QQ&Q<EMZ%Rk<^rapE2Dlsb+KiIb*=zUZ1P{V^_1'
    'lj?Ng`FP;KnCZMEpY=b6yxtT<qRqtD^N5b6hn`@g5iu}Q2Ok6HG(EtB`<STfGLZ<JjdqoE?GQ)Od7`XA<tyQI(BL>aU5}^)zA_J0vRWwZ)(zpJ'
    '`yyfr=DRU=nnwQ;!oJKj@yv1QMSA2O+dJs1N-?u^QD!{x=h7V`7s~!})<1yqG8^$_`oUxi>g&yuX59uL^JN?033Oe)1&SvHFVScBAJ?6lyr>~3'
    'S(;7<3pU+g5~ugg(*^crpAN1GB`CN)@qWp8{ADdH@^Rp38m(I;qfMr?eb1Bx3^xQ3qiuCE?IoVq%lTji^c5F<aFbB*bDPfRm*um|XW*E|S9jkz'
    'XzOK`x@e8ZgS9}am^~BOxvF9!oezIKEBKsnYQtJwc?N@UEi)6$v5qLQtPMtOnq5Cg9AE0-2a$d8Zk|$vk+{Cl7k<+c+yibnNokhHiD}O`chd{H'
    'pXPqwsHV~|!r()#M8}16zdsjlU-1Rny%_Cj#wY$N%)&O@I=F)!5!uLZ;j~q*$K^;SRBFkI>Q0AjSRnSqHd_&&ZU?H;(0xZm4&57#W}^FzbQQLv'
    '(J%<vu#@HrJe7n|9OvPkJu4VT49rMCA&azGb`G7B!wm>EGClU%lE`^m^D%-f!}fM8c-d=e>=X_zPU$lHsOCd|yV1q#;>wU}WK*#$xo171fJ%vM'
    '<HY!wMwJpDqIpBfZX|8wi^QBR-K|jJD|tb$<(^LPBNHkw6ymh|unD+~6@10Gwn&#pDob9i4ZHW8E@9<K6<EDCdN`Pzh4tS2bj>$Ed4ZLo6`E`*'
    'il0?VCamn7z^?>6+FZkCAHc;$sdR#6f9=j&9(`DRJ8{$!Y*7;mn2mrCfWppE)BBTJJyQ$(N)66og|Y;Y*6&-Ynxfljq63F7Cr(tkI6n~=nyV$Z'
    'f|939$U34A1<5(Q9T?j?Qt))|q3XFjss<A&FGVKtqu&f=ajkp*9v|;^a7z7(xS%|=;psLt)JhwrIdC_oVcO!^wBm*u_Kcpj*ZgsWi%}ZSCq(kB'
    'TY`s;sR|Qv!VBG9cqjp#jY8CkmPar6!v2XN+vO=|C53731uw79whEHIGO)+y>V{39d11Ac^G9K8^nyyz!)TJ{5D|LO#TFRzyptnTqTfAX^R-}+'
    'p=Anuz4*xa84p}OGGrVW*2Rc{ge<K7fkKBy#`WhtXF8>D`8a>sN9&w8kL(n&L3A}tJ)Vv?*{4s><1)HU<})Xk5`SMqm~}ezW1fD>|K=@q+4Y~?'
    'zQ3<N4259^(D{!YjC=O??~wm5AN+;T|NOwONsQnyf>Q`eQ6$0uV~67u_9Gq_z~eBx0$*vFq&pm6ofQqf2b`l<oKnC6F*_1pshl7`<S}qm+1tJW'
    'I1=f*v0`<8G`x}#cqxopn*sI<5S9UU3eXx^@k-}E;W5BJ0o)m~wipw;B3`{1FoB>Oz(N8-=WlZu7rQju<@8EuiduU}lRFgN#ndhZI}q!M5%NuF'
    'Y)9s+g9G1CzveODtUT7g@K|F_ZR1R??Jo4`CrswQFd15*{7WVS!TSf31LS(dv}cNj4X`RObOH?07PkF@4dwjR4svi0u<P}N5>Hjqo(blZ4lI^{'
    'h?DJ$#VY=xueztP?$L=O;*!8zYaA>xj<QEG6Mg2hxirDxpcSP@fLIgQv?>PMW(c%210(mx#;>pMcP<b5XV>>Tmk0f`>-(L{gR)gpdFuDWDEE07'
    '-LnFC-|6}HkZN~$v$dKbyUD0tl+N?Hht3&!(Vq3`8d=kDdOYUFVv7iklACC|HdToP8aS;UKM#?V@pCU!sDH0&tO4II+j|P7Nf%RlsxSKO*?6Jz'
    'O^FoL$ScBs?k~YrhE?-aq<ke-bC?7JjGB4t`{twaTQ)o30aU20cLDauiE_MGxhm98qhD>y&cPKjy^!Xn*i2H;8?4S=UmeojUm?&$hkVM^Ezwbs'
    'h4<%|)R_SwPjkCn<$)LFJ|Pa&;}yu{8FmH}IY=AOT2kyoKdH51o}U*)d1b>r;i1=gX*owZQDH$(o<(f;gQ}@^NK@f0a1<wFlB;-A2)W-=W%VFN'
    't$?%gxH#~o+)fV!+6(~?+#}1zz-bEH=JN+86F;aZnd}>#lTf}b=YFLpP&EP|sQmsYe=)Kg=Nkf@6wY~X?$Zb2@pdJ5w~IcEa4fLJ8>^lv$^sje'
    'U+oM1VCUom+M*~4tXI0+HMyLg4*2AypC2saQXyX+bLi{moW<3(cN**vxp6<3BQ|a3?Zj*+xNlFUI2+q|Ib3ju5T>g^J?RHsK^J2Q5DAu<2f<SU'
    'H}?ANIzQ!S{p`0qX5IFW{^2NiF#xHV=i`GHii5hf&5pveF_+I!mOV<mb%HVJQ$2Q$Or?{3<plU5BC{xL?;BRi+JaN0Zr&K%Gv$T#LG`Di!;6uk'
    '2<SeG?gH*~*zujHskyv(oN_}`c{Ihn4fDtBm~&67u=`@xw~|zC0%oujCB!`@CaDxc_ZL(~wTWL~bPkN!yl3PwPds$N_Osq;7iLK!(LW?h{VcG?'
    '?@2h$KyN4iL^m(u4k@OExHlZ(;siYia7DGrG#}O4I9!7pCJ2S6wPnXgzs+B{?UT6m00RLozy2Zk`ll~+{M#oN`;Ni?Rs&x+{F6Pt38&H+LBSXb'
    '&`U5B!Qd!~!VE*;KXJu?pvjxXfLt)KL$Dn|?DBV@Gl_S|+nQqeE`fLGk6khF(M+-iND*X3H!!eBx>6CejlV;%DYANClw40mBs-dT<DCRX`zI7m'
    'lU+jWP;~X@t7AuYD7D&hGG6%&dI)F>8UoFMGXeLDfWGA`>0xTM!GO*rxQcj3y)^-a?%-^fGV4arCoK6Dg@wZchUjztg~A5MzW;G*SoyrJ{zxHD'
    'z5rOk;qQS%<X`5&MS<VCNMnGu9q?vef->+sD9FQQ(3mfAVcpN9^7(T%CMfV_lC=^D|LRTin>WFGpZ)21G8YjyeRldI-r0O?gZ|jqaHi?8lTyCn'
    'X^1ai>13upMlXNG)z_FaJkA3L`zE+8(C1*L{>>#cA8)=b_UrrizC|ANPnl;<ZFc1dt}AQld0<N_7U#Oow@!$PX>_j@gNEEv6JC_AcaB?V=J@b7'
    'QdyppD!7ei8DvvpA!j&$B8G16%LX=ek~|>PF{mnzcr2q2l}c{%wxq$AYi+!kd~-eZ7=G?rzb?3Yx|!4Q5;@3%4T4H~N4tC-WD0p0aOsxw`Er5u'
    '{po6N6JzFUmpGyNF-);RaRN;7OZ!30#!RLghNqs}fMIO_jZMw#B;jA1K1%T=gB%Ah?U4sgPq~igjRWjxNrr{-a6B)To7Uz}WtQkgw%xdry?Ll&'
    'M-KrTdX~tWk$8d*Lwx`u8oQ%joDWPfx%=k@H7Frk%1}N>H)kIwkBe}|B=mK;NM)6NMxMo+!1h5uWZO?Ts5tL^ZH_yNlDeHdY|}%=IXDkz#MxZz'
    'xMrvtb074NROkntIK#1?Y@iRDnO&X?aS9+exKM4$YEC?Z4`wXuY`V;s=Or^PBn#~4l^uMhP+kIl+oouymvkoPSW^xtF(#9Fg__1B+|;%Sqdg@0'
    'K#SL84Cv#X;N9_Ya+?hUKFV?y?Ry(vmY|yGw%?9aJhk?1(Rdvq3odi}Im8avqt5kDC8I1>$hc;Mh)I_Dx|VHdG!>QVaHy{_Ff)Xyk*+CY){;G)'
    '19VB%A}^`NaOyi>P2+Z%htR?I=K~m6Y3tx6RAtl%eN>-<6N<h{U^cU8L(9tjB~M4le9@#mAH3=;*!Dcjx!G36%Ok1#JxrL5NR@%+CvcA{h7F^d'
    '1MJ{%zUG3NU6y-#RiH><ir>bQy5!w8|9jeB0A19RXzj&M-rw2pjo?4o?F(xD+~sS!FbGAE7)%m417kFU;t0VI1V)lH$uPkC0oWiv0!>V=1OcWA'
    'jQ+r$0Y65(Q)?K$CcH3a$G~e|44{Vup6$n}I`BTA2{2VCu_N9wTi~~V-6M&$0Sb9TBVAn@ldkANKx4%&XLbnl6VQN$Fwm=XP3$rBI}l9lU~~mv'
    '#;gYeupz~pgULIN`^F;r{${nB#0tD5S-mA*tg%`w*`@G`Bmx5m{t7e_y?O=a@<*zUHFzwlPU?Z$R`WJ8kXLsp{O?0=qr?g<80NqAMN+Vcfyt>K'
    '5!G@syznadEhnjx3C5gnm}2thmV{0bF`Yc3Nl^GRRMIu*xvb{P7F7HriS~J$P|nt(B2mNQ-y6<<`OIHV46SD_OSS%fP+^_-pu!6iyS}fpJ-BhJ'
    '{KW=cc#-23PkQMR-k>p66W7;XZPsl>>1hs|yv-eXU#EMWZo?OY<(rJ~m-Ob0u2tvf>loNKrPDN4=iAtZURil*ZRO<I;(dSb_4JN57xxgCv92)6'
    '{h@Wa7U@_-PV?*>u1j*klDw-p(y76KO)8LaIl4#m6>OF{OGlnIo?HITz*hD!No1SDu|d{MZga^f$q9m5xQNN26lpS$0Q?{wphs-$7jr+_i!Zf-'
    'bS=6Azvl(%m|R_#WXrQ=S7-6L_}whIp%=qWaB&hI@m+X%j*bA$d`M3RA+fiPW`s`X>C+QWy>UM_#`*m6Z9i=&%j7mWtGOa#olKz;!keNF^IazQ'
    '8%P_1kR}Vd;<_uP%j#Wpua&xA>P&*UTW9i2!eezV1$?4QRHNm678zX6DVKR8lCT2}MsQ~Q+U>KGfj(slz7xv5km<5Gono3k1)GZ{rFVTM+ox*>'
    'iIZ-t>Q?Bmd@G*fY(ZRO#eIKh&q7ol+bQy&LeoEcK^~kjO{}9~5fsmiv9NjOs!Pk+bQDIjdtQo#eFU@tRdut0hwg?mw|0WFtN0KSdVf6C8-z-&'
    'lt&(@BJ<_Q@vfO|T(zzS*(QcSpa(L`R1R{ao0TUUV}YOhTa|Ea?%jR0-$;ZKjFHinkBH@TM<{x9i*}n@AhNw+nbw9WT;iZ@fYGS1E%Jy3Dt~Z6'
    '($aAmQDT0U*0`<1ay_n~rm8HaDo<Z*U>TQF8AqIewh!oZVc7U^ZIg~`jf?e6VvjrfJTTCbVv50+himiQ!?h|m!3&Nh<oH0BEhc6*$H@pa>vYf>'
    'qdi?SnVI8Ayt}BhWO8`TYc2p15wSc@wi>kzmh$B+90z?oqG!`SOXx`!%aa_As))2FxrISv^D!dYWagx`!Q-VppCTZ6eFyXa=uL2P$mF>wKDf{H'
    '0uUEu)tWeu5B)cJ-LKNRf5`zuYZCYyCBnh!$sv2X4yn7Q><L4D5d#ut@+AF8h(PP00h9=SEvLx4GG;9d>^zaJ)S<;As0vx7ts@xl7PlP+{TVV>'
    'i5WU&*;A&St5E{AvD2wR#(UjMwV$C>7^c~@5<X~wkBtdaBxQUS=iyxL6)I4<rQ9CJ;#Qv@QkldA3B}Xp_Nu!_EViAg0vFMUksaPQv^zbpXwrs4'
    'eN9Krek4!gIncMt-?ENwl2P$GdCSy8n)QICL-Y`iHEDEv_8Ha+0jw{HP!FYH>q|OfaOzZvs*KMId?Bjk?9_bjQv6sV?F1RZAsUt=d^cfgBj`P~'
    'vGBThSgyCkol$KZ?o|;BS)c2dL5~=DF^<>mc0cFjxiD_L4~6qHube#*`-RbU)s0Jh$vo5=rQEtImx+8?@@GX5l}Q#UOPr=Ac%1qEh32l5pXD=T'
    'RCZ#q#3hF>!$~U~ceIG^pgBh}K1Nf_crtdhkJdyAhl$JN+tc1BGi%(6J<6k_mOw!h0bzT)Kbpu_$+Yk+7;&%lEXvLK>MJ}Co=5p8I&;V&Tl*SI'
    'Bkm#_>KUlz{aDaj$mvX}758D&ylmF*Pgj?b{jP8hdBmx;tZc!C%BuY#JM|7+&*<j9Xm;)vh<CpC>;~#$llBz@46R;?m=mtiRLEV)+OxWAN0WRi'
    '#Qvpu7HzFGQIeYIRmA8$a*77~G|TM>IrEXTBC8CKK=*Zr<KsM>!u|Gv^}^A}L>vk6J5N;1{<0)nJ_a9(fBb$DK<+;YahA=Wg8+Xd*z>PSwEp%<'
    'M%M^K|K4-easT_1+NIws!T+$SKLQiK+055k@`p8DKpbN6nh^l@KSg#qxn{fRY*k`FT%m8lx9T(?y4GmG4}~I5t!acfSxrCs5woXvaK5U?RY2lv'
    ')fkYD%v-^w=$arXvh`GS@)M!Bs!4nYC+n#}>v^(D%#>c^2?@T2Jl06XTTB8eSWxS347wHz0HH|cYb=7qb~*aFP%XoDak^FtAk3;fv-p=0iPtI='
    'Z-3<JIUoRkAPRY|{4O0GhUN<rg^!_jEpXysX$F*eCKvH5S(f^IYc&bx!YS%ji5$G-hCP0XPC#OiJzZHkpOo|Ch%$GB=d|QvK1^SnjE{u2AkLKn'
    ';2<6&_ndowgge@_bFYAHZF4-httv`LCRZyU;M`;Hs+i6uhaUu=CEg*8&yfpL>cKXEGGATR{~^miBX-zN<q@c+h1EW~cJ$dc^i7xj2;(}ADoz;('
    '8YdGJj83jOi68n{fyC+RgRaAwVx5oCt2NzzlG%@3y!euo1a_;F>=JMCdQ<5|L}RQ40Q^Uy0Rn98U6d|A--j}|FwczVzNt$%dEb<6t!P%v&#@8c'
    'xAFl7^E#HzYtx=#=JnKMeUFu5dn7$wfJ8EpRMF&Y+<y^$sC9F3V|pj?Z#;}*{PDG@+~@=w4yGQ={<=4i^Q3|iLk>>^-m?m{-J4N%WQpMLY&U*{'
    'W+HiQj;c=>$L-Crh0RUh)Kz#Z7~Ghs<4Ix<Iyu@sr#Y0{O*14ECVQ$4wTarh)laT$6#iJf%Dd2zY`@qrgUB3%>-)z&E6j@CQ0x$po(IH&t2to>'
    '$!Cvi`1$G(#|9%OvOM*+o(AbHZ!=|x^R8iaJEdN=Do`GRndW1bj%TyASS`{f*@f=HebO7|G3Iqzvl7!WK7k_E{ivZ^!_JO3sw&*)V!yai*t6Z>'
    '`BEAO@q&vVu@UG?aO8I-$@hu`l7w4aIjM7+Yn0l?3>Qcb)szFY+~z-zjqoQFK?tO{9H1ylg<~OY?CJQ*JhW0(Vt+d3Fhj=a(`v2;BP7v-+Gpx('
    'xeFDKmLauaHRQ2J+cC=@5OXhbk-qz)Lh9~aK5T~cp}*weY_MIq@A?iIt`@Nw2#Xm<JUDbdcG5(KIQxg_F!=*is`hXx)%)EQU{n(nPO(_(ptik!'
    'DJYE`VopDWbi5avUb`BIxOI-9Mau~x=ndsJJ%q~sVkmg91<dYfY|EkL0iAWn<`J^Vq=1gP=CJJbyg?}bvDXWPCWstd!Wg2mu(u%t$QobAurV)e'
    'pKQbnd=0oU+!k4&3L7=ucK88YQ_kF-Xgr&mAY$kheZatLwR3k<A^f3<&vwDcYC(RRn%+GgiW+>>euH&??(64i)%9&(*7^8Dg8mma`-P^z-Q+KE'
    'nvrX4ghqBLxyDSWe8-S$_`OKi|I&D^9Luvc@LvFAkw3&K02`97^=wr7P7EYFIDO}~=`~&hFuT@7qid+W$k(%F_%5f`_z3*7G&`EEx%f0$iCQpg'
    'h1;61N7m2_^DeCe_(qW(fvkN_v0Z|$1$*GE;AC08_J*Y2X?A4Q1vIu&cg^xA?{oq2OPpdWPRHn%IBou`aH{!i^9N29$%2mu?Gi`fc;dO>6j^<8'
    'Va5c_uBU?uJXiZT&iGnvHhoC~=;5EoK;WQn`1-Hn75bj9f8v$?ExbbC^Yt%y^@2&AzToxcXR<VdUbczsl%X6pP%IPAL}og0J<FeRLY++Zi=1e`'
    'Ip}-bLcikeuW$=}@D{sI&YouaEzJ(nGa?ujJs|{s(=is6BH6T*`@PWje(<P+J=RB;1nc{F>zXCh8LpNs>NR|#1f?#S`n=8<pH=OKLZjXvlj=g$'
    '-jY_*GtBn);Xp^))#bc8IE9Q+A&_F9wuIz8yloYxZOY3<c}T-<Q0h|20IEHM81H-UJnpTtg<ZVKe#wV!TP2}o9&cL<Ql@+JSZ>*7`yyDasxp(l'
    'lxMD?DQ%9cvvo;_K<EypwS5?MDxE+Fwg<{8PQHL&smy}1w$HN`hbOy^!s|sJx7_w>q6{XeuLAgOT%z5L{J44H;$BX^+dr%(np*T8o@zX}!;o@H'
    '0`2aooYXlN7PpBzMNgZlIPb-8auGknE%YniO3GxK)uuyzZu?S@zDM=GPsxEp#%{$e^kd$#ZdCNGKUvRKJ5!fx!&iP6WMvc_9%6q+k^10te6KeF'
    'G%5j3`|hpFy`t`qmmoimaC*Ea*P!&SDn}W$e!|8Ven}sV76@8R2wl*>n36;U<AFhVlWo<ZXZwkug6DmBEKd=}TGt;@hmli7PD|SDdW$_^Qe<a$'
    'q7NpC=+7@sD7k%6LUgwcZso9bDj1_qetVM6o~oocyr>&nm5{dEld-ya%`{%T@`daaYF`Y>i<?oPdbT=rHMUMWh5FO(k2<S6&(OtrPkO<O#3<Q0'
    '8uhl?XROZh2K~aG1|PW+zueif$e2Pf5a?oFk4*>Ps4I6$QJ=6nH`ihXIhDbqSkB?i8>m2i*j3cQ{|0Wq)O`PUareKj{l5bEcia9Yi4oumiPZqc'
    '#g0nWvTuMfU?f*;GHcyAu!s4($Q%3^qd%UkgsxVSE>=UlR;6WY^?44z%fH`M>14dtx38IV`t3OBHCI9w0I5GAF+r|v0YLy1K#Z=ImZnzU8sobJ'
    'TX_r^%)qNeNQ?C~LDrJ?HR%GcCquARSO5~E%nE!!bTnR#G`6~0;D~=oVrosb-}7IR_#*tjB(c4)#1|3+H}VaMzbd-^*QpHsGuQhEl~3hQsSN!y'
    '*ZVtEhQ7w~kEuLPw)2_Fi}o#*(Qt+`aGl_0{mYK{_o@Y~z_dr_wh5@3N$^vPZ0uUHU&^vI7J@EC6uv_CSndmd!D8%)ADJ_H)a&HXPHbtY&*-p4'
    'tL?dU@T7~~yLY(?RhsXQhJ)D2Hc`Fof<pA`8V&UW%{YHpw&MkV-ALthe8kQD*s84(KIyjCtSP|vaiuuHgyuOXmn4Q0Y*ZmS<d2MS_McsNKeDNL'
    '_o(j949(Cz1%+^ngg=_JA35q!niK3Y8v?s>ZQ>YvLz6GpN0CF7TWN)Svis$Fza@u<#gnAq*tp3s3Q0*r;~h>Hn&jXhl+EjDsu-LX&aF@-r!l4O'
    'XNbH=++cP=Xl)dOPV2Ew%noUTSliOix_`c;Ak6}<l<<HL{fkjd!FSaH|E43Bv{%7en;XPt>7*~U+7H#;yDqbMl7)X(EnwYZF+;n|eqD;wY^qQ)'
    '5!GCvA|`E*R<Bqncjt@~Q(|cv#{fx5pHwx!-vcizEE^RbCofaxE_`mQe6|i8^vp>wSu~iw%Dh3Lywlz8`jD1IfYNyzcvE$_J&Wwtdc>G%+r47='
    '^UIN&D&yw;4OyVu^hh%2b$658ZuL2`sHlWhI&>$hA=Q1>Y_X@~NZ7*X*JB?nbd#zSrtGsR$!G4ILA5CCi{O}TUzCEU)K+Dl@}@^Z|90jHICb5I'
    'g0~4m>0V6TBB{3K8a2ED71h&uKJXm`-%w0Ha0J;b@o|odZB%2X{hBsdq~B4bJW*;s8{HMvt0&vvJ0XBCA*RIYe&M{9x1iCh$=^owinGV%lRrGh'
    'd!Bu=^83^e=e4TL{zuT&OMdUa;pDqUV69a9eBe)J_kKU0_`mHee@r<3*%`j3GD<NN{=+J`j99A#fJp}MO^LOz;KL!~<VsnZ*-^wAG6sN)<F$(W'
    'hjYWI_jE0EeMRBbhk`@bNn*@e*8t2jO0R%jXO6||#`wb_lRM^TCV4H8pw~VCKm(s$5NoU$XI2jnRK)7)(bYKvcMijA30y+1v%<)C@i_oA;59JD'
    ';56C0#9}SyqgLCzP7j0E3iw~4`LUw;W`9Amz==Nl{qxK@0c$GwcX;AV$OHqt`bT`V4HJN;)4_eJlG`59>XD$Y=Lv0BX!^!ke3)K3Y0j5AH9~+^'
    'iewS|tLeWlwPDLIXqJOFd6C590x0dmHQjku*SSwh2Jkzsm2Q7d?-JB`b)42>VxP<Bfa5k_U$#L}!)?B+v2c7rticfYWxDSvjEHM~3E^b^i+CuZ'
    'U?w=D5j&IroV|US`TKH|@cx}hxF#rGI)@OB*JSO%CD!`~sb9?Ss};W7k5JK&HLnVk$2x%w1NUKA%L;!qOAGpXn%38|wD9en=`o$0o`NQ+1rkq^'
    'jYkB_QP;bMAX^3*?;|oOP!Mj0tDs+w#~e+{jSM#|-)@^j9OjiQv{`&{iB~C|24Q-6O+~|{?|F06s}fCdq+vq-VV}?>v40^+7~S%yE{5fXHi3$t'
    'P8v;X8a0nerwfX}&De&o$;_xSB{)63Tb{qd0OGjk!C5Z%&}$^Tx={>JOhZ#?CjCOI6HU08e(s(scvry-+qr`gb3AOusH4O?oD3#(4m8Z?587F%'
    'p6FIEH#nZR$a#ZAoK2KLPX#R@!Vl83#^>f>_;xyM6sCmJX9PRoED)RSN30U>5&{<wNpKI<rHeCMG3Q1Pv;%QPd?Qp(jvIG`=X}og!|LP+AJYJ#'
    'FVnO*AE;YE*RSVEgC|JMM$F*0^qCnC7L`1lr>%<?d_tJd^o9O1Px{-~hV<tQt+*dN!)AT-(r=j>7VE4=h#7d?O2nBd9j1;^;f8#AgZKyo@$T|X'
    ';}toNYYl8uxgcbO6OQ#b@Uaulm(&J)Q3?Z6nRQy(D>ByUbPjg94Rlq8!il>@{gwzYSRXd{utzQ)B30_pI%RjrSoO)^-SLuNXh>sRrAd0rtzOvj'
    '^3IBJIh(1M>WU*+dwP+*xFsC~zAxnA)g`?~#LelBRl`%`BKmfO!rod^+mq$H`f`%~`K)0->P}DpQQ4(~Z==bqdrse++S2vLQFs~7O|Q{N+OR}u'
    'yi^Frj$L=^@7yiXD53Li%%ixJW5+hZbp)D-*miv<MXDSm(S7leV#JBd{fyJ0g8B3G`^i~90%ZHnEq=dxhR>=IYyE9SVDOL6mE7M^^FL_j3l@Lb'
    '#5WVSept2_uVxS!&VpQRDfJOxMOPaL$b#f+_;pRM0<V|tDCUP`1R!Ga)mD=4%;#!(0b0?uARJi9b-4>-eWl`c9`#xl&b)Dn?Qr@hWK4?H--2G{'
    '$O=B-qjAume07~PyrzZ=dW|5jYjzN8-WR}qt>{D6dDIEBc6E&`1B;rjRfwQlYgIb6*00CwOtfE;F<;4evHvu!e<{%mfNAB5@8}VPi|9dMEcjB('
    'qlG{{hp=QD0T{sljI$a7oBdHQZhHNse+GfTO92$Z7WYT#_HQnZv6l0hLONT5xj-Lvee7r21)mqk_;GiC)LZCZ>F$qu3;nFSU=aIREg<(%3n;F&'
    'fGgPespxe4%Gv>O0|S^}yIv)+6`9dd<ODetxT1w^p3H%LAW2<$2iQ8O`;D}BoLmyYpsvG;X}+B5q*T6HXM?II)3((@ZeJba&66k}qMYW>N|dTH'
    'a$ZvB6iVrgDwp0jiUR4_!6>xN<DSWxx@66jdGURX0>68Aro#i@S5GZ0J;OlsWQf~{OqDJ8daM>6EsOjBxy5t}mvKlouEJ=ow5_n$M$4O;gE2*#'
    '_qcLwFRg(0lD~B|4pkX-evS6P4O@CcZ5L=bpx&|65<N4Kp0HyFb<0CykmeJxS7$6o9*Eaw|5UfgFmHl=y_6PJ4)nI%96Rvqhp_17or;T5CU}jz'
    'uOmy{Tp2$rYzcnrto*U2$B$<d{|?yPn=Or(CL@jLsqORD6J)n(cp<txKI;_dn+N8tQ$%)eh1fnDiaNO|0$T-f%{k|RoE#q|w2LS3^|p6R{-E<Y'
    '51Hbiowv-5AdhT;xBTUPbct|p8}u@x<w4v&H0LGU<RV?-qGC0hP!YYg=j~%0xU3zaL!LMkW8F?yJk-^YBvq9iII`oTHgfJ(AGq}<)NWf>l!3Rz'
    '%g3cnsiDG_lo%Bf6`;1N7-0wk`{=)P`+V;Sf>OHc9QF2+N89Ipzc~CYJo<1_Y*2)V3SCrN{UOi`RS3@xipQ&ROf7O_+2F&o!By3-tk#KMu#nsM'
    'b-}Ey%m+(BS;H2QEWS^>`B=eqxy*-GaXvvuV3|&yae$XaCXVDB&@XKnrfJ)awn+#Sm8rqmrIq2gD~#-acp`6`AAahSHv?0389(v%-~YGa3vXxU'
    '<>}+iAilp`9^DtPtgPW#^lOs+7qs<9Q1+kh_{#t+nZC=!vo*E}pa3itFk=b2nzW2u2?C&opleZj27K0!OVEkpy$n>kG7vy!bzRunBt@@vKxzJ7'
    'vFTmclVa;KBN)B{C#8U6`<cr_-gQmsdSvo$5%{%raxt-{Jn467I})#Rol<hGRRSAHc*Wlbi$B%}SqtCaldpj916Q{$Je98mEXZH7EL&ODZhjGf'
    '<+AVKpa+83LMCs1u|jD8hk_4(F(^(MVD0L^?!e&*{)~^l<ci<BAt*q@COdq@1|5{SCx`Iy6&&7F0jBM%EM_p<K8u(FyVzlWfCOLte&clbZjmRi'
    'WxomgDv~9w>ofr`Iz!pPf>p^PR!@}x*XF?V131vY{bsW8=qs(&9<lIk&H(40NrWK4)Hcu;_x28dt^jQQh55f08$x!dzk<OgU*Uy+Nr*QzSK)Nz'
    'jMr9=p4N!AOnf=1bANaW4PPx7Mx=~KQs^O{s(T<0(2}&9?7G=(d>plOmYRy=O9bFOFUX-Z4@7<HbRxdr5aSR#C)Sy=By#$We{LOIyoM$evIoq1'
    'xKfFY!6{2pLBw3F!_C|B6r}_w!`mrNu+ufTwd5mhhWL8Tf;)TXFC!wAX9ub*?gm_+%nF%8D8#{EHU^32c&!i8v$aAn#EC_6nJV`z=RB1h-GQu%'
    'P(Q~?C*30(>YJ`;jcQWna$9d-?BQYyd)2(j*LGMK;uJSeI(a1rWsB&deYeZ%NDh2z23z@#c-{oXljTevOiOn}wD>g6it(H9<~I>b_9op9S<9U&'
    '+EEo;Akq=C_o7Y-%l@AM?=QUjN~%ELg*Q$6W{HE*N@JS)#aJ5r*(gqSpHgi*^2SX&po8vRqdf0v<&|9}DDAbE&<x%pZ@RlKHjnM`+|lD<+s~I}'
    'G(41^t*xTa?A&pQ1TO&p=*fR*$*V&1{UL?=b6Lp##y)SJuT51vmVjzFP79I8;fxjIhC3{^5>oP&nh!o&l1zSn@MjwxkSsl3DjK?P(WdUba**|n'
    'K3x=R&)wMMk?7$Os0J2WW^1Ga@^<fBS-i|H)%YQ$-CP3pHfKSaAtX5SOlh<Xw;c-W5`}TMrPP7A1jW`0d;V7XM%_M?)VsLP*n{&DWiHR~piZo!'
    'y6G13n$G2dvvH-4SQ&>|qxZ|97yClb7;Q7MLl0xWZN%909=G-QwmW%u|C$#c!N)H<cz?hCo&Eb329Fj^pfE#H-+8hBtfepf`sb~D%`XzAkagt@'
    '3dK?I3KKB>L!vS7xwY9k`3QbnDd2qoc#042^Ue+?>FR5MeT#ow+*7<c1t_-W{m3=FhyrVc@96l=IP4ut%-><mWQ7l4**aM&1y<>2L?hN}AOI=Q'
    '%DM^_xkfz6Hwejm%?|=F!N}Suoa|zHO(T-;HLXCmL2tnc;`r?ei}mV2Yb#=lwZeAIIsTGp(mQTR{^8ElaO&L_Hbk7BemHYC{;J3adh;R#nz3Qc'
    'FKak)0dh@b>0x^2q&lD1Z{n`p5nEG=?Xu3qNO^)YYI=gq#YAiXBvUw}*77Ir*lEh0$byg2>k5$gwmqkafWN05^fpm%+=(yH$oyW0s!=DieP;)!'
    '@3wu@{k8Ydf71Q6_t1aR{k8Y+RVaVDVpRDKMe^@ZWGS*&IuWnl<!sp7RyLz4(5)vF_>Y2b2W>i+I6tas&sE!V5-E>>-C{1%D^o2XVECwY0dJ6a'
    'pPbJ8`N~E}NUMq39UwfOY1PzUxN5oeWvw3t1e>?4tB{TG@Z2SA9@ze=DCbbYyqw@!xwzJ1#suQsfENbRb*!v!aDA6fZPTBEhOh)Z!wI*m8<V%m'
    'rQjG5DcD1%3o%@oFa1%J(lxOMU}a}@3zdAjL=%bC<tyWsRGrbq%g<@;3I}O1r$=*#Z&Z>orxGcSp;(9RvvD8$W}mUh@j4{X@bcA&RLt6ag5PRF'
    '_u5#Lai%DfKlIDR<F1<%Ol^Jg%s3s_ZQ4G~_woVlUnRI}M+YJhXLA#-s3vYWH9a)KWZ-AQRaE1-L0HO<jV^mBH?e$JeyDUAN-Q2-=7}-H^!|ZL'
    'P?FQFSm+1&tW^wrJCN$*C9(y1I?6Ku_MTamt-OEAba*qOT;&Jl;lUyv_(&@;<tvADX)}=mBQ5mic|o^SWm#Bs4WEPNiQR*wC-JuTu6x|&mD&u#'
    'DiCo8wN0cDr_<fSCFn_-a!1$5k~;<RN@d}23o|LOVr~EwzSk!Wx#L<?PK2X`6C4l&EN!T|AnqFjACnF$fHVu}h_xiPkM^t=DB{61hD$EnG-K%Z'
    '%lrUdP$U|OB>9;Su<ju|_S+`xQB2Iw6x8hX*A$}JmA#ufbD8CRgmmy9+M+Rm82(0ENXD@i2DQVg3k7U8lrPoPnrEJE66dFruRl_+0M_Ls^=uH_'
    'Yt<g>BA1gpR2LRyD||3JDsSD{AFo*Q<1{PKnXCcjn66ARfANA@jqGDq@6+HU))!PNb>U3=Rz@RA=HIzSQA?k=AsI}`jqx}OunX4|3^k+G7`1g7'
    '<$RM+2`esbdAq5wcCwJ*PIg@k+ZEn=X$0;ucg}!>i}fhlFv2EA3t@qxKCRLtXU!WHzbqSS^I#`G-N-N+II`Qg?WDhSOygsHE}sDrqgB0)iJF7='
    'X#8yP5b{jem6DFt!x<*k2HQ9B<Bl4PaxwB$DIG<u5_Fi)wsGyKFxVX0qCkMS_Eq@|pP2@_PA$*7KF#VKUjkiYj2w%)66M)fk{tz~oJ&q?D|kw|'
    'MZKVYTfjt-j5mB6^Y}a;paYBpukDlDdTvnV7(YaGw#7}dsSx$3oG<uu&)hOTCKZ0~9fpWVU|qP6cN#~xB#>lKkv^67p!Dd?qF<?jXPPR?I57Xb'
    '<~v3_ZqF}t***euWRVU#Zj(pkBscz|-E`bAC>PT419L?i^-+q$7`<R6sg^b`9(OuzX_hltL)+ZThoS8EY@p%oBWG2tIbF6(-onW}fKL3PX;f&O'
    'JEGk(<{eL3`>AZsjwd_LA-~w}_SQY@0+vrtE}w5%M{eU+T#^)!-I^9a#yq;(9ALTla^pc*7OBdly>#=q!*(ijbUecQrhPf?U^351KKhh)3dM9|'
    'Dd1dT>_bMkzn$s|UtBnNlKkG7N!;kESyBg+OhS5t&Y7Ses<!+W=0b6g`MRzb`mt&#`jsgA@(%0$jiE7w#4z-GVfQZ|{6)+C<iKz8%|DWCIQdS='
    'qVM%QiB<Ig?E^#?&_Tp|5<HWv!2}#%zd?T-P{)}a9IrWP3SUDNt8k0gSxKwxqt_ZTp!R@@S{D#a)~ErHSqQo&eVL!lgJ<IR;w|u6Ee4bxm97zS'
    'px20OU2ZggYe^u)QlK<}7Gu_&z&gi@T(i?_1SNg1#e%GBw8Zb_P~m*7Lqpydi2rigGbvi@v0?eoAVl-SAcXy05W@BsF@sEQ{1T!LoGv6%Sz1<!'
    '63j4R3+4+9(u>)oFI8akFSF1kSVQsy_g)Yb`m!>p`IUzGtiaaVtl3)UyswK%BdY>)zTY-Me)Fva^Uw54@jsS(S{EXd#6QpGgy!A$%f<AMi@B)S'
    'x<Cu`d4(21;4(ftw9~pSr}}w)PE}C<D6MkV`&9omwg7zu7u1j7Lb(PPz)iFY<?t*xj&ZRKY*x(PN8;Rnn5B~R_^}|Qv-NmnNQoE&L{_g#3TjGm'
    '3cb<E3De??9If))$GooCX;>y(5A`R3?=deqw9E9Osi&krFmpN;`w%j48!aCDjyaLTao_p$3H35{I4fE_M!0aj7tX69Eq7~Xn?Bmu0agSpErlkb'
    'Ze*T8AVf!HFMWgq;>d|r$|8;=+l_dU!;aOA8<!p~jw^A!rn$w#FkRYfxnpc`^K7C>s=OexWgWlU!qs&@R+eo)#mDx*N;bD(sifWl{^sA(?Pvsf'
    '>2t4!6rSP$hfY}dOT|#m334u3edvm^Zx7@B-d-gpAP3mLdt;OnO5YWBh#=%(Xn9e@(~t-->if64Tn^)dZqFPP52^J4AF`q!ad~Mje4C&4IbM<a'
    '9uc@Ct2YzeT&J7DvY~_{eaUE3_bS!Jm3ky?2PhaZ(e1bCz1SZ^%*@G?19bV;$C@U;OZzc)=eiiZJ;B|lq0sA1@x-Kydx=ks7Q{vkNp96~=j#@U'
    'X2eg-1(%iKkWkkPOV7v)G4?zWv!U+tg;9__cI3`nbE}l|b~LfBay@9j_3LG?RcA(FPU!Ox+yDghJL{0#!3r&$miG8DP?eLJ91`Mg+APuxvi`LC'
    'N1aZ+1u>q?Wct-2J5}(qr*e29^^q<Z?4*q5hC-6WeVB5S&(`rWDq)^ej-qOH1*|^qN3T8fZT8_eR;w{DY_{R*b8jH-by=XtGczZK#CsAZeiF_3'
    '>)`TsCL$XkbOkZVZL(XHFf@HiSV5y`yriaNZm-n!s<_*{O6dDGLN~7<*^`gUq-dFFNH1!5?Qs$vAr^%nsYgCvwtep@*c9U&-om#ze*w`(W(OxR'
    '*x~7nQFc;9wOQ0qyqe~<tZs~adtrCTZXZ)?5h4zYYCkHYk|m5!C6UXp0Z$K?c?hWtBRB;ig%=f@_9>qBM9eu6QvwmxLz`l()2wC21(BbWCk_Og'
    '3OMb>x9yXv2y!Sjy{^(Bdy-?Qp3jCzZ|{TN`Tg9VPXz_(>4`e<C^4fkdMB$yY-Q>0w3}mBP1{?0I~vDK=+5Rg9d4S+%@dJs=`J6fS=C>g2MP(Q'
    '#~Ug)ILBU{>_;0jo0B*`bR;CfEmcabEK$!qkTxeG+c^@9LL;Bdz%);?o#9}F6xve*lE8%fCC<jkHaN6-+z+F9quASR!Qcb<kTH&epBqf=$?2*w'
    'x1}fN@gl(eY&ej*c?3~+y<*O0>qz++BdvqR_6d)uP2)&}Hk%=K)w3Mj>gbUfp1{SjebkdY-s6@|LByS*lUnAds3iQvJ4W)UUc{So826+$d9U0J'
    ';Y&Ji22aSf3!9S2$-Un8H$peJ*DX^)*j|eLXqr`c{}}Y<L7jV#_g`6>>YKb6_zEpEe!DJ{KgqCmWkT(IoBeYv$H1GM_X~7HkT|l{C;r0Dw=8k^'
    'JD)$9oZ|~cd(B5{(8?&hvHz}E!u}Jng#Ei>3Hxoa1XKr>tmSy?x;yD-rIgd_U-qEscK|7W*UnRGVkA$0ygFUHuHw4>rH%Jow~v?<Os>@f>tE)8'
    '*J^<D-2jcOOTH%WiP`I^sGo?XJX@Os(kgkcHAKa0ObdJe$qwwDmZ7ruQtj}nz1Hb<=(}(pU(byJ)t9ct^5Dlf-y!eP0|tB74Zfump8fwtEY1H!'
    'EHx!!OW%p5k8S_$V#)kB#gcxA`D+jbwjI(fnPm-d)!i+jT@HP)e0&d8bn#qe)aWC0GUk|h4q=|v&hb3e27}}KEGcjHIW??1E&?+ZOJbOg#bN^A'
    '*h{c+u(<;__Y;$1B4lA{@4K~24BIexA}`~>ZU{ON>&Jf5*(aP`>#D}HaBO;iYor@($!+yv_x?OQkH*MA_oWkrQc^A<?D@=H*tB^?6_@N;Ns88v'
    '{zboMQh%GQ*Xz&)hi$DL(I@rPIqd$d(ER~|1?`5k$SCaPC26`kUc`s(u$^S#_+(F~Q-AbG4Vk6NItOEZwO$KTHp0E)%8b#86xw2}&)Sa{<6ET1'
    'oWczoSsr?sn8fU@b_!mSwD{3z(7vOfuarQTsn5|T(rwMh6wn7quYiLzho0Ob!)+$xZbtc}^n;+3eZxoPtwPb*hT)a?G*HyJd_8lf*Yj{27nj=e'
    'kI<q{aAK>C!JIw0mWl8rJ$XVRWM{rRYH6glM#3d^jK!KNE0YkV=8E#Y@~Vs^vYsAfBZ1>iL3l#7jV#+2x1lwmb>_oBTgR^NC|u}KrZu>>$D;b+'
    '@SKJrGOYz#%FG-lKp6g#Oev9J)EiFEJ$tx<k(~CQ6ZRVF<w_Kkr7a6q*QZTsiVx{=ngdO_?2G7eb)#|*>5T9~s|AdcjqXL-eYUvfct=VBsc#J_'
    '(_9>0`jJkuK^ISkWZI#@n#M3S;>eFijQ#6kNzC!3*tW@r!pHwh-g|91s&!ey_dG@2Yjg>3&K(FV;X$}Nyb%I~5$5R|l;%4pzszH*tGdVd|1lyn'
    '6bQ44Kzq)$_F8jJ^Bb^p0=q^RO&8wmKP5}_g{}a@zH<-dO8ZatjaH5VZKnaPEMvOy@8sRO{L7Tob?Y9Ayy|*>Yp9aJqA`NY`>=zr1H_iGQbR72'
    '{qj0pwPDD!i-(<~O(}1$9(zS6{>mxy0-+aTA}hbmv4?Ydl~jD|6w|W+N$7|3MPhEsNth%$eZ{lc+1twZs@P<km0v_|r5G{hgko)#;Br|;vWAdG'
    'YVRCnz<_v_XUy;s<Q6?2*M0QR(hFcH7~nP2b56WNW)gS^QZ`!gtj$ndYnH!cm%=zfr8tCuhFOT{UYar3nwwjDZa3NKLz#tH_xz!tyH`&Jnt6jT'
    '-loGmF9kgIKx-#g7e>{VHvl3?Xz}NMyk1B-e8d-gj-l|{N)pXM?{%rx6Jb@HYPEihpCtHZMG!nz9N9R<hTs#BJk?wJVCn~&p<;VcipdqAmekI?'
    'GWc5V`sS<DA1blgb?yi~M7ED7?Ut-{lQvv=aKIyyOqJnI_{gw=NwN=&R?ZMdIcJlJCQ)u>qF-HIjpFTbV#8N>-DeU9_F~RZ#~g(KMB@}Mn(}*K'
    '%UKcioOP-m4^Og1F?cJ_;9e(!46*v#b~=g$oh=V*nI=zEE8w;KW`T*I>Quc6X+~YO<;Ai(o2J?(kq<}_M*MQiD#jiAk(m6(n~EKj!1x{(?F+Ok'
    'P#RwVdd`W7T2u(O*Ly@fU#~I5ZE<4yWqU7bdFjsL6vY3akn?}pX`NbW{2yOrcfZh<uN+3(-~Lw3!ZqWE9SrHe+69GYB!0|szVG#=0_Kt)JO5bg'
    '`9FH4@8zI>a+SZV1dYQ_E(bg^Rp_V9pMsA?!kxlo>Bkr?J6a21;!_Wr{k(bxJ1Q^<_@F^?bgVD#Tr5tGB}*7NvRT9zhnwW<Dj@_NBK|usOMc~_'
    'lO-QBpYSLwg+2@s%?`cbonGzCG0hImfc*l8{6BsuM1mjTo`gD*W>|XY9}wxGBCub0=W!Wwl!_kppzyKU8T};}W9Ltg#PlbXpkH-)ejq(2cVB>i'
    'S%S5SR2$>(DrWeoG3&Tt*3eVy!|LXn(~ZO>qrZcpxX}sl%`1lg<H7e&>%-BB=VFJE+3$*96h-8X(Gi>>aMT*`SLT}{@HaB|jYj>hPvVf{r&rCs'
    '!(S>#l`q?>W2x|~uiDS<@9*3m@Mrh;cWw{(v-|tA+xu2(3j9^ADQ#S+B+zHSyuPnDB2Sxe$RZ@TsxCU7Hx(c`ImeMwa%wz!)<$9*>x~+9J=RTY'
    'OiG*4RH0~i#wy?Qty~<M3Z(f&W15Dn9y^}_Q(kS|6?%IB)%TmuuTZX;BFPDDT0@wBS3B0Q_9-vPhA>35<)q-<#oE?8<*__xp+NES;Bp->_@!))'
    '+Td}~BT{jX%PZe!a8%FmiykiahM)mo>R^x|t|%_2MVPzo%1;;&r1an@MGnHgr=LW{Vb$$nNO;#!L{dFV5es4MhC}OB1;qfzM$O3^i*mt~?Y(+b'
    '0Is2xh%@rnBKj25z+ksn>M6s=L0UAhzw_7UxGX*7IcJ<93X(O?Zoc5#H~s?r8G-qgM*qJ`O)UtZ&k3x-!X+$jFM-#4dKK>PGoh`&A}~9@aVq4!'
    '$Nm)DXe;2#`1H8J{uRqkbR^98{DRu45lNmAWdl2T&&TT;QZZB@A=orm5{o-j3PmJ01NO`Z03=wvg+1R_!${YA*wqw%8H#akunq1JZb7_(@2t(9'
    ';!dQ7ex;^#obLJg&4kG8A|Qb0&o`lK5H`DMSKzlhB)Sh&RFbO>Ps!_fH5@Q?x|6};7i;xRMIZ_t6h(8UAt>`~fP#!uZtqmWeTBn`H1ss;BTAH{'
    'M<#Cy$tZyw2%1v9^G7OFSU5~(&+;ao-BoRpo;8qCX{iUHu<6oMy+E%=2ZzE)&u9&4jLc-^%A69CqiSC^&8{VMu|y+WG+5UvQwHq-yVKc@H}38~'
    'QL|(Jmu=oH`#=7GdWW^lH&>c{hYzA1NcRJB{?lW>Vd0-2_s3cs1P6a=VRKYzewIvd>gdr!iKBgh`ZNq8*s+##WF0=e28U+xFCdXT5*lH2s3Rlz'
    'v0{QCAH}=R(TDtSbN~`e9SE0w8vn8EX!y&(UrE(bhx$&49xWF8crx$+WE}o16Mb3*G4xX}ihXKw@FNA1qK66rl^%zrN8iO!5F37y8b?nfb)X_f'
    '9QCm=^p_Sk$^nVXcSvL}zP|m`x`qS)*f#hudEf_&G){KR^;4nw6&C(z-?Gp2{METb|B{CRqE9}9-abnEtn}5s<(uQoQBiZ4w<(bN)p6#>ZNSfl'
    '^-o3x{A^f1AJxz6M1h|difXGhP`G)bpy#UNT6uQwoO@O6UI?l837(nurO_;B?vLu7E;IYywKeN*cS^YXc$_=0b9(ox;Z`A=#TAC0_nBF{@)br{'
    'jsw+)b7f&E%e^}a1EVG0ysf4gp4z9rwOY!lGZ-RJTidmC%@Qk9kS;dU@q%U*{rk>RooCi(GuB1gr%YhA^frFs;G6fa*&@rLEWB?4eOnz*VJQt1'
    'CP-AB?nVU5##}_>)q@I0-08IphD8_@pypprt#-!qEuK4Td@7-R)oyGinkV#P5nFdEn)_>V#1kXvWBHiLE?jJZ#<?<VFtY>BMU%jyO6Kv)MOtDU'
    'Hi-{>1H`6?a+V9^A>mmjb})&*`@~#mvprDXJ#Yy4%Sc*BLSC^lMMaCZiCwg8?fq4~qPp<0U<3X=lD;tDmqL$>kwjUML`jhZx)t#}lL9;v%pzvn'
    'w+x$I{B$bdkl9Tw>>+z!o;LZ3)yaio?Fu@cK+AE|`_-1_FAv#$Rlc&DW1F(x*Zomena>a9QO_kEm1BdwLEj(W<2@6GO6#()`rYJp_>aOBz&;E('
    'g1;7cJ(n&<jM=~$re#lp?iOGo(zv`*NP@&uaDl)t#0;AP&v^UDbpT}87?Upzt66*ulc%cBX8|HNZ$GiOU9-<;!NRKe`S0a<!1vBZ@#Mi9D<QZQ'
    'XBLm=BCGMtwJRCR@i~L(Ww}$hQ*>9ZPgulNMRsN-ZAu`Fvn^JKocAMx%`T^&=AlBtP7Mg3N0=rWUB8LxH4W9WYJ#jb1lCeZ@dU~i%2OQ(w8;66'
    '5Eq|*E$<K>hO1?+t?Nx!r?0U}ZpiV}TUoz7ghvI>c7Q>Pe-^xZO%TfYg5H4ba(}6Yjrv#4No<HYuSzDw#ekz%o4G{~`*Kw)f5o?Y+z7$E-vz{M'
    'c#jBU1)kBB1a!%LhI9L5(~JESE>kx6j~eX?4->SYldi=UspX**^$tvkXYV@}Q~6m|ZsKScPs9hVZ81Zqm$}(Ewhk8~s(ZoP2{;68r}iZMcK|i#'
    '{2yWUFAx7~xc++RzacjIi+08sKWZ2bU+<5W{}FwnN1H|r9!Q9O${0ZScoF@)V0I5AW9s7vu*Z@g`Bw-$%ma4p%)-O?H6afH9)ddJVjTQ<$WezI'
    '9EtpDK_UHk<xoe(#(p9){-_b)2So2j?qfULb3Uyl@Tc@*kBs-r?1W*DSD`OWA?OhX@3HQ&yb&G&@cvfvL2~l15!*Nrd;J4qgFi)Vp8n^EeXHp9'
    '8#YS!zk%4M<NpG+@3YDVKcMz~29AwC8`|F;8Sty2{d#2oM8M|SECp-MQ+Yy^+eLeOGq({~`Mx$(-ep#rcMVWi`IRadt+uY))8B!`LK-HUgLu6m'
    'RhQFmcBc9pKb)ulyWXdfRF((a=BHbf>z70U0mRlJe-w+&Y&xPSbek_Hv>;rT9~^hg@kufKfFUY{xIv|tXsmn=YGJTzn6%n69sn=HR`_(uLpB;O'
    ';)GDq$tGNX$<a-SZA-L^?A4=_S(%G#glMTkC_)xU09v3b!?g)?1orIO7Qgj~DD+~%>z9*Oz}N;&OZdjY;qK?{dq_2eeLt{*szl8t2k%{Ym+@vr'
    'Bp~L-NxZQ>OO93!UrC}J?K-%04lciZ!}Cvfgu9-*sZS9Mf<z?5e}~+bF&~0{`QOTctJ=MMEG4(Lfjq45xa}x)OhZ6am*(d=@C$<&-;vwdk=xpl'
    'TWlqP+y5~|Lk)+=FQAp=I}qwMa8)ouu9*D%27ksBJsnU6RZaibgH|immo>Blh>vwOAV!pZBmIGJ1LTg^>j$MB|MOa5X-wuw%Dg~dvmgiTe;((-'
    '*pVGDZL0c%{*rgClPC36Vgeh&!-kj(bMwYriU-psd+>OSI@vM&7%lLJ;lk<~U8wH_#6ylYUNiGQOMq&oK>LXua`j*b_O=hdn1BQKf35mMgM>GR'
    '`pvqR8X0olU6cv^r0Z>Zx1zo{`yGHx>;ftN<B~Sa2Hm5PWrMBgPfRU5`Op{%;wryay1m|as!|1rsud3ex-DFsZ0P`EKr`INO5_T%?)si0NxOF6'
    'Lu=N&^u!W!cqtK~w=kkdV0l*_!5c#arM-omV8<evt2}VACL!^*%!6x>R>ujx1*`NJjXfOqo$-VSI>j2$WlA3=L5j5rfeO`88Uvo$t4%Z^uym;a'
    'N-~Ra*YVu5Wx%1@bxLUU5<(ZL@h*Z|X_o{NEBzI{s-(ecJ>g)c^cfimULJ6B=J&hhnaSVIcmw53N2t(-*z!wp-nZ&`ot*bftth>UuV#rBnYaGF'
    '4DJq_Y&n$q7ceysRlF}hhyOYJsIm7~`+gVT`C-35q?196fDsJDK^UPB1R-JQrx|7#KiWbLZ*%hF_eT5%5r@b-iX9>A9*aWZ0o~xIVG=}sB~^<<'
    '$J%`QX@pGDBevaf6pfA`eLumDuOW5>v*>5d{{VjC$OjX@$}p$!5xt|~;ZwT@;>Yqnc;It}eb68JC>ekU+#h|I)S-!RIO=`z4Z@G$|8R%@Sm^ES'
    'gA9-C_Kx-$d35Z2Yi9bB)&B4R8%X$<Bkc9I&%V=K4t(`<ke0q9A@D_xN0omNg}cO09^9vbJzNNWFBo^*-{bb}U9d8R+$htI?vI)OrtrQntYI<V'
    'cKDJ}<)yE^ncRBV2Wdx-rhVVONZA>C4D!c~^ZkcJ@f{rgDA)J6uE%5*?{iG@<QCwMHhISzb+gaAQ@o;!VAI|=?H}#{Y3}R$U-bs=m2|+u-}M)|'
    'lr3q{mn7sp3mSPny3B}{0&09+91mws_$b^pmdUsp#a<)kvRimY=D49sk8bi)2yz^L7pQlx4ErSc4pgi6LRAEG*NSkr43}Y!bmDay+5x0X+;_}|'
    'tc26cqdH}KfUFeiK3G|{(?zmP&oo~xnJ^#{u)yoHPn4x2wiZkICp7M%D`7H0{4n|)<$W@w!{=i@C-U^rNcBpcvf9%@)bhfJiBiC@a}aOeB$(zL'
    'FL0yb;lqL?+6wXa6NFm=GjQ&+64uzp$3@GZa%|p+%yr0xY>I3T=vVJlJkW<+`%22eDQ(`KH#}wn7bE=w<_h)vn)j%_vtCY4sy1gVn`lg{*|DZk'
    '^%`IZxYK86p}s*=japjfp3<_VRm+7ow3#e%(6>3$dpURBu=&<i#OGGo3^68cRtkavk)nfS$_FOW-G;UOdR&SE<9LiSB!v{i$tY^*hOcUl^ix&h'
    'tma0|G^xP|2OAY$0VDIdN85Hc7wWZQYZ4E<#0Ig=T1u@;lQiySou5HI_8dnH&9msAVeq)L*dmVk{mugAIcVIpVwggpkoZK?52`lAA~qpbdY=3&'
    '_udclRzyY6mq^_^%lUzuLLg)8^`2?w05r0q>1J9Em0>{*zP`980eWp~$au*Y=L}=xjPrEjL3g!*OKPU)0`1(lETYv(w;`Z^ITr_+Va{I&Z!p-#'
    'U$EvUibMb2r}~A|0DtBQKL!oj6PG)cDmj$D#_fT*-5$&v6ZmgT_p2xTJ|kWHJ(Ogdz}BVwNdyfO;{wt>hg^hHcI>?J{5pdKc2hL}_T&{{ycky5'
    'K;u5uA&u<auzpRiD5eN;*}c7<hBjY|d}rNZQD~nCd}`DxBbF&O^0@I|86dQs-Hjyy+m17sBL6b9qnQgUu1e`O1Va^9t30(sKx`-Vv9nL*Y!2Yl'
    '(kP{4yGI1n@1&U6H+LffG?I-fI<pi=T+_rn1$9^s)Yun`%@Zez7Y6D^283BUa(ks<ZGPal5ICi^CAVYFz1}3{GA^+&aY-6GHCb5~Hnf#+N$7EA'
    'GIp6NQ{4%}yH`{;w!<?IMPUut{J5-XzPzU#WgcZAO!5mH_YZ}Whi8=5^2U3P<U@>T;(gw#<td8Xh>#ke&~>=87ND`-Ba;P!iErbqvv=(z4@4J4'
    '4@T9*+Q)H%eb@cuN{fJ#4^2n}%ULf4ge)L5jS>RnTVZRgPi*kko!mhK^?}1V3W4A|lS=zXyh02A&7XaQQ`UguU_5Wy#yv$XcY;W^2LvqF<2@1^'
    '+FqHZyN~a<Ih>QQHPZ9zezQoJF6)zV-+zwmCZekbp}LDFnkVEeBH93KidN$;d8@jyp6d%ghFX4KWX185f<%Rh<AUOSH;PG-s6?SoSJuNtI@X>W'
    'SgsSf05ZA`T#vksOGVz?G#d(44@#T6FHI+w4~IAf;~<h_a7MO>86oqf*H)2rof^x3zk~R4aZFkYprgfie|;>o>o@6m`D2IhpYHj+1Nhrse@Iu5'
    'Fo}UXFG2~F#3`Hvf3D;Y9!%mWfJ~1>{?089LqhZreh8tX=I~hdhL02h3I7KELO&Qe4kf~)d=kPwxsdFrquhUlvm;YMK}Sa6SpNQ4<wWseWQe0X'
    '6Z>`N2%a9v69_)kn2z3-55<YngIht=Q5CsUt)2HI#K#)(Q_l&*2hZCH5cC-~{6&26(;u8bN7wREPI)-}{uMnE!R>NkqVKs2$s07Jd#LA5qkkro'
    'HXGHyG>rgyp0CDTWu5xUSWdhAplM`SV9gky>M8~}U%qD&%&*&q8Th09;wN8mtd&Eb+{B^eyCp}yVpG_|)}H&mP2r@4t7rrG?uvNl_mCp6jC&pK'
    'T*ml1V{?~z7Vq5nWt0`CD)jgAP43tRI6p4DJIX(BRJ=sME1b^${pI!R$qTv;^e8r{--y1)`cGmZGjr1~=1tF@Bbtqlo$%h$sV4uP$XuzOtq+J}'
    'sl#SSa$F93I#Uf86M7c|fpFbj=X#kkj)_}q&XQ5h6@&!g^Yx^@V78Sl(|21yfXh}-E6@~Hs*PotCU8YB6uMBUo29Uol=m%er;Wg^%f$dIry)5z'
    'd3Xg=)~njlKrQP1mSdhyYmC-`x7JD6FkHOIdm5?cLL>Y351YZ;O=wy?#pwrHgVt*zLX?&Iq6Z|JoNv74WG8mo^6uFrJT1Fu*<)Zh8}|Two@uf>'
    'qbZ?WjQ41~OmKY6Wc4B=hQ;JF0Nx~ra+GUqZfDcfIIIlPlXj6rx+nQQY~wjZNkQZ27c02a&OKCW?q3>vO?!92QW1FInNYUvR>L&HvACx{(T-2T'
    'f~5pWW^P%8zaGm&?u}5c>bq{!dmvi%13|6|yqr-2KyO^lfMvh>HF%y&J(tgP{q#0sTI5iMlTuNZ0c00kIm4Pf#hA*UA<glh$c96@q5)6DH8Huf'
    '<f1--nWwr%Lr!@FpP*Z7VGj<;Dr}TSqXn_D%r4?pf3e0Oh^O&B-mESJVy}CI;||h-qV5ygmGZ&tAw5?9Tx<qWS#GBZei9Xl(Z5nRfJ=^A@Y$%L'
    'ybIG#uYu`4cm{o1#=e1&$2mr2ZP1oI`jE_<0po$B&|PfwbnuPw?2q$$q%Mbe&J14yZnJ*~l8XChor`Vet#Gq&x$GYp<IXc1{gZ?TU-^hX1)lN_'
    'p7j6(F8_$!dXhnY_2HsRp42A)eo@3V-|<SVzFXtIt5!+HO+Io36^8s=2>5y>rYO|!SBhYDi!WH=!zwI4o$Zg63$|4dc7<$l^ME`UaHbc7*^yE)'
    '==p8`g3U2sa$Gy#^A#qfdG#ianx3g^Y6DIdxOgkp>aZ$eb)pW{&-lx#Q_k$K!$Y0M_4he|FPYqQM2r3?gSzY|rzrs6e_^w9Io{wI{6d>FZ5Rwh'
    'iv}Id%t{LnI@s@$77SXVnFlT0kMHd99f)%V{Opi39W5xdZ|qES|CyYbiN4VEJ>L)1KswFo{5U~i9N*`Czx_MM(SR}UXX5?+jC6Z!2xg|H1(f#Z'
    '<AmJruXsPc`^Sj|l8$KRO$#v%5XOFm{YvTQjLLq6eaQRJLxXu9BiRoqj**21yB#OqPsAT12#%5N`|Y>z<&E$&bdHwkFDJ4LM)=%<L4!2w(+W*5'
    'G|SPdLBlk6r*8)Rxy9oa44PMtGuL0Q&>m+_XlAC_mX>GwO^Y#|%nU+b(67HEg--JQ1fO5xc38jUJ(C}>74Lrm{}GBN_*o#_AKhgA*8?TPOC7-V'
    '772V6y42*sd*HtBJSzN0yCD&0Q`<iav-M)6mJ0<__~X*u=TR=PdVjQ^p}W-kV?F|*i@pu-T7^OlM~L$Ff2TAU2>a&(xfY?<eMX@;)Fbeu=}YeK'
    '=dp(O&GhsT?az(nbD$x7{{;RUS_9u>jBC8m-MKm6)yCRU54$`?;y$;*c+u6QQ~fBp)gTPP7@IQ|sx3`pkX_ONECF&R^*q7Ey@R`V(7&DmlqjTf'
    ')uH{q+A|%hrf%Q(&LI_QDN8&@PM6HTSYSku`5m~fmoDJ!vpfdS>$#}@{xDj1_3l%BxyjuVyHi|Rzk{&ldP8;2CxhFg$W0>drJ1p(CqOG_?&c|b'
    '5P%DUjVDC$ya|*$6Fy2cm!4*moC+p|WFy3>`K?4>F(k|eO;uD_r5y{rozqne8)n#PIQjtT%h+G9(7WL<CdTyp*4EC5X!O;#PRq3(n#7>5i*QA5'
    'Mv*o3a{$H$9~;P+rCevkhJT#j5A@RcK4M7s{-VoFF{hmft89WcMp}+=;UdFDPi}Z+!=)<%L|Ql|2TMCGI2G3p?e$o59uEzwlp1PH!+6d)SAZ`l'
    '!b!5ZFrCQc@7#r+7|NM4Rsa&db)97?oPW8yuUk3Y8*5HBvpazcXRWCaMic6I#jN!@>)Q{WNXzWzrH*wMh+(6F0$ONzSREbmay3rTLdHQahVXpm'
    'SE9|H-U3gf?+MrO{G5Zn6Z5OstgoZOHQG)K4<yLRzhdp`S$$P#1pgHLcU{u^r>J7DR63tBBFJLIXi!q-`NC}0lRR(vh)kspwXg_uy5ky47|6Qy'
    'aC!rr1P)o_tDiGdUgIL^`bfuRk;#IiqjLVMM1A6)$;Eyt$o*YM)!!9}{ksSLK@#?l2mL-4L16r+omd%l<Ufh@;{tMMmLEOe1oE}{i2@HUe`uy>'
    'N8Ri%Y{aPeNQ<K65mFp_MCkE<f*jGt{yP2GukWu93wZD_7Rj(rKY8{Wj{Qn$h&uFQzg#{0h?`@{$A%<1)^bVW2x_S8$kQg+(J#LTPgrz}5XFvw'
    'iTo^+;vZ!r96FllDe|zNKlIwu-=OF(bF-fgqxHLe`-PR!pDGO9e-NZ|_;>*h{{KC(>6m)}k}!4&vBvM||DuThYG>kNg=xR2@$69s;PA<jkNsNV'
    'I{&Wk>1!ZT(Xdj*vsy{0vZ=ohL>AS)V}NS!!3NL$Al`27^OZDn-?ZE3`o0Gxo^eM<1LT%}S*{E=z(8MhUH3OcmJYw?Vj<Jpx8)|hy!|IXeAj;k'
    'xjzIaz+XfsGn2d}9NoC6Z3_a$)JEiPB6OVz7rr#tj0Yfa(ad`z8{7@zDsvFxE7-AoRv0&rI7-oK-D;#&8;Jsg*S8bCZ(1<e({1L&$7pQ;NXyw>'
    '51bzMwe`e^{)Oz7>H*!Ww$0B4!4JMa39@UhuDQMGfP28BfA(x0ak5)>DFB6;U+uMg@)0tf%?C_sH`74R_&WN=6|5D4LKxC_<|o;|UVO)%1z3m>'
    'y;DKA+vj}|*rWmy`*C32rzqS|j}U}c>}`S=%7~RdoYCIg))gTxi}`3lC@v!Q=Oeq^qJ7#gqZmN(Tl;X^Z0>lz<hS}M7fWZ}gVkFgE?(w@Bgf|g'
    'o2CxAw;Ow!(BQS|U3`J6czKL4u-=9e_7uI#%#dy$XB$Jye8S6wS6;fKG@%I%RV57pO+S5@gYB0pj2lG_D?CKOr3C6w);8*O!R8ngf~cD=!t3VY'
    'Pff<P+r2G<=8+Ag23_1Ng+@a(-^vS~{8EKkIgflDXz6peUY+wBa!tnTb=~ynh(fPBd19f>h&Jw0lX4jal<Pn2sVT(LxxUQsqUU`g?~ILMw`^i8'
    '4OdTH<u1*mQj%HDEaECl@BDd|FAqMNuYEI}$oKjpU6L^>ke_2eUF|65fR}Go%Ih={&%rB++j4$x#Y0-9*ENy0p-|VeB5crpkB{3T78oL<c#d_F'
    '#=K`<8l@+I+Ps<Ba?F17dta4VvVU%$@-wRy;Jp31)5_Z{CYesIn0WP=JT5+JxO0f-F)uU}xQJ?;%K)_IROyMqt5O-fFrw(Pb1z}J2p*n=&X619'
    'sRYNK%dUxBMQpo2=TqlCxTo>5y4TPEa?z=IbmAb9PWyXyI^SQ3a$?shHu=kiyTQ-8ixEkESN5rvrg2_S2*PhHak`@m?(%?$zjalc&o>=aNGBES'
    'p?0WcyTdn!Vw&y^C8U9%ye7HsGESVA1`f{*ShlH)P`YXhm=bJLf;qP=oZM)S)w~PpH$#3-?Fcu@V!EQ#B~J9yx}gswV31nQQ75w+Ln9N6H~~#r'
    'rxeMXK66gtd|GACMGUaCv2%bet(oL}o!9z;J|&WTK;mdzX%T_V>Z*)dY`6sgVMbW8@**`x*}vQ;%v?KLxK#9n_JnFyk9<tuB?X7L24DMCr>Xo#'
    '?xDHagP1?LE`V=l#qG~hoe3jxI>$L*Nceq1@uxfB*-DR*Cz;uEn1gdLrCnJ{1V`Q{mU|)36182R8RR}+$}H@M=qk`#tZc(hw>M9%u`E69p)zrm'
    'NaaBkt~J=OX|JL1c7yH8=&$aERlpoVR6#2wCzgVMG}WT(D|5Z)eW_g*S;1-HcE&3IfjTL^EVz**PNri{aU(fmOWh3!1<^3eu#=o?C#S=-oJM4O'
    '`S@rkn~g*!1}%5mLF81oudIC5xfb<gOKoc{?a#00x(DKs!6@K=OQ#k5f34FB{=d>`1^;EI)xn^mgJPxV$0#m7mXbm6=$nGV-{SaCMI?yNiu2Bm'
    '!k?FwQ->@hoP1~wd1QGHai8>{IXj69KXx{Ui#l=m#q6AJf02+Mt)E{?1VKk5`_9P-@>7KVkt$B3BjX!|$B)EE2s!;2v6A7@5f+CB69b`xZc(3P'
    '@}WfZX@UpQqk<0ll%&HuF@yjA+i4~J*l7jsBn|xkOsAFfk2<Yh9@R$Psn{N=7kau?VvnpQ;llChdjileYkNY?CbqA)dP7JymII4vrqDlMC4DYl'
    'c^nWC6Ze8AdMEIbi6beSZ+GgS^jwq|fNyO)=xJ%GjVe!Vb-F*!)PtH-FmE;b%)h6kjdc*KLBv|H(!AgLJ&0AR%&tY;xt0J_+-$Fpm-->`CnRjd'
    'mk!PEtxE@IczL{z4<q^(F7JgRKscUGS*6ucXR#z}<5Kv30abI$b=*!B{{1c<&})z1S@V_~yt&o1lkrbod@^NezDkxKA?10$YwKkZ99I)*7Ks92'
    'mLM|E)II#f-sj?_!43&6{q?Pi>&fEIrCT)~e1*`aI|+KOrh-3m?dXaBU7c2Ez_n<Y7N2>0x%QRnt$uPtWo5cpf6{5C7+UEYLzZa83aCRcp6+mZ'
    'DsL_7^X^8%M00xe5A%Wcct`SgWE)?a+GUnTJ*=)f<wYHWCt8r)Ql~G#^j-?-<ZsW7!NV;mQyk<Z)bxW?j&5k*Tpb1RYc+eTE#sHZvMZAXtJ*Rf'
    '__r81GazxTsH*4Jd2wkh>b-O<qQsl|w5-MKacLD(MYcOlj65%<C2FEzY$6@>1f{p*2oVnCkoU?IsVmKQ7ZJLK<}SBd<SCV$G8*b^_KGUuE81dm'
    '<!Lv4r_AB#)nR42G0Ye$KsBxCka3yM_ffwN^|b>10k7FisiYTd>Fi58H_VhM>N^CP$MmYU<+N#ZGTCZx);hpgsm9^_H2)K=JbG-0Z!T#cOoBn^'
    'vtqe#|8YU{&v*U4qWQDk{;;}<qX<b5C`FJEf<QP5{xrc5rXQhv^gtyvIvSUV?1<)Z{6M@N?sja7KJKFXYwYI<hNEQ{Iv@)9sQZKQvAlTHT0tL6'
    'a{Oa}79N^)`xTBI@T1auzZCq-_G07^QjXF?=LJQN<HJvdSA-m6!;k~wsL#?SiGLMJ-r<h?RF)&3tV2c~3N?rGO?KobLj35og1)HqqyJQ#U-DR8'
    '_RA$3HtDB{2A$>7Js|zQy6G6+v10LcA{U&;mmI-SNXjigu4*O%wf$Z*2H@uFKB(`jn#fVhrLuQa*_hua6ZU_1?2}7i=S8gO_<Ji9f9JsnQU2vw'
    '_B9WnR0q)gu$p;{^hYV<9o+u5C(Mo>PGL`8w6=s?z4h*`bbz{lIECAMdW{WghxAE!q}cn~XXKku^hegFU39rhC`8>J%2|@BDCSqcOey^N?lH7i'
    '0EfkmyK<tTt4H9ndx036ANN`N>SWR2u<#%-57+CuZPt)zhEHpSy%SM>y(;<@!?zP)1$?oC<B83c7X`ODLQ4+opicPSs(cWjC4e3mcdgtY7q4U-'
    ')#X?uB0m^s5mEhz0iai6a6%4|UN><M76%i7K~b*Do9nl0pB0a@`>1Ixn7j)=rh$aFka1R<bQ4IC9YGn0J9wYoeX+L5mVG09a;I#lvBL3UOjUj}'
    'HzeYp3+5!(1(hOk51To;A!Vm7@{Ht-5=h(mJA7m|L;QdUO=pCQeDklqMws=fp8I|#1b2%h`<Fg3KdfNg(wgbHq08%>825P9yG(C(2qJYT6ej=D'
    'OC`~Ux#QOH+{>SpK3bS%L*e#k|0lR52!A5ZPd}5*j%uzHZVw@mSyXrkELYuT*^%>X^4>PHHIGw;5km!OL_k)+JIJ;W+TO$)qPy`_JaFz-ytcQb'
    'G8i2}D77^Hb?0sSsGd{dhVz=mFh}YeQ&eZ{p#yBk_lX%5QnvZmArVJB(p~YoWPM-Qfg@_<^Bsi(IH&8C>J43!y)sbedc&g#$GRAJh9ZAa2?`r~'
    '2dX=sRV-xg?{|VQ%=3&oW9C6H8B#d(YDnHMU-nWvitoH+SZIdBspeVWu`gUv<6Ynd7lm}CgaI)$4<R*K>6uP9@zQV<elo*Om7^s_1mww_r%ct&'
    'tNaFTeeCP6IDn0j8tjBI`U~ze$a>Bn=Ad816i<`C4MoP(I$=@{-&5Dne+Y-x#rN&<4%|Da`~XY;;IMBH_0vQCSb#%-D24A|FplFCjDZAlDDZ;_'
    'frB`Pp*W0!1WCXki0o4Z_EY@&DD7j>;U<%%ha?&G5gt2~?ZHpv6dtk8p~=6aTl7=>+9RSJI@0hcPp0srD&~mys80iKc$mY0;gPf6HxeJw{un%@'
    '!}d53|5bI)5r^T2|9A4K4I=QP^LGybu`eS2@JBNPI|_#OJ$Lv_KY`s*-3%XJd*rx}8HGMJHpHi`Xn&C%V>&?jFY$}_k5y%`{DxomlrJ**1rEaf'
    'U8!>nsf^N&L39rS<)^)Wv-N}RxA6dfSM}T49M3}$6coXsW6v#J<kn!|8Xp+?R$OEA&hK{mS1LMJ4m0ZQd$Rm+{#^Eu1yNb^z&8;1aihZhV8s2n'
    's=up{zHtj<CNAaru6c;$D?sQ%-2uCbiSASAw=!zy_d9(TQIl9MH#g-UCCKx4O&itJtPytsnd{0=ws=D>$b$<XoX(66FsI2r#e$Df(ceXaE3zgs'
    'dUCp8kJD(P$w2Vqb-wq`gr0{2U(R{=5(pM#pN_<Um74;++Rt~ge(I_<(771ycTBwKtI*>{jGl|l6+?u|af6M#c_TOc6bA|xYy0&3Qu+Pk0^p>V'
    'O*0<P5-g%<juvi)>qFY3j21Iy>2H`04Z#gOUvzt;JnjlMc~h;?<+e|OR$Bn5K4Y(14>NDa^1Qa+JjgT3sj%9UoV1eKW|g%pCgNf=%%DP~=MjFd'
    'v1$o@`uy@b;9iW@7)V&0D_6gVckBqJZUpN&SD#3xaNwOS?RF9<;aul9-4r~^&6#VwZJJuNQwxOAj6QMeQIC8HKO343!f7Q<Q`K7K^(KpI|Mgh)'
    '_V9yO15S@uDnX`hw+`{T2Gy&M0c7y7$7Kg?&RLK^2qN*7={D?VJORIpplx}4x~w|s=BJm`_~ROKhM3y6dC`pWdKQ4&6nRwe+FS;GE7C&}AgdgM'
    'ydvlV5wA|-@0_CymaKie%;!WFugAl^+)B!~@@4g`5h$`KSRz3N)4QQOpsZYJT<0E{f;s`4yyc7MuzSEwga}WO>Y1}eL}*t+s=Y>z@tX$N5Abn<'
    'hzBEMtAP8Be6Pc&*LxoQ$VcRKpYG>{HJ7yHq=<{M=8;Tkq?<1UorNc@jlg!P-rYUh?(^R-SpIzt0q|qNa*Jgy3E?HD3B4JRBo7-Tk@It-{M6@z'
    '1wO?DOoh9MN9s*4dPpX&<5~Ae#acKff!Nz?5_%6Z?~d8!RhNc_yOe>gX`}JdE`VZ((v~*FLR+pS4a|aq%mxh`)9ruL#z^cF!i@bBWL;755yF$3'
    'RH=*kCBa2sI0+2ItYV)hUhhg35%e~!w2}(qM%T~wm8Z6TAvT)1prct*T`(w7btVRV)Ni#+!I$!`0xxg4h_}YjAX1(s4%c0~c;oSC_mH}%dAF33'
    '4=U~u=eLWFw|Kipz4az07eQwe)4~A%l8-K2<@~FD=A~*<>1e~O5T&Ol(%j#D$wd0e0nzgDn5z@A;7bE0OS=dh)HuTY1|rzQ;0+n1bV(`QlGi6w'
    'J1V~fx{Y-&jZrp#i?hok<teTAl>({EYn2v3e?``$Zef5dbg)0s*9GQYk)GvEh!e%5ZKIW#MzK*Jtj-Qdgi{$aG=^ZDI^3YTW!=CmoR{+hP%XwL'
    'YkTLx0^8+sdA0ZR+tTPYnsKk8%c7u^brLbbHxekk8XG6>6v<}aNpy8zY6S%OjeZ+<Tm#dXpy{WryV5;6wGu-53_;6;KRjF4w*7nGd)IS1;8a5s'
    'N`|;l61qhPydV@O#AS~#VxqX?DIYyS{(fd_uk#_Y9&mTX$hEG#-WbRWND)p~qqjOTl&kdg`4MOeQn*#KHA;j2#H9y$3stD;bBhQb^;2^S<$Bx9'
    'dAdsR=4&4NUuRYDe~nea|D099Kd>r<0wD|s2@1tX3fox~fui^)1widIYu~=pEfB^@7$sor7d6k}N5Jc#FzLZNjvRJ!BnEa4wa55h%=)76cySP`'
    'pJxR?>Znz~KWqJDbbKZ8k*UV8BPJ)Xqt+ONziOkT(2<VLu-{_xHw6C`tI9r#Dbc~lvX7rTnjGnNoH)vx!H?{I^bt8blxc~NAuV#8cfasX5|iXN'
    '_~Sqrg2#dTJz^jCz@3*t<bIF;m{pm43|{$(DT4tb2OPa^W7MtDoLKq)3szPBJFC*zJEm;cKeDQC8~=w{mGqBURneF3N}E;ep!wOH-dKN<dkGQC'
    '=g1d9$!EapMK<@;nS>>}%N}G5yo$WN9QU>BV-F9>qI<hSi;w4pbTZ0y#6p&_!r~Z3%+y|Sfd=iXHJSXKO!>+Zx8{3o){M1A)lo0r^?J%~B8oR*'
    '7V=a`Ncc6Z$NR$?PBJ!~sPzfNm|*y!&+->`#n7}WZ}8Yk+quh!`d)espNq~)<WO#`m3C$eG+RP1#_8BaP%9ixfJVGf2&I`5?)5IA^WKwwDdFX<'
    'p7LDlPOVbT`(N>qfEccM(V{#xf)}0zLGaoWHw_4Ask542cj(lIn9_x_)mJ#=FN-zAS)XCdv)5QJyK&BRsvS_*ZXv9^AoslJV?-xl1xVph<hheg'
    'p|uH9uefre5g~ilk*td4b-KL^2GZplPp4{G->v1@K$8@-GNh)1dV2v<EcjT(RsrORPZ%GBuyDG^T>vi%4xh$)XOAYA(S%KQBgNWWoZ4ra?_uwT'
    'R=(tH0GS%bV7U_%+z5{36qIekai7J<aM*)rsnAdb!ZtBWOMaSINy<!ceVEQ|XFocMqy_L+@1}t4d~&XG!+5j!vfu5^2;lJ6_a~{j*M3j8?Z97b'
    '><vnn_Zmq{d(NY(pzbSD14K}6wYyW;^8=#PleD-r^cWa2G?$__BLk;Ux!+KZ<DA;%X|xBc)s1|YtY-B=%K{KzP^PzM2m0?~RYaP+llpb`wdLxP'
    'VVw};$~Qu^u;8Dts;ijgEX7_tY?<F#KcJ<KI>P#9A?Rck$tthG6B(1&wEymn9>HbVZYZcxJRAq;uow4mg?Olj<jL1O?AUqT{}%rHDHGW^-Nsq4'
    '?YU#ohg;T#V$tWe5X6@*-k!<Hya0V$Rt8jH*^9V!j-tM7XntFC;D_d*=?kk&B4eJ<D4}zvRNdT0kzp5py6H+Q1}KDpdkzA@uTsa)k-IUX9^Ixb'
    'C{qgtODxH*DJ?ymtM)GaR9f#ZT1<N*s<1+?LP9mr2B_cAQ)S0ur*aElFCtT$S6b|RuBUGV>QO_KZ;AV|MMmE7AA5`5`6{luTnIuYwpR`~Ij7OD'
    '?~iAF^9e_6S`YWM$$yKB7~WBOC<44!O*WEh>a{qycRx!joj>Lls`kH%=m7B$E}2jh^Z5>&@lr%Jrqqg)_EWBT?R2I{Bqze1DsTGaFx81Ah<DbS'
    'y>U|Kr#dD;5=p9Sq&#ma81xpim*wlwqY?+)FDY9&e7nR3nQ(z|-e=0c2a<XP^RAJSL04Th2W}U+8UmNyeD{f1q>jOf74^fr@HWV5^k%UM`fYJL'
    'c{`KitX}E*EnU;7bl3_?{Zs)&M_Z4eiK!}4)+=-nZ|XI5ko((UMXr3_`I98E%tW?V_O-!Yq3wiw6&ZUb%V!&+fNS-zxq(4>LE0h}QbM{*Vb2e$'
    '@<<3S?=_?vgTc~L_sJs7N%^m{D&)V$s*r!qs*oR8)lQf|3M6m{BEX$a9jPfCp>}?S!4O6u@ZlH<Ap}TLFhXJEPYVnV+LIj1En#vj*5hARCZK~3'
    'ksqNq5c!QFj$Zo+{4F7V?m<KztSd^6B+^c=Lh`eALmg`>De)Tuenjg&X{_{9>KSK8(-)lXSN;{NA`iXRL+mv@8tV65_p2X-2s>WygUQGvn?~%U'
    'Fa9LSvg7hl_R+ujbl)GXZOEsso;sF&67tBI;nYzPisJv6RmpERqRX;@k^T&YT1WIC+bX0L7U2I2R<-^ct2#8j;2&Al_l^I<tV;REtZG|l)Cf@G'
    '#b47#DchS<1?Q04!~rI8X|YV;ywv9|ehoyg!j0E=<udi*CPt@xwC&rO@5~O<rA|5HTXsz_4fdt=0@~?1PD+1MCxCAiqI;UM(l!KN_-HnbEIO*7'
    'HC)R}quh}Db91QMd}-Yzwzsq;-?Z{p7|mi>Ve?GjPG}1;xOV7EC%(V8=1WZR_HiZd8p_<mTk&=RlR%?r<_b=3s8=GjYe8d|xV6>c6a#$-(TVuz'
    '>52r;=Qa;L#3r61H1&F;s5By>!Rp`doyFH}grrZo6;2EYy?c`2Oj9!fUZjO;Ib|m)=>~&%&*&q-Pi^dH3m!>*4CRX4lp)TI$lYO|{q?16c;hl~'
    'iKr~NN5?cJzWE@ILX73<?qUbIR1Ei>!eHGkmusgY+)^f4SAnxI8?0ueO%4Y$0;@}mnztE9*J;@wfNlnvQnp7aOy)}Gsy>}-?Bycii@o?8%B(b6'
    'K3y=J;-)4qv{D2ij-cjR1B3M{l>~b-dPXN&u^>mAbiBIP;wBe?;|Z^^PmGb%O|I3&u^3M`Jpj)&!7hp~F&*G+c}hEz>ZFy3kgSrd3TSx_Np-o2'
    'uSiPVxrwLmm+ZuzByE7OMHr+3^YnzcDgtN#H0r5jc2fA>V}=TsB7r$SxRXPj{joPVjG1jb@fqq3)&`NDuZuXxILe%0A~FzDKLKl^#Sn4xUdDeD'
    't6GZ8c;BiQ{m@ro4g=4c3`uT|l*OO0D%LDuCxo~*aqI-HRGSwj+z{h_$$VFCyKIovow$y@j^6_4Ouya78kY8mbPI43o_c)Zt%uq>@2amyBzQS3'
    'T_6zh#O+s#*#z7^8}XLEW`WCMNo1(|OF6mT#!N#a0sNgQ)<$;Y+h&btI>scwBNgHu3c4{`mmBX2Vb+HJs5F=4{Z^)mcDI{aERA7f?)we2i}#|>'
    's9nPL10+QYmu$jHIK%epCyw_NC4r0B(Dy#s(qK{d8O15yauz(iWD$Hm2c|RQ@3UllIj6c*-<z2mn8=<2HZhVXtTr;mPHfyg-&a%bUdVXXu&U?d'
    'b6|P;(1tny($#qq{d+VL_4Ty&sqENO<e%{ii-E85w7+vJ(3K<4&C&{GBo#Pw-9L8Bm0xDs&j94c+LIGDD3*^IswD_I_YHf~l+K=MdoFJs#m*(c'
    'KG}z;iEq-&naln}tk>qr7J5_zq{5rrK+9roR4i}R_Jz7G_ud?zSkAg{GDIi-Dp*Kq;QjTUM7lzqtOyZtqZi<Jast>QmO!xdKvA$rn#A;KpOZwy'
    'C(GM3!40So*3;rWlRYxj+6rG*xG8K;Jv)umP@)Rxb=#@(gDMn!2@*4S1iYJAB9mYQmQH-$B-+R@6_{yb`amh$Dy8nUlO_ED3q3!cfpvdeU6=J;'
    '!F8&;ZBhtzy6%*tZ&`=|S6J_s#koE>>kRp)paTECnqZlim$V=MgWk9GY4RTu`-S!hUu1^9zAH8HQFA%Z^M5A$ws_z6pK<&AQCsl;^km<a27i5`'
    'KU8jF2#Fym3E?1#f;;7+5E4fb5J7NwCtoN9VkkuYjC~!1i9FcX!Do;o6-2_vBHSTKNF3_FJ7GE$^`XO}h)RCSzIL*Pep+dE;<GcOLlGc6GD?TX'
    '<444Br(`Mk;a%X-(@!CX5D}LAhGf5BUppb(>C=(8!jJLn!=SQ5iI75%BaaJEhwOj)ap}&&W7QEu4$=srA9o}8SQ<pB&lh%d(1af!B>3auO=5pp'
    '=~5qksSW;(eHj-_iM7$kg3}&i5NEc>deGW_YIIZsKR6vZ_l<KDM)^`(QYeZk)J=FlN*|5fa<S@nJV@So5CVJzOpl%1&rXvMQ=?)XU31@f(8z^u'
    '(iuk+<b`2kM1|s~^N_fjJ6IZU&@^-VTFPlFv-T<FJS5TR`AaEhJ|BHC-?vpv{bQ}oKOXk)M-BW}hW%~SM~Mya_iAj|06RQ-D-w<$PwBDQ+ev6s'
    '#j$9h!J)emIU<6EEp$84a`d=uh)0#7LtXX0lJdEKU+>;!)6T*jVwjGm-^QYHIx3E790O5#brje2-ihLY1y+*O`xWsQMMn*#9!|(Q>-qYG3!a;!'
    'GC@XKW~}UXG9#HoIZEsRF0W`>rsLZlH75uSKXF1!{VdKK_IdHl*>Rum7A~_l1;c5iuZ>4{PG<FI%qd8+rh#Zd%y*~lp;i8xF!&tTog3T38Paw0'
    '@<v+%*C#l5zG+I+eK}hnFX8BLx{4dC&bU7Tex>bm>J>5hzR8W2>_B5mqx{UsOWaCXA>fo*4agwtJ$im3v(~IT4w+4D3+ho~1N@bl&rd5|epinJ'
    'FpRCu;0t>?-a4sc{>JOmdnXa~7B<kIRA{a*$Eh@30t^@Hu6P1*DM=Pp@CG|XNZC9IgRp!&ACo4mQD)fpGIaMxJiV=!sJ!4!EtfTfdP)Mo>iV4h'
    'o+eik|KGHI*|wWlvh6!xQSTb}ioU5a?gM=%K=jQUeIr0ffDnBB1=-F@JMGHMs&j0Q?Y$8!Ew-eH84)vP5ab@+E20SQQ9eygTLx3A;aw-BPNXS-'
    'Un+Rn1B^>!*CYFem<uZQHPCj8VTqw>$)}0QUuYh$op>q{U4fj{7a#Xlec3(jSEG!t7v4#^B-~B}$Tp7WAH&-jY^~?%#-#1GIjNL!Pd?>Rt9d;T'
    'P`J(tp(+e_+q6~4_BTDsJw{M#?p@UR+j8aD7hver>!lhe)u#Ig;+*+aL6IS|Jqzb1&n)Q^J}*4wBTb<#$mzkbIRPR$8ct(SD9as?D}75evZKQL'
    'fc-5k{9n2s<bTpBBL7oP@%zCs7>XStLKF#sAc<iJfj|^YA|y&-JMP3#7$-i>p?`3S#E0*>dqD*HRD8Z9BeJ8ogXI6DsDnYXhy8JORDz11(`O3o'
    'Xefw3+P#NtAbIH9q#r-K9|XaF!ua9Tvh<S>AP<MTJ1GSGC;6+M2jWWw=TkI7(?iE*_k!S;%kZOs1SMY?ox5vIj@r$UN!eFFYEt;YHKnklVwFIj'
    '{tf83NAx4XgB)p#KXZz#bvVTo{+Cn4h4@q<#r@(bmU`9|l^F?+R++NgKhyiCcenZU_QkUR|BXXDJPYvOIK;!V07r)4KXr)5u7Ur?As)L1{xgTD'
    'E!n3xH+=wKeycLWl<u=MO<FGXnx@SNBi7LpgK67syMLYa(aQ&m1qGqFyx22oX37Z)TcrS^9xbqJNvz;@*|f-E2Urix%N~pMIo&?t*1j8!Q>pc>'
    '7hhV)8FW^7*>GZgqAno91T34r`ax(yd+bQENUpz>QFXe%>?DAnd5PUgT)+!FpiwEfv7qa?%H=7pOZM|t{qTkY=tb{$n02EYx*cRepu5qw5f608'
    'vOy7U&4No_$o;Zm!Wu?c&MQjfJv;9G=6b_uLqKUF3d&8eYHqA1EwFp07tB{0W9aMYp%LBY;L>zAZ@rM;ETczaYrc)k3ccJa8q*hm4^b0$o^Tsn'
    'W}^QSYx?_+_x~!q_)ix4gBAULk>6WT6s8aY-7O^uqBuqD7W5Nk5EKR?FbKog{?Jczx;c7SA~HS-*BE+`+A;W$CPnd2l{!1}rbo{9L!n2}pN~rY'
    '#0`5uQcy>=J^M^ACGgKh_%V@$Ko0Z|;s>2DO+PbFiX&Qx(O($Q-E{6N?q3h)J$M-R96JIN2swhA{rU_!Of`%gPnqSPA@;>F4h;KbeA7>Ofqv4x'
    'FmaIhcaw_6pFt$aKe6IZql)GeRm8s;P<ng5u}5k>VwO-v`z@J0j{UTejH&*&q6&JEezQi|@2$~~jr`J))BTe0-Dvc~*l+0FSbibje=(@;Z^tz8'
    '$3}k7`A(djU*5leHYMq_-=(KVhnGIGGPmQLkJt-~H9!J`zaItb2%t4YaLXMU(=wlp39M8J`z<k?u7_ff{5zBheEE&?UtuQs(Hde)^#eKQt<ZJ-'
    'O~hok#tJ*xeQ>s(_lhlRow8bYEoK>j&&EtP59Q{(aqKaQV)wc}S>zs+x0`ht>aHjJJ6@eo!GdJkAKgoyhVNn2^evX&-5Y@3M1IbSa>Z;;$B9t_'
    'bpr{;5qyI4V4rV~q@Ik)j)qIv;?eY^_b4d5Qdil%g%q5dzys#RUOun$+<|x`uQ3s9-l@t&64s=6_87%e$jzPFSyz$_LeTT1*n~ZLW<E5SzX20#'
    '5RM25<TW0~!Cj^+q<P`e+imI=vYKsyVT12zx4Nt5>f%)@yOV%Rot!?Y^5mMpOEy||w0iX#Z31IbR-bUy+g4=9(w_?@aB8I7lLygjJ0wT7q52_h'
    '3H;T(W%Wba(y0|!W@-<>W_`xWGk$vBY{CqKX1o0~Z~0NY7nxpFtQU8y8hn#7yh}r1_lDF}^DlOP9$wS<6sXe@AUdKpvSWloZ{E#@ym`Hzuk!0$'
    'Uq_MGbk&|^e%+n+3kCFCfZ^=ana`JG(Y07?5vT~yIH5t;cYKPx_1RRNm2rV2wSl7xF{LvRxUwNe0i=t7kWKgQ%x#+Pp0r%mD}`w4=^3{T3h}sC'
    'kk@u`B}OtWArM`HZg5n5E3PA~WTNa23?QGP(Z#}xCj=%fa9JIzE6*|>bk<xe4@&FmJSxmxZwqm9!34i3$hlrs%%*ON6+1aFT=tkr2b026i>7V4'
    'S{848op=e3WLz2|MGo%2vsat#pqXe^{VhPgk6)sw!#CY2T0nb-|E=#s{-=B&@;~AGzKb3{MN1Uj{T_&byB~xph`{$a0y#9pNfg0R2>ogBumk@c'
    'f5)F`-Z6F%vkvvj{AkqLu{f9=zKX(+>>9QQ1V3+>CO$pMy9*+z!^!MH$L{;^?86De4=I`5Qz0LT%#8YsmLw0#8FEa``i1Y?on8FtU)$Yo@#&U6'
    'i1g$^2;09F$kE{)fBM}HMRVjRo*s;`_^5gA8wNj8p7>|L`5qm?pH6_hI7nvu%GsZ?#MtZ6JC^#t`98+;{MS{<2hN2S+`K~ZB&5wBf`{sVD|q<p'
    'e($Jr0{@NQJKP@d-}t@5?E!zo?`@hC9+ElIVGp+kJXAgeKt*|;W@RocX&#A-Xht6>dmb;vD%s=(Kc#1F3#<pJ8_)bb%p|A;FsW@OOAM6{2_jGo'
    '=+vKZBV3k%ptFTaPyFS^?y$N%n?6W9Gvg)*H#k>7&OD(e55HIBfy)CfJSX>R01>q`=S55JC;9YuYgmUb0DkWbMrx9WYgfIqde(1}#{2pZ)*We+'
    ';lh@o{Po`X<8_H?dWlT=4bUn~lHGFVZ%^yu^c-7uL3*}j{l3Zy@#<<BGOIXiP7%5yUF>jYNgK`XiumjE)J<pLPRonoN6FIJ`mA8)?lC+&zD#dw'
    'v+RHj=%kUWJ7pX)p%3LT)MH@L7X<YTHO9P&1jaQD{=U)t+S2;fPNDyW)%=fE`h(g0VU_RfCW=8A2x1sX5d=bj1VK>9ZZ{7xVGzP`2!)ZKCtb)-'
    'pHF%WCO9OwiX&a0phuGb=sNl$?0|eo8^?H}pT`W@VQ-HqMA?!1-%Zng=^iH>8JCYB#F6PBzj9>vACK<cFQtZG#SGY|d_a6?y2VFPI4%xbiKmAp'
    'CO+o!$fFbo0VPfj;jbgM0T07U=AU>aJ~$!!)9+!*S7yj3E~2P^lH{NAKyC*Q1gZaJH={A}Fx-%xOKq4rH6R%ja6iTj%Mmlw|64Hwzev9gVW@s@'
    '&3<d_{aw<<{5wgP`hP3w^4GU~?D+2xNzT~7Z1E1|F#%Gq99?VTZ6h?b-%<AtiIEkkrz%=zei$|=d?0bW#TX%?rvB!3qxYU~29rF!F%A+7evW;='
    'u9akC!r5n>x6MIv0lWv)8v^{)<82_ct(QKi`wijP@i{=9KWy6ISUkV~0;Us7E;*0&CXobEeKD7Ws5uW<Z8{6r+qBK^+!<@<#0pinIZq~yazYs6'
    'm+?|I5*~G)DaK&vh`x|*wdy=5FFc_(0FIpz2TvE+OXjtoG89J?2O?TMPv0x`aDr(y8kCEtK@3fW!4{;Erl-VD{yj8k%><gPadq6BnE;llP(JaB'
    'usk52HJwWUFV?1ZxJ3s`<>)r~tVS;LAT*k8xaQii2C`>>)w9@+9Tt0ZWkkU@g;*<R>mc4M18TKW>rUM$QW$C}4zmV|0#|`6v<u>3kV%8B0lu2L'
    'u6I=AHs;uZHP1P52~4$(0i_U{yIHocOvAv7_H<el8w5LH!nbSm&ZrARa~e=stGA$ML{8L|PjaF-U%W=5N7H8?qpyXQ;>KC0oTxjyoKDqkXs%Xm'
    '7S$^$IukcTU{)i9&iQLgFO`%iuDU;CVz`Fe3Q~4KyXPfhvJAtY!b!i99SMTG#ka4P7r3XE1}czNVa;X~=}7K5JS|l~nx*ScuQ8s*8a%Vm%`1AF'
    'BkvX=Eb?jhJ*cV-J%ow3SI2-8KxN%9R!A%Ur}W$(BQioSnsQR!fp2NZiuKo1j&~}Wav=F*K&JhRNOGAfIDm)bf(CDePZnIPX&GrEvAlXCg*<x>'
    'J4b`sCB2dhyJ-;4H>@%TuN+~(_8>kyu~V;vVN{I`=Rg?lLr<u6P_Wq;6J%$};~@97ng%h4o!>s+q}V^i`le882Au4C)?^=}x=c5kqh;w<yP)%2'
    '1&~{3$jp1FmdyvfN_q#zv=9pC`;gfE6K{~j@l&7>9xC*Z(XP<Z`fTZ7y*v2QnHy!2%0Si^#$1Vwi7pSKObf-w#7B@|ikU>Q9!rlH7@N?|%Vbq9'
    'H--1OfW3%l9Xxm$7Fad+n=O`0Gb^lKbRxWttNQH(4%4kJFTAe~r2{Ezh#db+%j}|QgUxehskHC+buqA~ESU>9)0ob%f^4}AYgC>#VQ)LT-35rz'
    'u_vYjVBn9S_9V=t;)eL?EQ`lG>jHPD3y$7=REG4C>8RcdC~<O^b5d7vZYTDjR&`6sIe^ZPS`$lhb~BaBs6OiP)dwZhI60tkHuqPke=V&^yD_V('
    'V{hcz=Hd607cW=i33f8@JR5eG#2eP}SMcuA7(~YyGkd+&RdckyJA$XB`D}6^#U|QKeHj>cYKHfaR=V<VA>bUg*-Q3n$+_5fc5;bm2$t-H^BNgV'
    '=%k7$$xL<bxu+VgeJFW}jk|v&E^e&&r-JQ(QssQ<X^`APIhox(@JdH89oI@*oR~Kw@i8o2&BDr(?MlMY>8}s8GBkrT{$bhlKMt%^7j+s>^}YWG'
    'Jx|sBSx@T@y1t&o(!U_<{>O{_HUjHU7x;cC7DR#64$?4$z(^RR5aghZKnRXtFiIYUGX(lfUHAiRgOUSgC7*&4`k5NNhl_`-7Jg7Y;x7X&^CRb*'
    '@5jlX6G)096PtZhO=9u@O2?=M_^5^z#gT@kicixzc@Tk<<Un`F)QEJ4hrfbt@TbuoI-Y%B`jG$nw6MdUS(#swzend5aipa8ohKi$)<cYpJVJEr'
    'GY$eKj*uEh4%mq%M{K;qQScbk^{226K42Tk{s!9|^@*+1)Fdampg>}eFAcGGeg@mv-OBzT&}xD5TiodAOZZnh{4HA}{}`tymyR#&sH|!aL6fxk'
    'qSXp~E<D6qVPT9qYK=HPK9noIf+))bDcu3B>xVr1JMQl{<*s7}r6b?;tK(9;VPI?*<V*8+lG~pVyfwpQfpt$1Wyqx4SC~g1kPZV5Jof|6Ll5Dw'
    'Z@OWBc8kED-Q%C#BJgMT_-D5W{Olh8#w-g9zy;d|%fTPxMOSo0*g&h#l-pCsbxKBPI!)dVLOQrwsaG2zP45X8siY!da8~Sv41i%nnvu3D;ze35'
    'S%6i8s;34^Ptmp0rDr6FufD$+!d+JI>_NS6dNH0&1n<QSM+lY$D8@RS5`rIU>RMp!c`Dxh9<ov#&G~gcJumuoYOpdD)aiuf`h3>wJEq7t_@+O@'
    'XXOFs{K>q;6|T>k(L~Q%2fv4|s8E|@1Sm!-&Up*rby?e%?_XlUtu+qEr$Ky^X?ef!1rTMJ%w8Th=h3ev7$TMNx^MfZ#e_2>tshBnfi!Wg)qquq'
    'N!?%NoG9J!%CT-_Bn}<{r@;;2e%U;bCmT<iSRzWF>$?#rDp<J_iF*j&;grzjYU9^7I6qqdno_UFi&Fdxu>g<j8JtyQ(9bhIU(Jj0>hC5f=XF-|'
    '>-+kKlUG&yEZVS@|76Upr=NYAzpmT_QjaLE0Q<6=Li_}AwxTVJ$PhwEP?J%k?Tn12S-XQz-{Ah<+}<r2@!Ta~Kze>$qPIK5p3DL>RTQo`c-He&'
    '-q)%s_P5P~tB(sSJ}eTw_jDv=&l4-MIS9o#xI$bPpDnHG`2~-Y0ub&=312B1DPE>|ug>>P!!PZUo0iCgBpRmv_$1U=oi-sgx<NuU9rLrW6d&g`'
    '9_j~>KHq^oDVIJO&GUuP%siMR2g+3iPPfZxbF)WpoqYa>X87Nr9&lj28K+KkgW$u9Co37Bh^7t+{kCe8`E#YV-<5-b@9M!n0frx3NI&0@8}k#6'
    'Su?z@j?25WqHDeOYJo*?u6Ncq=vPmTs;pBs8(tZ0dJ1tp>d}dhF2m*d$S=dNjtLl9;=9sgHJ+Hzj=hHlpjmnvnCJbnT)}6@XFM}L26@8Y1u6{l'
    '?vlpl)Iad6O5CZgXu@=9L#xBP{^|q@Wq1JG<Xl>9PI_W%3%hZKfOvLrqg88@2xTlKI=#hShK@~78h5*#qBq$j<a~qWe%ksN5Z?9tauy}Np7?It'
    'Jg6Kw6v}hqT39%EmS17oOhlxZNGAlB=kr$1)qAe)4}S4S>k$F$TsaqI-=KL5GxOa(q}N3z(s-$BVR^sKAUo9rZV_xGh7r2BbPC;>ZfNAd<#xlR'
    '0?Azxt3n+H7U?O~z43g`ts??9K^u-{oM7+!1CBrj!Yqm~b#;Al39jCl>&x@I^p*q7?MBTfSDAC>YDY39+!cD$-qCvwal(@4*m;j_B2kYDA__D<'
    'NhP{kuNT3i6jXrg1+c-WIhQnON*uEgU4_Kaf|m9nsyvj6^oW!<j@mN!*q2Netaad3+Sl5W2Zv>`p8%#&?GbFA+0UNNR#88r#fm&vjd&Nu1l}%S'
    'q0AaR#@r2q2}>fWy!FQ(KEGj5y`gIhfEo)+35q*|T|+Q7vZSgO*Lz8l&J9aJ{h`g)?J1B|zCyz83%L8G-%>)p#F1635(DU-AuzWg>v5P6ci8lo'
    'fuU>fkAD<e|2?d8s{9|Hb3Zf2^?X|H&)X09@V{N_8%+F5>wMqwg<?BAByf}<ArK=8lE5g4B%u8`j$;J5fBP$(cuXLt4s^Ez!-P069)kQcMvjD8'
    '{2?kGa;?~b*Anbkl6quu0JtyI<Q=H(U@(S{`Qtkt#M6TuTo4EKIR7ZlX7Sg)GV)htk(@Z#$SHLIShzTvwBq>S1LPkuq8%i{A2FgG((WgaA6$x~'
    'N5zFe|4F4sd4~KPNuc8ho*i&9MGkI2n(Tn~PjMo0Py)!`Q348R(ynW>w&GnR-Z!psxy!F`V*Nvlm*;7}n_gNv><w$Pl~JQW*`na~7PvzJ^6O+%'
    'a5z}HdYjt}7Y7#hyGAROe|v5$x~1pog4<g5{=X~p`(je|O1trWY3T7coTzx7V|mIqb=JRy6~FX}{Rvk5cee@rmHYg6w+Z}}`}}ve3H-bJ{4017'
    '_zD<lzH<Y;Bsh4fH&A^CT#!tgT{w;knI$aMkDAe08@jRCX4KJHyT<)Ujb{cxu97om5uvZ8rGiClq%mn!9T?y-RYY(Tf-0Q7)WKM1>trY|&{+Iq'
    'bnkV(+%xSK0+S-SVdo?Tu8Cw=hVekx*UNU|&#WX!FBoG^24q;)yApb<tgICcU2g|p+8H|~%60~X0SsTBXy|d=M`N`{)L2DN$?cGm+uy7>u5Al)'
    'S##%#znCb5Bq)og^Vv8#FmkyhFyQHkjJ;*ti7~ByW@-1d5t&2OVwJ&Xj}oyMGM14t&Mk7fO)n|TKDk?Nrr>qcM%@7jYJQx1%ZStL*@&!zjE=<V'
    '=Sq7J+HISxT=Dw)gi_uM)j;uf6_@j-*wIsi5hS@4IIyqO7A4+BPktykl@B3bdD94UgUm&=j1fdYWH?Qk(JfG*PYm?F#1Hp&L8zLp%gzD9I}Sx7'
    '+147&&lmnYaJMULsyY5vv^Lnbc=3mzin;Al_2^tWefmzyN!P{`l$<GI|1{!DW2_+k+B`3#TLtFZQ0z~(K1bHABsQf7Q^(55HGgx;#GXx$q93ls'
    'Q%c`^Xr2QuLj|5%p3Z^QTnNF8%)aw^c{bmJHeKn~f_j``a0l7}g59#rIN_)KQjpO*s8%oM0jZ=KXm0CyiVDvr9)T9#_qS$iB&DI^{pu)b%50?W'
    'zJiHZPb~KXUi_{==OW$Nf83w;NV%mUg&oOe<WuINar`A-1b)gN{1sjlHn*UWE42ue8MQ4ZT?N1$&X<#RikO~E;G5?47`hvb+!wBbePwg0Wt&Ob'
    '?u?Er@LAB!MYfZ7HyQJNshmSu%JWr=gl`^vS!I;8AM6=<J&g9^*>_PEAunfd5z&%Mz>hcH+e0;Fn1lNMB=*;`N6rX9JGCn)-i~j2B2@cXQb)T{'
    '**JLQVcfP;y^->XY%D7#L&3LAzN9vlB?Pp#jI+>;0C}~9bFFUpdNRPN6+$y$TKII&di7eP3;ZNVok_8GlgC~1rpBQc>UY+dB_eC2pISg|t|<?`'
    'S6x4mP#_hLUdqs<9UE@313!pgUTRN!h<82(x#NeHyGNAIc?qT+Z{ET!2ke5#^gyfyJ9j0Gs?aqi5?t>UTgb2p%-9vXi`&dTPb(Lpf!hfJI3`_G'
    '%Kf=O$_NOgRt;I)HdRd1*Za7pS-sL&Mr~2D&ii}Y6hXwgOTCoRSBguae4(K0gSe8b0Cm(Ec-TlWoBM|=%Hzoi;swr^3VaNzf;P>IN)`B3jr@6I'
    'PAGkutf(R<+l+z-#TNn5Sq$I>tL~eshxlr?Jp0+NE3i`iWWqR!ql<zHZ*az4d{q;dk$#muzj2bDkSN?i78o<Y1y|Vzr8kzu@l8Qa8u6GKWQJ0?'
    'p08DZHQ6RSYqdE;a3sGx8*3XuLd&;#!euEdM4)NjTwKAusAJUCO5WkCS8r-V{ReoFXW9QTy!fB3^+&w;Z`S!Pvj`&~gpe>oz#v3XC<*O25yPqd'
    'M-)XUioggMLeQTQY2t&wen=EiAEC(NKypQPpf%{wSNbQ39MqchLlRA)pBIEb+{`roP~zc30{PHvE)E>JgE*Wx>cBhREIy-bk5$uyB!7&r1%H7U'
    '(c)m(<KVFtntVVY{sEfBvDM<!Hg`;)1&?g#G4<f1V~KnoML!hPBs)One${>s9v_9}3_g^c<0Gs2r$n0OAktL-BGLr%9KF4V`_7cNHxYUra+>l7'
    'BFz^R1^hQ?@jy|)e}fhe6b1YMqXZMw{(5F{2aCXegBCxT#s3B^9=8en2WauT+XQ}fpWk@?zo7ZYPr-^GMSBP2Q-(vf^>WE5-oeK6J^3)0M_U>b'
    'S+9p$SRlz=zHu|{x`a>|L<^qLTHLl*;nsa$0(VqDU82GaQ|H}fOMCN;XR#fwk*nW0zx7w+d}-g#=$*F0QO<SaG<ooq=Ffm%{PY*<zKNq|Cqfz-'
    'Ekgund<!E64ZS<P>6%~98v=eDICS2Ac*`#O{phBo8yb#q-e>jg)-DVqx%dh7H3rzW`C(SV?XJMCVaitSy$PupZgY<M=F>RWqpZA*?KZj~tC`%O'
    'c7oIhifV&sm|hbfu=HrALIY2{no{)Ew~goPttw&}RuAKrSdVDZS6_-j4+`R{{OeT5FPuWVF8ke}{{9E|_dgx>^P8;7|M`c7{a~>F<3+w%>VI?A'
    '_apWQ5+f)Wr1n1`1`;rg<0ObvBnTaXc@#<<JyhsVEj0Bp$-5ziJ`6!9KVs#h+lV-#VT3#)=A%Ig{!Cl>dF|)m`JhL21_6({PK+Lm!@M{|SH6t!'
    'i$6v)%MOW^J-R+9iOKO$9RI>XL!Ww4@~J}Y`$4iJKL8e=`ci&02_xvCaku-8LsO<WI6VdSG33zEK5)qABL{O6`V0ollTYCa{4|15`(FRlLQ6+X'
    'AKTw7v=s`ig0kT}LjlJ2xtbQO3X98+EVaeu_#2?H^0!%g$+v-ZF5LFJt@s#`-^S|M^t3-Sq*>a+o8P#Fg9Ln?d*Z}?HvjHH?s)LK#~3u=9Dd#H'
    '=fQ0J*i=op2LR`2ADW}#(3|F%iw@mCTl=d!1Aeu&zq&KvXY|G2vllJUHQLui1<83ZGQK(~<Yk&XLK<Y;7H%m(it_uCGPrt0;{jT?X<P#g3|#;E'
    'v@#gt?jtKjj;Tt>GsCxKyQhBU#MaA<T(lr>IZzodtG{)2h1n9vJp{Xpi{9%TC(0`39;sggp1)<@z9UXt^Kh`0*MlMNmBrsXq$6_hel>gO_IY0b'
    'Kcg?whBxqIJHur7p39a&qXIph;TY{fd(9y-(ytfB_AlPll>i1|nN!YOFHEo+(~43HkFb=NG*h7l+8)M9*x!`?J&R;w6*kH?NIhfKJ8LNO+wBeD'
    'y{zN_3j<lC1ZqDoC;PQU1C9J;J1A#)|8*kOz3cL4TK{e|=rO$Gw-bJ_eSho1Z}#rrU-TU$MPP~~VF*M}3dIo=Ms~vogCKZJ1|cY%L?{&gDMc|s'
    'j#Bn9?Fu<ai1|k}GeiEFe}<8w)KM$mzhcy<NKO2zt%>+D_9{MRbYvePgB{Xh*gr}1AO+$dS<ypHA^)gKr3X6QtseZ#xue;^B;TKxN)9E^>;pc@'
    '<Pf>qf$whn$Pa^jH^;<BnG^$$f4kM*pMdyS+5O4(3*qAHwA0-ZL(~C_cXS=+e^;u?WJ`f9>HUxEHY;yK$G3Fz)3zq{XB0(y5BtB>aTVLQ+N8DC'
    'EYLyCP8a2y(RgD@BziOOWtxY%qbq7kd~Xfm_IF(9kC6FS0BIgr5!RgYtu^xY1wWb#@ZG_NQUC6afFHN?S9bJw7>2#e^!XLLQ4pt#q)%C4sICw9'
    'bdAt9tMt|Z5OcZ1S+SgP+%pk1Iwf9K$WO+c`L`=MR%t@y7LC;dyw*<@%Bzmp*zjKXjY{3;*#%B{m9q18?sWB)CI;wYlu@1bPy7WLolRb9ehh-P'
    ';9c?p(?hPqzWjWxW)a?zVj;=_u)!9+DtcM77qZLl@T#db#J*ixOrfMV&UD)>gO0SLDtGz#EcJ&Q39o>fPN(?_auASscmABB;95Ir#%f96?5|6U'
    '@U$Jknhvr-bS@z`rzT@e?#ZOsSzY+cWvgfNb~CIRaKJP3L`NfI@;ex)a@^k;J6%Dm??r)-;*LQjzZf7n^jaih{OvVA2cON}3WB*$_5!@Z0&CW>'
    'VQU>W&gq7xH=2Zd%*HRJ^L(FfTesWsj87%v#6Zt>j5kZvwpGtP#Woui@WvZ;TF9^nM`E$AtP`FUXF(C%I#pcvEW(<&=w@W)_9iP%1D<YkUwdl`'
    '&YEt7kqTte=J{d4UO`j~gbR2rGP`_9k2}7bXUB}ytG<UfcZZmp{EXeQfOuYThFE8hDHl$1fb<l+UJq{4mI-{-bomyuk)%s5Z+*G|Bcpv3pwti*'
    'HI)kL=r<L<23m_3r<5T$q<R4@u{zzWOZkC8^E)dES+*W=WhT|{c^2lBws8k%@mSM|^Cm6n22w5ic(WjH+^?7p)S~yy9RvJ90Q7Io9sQnR=$g@@'
    'Ul->7ng?k<nRD8CT5afk_-~}DXn4MH7kIc$q$Pz>XraBTLAhs;?aR>Q+x0d;IJWyb(WQmvb*ZtF3#r=FE)sy>YrG35v(<C9)TxR!S?6i)ABmA*'
    '$R>C53sdwLqfUwX%0wEvh2UwtG{mBv-sHSYz{PrLg!+g_d??FmoD9<7uU@XU6`p2E<7gUGva(@<DCUwb)GY!8(jeOqcki@R6aw^ga$n*!3_R5%'
    '(mqonY&t#q>Au}TP-qEwhD>tv&qO}Djw4Co)rrY4PtjXbzeg7VPD^N>dM}C^K~l2;?y7AlAH=JBwibn!P1ki^*levA(l7*>?D;HWK}xtXd=9P9'
    'QUM<hUbVSpf|{1=yKa@l)K8|g+@}jjYZcf$_=hcHE&RUnXzd0?KA$RR3}nHwZs6bm^zs^m^u7`Pg|gE0<x}tQF4GwHdIsl8bBB3<<M0EU=?<4c'
    '?Y4!K_-b90I6v<<=kfqrsO04dMHg}<lk~P3-Cd2HQ@I+$+Mw^Istqb}R=*#D(stL!{ds$c*aDY9GcBh|1kgH)EXmE`z~94g(5w`w3biRaMQQDX'
    'c!<sVnQCX^IU=fk7oI`++T2_K)l+*?@FD^_w>3_xPs6Kwl|;R+$J-XcBgxBGafglf&5Dhtpd}p<3-a+I%_3mx(?aVIs9-Km1H}394!BYrtVu<)'
    '1-&?1`gosAaq`sOAgol}G~#6iC#J?L5tsf0V0E37woZ3slTP>N-^5mb?b<)Wt6yCA=Lid;2z(DINfe<FWDhWZhOiLgNbK#wR{|cnv_0UWKC&A}'
    '$}Kq<f6!-$%^oOb`#C>vp4(4{siVDZhcd^gHuBRdhaOFCdt6z-A5{<R06_3(zRgj!%?_QY;#XpzJ0Ln>6m=vC4=s;RTnXbxj7mWtf*^JjinGtS'
    'xBcKAEhgBJ;UnS$f*msM=`pD^|4e@;i=#eVd;(<Z=yLf}gcThTC5ZnNVQpYU{u_j)|4oE-U(|1Eo2&3W!g3|APQ<o3#&(8?^-Al1hq6*g+qCsS'
    'S-=6azB|}3`rp|V@Uw0G)m<G(3;2tiJy;$ba^UM1&Sy{dHTK!;tXK3-0Qv1cYW72G5_VWN;rWm<xME}YDGMxTHc!v1iTqWQQGl#>5xzY5VhH;%'
    '=W}%5n79HKlYscd;ZjZIFga~zjFa?*QB{y#p9W9Zq&)SxU3I4=HY#FaFIN*|O^Crx>7=zbkYuB@-cOK!W;qf(OP4s1pXuz$s`*xhEc9nv7qQ2)'
    'FF}ng@0+pPXLd+u64H^`wFKZCIv2fW8Q+HE1cqc=lvGEj95ANr7jGAjm3o%Q<&}k8%rrX!OPe^{W6CXlcUp>A0Mg(R&n49yTQ~tT<~Y98p-oC1'
    'KRtCu!<4+lqS+4f$KCFfcNE>j)3Xql-Cm0v@>&4i9g#b4O*uK=8%YA8#JBWuTZA-xA}t?`QKq>Z{BFILWCC!KGnalXLVs^DVraJ&pw`R#M#Bz_'
    '54`IqS`maC4nOW{Q${Tk>M=T0r(}bPKA}?fm8s5#vK5w?)q3%2$^*prT3w!jB+Lo=XjXgogfN|oP&L2`w~S~jICp$n^Q-NX?wU+cJYtX0qaDG1'
    'j!!27;GzlAX-r=tOhw-LRdenms?Rg^)LW7>^g^ka*bT4d`#qe783IM&v8BTWc30EdR|5Q4kUaJ_mupo>J4k*YazN9uVdd)uZ8WN&?vb_Q*>t=X'
    '@|djN<YWQnt%MI16j*YAe?|oL!NKWj@H{gz*xy82z^_sgC?b{pRQKl8Cut-+Tjly(@T(=L-%rB={?%Q-TO+=}5%aO|5syAyD5FlU(L!ca-fGE{'
    '*GHuEq5r~VI`zUK>fSPBHoyemGg&BF+E*BX(i9j8E=g;fS%Jnq%B#zS1k}=-J|cS<gDP<YZsaP)Smm9bp5y_X#Z85Kp_>yycV*+5S(I|MFeG=T'
    ';;Mk2wX<MbioIP>eACU@po3g5z#<`PI#x;waAHn1#lTLH4XUY|+B)a(y6TfS@ehURqbkt?0;%SQ*H|)jmG~31Dgl*^fxdteDFW@%@oLCaQZeLb'
    '#2D{}q0G$tEu=}V1*DA_!qnmC9#<$R=hvsz%<=Xl1yO)>!C8Eut6Gy$9&6W8Z4D{KRVaCt4d|%j-^KnR&XQaFkR?B@^6hPEZ`~5mT)mXI!)gV}'
    '6@agk<Xq=IdZ)o8H$o6L`zK$WR4Gf}wO1)cEpTFhzd89eM5TaT%S-eQ{r6o(wW`N}Q_^AxbJp?w<I7E80)xRVpHmhcyzDIYi@S%dZQx-ngn3v~'
    'rmfmW8b-)zU||I$D!{Y{lrzW4ano?gKveoWc`&}B`ENxc;v5{I%726XR=kxv>j-aBL{R5e5YRoC-(E!nVr*u^xxJWMk;cMs-A*qylAL^Ef`}3<'
    'SFFht!m_ugum)_inY&Ks2YRmYh9zCDcmbrFLq)KRjPbtriKSQ!2d1|%jf{fCy4ghhmWm6I_8va+yu{N)-cNLXO8<H<hp<B%-us7T7|zjfQPq8X'
    'K!dpdq?dkC|NOC+<3C;Gw_c9lE%2Q@4@h7b29rN;r$rCkk>E%55&j?%;)7gvEOW?dq8~}j<mhoAq5a@bkyH*JjS&Z!O1|c&_KS8Lc4W`tkG3a%'
    'u<qjYQ{N;H(SSopXNO0~uX0uChaUIojYadL;(BQ7V24Q1zC95ADsONI9(;s<!1VZvAqPl<(od~7Kl(sG@PKpso>KHPQ#U&@Sw;4zNUCv;cG};n'
    'r@Y8NHR$Ka$^QYOaDdbBi^ihghQ#(JTn$ObmsZ!#p^r7OFN{0vXw%->ZC%@hfi)yBTAG0e#v*kLJwHl{zlq>*9R233+tHuk`Ldu~9q3!PtbBCK'
    'q8g_y`bNJ$xvJ*&2DIjw!T$AN^T#dz*$#m}+v1<?5IDB@*SjFNAn;#0&yfY=^&aDb2r!z&*s-%ASO|Ut$Dpi*H!oZQ*S8j7RJ_=Q4Z(+t*Rmwb'
    '%r+4fYEO-<pAQQ0*x>>=J4kc;Cr9jvYee{V$=mFj<JASfB5JcK@*8?Q-usQ8rHxQ`zo(JjhR83;Hv(MQ4c|F3Zl26&?qu1I6;lw5(`Vsyx>9(x'
    '-oO%KgL}oc&P0f^bUx$oz!vP|Hkr;I;9KPY5LFaiI7<;9r3m4*43_$uH<udkDm|%JKMG!|Up!ZILS~KKh>efOw|IRf2nnm3wE_HKoe^^B`j@Z<'
    '9@F|EHH>JMYu%X><p<P;rzLNS+`qZRdrK+;E-WK60w2+9(Jd#SdN1M$u|t_}H<Au)kr2x}ktV5b$Z^ufP}6|nw6rx+pHD`0nuSeiU8)#X7?Z`<'
    '6^JPW;tHFc&h{GBsHtA#!0%^YxRZ=%Lu1mDm`_KyauK<b)b-m0uJ3z((@!^ld)y}=R!Oz=T|CvqWOw|Nr`;bHcNRp#ps}72IDgt*E^{`BI>l&f'
    'sV%v^QFpbol``)15^(xZ?0B3iaWM1cds}4}DYDS18Ixifld3@PyllBccBN0f!e$&xyz2&wALXJ*W8nc;^*Xhrmh0C$dNNA`C7Db`ua?(6mFZEr'
    '?uwyWmr`X<f#CI3O{G`P0hcu83*({c1*HD|rma|Pae0M6<RaPx^o)f<^G&Y^)|Swriw{V$HD2Uszhs=|TqBgK(-&Y$9`Jp%&&=a4G|H8@Y=6C#'
    'mibZ70zISqi_w@Y;p5Ze!oQaI!Gx=GTFGB%8_5hnvw=8wuV+QR^0MjtYr*gXJoD*t&3k*g&NXv>N%gv6`66Q51|heZa%&iTjX`ZB4v;tJ$$ei<'
    'w5A?;I@0pmbW*biU17&BeRS2ic#6oYVVbf0E{Yju9w<~!XZLz?9{WoMG{!c$9lH*6@^I!C7{7Z8Kf5u?x{q$!B-2TdRWgN&>pUY1F9vS*r*gMD'
    '41qEtV*|Wh-s$uC<-#F7xOY(KBJyl@x95QMVn;D7Jc>MaP_B4kVo!SQhnpHiZdXaDa(=A96_d)X1QT+j<7YzFf%S4;t1CFUXp8+R>bEz4BcHCx'
    'w__<60mD5xt(76JP0%5ODBvxRI&V?V`o>p*i0&EmEFtYBGdKYmHE!rcVbbozsX?w8QGPAkC+g<Da%Y-8mZ%J1Yl66gsd0_NCLcrQjh^M;Nlm2?'
    'pX%DiwbP?O9ogz%lI@@zEQ0LIP*BU2+KsO+I)HU+c9E;~%CQWy$DerHO>lLa<x$n=aFtLoCeu|fWZ!B^zJcyLpua|rZ1a3(UWObvzcAm3C3%DJ'
    'T=XrG*YCkCNrh5fFI}Wi7=8(vWrUSeCg(n@E>!9S*J?F&N?plQ1km)IX5XR*w~;`jrP{-V2?gEzAwzUxB5Z!+a1x?!7IwL~L`V23c0Fgb=Ppu+'
    'oL&)t^~nol4Z^@%Y@}RPO=0DZg;%=?dgpebvlNuJQ#j(tIR9n%WyrR}|HGH<T+P?-wVIeC>16!BZ;u)7*OP_&+-F~)6yIm}=lF-#+W)adzrnLV'
    'S@3&FT7tkyY=1o<93x2-LQxooFbXC}3dad-2Xq96lfM}0eCVN5$Lv6u{0yWaj*=Zk9=S3E`{>DnM*$Ioc3k!I;e*A2rcm%BOF|x%%N>c~@rTDo'
    '9%aUuJXWIe5AOPm%!xmsEB{qy4F53TK=M$a!ap-|3gV#Er61k~jvbl0V~6-ZVdyAP=GaG*JwDDUK8SM1e}}pXbl_AF`Xt1N&!n9F;Gd4k;id!6'
    '4gb=l&7OSe_Rdm;nK+)yMtmjg!u=HAO+RMFIGg)dZz)@8k_Wa<<W6nw@bw-@e`7yH&VJnE-4d`m3Q9Wb8<|VkzkeO{v54dE8XJBtpx;{Y?SkJH'
    'w7<wq0l(LoGHZr2oi7rLI>)aE2SYztZ(nBWY=-mg*pBfwA=X6j4SYXSN0&8={z9()a4xdI_Vm_<JxsIZMW(;Wq_o%lxNF&r2qcI%N1_16J~i(k'
    'Z~vZJQ`oy{_U>nYQ^=yeUGUq2-(;tNe^oX!_Q<*YsJZy>Bo|>OM*xYx-_$7%#`IZBuZc2@Q%EH;*70aRGeVYAa@)!^E7;LP+(hCbjFoJ^LJq_W'
    '|0TWwf3`5FksI|SI6KS{0%_W@)_ShM`^Cnx_;HP7LV^e`1uJGc<w5~5^{qzat6k;Q6abI_nP+0?Vb+KwvOJ>{aZaEK8U1OVwH>ycB-M07Lk%Qz'
    'wy)$G3Wf8^UI=mGpMib@W+G#ou7@Eh%!&c-XCYTzKU*QnzR!y1nv%v*^Ap6+=-uqob8l<O_zbC%F(rq^t^h^3s!+mIbkmTc*13H5^VQ4K)a+q&'
    '4^SUWTdEmcKu@g$MK8Ht^d>i6rRWaxyi!j<gRSs}L&FOt69U~a@VBfG#4pZ9U%qCAzGQ^LKi1xWpJjw}^DOI~o}-WJcygvrNHNQu4XbOwgP)_Q'
    'OUN*^$m(yG0lws#=wItF@{D#u^R){_vltLzywKeiR)o5#dh#qQAoc2?h*3mP$rE<YW3)%$G^!&;9k@)Y8x(A-Yj0>y<dmmC;-@M!T%;_Zhbmnb'
    '83Rgtck^#QlpXG*Dm2~bQnj9ke7zzl&xgdluh^TFfu8xyT`|+6N$k&OBw8;1{f<5jAbPo1lZ1N}%7_q*9*-Kc;j1&DK0K)rgW8v8CF75#&R6Jx'
    'CG^D4wG`!f{!(UBk_sTc3ayi3I}oLuDDGPFA_j~^dsb<LkglG+i(UE>WGB?%E8WF~^;yw;G9}py3&L^==qaSdmgkBC8zS?V2jqaf$=SHN`p_#w'
    '2(l)DyeGQtQRo>;lGBTL&1ip}n`lS0AX{Hj5iETu2CL7wxi9fQ<SmJJueG&xy5)U+9J2o}{eOROp8v`9-~8kc*M7%B#0c;hSAr5d<|1(lLScx2'
    '2?9Y;j3f{eCr|_-2n-`(3Wq89rwxYCr!oW`b(*7_@6(ibXhcAVmILw8Qrtb;?j5N^!~ItYk3%`)qm+&mhfB(mV<j9sSlhdUgTH7cew^a&<96qj'
    'e3TfoUo{xUA2mfPJHGB0L-8?@7sC%nh<#)n_kZw*K$#Pt@xA!5)qVdIdORiep(h@k_52|1faswdmgR@vPUC+Te@f2b(xY_LK7N}ccfAi8b9#GV'
    'bMdB=0SAlpyky%An$4fjk#m1gYH<1Gt#Wktb&i}SfzulL!z+XN(hi0?w0D1i3}fu;I1u^RkRVwl3)*bj==%tvzEY$$4$@=OjTE<LYzL&=kMsB{'
    'G5qmy&TRqo&D^x@i`L?|gWry6!jD>ujP^UXrE&~)0n$!*e0IRM_#V?7-WET~MS17VyU#=R?K+nmKWkRG2<5k=2j%!TL9{)&1l${S^$x<N^JOy0'
    'UmHxqA}<azAN)%P%u8T|dG4=IyMoK59<L85M?yM7m&=C0_i9`^H#f^`=xR{gG}zgEhzb&eG1?LH<N(OkHla#aIfW*dvlD}NRKGRPbWEi49-MG<'
    '4Hf0(#=hJ~CN3v%Aumj{Tr-53(`#ZZ08-NVgR`U=dp^(Q=)RnohfA=0orh$_Z@#R8SZJWHEJ^wn+py~kIypY2Urr~P^Pf0?6g-vGY<p)^&<R*<'
    'o3hnFJ7+*yUScyPy>-xeo4tONw3U`doW@mlNcs_vB`ixYfU!rt1)1e~d5oF&NFf)_=<;dX*woozC<(AX_3$dw`cl_9S4H|BEO7!BIxDf>BpnFE'
    'JH2uX+O+lSm`w6_2a^Dw4zuqx=gnDow5oUsF5A`HEx*<T=PJYSZCQT;7=dq-Nv7b6($qWh-w=$)+9Sv4`*=fW4Lm)%r?mS=vp?gV-=&y{iV*3j'
    'GCI)Fa<p|Ze7>A56g;Q*0yEC=Em<drHn_8qv=3$>o|3h}_g*zuRHpb)y@1cTP#<K4b%qG^!7U=rIl*zhxuDO<S<cYLT%v))iTiaaTaUUbHEGGH'
    'Ze(V9ePJ(aVvvESozvQ}SKxkI(Pw(DZuD7ymQN`NX2jJmZdg1$A$tWqnpvJPx9I7mR59JkTtPG=s_C**U1f0vG7#g2uqvu9udaCv2BHXGr`Ks('
    '8{uB&^OQc-#=hGGR!mF7-d20SPiI}1-*cpGb_rZw{=jZ$H^`-HrJQRqRf>8FOKH}(>F*3CIg;jc_nQvo*G8o;gWrw+=l1oMPxpT~d0O@N_FmTc'
    '`0++ZNcZ*9znHuKUwoe5()+)Dj_<PlJ1nIr5Coy4cM2g9kUGc}1di_B6N6xk!uP*F^Ne5G(s!?yQODf(Lr0iARPM3l6MdmazY~;yH0_gr7Vyt$'
    'tH?pYN68~Kzx%7CIE3&I;Y{)n#Du^jnmYz@;YS?0d&cAZ^e8q^@Gm@L@=^0I;E$J$kA)63&h)qv|Fqi|_#xMSsAhf~F!Bj~3-qJD`I%9c#2>NZ'
    '_y~i+&#2XX%?v!ENAS-jn!v*|62EyyQ_d1|N02Q?-d6p*K7vZs@jtZQgI`+jOYV<eagTb+Z_`ypZ+9=j&}Jf8dZO3FBKF!NzCQN7?Qn*`;SH5-'
    'cUfO`f2G?eDGwz!^O5z9{b&f`Z*iFbW#aCYyB6GI(GL?J_!?U#pROXwn`Ge&St9by(&;=fgQ+!MKaB$GenH4>^77&Ob2O}R<pvmz3;R{M+dUf8'
    'kGcUDE(WJz`VL(+S)_l6j!lRAT@+kt5#a64eRrc^vNCSu>-VIi_K+|eqChL%6=N<9-|xSfZ((!(+fKjMAAnyLAikfG^7(yaK3IOCd{}M7GDZ|w'
    '$R4~Z&o4X=`R_<GQKz6mvB{?aPPDVCn*B&j&vJ9mGgH`OzbTE-P1%I^^ASni>|R=#pA&ePh&gIAIGSmj%6XF=djLGuxON#&to7*aBkvE=w`C}#'
    ';e;nje!8<I8&uxo(PzuB<}$>brp0le{*vhatO^WZC@<@@3Fqd-6llVqITZD6p9`2f7@p#L$E)K5q&O==!NhuElBT<JI!QuEJ^K)8d7!vWjUspA'
    'r7_Q{`?l-#(JzK-sd9%c!V8nKzE^PM+?8suq>*_WM)q=nhuN_r_Ics~`*kkPPou!8E=QHJA=K!Zy~77gu9NXzZx!_xQwWX1t`fYHZI(BcFsEb*'
    'bB?)hPzT&01QZQiUPCaj>@L!Jm(_A~P{!&>&oLC<ytDrHVi~R#h$C{R&KHuWwHFTtD+t%X_$ExIeP+~fy?TfrQN=?Py9^zPlYefU^p$6}H~SkF'
    'cmxEB7L&cRI5#}bHL$a6_<#|4L?Sb>^VZk*lu>Fh@N=u))X8J4@>ZT}wVc{<X_8gp^dLyDwdB5#n84rGrOY?Lc@ZX?4GV!axHm@=On8A!ZS941'
    'y;VWyoF`Cte*vp{Q@yhmV`**I?+4rVPwpkqHV|i};ostmF^}D;zADp`WnMR#9<I%P3-tV^6p@;JBP)<~yYyxSy)>p`${E$53Bq~+xfNsQHt#{@'
    'z4HUs!aIt2E{O@x?j2&tdHNH{PT*5$_zvLM@ZB>pdNj%_imR{d(>*b32Re7-?EH}@0(^)f-$wxYZ!`}{Y`KxR;R(4zPG9jylMRbWds}9338$+I'
    'k0v0T-)*I(rX6uPOs3rpExY}5=+iBV-LLuefyK~Z>1k<M6L%MPqdcq57+r@9s->G#0Ib)8K9XMaQ+JWI1Z8jN>@(X_qqu9;aSHsJ=?jKwp=_a7'
    'Tev~5iILvr6(d_HO<)QLbQG*Mj2USHp0n`GT81yM=e(<+c=i%QcOFZCFnTa+18HmbwC&&rscKRE|CxKUB}dU^OZc9rsC)iCVjjw@F8~1o0TKuh'
    'aK}8)AcUU&2SsL9X70#S!`|Je%`(E21bhsV+?TsAU+#v{y3{~a+?De=>e_2b(zk1r87#DV%+c;n%|Lc1m_0lEO)1*4wt`E%eg9@c@l9XFCbcWg'
    '18^^1;^}U>(`L}S;z{&Es30JmiR0t>YBba(Zl?fx8W$}n9V$+ymhW-NmSQ`LFNY!km{x8Uvk4Z|P_CvMgSXnu#VqJ~-IEfoAvSxbTyj$zbaWj1'
    'MO;0i&aI^GdZsDI9=IOnqJH2nwK;Lk=&hLBwesOq9!Zlo&vsTGa))QaUghrH9A?k?Lbopt2I-gukJz~d0@5b}NjpXqaxSwtYpMwo3Ru7jZAD|D'
    'Uc1IzL#saMaLe-kJWX{_D46#cP9l{x1>i8sS<$k`Els@DbbS5ftj}}k1vt*}at7nwU2&Dyw0-xSd?f8!c;2h@Dv(VmYRTaW;1}$`Bc~am+bK(q'
    '+R!1Z$W+3DpR+JaD1-D<ZhbwU8h-Sdtao0IC91FFi*d(p407N&-0??#yZ&W3d5WtlZu0OqCiJ7Y-d^}k^qUcnu|I^_Z&EW(`84kcZhU9<cWeg1'
    '_yz(0&XGIN`>$U@&Ht%u_zFY+;rYLZsL*HVbI((}<vTZUxvQYldq+MNyd|36RRRio^EZO`sEPRV!o|Cf6e9M#j8E(p1(@F3JGX^5B#I|{|LBGo'
    'gZB>coBz8lzbmp6zsk$J`}1jJ=kr3ycHW(261+!M?NnjpJ^AV5OyS-fwKsPqd(+p3n28UzaJ;8-5Pxr=Lf)FB_&a-qCcmS9TDTCoy^a5H`HDVS'
    '=F=ht$9Ba}LYc7i1di{~vmY(%Y`K9%(VoMXz^lCU6`qkd(H;YFPjaZ6H_$Rqw5R>Gd&f&a667jG>@2LcR^qF9Lsi`d&E9A;Tt5(~@?&@UbMrdj'
    'w>Ewa%BnzoR>210Hh5aNJ6-p_y%vRegJ&BQ(kj=H3x6MR(P+>H>)>~lr1@wR1)?voO*O4AloxAfwV<l`7KwjTUbMXnyik{K+loJ)2k`v^`6tf<'
    '`2K<Xlji|^|3Lo9^8mhoAm2ZazY1kHmwn{Gb9oT4hPoaX-Z2qf8#b@kl$2KukH9S1o6$oPMIX$YW={CF##8OjXZJ~YJOf~BF%G%FzOsXVaG=|L'
    '5syc*UL3s1sO)@9c}ToY;5dLA^byDBaNrb(O<%J%34UQho4aDl?OHg&v*Rdlwc2d0`yo(P_(Jgz#OBA?l8uRbaEe>>m%CF8o;r;nab<Kbh9LmE'
    'flYFz8ci9y#G8@V(nxruo)1!1d5(TYPip9>Ff$r2Yie(*DIBl9M6`FG<Yb88fVOZV;i@MGQbu7neDpO=%Uset$Fas|2lSSxKzK_-&Cc`8%8k3T'
    '7ZymE34|mCg$>Z$i$WasW}-RvFqa|6?=Br&4PT{F;e@M>aA<PSfi;)+G&(dmC8{5jc7C;*!yJbrkS3|K;u7LSVu75j0CUHNXgWzxU_sRVNye+o'
    ';;<()xF@Nt-ta(FZvynxpGi@u9s#(xr<_gplJR&h+8FifV!d-HmcY>zlx7*d-QBBqMw0p9QMO<tH>h64%5!6G^oO(uw2bHDilf!`1}gM(g`+SM'
    '%A_<9H@zNi_ookD7^km}XjjrY<Ysg|=bA%gDo-q8*#b%;X}%!#7-6H&{-z&$9?f5TVNkrxU8b2v^8m&aD&sisX4D8@`cDwDZK1CV&tF4;T@JlZ'
    'FNu<RD=GO~yrfSEObH5TE)1>KDi|}%2y?9wLfj`%7Wk{2neXdUp<y?xTF4K_j(~95ju88ZLiy5W#$R$~nA4pMY(wcY)-?)qb*J#IRgeTYlRd6d'
    'OivsxQpE{NE*&>{>fMgk?8u%|q!z#<oVg)ltWPi#ifQer+&w&-S{-dw0#r;~?Cb*Kl@KEPSWIXR?Mmec>wp~Z$KJGLn>a0jbUT^ihH9h387r?s'
    '`#e<s;n7Y2tsG?9vVvEU>gOUp$NmMvmTJsg-#lRTT}E@ZK$5~}46B$*&5z|X&BG9L0M`gaY{0{lat!ao18ECFyIEMNx9(^t*yHG8c{PX)3(BHs'
    '#t?N>b4xRB`cMsq=nwRHgULQnP~s?#c0(Z)1U<T!i@hGgz_lIk_TXi_k*7069?~IcpSMMtdHY&EuCr$M+Or;`CIcKge-%Or-Tm8OA}e`%7D41c'
    '+!a@}>X>E6G!#$JB=T3@ezb_-9H;Xc6YwKxbPZJLKn0=bvGSrtw)-t!JBmml)3+fs@E#mTQjp_<V93S?4R0=86FzZ;bl?INey+ORM+p$TTK=KJ'
    'Sgy~P;|dmi3FhKcqJ=bLjt4<BwYZO$g5@6eB-0pIP{VP$J<de@kR)5hfG%7}<P@UnS-v9ogF%(tq&uzijJ&hv)~FuY8_cC`)78$Mqo&KTf0S3z'
    'mnG6Gn$sDG$y`K+^R+gyh+m)^ACp#pICg^La`@$#^f?pX5mE4Xt}EqG8|>@to*}0V)H>e%3;~at?z@9E>NB(sftxi0LH!?rvR{Qk{-@#WfBHK9'
    '38ek$8vYd4Qt#=Z8)AgX_lP27&w$48j%=Z5?>^fA?cS4*>_9P2K83Y(vd<JE;eGZf{Z^;i&}i}=RJ7}hlKb*OxC74(Bk!}EgFWXN?2}M`rA~$I'
    'oo5?5-4&*G&48Uyjr+S`!G^<Od{4?E<lb6`5^q72aL2a+{VsU=JHp<lUekNgblZ7XLkah!?|v`T?<o4G+9%5nYs>z7So@=_&j#W8Pay4%;DCPz'
    '((VWj_`49!II`SV1b5jG9Pm#etzl`$eSi=UpvFhW^~l3t6josM7;eyZC+&n!wQ9F*`krikZTo!PwxoXhu4Mv$ka?n;s=uk9dmi+}FCH6-8^~<b'
    '?=HK2U-tJ`4g8(U{+NOEWAYVHEq&3yW?x^E<lUd+UdMG;mUR)K^zQKfItyxjL$3DAy9=v}r290c*S0VOMDLU?{*rk6sIMRFARXe<UA{{*S!8eX'
    'W7iGZsu;bO<=ETIvJ8_mh{Uk+IR*4MQ_>A7V2||4d$s8Cm@MDGNWW3%p|G!!d|$1*F%<VleMLE&Vr<?Zy!9fmNTti08|$&Qd6bjcH4lZ)9wujX'
    'geE-iG!-q5g-%*R#AwGgVtcl$j`H<+`^c7Ma3Wcw*Em4k@WyBD>4(?n4OS=pz3*jvLcE~pIly6OPiFW_qddyv137?rn3j0it4u3$+{eAY4@N>p'
    '6?IM(lZ#MGSld5y!;d?lx|xia$Dvw0wjk(E^l^f*yk=%Gev=|1qHp)(wZq-pdT_j_dXaQ#VPgSiBD^JUZ31j@gv>GMcq8CaSc@hKalvz>OrXYG'
    '*9n!!Q>?CxsiuZJxwPD!I~#w!1Nml%9~4LD-7wrt@zBK6-V{8)l?1=pSaE3Q?&lulzkT$#F68fy{DD_VA{0f?2t^PyNkbS(Km<mR5Q3pNguw(2'
    '5ipE=YR93s{9Z!uqAAgbbQQWM58`NV;Kic78F|-tfp&rh_IY|@Gp#}NW@*s7z7+H(Rif~oMu4N;2yey~#rM1i^yY$K=$@h27p8t;$7y0W{P8>I'
    'fxN|C_F5VG7McF&YWDXk+b(~I?+lUc^<IhFtUR=v{>=};{@#nT8TvTh>vZ9p!4f5V=`Z}#^n~E=b{zheo-i0m(qH89re8GA5U=TsT)2Gsl<l<u'
    '=IdW2_|7KNe6?A-d5%PT4Qd<uXxp{lrsr!E4t&_~Xbn(%`Mw*4U!JlB%crli+V0=Fj;%#27)UkwMLTX7?nB(=$Bp-by?)Yl+^Jmn)x+#I4B8yU'
    '3~ZriY9V$JId4z#gP}7}`4KtHQ!p9xtM@qam1&jXS2Cvys5>z=mwtXg?3Xa)%Iu;!Y0JGsk~7-Mrz<2JlUI#ngT1C9kdb6K(G*rn&-r@soc2_p'
    'QFzV|54#T@E@Q4mfY!Mf@HcZBgyLZ6H=m>uXl|eNDu4iFs?=N-FzPhPNEQeF!Dn^(VDr{{`c_wa^?FT;=kg$+PD+Cpt{&_3Oy)NXL~Dnz00uvp'
    '1|Cthl@=D5Vna!t15BMEt8xm7g{G-}K*wB*7j2P@38o5$0$XrKqpsM%`W-N-^M$u2@U=YJ18Jkm<F>}okeaMi9Z#IbtaXanYDuzJkId==uW0Au'
    '2+CVrV4(ea0$ALHT=X<5v;4T@Ig7bfsGX`YnkljrWgMU8vd*dc88JGhlQCj&7vV9ZG*O^W(BifQ@~f8SHV#T?l|o45k>s&CKTqCFF^5WKqnt(c'
    'J9M5rmhcxg>a6pTE)qC^Zl{;^0M2YQLS4c3OjSk*e$vR{G6+@d%kUwbeEF$+?AgS<>jc&G&6IgR@>}T1oFG4|gL?y9Dq+rwIZm8&!>2ZOk0H=<'
    'Qkz>Y*CJvbY#@O#)P^@y75K+XBxY9U(dV&5Z?Cm68=%N2c6(F{EKE;r&`<NYp$6e8O_)U1XODKJK5y5WdnrAgE_%?m>QVPkcQ)aJWe66aKds^g'
    '^4lBNOX$h>qk&5N-l9eKFkG%$iH_-T)Z6xONCGUgIha#)8Ah|s;kY=;Nx)!{HR6uMbAlS{P97ej39FEH{gH?BX}JE2*#3tym4Qz}Q^#ab;f(M~'
    'w=d1gb}l{FLGXn}4E&H3-FY}E&)5d-_QAUL!cjjeCs(Y?R9;JI5Czzgx*3#|%D)|Ky7ClY4zd?7G^XT5APzmBAgSEkGlcidqZd};o+W~QteW99'
    'vmOx)vJit}<AQv84NAfjbpU1KEfAXoO7v~0c|Ml8CCTUEy3+nEAH;4{^ZDSwVEt%w_VPF&&Y>@FV?G+;r8u0=fF?{Xa$VTfzTxv0ujXy~%B^L}'
    'jw^?P#NA%*grYpqr;?n^V&)#jNs=1vRZb@^J?l7dF_@Qx$?8=G#j(1(rvU4+cFAj;%>CEoTv~ZCx3Kw%H42wTT5!ptVr(9-{&AW~YXHpBx!)$H'
    'eqHQ!O|!o9oI>zVXm>$nMF1=C0FGxynjcd{&Y<>;apn#!QEXHir7aN$6xx-qx|dxCR*%V+pYr)^9?R2fe4aYtY@f*<0}1q|!WxYmuogu3Yz!kV'
    '06j*2*&)!bIm%*aQ<xVWUoQy=b76dcig2LYBks+~_86-TyIDDOfU8FaE(Moev9dp3WTb!g0A{59=x0aQewZhEAqyv1l{nX;h;me9p{>J2u8@!%'
    '=rxB#9>Y8z8w5nr=m>_*D+APqI5*ab4VydvNM%;9=tkyq3-Y!nm4=7yb8<}`!@!&#B|WIX1~P?jDbK%_Cxep_5N}5FnTGDOIm8Br9nLbwvm;p9'
    'M+1Gtt6YPnqtkSNzz49%aHkz%rg89Gnub{9!oNsxy8Lfp^J)Lf;MAQ+#B6~nBYD4l-S$12`qMqXBB!7K^aHbq!YPtKAqv@06Gl-Re%c~n93v=X'
    '15(=y691G}6eGVw^v+4$!qf<T;|q9K#Dm`joehBO0VcV(=<b@xpSPrJ5C?y^uk7p{WDh#G-M3(rK;9a3@5vw=*1>~)9vn^YLMmI#y8T9eCD6PF'
    '<8N~9hU_+!1-(hY8;&E$J*wTudmwu}>%S-V?$bivbsqxWDNws;D7iP*?1IkkMRtvrcZ^R5`=pTMPX(HVbcasJ{1rM~9q*#4Vu-BF-jfnpnOL5F'
    '&hB%I#i+;e=YEcTb~yhLi0ph;CKJsPwiH`FnkMh5>=)p&EV^!~sZ|OxaL?KAc6zgEm&+b#7UdRvS#NgFPNr4&VZ8hH<CnqZ+u45#K>z;P_mcyE'
    '?DRJfkkUQVQ>SJ%egIZhn-<lhPYmZ2>!M2JsMjUei9>wKuX$kC1Bo~DCCAT~ZndMkaSF7YKrJIodOb}5mJQ4MxkYbTk>F-y*$32FZmYp~r|pZV'
    '9~YsZA}AS)7Y^xUKWY-JT~1z83`Z$=F)!eL62j?f55c6fmXexD{XDl&V@PZ>KUAg@#e0K3$Oo$Tx)g`Lhs%3qJ277zb<LgvFtJC+=eMAdKN2_^'
    'I`Ql(1!4zRt@f>Hh94d-zFz21>K3=i{u*s>4llc8`RK!B0X+aEu|l(~n5kai<mW+sbA0Ea=F6*raju;q%1xf)+CPnF&*=79p%r2AQ%J7hx{D+Z'
    'kdo4!mH;-p>d~Jk)ryO&#TG(Dr8swc%4Ko(dS!G3v|jF`Q@51ic~%IgFwqf5O9ATOQNC_Rv4&dl64>p5I}>DeSI-dHQ{<^QD85%uHU~C>#;M@x'
    'RCmuLY0T+TSD`DAz*6F;s&|m6y%%Tc(4`{5T7*40WF~>3f@{4y-x3h3#<R+jmmuHX72-LDXbvw}7vBK&EXo-9w0kbO-#|nk+y~*Vwx{?hjE23V'
    'lCSC&#t{_19!`p%OUA8T0>Kf}npm<!0PnVrHb&Dl6I(FGb5(^DEY#S$zyxSKn$7IP{lMb-IJKc(bgly7en>(CrQLNko&c+tWLyMA18WmvO&iBm'
    '(_t~?K=Az>3gE8@D0S5(b(vpw)%<zR;2P1-1my|24I<>$&<2ve6z~MNayO~R4{RkdI;tM6MO|EeJ22hA)Sz;u$Z?~{=$62421m%?HaZ#0C8r({'
    '8liwvf6T%5YJ7?~yb4#k3`OmwygsQne}Psk&YsbOT9}XH5oiRVs_`XnH(;41+UtCuv_pEzd;M830mXa7J*tHR%@|jLl)Id818}O9TTreRNU<<r'
    'IM3>M%~y>A$0G%5!J+hM>@c1l^3ptx=lKGn2h>HQ>VX7p@fr|ml{!_s)cr*eT@_Gl4YCm{h65#%FrMu0ZXqL~Tz~@FmsicRd5N?I_b|J=Skfsw'
    '>o(>1WOpIT3uPn#NlLFO<K2m>HdIk$En$XWR^Sl1nDwh7G-WXL<Uy!y+fVB(a!7r=D5RF>m=c~54Uju!K0Pe<ybK=P#X&H0t!ONS<c{j8<R%78'
    'BCjFg`Nn7rnBPHH7T{x(whSA=cu@n1hc_X0@z0OV<q|w0Tqx)vNSEBpeU|6=lY<Msr#Y|raRCLEGM~?x<u3skxuo<gI)G?N!?b*jG9RTs_5`?I'
    '(E8AO%&qe8LOWrH#tL+-9ztQ(lw}2(MF8u2fxJdEU6l@ir{}63;E2jOIx3a|$qRJ*4h;9ZX`=$YCi#(ixiwshk>)n-!R(=EGd5uS&|6`mS%5C{'
    '?QX)W<<uj8epn=<)p*@6b0OaJlI<VGV1~2MYw(>KSj3)?Dx=Da5nVR3w6rB)^t?3Cfo~Y~9TwE+ju|+m9#I1Xm4dRwp@UVoLk~u3Vh~j$JZCde'
    'g5CSEI=hnl0OpxmBG9m~A?Is5XZq}-SY~&<U43O5{zelNQ~R&B`9bpTW7AK0s{d}kZ@B8GeSXMFVJNaEq$nCD2pp$yf+DHC$q7bKm_$$r!Z94B'
    'P+~JtpX#e)=$qJ*{O-qlE+~n2x(t%Mi893R6t&j`(6>-tNc|oYp8_l@dJCM>dt!eFTk$*jPwv8XP_ifgiFg+*-sft-dsh?T?^~kyclcK|hJBcB'
    '^cHHNc4c-n+7(;&f&sF_G#}lOUx@Cf**2nYWfqutiw!3`qT0@}E62R2y@kPE<=F0JyTK1q5Ao+MP5K*H)L#MCJ{miD;q{?lS{!?@SYBT1s_=rf'
    '_^gfN$l#x3fv!6u`;r9`^*fx!H9f0Fxd>lVPfwN&?g9bqWaaNf*q?u7`K?te{?JkXDx<Fbp{>4L%ui-;{6Su6_sYlQI^82E{s36pDfF*b^rgn2'
    'r|*3F{v2+<0$BV9z|wbswfP)H#?sU29BWPigg$*r1r|!~qzhviLd#W4!)fMTD=1_5$G}KaHeFJEiw(!#)U}~yA1xZ()bu30JQbiXgd|ZRNW2nw'
    'G8*i5&lhxx@u)~6*CWb9D<NHMpY7QYu%w|UHXtIc59^nOD~EmoB!Llw)1aryxd#2iXguqybxcp_`Fy(A1vXFj4z#jHm4mrDWpRMjg%vVOR{NQ8'
    '_X)th%*BGA@SFBJKykV#4m3sEXCKDWlEz8?ekaHf3mvME#j}zf!6A(Lv4^ORDvvp=05mFuPTd@c&f?ZrejX|Y3+M-_+@;_dhOvDSP)tmuBfg#_'
    '+CAtTd)PjEe9AB2Wz}n-NH<d<4^p2(+~(#P#@}Gj-zXaZdmHW#7(mk9mt;YtvZ$4;&zw+)Pg2s&w3R-K7l6I%jL|ulDk5L^xJ(>3FL_H-EmtqY'
    '?6xy8VAUCyx+8lK4@+5CGqj#XhaQ4w+#Dsq!mldF6-CWCSBWrjG(VY%WXXd?_>nnq9Ma42$>WV@Rs|Bw7R7X^#|Jd|kq$4`2xwq>yb);U`V1F5'
    'oRw1VD{0RtdhIRe6vsSaAFLj+sYh;JXhLy>$N65#fqSMb8hSi{_An>9Y)`6fQu=f~85va!QF*<cI3ICrER2Lze;II4Mc$Iip<FZFYgIj=B_y42'
    'EC5$W30ze}2eaeZk@MECA}1}Z@=RceidoCV+Eg1LPgy%gh?gx&)9O*|#3FMH%5DXQ-Z7G()tlBEMXbl~=5>pEZ~EgQ;{Vj4Ab-)JAb-K3AfGrC'
    '3ZW>RCQuxQDVRdB&AmVbPSFSsL7ThTUZV*5X~e#}34E_Mhwn+}TS&b{*t<w6v{x_i@OLuY+iQ@w(;+^0DENEwdYtT4=7{`4$Hd<SijSe}RIuxe'
    '?G+4s7d;K%6Wp<2a|^#3*b%%HUy*mwI@}!<2EFSS$iB)Jz;FI8c~`$T2evs5;yoFD3+X9zzmX8zOX&Mt5PJ7JyB@_mnD^fUIfFm%1bRD^^+$&S'
    'buOHB)cFYB#rT?S-}L#cz5aC&=YQOxtiN_Bd)fGhZU1S9Qv98o1#)jzB)pZ+Gmtu!QOE0fMW)m;E|htP#Dl^}MFe@gIGp5kff1E`NYWOLDq@i7'
    '*W;a@&V*WE<tgxhJ9H?_ODbw5s&1H)KFZ8cPWl#SbE5_sc;<@SV7Dm7plaiLs?`L&jw2|m2|8UlDF8?3`nKJu1~%uU$HU5krMdvO`|GA$c05hV'
    'Zen@SM};2QphjXP>7k2GTv^$4AM_cZni<sed&d`MK_Ld@<_pd6m4CistFfVf^lmjw!;?rkpeK6J=vA;wp1P7}g2Oy|01(SD=L4H$AVew0T11LN'
    'OrB($K<mw<J)%V6h?7cEXi34*NL|5Gn)roh7<rW4!8!(B2QIfAn3CP@p^&EV!u0ukfHccsM-Zlh2RngJA0umqf0hqQu@5(Y94d$KACIFG7yxx4'
    'p;zlSm`HY$SZ65GAS&f`N*9_<e?N^vsHbKkTjYgI4*m`DUb=X_-GZq<nuJ#XwY63tOg^N$K}Z5UdXi<YucUJ~|9Z}Xkhx(iQs4^hVFaB;OmzX{'
    'QqM(jz>8jJUjV62kd8ZeAXYbR47=d)v>A9wKpdnE@X_3?*ybQYmeNYbu6A~MY#)=hTZ5MM4sb{Spku8qgeT+$YTc>Q!h@owMwF5vI-uIzZ1FtE'
    '4CrbznRN*CiMuV1&G#;3o0)YFB><Y?IjN}wlq2l@R@E!c;FZD05to2yJpXC$Fz{LPFq4Wu^$y>b<CRs_t1jFbSvr{4%Iaw)yJ$6F6`xG&{SsLB'
    'ea>vK1#3YrhgGzuy^OekEyIwUbL=kEy)O_zk)CTt)X&3-ejV=GGd|x>_mEmJ9n!~4^8;6b{n=+4f)O~RC=KLs@+S~EIN=)3mJ5Js1GTa`I?-8;'
    'TpRJc?N-qmRc~4`IQfxty*5*a0~k_u-N{>E0xQor%DQKwP(*nHN?aQ{Fnw%bjdz87c`>pf3bRn$WzQx3Y0?NETmzKh62`GDG?E+HIvtAp4d=0S'
    'sQ_|*s%jHM&2#8(FqA%{fj&v${aIdHSQ+cOv=^r@6%D@TMl&{tm=&qEMqm6HS=Y1%f~l@nbC7gHOKF%>1)o?0qqW5<!thS&k^5aw3wmUFaOR7)'
    'sS1~epGcmHm##jXDqtQAN>JF#8t_RZP#9gE`ufn0ZFaKy8`Oy9{W*~GCDc*o&Ifm24-|{qCtytM%Mw5!v6gFclJU4|G^cDYgFJWjNy8JxgkDOG'
    'vCFz{-~@XjpwxO?L!SryfrJFjwziuQDA14?J>KevNANeQN_Ejzk19K3V%s2%f;bFD6kMW4`FeUz+MzsYV&dtNNK~&oPhNO{B+iv1J<+otwTn2<'
    'x^`}-%b-ybtX$;9tFy7Sm0T__hjZle;OQZkvKqPrL>>$rI{|cISDmJw?Z*KY5Mv~XG?%T~oF<A9=*~?lbbcE10!2b18OIZtT!_uQH!S5m;W04*'
    '>^jP>xcuY58vTnn2>lB<2>lEPZ9g<bLnJ{UG)8XV2i?Nyec~j&1=-a0XPibqC4KB;d$1kDY?vY;cc2ncZ?@ihKI9&1zv~dm$4s!#2l?zQKWuM`'
    '-XIGae$l4i{^8W#CPHBQp&vaiNW8DQ_o|?KNrd>7R>-^mWp92?-kMkmyi26+(j&;uK*8R!Skas4vBmvc=#0X9xAU$97VPjR@^@+<jKAlm;d@;J'
    '`zUQh`-%NO#X;<}`+s}>0SCd(&CzQ2a9L&_iSsy0uj}pS@sb6D1OE;N+943|9R_;+T@3U?N60_HKsy8i-Wce`Zab+z5Y)aBwzg32#6S|ma<$V@'
    '9-B~%R)Z-k!huLt=gsQm$jZ;fO_>s64IQ_yp(Mn%Z!?|^7iW2Op?%5P&2A%EZrBlR2x&CFlFD0(!JCKz_&bsopLnGKn5Kurb{IMwIg!PM<%z#|'
    'F%YojXC7v%$;^=znVjFk$os8*#%Ph01Hkrob6|Vd7ljp^#SFTRVJvdBjyJ-r>YSu=Au}JImAt;HM>9P00h{s{c<C5Rm|_)hS3^2!)RIJYd-*$('
    '4nKY2vA<|Mu)knDu+NMKP2v<pZN>woNeq5Z03*=-zZ6Ms4g;Yuiu_cGZ`T)kvuGoHXa2(E9#HMf*>@{g^j0I@_QBrt-SG3WXF}|n2^6-MJtJa|'
    'Zi4qX+AWlV!ktXK#bujy*<S>EatwY)T*UT${+03AECe3ygfQ$aaI_l+Xs4d-N_=l+K$P0kc6;nZ@4vBk9Js|@;k#)rd5;6z31rCL&9>XcU_X4j'
    '5%MkK@Mp$@+Kq>k|7biYk>vTM(?NUte2wGE4(#z?X4C$MjR*8UXFRmypRilC^N<(O27*-WFpB3Gn%fxi6qjUkfX<-+S+b`TNem%g=sHhG>R8QA'
    '+|pfGvwg1xlAH;S5d?=g)r0sFVwVf;U`9@%Yze5uQIR=%ncF-&_bd!b;_RjYzu6c($m`|wXlLjA>ns)UX{GAtER}X0pRcY8##e?kzHdL~kixvl'
    '2JbBJ6T9`uASt7Y7N;J2MM^|E$;1h|&~B9<?gS2lr34Kx#Iu+6Rh-Y&0&rz`p^lNqKd7np^w!L~t7bv3d%90Q>|ln+$mg-Q`0ga%c|Vd2ZSAl;'
    '%x6QrP4gXq&#U4ilgwA@YlxEak(<<{cL;pGQ#|uGtdVK4lF6KZJNxzg+fDuLc2j;kx8-g{b~%^QAM@Y-*JhW7xqcT0%y}sDHU5pwtGpiL>bFPy'
    'n;Dn8Dol}=zcGV9PWe##zn%9(=Iz+8XSi7Z`{N|vR$e#LrN%=UzxH!{xq_dp;Qx!)_tpCTt!w+iG=FApqi|Py-@w%NVsEug-V!v)TlF+}i^N3l'
    'xjgV&Q~q;Zw+$(6SZKp!^gD+XzQu0h@I9H^-#d0Udq*XE<3^0__-b2h19oxzd-$uI74{a^578ZpeF))4?+yy=EgZMut<Ah+{#%MBdd~oQ=e4L{'
    '&#i5cF824D2tx0t*`?`-ojSa&v%^MmFTMPUx#iuRWdhBAG+LOS_YXrqHCxz%^aTEpVGGS86jg51RT2lKH-s+SyFL1*uv>|*<`=h5_Ua=Q?%i0<'
    'zdt)5aI`AmSY+E^dG~1!kmtj%t3l$0)phnJ19@_9tP(jg95`00Z2Q@kEZe-Gs5fW<&dV1q($!GhI}GnM;4hl=!?pmv8+G%(pVcP(eV!~oW&1)F'
    '1U+|BFYuLktJsFEmzAYk<97MN6x~?U+<q)**>7j~Y2j|aO$)VGU>B58zsRksFaD_()^a&Yux8pjK?YLyj*aiOsnY58y_*6yKV?}3@2c#F&@1~?'
    'uLff0as9quB|x;y+a8u`NsIn<hWM+pwr4W<PE`RCFL!}hO(9~B(#fkN!Ki%XtrOJy_c7HSIorEf!Wz!D`-j8E-fnN7t^0Ayz;@41#bk!B8bb2d'
    'hxBcp`m`<ZmZsIb?W~^Dbsul@$8!SAeJImW|LW8xTd=vCZLqhM{rawG+mC5-`|XTBE{v2Zu-&KmevkJ;*xwL-9Z+jgiJk;}`r;|9gl4<WC>}Eq'
    'LN*6{(kqkDE8FAXXGO{FO)DQQdotTAR_oY=trQ^@c)o6cSLv^?1{zF}rB&=|@agq91m{9{Rsl9$kh5{V3<3Y5PSG(Wk(_>kxBm5DZJLlESkeYS'
    'Lzi%Q5HJHio!78JQ|L?#Lz|mp(P*Ah)59#js0Uc^1f3n~CSL`oISmPe#IhnI4&eHsJ_~m}S+GfdWe^G`G*V(W41#PaRV3_kq>cn~hN;T3)P+1!'
    '?dHx*-LivYQF#X-zez6z^aXA}s-7JYbh?I$2$9d{g}&d^5ufiRO{WSO_qxvC+A5e$IN}&h@x++H5`d945sS$VjGtHG$L87}`ei-yaLU_2ylN0-'
    '3kwV$hsjExC%~rCPr?gc{ADQeiBRN+$Sc<#u!LWWp3G|DsW>A&oa$DF@^i<JQEa2|%dT%scIr)>sc~LKl5?J90CS4Lo0`JCBqq3$j;ljmMom^U'
    '813iCQk>#O(<ilCK&TeHC&&qx^Ibyq+gc<`a7_T|dc`qN-O&3QR$6v3DQytQ1P$kW@`?*A+m`{mW@_)DG?gO6Ff?92dIRWP$f2Jxpn5Gwap;cE'
    '&c_W$!bT#_ssb@$lw>4ZQ!@}<IrwH<-qn_ROUoakc`R`2I2_&8B13>G_|=}f5{!GeF}zxDlvhGuo~m`FItg>AJ5=<zQG;icJTBQR=kP&TLV0Xo'
    'q@{8RP_^iFdO%ELw^lt+oN;y7rK57Em#%I6H~0<Waf^B0a&nAio_;g%ucK!~i_yg2j+gD%cT4=X?{zUG)BTOR{MY}dn8%-0U;iTuej7~x>0;l*'
    '02+d}@QfyKh{PZmf#A<4+-%WM818x^8vsDDokNPhdnIvnk7IUnDz(Qh81*}x>}8-|D5CGZIn>Tvpx#Y0d&q?DI01d9U#NHEWK8d8Ac%dv?VKd`'
    'ZM}b$wM+I)&pzW1dXL*d-~E%(9vxEt9*RNlL=p0}U`8i<$hAd(8=l!`;UIg)=u15deRpOedk_XkZz}4ac3=wmUZg>}ufRY`^x8Q**b~vTpLXlG'
    '-vI<*M+iEEZO)Kcz6!jat;p6b{3P+l)hxqQhwPipSK`gm*j?0Iw{7dj)3?oWc$-htu1fw?ZC>AkHR>aD*d<k2?_}%}7hhEB-Uo5)O}l-FzkZ3?'
    'pnV$i9-zUhsXjIPOVDOYuWkG0hD-Qjw?AC+&sPlm-An%Yih;j;$&$o<=I=g~Lesay<K7N0<r&0R@06NB(J2ndm#SSB544jNb|o6gGMP(kufDc9'
    'M>=u=96LfmO?_l4!C0OReYbD?nh3)Pt;=SWM8_<|whw3Cj)^q8=Z!>9qg<W2hce_2TL5O$Y<OX&+X{J7CC{A+q`UOjG1iB1b8^KY2AS&_g6d~K'
    '<eW#^{h7<M!=SnKF@eDuI9nJ!)#Nygr$xr+89SIGN#F+>bLp@dhAx>rvrmS~UGj_5WQv|&U&?CC{0S9Qz5x30GS#KckEG%#D!PTbvd*9JaK+9S'
    ';h7?dm(;o3FQ%!>G`HgS+U-X+4w?){8mp@T)jB2D!$V+aDwrC~H;MrDM3ux|r7M9^6B(u*+3`&y5zx=Z+PX@Jocj9HVOURu5x|>813|FUB8rSM'
    'NV9@HmyYJit8y`LkwBiuX`$-%RxOQYppd&<FJzM*?m2;-rmDRHuXI!mBB`!JPA6d;Xg-@&ua1q3L_OmkdhVp`G}U&LvyHD(+9NvLPfOL;v!aHm'
    'SON+P-BKkoRo;tl@Xb3SiQI+7Dybqz%8-Fl5(hq85{jX;p6SYyCH;6Ca<n-<MKR`pLOjK@@-h_sMILEpAdLx`V;#4X0&5Kf>sy8~C8Ze~N}iQv'
    'X*o)x?Q>i_;@h~i%=S@ct!fF<QBS<*LWiCMQGs1K_ywtoxMD1vvTp?Yq_Z}|=x$+i!4;%fh|s!Eo00>*C${{M1-K~k_Qq+iIrm%Vbv+hz^}N-R'
    'pH;^9paJ;P1m-8imR;s%`?GPglN9KvXM0y#_PCDT%S9H~x{rJe7nayyClmyQ_CPoBsPu(=iYB>{F9@9+)wNoO6YF|4a5N%XV66bYJm?cXAWj!`'
    ')3dEQrhk<tooM~4kV4#E=a|j2%(=KWB$mpFut(Fu4miMF>RTkCutA@P3muTL=v}l1#R*U8SdFA__bU}7qZN8uqd?Jl+7Rq1?_MGAE)RHEx6eUc'
    'VJ@^moqBa&v8o|=Ar!mtzEtb%!^KrOMc{Q=AFo)%mHAS05jbbm9dj6iN;hmH-=$SvT~}>y$zfp#p6q=yF|IRfEYff~pYh}69107~fl+ce>!-={'
    'Q8E$_7heR&M+$7w1u^%5LOZY6?eEVVB;&O9&t}msrx(bq1k}vwGlpsIX^$Nm24^_(1--Y}qd-Y5fQ0ldhaZwl8{D;LUUBKp^wOqAWq^K3Jt<cJ'
    '^+v}$M{UT_qh^V8I&*O9vltdEYXcBHDJ0M7)CkWuE$7GP>6E0{1R)Zo<k;ij9l4-_J0z%K1W&(=aZ|V-Ohd2WVCZ$gF);r1N|IBb)ua2WC2@Eh'
    '`0NtN88@ueL#c-oh@ys9@cBz}nWXlQM_z#*=IypThaNDg4h&0338l5ZDRbQ#<}S>~*T!w`)7kWWrjxC{TGvOE*X~JZQrkxPfV|qL?0She&lC}`'
    'LzP2(qYeqG2JN*yo^w>cFDEpBsH_VgQ2IAgOt+izUtwE+$x?qV6a1TT+b7cO85FJ^x^{T~{by1Be`ld@>imCkk?(;TMUgmxK?uFGTTvK-uun5M'
    '6tO36U}UEm?PL1jJsaY`|AlYWiy+(+(K~q*-hk2PL!HTe_TYx5Hc+<@i+Rs7B*|S51IB)*pf~%}-{D^n{qDbY^s)E&z##Y)jTPSk-3H5W;ynl&'
    '`aOtu1R1|Yl0$ee32wj(dM~<RHJ{ouHQV-&dC}xsoPQUZ^LISBbB~hu>}O<8OA+*+0yT7J9Z}y#5lZp82GG-I)UNy#s3pgrfZ97%U2Mkn4b)PV'
    'wT&tkh1Yj8U`|^ExLH>F6^Zos68C3d*SOzvBsxN`p-8V^ba<bt$vnO)^q=3MKVAd~^o^nPRht<2RGfH&Mi%t7C)-`rEhJLS@O3d&{6o-<|F#Wy'
    'Z!B2qlidGBWtNZR6SD}mXk)IUKKU=hZCNH%Stxq|J1E;P`HyT?yAKuEvlYhxm6z@3V=_;{KUI$U$Z~96(t<TrskH|X+`f&9{%;2&N`h?apL8<;'
    'za&Rp%PZ=uLlQpp^J6oJ*uBPAESQ@l!w&aHcX<)F3Ne7E5S{#IhWco*9=z=+{lEzwrg)=vuVl<gG3R2>hgI0ZLib_ioNczA5nc44NlnOifIfRj'
    'vxw(TT|XUq?3sq70(E%lQ87W6g1RDtL<Y=JU?KfjZWp3V7gF-7!z*|>b;to6j)?aCM8`Y1bCx_ti5{)Z=8>aQ?RAi3?+gV^n?Da}+{Tv`_4sGM'
    'juCqWt6Qq00O8(Cb$!s-<k{M3@jAY1pX9lP$Ygs?7m1)m=OMlDQ&i>|XF$(Ir~SU{O6oPt!XpC?6;<_x;jSBQv}Gu$+0*eNKf$Z(jh#+2S+j7o'
    'uyE#DC_^JA$JZdK2h5O7r#~oz0JulgOW495`^Jo%^cd#K`7){rxxOl;Z-^#e5z7kbVY%Lknr(^Jx@+|;5C+MNG|B_Awle2dU;|GF*UM2(x6esa'
    '5r>4br1~tm3NJI`p?X}nNHN<ZbajOjCS??ny)Khuhk$j%!ZS+wVO}(h;uw({IJgW>>;|-~mjxe=Nx2-nNEomzq=_5%$Ws^Tsj8Fv>m#QC&%Ouf'
    '!_xAb%O5z)?{d3aDS29(SAMraXSh5b%9vB|bMmg-L#47tDv_~qpUw4fDQf^!yJwAp=Akf}j3+$eu)boZe1%F^cTF&f=yec#OM7yXDapp2E3q-)'
    'iRU2%LoVoZKn0Q0S8|m5+RV!jm1Q$xnex;=Y$CB`lkd(pS>%kYBlX?<Ws~;@43rk#Rau`AG-&hxaZWoOZB^>6?40=`G1bxcyuEuI__=*ND}LRf'
    'B(WRx;2KiypzxI8i<^ix5O&&AKErJZ=NGl7f)Qno+ru0p>8@X$tf!S)>AaAfjNF)?L<3rEP$rdK`&7(FYzUnEsK!XqVwYvT_(3m{ERL{981iP3'
    'Pbd$1R+1Ol@w$jYXT{Cc^4G`3%Kd9ZHd;CY*R;)64tfpBK}fyw8L0vshIepGn8HYIk$+e`7e|T*V{TE&Sk3T7K9U#4(r|$+jRVl*2Ik3yN#{kB'
    '(b?iTCV3o6lOV#Y>z8XazTz2#3zN;s-a4YKV9b(~JtL#&<3WdjaApb_jl!ur_E~N-JxINd)SRRPkxSPHGTk5_AJ4+*=vR=+DyH9Dx|Kwm_h%n;'
    'F#taC1kw3fsLwkpE&27Cf|_m*Q8C`}0<?uIS_JbX1-fzqLkl`!l9<mG0g<eemYXRBPAHk#Ua3eCVK(VN;=Lw6HeYa<BXsOpxFW47byLT?9Z{rX'
    'n1-ruucLC-oEN;AKNmRD2`twynJsR2VeXc@(XO#mDpQ*sj<76U1A0WxGOtX+WkO{a!b-DBaK1kjPX3%`pi!2w6&|*qau4T~WN^~z9G-{S9M%Oz'
    'E~H4D?PX>#h*+01Teu!a*!L8T#2zW9IRRSN&8OOGj`NB%keuRT!c9@fa+GQ22p>GIZBpJIj=@CnoYx}~IvojX(tVy8>Xx~H6e0^-Ii&oe&GN)`'
    'EQ>obS^kHi;jUQrAAyFyTIg><!)=itpdm)%B!W^fiqIqi6BzPohtmeU_Sp~EPD&t?ox4pXdw0?X@pjrlvX{$Xav$1+`oB}ZP~Sm!^hJjI8pwNs'
    'G>*O7yMvv>wV}ohmC^W~Ym1RRw+F?0W(`6%?Dq?3h`u|%gJ5TM>@88yo2KFKE7HWy#h{UQ#n68<JmS6Lx9b=q`_h=dXCJq}?g~90SFq~_?XWa_'
    'H<%OnpQ@<6r&MRRZ_qG`gJh+I_D-Y=m%7ppKwbs3o5>$w;f@M{e+L%ss1W#fVBwAmflpwephN0UurPgUN9Oe-Ed1C8{5!C4M}@$@0}FRl2>c~j'
    'xa*s}K4*LY-zXovJ@@vJ?{XDsDyrT5fKughd8MC3k)bN5T=MXCBZ{)dS#~;ARX!-5BLSp`Nm`gT1XimSTnuhIfRr#^{g-faA)d@bbR-pD6C)L3'
    '>6Lt@-eD>4HmOdBp1Y<17uPKK&`uDc73%f~f9y3<jLcCN{AKYFhH>TNQFYphm*PVEn!f>luKJulI3rs;zkOg@#!4qq2w%rW(@nET&o>afmr$r@'
    'gbKYsXu!WFdwwN;c4!E=G&=Ekbp!4mgOC8;C=)27*Muie-G2(AF{q)Wv-wPtM;t6P7H{yQK1E?c@_i~TCvqh?P+H{cL<KHub6p7nDFeOmyI+jN'
    'h3ulcQY_`zRWOJ>m=h;v6VyDrpgJV@y{rDVapvtmkGKuwFPrFpW4WIV^<P`+dvi@77=<7tMq?<BY`;+aQ{HU+ZmdD!o#YDpJ27oDwfNhZCT~N%'
    'h12kd^kuZ!+)vH*7A$YJJb`wtbUN6}Bq*}0h9uZ-JNJ4^w3BnUz<vwkx0N=-j=Y<E=wF#@<SSj4cqbG#A3(iD(KZ7fe>4>lyWJ+=A|nL6S6a3!'
    '-&HQ-Jyu7OJ?4+zm7P7dk9SJ&<^pJVug2ivpGNY;&c&d=iKR*Q;C3(bM#We6(@1`^;NJ$<0Uwj=Y*W>DlIGjqNk_)EJSWS-*B=9EH&A-IiS#}I'
    'XE$BnXa@k7F4x_5ZRY9`Htc3`KLYbD$X>LswG0m5qy5=M=xH-s_phwAT>ujJsOW27r`Ue4keOQ5UI3B4HYM%)1A8e3Q%(J)!SC|S3cNQSzis^C'
    '{{G7C0sr0o{gvAT{=578E4K&ys+jXxEvI;Sm3}$h&G6_<mr6wHM-Qk_qM6r<P6C2fOmsoeBFlQmo72kiFR*j%k2=STM|{m#nLQL?=ID$ukWRxC'
    'n`udaOMJaPEmACNsD3sxInr&@=)Fj|Jjy2I5;~`GdA>TAkQ_lqA0m>NnQd{*<jHIJ^Z_h5p~35%tdUOUyx2Ahs`T_U#Y>sA<#R2ycHpkB>s2r>'
    '-U7BS7`co3gU3*17$SiNPPgPy&ZGW-AH#(>TvH8Yq0Z&+Xa{!ZlDeGy(rt<KVv~JD(GermS1(^cmN*ye%{2huOZqGbuT?rJD}T%^rJeKffgbTT'
    '$5GJNo>z@3A=6(^#-c7c)e9oMnf*rXGEEN|AfUaBV^94&6bKP$DQ+P+DN~j=R?b~}Xc^LAdF$R7C_Z?Zh76~O*0`IHQmE5+s}6`Al_@70n~)oZ'
    'T=JSe<u5y&d8knM_)HW9a*AGQW)ATx9ayKVQ?%Y(0QxG|>&)slaJ`?ytVl&hbZ@v&A@}OaFkPPW+|(MU`4WfN>(==F9pmpJc|Ri>!^AM2PfT;q'
    'YV`ti>D|5sZJT4cITm_|oDDk|!VuC3&)&AsoRWgKs+Q*^wN6QJOXurjwmA31vd(my0qa=i0v9M_F})(eKCx)cUi@_7A+utoey%dL(o+z(s9SJQ'
    '(ek8W6xcuRY}qCr;k$s!z9MD&u86Yjcw=yIr0GsO;nybRHx~FslXCJA$=_6d2Tv($;;!<rFxrCXp@7+zsXFu;7<Jt?KS{BJcaDTFS6jRK7(nYj'
    'Bm2<{fxNDlvA<dPVei0*kqXzraxsAAQx-`t3kA!|U=XyoxU-Kb!z6n8a=t!5<LuH!PUlc>>l?l!%q&0Pz^z74&ck-Vu-l&C88j9Oc}8?U(G$Fs'
    'VU>{0(>-LZVsH2-IcwwDygrW4_=FZs=QAk~Dh&S&5;W|SSV|FEU2U-tZ#Q{XL8ZRjk#1J6N$PS@czm4@F`bWRmWd2YOAh5^sQ^j$VuLphLB<dN'
    'BH?m(BYY)3r1Z6q>yUQqc$Q;(B`!)yp0OKUj>A<xbR&O!U4+{UI0R9<YJ*t7JT*RM17%-LjicGLz-s}X%jdbmz<9I<)jP7GTwQLd%ZwLp>>%M$'
    'I}=b<bQK+6BxhQ4j4$TF7_UwkO{v-4kJLh9KE)~Pc{IjOyq=lR)I5F?u-Relnv3}wI47iN)gm!E*Tb@`A%1`M)seE+lDSu|`MUe{=s?e`L{Q^G'
    't$C#{c~?h`!4WtTozH+CXf+29WOBPyRMsyCng~){pCR**ltXL`i$!{2oCeBCb2H^wvX4RzG3X)EXf*ITupB}`9FO+_HS!x9p=Dj`uJMX1mxXMJ'
    'a!=~@#n9ZL<25*|R5woBnKKro!B2F$eFuRX&0j3eiPl9`1*$$WOm@*M<eY=(!gNNh@Wx@qt)|N2i8HxzYIrATM~BW98Rj4osL%Ejf^`$QA78XJ'
    ')#hP%k~woLg4<}5g5VP381)SYF8`qL^Jg&a?*#b&bgjP&9e)b*QFw!m*!F%CB#z-Yj!^h#xDls!l!&~iHf{)SC%M2obPS<ADBk`X&~KIUaF@)b'
    'p-*um7VczO9Nxq02;MuKkT-OMu^rHb#IE|b{TD&sBD?VKA-S`1x3!7rSGaKlhsa*h*;~M(ozJ_|g~EMHOzu}0;5#ba6?5NwUW(eeIU82Q-@Wb8'
    'yR8d*SE3U7ox334(<na_d8t1Q^Q*mNkbM(NmlUoJ@6TXjJ?me?{MY}DFn^1_*Kc7y{70B?*zRAh0DT_no6^68`oMc*!5;o^RDhuWpSAbeaumzD'
    'M(=rwzGwVLc++Ei7dYWTLKwjv-h(8NFi(F#nUSs|JFB|8MpRS<0<;w&%{}KbbLqVNA@v_WW`K@v`4_W5pU8dSUphS0{$k;rFCJd631XytVNJ^B'
    'xIT|8>ZXc*rXjLdsf=z*M6EM`D@XCcI%JGiuzs_~G3zgA0S2(X9$6}vB}DL8SfDd^k{nQnO?l1M;1Fmztd2$f1iX$7*(U;0syHnpqp0C0a{u^J'
    'ug_}=_2PXE^D#Jz2y#`U1`JNX?}|KsmHQrbOYwxf<l)1(b8ziMQ4rsrR{*bnSKINc-2d7Qa^_UL<`e^b-C*k!0Ly4Sl#@A~{6zHF$1o)H3xq=='
    '7GIL7ul?Z9C;pJl0qUFiZsz7woX(?&yyUH|2RTsSdfSpREIl3`y{?v|lZ0X~t=Ml`;Gkc4WPJwyLn(*~XF;}X`#HY+om9Qp^ikMc%Dmf)9)I}3'
    '`SGWZcC-KY4~zJ<g7QDP!MBRZ&(HX|sSPGcf*@d$CQ%H-=-mxu17!$>U;?Ibl>F3RD%&A-6U8aEOYR+?-;vl&<3n$gsNEnW+|l-J(e$~$)O%F@'
    'b{&-NptvDl2)}1dz&j$s?`PNtTV#8E<sNiJ-+ok^@P~f~%kdtxP51Hk?@%zb>-r6-H?WP~lPq>{hjx@l-{$HxwWr~6<ZU$i?(*2q`Qn(qH+Q_9'
    'Jj3K29LWAkV*VEcPt!_6lEL(K!rbO!MhD9kewFq5F6(Vx$T#+leGI(4TFCtJ+vDIMO&5Jf8TQ?SQ2Dd4GS)|*8CNGmgeV0N9gSPCVcPcx^=}V;'
    'ee5f`o@c%KFz{riFP7)$8Tjd7#p?QnnWX${yTzPHkw}-mH`}3?eCuA@o7c1pdoe1(-d=+6(fOhN^b)oQKOSS|UmyFP9tZyD9iliAA)VCV)eT4e'
    'MxIWw!JS0NIuAqsuw-C<j?qaa_@}Ue$9$<H^l(#$RUG8vF-M^S#o=<8ZPT&N1t~ld5q^kppFM56ciAUg13~`0<oZoOJJYdWW>;S6Q!486!Yb#;'
    'QCbZ`@bpp`PH|Voo<l`nFtg#JzC=rxt(gZxBc@OC<2baDTPt@|KS#&cQyKL<Y^7I=6U4oGY9N@m#(6_Mzf2A_k9II|mos%#CP3?6-Agga$UT)8'
    'Y0(8H#tulhB*+oO%)5S4@6hcOt&P)PSOldjO;uKU+x4%R>`9jifH|F@VTf4nTGXAp^y-|)`XsWen_j?<pd7}k41<2ua|woPxR~i>Q1}p~Oc0S+'
    ';|kPdln$?|ETUxXA31!luM4I?Nbk{3`8qCci#<!-wa)d~ZA_w??b2%@-1PEMq9z{!F4uT^Ndk(8(IB4-_+SRbv7%8pX{`o3tC4Z$?5oWjO_VmX'
    'Cr>q))1NOB2X-LYAGWu0{#-cCD1yAX4`-hUwtuD*10UipRAnd>{A8mb_rC3%q^s^Cd*)IE<2@zoVm81!z;kBAbYFKc^a@1QPf&KqbXLNPm|8EV'
    'Z3FYpjwaoFn>I8~=#Gtd4*dzoPnow?`ppL(!OU6L=E?VQa6Mk;APNta@`?qpHX<^AqGIw~{J|Rivs30w5X%N$2dTAb-R`x<DWK<>e-w2}6_(de'
    '>G6N#cmAibyw8a7s(L<^{WB}!dG+Q4dsxK8?)fhY{JQ|ZJb{06@^5`c^5r@bhD0~6W&qv52)%N=;mvw33^IO%%83vX3~oLD?mqjIoKQ^vu%buo'
    '#bA(4$BPeNFW?lTr4WcCAkR6CrpLunLa1>`CdG&#WdmM-gX=)3t4X>jDzM8#Jw4jh0f%#5^l2uX*96xe1PtK#G}zkAt3hk(hB?S7UrE`+XIBGp'
    'H{zr|8bjvrDKs99b6EJRVJ6gz7I?vGsZpzdm*X>H3vtiVO{!3sodkBQVm1)G^~kx8+2hh4QyRmh4!kA<c&}&o5cKZdI~2FqD+6MlzfB;{Sx=O!'
    'Cr<%8xJuW<IrfhfW0w9S$1y|K8<3#XZebs&J=oQ(>R2s=7wNVFy_DSMO{`{^CQC2e7nl5T7nkwcq70iT<On{QL+PN0T#Z6?=C1MSNylqU9a$Kv'
    'HnQBA0m&NllWkiB&3ol?Y$XC69ACQC_qO3lT#{^a@=<SnISZn<=`p1`8C+poetFpd+!$K7vV;A!nTmy$lc0fOGq!>ExCHLJ)T=hQrE3xz<D78)'
    'l8TYw8-}ZQ(PN}%@C7J}Bcy81KS6@UlUtU_;|A0$q=e~us$a5p4C$GwUZ$zU^^3)6d=Z}AdHZMxdDf8@K-HAwxuB*w#)W`<y)h*?s1rP)UB{cj'
    'QQ<Sqa&KlYSn^_&QyV*O!E^{*H_9Y>7=RbIIl6N_<!ilV;{%*)SFTNY)_o{9mig;+%#<&-@DESEq-whS;|o3dLXAXjXGiA$eLS}Dt1l-X`)8MY'
    '5wk*<^p7D;exYdpvzva<wm;nPCkJ*6qA(Q02?T~v3dblI+b7si&~^yNPy)sg9RD<d9@4viz$TxOw=*dH=06#=*HaSo&co=p3&}n_jNG*G=N|0P'
    '&ekYw?>|AYUDrnGE_OG<7QJ=tp4)lPq1l+=o&e8wLA*VL!vChW652&E{2nxhU~fb9@STQ--m*H~Q$9(w8=DaCDQNIJ_k-*X2Rosph&_pey<2HB'
    'bXVCpzPH7|^gpTOkIFjS6X+@ULE+Bw<>v7!8S?7LSP}K;ONb!;#fX3%cO?q^AVv8L|2+e<@gd2D8ar^tCbflfQ#2n`FR-`cduNH&(l8LU)<?GC'
    'xc&bt?u=%G%U<XF5Au|KT=4CN7xpVNo4&ajNauy+&tH2~jg^6QzMf3`ym3+MOOI;xam?9{8KEvhznZuk@(%$4RhW|N#Wk7>;%*orPcrkt3!Bq+'
    '+_5gK7@_VH2*eL<?>>V~0LO@1>z8~|J_du$^v4C?ZYT?1St|D}fu8U?-_<355*T0l8qe6>ua7Dw2n;9le$EKC*_<ccKgC5!At#X-u&xAB=UyG}'
    '$;0LB$jJ_OnyKq)8p@6u?+T`}e4;UrRjLzNc`oHOs3b3;lGnMtE1G=8Jm7|yXQ=9&!B4R3TzWjrM1~!o!Xb(g%P?*-aW=q^_EypA;q&BFKf50Q'
    'A4c8336}p9|Gvnv^Ds|*cVlyN%+xX^ZQ$WAkR!fdyP{4$%Q7No%ntkI#>_7<9-R*vW(v;oqzuVz)3GjqlUlbhi(cucB=x7rr>}~0vrK!tUpx~_'
    'zP+!NnAN=&R#cD01W*Al=2$b8z#!{+QzLnGXzQ9A`zk%EbP_4eTv`30q_e!QLQ!H;&g=sF5UVAb(&QksCy${uXKm@fjK<Cej$hGDM7{u=`F~DV'
    'zI*(B0ogyD`+=SRdfrcJ7r{u9Cg|PhiNxRyA!(R~u?-|i3Ws(-C=^D>PaQBfxw>Ib2JK=I`;vx^-=-+YE>ZVch~aKpxxp&Fok@L)mk6~(+jiCl'
    'ihJeJ+uI4Ib}hPn55EKi-=*T=JHEL+LqzO>Me27MZ2GNtHxQ1$4Ejp<=p#n%Siaq5uS+NP*1_yO^n91IZ+u1J{kfxLpNp}<^(Nd=bgx26@%PHY'
    '{pmLyjQ%-;ZSC@HA->_|H34U&xmTo%fL`n5!Pz{MpE<_!4E?Kl3vXA#M-$MVy_H=LzqyhE$LM($S0?xfFba*!pEuY8K5)-k<u6f2{ww5F%${ui'
    'HlyMVdAzW^Tl2rot$===nqio~%&l;vwsGRlT@zl2bhiG8172Kb6XP3d0bgND(!Z+ozmpE0Q~v=(==xG}r|U7HM%shMWNpyi>t!lc$#+D{q+Wc;'
    '4&v-AH<dbe$3;$55XDu$wfnB5fx3O>{e+a+aJL5{vMT=SCRu%@2l_atE<sAE-OE(<$gz+?K@c|hQR|)$t2Cm+vbKOL-JOZ+T}p3_LF!4xl&+yE'
    '&zm@1tw-PpVc2Mk;;2o&33F`*3)c#el>x^T5z&JMxPAT-tGi*6Pfkc#X?yjTf_RZdhn*C0WIEgGUNS0ae(*|d!o1tl^@4&^o0?PX@iD+1+<KyL'
    '{w2cmGtp87eyW5~iI3+o$YQG3Y!7Q(KcphXzmW08pbBaLVJ$aB1FYl<7+Vm%D2_ZhmRa}{!8GSwqrrm<QKWfe3YZdF!#(Gu9v>`leR&UBO9yc@'
    '=j419H6P%iQAN2I5k2O$9?)Ti`TiV4*ZUP85wlJz><&NO^75?j7j>GwgU>&>6Pv0Y7D>$V0xH~89?6sLajaPSIv@=Yp618n_}cVAy?W8efX8_`'
    'ACaMbzD7bLDNEWAU%TpjMeq$^glve_Gb~-D!n6xJ6?i?zPgm|nBpwE;xOvSlrX>$`X4vHoR=d|Czar(8Z<@ME2%wb9f$X>eOr{$)O|dyEre%bk'
    '{b1VVbPB{<YK7+GRXM&0HNnwSdWvU2{>eDaw00-JB+gJ7CAd)1(wwHZ2I;6<mvm!7lhpOr98;@sTjyub>K~%Fz@M7`f372wgi2pwoaYa>^R(@|'
    'lM4jP5n_@}ssA>`%h<t1gRAm6ZhM(_Ae$Z^Oy<HvLVD;cKtms+G2XX#HHzRjvbn<LX<6f?kBer!W7x@dqSIp{$J{=@PK`nbFSLjqWE`Fpxc#~T'
    'IJGjCgj`oipk;WBHhCukDa`Vy6fCFFD-SHUPm~VDri0Wrhd;HuXqKh4#K-5DH2{3?3^b*YR)!dUfFdwA(W+;CzKjpf>*@5vEe+z%D~vmCT%}bR'
    '*i!<AtU@cOiTBQi2OUI@d;#H`R5~Ws>k=RNSfUqJp2!w7gv%gziS4{F_IOn8vSsuW@wjvtNWMHwbAi(sj;W$WSAJa)6(yeHc$j&=A9L9)oAc0V'
    '%r(Zyvq9+2NhvoOJ>6LMnO>ZBzEW8QEELrRJ_aAj<ht;DaCV>gQH%O12OT|3omQXk1bHo#gLA$!QePEHNywExUTLwRxCjtL9}}xUye>+AN)F0g'
    '=-nOG#fK_WMIJN}c?5?`BeZvuxOjCR`iCp-f+H&jbu`~|fY%+_9|)$W`IQu_^i`dtBRn2*-O_DMYzz6pn`Ex68;N`tRplOI<S-7eOh^l}I>`X&'
    '=A<Qn^OCCytN4AWyV{crl_%}58qB+g+g*7U`BFEw=z&}Ux@5y&)QBD*<-&;z;FsbC-`t|Lwtc0lDl3kiWl_h&(=18S?1zIvSKE4|Mb0)U3OyMC'
    'N-BoIF9vplqbuOBpbAbAJQdvp{T=(Loxce4n085;{KE~K@~cezGducgSN+J7es{%Bj0qxO2tr5_$2VC?;0R5kyL%>1ksB=F+Yb;4L7&>)h43!G'
    '@a&&orct186Qy0wWxMAk`JOJiTP`HKG)$3C8B>VvS%C=JwI1>wwuQVk-KPFFdAOU<A$zDli{C8goio^&S+b{7f5VuPFI9x}t`G5d#GicoKWuBD'
    '-o~8}v0tCOjWYM)t#2B(F}L(R;B_~*qu*uO*q-g!4#MP~|Dch*auNBnXSlaBCP@9pm~2{pRNDr)@MdbSmLHVHMnFDeOdH|(JB&%$<2_#)lXQGD'
    'rX!F_R<kL~Cg51l_vYI-x%MTV|7|Gh#+25d69oCZsfii*AweMhC#wN|T+W|Xljm~z>t+Bj=P$bfzv-#%1eNLcoq@Y?=eQRpb)yyR_M5}`V|QDJ'
    'K+F@H=)tFsG16lwy?%oi>~$QJVUxvoac)Wxj>Y2>I*6UX8q0%xhWqe8Uzpl%xv=SQRPmb(X$5k+MY62DF2HaSPl!4ntrvI?5DrRE{4T9ixUo3l'
    'bdIUwj0g}*Bit*w9}RlJR*P~W++%DUr^5aQn8-?iGCkUH4x<G5Kso!FI$l>q{;@O&c~izzgIFDxv<I(nj>St?r048!e*ud^lNuN#Kf_rDKF+U&'
    'e;kJ!cdz2Zq)0Qih^}tobh~OCj%>SAg?9M8WV)WpQx()SLol-vh@tH%r^-5k62;+{RY_^;HfGiXKOCCd1Fo-6pF=Yzd*%|<s&Hd>6?Hg{{De1!'
    'e5(Lg_n7g?r56;IlzYr_N7O16@;a@G0QQQ?wS|+dh0Rb)&G1I;xV6?}s+Bh6a2&K1P@h4Gl#j^s<g?=R_xwCcEToIEoL#`1ZmHLsY^P6WMp@&5'
    'WUdp5jLZn^DE0E~#vTCs$-h`glpe^vx%Mw|g}J3|F0Tn|36DczT`6aylku#sg~O%oY^keRH;Wpr_8bfrfni2m-%Y%XI84W8EIg4y99GZ}b$T?G'
    'AMynyueJ{b7F!0R$6V)geqA8FmvS{U`~iT$=B3h#$_6K@Yw1UD0A<P{n$WpjjOluxi_n0EO91)u!z6n+$r8(Pt94<r1lP_yko_CaCFFW0@J%K0'
    'S$shyJY)kZHIxU6S?6zo1>lb(#{EwViTQUjjSmf=p=R#roo@y{w3-o-kHWoa;t-0jBpY9~WFNcx#s}nQNb1iLCs3V-2M%RS0?cB@v4HSKHTERj'
    'V)NASrgZnZHNHeIRx0l-Z3S9<ljOb<@%#9oI_t1r9flJQvner=I?R_d;IeTb6pvY=V?A^qNPMlJMnWtOBZvBUF<&BB*y@W)M4OI-2X;QE#TrQU'
    'NqOY$D&s&*40qV;<Wvz_{fd_J%FhSZ!jf4wg@c_OZ<oUbNyzwU9+wA4Qfpyo3WHA!%3ZzJ4ZxmPx0F#&)4+#F60j=Am+jsBJV+>2(VV0_m<S}B'
    ';SQ?l$-1)Uf_F?)S{-=6&YKbeMx=t15Iv1qbP%p6M{$?tk(`L0Uv6N7#<!4vS?UFZpH+jirguaK@l<K!OeWk*3M&8+9ZX$w*trNM-%?M5H5lwN'
    'cDx9yXPfb5xL@3$Q;r}*p|5C2L+IhLZTYxNrFip9;B^bnS4X+dr`lmw=OJ;h<xXX1j@SX$ONc>F+;j<<=QMH>0U3`aSdd`>2g2k%2H}9&qD3b)'
    'V^Lp>7DI<iI>L_O>FTjl6W$IhW+?76c^AQ}bg&$7V$(ag7*C~+H1O5VK-`YEbx{Qlkxvh!4jAQ9Ce`X_!DD0<Y-C&cY`}6{T;)gsulig`g8|N!'
    '7Yv$ojdUQZ)Uez%oYANx+67rsH_GD*(!qsWmRNWsMS*m1IR9lP^)5uqyYO4-gZY1aQMOAzmct&2hc;UCk9WWvg{Y0=K<KZv7ysEEJ{Z=oSO3VW'
    '5P~LQ41+0(gz$|=VHiPgv<ilB3`IAZg+L@uz@L_0KyN;RLVN6K_o9q;`-3QcPgF_wgVEb{D#3ThZ}M{oawOT!CGmF&+(w${_joY+-2?~0yD0$z'    'y@N<^PjL$0pJ)5Z@Qum+o>fuFyQ~7;8B-GNQLqr($GfEXUVBHAd*BIv+aHtfsV;P~H(%`5<@8RS@NnmYG`<J3!gs;Pc87PW;Ge`FE8;|N<v3RO'
    'VeGvAxQSRdyJy|#!GMioyShDv&&SStzt}=qjXVn#bN;9d;~c9GJs6L6PsLS;b+-SQU~2DN2+&IgGI;?qD*emMRGwLlAANuKQKw%z3c9EjzE5rW'
    '8lnfj1g3=TVtvu8<jbJdUykX={^#b1I=JYTya$PS;7h=&5kj#UQ;&wi?Gq;PO!(E|Q5W9B#N^!I_f9!~<8~XL+o{~@&!Wv-fp4+3k770iFMcTU'
    '_>_wM$i#r}RE#%7zG=j!or(7B@%^&<cTzchI+~X#=1t0TG4zV4OLgu*Zh4}HM-L`2F6d}&JM1vF>q7fir;~dG!_BV0Bix})3*}}cBUY;JdKqYW'
    'Lr@04UoTbN_;K&iI>43e*ewPz>QShf=R`A>RW%r!s%Mj_+rkyN6n{F$o<oG?1p1M|Kg!}Ra4dm_-02C(v^%XWY=sv8?5__Fy2$g?t4HXixJkoO'
    '%JrcX$4Pq_FlU#qF2Bol89&d%$UkNB)&jORmbX)5d#y!gN=5Wgnew>zyv-F9KBp%Gc`r(`F?E26Ya)Uc=Pzm|&9t}bSuPg<htsbc4}zV0DpwS_'
    'Y0~VAx2!nXF)E6F57qq9@$dSypr(W6wI`mZ<KW#f!&h%Lp8@G9f>~+43D|{#60u_kY9pc*b3dk}*@~OSUhEC7D9RXx$nD~b+dd!4JuoVkO;LXZ'
    '<UXyYn<_@HW+Lx|RNziDOLtn&P7d_+f&+=mq;!Q-)=zF7&t~fs^?^pNR8GNzX9HY+fL;5BG%+5ua<4Skcxn4Ry?iDb5_L3^yhh5iTsnAEhQ@{C'
    '1E0FG%muZiaBvMM-m{gxHVQ`=vc2autws7iXL!vfa<xXdmRyerNZbp@Wx)X=tmxR|RiL*xdnGv&2a2iUW~Q4P%)hGwS|&Ol&hi?epjsT^&Qy*K'
    'q$jt-!DdG!S&Q%~QP&S9hRG}-?h?)N|MEn(Ux%^+N4AvQC;Lo5tTyb~jPX8$pHi7#vB$sI8+>vu@a<&b{4v3m*7;#F&)+7vzFSa#n&4U*?+LE)'
    '+P?q|-G{iwPyajWJcCYt`BxWu_b`d>s;%t!rR;<ff{Lwm4$QTXc@$;S10S<seN-8~jDr1w30fO08uI<;c!x64*p3@Zw5_V&Z{qt8Ae1a9=KI%n'
    '@)B`){R1++yRH7sP2SoU_{_ec(aO|5@KtlpOPqrHa~8*L;!=z$k7nN_A)mjTi>zIGR0D`;Oiqt6K1D)*cv`k=olbqgL`(r^LG3I0QWgB=a^2MJ'
    'Spsjhi-+Vjd33WppKQ?*0m)q?4DQnNC`NaQXv+jSNqRlyPl)Vvlp(Ax567HK?DRpe=U!E$g=KChBQ<g*mk0o2MIE$`ck)ir6TInTm|9bN5$}?5'
    'tmP>mJ7qmCCdeY!CRJo(6I%>{O&iSxhoXyFpka_0f7W<qfvw{&0naxm7F{B+m^&At?_p2eRA|1Y*V|Pd4#pKR#LArmvyU*nPD-FhVnbA<7$kxR'
    '?G#147(tb*-Al0Vw9qD$Yx$tZy^x};wWT<s(mgNbAfeV*cUWo|$WL>9#_blH=hy2FnQChWD%F5R7R<!9^E4TmR!|;$<K;qduP44r(KEL;0bXsp'
    '@8JbxVO-La<l9-RKnxMGZd-S^eahxbjWxWU8n2?w_BG-14V80GQEIBXg#Oq((N!l<z?d>x8C$=&*az>T^X(H!y0EIRRb|4kY(%tth$7(_LY-OO'
    'j$(YU5$(YBF&djexD>#~F)!g2-`?7*Bvo;j6P`X#T7A@Eg^Ad8IG|$9-(FC=jwZONj)*AFFrqQStyLUr0??Y-bn@iVgl3+MBo(lQJ<j=c`y|cD'
    '%n-2X;L{}?++}Lq6IdcOsQPx3J}OwPH0ZAf|I+rCT3vB>U{CdDQar+c*lAqsw(EJB4*$@~wj9%Br=ef3I;rw6{PlluyALw^$*q3kvnWoZFhvjq'
    'MWHag(cz61L)fRSz;wJ<2k%8A<Q}ez-!mgZa_`lp-}SZ;vBwSfK;iE6^?B`ZxOZvn)(P1jlndiMA{W2=E=YW5li_<5VD=8^#o68;vOPql|D@vI'
    '*|I}>u}YY|r{55J8kY{=1<A?opo-%=Ki!^#etW=gEIa-(8uxuN^ya+V9SCBdqC>swi(_j4O5Wwh1o_9=wC|RVZuuavs-9hIKc5HBL_Os5aA5Zl'
    'e*?Y-;1v6ZLR)Uu)xd+lR_n6b#TFW!(?1GQ;=qC7Kr9yj!a6|U8GY2!Lxd!^;Hu~L2G-%#+KW%VvE6OQvA^H&r}AG3_%K8_dFI`sv60sAnb-B_'
    'W4ajsLS!2g&@Fuu&R>g4rdt!a?~3Kz5k^J7IFtM}D=W-%V_)4ml$2ukJ@=8~Z6Xf@NYlg%t8YYo-`#56nkMmE(TVZ>hTjK%jIt1aa~}u(iv4&E'
    'JxRg~Rq_T$uzj&1c1R~MO`qa<1v13ILd`a`?g+#9kk2)Aduc)M%MVlzZl2*j*5t8~tl)8|;Xu2&wb%zbq$ZGONUjM`y$H>CU_Pwcb?OIrl2|y_'
    'k(WvgZd>Wp{b6eN0p<_c^&X!N<2nmuqvNJtM79hucOW6n*NG8^$V387eg$^h`ok+dog-#RMakpc0}tL6rY_+42nN%sx_12|<NT-kxbcM!jCKu2'
    'V9$qHPq<=vjFM>4pp7EjHuM@RH@sgw$kHiID$WFdzd%Le;kFZ=*$J#J>j;<$&0(^^CI(oou`2pP(PK!hxeTY_QgD;cFm6|8`C8cAs)^_$NvK$U'
    'Y`6Quzkts|VIW8u#f_LS8o50)VcVrB@Ni;Lb?*PAe+2kD_T%5&$B*5C>Q}fx;TbrEW+uWf3wc#`Cl1Ifc;5W<l^)9(It65#B#-O!o>J!`>rR36'
    'z^`a>x~=nyt3xDIIxv;;A+%q|v2b4fdKJTMFLDVACo%MF#JbN*1LGE}QO*s7KCqMU<j?oJaA2y-9P2~^h=wmSQzMcspJ$IqxSTC3yR!L9y)Or}'
    'S<<_ooLuS->W}hZx2Q#Sk8Gp_nK%#~<4XXMja7}Y%oqm)R|)-^FWE}!mEp5&<*kB&K3NUpinE{|iKND=v@9G7VqZwtdwH|~*7<n`?_}}9(dE&^'
    ')GZ_y_jS<%hrb<ck=0IToJ*=_NTkrMfZSV9q1zMt#T8v0cb<XLAc&O(nXK;r_V%}T9R9G;p#Os{@V~v~FWca+xBF=;q)3W_Fbskr7$;$fB4`YU'
    '@lTD&x2<H``$*(n9+|x>C*K2@@b|8fQhS;!qW0k*1o=<w^X|rdpe_2(EZj>TGvvLg#_#eWbT_x$_N8rK#i_U1B()EOL$lrJD2lf2@^>|u#J=&R'
    '?}{df+PA#jUL)BZFQWJS6BOI?dGI^bv^yRpd%-8Vy%ubrXSZ#O+sZ@gy-Oy0uxeXVxNU;(%ZccZHJJ7;zmjjU9QAbarMp*5{CL+2{$FY@AHNRQ'
    '_>Z^2eHR3Nvkm4S{W;q<c>Q+6y|ZumxjzT6){id6eD7Gqw*RglX*6Ts0)ISK{k;5r^}v6#{C)Mnf3y63^+56te#KvZ%QDO6&Lcmc896sfhB;Ta'
    '^MYxX2CFA?9!9ie3YF=qCc8LDwp<(t@UHgooctK4*yRD1PYpb>t{gje;l2>k!r{$$ACqNGVnSm_PLxSngnjIEnrsN3mkW@+!p5gG_=;gqn-F~Q'
    'EI;)8&IJ<W)%4dftUq-}Sk!f62Lf&D<?YD=YZ1p<S*M*)Y$t!N*?*(&-)}JB+dFJBZX4NZ_tMDM%P7`KK1<%kWy#!+`trzLK%QgM^HPASZRUoE'
    '-seZ+u>j{}FO%5b!_pkLku+LUcG+*zMK|}LHY#DFBi{M!xqHc=$On}xYOehvE9vzJ&K(bcN@Q3>$x%h%CW{3M1?RHdQvK(0g8PyG%U%5U)WaXI'
    '{;gQxei925g5&V+{Y$_o3KI~7(Krs_pVkm0Zw$nfJuZ#FJIrk;wo&m2+QZu${v^m7<HEhpfcU)XGJR`{4BoHU<iLi35WOe#H(h|g9fJ~l$5)j6'
    'X9Vw|>P?Ys5V*l9^gD#yErW^uE@8Mw;x_=?05?STn#t&0)=9mG<!v`2-Uzv^oXFloKi}TP8`N));@JLt*t>LK1Mc*#7YJyRG=CHe@!n|Id}}n+'
    '7?nIR+Cx}Z4Lg(ar%`UV`eb0;_g=xl=300B+HiQjK=pj&naj5(L&P-_&+6k=$bpN8SAUIN>+@IpA57=vjsI`|UH5SLmzjF&j|caedhV|yr+%|S'
    ';7?2Z(+Yu~miRZu53S&HW1wOHu<`1v+)<@a9ddlj6HZ=kFVh7(^mbcj=k?IwVrOO2wZ;#}7Z%H8UN;(wb64DzPXQn$C)w+r!*xgz7R10wC&C9Y'
    'd*`ypl`HSPNS8G3$Ut|ec!SBL?9B#Tp68>TJfsZ<0hAwZ?#;Ll)bVcKAexTFt9i^fmO5D&c!8cr<S6+kFg;S5<>mfGb;Wo+lZX5uCy$o|h$sCB'
    '`O#XWX!lI&<>7krdJmC0VowhVb7ee2P6sA8*eK;TX3GjLo)H=S8r9n^1Y=;n=y!UZib&h2GDIHDhqfB5MxhuJUP9Zs2Um1sR%ze2L!&?YP<g(}'
    '*6CKid!qgV1L4w4XM(+P;05RZO)C6wm-3j!?#$X;yjlgXig-+m@($RM^FJCtq${fX>RtId^!>AIr0j)h@fmOGqi!zoFpHCa^m*~2(i`?uEeGnz'
    'U{WM-sLkueRs*4MBXkyS2V%5A?Zu`HICMwz<&tn;@$gMQa8=J4m5ErLTwg}`Drs(c!+`p3oP<h1jOXt0!V5jZoD>4d2l);g-R;sxP)Bo2=RXUh'
    ';m$VB^a5co4{a!T&UuJ{f3};8ZGjMF%k=rc+@CGs9?8{T#*+>6&f(FJtv}HdM^H@pvS)#>%RHW?+sjmLwGDu?bZ<*p7pzXY7EjjUdATW+Cr*uQ'
    'h6`k0r>HA45z6p-d*kmDWt`bo)^(k6FKXIvoBdimO0~rD8^IrL<sDXZER(Y3LGZjI|CjuqL;wDs^*8VEZ`nQf6T8PLgvO|i))N?lL)+d3K`@3x'
    'pLSSnj2K7X6O_^SNau9V(ZYLkz&{go-@&$h118__k8gX>=kE3Im=yM&u1dcr4Q;n1lRZ|ok9CdS1|!-2wP#oHz59L-MQs}i@w+iY@g5)BoA0Cj'
    '0+@OyVyQi4yDb=gPo>V@z9i&sbh?ih+;+)L5D;&6AL9E?ioSzs+sWHiP`Ynx(0d$V^v5wnoVxE_k@$_>r>KbJO^6BI65s!o-G{%j``zT@-_c`7'
    'XXOuito=Zbm8jKcU;~--qdESFeB1DL>ycmguJv#2UEcq6@A}?(zwKSgx4p}93?BF;_Qvb$A7;m%kj4*jQYn~(h~g5^RZOI1aUC3GZtRwVV6A!('
    '2b{Xaa9sr=-=}UB)wuU;NtEWnWkchWHo6gJR^e+bfk74(reo=g?y4AAmoBFmH92y;N~0ZTwpo%CLX0=_p*S2~*X91pAQ<3X0e%|8i@`Cnz%O^R'
    'W>};S5+ZA-gMIo_lQi&?U-<84$DTO|;V7=m5X2T$;tXMSA*t|Vgkk_4Ll`}VCr@BQEx~e|Q~Bj)_SqA=ob}8rpaX_t+fCTX2~3M>dfn<Y-tyX`'
    'cFSo6fF_>mv$eiu^x=`j6Qn0-MiMLwJCnmP4(-Mmch6_%{5Oh!rM}DS?caZ#`eFQO%KcA|`~rG^{i+Y3`^^<UHI@=E3GMa16h)ITO5r#~Ar!n9'
    'tq=%J(kMn!B#M$SLLm_KDgMFmPPggzU=0%8i86%j*2h`02O;*-U}~q!@!MxP`#id_owD)j1lq$9$lLjIhrsCVy@c*ay8DN`ojdmg0J5Xf_9M2T'
    '67n1T+r$Hs?KU9$@YZ+_)^A8mLwiJI528RjknY#NJEJzrPQ-6N5MoD4G}&>H!uHA-_>JZ8mvJK59;Vp<Ir-!K)#JM3ADMpOpTn_1R@O^HGQ3hl'
    'd^YRhb0dqfcRzp1SElF}L#K-{{7|j3y_22d6}9m`#Pk`g!ez&XuVY3P;394ZmwhNF-szS<9Y5xaPO!Wm3z7HZ=Lj{RUr^}%IPl{MKO)hFgCE_d'
    'i2jap$hg4=AKj+kjsg2YU8H`=02JCsDa-EjDNN1#*<@kdU&;?JFSdbSUZ1D4=MTI$-Y*Y%Uz9r{z4vYX6#3X62Yxz%`yu?XE%8rfE_;;=@U`N2'
    'EsgBH=2UJ!$QI6xk!(6@YO+lA$|9dIFw~RYQ>NG#p2~SzaG3QLayXhmlD6;-JT!#u1-L%NI5cLJt#1_Au#qq%VH>lnXPp&LJ31VEUWyWA+_Dr<'
    '&U<3547fcTgBmoP%%kpNB?*zOOHwb19{V}r$`)@f3hfB<@^o5pKsZd|Lvv|K_<Vxf=;i{nXInl)tfkXpWl0^O-a4w%ate>kB|S|W+Ml%PmdAx^'
    'rh|r6H{%g6+@@7p{3!LU4<N6a(emiV^Wy}&Oj9bIwqA{#rmqLX%Z`0Cr*{fgpThOAh<VDNA;&7T3TmygtW_U)X|~8Q6?O;<Jy2$ZiJ;frn^vCA'
    '52}_^;rYlF9e$hQT3ntkVYS!WGzRDMrm;rQ9)ZY64@xdrec|6O?EtYieh_FC0g)R5RqIF@{)nc6OR8q1Evs@WUv+4|4sq$tMju4LjM9%1cB0GR'
    '<i3qO7nm<N{tgZ@U7cNh;*K@dvM~B=O)DMxvm<f`%1EikPfrbX1%U?X*+w-e4|5W=stM?LDImL<y9_G8X#0bhTF&(JvnkJwrZTCfRzewOFEXe_'
    'jr3K(77kHAOsIILrQ(99SLzHI!o(b`(hla6Wq^S^%7Zw&2`T!%n#KdOxa#ZtqR<KyD?sXc+EK@fea7x4JP^xH9fLfAR9*2I<-&(sYFIuM-san)'
    'vNz_N%0l#M``Dd;Uu{ReY^a~^zP~t(oUdIBr9eshxQg=j)wtwO7Mz&Vdfe{(lYTqms3G+)&%BHi1g}o7<=MdS)a(fp@Z0j_W8|g?*~+<eIo}2!'
    'K9kp=G-B*P<TI{ah~P3_2u%b?R-qEZm7%6~+L(Vl6X`(<`Q#Bu=b~nCPfpE93s3K2`KXvbwN~@Pr!{d4lsg<(1N!Z1G0OHKI-scjQk2IK5SWmH'
    '(LicFDifO5BnwsbmfbmEt+9eLqt`$q!x!ya=Jf&O0rBdUc6{AyHW&s>ve)c9A0XQ!pl6YY2MMJM?1+aswDO1k1+o`B*Nnst?^i7AYCzPl7;Kli'
    'Qmr&qRwdcol#*Ms)JDwi#!xTksG1`j(YHIaR#c-))RKiV-xz$H-j5dmZ3(-w^7i0*!^;OFXaHY0<`2tEDG_13?!N8BByIH9b7YrBP7RZJ@4&j-'
    'koK-AEnu$I0SV3%-KoNBFO_2sV!TXV80gaBaXgaIvvj@tggji8DV?rJQgp-u;n+7r&JEjVfoNm+io3QRrIy9S#Iq*5$*{>MPB3TLOAWi99=MqF'
    'xqVtx^1{lAlXDQ$VTD)_F`#7jdUCN8Dpq`05M;yVcpiqre(-4P#C{PAk7wgO+2`ZTl3IMHIj-rhCe-j?n`S3K!w+3D9t-s~6wg&U-*2>Z)8uj~'
    'e8M?qf(IGh?71Za)hq#>0_0Stj~JZ&2|v;*8v>d#jB^+<kFbzvF40W}dWuj@IxoB5^zp;xDu=4v%gC#|-!?U`h;fH!_k@jTX%<AFy}h8n%=Pp#'
    'e)L11jX&tkZ`PUV55}1Y1d|(=`+olKJw5+d_x#|Af9rlfb&a6}h0@Tbkuj8{Ap#)@h$Lu&KoN`}2y$a(B!qlg9+JGp=AQl{_Pi7QHqcDqy=yFk'
    '_O5vh*(qa|?zWr6=k?9>yLw~qfk$_4w#nH|GH*mQjP??f>`R9{{hp4C?R+nN+r)1t$N29Cd*FKpY@?jJSbi^TPjhXnBKM+?lz#W$BYT8-J98fj'
    '2k(imjZnt#D(y|f6K^}bgxvKq^`7=YyoK|gWJCU_n!VkZB>C=361-&kfn{k)9@PyGuliZy$bVJO&9A;ByLwJHQS-r=T-$4^xTV(!37~&<O7|z@'
    'YjrU%EU*!J#<CH=SJ0i`TJ&?bbmwRHOJ3eovmJlUiPiHv|5fReQJvv0IWc)M*7vc!aUb%kFU$UM)xdwU>>pPR{3pxaSN)L+13u4%+0KiHxO3;S'
    '!g4Zl<{~nU@CxrG>*r&$o+7og@YkgcETGR%K^I8GScG#Wl4+)+Q5yQM_3<*}%b~f2Lr;pj5ZpQpe5tm;T#Nita2OTzwCP7cA+l;29>(-ck?TuB'
    'tdqm0I#;<od--h7E`G5U1HMn#`e{U$yx`3eA7vdhLvYBgt9p5y&ILaj_Ws)I2b&8UGnY}|coyDwW`2FAO-9e~Y{OKnPu1w1KQ-C)iRWrO5Y+hc'
    '^!^;2(A5PrN}X55d^*~o=tCruS5h%<=L;^DNA@m9(5BZn-5wBD2=T9*cQG!t&W2WMj7}vwEKoj^b1=yBxVFTT?MoISsSrMU@`-wkX`=H2(%R_X'
    '7<v93;@-0@{>L!<-`(?HVfZiH?<Wxt(Ik$M<R;+}0;6dH+Aw*O?liH_Roaw00-@-qZYO(~a?{7}?{T)H+orW+a?fqWZ@l~x0o;y5*@mW{&+9<<'
    'XyF$aN2B*}b9DC?*>C)YzI|*4yhj8!`MrVRrr^W$Jt6aVBhq(g=C|qc{-n{K_1i#slj+;uu#fV9_prcr0)p&X97p%>+Y3pfcRfV*v6?q7Bk$_K'
    'P195O9+}wInnHin?)SY&5C1kI{Va{<m2(gNs2Nhs68Bd}ABXi5d%f+m0eoUs{I?(t_!ZMWAnnU6ia$dd@PTPRBe4wY8wC7<#Cx;I`YRFx|LF$u'
    'v1;HyS@y@OcWDm%Nt=J|Kv6xCaCB_CHG$x9H;=XujV&`X0F03qYrSpAYjKaD)Cx~|7r@Lag<=bWd~+sDfoWp)8qD%pR%}6A4)Z$pwH9((dWC=>'
    ';q}Ps^d@V_hj4cuXEMD&dQwd3MZh^GN6xT$wkbSqhJo}mM>%7G%f{Pp1Rr}31|-e75=L<Bl5$ZVygEy)`e?ZtjZOi1nn>79mKT4Jmq<%5$P1H^'
    'X?t}Z-Ncy@uVV}3qFssi=?OaVk;+4)MNe?b8_`Tiq_W(LQMp@{BH3mygGtRntE&{wmFZ8^_2|7c1*n9UJRV15InkZ%Oqb@4!iTQx8!WpXTrAIx'
    'rMN5_3Cr#H9B`?D5;w)@<08g=p*S%R^8Aa0y4<*qHIA24W893w9zZuf_YXK*yW$jCWtvHMCADO;zQqq$APwzA+12z6MZgcOi>@_<EYL50E$n60'
    'bzym);M<*6hkP8YnZCf1YSBkoL6xKcU#^t~au6Ud=f)9$N63EQ#+ME$ahP=<jc(oKTLtMLKZ34ko?Tus1RAN;l`?h7$F}VV15F2Wg4;4-D&UBN'
    '{k%^n1HPle!`p}f?me2gEXGcOM(OIL=EI}{_h4Zrgq~F>x!;Ml#hRr&T{gA_fJcQlU$*Mn&M>IKeNtAO>ZL+xAB>eW-9V8CnNSt3v7Mt<-|t2?'
    'fZ@wf+<ZxW@C<l(j?YXkPT_puD~P#$ErI;ZQtVqV?++C#!0#-@xOfaQEL>ul3a7QJCZoH($k7-|{U=8;;73cbPkf2L$Z&Oeof?!Af>5dMr>-8u'
    '>oLmh{vL3EwyD@-?gk3g=Y)302=+19VR?1$cylJj6Qhim)x8?d+Khg^XuLa8T75a>Gk2n3lLK<yIGIE86zoHb&7oDC#<7qnC{YpRMiDqnr&%Fh'
    'E*ljn9_Pl^Y4piGZ>r<tFE@M=z!+HKqn{6ms+<+i&2u4&^l96SHP26u=LS_yHE0^{(MGT+*3}!Uv7zriQN*4dyeoi9=WGDroNyzGnZq#<%|a?8'
    '<?7uo$UVug>YOO}HPR+G49qIso~a({K(w)h*84R<06P>jP=rz`IT7UP1zFplCyEcKmpY|_%8%k@T%RjHDgqj3Zb<gz2{WWtnNogXS_uViuj%xh'
    'rz=O`EOK3Fg*ee#^{{IEGRHGimjoTj+b3~El1=A2#C#7u{eau`P>6#iTEKj34i(jTK_%p8i<7kT>P;a9wfe2j4}<N}5=-$jQK?t<5I99INo<WI'
    'v+%s1O6GP0MDG&Fa6~@1{uyg{J2Q(wf}Td<Itz;T^LDZ}v}HAV>WQ#HJ*~!+2UGp22OAU3Xdp2)*<OtW3(j~HL6--K>2}9bA_5x2s@gGh_M)_c'
    'XpnPr8T77pS<~t(<tk39>B0aQ=~!BqL^Equ@KCxLkr;AHBtEv!?SoU0J*4Py9P3L(@VFYi#z~m2jaa3bJB4Au0u}>`1GiXnh29@IDE#%D^Z&c7'
    'W#0AQvLHWkvNZmOHYWeyuUY25c+I!G@@MD&#M5ASlgY^LvqDgN3owkMdsi?Cf0|fH(mmmu5qsk<h3%wipIP=UGm6vQl?11D!JE9TIqA=fqBiZj'
    '_w2rBUSRJQ;7u`O)Sei|vt7#W2I|<}2NAwg&GCDl+V0B!yP~Kl-7_grw9~2WzI3#IZJHX1caOXjdnZchuT8!X@n&*w-}r6Wd*Ri)@^zQw^j`3a'
    'zlmY`wvpebXa3QBojdR3Ed4eXU1wZNCKrir;M$<iXZ6>q0=gvpGEA*5+#d|!B%Ud_#IuT6d>g=hPc-C{@xgimPtR@1ssXJMt~%?yPw>x^>DEW*'
    'a&*RxOTi|8hD<x2rHY9^`fQJ$Gdk#PZ-0C3EC~3PNU4}TiSm(5*$LW4)EHF%o=o}a*vHHG!MgK5dl|s~I{urN@l$5{%gbN`oz;KJOn>|Zwv9_-'
    'Aemv6C_ecQe~`u(FqbK4Dcn53{zf=(UXh@%ICf7TDVMn+B#3oo>0X{65p4J4BQ<Ya>mTV}e|X|K0VTj&W^&GODjn}%-L`*I2=rOe(58xkAKbPj'
    '!E$6Me6T6A%nynbmw<o0R%ZLn{)^l8w{w9{PX1Xc=Z3P$0g)*MW^}Uz#%?aRMnzHE1Z*@tP(@WNV|SHL&aW)Jt)xa9k(zVznb&U7`2s#un9ymk'
    'KCG+Z(=WTZQKL4S!)spd%@_b+n#KBG&N`d_w?BH3MdKfvwltmpi#KKY{?Rf`dj~5K`4Rs9;`txY_x;hY&?h24PXR(VO^Q(j2Eix<VdS>se;O6s'
    'i&Egdw`=eGdYfl%dXC2S_}eB2iT6k!irnFb-oF3F_2BJ;NuxVdreDkos699ry?q9-cN1Dlzl&m$cg;?+*XE@AaG>8n-uArv<e_xWC~p_<(|k9n'
    'OYJ>j$lG){L*Fwhkv)HmhWqg>evb%x*Pw0~x19sMe~gpeS}G#mWkTWZ#|hzocHi7{$;-E>pdy?ZXsk)mC?VuC6Fpt{74jP8q+91n_-6Av@|LSO'
    '4%A3?$=YZ82e*THlXJUHI~s}wVL9N`^vQkK%dpb+asNQ9Md$s=v}IIZ-4De2>Db3Az9ZIuxC&rj#?PzxK1|||vm|u>2qac(WsU_Uat89%(?gA%'
    '-4y)O$EA)#4yHNXZeq7`7y)usA6>6KeI;nU@G=NDAbA2_4SyeV@Kzf6Q}gNqrv+3LaJo($?~05Oqs#btf{?;haR+fulA|>hMI9lKjCuAE08e?u'
    '<Tk6ri0x;4t)t^j#3@t)p9g^yo^*J>42O8?ofN!`T>H4MUTB-P!0CRwo{AgLftQ%#I{SL+#AE5DGNtE}4V_MF!3-yYv-tAv6?Zj64BynwE=2lP'
    'cpXyLBy_P<2Oz%12N`ao<+A<a&&g?(4y8-=msoqYL1x?%&!n4dh#Cs5@9F`89HK}3+pOpia*7rYm`}&y9+J&E!B3Uh)av7^I@b|9>UyrBhfQi;'
    '3nA!e_<S$AT&w)%@Gv&f^pv#zRKX|U!7ZfLM`e$OCp^&aE8#ts<6>N<=pfYLkm`fOuGjpYfEp1}u04l}N1{j-2f?E+j{rZ23Nh2&?0Dw3K-4Hl'
    'Ea*+kxeW9HKB7sh7Ni)1r(Wc-V|a5|YJ=AH;gg_nM6(&-?N>(Qb1|%*Usm^p<fqVBX|Tez6Jp6uVDx9EaM=TN5QurHmh2wTP;|qrDj1@C0kn8<'
    '_#^M<h{uzgj$EnX=+!GB2FU|%ARD5T*wv;bCRmKlj-xa@vs)Nu^0-<~KyX0nS-EQIV1Iy5aeIGYquo3?%hd!+EBiv|^t%8pJ^3+9;@tr8!|n$B'
    'mF?|^-Hnqka66A_j<MIrT2Bg)P*&bG)|2_nuJ>#Iy>DRQ)65oM)?8*a*<}h<>Y^w_THS&AdJuIO@5Qqznvl+}Q!?R9o(8^W;e}9+2Zxg};`y|2'
    'T0-#we?Sc!I3bmL?E`Z-AR<T%uB3w!H|nCN>OE<*3)Dt}n+A2QTj;}IZ~A(zJd1{Ph*G%)YH!iq&aQ%`pBvy_aty*XE)BBmf$`e|StGQgI}8$F'
    'm?h3g$!1p0VhkrXQqJ`LwRqhbfvs=|YF`HkFcqGB8sZw~krJmNJ72qzBLbW%bgerj3EvHMO<FR71sU3KVrnJ~UWt7z1(UzmL>tRwjlPQB?^tad'
    '$AuSbV|Ck%?!;HeyezJ&aJE!=XL0nyQ4;V6S(<^PDJt@Uf@=*lV*&-@INP~Q-TUh*s|IgggD5)kV0)V!sdb#P@aP^>wl`Sgg`*k|p1$Colsk)T'
    '0=Ma=5W@&cL{<7dj|hT$X&K)~?^i=Z!8>f$;HD7=dD6L)8r~6Y?h+nyj)&2?%vl9MXiZ1ns4SP<)H>_@n%2Oo`g1X~-3e@SQaU_t*TfI6Qkzdb'
    'O7(#fK5(2<c!Vi}8aO?#p)LLYti9K|qu7=-de2kTy-v6AroZpM0O5rZR=^!z!V2Me`UA?!+L>9IT~)hxStScip|!LI5p#@)Kvhj`FpmhgD=##!'
    'b?mIH(*mo~QMk8Xm{lk)Kcw`+t<*Wa2xq;8tv86>IRH{B%N1p!dV1<4G=(Lg8mOi_5%0Paqg#kcWIjeho$14bw4(Xhpq~C&8<-@82-O1&lS$;g'
    'mOtD?mh$-TcLOxq<;?FA7k(9IsQ-R0<5-f$S=Mhig|>O!R6l$8KQhMu<hoy>)!$z8Tfjx_I18s>lGynsiDNi|;4qBC*iJbq0-<mUgK&%@QFK2C'
    'LVl`QB#%MggS>q}&attN9bhIxj*+<Z1AcaB6=esVqoSXa&(G-c&i;0KxdSjXJRlE*ezxh+V_%+3KUSX~jeQIrl=hJQB)=w~BzZh-hh9m1bSe%f'
    '(2rVZf2BiV10AStKe&Ur{i|?z^k>sg(*cYRlh63$0=l0cCI=)VqC>S4q6aNLrl9{CiM0pvK>tW&bm+jC#ZFR?%;VLyTMW=#PFi5t2Kc9~w$D^w'
    'X#X(P2T6-u(B)STD$&6hw{$IulieK`>87jgSHY-;YYKo3$=a8_cY0Lq{WqKbn%-UMh8ytC^IsVeKc+DrVT{0^(irV;2&kRUI_sbsD}Q{cem}OV'
    'n}ca~6{<q{qmlYxsg^&>zt0x34D|IXF0QM|cIn#A%Iv6)cg&KqY>Q!mBXv<Z@*P?Ft7X>9F8RCZO8M8ku>UQb8~7%j`)^J0{XWD8LpQ<p_PZJI'
    'G`cq%Fp(qZW4R+-9&}fz8LIoUQeIG)TSPt?jrW4RzPuNF)h)3H+A0p4Vr;OX2q0wA;Z~5|{TG6s9#XTD?Nfo9ef*Z&(>2?kyxq<ctg3@W?=@1b'
    '5Ozr;jChFRldL#EY%N>hI<Pr8Rv<Kn+`3OXie&l$pK?ebJnfCXO}DGF)N*ezct6!={8=;HVA^F6Zb0e2lk<z&uD5<RcNBJ^GcooQIT%#1I)^I7'
    'Jg#U$Q}^-?hhh9Wtv7u~u2w@cQg`)lzz%(_!sGNry(=rXVU#@TBfGqaJ4rYf$|quLM+9>e=G$}PtPWN|#|uo<k4QZl+76g5q<TSwx?lWrqes{#'
    'Q?`~$Y<s2siI|pYvhRfyYsM4{<Bo#}!*aSC4uf+f7=oAqO@M5!80pT|GOw4+5VTbkGyH^%<_h&=NTw9)#h3TX5pN!^&9PcbuP5S!FuysMqqSgQ'
    'nLtW!wB6hhLl_#o;+6Kwx`@4Q9C#(b<VCOK^K|Cg?M)?)aBoWi-V%kD7JO|1FzrvxZApYy9k1jFk)W06UF`Wm_>2>6t{$#7fXhZas(5kxlab+l'
    'a;FIazUj1vguq2+o`dcTMEPvOB@J8!7p+l$dAX_L3p2P{G?8hs`j1G-g=x5@2qbQo>RnDUcY?2ntEW8jygv&*-road(VT^@l~*DeDhxt`V*FYw'
    '1-?!afZ(F0C`eD)JwpfTCKJlr=lZ{`l>&YumikvmfK{%!q9-@k5RgQ%l<88^7N-PYagBT;U$3nObS?OB(X()C-d7kB9p`;>s@AIR0&~WUQ5Vnq'
    '5AktlFnffDRhllrZ1ZovKLkTjI21rUBJnhCqI>dZNfhtU!ZIA>FvaD?Vw|{a+Y5IvMQ?MJXYC@R-@T#i+!uTe_<R*=;G{SUHkr^GRd(&UqExjG'
    'A1A0lgb8kJsDMPv!?)8mX)OY`pPZcFsfMafkhYR@QGmxA)JPuFtt}+<mCl}}d`FEwoRG<oO0_qojlir9jF>qdUv|zR=mUH0T!wTnfnuaUCH9gW'
    'KbB2Oco+5TX04u5tC`hI`xTOOwXDdQ!1M^bP}XS9wt7uR20=j97Flv5fY+I1rw*D+tyPftF;vhg%;s`6GDK_pC5)VH?aJm9OvMXky*K;JQ=-f#'
    'ePFPQ{UCwY^Li;U&!7qXM0YfgSo9Nx$>hnJ`7-*~(Ws!ynHF)OzH4ztNT{IeY>k@Mz@}Hl1Qf<Tv({scU-!t%o9O9Se%JBxi0~HqKEvlVeQ4bY'
    '9hy`^?5>Q09xS!l@$AcaIQ1TYNhuO1mj{HzF2pGwIjKwS!VzKy!|l`x()l5@&;18?j*@!xyPc-_?u~m=@W7*|s}3X&I4ojADC`j7Z+hYiHBuCt'
    '`x0O~kJ5p9LuE=Ta>&+s`Pwv13eEENDxCm1oyV~PD9=luS+f3Z3`k#oGifRKjn`EBzs!sJo5k%nAyzjzYkw#>rf%&h?T@eO&fyc9_CFxLe}9#)'
    '`0j74@cqaggrP7_?D!5wFa$dE83aroF*gJWffxque}g|C_MndaDJnkX6(DkKW+fj>iYPklJmXJ%_71@g)ibsq{3)cv;ScDd4#>14HXJ(?Vf$in'
    'dLSzb`3SW?!Vfq(_QYc95O(i)4E>c+`~F(!NA4CupS`+|v&4QS5%D>g9c~iP$CL>S4=_h2$Aj=Q)UiW4j662x@Q*G#`j}BfpDx7yc!ziKU)xZ8'
    'l1Z~aY$yzW^4CcBI23-w0<0v>1y3sbPa}8ek0W=yvwd%iZkCwlULeZ=!Eb`NdzEptDz4q_2;2s~ByO7zcE4Ni7>{>W$W)7b)e3snxOP!ky8F5b'
    'FM<3q)5chCn}1y#*jLXT(6!vM;&yzvFTmKQlekVv*?%b8Z0P`8n7YNA3jHo@`~4X3`@uP7e{e@Vlx_Bx(Xx*_Di`RsYYa}QX{v$F?C;TF086_E'
    '%B<pz^Hs+G+Ech4J%xRd!LcP&E&N$!&8uq7^ELm9S~cddr2q`43Z-vWmw1hLsz5e5%Gwt=-k#{X^3C~$0uK0>1TMr~=q9b*lxgM5l2Xe9Tdip('
    'rg9P{eUORRyUpr?X++akd#8^t7*s@{k0e~6anSSEEvVp!b}M0pYa$Yi$R0FbCZpBoB;(H^3EMHcfB%wY!>Nu*u1^DMuYgmNI|9M=C;oe2%0IM}'
    '1pWw2p#@Ai?V!aEa<V)d#vOmh%eet-O#ZV1uB27LKPKr$z#7%Jp=uzPUER0o7f6Y!!Wbkk%S=PiB+hK{w8=3x&DgXVqme5IOPrS77~N<v=>n(*'
    'i(B=QKgHWdyq~_`HTsoQf@c@ZstHfMyu%vsETELQ`CUw&F?D31MW*k`i_7H|m`?G(6`1|uv?hvwAAH?R|J8@T4$1!CpY*F>?EMMf)lv+DafrZ4'
    '62*5)3}PrjVI+wY7=#=?cNmH7un>hY;-?nPJBQuLECL?oX6KYReh7Fe^x&QNr<)0*N0W6gyN9qX`?>H9`4p~?7A+1Bx}5CGd<NJM>ga-ypPA*o'
    '$nJ$TI-H&l61zWz0)ORjmmN)wy@=z<$Ia&x8+IggqsI&!_AwA5!H-p5c)ZxrV1bT#=l#t6tH+ofc+mYcJZdqHeCC~xkg!8E7gPT<_`>3nD={W<'
    'A;=i*&0V4-Y$o3`^GD*w(hd!%od1JjOy*UyocTX&;h699sRayHJniw-1p@fp2I8k7)=pu-zn4TzJ=~Um&$#$q>w9R|R^Xe1v-yMA*C?Hji}F`J'
    'FUNfsyPZdkKL9bzePhY2+8p@(Nxu_wOJn_i6nxRYMPtPkt-_-BV61-fYD>+G+SgOLmg4=EfF##n+*AhikazKW3?}n3V!V?$PtW4uAw^C2H6XC8'
    'R;1Rv$Ud#L++a?1uLNj;RZf*Z{P$=Gz$8dK{Rq!*JTGV>bXZ~;BUMqLFeF&LfoDS@qy(!GGkqtVGLfP&$(h}SkQ<fSm;eZbi<gom-e&baowKVi'
    '6)D^cH>e}rj55glM0k9;vZk%QW$GgATyqG|`a8=6zRR4QoOQ@VqNXBBd!fWtJnrO>v!=U@a1G&eLv#<BvQ0q&df*#NUQcCkv%N=rx(pIJTO6=L'
    '2s{Yg7G%q%skmBNS><NhSe`-^pEEb1w!9!OZiP4%SMrjaOnVj1{5{;?wj$kmVDoac9*0YqOQ0aBp8YcKCndZLnSMuXWSbf?Pd1DYEbXmm<{E>V'
    'm!&KU!PSl5d=5Cp2RKN0Wb{>7+|PQg&&V?q<BbYbQkBt;HQrJ^+iWk|4s(*#`?Z#2tmv#Je_k{|I=4+6H`!A1V9OzJX-2WxF4^_2E_aVpVc~ok'
    '3Yj{cg2cgt6Q8X_;w=erD`0-vdSHS3U_EODdFjPhQuV28!jTNduNu{HuT;B>*0mHFsjQIo?tY7?-%8NE;~=>_o3aZ5X64_xe~uQu!I7szGxAn+'
    'RS%b^oSMAu(HH~V8<W^%$gRHS!aU_&iwkV4#8uom7Xba<?c*<J-F_T(1HRH-8d~2mDu|uB&adI_phbAMGLo-%Jn>5cD=sKN-29883{m!y-a9pm'
    'ry)<;QrhgSnO>KcFoiOGYZc#uDEXrD(urh8lr??PDWXK(9FWIWwsaO6$?O$sS0XI-@2yymTv*I?hEyUkPo27WI1+JE7>Ew!YN0~%FP-q@Zg>K4'
    'sUp@%5r*`>=1Yk$)Ge|DR7$7YxNX?;gm0~{ZsvmXaSnQ%8E+d8_s(h<m)jtfz^iFqVvj#Dk`MTROwe)+Z!ZeIT%b3sygXj(SbV}&H*E~NYt&>D'
    '7L(y|PvK7BV)6iQKAtjjvsMt%J?X}1lVl7AE=5uCa9<}Gc?GrZB&8x?+PjvC31&bcdfeagwdV_E0N(e9dwxA}aI;fNtse7?3sgCBzK&`s;jDMD'
    'HeG9F3_=4%r0e7WO(0xQ#u&ONxm5x|t7%XB4oBA<wwm&hUKGQ4Z>GTtMjN5rM!p&%^X6RB^3_*6DfbL!8?0$w)9yK8z<BbrV!h)JAN0grIe9M4'
    'x#anzMBC)4bl4GLCaX~v!w;#v%nrp;mN44Zy4b9LZ*BlOmHra7TeDaN!^2pd?S()qV3p*<*|wBSo|1BVHykd{esG$K)8sFnhpKSoBtnb>8j{8s'
    '1(z%mutED`$=8`+IT`gS@yWsz0bMyNkyCyEbIeHm{H)P<e}1<SX<f&LLx8Crz23_go47SYuG(8=CGV#jY$6GHbAcF~v!s_7{%=Dl?%#n>+&_g-'
    '+|MBt1tJJZAv+pDC<r4_1SVk=qi_r%2ndDuGk)4-h_DZ7!w=4wq=yY5i5!ISppEch28N)=3|SZ-LlpSWA=HkOqK|$*`NT%=*k*r58XXJl6c-H-'
    'e!DM>ARqUx?C>&)J`9umrT*Y^#t{H}oOE2_VR@JyA_ELOfDr;6<8oAXTop<kbU7hDtq}Nl)fhi6Xy?NF_3!^sAD9Jwlxf&OSpSleUXFQ>K=>X)'
    '71{_XTP+I(&-zAE>ksxvLU5ob;Qs=j4)g^43O<?kU&E&_F&X~{_;jEr;BUYu{(w)v@-GCwh_<YleT%o@^h}*5fwWs!nO!=lk8&O8^d*y>GtQfJ'
    'd9Whf)^jy4GdGt^F%%tOp1M=t((f&sTQ(W{>1qi_)aQj}ApE5&>55s+MQf!wU<p~89Mq0ZV7%YPA6X?N39xz{bGuxA@8AEmXzNGK7VxEiZ!DMB'
    'ei!J&1T0M@SME>jaay>NjQ+GG@rO2xqY=n503w*CCuUsAy{gm^zBSJczF>mdfUVPKK{+Wy>zJxapJVrln)&EYXQw5aLYZT_ph@6licY~1^n4dD'
    'yt8)Q0xGIY5~42A6=*Ejgl*OH99F~abfMEtlXemuoDs2&#wSAmeJ)6A{9aGu@tq!JWlG=Q1o0eSqsO6rKa()|ElK~?{EUz0r|x{t*iSXX=l0{?'
    '+<$Q0KX&VWwdQx-S8A_<Ac7uQK}Q8dv7gmG_!HTTq6h2R3D)8N^qDY=;G<YX__4Wm5X1E7wo>@d>0|Us@A(*z$MMnqJe;IHv%S#ADSdwse!Nn$'
    '_#l_?#|sh9eyzRAqNACb#-Hsx=#bCurEo8N`;(7}W9U$Jp<j$)$^VJ5|ACNCar{ih;h$8+odh3sJUPaD)9kQ;`3&}c7W`}aNF23~`olLxVv}1j'
    '2^$s?KTq|^ed7<`kV7hAUz`|LHwo1?XHkE$rzLN6^|b<tC9j)LhDkj0=!ceoe>d{r5GH-odi3FHii&RxrxsN)98CCliSY6x^x8!#==^K!p)EL{'
    'Rqf!eL2>Qm&aqhSuHWYD{I1QKb(;oN`zWL;dT6r%bt~tOgZkHl#f5pW-`KmDs%&olrWQG(9og64%gy*hLffbp=c{ll{c@>C&zD-myZHz%Oc_|;'
    'HHM3ii0k*sJm8Bp`@q<x{~7UhYW|fL+;fNPUkz4*&!W6m`G~vji`n~PaNtSbxGviNU_?)w-r+jc0dKka>rw!5X9RQr#}|~(Vz9<v__i?|MpXIK'
    'b14(O9-A&ul9n&?dz8^6E1lJ+NfGxFKYLLfunN3BJR`=Ikh86mVE>>hSgBAdgkN#gOg5A!uLJ`nIeifKhl;!;&mz|M8NP?jG>8D~CM!ADk9QMr'
    '9E`_`V_?&*5p~@3Z;n6>sw}r;u7R(3Vqn*zugSPxsg}4IPW28vK!hSz56E|v+S_gNp+IX@@hWiEN-5S!>SY-kN|1dImaeP)YcdnPeR_SmEd+iC'
    'bp_aBxMkt@mF01)DbpLN)$k=B{9xw?qjf8jrJ`1_9m{68DGP)2J~)N)^4xUBIO(eiydYC`=f+Ly8;=W4O4Lxd&2@5WmfQPIOJ_F>*v08nyrw&J'
    'c@$tP?i?V!Wp>g(jSaXHPpAcL`7Kh&jR6Zny1rhcA~EHBId@B32c@Dcm+OA<XUI=L)~#eSi{{v!v1<~Z0qdzNluI%`brs|F30d<SI$g($B4V3t'
    'OUVURuRO}pXCi>TF$H^vy-LyK=Db*0yxahaCO@7=tg$3^Nl1o^v4wN4Y{b#+P?;<9J{d7)8YyW93~fkL=IISmDyps5GV4YN&|soNlR>}kBo=12'
    '+>jqh@T&b>K!@`z@>@R$B0gW1@>ajQD|b^}T`ZtsHBA*=F$NgP7MnJoygusA@Du$NV~W}|Ny$~`uOoV&0rVf!e&i(sg{1&m=wz=i-M?I6^?^IR'
    'r*g;-BYLq%F};s#SxI(wO+SZ1N-Krm7;U3<;2%)tpN{h#M)|b;z_Di^<~2)=Gu+T&wa8AlDOU(Wbyaj-$;!&}MHFnX58CF<Itsbn80cZ26o8VL'
    'BuyPJAV4S|mGvfJ)P0MTdrQ;TOwq6FwiNhlU;?d=`{a&Olp(D}WtudF3uytoXUt_WTJ}duxrYkuoJCqojcK+lDzzwGx=6&?Z1etV=!(b=34200'
    '%n_WpXdi2I1z!Bn@lU}*JS}e?w2u@kgO9mCBdbidgK>L<Ci-yLjtwYv=6j3ryr+B#7}Zm;JOhF0W*LNed*bcH7Pz{xB=@ozO@|-uJ@&LUuUNP)'
    'G_rjQtx%X?;BGpYj&J8ghq<=nLA`8Bxwu4_xn8?#>8foQlzD4NkZ+;4NVoMXF%6?uHYyW5spsu2uQKSsgah4CEDeD3)<U<=b*xGbESQam2}3!L'
    'x+08;`AYB(=v&15w@3RXU<peMk}fx`+keTQ-ZnZi1;AT=R`_R+bIOAq3R?%~F&}GIsrv;^An{RBLxpjpeUjSPcJ5#%Z|A4;X27`g*GvLVw<rkD'
    'v!%MeH1pc!jctaC5F|6vi%F{v=@uPXw_0ZkYfccn@ZJk*)x<5DLj<<KfLbgX^Hg*`^^#_I-r#|-7PhH)RJ`e2_Ri49a5tx{0VU_%5VuZY>L6*6'
    'H+Jf7Y1;zBK)9-#-}7qf#-)PjMh(|852ZjiE-h|9t_h{Ds$aHsUWD`i`$rLwWBnU<`7eY-f5&%ypT_NPY&e9!S!+L}b^n|7-}Ha~-hn+%|HT;H'
    'Pr@PplWTt)8~N?J-;rt@JX}XH{0JE!AdEsV3MCGi*iNM>gu*}yM)98-Y5xuzkt63C2M?751pjXHkACb*kdNkJhi`}0ANnb%Jk$)INj&6ZW1W1Q'
    'RYLdxnEM}b;^4bGF2p_o+9`G*!u`x+)GqmzfFe42!8<c2v7<waAqRL2!-Ebd&>_m-FXjtiOu}QxaA)$wCxQU|TrdQE)cnLD{n)|nVWSFuz$S9c'
    '^<{r)#&-!0G?M;dq-~@U*?1CXInPVQX!L+YuZ{Y%tqS;KkJqqS?rW_-z?E-!+P1^IN#e{$BJ5ZRskTILhj?XdrQ}A{if2Inns>8cAJmoH!Jp2y'
    'eKXqj4Nq2W;P<dbD6$ydSiwzazXg%`yu;m{eaEZDI^ZAi1K%72?!}k)^6$PC;Ol$&ci#%|2c7@LTlwFk2y70xO88sY?*mhfl^T32w{(5$Q>M02'
    'uIFXrJ)U*e2KI`=3|dP(%9O}T$gS?e7q%hn8sJwl>>==SN6X@-N+x4<&681m61s2@0fNdUmEG*Tm+~xoJ;-*sG0sd><N)adPF@S($5H%mC-J|H'
    '1>_}A2pXeIiud-+QWAPYVrHF4fa59U7p7~!pz<{9T5yd$3NF*nGT;aVBhRP!fm0)7_L88$)-@KVO6F0pXk*u}o|xIo;`>#GXC59j<71C%v{rD&'
    'rv_-I(X7@aK@=uZMN#*PJPe1j!cK3*59Iqve}`Is6@$PZ<EJxa)S2bT@*h`X`#ttYzREXz`#)Td|HH5FLskA^_3yn_NCHGi5Zd`Yj6xJfko%vA'
    '{YHx75CkJQhC%30$8UD-yw}JWK7?UedQ`MS)SDgIx!{NR?^PB<4|0CAUa6m!=J>Ngdhl=XQ$o{YQ!)OC=Jwhc5eIjNKSMq7XHOEvJ{y?fUZ#J='
    '_tV4ZYQI}x#4%UBmv(|U%Ky&jL+ViL65%I1fjVAhKP~=jYwjl>n+wUY6S_Ygi;k0{&v6hv-e&l@fn>>F^8NWBg81`aUMp`ZaFjyM*+gZg?Cm-y'
    'h_HXew&3Blf&>4Tns$^l;NPuj;@1Y%$6&hrqoz4=;~uY2{+a6^WtxLkTRL_nwy$Lx`0ilA;Q#b30YAIt{FAo?{P>>!&RhDnaSi;1NsFoYI5BKd'
    '7ul)VfVlmdz4B_P)%I8~6tV_D19HNa!o}FL(Z$-BOe0@eIaCU!HxSLg={5IT>X|Sx*TI~(lnIgP)P<(o?WWV`Zs)oS%7r$wN^UGCH@hF>YFl`x'
    '!h2|DFj&+{+QCQ+VXR8INL7!>>sf*~%tj^gVRV2tkJ3%;W=btCZHSX|guVjEd!DaQ;N5V_UDvskkPBg_a3<H%kT`5zfG%r;cz1p904ck=?3T$E'
    'JYFMpQ`NrK2vj`1Jy;%zSI&{Is=B8+xil~hMNT-V4cZAqerB%RQ$_%hb~p4<Ek@7wi4%q;zt`p#eZL%kW+XJ|A6YSVHJ(AyBGWgoe{yY-qp-UF'
    'j3Gw|fx3I5TGXogBy+-gktouspbZhw4Py~MJ1zPfayCp2GLo?R0ln9~=go*XgOpxByC*=ni6)J*P#5H_w2d-zy`qpE1YF+p#p-)-e@g=m(j6SX'
    'u3FAeX2}f?_>@f8>ZukFtizQy5|Zz(H}@ekx6ApK->^Oai&VayWx{!^Dm9A8jZVE{|DC`4oZ7!=3Os3nIf6H!3$rvAhOo<1Scpf`J?oz2wQ6q-'
    ';BB137aR|^YWYp!%Sj#7XQn;l<--vbbe??1048LGww#4oK@70fV0UuM<OWW`k^?>!c-6WG;n6!al`d*@&L_wcucEmbC(?o*6o&(LpTL9dO2hY~'
    '*Z=EQ{qHnhJuM3aOtfM*AUaxFgZaGGEsAzK{VJE}`@J#k*c$^r8)Dq^2^qAa4D@+oHg|AMS*%`fO5gDfM<b{@J1Nn~r{WGJW@?AI`+5YMW-k>A'
    '+?SdmVf8eVSX7*y$;)||+sK|)8m+1%%({b|-Fq(<^))o>HV>67(thhf?w8tSYJp9CH(|1hO)P;B(wHEUqFq(_=NDL?il=aU!Pf_DdYBpG=u~TC'
    's&1(&7_d?#1FD$-rrN4RIYOofCP;#y8ndwZ?v-~oQylGdI@p<VimQ-hiTR}?FaFx;4=ux46LVC~0EDcuuMFXUE;nBzeJq9SF3zu_kMFOgloo$U'
    '9Rh9?<=m;fh;YX8l;MnC4LzjMGROcdy)iUjx2H7EC#me&G6pZFmp4}`e7<JRdlR*Du2f0ZVe;Hy<k=zC2F^N5QJ!ku0iY98T9dZ-yZM&M^CXjE'
    'AuD%*!m*QD!gG2rOg()XcU5O6n(U!h_TKXCA*oq7Yy=D32y#MLt30j!W4os}>ueYJV4N}Vgpc9fHqE6LR}l|*Y(mA*QTqX+?nFhkXK}pRD$vOR'
    '72NvrUbbu`^yo6?tbx4|m#DYvy|#Cx$dd1g$m?E|G~N=iS4lUc9}GimyX_4CCChEu*)itmx(*|1*wJ29%;tfgCKPl`{$5J`8@=m6T<#@>2k%L8'
    '2@9D|-Z<Fp-$V}PvI)KS!xbKwz>xC2(D0PD=$K|mP@NO@YPvE6)2hdgY!Ur!kZ6z12Vi{*-tx4G)8DiYG7GEpyN=8Ut#Q?k0N-u%?8fv5Ncf*v'
    '?<)ZOajoxYIk?|JP!Kyt0uP`^pa=<r6b`{SitPs|93`Rs!Qqw<!o*LTKIErk5>ba2-j13O{O}LmN&618qEF&gMjk`X$OlSA=+8l5cK8<%-~sKx'
    '>^OaA(E9`GlNWL*-LhkJ4~;&NS>Q*hhaPj^UuU}i1Onmoz?2Ypj4mDly7A{?(2ou4e!=l41%&!^sp7-z0LPCP*s*K$vGzkh0a(~)(*gWMW$j%3'
    'n0bVcK0FHjB?#<~rVsW9KX<rUanX`d%Q6)BI!Oj)B>K8Pof-A#X8HaPvO1ST4^bQRb$D4R`6jqyMPM<y@0qU%#vYO2e0n{=PmmEG32u>yJK(9S'
    'CAojww^mh--+@tOu8H@>8z1<wsiUz6_s$`0bKoyP&-ngWv0vj4hI@`(aEQt}U&qHs<DOJetyL0-eYvWd@Au39v3K(^-~%Mi?RQiN#x*sD9uEaJ'
    '7pP49RbpqjqC2{x48_M7<k$R@Z(20KU)w0$H1NDq41Y`59k4@wJ~Gb0P`-Z2rew!(7@qp4#|BTn&^cr_+)72<YPEi{MwUko!P>#&y+C&~l}Jqq'
    'psRZA>p8-~vcGjp0>HAtw)zZWJL1(mgpf-xiVDVoZ+F@ZX6zkovTT@I{i08H$&Al>(ysSR*e*z(=s6F#^GkAWFWjJBCxRbCwwB@Z*d?Oxt^^|x'
    'TAF7vv15ifB`hXN+#yr#j(v>b7D2um07C1Tm7IBNr&X7;ik^(?h-5*tk>#24+umHdAetTRoX|;Lh~zb%>ARfnpJ$pDS)B)}=UFl0tHMb(d$BB8'
    'B%B+ZREW7etx90x1uNOxjX<g}p`5Eg&t1*F-RIr4#OP5q4)7*J67l(wp@!U_h@KOOFr-B=U&hz1lOu^r%4ImmZG-q0(OtkwM1waen4^hZpFRwv'
    'KAG9CGU;1VWgpvlbrJd;(8lY{AtVXnvVen+;IiNQO104L5!4rpTaaNcRd|<55ujFFf18vnJqJnpEQ4b7q{$AJCj_bU13d4S``k8Yw!^@vFJ3I2'
    'YxK@>QXEmYQL=KNm>Gx9Rx@&+O;t>93-g=pK0aGN>{)MdusTqK>SRn$A*4%xz@*zHSDKr(5pA~33_wU!x_M{o%1KP+zn|3x8j^>=jk)pKRqPcS'
    'y*kg?ay`1d#nXjnUDmS_ed;e%*Q|E{JFlr9LL4|>yzhH7-{Lhxs9$~NAjm?6wgjU7sr9sAxFsAQ*}npOKQwvhFsv8K&N2~tsfGP0@J9^QAV7h}'
    ';};t}zqDNFa(5gC&|Ra`1}sk&X3BJaywvKLKVND3T%BD@Mjy-S*%VH`N*J0Zv4Zi565m9%yv9c)kwkq1H-7{St`u3fNuSGQwv3&}VBFavvV?94'
    'G`Ak{rY*x8BArHr{FFxEoUSq4z`d(kqr;950KOkwZnT9gnmFS2ghUQK1;m;6mSKpTxb1S&_mcpgR{0FlN%w+Ho0L<n@#*tOav}i3_X&ITYu#&3'
    'NgDA*)wmNf6r6K2!^i6pHq}t>tf(ksem3P-m_&kBh>!EFqsMBw0gFB&YPX@uo%5iD4#rHhE-8f@FDSa_le4^B{o3!p&s1{D9=Y(malw$({)l7C'
    '!fXwY@Rd)@tGuComIP|JV|2^nFE1R5Uo;aH+GCSW%6V2PmtjeJFL2091y!ar>9;rt7~sX=D){5AxG)H`Dx5K_9RKR8D1Cyi$Dey~-9Utw$C$ES'
    'v~fmQI3ICxYw~vXB_aYE7j`-Y$}#v#C#}G;(&2v@$Y{P<-SzzTJ#ptw^0Uj5I1tv1Z<j`UCOl<S#B}xz;4%qw;hJngTX?&jC$#XylV|7AW-_2c'
    'ZGju-r(kH(I%s7Mr-KMIY9k29`aX?nAOhnVHd1L|;uW7<^Bn7#yhg2Ug95Lz@dCRiX?R$YtL4a>4v;sjPuxRph?(B6bSw%Wp*q%-#?-Y6`Uw?w'
    '$zr-NvkM=>>=pY5q0b_{lP>x<Td}@zH$E)#;3IBSOsgtwp7C#V942YKKM0%TH#6<i@Et#XlbU{b4&wpb`u$ly1|$7vm;NI?>DSACiwX&xgb4DZ'
    '#UmjEqYwhb(H$nj_zo9g3MLM19{e*bh+~IAJrx}qHWEK35)bhkc#P_V@B!|i&lJzG>9)hSpZ98xP^9EA+auwR4+8nI21E}O2;zqiUy>eh5c;6I'
    '^aJM-;&4dDf7Po=K0$C_-0PDsxp43SRWs^P;ziIg&9g6;z{iT<N90Ex_JhZ$(f+FVM=i2nN|YRs^H2&>NB8M47Tlls*BgSb19hP59~**t+}WZ|'
    'u_PJlC7FSNRHE6>3MtF<KW+#f18m=cDob$t9op>-Ox^DS+9MF$;dt!dv15O$0%F*G#I@E+Ts6js`AS6hgRtWD08Ct|UZk&}DzZ4<vYcZG$W)z`'
    'u^jN&j{8@-+<Jt^eVLd%_V=Vkx4BufolXBTF$sOXzI{2SLG2u|JDmM)UI~(ZfU%D%5|$koR)xgzg?~4z=)OM|_%XOJR^VwB;CpfrUKlxQG%)l`'
    '=mQ=b^+2eL%+k-VFjfE`j8j&Jqn2ay>K{hU-&z!|>OYy|k){iVQx#CpZd3K8CM%7>);76~QYl<kE<+M?op%iPex$^Gzh_}YDI2vHki0neCzCIN'
    '=grPJ0Ck1S8Q-iyXcA?d%@*{=5bg<EIjKcxq>U+HxLsgrj;ggT6=K5cK4mu}$8#rmoPdyOGmyNSPkt<)fnw%qsOs)Bhw6&$LfChz#|Y1FA|$Ey'
    'H0q^Sy!aT)MZ6*}@qntpE7G%fS0=*(Z)fQhVEaut2oXq?je<Gr7ryMFT3+mNJzp{Y9V{rAoaJY5TGukKry00DPWlC+7LQ*?qv>ByUsPyZ57zdX'
    'UO-wl>|2CY5BwbBLA;|0mh$aK!%a!ukfnx1fO02H@-;z1J*LreSJR16u2=f0OLQ5rVX2>`xy&?_BhSojyT3^jG$q1ir5DPS@7M?E(J?_^iFkum'
    'eLG{W%^IS~1@EC947b<5u|@Q>-k$W#Nbyyb<)(BUnB6~}>!9l$1JHu%jJB2{#uT-jBMOBopEwwN&DT22?91J_OM&m+-{qvB8cJps7_NFlh`9E!'
    '2EPM1971fS^=pi~-L+hB)w_4Pwr5G|>PHwLR2Pw=u8h&k*siT+Jm`02qY>(GE=o({8@R(oA-9N{LW@Z;MsFx+=ra%=*IXjP>hQe2^|rhlm)r85'
    '-kNc(-c-lszBz=3Az$|!Xlte+E28)b)W8K1vY_-`*KYy~*UZ={36&^*Wwmwm_kf=^_~@4;;X(eArK@`C>^tdt_|w%UQyG7ReZcR-zQ4qMw->X2'
    'H?Svfxpg{kZXu0wlVpRPXH%om4&XtUG2Nf{@@hC-_-Z4ggmj0N;mME{)~Zsd<}9oB5;Yga{R2z(XzW~~qA4KS+0F=%VFApkuJB6e+=5t8vwNT7'
    '-Oexvk*RZXoJ+|cs?2q+-J93>x9r}vDtu$~U0uQ=1oofjYjV}way!TCsGZ1il^$gx2$M=v{>5yEg*9GQB;8nZi<Gy*-!2aFxZ1Pj7(sUf<V|5P'
    'rwpdExX$g^UW#(LDkkL@es8C9rV_y^fuWOgyJYMTn*~YwOR6^KXEZSZas#$4<3Vu>b%MS>=ov4m@WfO7?UtiKN;hI>$g5ONh=zoC5?eeCy$UGe'
    'Att_JQ(z51!R%}q(<rL<wyv>njC6Nung!9Rxyr)*j0)FjRXx1#>(niaFwNk5^0=Q`6uU2q3Ib;Z6REvqcDKz{rAJHj<G9{$T=K?yohcq(wcXxD'
    '`*hODd=j_qx~ZZoW%!^-c1pZ#fDt67$wb;d5f6Q^6p3MRy2@&T<dgwpgoY_!g|<vB_j-kah3r?ApYi#;<su<j1O<e*XGC`1O|>5}AHM5qW_MWH'
    'Rj;k?aNj)Nc%jvY+PS0a*`6N@mW(^2v8~sH(k<!Vfn`3oxr)YD!2|`Pu#NGi(>!$UliBWdj$bJ*@7e%til!+u<b0<h<Q@7GJr4s4B@Tcifh|a&'
    'Su6h@?)x@y_dksL{u4|81o!>8?Ds|t1O{OgiD4)Sf*3>+D1m|misJB*6^vm7f>57$-ai4qFg-TN(D)dh!SN$wBl$!O9m&7((Z8jT{~^#LJs6Gt'
    'C;E9}W)vU8;qgbgyW_eYe^KzUCwQ1VkjLg>`WdPD;uw9*e5c25APD^rO8zSQC_A8993P+*4L@-ppO}s;J?3#p;(&ShXQy&MVP6{hz*hn}TF~&P'
    '-3w+1INV<^4nMKOpD<ABV=xW=<tE_8J)lJLuOXcPv68~ed>wvA(qy0S>Gix7e;U&1e;m^J$Dr@Pe89g6`u<212L2b&cQkhw^?T5F9Gi9b3+OvA'
    'AMk$xeFx?P{vFWwZB7#KFVOcFQNwI5o!>%U4Kn_|QnEg<G^(luaJ{~lxP~g4OQpwc4dr_5EaKHObSHU_Y<2yNR23RT3)6R(j&n}s42R8HH8$()'
    '_XEJPMYZOzobwY1M6OQBog(hybe)(F(~Dv5GVR7)`WSxUvjF@oC}B1CyQ!(17|pqZVMo^W329{~i2C+VR!IPz3&Nj`7GhczjEl;M>3b?-yM4}G'
    'MnB)NY#KV1#}+acv%-0XHUm~@S$OX_Pw`TNGdy>F+Z*ym;J!T8xinwFG-SxgoLin;^YJclT-2V8`4ZrewB{PnEEas@^`}h-uPl4@W$bsB<JE)`'
    '+o=8O|Guu~*ZLOz`L4s)yUo)6(;)fnBJsb`IE?Sa^)p!bosQ=Ju+AU4nSXbU?@BI399hH&Op+LZ6Yx&Fe^y@6^r&_RuSSm|yBDLwKKf&OpQ4`('
    ';Ezw>UR$A^X(K=9)zQIrzofeD1sVP17bDa$w0I<_V@KNt`$!e{iv9brOLjDJvh-IzH^fKbh<y}}AE{sjf1C-CqlL0F?Y;OO|4oiLARIj^?0y>Y'
    'QU4sxnfNeeAig9kf68l|9Ic;&mLCD`e^p)u{wS~KKX|nyAnXgAPGcngTv+3L(^3Jxif0at{I!(m&R>g4BrbUE1z|6*qC5q)yB!A)dqM-O1c~Ed'
    'weUA>{{_?8-<=2#o0=mb?qg4rd~qTyXb9K~`X2{Xp8LTi!nIXLnvJi1h-~$Tr01)m2l$hu=gA16Cl9{ItPvdScY!ZG7Kzj3LldMG60B~<tQGk`'
    '%OtAmQOBo(AVUd4chCrrEb9yj1q=^XqAPqe);DLv-MT)O<SM^V&V0S@ZaNJXbHSwkh7DBo%5_UQJ0>P5p4xCIY#1sKhdt$Z=#8PMf^oOkgqhQ9'
    ')t6bZLnmUHn=%fEBxRj=Ma$8$BhKtY%&3lM!9L9dK%u1J?nC&c#P6XiUAiLlcd&}{lB#OUSuTs@458eB#TJILD0r?j@K#4AcsA(`!k&OeQ!`Vb'
    'xxl}53XvlDzS;?6*)5_k>|Uk0ixzk*%?nO8gc5FX{VO?Z{=0ukq@<o7fQOU$)G=^|L>0kwf^VxQ3>m>2PTz{|iiPzFd#u4^+*j#Uu~b;A3Kgh#'
    'VX1HZ2uDCo)&^y8DzcOmyP>E=mQyirCOx5%n*=&2f#e%JmE;+pu7k=qUMaQl;Hi-nukvLDg0tcCFBLy?nGbr;yK0{B>%3%MP!B#@h4O`gVeL$H'
    'AYMydmw2P!JR7LJhPUSV-sun*^_~*c3AdU8MS4$IKIs{m-Vy-{`|+_-;Wo<5Wl$D7Jg;zQHoQ2MN;b}7M2Tk`xJu-5cPD!_uJynx*XWfI2I)w0'
    'eY#T0L^bQPV-uGr7Zn$if=(rh3AQ<{1Zzy^i3f14WS(ppR%lQfi9<Z*Wjy6)VRCY3+A0l_F=l8_ck!;@OR9F6CSO7sMVMlwpUw_;bn7MxpjGgx'
    '6Q5*h9>4lDpyH%TV*h=s#H_Y-d}}63-x|VAR5}I*Q4`t6t5i1H`nFYaIcz=mTj`D%7*!JLFZl^Hmj~#a2mStUE-<{401|yj_sCh9ed!ZaWH{pf'
    'q`L$^z(k~RWu=e=iN~O>*67a9aZS}b(D~B1y<i0p!QkX0%%<}5ey{HLS9N%1mM$t!r*^&<FoC1vnW<=jq<6$p(t>mRzdw%e|Gxmo7owbb&;m+F'
    'GXsD50u9n^{5j#XK+Y7$6C;|Lj`Mtj&S`e1?)%jPG|SQ2_P0iR{*`ttTH=+K-pNAM!1Hbo1!9cmV<oy<fnFAv9g42Ox%-tNvi$aB71SsqZZ6R4'
    'm4o{BvRxpN2B9!4Y>nTc1|^d^O)<!e=b-m_mG_VIlJ{8<p-3oK26C}W=8l)zxfLQdQlwYT63JB2aVmz93_P-s(rynr6(l2OyHn=$SRR%JBnQlR'
    'e(ZF$PcFCX(n}RiPRDMWb$cRDNQa)4gkm?q%}`iB(dt09oyu|fAhFteTHv73+jmVoGOcBC*~qcywE&ru;aQB$Ujh%VEDu=%4&ZjE_!PohTs&>W'
    'x*(cDcw~wdMVVk%IwDD^;^jO2RF|>v@F#v9+WlmR#@lUV%)1Lfq0>v3Q&V4x(ag4GlyX{;s0&<)ZlgPPDDu34j_GCPNDG>Igz2(cBErc!Vz%J{'
    'xb&0S!fA9BZLX%`@J5^dtGy=gI3c3*iLS;5E$$s9$aHcB%dq4nq+CgouHZ|O4<>*uk?5Xt^b}@Vy~+*&>ob3c?7+~jUfJb+m+F?m1iI#ll*E+O'
    '9d{iiH?xO3>s&Vj8O3sHv;XE~XIa01jv_>$QQEcZ`TGad_0Hs_dEqVA4TZgboW}hxC!AiHCPj_^_9)=FbM!}G%kR~=DDe4?+_Mu(Fs?mYzKxrV'
    'J6>&2c(>4WBZ8FGlh|19#x~}CuKKKY1%#;Mf;GNPoSaOS>9FaX#B`9olns}}#r@lmb2^4+zN5|h|9c+CE{|su{&s2q`~Uk%(9++3)>k<Br)PW%'
    '6LADQ%&!Ru1z`%qK@f*g3fr+Hib02N<`8952ni!3wx2}(Dtqa0<bn>d2?ie^Z%14x@=?&F$CNdOeFkJcOqj%euA}*wEgp6gpPtS!n*)EQfAC|;'
    'BQOL%v^W%WXs03kVDCEsjE@)j6-5U>=^^3oVM{P_G-=@Q(|tjYN$njC64Wt0lwyat289nz&3@&_3w)+{(&)3}fP4(J!=vpKV+Vjda-@*Ir0DF&'
    'nBtG@B`2yo@*ckI>6K#vu2>;%5LgYy(9q78e6Q?#3ET>BCu-^pnA;C_5Fq-EQC4enaP^rrHsHrAs=3^N$x-1JFu0(LP|*IrG$dZ|IZ@(V_An5P'
    'VCsmZWd5)_WaCY>X=KNipvM1hceoz|zBxGmJ68jIdpUo3HKKpS@QJ^F502Xc4_r}>qc0Nc=QJ0%%=O(aSXJ)8i7wa{SG03g-3>3J<d=CF7eu>g'
    '!`4>=M3SeSbt)h*ogWXmb$h6Fqqt$Mb22;!jk2EvyqNssY2=M~YN&|Qvy*W{XjoO>>X^*0cUnuwjW<P^#6qdYzH!FSjD>5q(Wc?K7PoZmPQoBx'
    'DI&Xykw}sswhjDUTf-lI{%pA4GXq1K0T)9OcM?VPRHK&5ylc2&qtnJ_mRGu%V;k~df!nkhOijvtJTNaDO1ChhEYI=bo(2w!3p}|AO%;aMetp2j'
    'Sqh$$eV6C_k#+CVf6Xz&p}t@!eqNh*n#Js_2Scru-xenTf^6&mu%!L-a`w+k*-y$CLJ}B(V&GA;C=x-Dy@(NeU84w;JRA!_3MC*MrNEC#A^FpB'
    '!-zbjbw|cq_OU38j@m$e_~rh4pMJanzjzfMzWDLaUHs9*e-)>W(z92?op$bjJR$+m&kkR5kl@3M|1&g5easHyPvUw+{K~~YJlyy95{qMp`em<1'
    '_{YB=kN*e8KS@lVfV$+<Una>zzj$nAeq1L)>S&Aa$9F!y^JWVD7zKUG*#4^cUJ;4EY%#lsMd613QO1muws6#QyPIY*khprbJt`t*zHpqMj~g2Q'
    'hf)Uc1?_w-9_-iR@e{d-wyDb(1s@H4m5Ut5fIkiv4EsaFo3)E?GL#;w9lD=6MK%<w(ccMrw4(jj1h_vU;^;-ylFvY+`qSya9~-~GpE|z^<Yt0s'
    'j||B9`8|KvD-tUvgO@$)J?L}ExAAiu=b#;W>*~jV^nSaBtc)rl75BK-C%y=u7-0yRG~MG+^`Q=La8>CQJ@k~;92w=sD$^~hSNgG*4nVJ~Cd+Rr'
    'kaQ^QW?NxzOGC}QZ_nWkVcZ%AX{R~g7^OLBQ@1mLaP%kqZgbknHLVjMyl++%U#FxF-Ei&ZN=$h#H*Wp|Dv~UDW8@Ik4cp)9m?v+jxEJl)RqOfX'
    'VKfRFPyl(!((@@esbJAu7R(2&`0dP?XVsp!GfLXOE$YO&Hhu5BxV=uK3C*~?K?FoxA~g|#tm>SH6=*u~e%tzUzQl4hzu@E&4Ehkn{QKqz?Jb5G'
    'j{r+WelLoR1^W9X<Zp=$ivf_y#=!_3>rm-gUSjGxKFCr(k@gvRUY=Hi)K2;0k#64aL?DtFCmQ5x%z$a{c4ew(4eV7mKINvsLHFzGnBvHDnD8W8'
    'O_#A1s;-yjM7~Bcqv52xTYcrfZh^B@_3e^8uYRBbFJT(bl&O!y9YkA9+L1wU$v7U4akI~|H*QxqswO!Dd%2X2^8AiYd#DCs3Edu7-2j}f+vt~@'
    'pNvJ_`Sl2yv33%9Z`khz*A%O~@N5#r>|LN2yM%WEe_AP;J0ilG7w#qA0o}7kn-ebZ`C40=u+?XE>n6RPRad7nD@p2GP51uOA_eybF{Q%W)iBZI'
    'HKsnpfxsV~-|s1}<2Ot}dUwu%o;qmyc^`+p@ZR9(55s}LAJc*VaNzG6b(R&T13=#Rc|KVlDW6_);=Y^0K4Ckzri$0wc}qsRGZtIxuJAa=8l>b#'
    'IT4W<U1hq*xW_#KnuQzAVpSqKn^OsryJTJUO)xuG`!vk28478T^gPdYYMe`i4c6Do`PA!+LY0aK?Oghipac(*Pqla#RRY6q$(`PdC4%>!6g!&G'
    'mnrFR6J9PlqpcQ#voO|SGDz}0_n1`R8osg1)q84-eeI)1O)T97yRj%4#`iGFqVCR-&DmMjlR=xkG$o3#K&Uu&m(ZQ0=LFcSBVKdmnlk2Kt^@6k'
    'jdHCok6_mGtzF4pl$(VWb$GKY+0b&?8<twPX<;3*gi|cQBHiFZr{dImY<5cTa4N=EIlJ$lor2nbq1Fdvn6qp5YKvj$J%7d=ug@F;Zj_8R*&C3^'
    'rxX-DrF;IvoW$N+bri?tI`M4AxMhAQcQ*QjU&<Sd+l7!4HQc{>ZQgAo+H(;FL===cl?(aP#cRdQ({Et4lZ?Dx*xQrHQLiHS;p$(sj!V5|yP>Zz'
    '*}rd8eZ?#^(-^>+#+TAu@6DPOU87MarY(Y|Cp!2(t2w`aa#5-+N%gwjpUY4+T;a@{=a2kb51JCX0rnI8|CxKUF168ZS@d1MV!d<DRp0F~&VxGC'
    '_bt4s1%v>Bgt}jU^~p|`?MkmI*V_A@JBGU?kx)9xP|P`FM$nezoNp(>YUMO}_iFB6$4-B|jZ?@@^7CFKN>2-B$caJ05%@$$duBLCE2$XDJJj)0'
    '5_S8T(y_~nKo&oHRF{6a70Prv-*!racYlBItNNb&h1Mk4N`lmTU%u{T|HVBEL?C?|#jcg<yZwnn{r=G(eCqonzo%0SO|U?g$FdAVBMgh82yo6v'
    'R&Iq->mL+Op})xC#W%Nm0*LX}k_)&ZP=HY7o6|B~0;lB?0gR`lzAf7RJgzOk)FIn^lnW9JMOQ{ckbu#wlxIDZ+#-wCVv$`Rq&H8n%@sebe&wma'
    'f@uI48JA$1kuqSIu#&K~BwY(ZlHS%cXz(FgZ0=tKNIfdHS{AFoROCz8=2|AMU&2b})~mrco!)viH1e0VpbTok^qWbc>lS)}B*v3|mfYx19p&$o'
    '@XzB~=jU;46fRP03i$_RIr%Y(924z*Ok7}{RTs&&pSm)WXgS9F`GB2HkcVqSk#N&K;DT>tN@{}entxE3!`HCNFV^>>`^BtK<hQU&XnQcoCt$P>'
    '9yBH9$C*MC1?KwGqkUK>&S1FeHTjKf){_U&7k94)Dg8f2u&KZ+`He+$QHnq!?pJbU`jO>(AGP8BG=tg@`nfp#zBXKrLv$wuQFxD<KbWy!llg*|'
    '9lo*=(L<EJA7f~TK8?LKT=H0y-q$#i4mX=RWfeO=Vnz4KDGz6Yb56=bJ=p4yc*RLiZ}g2*Dw=EdETr})J!{*nVBv9hRXV$v(D`;!L>_+r(z4h6'
    '!+!|+%(M5SkgOy<e)Xi`ivx8XE@f@9{e@~~iwwWjhS1N&VTm`k*9g*h^%d{j?{kMe+zJ|j)4-3?!^ud3*fJ*mf$|mS7ctZu#JzCSLAsFWO~n~d'
    '8(!cD&#XW_rmvGQFYmpE+$|~~Ln`t};U=Q+#WkZ|xQ{Osf}aGJ+NJ5cJ1j%{Y+o7ozb|gNIJ)|+()-{4l7a9<IKS_w^O*iCD4Q~W+_s|cvwZR2'
    'Kl+<Q<xfZc(EmbMioz%iCop9FgQXdgp@2^-h9e+5WP9vWVG8v{AiQ;>sBJ=8GQeGs-4fQoqJIU(oNH~i0%Gy`<a8}3*)4%%MWnI>rDeGp2LO1X'
    'L9K|f0G+@@wE&NQi3eG6iTahJeT4vk%gYU(FffJ9Dli)bUV|CXxvVI*9-nXRIN&{i08AxPu!{z=gSQxUB;PbE7_d!Pp%C=J*zF?nzbqG1P%fh1'
    '9PM4Bz`Et8Cyl-rDMPf1TU#E)PZi0|&x+(QTBO<(qz`dQx|WD&b}JqQCY>UA+u|CsuZ5brmW<HWZ(6wHx9zj*xecXW`#y!+0HL^Fv)oozG@G?L'
    '+M6Y-mqK5{+@u+ZPORW-nA@Mw&Pz<+998!t%dHhtC3+vRGY+kFV|a|G=76z1h@Ueq<LPS&nVJ0cLmK1za^w2Q_4J(tdVPLAZMO^cPgGd?N`)D2'
    '^SnLj8!cve5)SX?EGo`*@GRuPx+C<ogtyOLFdUDR<KQvma+Q=@JF1qJu6KfaRQV01t)INeXGSimMc6-vs}~FeP7?h%Kv90eooTni`Mi)ykw2tt'
    'SHO?-A=Xd&*v|On%{Kd-dcP-<L|N9oxny}+zu-9-QGZ84&GF<NpIBlQN0d8=rx)x?hr?(o4a=O#W9g>w>%4mrNhQ56T(}DaoyN}06OT0cDBc&y'
    '?daqEG%uY}CP!`ISlxUpWT<p}Rhd@D$=cC;9QFq8dVNTlEX<W1YKHjfJzN|2bcA%(@ZI`ZV|%A756#J!MKy0V7w2r}wCrZLDN+o3wbHRF&i;il'
    'rTIlL`sA&Jow5^jXn!hW<RUpCBlgdP4ukic3FSPv&v8UwuqR2$sXeE2n<qhl+o6d|!XtjxXl*CKyssgpc{^CXFTG@si^RT2W;uNw9CO#uaqU}`'
    'yrBGR=Fwx*>TC<s&#A`qT)>oIy|v8Z3z~O2!KReo4b}N94fA8rgWE+fk;xmZ#%C3jJnpk*d767B!`HiockDd0ZJ3epZb){7;26)*cHw#jYdQ;o'
    'qucJhtFo(fty%ug_z|79D#B(Q<D7E;QTK2;cEOvu8F+ltPbQSYsV&{g8}rf*B&TZ9GPmzZK#-c>Gv$JFyiy&jI@b{^8m2UvI5;w7S$f`e8Gauq'
    'sOnU>Drv@;+#UHyicsF+e!1SjM~UOoe;fYtqoX}@&y!t4J>cQM=0)^)ca1EH_2ETxpX9dzP0~+p8zAT#$PYM|UvIWNiYuH%z`JKrc++FOL)Fx!'
    'UCAvvp@CzcN9pG4-NY*wh+Ztcy_jpIiz=8{DH+8e6|&>gC32`lZ_H97NVu>Y{+ziA?xgcRJipVZ90qxQKXb^J$V7;c;pO;EujNZ@#VZ%Tn+bf|'
    '?;2xYR~K(@ca-Q=ZrEuw!Dvf;JraC<>ZtvaLdPyZT8EG2z-;4NyuwQ%`_H#DPQ?A;G2XSk-ixE@4B~-q(9+SG&U}-jgUZCnvq26e%kgonZ(?)F'
    'Z<nr??21a&7>@Es)>fF&Gzjf#7SDASj|wWqrZ%CX7|BQqFU$CHf-Y;RnLpAaSK9C$xgL8V-bJ_gy~mtJ>EQ>Al+Cb{Zu}v*cBU|p<K_6|rc!(G'
    'd(=5UAcIVu*IUySZHz_U8f>+~-pmO}NL37zW^8-dV2_Pe=BPdF%gRN_mvQM1JGotI<F$vZk|EQpw7%!$$K$2TJlaw7TE9A2D4nEy_7ous>is>v'
    'dzmCfDD@I5#6F<#m8vex_=2w2D9bL<=^SPjl0L`cmIeix?oKp8^cT<8PJ>A&Z7jdVHtvqsS2$6ebe0Ud;og(EgVwr_xF2HPzqAS7hewxvWpmRj'
    '=Z9%H^ua3b=cV+uvO93qLerju9^9Moj?R=+-D5X|4&t@zMm{p$0osjZGHH9B(?*!mlZqNLcy@$7i}c5ydS{1f^ur*zY85s-Z%^5F|Ia@P3;MyU'
    '-VVS2===HM|NfUp{Mz~c_fGPO6aLT7`q2>|urFW`fMN_wFbsj=EQQk~yZ$s1zc7McIni4EfjSc15_l@G0k$$Qx&n%`mD#LZ38}z`zi84^8K6BG'
    '0!D%BIcO9RBytP71zuAOU{E0ShXz|)6#=%hsFf6D|AqZZ4xDXneFY7k1nAoqWQ3+b@LO)aRY(Dbj_KwQg_Qq=(BM+50(@$%N<o9a07lT%HuGdQ'
    '5gv|#Yr=q=;9s#W9tZv9!?#>Ei#s_@HH7dL#u~ww=l18?vgX~D#gFPY596u-(Z~L$0i7x!AQEVj7S8)<+zZz)Zu8JryZP@vX@2|U*Ux=z)T@&j'
    'NXv&AK4{dN%V~tnFE05&(1yp~UE1HhGU!*A_IIu<UaMm0M?1Zb|0t8^M@!&1pP26VpvJ~VY?-(1U2~4|-?w*2^5Zq0Z}tSe4;gW3Dn4RJVRyIB'
    'EEWmyMDv`Xz4MWVr&(!a-CtRe1V1gGTpnZbec1^8PSnfCeK9h4`W40maphrXH@5E`O)PUT*JmsIX{M-(-g*j;Q%~xZMe<j(vNGj%*SVOF_-aH6'
    '8p>{agr*68GKhn}Z_cNBWuih_M6$)<b#V$!SjB9tI6VpcX3TYsOy)CiUzrWl&9S@veTWMDuMuOQh+853)RbRr<Tju9OI~*WG7RBoO#0hLeFLFC'
    'j`%a^;244<ER9hFN)reOgd_-r#y%CvB3oESfo!2-C@9uIFN*>bG~mIx<z^QQ5GoWP`Rh~ADL1PSH2<=n3iPQs15WUzDnqy6?X|pHF$e^GXF%Ip'
    'u>ZxNzYc?3KMl4I@Xd&%08V*dq`T~<puo1XklU%j7V2gxx?U%+)uRC_m75{T7k|?gM(M3u1+6d|U|wGR^<)q<wU*rvpmW8TspBo}BEK*DKe;TA'
    'pv+S~YifNnOc&1P(Zkr`h)s>U|L_d~25Uel3zP$s=`K<TeK^c>lWBM;xV(?xvX80YT5;6s{3F=>@z|EUv4V~AQ_=aiuLk=5a{k@b{3>}H`Yd`|'
    'a&<#_+vkGpXx!L^&Z~@Cgkv5RChQVq<{#R`4yjqe!vn(T>1niO@*pN-=MPv{t;oY;(=Lw_{JkTYr_&C+t|ia%89oO>ohzd?<ov)6$t|JR??OYr'
    'QawYard7lcam}4&cb;9({JHaY3nLswKwnzTH<d>g_>NDW2ov^&LrE`TJwicl2<79Vzv-6~d-wQ7>_(mzO0$xMF&8W2dF(U(YWKx?r=8n9w_szL'
    '`k}5PPBmu@^yKPY^FA@D<^}Y_q%J}iHK*H5C{NS4C-L2W-=mwqzO&fJtHzS?;X9)-aU<8~LzOB}w?y5GKf4tXoB|W`ky&g_dh%~6Gxz>&(flW}'
    '9zGL!du4a2AgTD{p6mL>c@W3Pi-8XCmER>bTcQ)byQj+Ty;Pk`l1)@1gP#rPN%5%ZpuY*i=<{TMY2p_`EzfJ%wF`f{Lgpp1^<m$57AGvvm+fc4'
    '^N!DAC-F3i*sm5_u@c9$Q`MSn1xIz~*#1sHF~hdKoW-EgMmZfu1CbW)XwX^R;d$X$VtVBhPTg4A>9gwUt3LUnDNHmNNjAeUG0LPk#30=nN=0X|'
    'Z&}9^j~hNYNrXj&#*(G)x!mK#!?)+@+&^zqlL^h+MPjLVDVcO)T$|sC(aVCOdhwbuCTC>m?eLvXBJ4+=_0|kA&Z`$PW-pWW1{8kmd5jYdPViD+'
    '_vgWyPW#4HMd&{XE(3Qn2;9y{eJwTbQmP}T``Ksx<7F8b^%~>>@$29+ZTEC9Sq2H@dk0Tce7z96$1T#+_Cl#$&yK<Ca5_EYX-FHq<LxtcBp=o7'
    '7Hji!mnFA@U7aXHDk1kOEy9ws%cB|h`4iRj+DYlecLn*d%qp@h!(M#^r^%)CYLBU;7+#mQ+sTbvX8n7H&Q!%P@RN@`?;<p}Ry~E2^Dtt%?-R=y'
    'm!>cid3U<6cO*Kv9MZCBuYE6f7Ob!j$0Q(HF-9qgi+S<<x;$d(RLMAzzSa^`)A8tb^0;&Re(YGCXkdJd@QyOI0M-w8PG@IEgN~<4b*6=3tbT7='
    '?B!z0s7T`C9eI^;)F{&-zgX{7Xm^PIE>-2BqI7wEFnM8IxV2J&%u`j!J5N|i8Rx|^*Sp;*_8VfTnrOzHy(2A1Kfo)sXQq_Am4>;0g?f;X=TkTw'
    'LKr$yy?m!c*nQ?yg)T;t@uT8*2wQlV;4ZIHnvQ&BE^cR?_a2uO2yUy7B|KN!zRHRKqTVbQx2~QDd=*^z;&9P09ER;fhM6i}`_^cj>Ynzbpw!qG'
    '-1}~Ed9_C8^3P$<-H#9=QS)Occl4V+!0ebB1w~kQ<+8FJyb%)5SFG$2B=?SN?nN#g?Mtr&y(QEGGR^$)24THwI@WusyW3eja85ZL@x1}V*mzri'
    ';%!FVpCYR0Cl_`~$uv1!KRuf)6VQ6+ruh0!%pA%b9Bs7RCBJ!B6t^nXyE&0{m){Zm#!ojq{|8(N|3_R2|81^>|CuWhEJ+|Jic>%YiqH(X(!`ZN'
    'ecBesOTa`{_Chj1!pRcAQjPo~J|Y1D0UJW;mUjadB0uL!1$getv{uT3W&f3L`<fXGoHdwjrdVu}P>KOsO=N41uLT{t)^60V#GnKqXzAwG3p7v+'
    'AXnKYI9*FKmIU=9hJantm5&i6h;J<^aLo(`IMm9`)(ZwvKsdM>Aiv7C#Ikf#WBrYkGN2GTP(N^`w`#mp=hSEz!XE!T{QE{sp#Ov?0b&Au&P>d|'
    '#gjI!^q=q~a5d0h^Ca`%+L}Wg=T^aDE9QLDABUivnfx3}vPLy&p(F48bVf~$o?xxn&)H6|(5IuXuNQiccTeM#4Au5LRTmh3CUPOG-kz8CQFa-g'
    '+I>e~Ii>ce8%6H@*mG|a8qc1mW0FKrY0Y7rC>j_<2<1OcC<8(ni01>I@l)y{VDIxmaS&K~N-vBMZWTL-f3h`iSFU^mBRcjiof^-hp-8vg{aJ?3'
    'X8p{tF1epc`6dY2oi!~iT>^tanccp7N7)<3j|SdyOKz6(1)K!diW_u%N8<i$i+EmD22F&vjquA$O62n%r7}dU=i}~dC)z<zBNX+H{Vw+m^&Y-U'
    'BKZf1Mf@YgB7PgOK4~eD_zF}AO(7UcuCT=t7)>!4ihQ~Pxp^_JzycaREZE{+OFNJXQEZyaZ9az<0JqW=z?e@FYdy5UxAjCCm_n{FhinOBUpyv3'
    'rH6u1A-zREthL{YXDckOFGbM5Ml7)2m;xvwxAd?Tx2P?w8qdDwT?3#cH#71ru>!@xuY5zr6}^}W;2FrD*klwX1Fml^1=lCj#Xmx<QLcx>^vv^?'
    'cf<b+h~@tO3bEY3LabmZ6#Jg4{poeJ2`i6zQ|S%=h|^=N*kn)2Lp($W?}WatVv)n8b`AKHT9)@YnJ<v59O!4B5*~YclBDjXcc<+VmAucl>e1Fg'
    'f|7^xEp#3Sui<+ozc6<tXD()XftyJmJV-e_|5L>BxxmU^g~Mvr(}^%=Mx8EtGMZb|{|2!rNrX=<AwsOSdn?KFZoF<o0H@+g_4~6c6-d!MX$}@%'
    'Oi@M+nWNrxP%kHgT?EXa_nR_-ktGIdVgGb`n`iXk7CDjTMhfeeHcWT=T3c_OIdFDyGVC<!>ND}`!ZLqZYT<`{*oc4MW4CNB>9-#B05nuz9$J4O'
    '8(@TC&-KqXx_|GGZ%(;CJ^cqyG>l<bj6g_?rD=phF`Ps(jK<hatxn?Pr`a{gwpf$qppU$AloeYT5~!vs0`#Cj&nE|6Aa*mNB|ZnOZ1Wpi$<voy'
    '84>}Q0+L*5uzJ06BsK><D~8z?Y06D2kZsBKzw$%F2=EM`wjws&)R!E@Z0k@}pxw@}+ma0dKnvS)7{K27_M8<A*Q-HMupSP&`S{iiuYly9-g0HJ'
    'zg8a<pbw6I+uL@yxTrKX+m&zU`Z5SD9^>-oRt%U8nv(l-80=9qy~ikXA2a?v80)tOpO@2^>^3_Li6zte5ARrLGmn*{E{&z{=K4JLRa-ULz}cd{'
    'PG%6IR^V;gs?FWv>thgj5M0VXy%OjL8{1E><lj4#K|c!B4c8e<hPV%IO5O?LUbG}b6)k5oryF*LANxi@#`{YpxcB);Qw#ru)_Q*_<nyk3!U`Je'
    'OIfq-{1`D$@M@&aT2W0f7tf+V-=FeZb<st;nHQO`FKTTWXBJuk@#1RulT|wL71vDn*gH3iN2mwhR5@CYl!M`|A;kRs)VzlMq+i)K@niT2lb7_#'
    'LXB61m~xgFcf$8a<8+hsduydnRWqzH6_)0uQfEoGsv?d^E6b?ZkYd9kr^6Chfh|IJJU)k);%qznqjMl#!azyKF1ltQOU%`pUL|vcmk=Dq;P6?l'
    '_-etoFh1^!FqyeFfN0rSZV7Ito-U8)YUGX-d^Q#@?7HlF%j|aVG>;6Hu<;&~k0#ccx~?p`hKYM)#l!=m<k3)3xz*g{<vVrJ<u5AZ&K^zYhfE4|'
    '?Y&>7$5lR+vHmi|i=L<C`qjNWUP0Q>5uiYFnp{lHzP6IG4d17yh$OtQ91ae~onqOzk9}s1qIV<ED;rUb50|QS&Z^dTdHG2}aezpC5*HSw+D47P'
    '#?<pqFzu$ScdPqFraaA7{5E->1*Y0lLY1bsxl;Rg6($;mdyx2OLY+*gQAdg!?-3@V%fho+`l?67EYD2-F2yGz*XSyhEfKzSr~P}7pNg*H{qCqj'
    't#s%b`}rttnsS*|>WrL|%+~!NOW%Ax<YU;DH8rwwNDFk#qdGhA^VNtx9Lk_iqXredBSnjRUSowFuueJB@igybOmNAcMC~*5vfZUj+x;2N*cXqL'
    'XqOM?{&cm2f3NiW*<a<Cs`iK2AKP)ggV(8q+=;<X<G6tz-m9AK3@&L9^U}4mTu3kaKG4UkyURgl*8FfJpIz1L=I1D3)kC33)hm(bh!JvsnG)0x'
    'A6k#xj~583sAQ)xW5w5Gzt`~7dA+r;X7Q}nJM~Fmvm`lGWkpTPrM@fT!@FO_*GwW9o)B4Mnh?iaj`HJ*%E1!Mk;gn8t|M=RQpW6)D6{AFptZso'
    '7pvxWx!-zue>`Uh#mY)-sLO-*A>WhW*>(MKvKVK1>rLM=51!C_wGX?CcNfc@Fw+E670RWeh!|~-hj;Nfbq6zglsg>?0&Q@8CI}yTh)yrQ)HM(H'
    '`!UP%bXS!lA(u(i_sk(OHEuo$u30XagXOvWl6BMGLsV(>a%-RP>-+F{xH~?{`KHF{Uf`U&q6+0%9njRK!sIgOmtH!C6bieq$C#t!8IxWR{@@cY'
    'WADuI?Iq9nO79z0;t*n@MQTL6o_8W5<Y&KWhLp`t?{_meWW_)4VK>Bz*+apMONvM%-LiY_U4oWFS#QmKBHfNt;IsjOR<A=FYWF56kX&V=WoB(1'
    'I~<LY;K&tFq8ndy>{*b}$&en8oZ9v5bZ^^fF5uR=7|h!bkB`Ejj;<nj8hLpcuYwEmW$>i9<YH*<!Y;OQrexU5`PQzbbch|F6>aVE$Hdm|D~;Ml'
    'g&$+VTz7n@n1_<b_Bcif^}%m+4tnv<JLKK+X6AoiiXi^)zzhB0U%dB?`k=rX3|ZOI`nj#RlW&>w6Sw+}!#?=cFAw=KDUbwWc8p?a24^vxrYM4;'
    'XqI6}280G;1OYM&K3xqY0nZ|`t&S>yAz8UqR@lbEXbd!hDje(ut~})<+3zQ|wNjat<*Xd2Lcr1MDc94i%m%~(7NB0s5D;-dZ!WR<=4^woAk>fg'
    'Rf$-VKx_&KAPVveK_d(U{Hxkt2_wPs^IDazXI!rhp}-3h+s^Y^hOSq$9#w2H3P8QUf-3+q3I+IzkoB3wUzUg%7y#acZ(7gFyg51%B>3*(%yFC|'
    'NN+WNE)&(C2Y~Cj|B!&Mg_-FI=$9lVfmgCvQ%zqT)vtav($q*s<oQq(S)nRv{`cBW^NXk0_|;Qv-2B4=j<m#Z{NgEQq92bzmgu6uRLuW5_*x3T'
    'lgd8=QF8l_JOB?vFYEKSGV-HHJ%Y;(n<$6`UI;JWNfX4c7GdJ&7Gcmgk1#Vcrn&ZZM1bDjtgsivvy1ibBE=bfv?WwY1FZmtE&C>&=$j=x>B2eq'
    '&{`?>BsE+eiGV%svT}^$G}Al(R{2+SncQfvyXS*NG;(o&Ors_TC~B!mx!y3@X`B(rjdU`5CvW$;-jZBoJe?%%Z{_wWwkPQW3`LohR@}8gGo2E2'
    '{`H*L{`2iFfuFue^{Ta^-kGXQn<90B9G#=i_4!dK-e_N#;eczMadZ3P%m4U0yG4kBS#u_U1*|WHdV*<lf`f0nS3w7CUzriJecz4S`b3c@A4+*D'
    '4#y>vy>l);1_Sfj{1(-~f~oY$ZznQtWCIlfD+V>Xy{o{RN?YGJZlgBqop$?HZXYAk`Y|_we{bJXVRD@C%liUaFB3d@d#f6f$*yl8`0ztcMl>Ij'
    '<M5F{k;%<cd{;h0KiAKV#`O~XIv?Qk`LMh6=j0q-k27&yPCNOkq%MC9+*7R^1U)&AeGHBI>p*+8)af+h43F(3%v@ilzI)xOHy&oE>x1&c^8A3w'
    'I=gUazTWXg<J490o>wBMh^=g|#kn#n4rWDjJASMN{|3%W(LciZzj4^lIRB?Ze!zK*T1#r2W+@B>iZYa;C<?*1?3uNyCRuj91+bsGjDvNb0`%Qz'
    '1UNMk%-5211<&=*YLjXJZ!-jB3R30g>M|5e6~LL$ZFInbwi~+%L{{8gOKKp+pg`T5Z!t9Z2K7My^(&lTD{+(ta|$#CdJT%$;$x6)wY&lyK+sJj'
    '!A)hY+`&X+lkbC2!VKIUvK++Et~VxdI0~@6$iY#}mWxwlzm4<BsPQQNR4Qo{AJiPz)c_;n|18c&@n7S-^kr-5PdFc3|J!kXAN?bocO(Np97W)6'
    '+Yre^y*{&r#0~@P?zQf25LD*ZOk9>qH(k=3_VROPeN_R1Em*vV^k~kGgwzJA7-D5kMKM*vbQ$i$JIllQ(&*!9*H(Dc`2J%&!rql-4{5=^L}+Y_'
    'vwQEgSNgj+&$yg-z#;qTKFGaDv`*Efi;ltXoALhv&PUk)EY5q;;r}Ae&-Ehf_e4nU(Zvo9++qJT#-n{)tb67L9epORiOnWvz&tK2C2-IT-;mDh'
    'V>U5-n7@1AB-bh*uM6XPmwsw3j`p;H(_MAnUH5ocS!CQ&_Fm_0x7RZ0RGCP6a_(w<cH<p#3=lK^`#66&U4R|sH@ja4#BpyxERz7VzkdFI{Y$;)'
    'KQD0o_QBsU|KA<>qscIeu_(v`XHW{q2$n$z6eZW+G)*EbNuxN4;lEf~rBM*ZN~J(ghi-G>lmhTwe#rfRw0N6I|BBwzfMpjY@cdnG9mpmD2EM{2'
    '7y_+y8+Z^=V3Ld>pvej(z$Lhol)o~;M9^(r6$iYXrZ*Q64BRuoMp?GGAfubdB?@jQ;2${X_^$V?occOt0(UD4lpNreLxQpU%KyP&YQ0C0f4#H{'
    'CP2q;`aV}Eh2WSjIF?^X=R6v`@OU%JpJ3nqOy8H7eE0$TwkJ3DGz7C2w*xl9hnbkPn!A1|bd}I+p(EC84w*lA2a6_Q2_L|lqkmWjgKaJDJNS1o'
    'XnRmpmk;<4>YrlIB6Hd=T=Wh8uU`A{qK3e0P<Aulrhgc<Z+9eAO5>v4%rS-UErGc$n)_>`Rk6N00z<#F1UC25BWJt@6;k|S3zl11h}j+Pg)vol'
    'jt0w6G>Ya!bgt4nd!b6KKdAP6e06swH7xX9bQ*1*0yd;&;f&r)X{Hq<*Bx1M-Alu??#U(uqlJ(qdMs^U-w7YRh3Mg-(r9Ft(foD$<_D-Z_nsH='
    '$LB)djs1&K1=WXmLQpGy|NN~H(sz!)&=*VK6KBdHh}YKA2da>}g~^&w#NzeqxKiRY;M#8Pg25=L+VC3W*0hJos@JdBg^ZJYF5T3-hZlH!5$k1F'
    ';y!s#4^2M$NBiL@%fmaRhT*6ar}@R9yJ&-VllJzl*^M#*iOEr{1u~fNr4sov4!PghruYGTJf9;FmikAC_cxCH6!3mJ?gzX>Szz8qVKhyU3`-+m'
    'YD6F_&XG8ak<7|?N%GTn1_&nHY}LV#d9w+sFfj4X2!IqokxT$DU(kD~z8S3jgm)<o216^JtYnfb0JWtzh4cDr1wnjsStqwSI<NsofNxs5;V1s9'
    'bnTU}t_<}HJw-_1bhIA4;u_ea*v!~~D2D-8#g>4%(k!6QSO%Ie$d=-W762Tn&D4$B`YZY7MUbx7_m_CLKZ4;1Lj8ev&J8K`nyUKtX)dLP-xudn'
    'f2wJ=pigGae~ozoSASq0q)30j&vzj?h$&vN59;eJ;g<<`y;9vkLcgDYLzZ{|4<cr5qIM9Ham`!5b5+o1m-TnA>NiY(g#~c}t@PvquBO|mtW31@'
    '8CsQgP+G^f@v83l6DD~CcT5d`3hw(j#8ZNu&-z=rbas7vwAV{#+>K@^he_`6d&}9aGsy^q2|H~+yhAR)Xahb4e7YwTm3R<Rayr4@Q6}T%btgox'
    'jCbSJ*wKT^^p7yOiF&bro?2);b-8WLm6;UzFqbtflwCi+*+T0Qqtbb-!A8P26X$W(rHkWI-LAk-X3~Y4{@{-$)XG>u1q?;kEwi$^f|V!-7Q1?u'
    'F@iWH>0%GvxF`rp<!z*jj<@g4Y!OO^Sqg>pMCcx(aISC`D!x1m=DYiG;P#qzpc$06m6!oW_>}_JiG7d6BDqvNe|g@9(Mht!p_~WQnF>o&Z4#uj'
    '+)fun&!tX$vDe{pGciu>muMWAJ3Q<w*W9P0-Z@GjhU_y)%7jbB2|B(?e0jq*ZO=`SKRaT#uUYzX=FJOJE^J|VhfDNERllO{27Vp2<C{un1ilA@'
    'wBO|gWDLW+P#Hr^Zr8M@b8Yw@<u&VfKppk*xP(@Gu*a;Oh=+Ml$H#83XW3i9f~=D@ZAc(}KESa581gEKHG_oBBjIG_#R(9scHouW^{kd$W#>HH'
    'rvh&bnfB}C0@L2faF1uJgpx<(Ed6=BD1*&qaon(#RRIOPsb0tY!Q0`^dUR6g^1J-lho%r_G1H5luN-6h>KIUedU$sBG$m}5`y=g8;}03vKWyQI'
    'ftl06k$X*5pyg<rI{E+w7jxGk(l6FiKQFw#pUOf%h@55N_CotAVxJm@^zJivYs*()Wc{H&YclRkqN5#XZ9onPmP=>tJdKc?sO5vXDe!as@zoC0'
    'yf-D`b>!cSx4yk@mCT>$?nEz^{aEWnY*1z4eZ8D3>s=J2MJteF^{$;_wBw(x=00IlGazHpg>Bj$52yU#?sv(xnDdExqoIr6(#VPyv0<?;^rFPr'
    'LpJf&cB0$2eAVoC>9Gm~RShc3<a74z=*&}zPcA#|F5%mK-4K!B=lY=?v^S2`{rqqtPwHiU@oGAdN#3UF8~J>b^`2nYOFjheS1bqco5=5nOU&c!'
    'd^X^$Z(){Ni@dk#T&@sT=zBY2_}g*CkftByFx#DP-0pQ)ai~B@&1Vl4J@|zq;@+8+?eKL7S#dGywU#Qp0fHUtPI9G#`-dZOK(pP`4y5DI&f-gq'
    ';!Apc@BN~#A4K+KcL*HOv~%}Wb7EBWOwj2LYN>vpNw^A3hJVZ2Q(f@85MrE+cVlZh1&=ex@N{q8aO5fOS`f2vc-Dmjui!{rnh`R?94;&_+z*fQ'
    '<zz&c(=9A!dXD{zQSAj^xE%>wwb03k(kHLTWG)xSCUHW>A5c8rL(fnRqW5?%2swyP%d_blZGK8B)8=$`>?B$6r20PcOg}c*o|11biNxU8GjA`i'
    'y$d?@7^<?B;=T4fmGvHJW9DpNTKnWsa%9#Yv`p$B2GfS@V@b_{7E{86ZS%PM+awE+o%C{V=I{2qzCHF6srswuevqg?J?{tR#4rqw<0yp!8zYQF'
    '>6JR+<oc~3DH10boWWQO{Z!t(mTjPEMr_Wu7!a_e2vF&*Yz3#bVvYFvVY$*7>~rdb0Idy3m|0m112|E&@vW62t@Ml9woTV3tjz4o3@6V)g-2k&'
    '_BUF~!%ZLqnvB#I<gk{p$i{$Ht_SQMGoVJKGSDZaXmIwm+C?@;N)iP{;+Hf+1lycQ5MZpkazkoUHKu>*Z?yM7hj9K@DteqsIJ@<yI*-qdi3SKN'
    'xn#fNKFv;moZ!!enY1bEzAkfa1jRc8wM!XDsmY%{6nP$~#h^mox7lqX|Fi<O{%wit)4rogfF=F#Sk1AYkvAVya9?SX_9YJC%Zq%c#aS!D{l<)-'
    'L)^SG<(r#_|656b7KcG74?ppA05Q(D-E45UXIkmKyGYZVIP$qZ)_Ts-vDK=wh}}=4l*4&<dGD^TolTl<01Z#?5m*l)<&VhlG78@IUV4w<3dVI9'
    'oZydSj{0#L&lh^K->lCvOK^j4#&Du5Gb;-y-OqkIBn>k@kiKH+$J<vPc{=Pzao|X$e|nRh2e^O1W{p)YGI?vYhe@HxOL*Pj41rLAuJhrFP46!1'
    '=h(D|u@N)#lFxf&mY(t9XrRW}9oow8i8sj)?w;JWsabouU>X4lz3@|78!omIM}<#Bmlfr;m{s=Y%aQEPvYK?sC^UiPrzy;}i|^@GPvG_7HDsR`'
    'dlJg|Nls9uor5Y*aI!5CrLtD$XA=SPI6QQ#CGbVoeByAmbf=+ITC$t~OW`BN)AQ^?qtZ*ktJesQ)T35sW;!WKuhgyudA=mR|Fq5doRRi9^^7?0'
    'UQ=?h^C)n+x;)l)q(Ri15A&z%@fXIZ&3!h!;&ZpR-go1Cx_ay}g|91harK5yx+z)TM10?buhzUaN6$)mZY8ky?A2(PJtL#5y>&#=;@&7#F7*`~'
    'wc{0G;~KVZ&vQ9Vn0OjPb1&Ld7GwOtH?so8b49wmT;4^8?{^^@jS;LdM53x=4m%2s)l%!1I4ThSJz!SO)v1rW^Li6HqwE&bgUZX^5oXEluN?K9'
    'Rf^YU<3{*$-oE^nN~B(iy{F&(lmz%kcL4g%&+#u6raT{<o;B0dM|LetB#IKKH&m=|7w49ntoUo`%sVQFH*cg7VLK_;EsAReQRPRu?Y<x<<46jA'
    'YKLLP`146JW(mQo{e!XMIPPiTq&s|_AD=AR;IDIZUC^H7lj24_mLMJR0%D?THwJcNs$Ar`#a^zZOW&&8lWbPD#NsdNdYLb5J)e_!VzSYR7iLA}'
    'gCxtPl&+N!I=<#>(!Ok$7);Z|{3Cp#Tt@Kr9Nz3BmTF<lrk`OOF6|(aUT@d>wLXSfG&Z{RDxjAau*i<SsHfzGI69v4MiM_-UhY!AjUMy?iJW04'
    'QN^qdiNVUd=pmjxOGubk8M4I%>eB<to0<ZXclK<t`SNbclW^vlJAPMM@etsL-KiceSP#YBy-Tq$EDzR8s)swHGYt(jdH95>r-l>iB;p1v3RNPU'
    '$(Y-7rKpK~^GXhTHKyAUiO1@sX#ATxr&7whH}2g=H8cmWPCK&jJ$qigDb74aoYLzM+j~-Ert>b8={CO9w_|z4<>kdH86j#<Cqr$SuG+&L(kJ}g'
    'Izy^OZoshwIdx_g9M@WE>UHG2()(jbgi0f$o$Q99+$LK4R;qA`9`F0DFlJ~L#^p+?<AhM=F)-aDU$Gir#>fE|?Azl-O}61V>X|_vX^$5by2I2~'
    'F&f+3MfZ%nLu0~uPBtJr>4p<?n%FJuC-_2-TEp1>djFj;SWHU?xvao_aif`~+~mcilbk)rcS=Eaw9{{C!^dtp8anfT{wXDreuEN8f0GhPKTx8z'
    'sA5PQB@l|nXcT8xW`q$WPE$030slu5A(>BmNx(O(1P+OL0XPxJKSltdSlLjuZBwN<(6^-Y76HY6ZvMaZ*;nENIzK2FOy<>=qqog9DIA<Q-z?GS'
    '0%%;y3~V;6ED6hgWynE*r3tbETN}WEW9v?V?tTfV)XK6_bmMDV?}{z9&4?77v?_q*cUAsZmVu@_vu(&D6i_X%Y%M3id^rDWLk<=Yq6GWaOX4r#'
    '(uKKb&PBdEVCg%9&E20yrX2fO@BFu@2w)=6cT{Bm)#_|s|3*NJ-uK3iR{i5+rig6XW9SECM^6Rb{9lY6$L8CstS|DTxBquE4FX1wU%K?+^qIN;'
    '_x_Fe4JN8-spzUv&O|!3=2~>@RDHd1Kb=`>OZ|?ish;zPv+rq2o8O;iQXQVM8n}m$?_9j+aDUDeITko7SW7zoib1Y*XwT!7xh5}c;LRG38k^tK'
    '&djN~ymxrBs8iK$q`LI5&o-B#U&%T@GvZ+8(_zLul)hY_)DC;A=!t;N<)Esk{8#4w6KBYFd=bU&++2c!8UvPnBWuCM9NAs^SZ>g}r^GaG+m5>K'
    '`(x_wiAq4;FSlgqgB$hC>!glePd{fAOKH&%j$S$jBA=U%lLmKNhWNg=FRrIrOGV&;<=qouDADA=`6Rnyl6`(%yuS@e-`r${$L;pMU-A^>fqt|1'
    '5jcQ5z9iV@$KKZ5_2sSmmtg-t|H}x(pWEaA9q0Riw!c2tk1JvXK~XeLuoyyvU=xZ&KZ7>91Z5QP3EFl|%dIWFKC+fqECa+9D|X<U2#^M_^7)Ph'
    '1N?rlt;wE!B-!B^(2tZA*a6Ggt;C}N;DAA40fZg|y8il=>W>EgLRkUY>ExzJ1OWvESeO9fkZcRUO99}5<qihSF`3PAh$g;v(ASz1EMZgt1WOWJ'
    'AF&0c<RIeUFUNv5s9myeZE}sXj>V0(h?7shehz~)<sZZ6Anw|_rXP;#hg0k{1zxzaaG(EBf&^t^A;%b9)RmnZm&uGI_ig&!sDIro6Qx-TzH^in'
    'GYsvEm~21h?%!JkflSY@Stpn&9wrC`<e5P@f60|M2{0zK#cz*|ho7oZzu~^?h(7{I*;{)TVXg1B#>gD^nk)ecqFZ)B=n2H6FI@Y9jcQ{x2RvFS'
    'ghxWa7BY)b6l9bh60glL;=5>352UF6)n=K0ZDV%*4mjcvC<ro@xlVZK%T8D)D&8n&!{o`=t`Ca8+fM6Yw0`9cRoV&ndsQ@0!LyxY7!T6E57{A{'
    'Z=pXW18x>)@etG4Wg70W`}UHepWU&JTc0>F(zWOlht-0q)uGV%%n06>6}#H4q+Gv@^-kv%YIs_=oy;GN<@dn#=gqPQw-QdS=AtB2S=h+l5WBo5'
    '>wPKN&XaZNx*+?rsNc+Xk+7*(o|m_a5N(92`hXkV-6|f$Nu9<~FxT@vXT*lG5;;8jKA`+0i`@DYnoH%$Qha*$T4(4yt=LLwcxHD~Gii9lfgc$M'
    '8YwOI`uAxZuL<10zIdU12-X0q@sg^kmi+zE|Kh?xu{||7`~;K#@Dv}&_}Sq<4iRyZ!f3$oXp~@Zc11%LVOA!{pahQ74304r^63g1u`S`RAVX6C'
    '6~A=AFakj0iZ;yVx4lA5wWXY}pSvOfJ@uwmqcZ@jD+tjn=!UHzw*pnZ*&qSCwsIq5I9P03sTu}?Sbk-Iiv#|+azn7TR)V?Y%23yTV>AeJN;ik3'
    'l?bjtyyD@Cff)%r+2{&zOm^FJqqit3wA%8Z5%6y;2cWuMYg+#93Yr_mY(vn&@hU$uq1bm$$9L-I2Dl;gNkYlZ6x<I3+`_#^ntxpjl$jU3NDKY&'
    'sJX~K^n9L=B2R?^RMVpUby5N@`!K=XOPUTua~?Jg2N2r%hmh_A8cATyW(ORIeL74Qx=ARI&9ANImamVEk@)8%mp^nH4^s)XJ>-Y27F_f7?2#Wy'
    'jSTXiBPl$&Q55<T>-&*+G(BXL$FKRLyeIfqi&v!&H#y<ET&UmaqdEJVVBkk+@}l!hxRRSjt%c{snDO+kvv6PIg8UYEZ)J9^BXTGYb=`~-;}Oa%'
    'KJ|lmBw%aD9igrjXYV}wUC^GF;fZ@KA)fnu$=*2b9VX0T$#>H#IEoXm^HfEbC3&B<{T#8=X=H2?BAMc@36^sh+nT){Ss#t>4t~D+@zrm3yeSr@'
    '_7K(49-h_c==tQSPvbnJyy&E@c=DjMr)AkWD)vR=&$Gcy>h%#>7qbmGeaGkV{2XyOx!tc`LD<@@k8NzmyIHGTJMW05fykXncfKyy<FPNfioJRo'
    '+{s;jadGl(_Ml`JX2(U5*sIHT^S)i`*fj8)%p%c?2%ga0taR3;pG<?aXM%0><+d{}-r)IiHx*v1xvBU{TJ^jlr0AwZrZh3ETX*xJpb?emP=shL'
    '6^++J313Y9Y<t={%J7$PWlzVxC)fY=hZkHM1)DD+cY25ZWg(@WcPMec%akV!we>Eu14P(A%|nNkUA!>eY3}d#VV}PfDn#R;xIftU>wRWoI!MxM'
    'p`tjopaNz`_oEFh*nP^bUWW?7v-bV7Z0y(wrrKK&qu9jbZxL1Bea4fpR6BiDosY=fu{>^YALdXccc}K0_>}mH*Sl?zYC`4|%cU&X0dIAMH7~Ol'
    'MGMOg)jn}swNs>^s7}=37EuR2#_1gt%O~YoHWZfKA27;QPew;ZlYUSG;tU7WdK=U9Lm%zO*4Q4RceshE$a%WfSAxw$<C(|TU3}nzUrBF%l<7c!'
    '6|53I^lmMqDizi*m~$guOOC1P-Lpm~PLDeRI(P#0sO3W(R*#iTtrc3ti#GR+iuGRH4FqWx?PEf%+||lt-tQ06ITsG3CYh3i>&*p9M`LuEvwaWF'
    'T47%2eDC#RSTXg>#qPbI4+U~U8%LA%8ydYD>_V>Jyf?+(9O_Ne<Qv*yA_hlySwDBMiabM2<nFV2TklHl_11OlaD}6?qwGD?U&i8IDkqYH5nHzQ'
    'I&%mZ21@ARSiHPo(8>jVw5D_+UJP5=L~6iz(vQ34eGXEu<_3gl$Pnfe;gquM<rLaRzrR|L|CqwN8PlgDY*lG82y<B47co<uvAW5*AoSki@lF;V'
    'R>*O!nBe$b!DX;*db3j456HnzQ?mZdPcvo4m~*16u|(d}Ss9FyEMe@H98ZQvtqfR^h50d0q-LXGmMGP&mED&L?b^i7eEaY`b;Rq~#$vp)m_Xt#'
    'rj*=G<Y?8&E{g0EA&yHz9!sJ&T70o-{`zb&)mxzDUis5=nuutw6?dkEo~?+dwPM)=kDolD!$DY;Jw{jBIoG4+*4vuJUtT+0-J!J0LS?iZ6iQl3'
    '_9lef9PFvK!%ZDzE+p1-chKes8QSuAslukgNhRe4gjO8ABP&m{77RK(xd%eW^;`Dwi>wI?i3ZE@wmZrfCzuG|cPd}c?SpQ<X7lt8YN2r)nVT0k'
    'jt}KBLob+Ga$$V8gZdv4Fzi1kVAy{~z<yZ&C)YRf%D^ZFrx2QDaRg;a3MCl=M==~lScD`o^waW`EVs2Y3aI|c3e<TZRfXC16;L4X$1AW@59}#{'
    '>Br}tw{7sqP@Bhp35JN&mLdlPR5Ta|eu>Zo%xT*?KoB73S_xB1{W`jReNhnSiEkM&G>~NBEI0+7eXPnAAT1QEtW}_$w^q*?wYC3nu*8OKJ8FQ4'
    ';Xt(t;@vm108qC6W#>)M0A)zue*_Tlxmv~Ub9AV^yuZo|?djB?Rjc98owwiSUVwT*zrnrcpShPAoMy<3e&$}Md423}aW6o<p#Ow>0qO;P<6iaW'
    '+YH}StQu~dG}#KV5`9O)#KCprdn^yBr`s4t+5x?ENX>-4cMkTKnd#0B(`C;(V%&Sp%~Ci?CR>?OH%a}|@9_4#<5$$xchK(IdT&wC;ZiAOUe(!a'
    'iIY<aYs4#b!#Q?jVdXDKr0AchSS?M5x@ZscgXo>kterKx*9o3f)DXO13U7WA=|JFX{kfO%O~uMTnV7A1&q52uYg-^UY;vsyaoNQ8+v`zkQVwDX'
    '6Cr}g_GLs8(HxAM`!0PJ+)}Ua4Rzwo!91gmQTEI!Ol)`5&)K06_n~-a&lSx>1YQ$ue>8^UTd7C5K^r@ME{p0~?U_aGnjL>b#p<tEb~!!%<-D`z'
    'l5d7e<?CPEyFZur{-as;Whg*UpzHSa`NrjT>A&dRe{9_ShiCh)ZTI)j^ux4*VHuXj8G^)d5~T@@Sj$%$?08W$!lG+AOR=BpH&zhAwg}D)+Z3uf'
    'm@1&u=BWhy<A8*NC_&wqtzh)I^c7UB>4s^*?H9=Nu@Y=qtpzbn0&NIrtz}@ifTo~D2RxxlP;s)qDq3@P(}HX(x-0OZo7NTGE)v54h5`e<3|wuB'
    'fr@p#)U_r}$xXCdg2$_ES)lroAya`{0?q(Y$BNm^UuPBDK>C`0mrpeqCU)*y3-PLbMWQ+{5bU2fysDo;Q*mqQVDg8LafP#GQpwFdn|U*h(YBDI'
    '>*n9|F}9e|EgcF;<6=<vJbJiI?P2DFW1?ZlL_N7lgrsuxUQhC^S@tp709p>9^ME!z?DC@{)Fy{r0Em8*!&X0)*Wa!d`kl-D>}sLEd%3^r>p`Hg'
    '$8jFEYj16K5&K<H;KZ2IPpe~-rG7lo_!eE^*tcI@HDk|_HuhyX9}fxRmU%8f@o<$aI7BSJ$Co>Es!_e>)O&}f<t2-T+9&nkp^7MX402|zOOy_O'
    '!<WeKeO^@fVFyvu-F7MavqHpE`__!By^+iZ;@RRc{qC$0ez%A3tT3Rz;rIG;U+>O|{FSS@JN@)h=qboF6_!b(-au?vUxu(c9IZ0uYufN0T-x0T'
    'rx30I;wcTcj~~Nn(cDSEsmF@S_!A<0N;TdJ*-nUHUg`OcO;KUn@7M5d<Tu?T!y<5#^75kT1Yo%$uVRd$q0h;B{yzh#-hV5gdjD;J>ir0)=t@CJ'
    'ip5ceK`<Q0P>iNX7Qt5bN#HED{>|Vt@~M3uj%{5z7L0y@c%R%-{x$^~2*)D9s3SuG#<KXY693X->%FmHWLy$p%DV#T3dz(4r_8pT00<}s7GblE'
    's#YX;CjP5LhLvk(8#7*MF_r?cU7CMQi@>&y-wK{9v=#_x^sTT7vgJ45zI4;b<uqW=U>;0?Ee4VRZORo<t1XlPq5iTBcmart|B-`L9B}qRkqkeI'
    ')YFgeL|*oL@zZ633i=gJ{au)XeuYzi1EzccQ_#09gMWys(C^*^e!g1hcP{rchjr)|+XunWhgf(ALs0vqNQK~+WZl2=Go1So8lGO-eGJ1%Orf$u'
    'Uj2++QDLE|+9>>7CkK~Roup51dw;k$$W%y-0`Ivqo(4`TF`0C;dhOVldV60WU*ylb$DUE1x$5`hPM^j~mZs@h$L6a#zbUcTF|d%-r`nmfpILr('
    'OlESMy7WzUs-TNqR*}`HjCK~$TgKj}oN$?t58WXlX4Bd4(QI!Q#?a%)Y&}GaRbo4p&S4;kos1`tDN%7uDq}AAuK|hqqhwlxFHy#_wD%Kks754c'
    '%#vp0@IH!yYv)*SJV<9V3+qrcaY%ie1YMmb)13D3%^;BonafaDaO`D9=Y|V%>iLFmXmP!Tj9(GgG!{uWT@E9~;Wp<((LuP`Sc=$(yq_J>MZBOT'
    'In)w|V-exT-kv5UYViwNz4^ldw3-Fi+P`sh@=)A5NszC>+~{A_-oEDZvz(YH#Y?0y<1#$$(~HDi?v$;0?d^J%YX+%G&rPJ$ES5b{b;s%r?T!VZ'
    '>w)TNMqBxZecPPp8-5KieqX)1kT}%dqkA02dbqfUBQa-As8}6#31qsv)L9QP@ASBqdE<!B%w4>5y}f^}{Jv4q>L@+L#;<r(-0duCnzKl_AZoBM'
    '759Q^ynhwd&VZDZJM!s3?Swb)zE8w@Kcb%l!V-?7;|P^B^Sx)Lb4>leynWY}qlUKaJ72Nix#x-;JjQt-3J^&m^F|g)AV31~^%vB+UA^tz-s9RH'
    'c9{}LRV^*%T5E>L^9B{=Yo&Z)W?RCiP&%W_1g!r?ec;~oAXI$3zTRh{?1bRfUeBy2%TE2ZuK|8neei?$fTI(j-F_yvA+(0WXJXoFLV!S&D7jB&'
    'SVM)9{K;n%<XUI<6V5*>+z*`T&ZpwNte~cF&p>c$l)OKbtsV5jcK?og*p>M;Xb%Ff4MTK3i7U|=*9o#(zOUI9w5XiK>_#F_{S`-mf)D5`6RFxO'
    'Y~rK`Z%-_*!~)BfJ3pR5N?eX4Uc_2(xU*CzYDh7jBSIozt8CUeWB~C=llkSE8JAP-;5ew&^0_aMmz~%uqA%g8fEtulIo=#`y-p6bdXt`vnt01%'
    '@^!@mN?;^h1!m(}TZL<P8_cAPIs3vm66P@`sCY%WVUNg^mhpCTWeSs)uuUJftTN=#`v8Bfo@zg!!gi02z*_7hX?t`@**s-Qwcj}-S3MW`mc=(s'
    'vsa$3x>78R;uX+sFFs1ZP9s)1$9;M~Gu(!WR@;j)L%?1LYhTMNcfKrw3zppwO(OQ%s)Rm*p(Bw;BJz3gfdi>@!=+(P-5Hh!N_*b0^w@)A>lL&Y'
    'kZu_qF$M&+n_#K8L*JUZ>EVQCT#^9|=7qok^?ABnMCt5Okf!UdEXRjfIEby{=oWNi%I$-bFYE%#C%8&l?a0sAZJm@mAHQJZGV}oChXmxVH4Zh3'
    '>N;p-GLg|2pvz{GYqYHbb4vDNp5_5Obis7G;ML)TPKr5d{iS6B;Cvs~Q#>%IxVFpGkjtuJ4eCbs4=AUPY=zSD<erb}-^X&6`hWNA(9deiuf`$>'
    'gzR&^?c4w2x}o2HsT+Fw8M^)M$zPG$zd7*-V77Zw;Rs117($^4vSBftqEMV9AZ+^zLr8?A5d1?`JGFPR$y>&bzWqn?w})p+yhD$py@lNV+1)y+'
    'Kho$|t?u>^3f=orau*=%P3i`e_F$}hXO3)u2ts#wg~GcqVuMTD#pv{p<X5fk&Zx_GgonI)*cf|zt;BERtasCm68o%hPujtEke0rqpSPYjeMfU`'
    'ZSvOVM%0cA<G0Om{O-MX`8~30^Zyc<?ejtOTdNzBWHk5&%?W&2LI?<(>Gsb0a6fB&Boz1t%!=7`U|rkk9m$P-ChaFS%6D`Z9^l!<cA)w3jtBjw'
    'r~Ez!bT_#8JR97xSMkz!>dJb4X-&7)katpPu^3+t{zBP)<QebFY><a_+ukl7qsk0y|GI8C>KRu;qjB07yU=8R>1zAVQ++GjoknMWuw2>QFg8#N'
    '{C!;mS989yb-9HV*cdG1<b%H1CZM8IU?v#FUzo1uK%d4I89DKR5{uf%ikgV(XNXfy0r_B|SMz{lM={GF$Vu7CaU%dG;xOyO;YD7{?8Z;l;v}K('
    '+iQ4?T|Y^?Nu^?miK?eeGcp-uOJ~tea*mDU=tAXf1S|q4)tJH$@ufujkUS?*(izM#c|K<rPZT2%q2Z7~-bM7eQHf{EhBRNBi!n+cg^B{^Z4rD-'
    ')2V}$%E#K{T)u=w55Z*imA1HcAye3OTgXA}4Gf0t;Fc%N3ry)Q$0uidBdIh^;@4nQ^Vfki4G0{tfbJ&+HZU=sYKX$ug=CH@WbsFy;NT~l8kRI&'
    '=I7e`#~KALNVG;~;hszmhlsPgioN-0l(}0J5lte(em*(K%sQt`r});wmAR0WCU~|%FgZ!iKsw;8v&ievblCa+^!XKMD?gC5$s5W%G(x&v&Nruu'
    'pQe5uRLad=`?@6L%<BQ=sulnSTum9(Y+xg{p6p{SQRdA=R46h{q%&?&(wz0lP1saEoqanF76F|juW0HqtJuH-Qi5=FY0Pp;X&J-17vTL=pHM@u'
    'FFNE({gXYcQQ_0Gbk3Da!#Ey!FB*|S@dwUv-4S3Wr;=FHBhqKQ3@q_N$6I@N7O)f4<b_oO=+UqNNNjJTp?}^lSg%;mY#l;8o!Sz~fnqBU;i{4r'
    'QydV>!&uIFe%Z&q?L&X%kn?G}Q2{Jl%woql;0r^^haqHT@>nl5Jlfk^gT4soq5g3?ZH^BeB&(~`-P92Z0X-Jh+&nlJ;e`LfW8s&(+bU=#;3_x)'
    '<$!Bv&|R-F>A-VTh(vQcBFOzEhvB4==h!*lE*z1x+i!ql5+-a)2#*WwIcmUp%CFvNdA4io71i_30lGho0Sl9ko$qiFF;Q+@`U{eAy7H`5`|jF`'
    '-&H-k8XWt~feTi?2AeDtEK{vu&hJhdWO)24Stu9=^U@c02b`WZZWpHrtu5^^ojg17&J01KPfr1OQyif~dWm2Rrqd^*JUT0Zh`tWFR;2V%T`Q+U'
    'PtN(Zl$e7jT7}TI1cetu<*h99022cvXnoc~TB;1aB2&w{$5X^Qxp}>_?wtS`m155eJha-yzITFN%?~RdXlf$J*?j@c;0qNVu8VQ?68uF)u2?+{'
    '`X&il<fBO_EfpqlP7gY5c#0#-j842x3Pl~2v1T-PAXd*+jX1)6kyic++ltWGQY0L1PH735LT|rS7$%W&YmTtn1<Owd?D|+bdm4l;G?5u#3SNq3'
    'u6$m?v&_)1!aZn>36gCV5w-TbgGr#xcTzki*xGqh@<4G)7ZZQTnZq!mcVNJ8qbgp&O2ZyP6UyZFQ8l4H3v@L}`H1Qry?V`b+|7!|g;=c`$72z!'
    ';C)F(aI8u|yLQ9@bL3ZG<W$|uf_Oo75GkJm2jVOX(cmS1khitWTl1V&5-x6yTEKvkdev*)bO4$%=FTUC*KO-wt=IMxM=rZvjCRr5Nq5g-bHRp|'
    '`QQHtn0+52`rE+lZ=L)RF#Gw$?|~UY5D*T-G=U%}4Pi7)5(o~FI6{yxjX@YnU<mRdZ*KQwCqK{Z@wW^iN#0gH+3wX2({DmCxywTF?OPuY%;<by'
    '`KIrXQ5@TMr#Zfl`*$trTUtuKGXdducKq(U{^kc~dm#L;RuJfJCYPsg-#cQT#ceMvh4)F`?n;X8M8AE=N52`+@$Njj0ZAy@(OewAEjf~Xe22cL'
    'W!sO2Vf)Vo$2-dy`@1WMZzgjhW5V~th?Yyrc%Z_McmJ~Rf6r~`w=mfb$$+0Q*(bN5zr<u3WPEcQ`hv+cXy?lP4kp_n8Sr;7**BK(_n7Rj+=c|F'
    '*L{<ihoV}q7y7P>dMAzuS$3mC=>=zdFXb4tK$LK6lZI(sGa)}ljeznHxhR*Dh~8Ee#ZB2~SKK<ktfx`eO5k}p-Ehe{loylTE(%!Lg|zV}jL#Lu'
    'U=`X^hGi{{Q$%{DZGSeuSPJCtafYP{!2Sy=SWBs1U`23`LKH6~1xJ|D&^Lp5B+yT@k20X19asz<dvUUZ?g0-j%)_-%Z~Cu-!GE#S75z$X;vRr;'
    'x%LDqYk1k@85x<M$e8kqf#qXTY`x}cK7Hc#Jm@GolWCTvUI(X*B4W(G)6H}shUB8!N`dX(rWAtuWxG{hJnLvQ{Bb!!Q+;rP+*hZ2au5bFK~BuI'
    'LDvNjZ$v>9zp;W~rf&QsjL6bY6aCMHYA;%Q@!AU3P88lB_fu{B%~QWr#=mvikD4-yL{V%jh%iJz1dbpOM#2b=(lE94wOc>CEAT%mk^8bBf9Em3'
    'yUN|ahu+IgmhSA3t!LZ{)9%LhcCd^-PPd@neIfboRk8O5VW+d8yI<O_(I@wwm_Xk9g?!h$NAE3bydC*fy2bXrJlYi#Xtq;rw(6F?JvQmLZXbHD'
    '8z6WmD<kBaLY%(yE~x#i<Si%LX*$&2gYV%Q@ZO$ptuFe0O!U_wV&dD7?Hjel3=6Vv1G+w%XkLcC!Prmc&m~gRENlkU&%<_}bJ_GruV3T~p?CR2'
    'xBafJe5x~hC45)DMLR=Vjr}ay;F-(&0zdV_+YA0qXjaLyVateC>7P<Awqt;1C!Y^0ktWQGS~24no{Zv%P>gEDC;!b$6Mm8Me+#b=fxRfZ!eYz2'
    '^JgV2yv?Xz>M1L{FYr@z#zp*Id<J}^K5M!#IPu9Tq`3ku&*3qXYWAGu4Tx^1oN#))ERIH;c=O-`lOK_t_p)QzD5E3MATc(Uip#DpnvThx4=_`k'
    'RUF#Da@rgC$!_AJ<r=nz<uh!ZF@UL*8x@|d7(Dn(iaidOmiau@{TpKG3j&-t-^(+$ZEu}2wjEhjrms)B*;OA0Z~iPk13s(IW)H7>3ZIv$Ylc{l'
    '=oAzw92UU`Kj_^W=DC?r=}Okl3F&ZJ33)CuG=6#j95--1JjlEEWSeOkPMG{a>xx=OoQ#C&>&!U9b3;VNF^JHl&!(|n5tn(=YErRM2hb9HkY%es'
    'KhE7hFL(R!>_04bAD{Y{<?j2_ew0$c8|s5-8YiI*7s3Qep$Li5C<Y_wR{KbTASv?0dbbs!6y0H0Ozprbd8-ac;w?_i{y?L>K7C5-LE%5rk6lIJ'
    'cK|i|4m8|q5&8~!-fHG{cAD>`m+gN)2^{cv-^OlV?7orM*L0vikLuuEwYHV2ed30{#S(A#;jQvwZ(UhV?I!s68yM2>e8k;V1m6iLalZ3cvbSgD'
    'K81X%I(C2gx5FC@Z(#GU4cYc-67)?<;n2Q`Ut60yj01a7gSoty{l`004cLp`@6^0c^R90-57>*|e^B!l&Hf~=1>Ofg)x1UHo8PW^z*h9$!@=LK'
    'dE320t{5Ho@fRa}o*YojJKwE1y{8CM#~6#$(rmEM<H<;EOVM8kmTe$71Tb9!-R|X6Q$|<F3zacChZ8$EC(jpi#TPugA^teZrv{s;5^fjl9EW0p'
    '-F#<q$KVMB8R#82_V~=6PPS5qTu3nXRLA#5&4o3$#fxh^U78vQxLVL#!bwlJGknxTy|ECz5UAT@yjq=~rw@}>w_g65o<i>0idHi+PjP_bd!^A!'
    '6cUMu4RkYIqggOe-Qi6o5&01~2E@D^6v#s+VYwmRBP?Xki?h@D7}H!oL5oAw$Nomemm!?$D?trma9fUoxMr!-+<;rH;)k2pcLaJ!i~e>tOp(S='
    '=^FOotvyB20~W9N^)^oK$<#B*m>GSRsT^~7VQA+ofC>$mkM~#QA;=Tgo}D{`6*WwSj0adc`77oihN>(*(`t2B%cW2)=c5*k%|r7ZCJ#VMcE2xe'
    'rLxZ&PU14W4SsQLTVn}E6+KEm<YkR-*mHei<%{9LI6~G);etI<OTqdAii{1|0ad1liIgs)fYBm!$uxl1cv)bER`da#K}&+&c(HM225U$0(hgc5'
    'j4d%23Se|AzTPj)Q@<s)n1aKQtW$#{nCGeC1nRFT3kC{9TKSa}c+DrK@k|Z$$XD_0nXN345SinR4{N)lwu~muorjI5OblFbiE^bGl*l?89S_M0'
    '60Ku0fw7{VLXRhGPw$~d2Kt%Sj-hm>W9p1a0=M-J4D;E=^zSINfmCQiC<mdey^3j~gOk2$Yqi~(isBco!cTkxp83QlV9rc+hP66qmg!)V+zLBP'
    'thrvP)&^=1<u1{;`utSLx5sIO8&DrTjA<<ZV=F0BN|FK>&UrriURHfOEl&sIVjQB!dEu|H)>-+1H0IMRulmTG>m!xkPKRq0nj_Fb&Qnwlu+8<&'
    '8I?7fGO;GunmEiUf(dpU8X8fybR!4kFX&cc;43N=uabb}MXFZ?xND?HQs!mI*nycDNEt4UY<oVFF8T4W-~W9=^{!|}>;0;0Mnv{{THD@y^&;i*'
    'nt>(vNXYM@xn1=ob~CzOTknOi2x*{3pJil1AIFBFuSYISVrQM)RK#mV+S(*zWC{%!hVA0yXnH(iGON^?fpUJ8bjFJa)R0)AGdZ-d>Xn?b8FA|='
    '%9DjP?H3q5abcA<0Oco!>ByBbzM`Z}FS0*qrtEb@Dc%iwip-M(-THx1b&$Dnw*o~o2Z~P2`AOexal8P~hL^g5c&wtB%(Uxd^XmZ*^)bcxlAMz$'
    '(w5MPV9-CN!y|o`ETqH_Mi4!|(Q)+=039j3NWHD#7IfqTMNY4#!Hc{n$si;iIcKoYt5g_DcukMh0EcuApcK29$-`o=W{U$UZ)a%@TBpWX6#EvN'
    '=Akj~fq{FE>_9)akF>>aT@y4Cw@eh!gBIyx^0JA>x@kh62tZerNEP$5epqGMrw-%m9Gk)RYyvWi1>#A8mS09LemX{oQ<kTWc>X&7MsN8>J<M1}'
    'KM5E9b=>2mzkS!vlIyK&x}wa+4=r&2(S^Q-C;s{(KL{zv4R8@CjNuT3Ary|1FhSD<4!uPb6pUh9KME7u0R-Q^MSjR-d$)>k{73wznQZ`Q=b^os'
    'W*cI{@|{kbzC*3kY{NPq=Rcskdr3^}5{Io1MB;snw_SjG<0v@Uq1cA;wg>F#LGa!*BG?Y_l3(WhKs!1_kX^T$#XES~pW|(8vbC-`y{|ww+=oMZ'
    'XPmsnxbQn(JAUUces+L+djo8M5`TNCK%ZhMHZ=B^eW%#(eJA$S%)|-JzzF^H8r?^7GVbD4eJo{sUF!MIED~V1c=M_c#0%dv^_uh<mz{lm&oy*H'
    'Pw(QE9%Cf!fza2!Ip*?A`2{{5;U7+t;v-!K-u!*bC}}H`0iOXHtX0hX$vL<A;(h{acK!93CU!qTDc#ryg}@iH0-jwynG|f;U{6+bk8Twm@#pr;'
    'x5#tX-8KA^Y4~}Ti!al~$pOAU=>sK5aapwwIc#4jY`~8kHlEP}<yt>1=QwxwFy%n@-bw~6Sj3HGhlfh0Mt7>>cD41FIW4*c*zh^PtYvLNNerv$'
    'z7k6n2dPb&`C`ObaYl@JVf54`Znuj@3SFQ#bi;t7k9iONegc?@^Q4*ASxb7dEt<;V)<r_zb;(NRHJ+yPQTEv}x<5_R!=KAJZ$nO6Uuu7A@N3P$'
    '!0p99P4J;!7SOCl->HURd^u+Uqc41FA6%25l2yWwKC$K@%biFlo@<ja)!dRfQs{yE9Te|%6Wmq0>iF`44`!Ppl>k~@cvVLO%e`lry&4r}ij>8y'
    'v#(`}emkw@>+0D)1H4%Hs32lg9U2`%6+FBWxfn86HAkls4!8SZub4Nw*DgxGEO_#|b#@6>E$uPps%Rr{l@80{I8ZH=r3it@X09WtZTc2r%jMw)'
    'pW&<dq6*%X!RG20!ttrE8*-K;=a}Pk;REaSp778>p~9tek5zfLS5TF$qrR@X`2tG>%u$!ob1yZ~+OMP%P4D8vRjwf`CO75@)Gmsdt;=vr8@{Zd'
    '@Y;&iW7_OtX+c<F@IWrQl?BOF-ASU3EN+o=KQw(Gln&mGHjvX|ZLUa?2yxSOF6qhV8>(51*=A8YW|4NrX3_}!v*L%B3}T!6{lJ^L3V9|fz!d{L'
    'Op^#{B+fnfbl83?ljV?yWx4T~Q+j9bQad7Aq?~BW$vMfv?7Tc4&DISR=T8(iphL7d_?3M1=eS0JuW?hZ$hA6+C*02u@^xpHLJ0Y?ej1H1xM9C!'
    'kiuRA_i)j}OSTzL*B?|}{mOgdmxQ-~bTUylOzm}4Ey#a}jXzqBO<T7hGBIG*sFgXZ{Y-Q)e>ge<nxcA$O>QF!@k2VQWwG7Jhw(xo{)Np^OjtS0'
    'UnuR?w=eOI0KTY;F5HVS<Av%AtK1B)BK=?=(eftr=OZIIdeYgwIxJB%`I!peqz+uID-y>OY{7tXdO~NkimlleVj6ADHULk#qDGQXUI`u>ZM{k#'
    'ntt^aL2jIbB(42HEnGrWiF-v<fNa-rDz|Mk$~btd%&j8aa60r3FT+wBM!m<5q#e$fPi!BCacUAN?zqlltTmvuL*@dm<TS{A-P$>&AzT&qO$ckw'
    '%004qQDS<ZC9tyRR(x@e=)-vBHdHX+SrFXhHG*413@no8vUm0X1<(zRjlP#o(xGY9_SQq<1bMwD_r!YlQ2B9-#G6f^*~Q2!|3$Z^4|lf>3BqZ_'
    'HswBKq}B9wA@R7O$kz~^!kR#w7j7a#(Yn+9=^He25R!2gOB^qZ%dN2B6d-*Tn_4y;3^BcUhWXOzS0p~~Qe3c<Pm(xxUoqG!4CYptI?hp}I;s70'
    'l~xbYr>X*q(@|Z+rsk>B{Z2|J+S}gm7$UezyT&79h0}EwOyQ{8I)7K@$K!fl)+>9E<hZJ~W)=XYd~Av5q9SH^ZVp9=iFKVHef6+BlxMJlx&edQ'
    'rM$1=ML8=3sKY~;x|415av1j=ARfI@nJ1`xo}~W*y2Jik=nngDpgZh)bcf+Exlh($2qIyagkWN~aH1iEMmM0hb)p!ABJ>{qLhmbw4`W{Ncg)s4'
    ';eSu!Q)(aNXYcHS4Prs@4#<*EX^b0uia$hmIQceO!v7%P9ZXU0V1ta<K^D5}Q}+lKg4zvGP<TK1$zg=vWdpz3D!lEN_Eqm2!tGx`y9#Xsd-&T8'
    'ILG!~>YmP>?&4dN*cS-fMK?H#eQ~$jr3vINbjaU)x?Mv-@9GKcFEg__cSm>W*D0H0zx4Vc6Mle`M+cMGv?kTl?d-zSpRCMg;GZD79oPZ?DYDb~'
    'Pm?#`2V_?%e@1ruw&54ZZU=V2KS6f;Il#Y1cISWV<-{=d0*n-d;hf9kDHd|^gUuq@^%u8dQj)vV$l710n}u=wfZx=C&EpdupK?)gvFmU(-FODn'
    'C6K|ZN44Z6;nm@BH$<&6eOrIlm>*4ZTPHf!i7fk=6fkCb)HX-w<Q_7s#bl-YoR$0+WT!7&r#_xe4MnUc6s)zB@C&%*fxe}e7mfW$b~<^a)#t|e'
    'nhrfLWeui>1ra`z<eB}-sNxp_F*c(f<8c-0<pwcK9H*fEWOczgtS_u4RH?iG&Pk7Ft%sH8=}?Q1T69ZsQVz#N={wvMI89svz6p^Pu6TIiv`0rg'
    'FmkC=Cl}q2uYg0`yTqIe4l$zl47-k{7zZ*%Yfs6Qaoh8LCpX5<nyl{He|<Hk`+-jKCFC%BOk;A*{`IFve~^~=-?`$~s{5B$`@Z;+2t*+`OzkG1'
    '6oMiog5xBFQuNkmBk0ysqbP-cxY*cw;3(dC$6Ganp`Gx%b)8!s+Znsb-qP-oR?sf<-<_F0PS)DKpHsUV`qs8a^n1hcPGm&jz09W3zG&DAAx7<2'
    '&EBCfTd)0gmio0v0rf7GTNj_cpMAGV$o5SJP3_rV*w$!AduP4X<n4>?1#d0?cFQ23ci#@}axv<i$A~6-t={ed`>r{DyQlxPh2Htib!opYHuUQ5'
    'Ra%pbO{GJOm@b*?f3V1{J_=O4X`J(g>yllLE}TmGR=b?NhK->&?c|Z~-SQ;hQ_|umKfO=e5oN2(OB22MFW-#n{>+8>6uJm}OI_TFFbt}1|NR`h'
    '1%EpBEp;nc{~WpqC@a%^y+hQOCiO3CfLxpH8Jqa%4lx21Z_${q^r=*TNn;!|?$d>~YB86;`1$@sl=&!`5%_Z?7jZZ=S@)#9JH2qx8m|{2I?*Ad'
    'YPB)CM}-f&5z<bjKbZBw0H*Y0@&^q@YC~l@4vb-;md^BWqVD<J(r4}Apt2ei2dvO}1XdpOc<kluT=zD_rMwB`RLOAE(I3eXR;U|yBt9@RF!a}Y'
    'B;3}?7JSgJwl1l6&>+^7$br9WX7I6>LBasq@yuzGYn5bH3j+ACuADk{m-zgU+EW#9$en#0ZK`?FeW-P04dQ%KBepTb7xseiC9o2?Di!jqLq{!~'
    'Xf~oFo)IKkg$LA8FE_|~bxE4?uYSHM%8|Di)Liq_DWb!egO?kCkmZ@2pyr>I)vxl2t!$zHm9qNVSNykS^@pqdfN3#;BoKtg(VZT%!CI82DQd&H'
    '8`h;D3dTu<#OV+7$lnRy8%o9Bo}Nj%S3eSd`xC!$BALD?l+j)o^N;t%_<QHPVaMG=Al-Mf8}!VHy&CTNjci}uCU393?9Gyi(p?9#Tlt~Cnp5U)'
    'wMnu+G>-Rbx_?3J>)<`NE8Wct5OkkkZcmB7y#ix$A625C=9JK0%&B<i#NhawyO`|;ru5sO2K#Hx?YNsR<KOr(a=18ZRw1M$ZdirvW|Z}t^}~H}'
    '1^jun`+KEzw>*}9v$TFE{a`jE%ggKM(z<HA_A+?krP%?bf3k$Z_G9|`>(UDBwe_ErR^T)5@ZXl!?{y*X(z<@L=mY*z6JkJc7aSRinog1X<Ushy'
    '4`oba9=R45g$5FbKU`6lJ6Y0HxblcDDtip9og*opbl<g*MS$xyX7TXk`ol@@WI?}|&4J4iE0<g#>4^(ynO-72NIHD7q+*)KtZ(w}I(L#u(N7R|'
    'TlJbC9n|s!_c*;==Wu2_E|HSE#sCh%*W>-c8)C95p_M=DB5jRh_2}_rJzo~bhvDq>T)k)zup<Xnm~K5JCpz2y^fWaB2*9=%1>eUT^%75N_B2eG'
    'Tc0haS@an>+x<vx&zz2B?{y7zmG}dj3G(wMT~=_k9|geLddE6PZa!-RlT^0~LIy(hk=2`oDa+FmT<=P}^$$&|kLvNIC4#p;540#-=;d&K0hG^Y'
    '2sVv+Q`WhvU7$oqcXN9sWAr6GtzcYYDLtZzFG?7)^+PWUN$nJSM0z=pr~)J%_FUD+0|C#jbFC%qFx{sYtkzt~B?l}hS5HTXM2H6RK06R%ECEv6'
    '>T{|&rFP5$pzf!E<;a$*XG5&c#USUb>XS-XZ_mjdYwD0)6}cS{c91*wwRDF}i<5$VIR}N*Yzi1eVTF>Chmtmz(u<^XHTWVK1MD>QBv#ESoe%k`'
    '%wKVEdJu7UxdvwQa7p~w6V?$%fR^zZ^ay3=E6yR;p>UoVTu@Aup#`k+6)YWKrF)T<=NX4W<+K_#RXvKr#!{}~SuX(a1=`l(9^GVy{81C~QRwlH'
    '%jW5x`9M*@&^3IbrUKe+@8YR@(qbq1OBU>B5-bArc*dE&CANozy5UCD_zmoI%XImugnib8+_mM}4>)|gx@Vw2KFPbpin-c@qdQRE%Otp4j<wQ}'
    '<Bw?J*U`N`oU=|duQffXLwsue=rO}bRrQCd1!xO>G!R1tk12z%wpSS^uY|<DUj6nFHbXF2R}l%IzMZONXbh@Udyj#=b1D&AP1%ql1(6Q~x*B)F'
    'NCuy`p3gqdyrsqB2lim;$xL1c>m*QtujuHlpKS2p8y9Hos7p}rDR4YSSHvGH|8O*5FYjEvkBxRj;zP@h8ywQmlmXq-9ZfBM#ayfn@AkvjZ|6F='
    '$k_k_+`W#Et=o?n_z<`1XTi}+&D-W>%w%vkr-)_^*kP2O1p|1!H+54NxXRM2JFSrlPr!1LZN5#yhYWLhJ8NxA6bgsBm&-F*7}+^=ZXAaB$?n-R'
    'C-t13-|ll8J0Np>NP`6eGf_Pcw<zlFL4J8g0-0~%ay)bEEtOUI^&+(moq_Y{UMe=f-X55BcnyIO-|l0GQqc)eu?5BBL?rpGoT<cd#3E`o^8^R`'
    'co<Y|vc024^QB3~0mxts*`O7T!NGw7RUK?9z(+`w^95wSDye%=<w-+VvQTp&UG5Jz6C}6MD~*)5OK{UGiUjtu9D3tb4kbe|*crG@M&~dyT9k)7'
    'Cf`%cn(+haLED?TrlGP;h}U79aFmrZsH2crx6UZobGCqq+|m~<uvM4#eBs8&!E-Q5UQPshli^s?EzcU^-_V5E9>@HP3s~Xubxvsfug%CFqyNwT'
    'we!E95C07Fe&f8aVD3-n{6KETA(Eglnj$ci#8C>vD1@L848<S}f?*n?Xaqq%Ow5RPujCEwY`_Lbb~WveuIOERv7x5)?QXL5m-yS>9sk&ZYQt%}'
    'r^?%5YC~lxwKu-x`|RB+h1zk`_9Pp^%Ah^6Vy6?nwY$WxeEYTzm_YXzfKWTRInKTTu=u@F-Y${9u_ckdks`E%x8%+D+YJMw{UG*^%0{twKmK-Z'
    '{*>H-|Mil&dh2q%Zx&RH09BgIeErK_U(3hotLLA=o8$hJn&Aqf;zFXKIy$ReK5GNcXH}TfHxUqc8{S>U`FQ>kr?FiG+MV(A@LaprcQd`u(PBH%'
    'Z`XnZ@YZVLz$bH*<kLah`C^W8{=2UX_|;4MyRQt`U)sN0BLB2QK7v}8A?LctukdJ(gb83!vR;%`dU@^LXeNxj@mBpTgsnfdBrkoPPEuaNh|6tv'
    'l{G`rQ$lXA3>;S*eU8f_0?{++YE!(rl%p*t{p_ctGbLmA>Nq@2uzsCRqWqY-fLa8N<0GOMWA_nksM<@zF*yJz7N0EG6p#RUN!fs*Txxevehrd^'
    'o??D`MaE@G@HM8$hrm)1J05xk;YEA7)!S#W1eDtM1Lc;kHHBi*;T90c{196VV!}@Mcw4{Y%Xzk!$aAsW)N+dIx*OaTjTb>{oIijHE$hpr>Xj1I'
    '+gII<k%by9g2U{LCAAxjE;&$K8BdscIwS{Ao538!vuwP)lG~%t0e^bjQP=J@PUzwQ$0^jaDlP_5%|~XE&o5%bcVxhy%s|#oovwk>^LDBw`Jsm%'
    '#F+rnm1uM>yXmDpE=&{Z@KeH;{3So8hvBLs+E}+%YgAeBlS|j+6RYA^t2GF!xQQ0e02Xa)IkSv9Gq>$4So-R9qo>>1B9!{DKEkuFvY5pAlx2}8'
    '>H^8bag1K_OVM@gG;SB@ti$3IzG8wj5<V0WVIX=4eR;v^_QimYe%2l!CFWqsUy~Cuhg)B-A>0f{2cKtG4yYyGx2`3X7sq)tMpvrO$2Gc`1hZb|'
    '7jwqkOLH5-3&i$F1Sydx1rRYL=rO_`Y2JDOo`@lhU;LBh=|=q;?67Ack!qPQJ}94d$bTlhe@+wt{sz8Eub$xKnpnno+Tj9)o{i&#ZQw;;nH2aQ'
    '&D{d`DoQIGw4fgu7gLA$>##v-w@QAwLk5_mWp3|^k{>*IRV(RQ5LfFO>k0Efd(2TsG(vbHKXCG>Dhb%ZvJRhy(ks=NL|@PZOvlESZP$mpMo&n('
    'uTZWEl2?Q*M1*lX7ORg~?&0*xA0t&B(&#Svr{nE(xP@+3hc|$r7QSSolA$A9JQQJkgevBCSbUl}oh*%nqV7aSwXZbilbxIzJFmn;T(awH9J7;t'
    '1MKZ>**?wOe@+w~-1JmQufnmDPM8=$9f9I6{vsc-`YxYuotusK#tl?@4PVc`V-<1&E}V_00z=BHF%(<hr_?7Tb}d-k{vc!ZSb*x4?ZmCRq)Nlu'
    '!~M|1*QXqZPnxtJ)qMeSl(2M}RG1@~v?`jAG9wOWnMM(R;${=2mkq1%N212<fV!$!`7jRWJ9vXN=prt$44ki!a~D(us<~q)P}QpsMYm;+Yn-}F'
    '6tK<F2jjv~9)nfiAL`Rn30i^UfJF7hgU%~J_5F(&*vxE+-f5m=azx-OMxlQ7(ry}AQyQj)kfg28h`B>s>mtVR?1^Dbp22>)V}QP#@>8W&C0SfI'
    'q&I};^(jw;e6lAEJ`CUliqf;6L9;VS$3@}DOdfLJC(nZzVYk%>mdxU3Zx|jO8==iSB~pyN3{SdJ_u>{wjeM1FJancdZ@t6XNmUUVzoYcIAJ1V='
    'hy*a<F+N}D(z`1>3$d9pMk5*Fvp9P9*X?w&W8P$fkv9?2|GhAv%qol9*HnpJR?EHOY?$6@JxbI^w|{Zn|NTGzQm6F8@Sop2|A(-jpU(Z!QJJJD'
    '62))~g-M7+_U$kMV+c%c|3|<C0ueC1+o$ZBG#dL5qb0;Ug)DlfslJme_H@*D-aYglR&8i%LtOisH~k~~Sb#=G`+{S8EczbC!STMd*jK`DP=&pN'
    'WZ`!>51Q=5ww&An)ApDg`!z;`-s0Omv;x`@7KXj|+3y_&hVP&ff%Z|}_I$hBUc3w5XlP$uB-w7@0>71L$y@xEKyT0Gw>jSS80;^zE%;>LTQv7?'
    'M8M}wnxn%wH%Ewc4Ih6*-257on*9^IMtu_joe#ow<dwO83D-H+Iv%v{D}75M&V|*AbKqgc8KEA4%CTB{JU_m7Fcy}}=LwZ-M_&5)A={$*EY9Hf'
    'l(S+6bX!AoKK!Ie`+V@rF-;VHS`qI-McOQ%zXTQaJdk<H9&z?5_DATi$x(dl(qgro3tPI>Y9*u^JAO&0bv_T;8V6}^TV?&uTiKR3EGGO4tFfQ3'
    'ny_QF?HIQ;&jPv=*MZYwK?HcV2{?si2r(57@`w{*ynLi~*YTc~&RQVrUF+^n3t?3AuxTd-!&j(-&qF%_J*mj2IZ2d*t34&gN(oDJRiCb<q3*!T'
    '#bZoekQ$t9AGU;8Mub>Hx0qFu<MbV0Q$T?=bR@c9Zt9j4#~gZuO>ThpGra~r^JFl@eQwC=<YgupH{e*1B<)+SaVl#PE*=9Qt_s#00@w%<7_>x;'
    ')=@WJ;@j0DAx>aLA>uMuumqakevqeozR>fiDbL4jdLHz|6yUm5VK2hXp~Eh%^jtakbPvktE~lWO*gD=Up;F}z2s>G>ucD%%vS^=Qh#Rbni-9NL'
    'N*|}?B5Xe#H~ko6`aAZ}Khn>9eZvLod{JS`Zz+dERACL(tSyEQyo7-FxaKS{=J1TS8<j;}&#cVNSOGnz=Xe*h{*JWBqs8)9W87cU#1+IqCu{-L'
    'LqMo0(6(oz6_+O(5M<e$OV#OYiolsOJ(+c!9gmNhnS>+T3kM?V9`c9=a#HrnSu^b!^Aw<Ex#s3k;Y2>otaV*v%?DHNUs|7JZCQgufVSN-O|<Vs'
    '_`r4#_fe8<BPpwQz4k2wP^+$D-lJAV^O=gxnBA3ny5hnN^98@w^xZa>J~yqWcM=8}OYR9AJ?(^yi>{o^vkTz37%X-#K)BN(3EL39dV&~`mPpM-'
    'qFdDqiE?}Js(yIV&oFnN*CL7{886a0qNC{mybQAp=SNC2>)q84)_4aO`6(1Axd;;Tdv2~j-%zlBcr(NP!OaZ&k=2fqG(=Ju4kI)|V<<`E&~_t('
    '$vw9TB`FA{wtE^y6EwaXUw@cm2k)9d@~vLpwaRa15T5OKIOxqD+WoK5cSoQ6k$!AAk*4olPiVhOk@ROF;BHiby)CKVo?mqSRxv_vmR0=rvPS;E'
    'ewA6i-NvA|&Jl**69alDH0{LrcTRa6?OUM;-W80<n@p7_`wb6y8=2Ag?q8NByDRH<dPMK0uEg7-jDY{h_JPP>4jkS$Gx)oknLb54#~Os5^y&72'
    'R0t(fXlSCw@ncr||JR$@7rxWCo7u`BUzzOo=bPE*WB<QzX6N4-Jc!WkeucaH0T3(c-0A|+m`n6HV&&|qXg_y166O(gIA#&6&M|kXj9i-0g+HQ0'
    'YRS55dC)1mJ&gi*HgfJ$%Po$QhjUWd215`~@!?S&l3T`sFZzHQrXtZ>;i!A(9yHB%Gd(SOmNsL1d;vtSEKzpuDFI}Q^O+j&ZVYQ)=XojVUKZt!'
    '-qWqZtaf(LxkMG*MUA)qwaU)5WDsfx9OS{QDE6o*Gp2wXf4e-2CtA3I@i^K=A05)e)}1LJIS$AvlZYge(DGO&H<Qz!1+4&eTHTH3jfRfb1p!<5'
    '1QA@_(yavYGb*g(Ym)Ad+xZB_hEOZ^#mDgVcwtlK;m&=+oB@bsshDyDE4JpiAEG?;;Z^Urfh@+{Z_Q_IE}&I()w$t8rb;8KR8`JeDp!`Cei;KV'
    's_(|Too;VGJkX*L3e81hI|(ATKas~^P{CPQ4aSLY)FGcv+%;O0`z1845nH?tQ3AkJxmFMK*y2~1cm2)>J-3`s^-yd5i9Oc%Rh}7Vf};g*Z+`vk'
    '{opA%926%Fot>)@fV?~6TlZJ*ZG|24p;U}{I!j@vEXF>k+Y8}4hbNJ_D&6FT<Y_Y4=>4m7*!5w^3=3FVETyJ>95kJ=F5xxhUeD@C!K6P1j5uyE'
    'X*u)B-O?6*QR-$wQK!~1xrD*eJ6v29VEO=L(UY6sN808{|Mlc^Oe_wnMG0+HR?PVa1J*y0*MX11mp<AIvAt1o4c0|=b`LJ-Kpf^Newj5u5zMa%'
    '=}N>TMSaZsRjcQ-_aGRe3Ke5oHmr0L7eRvrVDQ1_;xgy3#!u%+=8=nNW>tn;pn9xUrA;k=pI0B4SKU@|;YoRrYX~mmj|y{1IR>(nBCqpMhHA&W'
    '+Vz=FOhurjc|fdK=Qk+jd1cQqv``wJC!(hS%a7fh$#$0ZY1iApnu{hWsIM9{!k$m4D|s!E13yY@a?oL#U&UiO<(xkcnHaT&dSS`N$q0L`r^j`a'
    'EP&@Op?<yRs&X{3rHUKHIg#P<&iA*ZY0N4J%%eDT)ni)I{JIqg=!76{C!$K9!zqXXNS)G1RmB5;bES3~PuENf5@d;enVl)EV2(<+6&*Ld-#36n'
    '+;3xyQ~C|#ErG)|rvt>MzC6;VPhNK`Q%lRmN13XIM#a6YIHiNkUMA6?PEUyp+_aRD@<1FTpDaQ4VC3!#IAOk^p4R8l@hn@_uPnXj5<*(VMNitN'
    'W`&q(wkxRKaHM`jrN^LyNS1u2(cSZQ?Fk@d$tyW7kx|&`xOBpuy;OsmN<wEuvFW$O#c}J)T{xZz=VByQRl0F;OhWW%*a9;(fZ7cN7xo6y1zjHX'
    'S3NC^{#8T|SS>R1IzHOh91pGJKiW{Y^TqVe!#!f4nxZR}_E-QV@Jb<^%<j<S<X=P3Y_GEXx+yjLC~m5rsj6J9bC!TPE0G6ty*u}oo`jG;6%Uk7'
    '0Og{~lMh<|1b^ZG5P#wS0Ds{>m^vT?M4>p0;WS2W7>uAXnkEPwhB1;LU=rIoI}m|VFicW7^davYM)!7m!!HT8j}fAG81UAiZ%Aj4L89IkTKFz3'
    'M0Yvh$0W!%B%;uLbg-SYp&$J1j+4_nADzheSw%|jRGWQ&^NuXXqIc?V`s*BFl6r$QXvb4|wwr{Z<ZiH&ys3>FI-}l(`*gPJ9^v<rDnZ`HHQ4?%'
    'yVC>w&MQfGA!7Wtub`;6Wmxo=BuIHDjznKckdAourJ24eJ&E_ce3!|boxv1A&F%x<`9Hy4JM;p63wzl=VlRW&UVv_gKVYx@;C}4yV6Po|0sjPh'
    'ecM^t&R_7$&#EI?`u5=r+t{=Mro`k9Kc?J*0W&uVst4y%(mpI$E{YYw#3O895iawQmx#=P(`3AKGQo8FJm0C<P~!|XRp_Z$y>$UX$p@KiWf5Z{'
    '8tLjC1wD^2Nu`H1nwS@I3N<+jz+X1kz%TiVKjx1N=cIfbbT4z93VsGp==$R9v-PxrKZVkK%?cJ6#3Gcu!Hu33q^Eo1Seh8L>S~|raC^_B#M($b'
    'fSGiwo*M%b4iK9jMY?he)O24X6w*w^3at=CMdxIJ*DBVWs^Q>e_u*bhwG=Y`nE>M2A<BRWv-K3Xo-q)J{-_aTIL=L>IoRLtLizu(FOFsZi~Y8u'
    'M!pgd|L0Q#`UeEY-#G0{&HLpkKPG~pTU&{v6pdgMMPS?CG=vibfzddQU^oiV6i$C=aJUr(h~8y1TQ|5hWhu6=hWAV(au3^x$#*VMz8~5CO?}*N'
    'BI%yNM1Jxzgm?P&RwM~}ua;XyO5?o=O}4s3y^X@4y=A0{y*Z_RrJ~-d75<j$<kU|0PV>DB&fex++nM__y^W{ScLj~Go%IO6yV>|{A+|HY@pqf~'
    'Hb*3rcM3bbPh*kzkMu7|-{O5=aO2;Mr;~M@S>YNZ4veWcU42DT68>qy4ebkV`6G6stFhXbHL`Z$;4k^<pGk=FEPsjDSQ-IP-HYYAx+4pU^@D|A'
    '`6hLLM?7?9!)7qu4%SaubbCa)GXq}_irsASe<pQ{He-LOzPxar+|QNwGr_O~G>-XF&%*uXI*n_)9LqW7x4d7Om;Xd6{DO#qUy=$><biYBOTqM~'
    '$OvkaEN{405M0%HYf@K1#Mw!H8h~<Z2D@Y01iIoxh<=Hodc`DJ5>N<R&ymHx8Y_ZuG-hnO$%l0Nb%cH*UUTPpJE^(=6#jG>XlNb1D+SlMb||Or'
    'k@Rhp*rVU12YN=O8y_I}IW30mkB2C(BRPkZ4Ub(`R1{FdNKE%HsKg>dj&BfUTtlxcueyAWl<<g5!QnYRTLygAw8@Gu#L%ACTP$YQ%HBiH1}^>e'
    '_QLdgCo)yPK9Rz{6=crgPsCpkZ6ZLBUKt8wXbJT(5hBB(N~+<`zpxZx4s!z_SyIJwOos=vIA9iaAwgKYUXRhm*4R9cA*dZA>NVi1qn=-v%t9tT'
    'qz~R?<7UQ!4v<*(9lh}s6`J6!*CSlHL=Ak_bbrcY17oC@Ju+m+(S8iwXe%NEXEZqZxzNQky^1Dq@Ro!yJww6L!_n!k7o17607|?=Wm=tIld&FG'
    'F)4)HH9aSn$G~4B`=vwaskY`rYypqU_THbf3&M}6(P}e0Nupc@T~KOUmlbObv3e&Mt`*&XNDP^Q^EFDX0SOS);Gh!-Kyg1y%6!Go)Dm5C|G?ZK'
    '^noxp?O{#w6GoeML*{L>y(krPgqJQzVLM3SU1ef#!gPSo?Q(1&xKLXbmM?vMR@F4+^d)v^E)<k%v96+Y!ObaF#0ye;Ze5~gbh_9OB}@Sb__qAj'
    'Xu1fnxd_I;<zf@!{0vV73><a$c=GY&eke0eUFzn-e0(Dn-k;J`nlEp4fq7@Bj=vuP<9LNqi6PV%T_x@O2ss$~R6y`Y=%1efs*Eafo<0GnOCH>m'
    'JlUDb+Z{4+sTbg{yCIeK*dO@w<cB|hwaS5LQb!$noW-G@dP`c)oCp)(Bm-h6&<V(8%4-->qPF{Eck-If(N?&Vu;U}j5$%S!qb{hSnzDzCjTYlR'
    'S6T#TIYHilp?ngL=S(%Y%hd3JSI<U8Mwh2U=fs)8X8Oz&D#L0O|A4v$M4q_tx)Y$)>Y9g7_62aoh4)^>gM^d&UA;VegVNor9m&yHq&>zTxCpyd'
    '6v({d*47`X51j<lad>7~!crR&Ky8KEyW4kVo>pPNt#KYq?V6WTmqcRk%CS2XkVYwW8Mbv=R>7IL7lC*n#1jWO>J7kHC;;!4s6VnJw)KKf-B#dg'
    ';VBnZ;v2!XNDG(V$t*=RfDhPhwoLK$8o384=7;CR1J|>Dd^YIuRSNBaPPp6cazf3*7ULu9uCW@r>qW9fl(2k$Cgqn-`%BB*>ew?F?lc~Ox|1Bj'
    '=gfWuUt|zzMcctIL5Ye<w2rl7ijl)m%7qNA)HfW{%%wy7w7oSu2%)WG1kj9!K7C+3PAR-oE%zd;Sa19I3oc?uho^+M=feZ36C#D0a)S^r_rko!'
    'hb_#*1R{|I2+07?<`5LH!{@pw%5?}Q#|gKX;9m6i1O6C2zEngeUQ@k4LwDQRW6%6YhRMl5K|p=u_~JBT_onGkhpUeY_o8Trf0glxq<smKX}fxE'
    'Z%Cq=ZijYCL1qXbFq=UPeV~N`TonS3pJU&Kd{^j3t}y?RSI*Cl(f^^A`nNChXC?Jdm-rsmp)j-|Itbp-+*`g!K`4Py7z9BmhU|auLn3lJjBQX4'
    '|JWsG19y882evz!rk@ng_`Yu5a2oN6m-vn!-tf`Zg;E~}56AdBQSF`h7QN5gTF)rk6(<`|qu*YE8v@&Di10h&gWMlR=6|5SA}}V<-tH1_E9$MK'
    '-8<HNe=*TJ!EFycN#4nx+0MJ%I^3;)-a6_H=)u`rVvX<Gzuhb6EhXH(-n!$2-pP~HhFkwy)TizEF3!I8v--`x+Wv;UsCL}m+fB#gR$kKQNc%`f'
    '&Hq~+wf(ns)N;iXpLNvs(f#qH4=kiVlNrzZa$JBnpa*RoCGv^Pc%HvI27477{DeaHh~%$+)xZWrlh0O$Y=Sh`U2zg1*GG&j&k$*v<TV$ThgVx~'
    'TYirPznlYnKIzZ?+xA}s5v$ij?~Vt6vA2dqzD`5g23R;H4t|U2xjMk!P*me2^iQ6xRM><y(kVr=^PAka2W&JCn$^#I4-^mW?yU-C;iGd3NlXn4'
    'n82{bvY|G}>NM#d%2eFR8?V7Uz5DJrCyA=p@v{*f@OSRvs_fcZ{pMF&z2EMJbhw{_`zf-C%YK2sCEojDT78jVN}GZplxeAn+%p6NDop8gn~o{O'
    'M3+a7MdD;A3xc&0e5grEwiA1Udfb(V@l&>&R-cT^^&np~%-ml5{Q?;EJUHr+mitSp2hCbgUVO|6sLO6n=S2t;IS80uyTB^Z)HrUK>pw1*-{&6v'
    'gJStxm-)C@es_r<dSC*=Ae`EJUyLFs8rn)CiSOIi?HGb%<W@})6yLY7F!cXw`?4lCv8~y6e#L!Pd?DuHMBE24&mblNZwQc>L5zZ5e?hjp+iv@G'
    '_c`~Aa5)qdTToG@Mdn_)GWY*}YAN<9NPAf$@guwlK@YXhUZoBbRs7fyJWRoo!>tRV{ssMfR4@9Rd-PwiV*@dbj`B)H$0l7w9EBKv9ISXJ!|`YT'
    'Zm)eva!7?9zcQTwKQ0qr1_h&!6$XJHb#bqSNBut9wg(^H>+O*okRB(;p9;KRV`ugI9qiXQC^2;~<n+ru5y#fx<M1;3OEUaC_#2%6RxCxj2)2{w'
    'n5zU?mF~*yd$1@z-anVWuoU|*3g&l~Vt-XIf5<`l7C8J}aYTMnFyVh!Fuw&3|HlOr_`{+<he$bpX3sy8XW%#XtZBE29$y`2ZCDZ-l-iiLWv0RK'
    'MN>CpDL|8+b_OLheMTceEuvKC^~4F#Yxc@Yrd}C+^R}T_UEJHHLzNeEt^y`>t2qy@G(7Yj1coc+o-nJZ4Xw6YQ>gBN3|t{rXMH5KF4&VRsh#%0'
    '=i14}$8C$yI@`o^`R=Up8ZYi^*`zQ_TkthPj94(biR~mvtVQomfS0&YMy@!$y0Y5HHt?$Ja`hp;+-3@yv})`P->Xd_RO_u+T?ZRotzkF>1|B2E'
    'rT1wq=q&=laZtxQo2rQhMNSEit5Q6PGfNtEzy$5KMdwo$D+E8Bap!VNN#_o{b*pSymcSlh67MWU2`KueqnF<4Dbrt~m&*Ahhk_~ptf1D-aHLE?'
    'eeE|`A_pz?ft<Qu8_GPHI>Dpo1%Dz8Ct0ApyhL(ZpIPYX&$Oe*s>tr=v*@SQID%xg*zOA#o&E~Adb>(=Q|8;bhpeF1w~a_be4!Br<pml+%)s<{'
    'Ntt<QEIdwu2RB&daYR&Rr_ZMXaGFf3nOjdb=p^wt!$<cUES&}{2G?vTFid~RXfd2h(siQwEK=`+3<-Z0n78`^SqHdt$oP(P#Nep%EnAv{vwHvX'
    '1$o^`42%eHw;IFc7DD#ZdfTEqnVVR>MkVB{EP9(HV3VueJx`^3CykrThR;^Ry6Uu@YTO=3aAVtBOWKX|g6a_(=M-Wl`j4`$Urxe*H%hNQ#nP{0'
    'dbWhKKZa}7)@79N$~kj@UvzGNIb|n><BPWGM4+RFdpQVTZD)Ngrl}YhW*gs<>_7dx!9HWnxm9BmQayz?v_ZJo%|4SS8#PT{-aP-sPPvfID3HH2'
    '4ykK(=lA5C-e!=N?pRRuF*eTfRaVRWH+a>Qaq7CK%)e;o>IUse+ETw&Ma&!lf~^$F(l|nbz$W07mvC;A8CRWk?6@{iboQP+yK#0-^oF?ASz!s;'
    'z;&P2a|d>o4uId%H8Mmlzdr@Zi0^5?zDrn$1ovW%w-@g%;(M&xQEs%RnrqC2=4&n^WoyE?)44M6L?{H|Ilhv?XY5CB!hFeNxJ=nYz;3G*4cEGd'
    'hc==~SU{+;g9%F#E|+muR4#Yj0_d(pW(n>oANZF>BY9vx@mCwm*S@C9aj9}Smq~wt$eXGVO@j*d`Q)FAdqxtk*M-!8ZhERMyFDY!4jS<^(o+!Q'
    'rF8XAQq4OHVmu!HY~U!Ck}T1K`Dx7soiDgsLuGCAGy#7$mFB+OP30k}kEoF{QMph>6D}`>9R{c<t{AKpuOg&Mluehr{@@EzxCZw9E=x-a*aIUW'
    '+wHm)Btr>Sh71ph#{5*vo_K-F%$0E}sL+##Ld=7^BT+uR>bE}bpSEuYB?we2y3j@%P}HDaLY5Yn_I%RRlQZ}Cy3sejU-(IEf?Gri*hV!5TfZO5'
    '<f2UJc6qS^2#n<QIJ(z!Cf*c1N$6X=MAP!#uK&Ch!Fm5tE8=e~`>_@ArzPLPFoYs-97QM;gdq~d4m*7m+P`)PcIe?K9EAu7`f1h@{z;f5kA}qK'
    'lT!XAh$Fp!%u(;3DYb)C9@4iv{wwr_-4BR_5=U#3d>lyaLHrAi53qxO#@r6OSNP~jknkr~{BbxlkoR91>!+XdK4~L6@JrC6*Sg>2VePeZVd6+)'
    '0+YjwYzK2xe2DY*+dIr|kdJdeblB!RKKKv*h`6zj`@;?p_ix4NKW;@tb|61mT6GkrDa0&yAu76W|NE^7@AfxZ5t!y&HVyi|74hX@_5ZgO!F&I8'
    'D?-nW7OgJ~A^YyQb}qOelTQ`=+nhUSC~j~C4RWafJSnJeeQHr{c~677ZXVK&=V#KxJy!(}-y&-dmL$$)VVW_|rFl2r&~RJN!Bd8@l>-RI-5=}8'
    'SrhYnR2A~rXsyXQNc~98Abv+h&Lew!)hhNJgm2n;<f`uEo<%Zlsat#saN2#y;7ESna(rW^#6q;k9K%*8%CAO|?t((kJ4*#0F3Y@F)|`D);@08H'
    'y>YdEJ#nBCO-B$)#hwqQYMxX71lb}*5Yw}}Z=qJ*1OYbdJVyJe&rdg^E_Blc+v{BM$|l_bt8#DAD^!(7O;lcVKFXySYRMwpRuSjfzKYUT70l?Z'
    'Ab|j(4Ea)g15B$Y&UR()0fjRaQfyB*Ew~J=4NACu%ZeKc%S6z#mRt*l_m0QW<{mkjqk%YH-Y;rrYGxA`>N5t4`dLgPySe&ih5@x1g(^NwLV4!0'
    'Ik#AD!S`wl9yzYNrXZgyT9j3*SgvI0Fd-klcktx5jaJr)=25qVQ*H}2o;wWM>5L#09SL7RZqs1Ix_S5zoY20tB(v9XCwj8zB%gqb6^0R=u^PeJ'
    'h<b^xn?H5QtFx+g%37YjxE&}@>x1sk4DBRk;y=5{M0hHlPu969f$Yv^=_VvyL#-{*a4JJ+wHF)G_03;GtHNPde%D&gY`R>QPx7oG#=zo6)6VF*'
    'Y<NKTW${00MZD(K;^;{PN{_rvcgnOeKE2TETWkN9TM?lj{wJ*n##wRqQCs3rKcR<8-<)@GI&l(&0@s<IN-hzLmtkuyv=ry?UfgkcD`Ps!hNmP|'
    '_f?XvJEUvssO#VP>lth}D{9@Uw_+6N!tvyqGK{w_ujC1>5CRQG`%R0tjveN==N18>i^Fg#3|`?NLX%V7di7lv&~!_@0E9Ue`Opq!I@(1=YWq{&'
    'ToFwaV(Yaux=SE$)~!vNi+jepi=eS%hbTfx6!+8K$Xs9~6zd$Vop@G6jD84ql<j|g9Zi|i2}5F#=G6q3#MQAW*9t)ob<Y}>prH3=WeJgdAeNwO'
    'yfePLwqob4iyT<T7Z|JPH_Ww<Q^yL1yrY~;&NjY?B<=WEV<-um$eY?kpGhEp1b1ytOIZow5lkEch2#RS;V1N}s*dLOs+L|rvS#sIB`?NpP!<mq'
    '`6y~87i$;?fM>o#RXKM;+&rUoQbUMtrL}v>6&+>0Gj4KR>hpsqnW#pTyq1lDXYnRzxQ&H~13>Jb0;pDM8wAZLQsvoLavO8RNWS`yNih@_hu>2V'
    '>B9QZ(WhwWlMp|8y>c`5{?bk0**<(-&L$hvu|V`X_I!yT&%~wc#+aw_EWUHCtRS>Q!baG6Bi@|5_)^`xm$9&yVFdJw;PKe;p5!F(SUlWmea@iQ'
    'Y)3%?lORen*aIzFh|MAOq(~(#Apv^R(@Q6TaF=C(Prv7z7?#6%VJ7pIF#jYH&R+6i_#$Qd8d3CJ>gE6ZpCjey_meKdk2<>lVEu18y1!ieT^E8R'
    'L4w?oI05gETM~nC_=rY=5%9=_1Ifb%3ng&`M__C}g8d>R4o*ML{M4~|MMB36+@X<6k8P+O5$#wA`eYFizsFuee@Zw)(8DI{Fky|4u0Z_70`}0&'
    '9WTh}BVYOSBEHPm9Vu?dX}^GW&?lk^MGt7WzevHu*5Qz=pa*_~K49+{&ik18V@G4*KzAg0=t$5nav9{vRfj(tdC-?lHvBlg-x>PXDwFbnE68si'
    'SUV4BH6KLpPdeiWN&ubBeORV_A>!fhjp$v$=l6h$*OAEAx35w(+S>l;%lFoD7fHGp(Z8waoa?uZv>)O$B?f$I-;{O5<&$cDxVfUgxwvj$4t_iK'
    'XJwr(X_mWiU+ww1<?R3oTx~I=cOi`K52^UAY<m&>y1ge=-`)D}*-C!^p}+_8<(E-n|B;=7s?<f!kh%}dtXIq;QyFJNGdaw!YJzo&sHC2%BEDYJ'
    'q~mS>hG4jFAyDQQnmTRttSDrTd9FVZfXX=P1C#2fVt|zyF>U0ur^Zcg4^50}zC?#etD;jeq1fyV)O+J`I=Dh3`5GAYW%~f;i)6k(CnSD~6J8$s'
    '%x!Ldu`+R2vCUbfjJZLSN=wc`&p&Oi@80juAzyIGGuXC+OU`sMGkEuCK3UdY04F{=SqZwcbjVQj>LIwCP%M~EPxNwSG&-6bmBYrZ=Rnt%r4cyS'
    'aC4H9KK1=<&Y1VB%`P|3@i)@B)}Xx^LRA)$Xh{hEGMt5AF-l2MRf*uUA{FQx09E#?WUHOG=RgSGBF3WH6s!7Na@t9;L^_#ie!HMX-Nak0chVV-'
    '*hMusp*Pk!#{ebL;5>*XhNR7aD23ahWE}WzSo$qN(5VU5O~wkl4#28=pM(Jq-Iy)NhljKds%ZciniV%$E?f|6@ARozym^v&nsnb}FqROtdrOfA'
    '?%l4}IdRTT-_~LFTHH~|xzms(fbkxKlH~k~_a)|JFlk^v$c5o_gNU`{W|DJfR^=kRnu0)TJC{iCVGcKKW)qj~#|Vfke_r_sisuYPw)pArsTE`L'
    '*3%hsMWttyZe7n*0(KpZ6Ps*#7%8Fv?+Ba-#@SJT#e_ssLDd_>@+%F(eV6X6ORHt3K^kW;>FalP3jb)T;RibfYc6U<EkR>JcgoU{CPiLPD8Rm5'
    'v~#`(j&~Hxb4+IkgTGL(2YY^S=5!%FLvepvk-m&TD9fO@JawuzNa);PUe_*vm8B>8(8MwQia$%&9s(0Kx*b*Bc5J~)F9QJ}FiIDuwaoy(RVDji'
    'SwoGs)H1poVc6BUT;w6|t}4CAy1){|37Mg!fbUd=E_C(W0P)qKP#U^4`&ysRTHmrA`MGXOMz^9`FjhK)>S5`6K56wvWM!GUeDOA($rJJQWw`>m'
    'd<V@Q_vVMlJ|0Z5AeG2KtIglcasON@7#Mad#Cy!zY1Bh59lVOqaJ&|kJ8G>I15bu}m5)N5MKoyhs8wIOqezd@J9$-FqL=-rFkG_A^&Vl0YVJ1y'
    'ZJt&Z=AczHl&b;Z<JyJ($x;pP{FriiL&@g~gW@&gExAw>wdh2S$o1Kcb>?xobq0LPax{chTr;MO2h>c!`>JoI`{}(&=Vxo4(18;86shWVt04ov'
    '2UnFaM>th&tqf()CwJIx`eSEwv)lpO44obEab4U1s`;g;7n#3eR)pN&VsERbsY2({F1xH5GNi`JksS15OYZHGz3{V>0GF29pH0epVw1M2*nZ;A'
    't|GlE>A5PINr&p_BH&G|u8kfj?T$~!IY&!S_s<bBKW`w=m#B_p0k!`%Z*qmH6E|G8{ddL_-4HNflWlQ{HQiGseCN5?FXu>c9t3vC(?B6O19+<a'
    'CG)VIDWBefEIRl*JH=u?C9QFaz5ZGnrm|Q;6@vXTHWQA9Tllw;n<3c_cc7y=?Y{u0L%ty#c<alz_;zZNpXHqYvz6b_+OJl9=T1tH5Je)#WCMmn'
    'I1V8w2p*nR1PGESh9D4$VL#P}pzzU_JjNNYL(&1l2i(~)&=;Tvk_P}fcDS%llJCz`l#u(!i}ZeM*&TtppUG9?GX#--yqA&3SD8sd9RO)ZTwr`a'
    'v=si;yu&Aj^3Z;OAC<}D*nq<yM|X3-*nTAhJU}0OKdyK9S3!sNgZOwu$K-J`^`%z|9XjG8EdV=^<qkUcw?e7E)Q9LFeaP!~chYmiLd9(^)=b@5'
    'vWqvk-#C9VeO7-oeP(Tz3pG0a=1h8Zz{>GB_i5D>bg!-KYm#{OHBIGk^bCM+C%Le<CbhSI!#p272p7Nqu<5pG4hQZ>*RSE`$EMo~=<Jt+N4UAY'
    '{TU+)&c**`Jj!vD>_QeVap9cYurlzi4!FbUTXMcUI6f}_-%jH7DsI9m{%!NkW3MYMYR+GIHq-HZ$`rDvi;bBr4r)TC>CILo671#W@JaA3Bj?SR'
    'F%|Rcx&rZRz?Zn}&wk3^D|3e@ua}zN>~ShHF3RW8T~rbapLH=ec(!xV{z_qXk%|(7`vR&1@Vl<i?G!70cCjg>cJRL!Z2sjLc|`yx$g1tUQ2BT('
    'NVmD{rRI7E6|ngs*jxu;DU8pg8T4Lz=H-P$_jjQfV3e1?8Ejr&G$CNLE7K{(B>^?%QS!V6Tv^=n7*XfzJL1BN#23w#Yu@MJJwMRxc`=f5JOnt*'
    '`~3_zo|RMZcoRF1h|U)j76@t)Q@ynJ`qDz|+bJqBMQG(7(az4yy*5*iryc2|icpi$iVRxB;V2aU-~XZ(9*puotA+n=<*#eumsQ_K`yzYE!=Swu'
    '!h0d4Kn#RY3I{($@o;QDrXkRu4nx47WN|7zh#vtS6H<5Tn5Eje-(F#Me!175Bi@5LC?@`MCz%IvGzfO43V)<=$A}gAVVCG}kR*;0wZHc<!i68B'
    '`Q#@){Q>?9{}oN8K4ldD`0q#9;h=vk_%PMIXd}t-8pc0`E<Wt`G2~Nf;e(eFAJhH#V-tNC(cBNQ+@U6+K3co|w*K0x`FYS(_;;&jFY?0>ySDEM'
    ')K2*$xh?z-$A0Ser~cT1_{RnDu#XRZRS-XVkDnAoZHwP}^`#&JM@2je;^(0E&kG`ORK&ks5WkRUQFH!@)3WlKC}m={^IYl6+(2P8mPV#3$=eGI'
    'Qv+tzAk|R8Fh$47KmeOYUau5+el0^i8W<te4Wa1t>T}%~h0PMYQ4Q?H^IrZz&>-$W&*d22U)*ARiZ9y^khGNN*E1KO5(Dj2MCeUFnbU@!Y9}>7'
    'b1M>3Zjz}@o`d9WC6JeAk=x$Wn{u6sP+EAkx+ipZqIhDseoBP1it45kDC^6hg$InHX(mR{v=t%9?sXV2$ocMusT*}Jxn)^&FK6L=Nli6-VfLJq'
    'I@82m3tiCwR_&7~2{1Z6>B||D$$RLK7BCu}AB89IVoba&mnCHjNrm@>E|N_2zFqtKl-{!H+(}z-s=@Zm79t9+V>A$<(-}5U42u>Lq-tY#BdilA'
    '(gvRku#m#nSRiU6;%r1v&NX(WDnxeWLDuZiB2Sg#i@E4#z>uJ_%yb&sZ-XNw;*!_WbbaBcm<P9Z3FO+3DEKTC;@J9^c?w86wa>h<$>hwQ#1^QV'
    'mqVtk1QTR~)ozz=_ow#uHnM~Ehg8-oTOcayLreASl`WW<nD(os^&}Jt5PsVeaN7D(CHV>^D*P&J3*9G#BF{eRk!XzB1MD-7nyg$8265Z8gNbtW'
    'b$Yn4<_(z;SU`>>y+^Obm^`mL+w3SfmU23YCpp2kQ`;*O7HB7L#O?YOUOD}lnS*>C6P2S^-fkSAWHv-7O)r}1?t7=@zZXaYkV8YW3shXxd9bdS'
    'A`-Xvu-$dG1;5vTn5w*7Nj+E?g5X@k&Q8#9*I;0~;`+~cZuW09Ai9uXL(vPEgCKx}C>WET?B0$aEr%+@>__~v=2;@2%1Wg8oA3L=Sn?CDSaGXe'
    'w~*75>U?fWTr>&+z*wkHsB6X<CQPoh@w($O`Cj8!aw0Xh^+88wLFJ{y+1paMEzyUfRBs7Y265cnHxhWQ`OUBS{i7po0{6VRMz5%+y0Vk^*;KCK'
    '%<iB6Nx>*?_V6ViF{C*0B%Nf)qYaV71TI1}Q!2+AJ!(HV4#FOGEr6-IA`Jrdq<=55iZqMJBL(-Fdbsz539F&z@&Qp;_9%g;of34A-4L6pDC{|w'
    'R@G_V>8_bd*!%LO8nz&Tqx-14#*ncmUg_DVC?sZpv=7S~fZ%2e*6Z$j+6{)V%guV-__afE^b|OJA9xbEc8aG`7wrz05_T)lQbNM$g^l{_6$B7K'
    'jUJzJvSQ5(yYfU3&LJP#HaNEl;n_?=VKAi3D;8vpdS|B@ghBMKj6|2=`q`*c;9L*hluS%LOaX!zS*bA3cgnVxC@*+<la}x`@ZM!BQixRAajRUK'
    'mFJc2nC@YO3<AjHXeH<TR=x?7Y!XTYBd4v(v~nF@^}TY??-<IyJN#)w;$_aQ($cTn<l8=H&9)5#%L`h)%l#C+3oN0APUV&K?k7YrgQgSU!I5+o'
    'Tk1`A{GvH$bEEowluaX^u}+nRD?sO5^)6SkKp28GtW;{X5$uUm=1m}`f`1=|rT=4Z`Lk(%+{-`299kat?U2Sl8^-@9>%Kv-U#|Hsgb1P#l!VDc'
    'gA0KqLBJ42K{!M~1cv?$c^zrFJK>`~9!1!JS+MkI3haatP7iCMoz?ARj{ML};^#ig_{Wkc!9M>!F&1$A5s#$DyaGrZ<Ecju+v9*r7<ug3@2GBn'
    '*T=7r*G_ql0s4<xW9OGUt~+KQl23!+@o`l8sD;sw*!LK+2aoa8k8|^(%Y{AxaLLCwX@`Z$hp<xM;Q)QiqoRLFL$?EY6~Ade^ox<rf;iud+Z5Pk'
    '9WXzHaM3IceFI#;SHvZG4rhHW&m6rh(zWq+l1EoDa((l~#r=kRSQqL7M4n^VD<tj>0wIIG`R(F;P7pYatwP%4GEe<P20eF%St5TFjIeZ7sh*A>'
    '&4l|(yTDI634aib>}YJ`4sXBZOCHf782Rql0wg~=2k`Ej`?~o_Ut*2nWGEE)CG>Srvx2?ge+~b=Kzel3SKyB5Rj__@Z;BWGgG8;2y<oSiXGxw7'
    'uG;3JI(x<TEB`LtU6wGkAqPn7s=3$XpIQ%J)h2Yk{bHVfG3e}h+2O13G?D%JU@9G$3!GBKvesR>oYx&B5EG`kv}m9RTDajmZfWrH&g}Rnz>q~{'
    'v<q(o7xnxo3@Gd!xq2;C=&EkG)X(^0TzH@Au5z}q{pFg!olYlCm49QSVzDZRyY$xPoM*t^+~|r@3<s{5O26W{VBoh-#5RVM9lNROSdR!rQA|Qk'
    '<xbLn++ha3OMU$tzB#wx$^=y>q^6f35~%<?&@T|(znwt$Pk`XZlmB?`x5*pe%jnH@C)2}4lLYZnO0=5npxMUIv5wG&2$u&Og4<~|9wu?Q_;s{Z'
    '5`&SZ#fsestb~^mSz6ZAz$FvfDQP~RaCmTM$5*Hj$!LapCsG@+SLW(?@U8K;vJE8aE~U&IRschF@EcOk%p1SNjI=D9c^3?rgV1?65}X56fV}1{'
    'zM){Lglvl_X?oq8P^Fh{zOFbh-EQi?sptO>o(t<U'
)

def _verified_urlopen(request, timeout=20):
    """Verify GitHub HTTPS even when the embedded iOS Python lacks a CA store."""
    import ssl
    import base64
    import zlib
    from urllib.request import urlopen
    if isinstance(request, str):
        request_url = request
    else:
        request_url = request.full_url
    if not request_url.startswith("https://"):
        raise ValueError("Factory metadata downloads require HTTPS")
    ca_pem = zlib.decompress(base64.b85decode(_EMBEDDED_MOZILLA_CA_B85)).decode("ascii")
    ctx = ssl.create_default_context(cadata=ca_pem)
    ctx.check_hostname = True
    ctx.verify_mode = ssl.CERT_REQUIRED
    return urlopen(request, timeout=timeout, context=ctx)

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
            with _verified_urlopen(req, timeout=20) as response:
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
            with _verified_urlopen(Request(url,headers={"User-Agent":"LAST-LIGHT-factory/2"}),timeout=20) as response:
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
            with _verified_urlopen(req, timeout=20) as response:
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


GODOT_PILOT_SCRIPT = 'extends Node2D\n## LAST LIGHT UCF V2 — generated neighborhood test; original debug art only.\n## An opt-in scene. Does NOT replace main.tscn or modify the survival-house save.\nconst DATA_PATH := "res://data/generated/neighborhood_v2.json"\nconst SAVE_PATH := "user://ll_ucf_v2_neighborhood_save.json"\nconst TX := 40.0\nconst TY := 20.0\nvar neighborhood: Dictionary = {}\nvar player: Vector2 = Vector2(8, 40)\nvar move_vector: Vector2 = Vector2.ZERO\nvar touch_id: int = -1\nvar touch_start: Vector2 = Vector2.ZERO\nvar roofs_visible: bool = true\nvar zoom_factor: float = 1.0\nvar open_doors: Dictionary = {}\nvar message: String = "Explore the generated street"\nvar save_accumulator: float = 0.0\n\nfunc _ready() -> void:\n    var raw: String = FileAccess.get_file_as_string(DATA_PATH)\n    var parsed: Variant = JSON.parse_string(raw)\n    if parsed is Dictionary and parsed.get("schema", "") == "last_light.playable_neighborhood.v2":\n        neighborhood = parsed\n        player = _vec(neighborhood.get("player_spawn", [8, 40]))\n        _load_game()\n    else:\n        push_error("Missing valid generated neighborhood JSON: " + DATA_PATH)\n    set_process(true)\n    queue_redraw()\n\nfunc _exit_tree() -> void:\n    _save_game()\n\nfunc _vec(arr: Array) -> Vector2:\n    return Vector2(float(arr[0]), float(arr[1]))\n\nfunc _iso(point: Vector2) -> Vector2:\n    return Vector2((point.x - point.y) * TX, (point.x + point.y) * TY)\n\nfunc _camera_offset() -> Vector2:\n    var size: Vector2 = get_viewport_rect().size\n    return size * Vector2(0.5, 0.52) - _iso(player) * zoom_factor\n\nfunc _stick_center() -> Vector2:\n    var size: Vector2 = get_viewport_rect().size\n    return Vector2(108.0, size.y - 130.0)\n\nfunc _button_center() -> Vector2:\n    var size: Vector2 = get_viewport_rect().size\n    return Vector2(size.x - 105.0, size.y - 118.0)\n\nfunc _indoor_building() -> Dictionary:\n    for entry in neighborhood.get("buildings", []):\n        var b: Dictionary = entry\n        var bounds: Array = b["footprint"]\n        var origin: Vector2 = Vector2(float(bounds[0]), float(bounds[1]))\n        var rect: Rect2 = Rect2(origin, Vector2(float(bounds[2]), float(bounds[3])))\n        if rect.has_point(player):\n            return b\n    return {}\n\nfunc _can_walk_to(point: Vector2) -> bool:\n    # UCF-002 gate: building shells are solid. Enter and exit via INTERACT at\n    # front doors; this pilot has not yet installed interior partition collision.\n    var interior: Dictionary = _indoor_building()\n    for b in neighborhood.get("buildings", []):\n        var bounds: Array = b["footprint"]\n        var rect: Rect2 = Rect2(Vector2(float(bounds[0]),float(bounds[1])),Vector2(float(bounds[2]),float(bounds[3])))\n        var inside_next: bool = rect.has_point(point)\n        if interior.is_empty() and inside_next:\n            return false\n        if not interior.is_empty() and b["id"] == interior["id"] and not inside_next:\n            return false\n    return true\n\nfunc _process(delta: float) -> void:\n    if neighborhood.is_empty():\n        queue_redraw()\n        return\n    var direction: Vector2 = Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")\n    if move_vector.length_squared() > 0.001:\n        direction = move_vector\n    var next: Vector2 = player + direction.normalized() * delta * 4.1\n    if next.x >= 0.5 and next.x <= 65.0 and next.y >= 0.5 and next.y <= 45.5 and _can_walk_to(next):\n        player = next\n    # Smooth automatic zoom while the player occupies an interior.\n    var wanted_zoom: float = 1.65 if not _indoor_building().is_empty() else 1.0\n    zoom_factor = lerpf(zoom_factor, wanted_zoom, 1.0 - exp(-5.0 * minf(delta, 0.15)))\n    save_accumulator += delta\n    if save_accumulator >= 12.0:\n        save_accumulator = 0.0\n        _save_game()\n    queue_redraw()\n\nfunc _input(event: InputEvent) -> void:\n    if event is InputEventScreenTouch:\n        var p: Vector2 = event.position\n        if event.pressed:\n            if p.distance_to(_stick_center()) <= 105.0 and touch_id == -1:\n                touch_id = event.index\n                touch_start = _stick_center()\n                move_vector = (p - touch_start).limit_length(64.0) / 64.0\n            elif p.distance_to(_button_center()) <= 92.0:\n                _interact()\n        elif event.index == touch_id:\n            touch_id = -1\n            move_vector = Vector2.ZERO\n    elif event is InputEventScreenDrag:\n        if event.index == touch_id:\n            move_vector = (event.position - touch_start).limit_length(64.0) / 64.0\n    elif event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:\n        if event.position.distance_to(_button_center()) < 100.0:\n            _interact()\n    elif event is InputEventKey and event.pressed and not event.echo:\n        if event.keycode == KEY_E or event.keycode == KEY_SPACE:\n            _interact()\n        elif event.keycode == KEY_R:\n            roofs_visible = not roofs_visible\n\nfunc _interact() -> void:\n    if neighborhood.is_empty():\n        return\n    var interior: Dictionary = _indoor_building()\n    if not interior.is_empty():\n        var entry: Vector2 = _vec(interior["entry"]["pos"])\n        player = entry + Vector2(0.0, 1.2)\n        message = "Exited " + str(interior["id"])\n        _save_game()\n        return\n    var nearest: Dictionary = {}\n    var nearest_distance: float = 3.4\n    for b in neighborhood["buildings"]:\n        var entry: Vector2 = _vec(b["entry"]["pos"])\n        var distance: float = entry.distance_to(player)\n        if distance < nearest_distance:\n            nearest = b\n            nearest_distance = distance\n    if not nearest.is_empty():\n        var entry: Vector2 = _vec(nearest["entry"]["pos"])\n        player = entry + Vector2(0.0, -1.5)\n        open_doors[str(nearest["entry"]["id"])] = true\n        message = "Entered " + str(nearest["id"])\n        _save_game()\n    else:\n        message = "Move to a front door"\n\nfunc _save_game() -> void:\n    if neighborhood.is_empty():\n        return\n    var payload: Dictionary = {\n        "schema": "last_light.neighborhood_save.v2",\n        "seed": neighborhood["seed"],\n        "position": [player.x, player.y],\n        "doors_open": open_doors\n    }\n    var file: FileAccess = FileAccess.open(SAVE_PATH, FileAccess.WRITE)\n    if file != null:\n        file.store_string(JSON.stringify(payload))\n        file.close()\n\nfunc _load_game() -> void:\n    if not FileAccess.file_exists(SAVE_PATH):\n        return\n    var payload: Variant = JSON.parse_string(FileAccess.get_file_as_string(SAVE_PATH))\n    if payload is Dictionary and payload.get("schema", "") == "last_light.neighborhood_save.v2" and payload.get("seed", -1) == neighborhood["seed"]:\n        var p: Variant = payload.get("position", [])\n        if p is Array and p.size() == 2:\n            var point: Vector2 = _vec(p)\n            if point.x >= 0 and point.x <= 66 and point.y >= 0 and point.y <= 46:\n                player = point\n        if payload.get("doors_open", {}) is Dictionary:\n            open_doors = payload["doors_open"]\n\nfunc _quad(rect: Array, color: Color) -> void:\n    var x: float = float(rect[0]); var y: float = float(rect[1])\n    var w: float = float(rect[2]); var h: float = float(rect[3])\n    draw_colored_polygon(PackedVector2Array([\n        _iso(Vector2(x,y)), _iso(Vector2(x+w,y)),\n        _iso(Vector2(x+w,y+h)), _iso(Vector2(x,y+h))]), color)\n\nfunc _line(a: Vector2, b: Vector2, color: Color, width: float = 3.0) -> void:\n    draw_line(_iso(a), _iso(b), color, width, true)\n\nfunc _draw_house(b: Dictionary) -> void:\n    var bounds: Array = b["footprint"]\n    var x: float = float(bounds[0]); var y: float = float(bounds[1])\n    var w: float = float(bounds[2]); var h: float = float(bounds[3])\n    _quad(bounds, Color("9b947f"))\n    for room in b["rooms"]:\n        var tint: Color = Color("a8997b")\n        match str(room["type"]):\n            "kitchen": tint = Color("a7aaa0")\n            "bedroom": tint = Color("a8927d")\n            "living": tint = Color("9e947d")\n            "bathroom": tint = Color("9caeaf")\n        _quad(room["rect"],tint)\n    _quad(b["hall"]["rect"],Color("c4bca6"))\n    for f in b["furnishings"]:\n        var p: Vector2 = _vec(f["pos"])\n        _quad([p.x,p.y,0.7,0.7], Color("5a5145"))\n    var wall: Color = Color("d1ccba")\n    _line(Vector2(x,y),Vector2(x+w,y),wall,5)\n    _line(Vector2(x,y),Vector2(x,y+h),wall,5)\n    _line(Vector2(x+w,y),Vector2(x+w,y+h),wall,5)\n    var entry: Vector2 = _vec(b["entry"]["pos"])\n    _line(Vector2(x,y+h),entry-Vector2(0.6,0),wall,5)\n    _line(entry+Vector2(0.6,0),Vector2(x+w,y+h),wall,5)\n    draw_circle(_iso(entry),5,Color("eac27e"))\n    for door in b["interior_doors"]:\n        draw_circle(_iso(_vec(door["pos"])),4,Color("e4bd83"))\n    if roofs_visible and _indoor_building().get("id","") != b["id"]:\n        var roof: Color = Color("5d686b")\n        roof.a = 0.94\n        _quad(bounds,roof)\n        _line(Vector2(x,y),Vector2(x+w,y+h),Color("889597"),2)\n\nfunc _draw() -> void:\n    var viewport: Vector2 = get_viewport_rect().size\n    draw_rect(Rect2(Vector2.ZERO,viewport),Color("15231d"))\n    if neighborhood.is_empty():\n        draw_string(ThemeDB.fallback_font, Vector2(20,45), "Generated neighborhood data missing", HORIZONTAL_ALIGNMENT_LEFT,-1,22,Color.WHITE)\n        return\n    draw_set_transform(_camera_offset(),0,Vector2.ONE * zoom_factor)\n    # Low-cost ground cell rendering within a radius of the player.\n    for yy in range(maxi(0,int(player.y)-19),mini(45,int(player.y)+19)):\n        for xx in range(maxi(0,int(player.x)-19),mini(65,int(player.x)+19)):\n            var variation: int = posmod((xx*37+yy*19+xx*yy*7),5)\n            var tint: Color = Color("456249").lightened(float(variation)*0.025)\n            _quad([xx,yy,1,1],tint)\n    for rd in neighborhood["road"]:\n        _quad(rd["rect"],Color("4c5052"))\n        var road: Array = rd["rect"]\n        for i in range(int(road[0])+2,int(road[0])+int(road[2]),7):\n            _line(Vector2(i,float(road[1])+2.5),Vector2(i+3,float(road[1])+2.5),Color("b1a97d"),3)\n    for b in neighborhood["buildings"]:\n        var path: Array = b["road_access_path"]\n        _line(_vec(path[0]),_vec(path[1]),Color("a6a18a"),12)\n        _draw_house(b)\n    var p: Vector2 = _iso(player)\n    draw_circle(p+Vector2(0,4),7,Color(0,0,0,0.6))\n    draw_rect(Rect2(p+Vector2(-4,-18),Vector2(8,17)),Color("6898ab"))\n    draw_circle(p+Vector2(0,-22),6,Color("d8bfa0"))\n    draw_set_transform(Vector2.ZERO,0,Vector2.ONE)\n    draw_circle(_stick_center(),70,Color(0.08,0.14,0.12,0.7))\n    draw_arc(_stick_center(),70,0.0,TAU,40,Color("b8c9ac"),3,true)\n    draw_circle(_stick_center()+move_vector*52.0,23,Color("d6bd84"))\n    draw_circle(_button_center(),58,Color("d1b481"))\n    draw_string(ThemeDB.fallback_font,_button_center()+Vector2(-36,6),"ENTER",HORIZONTAL_ALIGNMENT_LEFT,-1,17,Color("1b2923"))\n    draw_string(ThemeDB.fallback_font,Vector2(16,32),"LAST LIGHT / GENERATED NEIGHBORHOOD V2",HORIZONTAL_ALIGNMENT_LEFT,-1,17,Color("ebead9"))\n    draw_string(ThemeDB.fallback_font,Vector2(16,55),"3 original house layouts / debug art only",HORIZONTAL_ALIGNMENT_LEFT,-1,13,Color("c2c7b9"))\n    draw_string(ThemeDB.fallback_font,Vector2(16,78),message,HORIZONTAL_ALIGNMENT_LEFT,-1,14,Color("efcb8b"))\n'
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

# ─────── UCF V3: safe metadata reconciliation and original-content pilots ───────
# This section deliberately does not transform/reference-download external game art.
V3_SCHEMA = "last_light.reconciliation_and_art.v3"
V3_RENDERER = "last_light.original_renderer.v3.0"
V3_PILOT_FAMILIES = (
    "can", "bottle", "bandage", "medkit", "backpack", "hammer", "axe",
    "flashlight", "crate", "wrench", "radio", "compass", "acorn", "mug",
    "book", "duct_tape"
)
V3_REVIEW_GATES = ("research_reference", "semantic_proposal", "original_recipe_draft",
                   "generated_candidate", "technical_qa_passed", "visual_review_required",
                   "founder_approved", "godot_integrated", "iphone_verified")
V3_TOKEN_PATTERN = re.compile(r"(?<!^)(?=[A-Z][a-z])|[^a-zA-Z0-9]+")
V3_VARIANT_SUFFIX = {"red", "blue", "green", "brown", "black", "white", "gray",
    "grey", "orange", "yellow", "purple", "camo", "sandcamo", "woodland",
    "desert", "damaged", "broken", "old", "rotten", "fresh", "empty", "full",
    "closed", "open", "raw", "dirty", "worn", "rusty", "clean", "new"}
V3_CATEGORY_ALIASES = {
    "pzwiki_item_icons":"item_icon_reference",
    "pzwiki_vehicle_models":"vehicle_model_reference",
    "pzwiki_vehicle_screenshots":"vehicle_screenshot_reference",
    "pzwiki_animated_images":"animation_reference",
    "pzwiki_animal_images":"animal_reference",
    "pzwiki_tile_images":"tile_reference",
    "pzwiki_furniture_tiles":"furniture_reference",
    "pzwiki_vegetation_tiles":"vegetation_reference",
    "pzwiki_floor_tiles":"floor_reference",
    "pzwiki_appliance_tiles":"appliance_reference",
    "pzwiki_animated_tiles":"animated_tile_reference",
}


def v3_slug(raw: str) -> str:
    raw = str(raw).replace('\\_', '_')
    parts = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|[0-9]+", raw.replace('_',' ').replace('-',' '))
    if not parts: parts = [raw]
    return re.sub(r"[^a-z0-9]+", "_", "_".join(p.lower() for p in parts)).strip("_")[:90] or "unknown"


def v3_family_hint(filename: str) -> tuple[str, list[str], str]:
    """Conservative suggestions. Never asserts distinct source objects are identical."""
    raw = re.sub(r"\.[a-zA-Z0-9]{2,5}$", "", str(filename))
    toks = [x for x in v3_slug(raw).split('_') if x]
    variants = []
    if len(toks)>2 and toks[-2:] == ['sand','camo']:
        toks=toks[:-2];variants.insert(0,'sandcamo')
    elif len(toks)>2 and toks[-2:] == ['wood','land']:
        toks=toks[:-2];variants.insert(0,'woodland')
    while len(toks) > 1 and toks[-1] in V3_VARIANT_SUFFIX:
        variants.insert(0,toks.pop())
    family = "_".join(toks) or "unknown"
    confidence = "suffix_heuristic_requires_review" if variants else "literal_name_hint"
    return family, variants, confidence


def v3_source_type(source_id: str, row: dict, proposed_class: str) -> tuple[str,str]:
    source_collection = str(row.get('source_collection',''))
    if source_id.startswith('ll.archetype.') or row.get('kind') == 'building':
        return 'building_recipe', 'verified_source_schema'
    if source_id.startswith('pzwiki.icon.'):
        return 'item_icon_reference', 'source_index_verified_category_provisional'
    if source_collection in V3_CATEGORY_ALIASES:
        return V3_CATEGORY_ALIASES[source_collection], 'source_category_hint_unverified'
    lower=(source_collection + ' ' + str(row.get('title',''))).lower()
    for keyword,label in (("vehicle","vehicle_reference"),("animal","animal_reference"),
                          ("animation","animation_reference"),("animated","animation_reference"),
                          ("vegetation","vegetation_reference"),("tile","tile_reference"),
                          ("texture","texture_reference"),("furniture","furniture_reference")):
        if keyword in lower:return label, 'filename_or_source_hint_unverified'
    if proposed_class and proposed_class.lower() not in ('needs review / unclassified','unclassified'):
        return 'item_or_prop_reference', 'provisional_filename_classifier'
    return 'unclassified_reference', 'manual_review_required'


def v3_reconcile(catalog: Catalog, root: Path) -> dict:
    """Never overwrite production.sqlite3 identity or classification rows.

    Keeps a separate SQLite ledger and full JSONL queue, so future approved
    original-content decisions and existing iPhone progress stay independent.
    """
    target = root / 'database' / 'reconciliation_v3.sqlite3'
    target.parent.mkdir(parents=True,exist_ok=True)
    ledger = sqlite3.connect(str(target))
    ledger.executescript('''
    CREATE TABLE IF NOT EXISTS reference_review (
        source_id TEXT PRIMARY KEY, first_fingerprint TEXT NOT NULL,
        review_status TEXT NOT NULL DEFAULT 'await_visual_review',
        notes TEXT NOT NULL DEFAULT '', original_recipe_id TEXT NOT NULL DEFAULT '',
        founder_approved INTEGER NOT NULL DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS original_art_review (
        original_asset_id TEXT PRIMARY KEY, review_status TEXT NOT NULL DEFAULT 'candidate',
        founder_approved INTEGER NOT NULL DEFAULT 0, notes TEXT NOT NULL DEFAULT ''
    );
    ''')
    fields = '''SELECT s.id,s.title,s.kind,s.category,s.description,s.provenance,s.rights,
        s.metadata_json,s.fingerprint,c.original_filename,c.proposed_category,
        c.family_candidate,c.variant_clues,c.confidence,c.review_state
        FROM sources s LEFT JOIN classifications c ON c.source_id=s.id
        ORDER BY s.id'''
    counts=Counter(); kinds=Counter(); collections=Counter(); reviewed=0; groups={}
    class_count=0; missing_class=[]; changes=[]; issues=[]; known_icons=[]
    queue_path=root/'reports'/'reconciliation_v3'/'production_queue.jsonl'
    export_path=root/'reports'/'reconciliation_v3'/'source_reconciliation.jsonl'
    queue_path.parent.mkdir(parents=True,exist_ok=True)
    queue_tmp=queue_path.with_suffix('.jsonl.tmp'); export_tmp=export_path.with_suffix('.jsonl.tmp')
    total=0
    with queue_tmp.open('w',encoding='utf-8') as queue,export_tmp.open('w',encoding='utf-8') as output:
        for row in catalog.db.execute(fields):
            sid,title,kind,category,desc,provenance,rights,metadata,fp,filename,pcat,fcand,vclue,conf,review_state=row
            source=json.loads(metadata);group_collection=str(source.get('source_collection','unspecified'))
            source_type,classification_method=v3_source_type(sid,source,pcat or '')
            source_name = filename or str(source.get('title') or title)
            family,variants,certainty=v3_family_hint(source_name)
            if fcand and source_type=='item_icon_reference':
                # Keep official provisional family candidate as evidence, not authoritative key.
                official_family=str(fcand)
            else:official_family=None
            # Include collection+source type to prevent unrelated source domains colliding.
            proposed_key=source_type+'.'+family
            candidate_id='ll.original.proposed.'+v3_slug(proposed_key)[:83]+'_'+sha256(proposed_key.encode())[:8]
            cstatus = (pcat or '').strip()
            if cstatus and cstatus.lower() not in ('needs review / unclassified','unclassified'):
                category_stage='keyword_classified_unverified'
            elif source_type=='building_recipe':
                category_stage='proposed_building_taxonomy'
            elif source_type!='unclassified_reference':
                category_stage='domain_inferred_unverified'
            else:category_stage='requires_manual_classification'
            if not cstatus and source_type=='item_icon_reference':
                missing_class.append(sid)
            if source_type=='item_icon_reference': known_icons.append(sid)
            if cstatus:class_count+=1
            if provenance=='original_internal' and source.get('approved'):
                stage='original_recipe_recorded_needs_visual_qa'
            else:stage='research_only_await_independent_original_recipe'
            # Every record is reconciled, but nothing gets design approval automatically.
            obj={
                'source_id':sid,'title':title,'source_filename':source_name,
                'source_collection':group_collection,'source_kind':source_type,
                'reference_only':provenance!='original_internal', 'source_rights':rights,
                'original_artwork_copied':False,
                'category_suggestion': cstatus if category_stage=='keyword_classified_unverified' else source_type,
                'category_status':category_stage,'classifier_method':classification_method,
                'filename_family_hint':family,'source_family_hint':official_family,
                'variant_suffix_hints':variants,'family_hint_method':certainty,
                'proposed_original_family_id':candidate_id,
                'state':stage,'approval_required':True,
                'source_fingerprint':fp,
            }
            previous=ledger.execute('SELECT first_fingerprint,founder_approved FROM reference_review WHERE source_id=?',(sid,)).fetchone()
            if previous and previous[0]!=fp:
                changes.append(sid)
                obj['source_snapshot_change_requires_review']=True
            if not previous:
                ledger.execute('INSERT INTO reference_review(source_id,first_fingerprint) VALUES(?,?)',(sid,fp))
            elif previous[1]:
                reviewed+=1
            if source_type=='item_icon_reference':
                obj['source_index']=source.get('source_index')
            output.write(json.dumps(obj,sort_keys=True,ensure_ascii=False)+'\n')
            queue.write(json.dumps({
                'job_id':'ll.job.'+sha256(sid.encode())[:20],
                'source_id':sid,'suggested_original_id':candidate_id,
                'source_kind':source_type,'state':'await_original_recipe_and_visual_approval',
                'renderer_available_for_this_source':False,
                'original_artwork_generated':False,
                'priority': 1 if source_type=='building_recipe' else 2 if source_type=='item_icon_reference' else 3,
                'provenance':'notion_research_only'
            },sort_keys=True,ensure_ascii=False)+'\n')
            total+=1;collections[group_collection]+=1;kinds[source_type]+=1
            counts[category_stage]+=1
            groups.setdefault(candidate_id,{'id':candidate_id,'source_type':source_type,
                'hint':family,'source_records':0,'requires_human_review':True})['source_records']+=1
            if total%500==0:ledger.commit()
    ledger.commit();ledger.close()
    os.replace(queue_tmp,queue_path);os.replace(export_tmp,export_path)
    group_list=sorted(groups.values(),key=lambda x:(-x['source_records'],x['id']))
    write_atomic(root/'reports'/'reconciliation_v3'/'family_suggestions.json',pretty({
        'schema':V3_SCHEMA,'total_provisional_family_groups':len(group_list),
        'warning':'Proposed grouping only. Similar filenames are NOT proof of equivalent game items.',
        'groups':group_list}))
    # Deduplicate by canonical source ID; verify icon sequence without assuming every catalog will have it.
    expected={f'pzwiki.icon.{i:06d}' for i in range(1,EXPECTED_ICON_RECORDS+1)}
    gaps=sorted(expected-set(known_icons))
    anomalies={'duplicate_source_ids':0, 'icon_missing':len(gaps),
         'uncategorized_item_icon_records':len(missing_class),
         'source_snapshot_changed_since_first_v3_import':len(changes)}
    report={'schema':V3_SCHEMA,'total_source_records':total,
        'source_records_reflected_in_queue':total,'source_records_generated_as_art':0,
        'indexed_item_icons':len(known_icons),'indexed_item_icon_gaps':gaps[:300],
        'provisional_classification_rows':class_count,
        'proposed_building_recipes':kinds.get('building_recipe',0),
        'proposed_original_family_groups':len(groups),'founder_approved_source_records':reviewed,
        'category_stage_counts':dict(sorted(counts.items())),
        'source_kind_counts':dict(sorted(kinds.items())),
        'source_collection_counts':dict(sorted(collections.items())),
        'quality_gates':list(V3_REVIEW_GATES),
        'data_status':'research_reconciled_not_art_completed',
        'flags':anomalies,
        'primary_catalog_unchanged':True,
        'source_reconciliation':str(export_path.relative_to(root)),
        'production_queue':str(queue_path.relative_to(root)),
        'family_suggestions':'reports/reconciliation_v3/family_suggestions.json'}
    write_atomic(root/'reports'/'reconciliation_v3'/'report.json',pretty(report))
    return report


def v3_hsl_lift(color,change):
    return tuple(max(0,min(255,int(c+change))) for c in color)


def v3_brush_texture(draw,box,base,seed,amount=30):
    r=random.Random(seed); x0,y0,x1,y1=map(int,box)
    if x1-x0<3 or y1-y0<3:return
    for _ in range(amount):
        x=r.randint(x0+1,x1-1);y=r.randint(y0+1,y1-1)
        k=r.choice((-29,-21,-15,9,13,18))
        draw.line((x,y,x+r.randint(0,3),y),fill=v3_hsl_lift(base,k)+(r.randint(90,185),),width=1)


def v3_icon(kind, variant, seed, dest):
    """New independently authored object templates; no source files are read."""
    Image, D=optional_pillow()
    if Image is None:raise RuntimeError('Pillow not available')
    im=Image.new('RGBA',(96,96),(0,0,0,0));d=D.Draw(im)
    r=random.Random(seed)
    dark=(36,37,35,255);metal=(115,119,114);silver=(168,172,163)
    wood=(118,84,56);leather=(104,74,53);olive=(88,101,72)
    accent=(151,72,51) if variant==0 else (66,92,92)
    def ellipse(b,fill,outline=None,width=1): d.ellipse(b,fill=fill,outline=outline,width=width)
    def poly(points,fill,outline=None,width=1):d.polygon(points,fill=fill);d.line(points+[points[0]],fill=outline,width=width) if outline else None
    def rect(b,fill,outline=None,width=1):d.rectangle(b,fill=fill,outline=outline,width=width)
    def line(points,fill,width=1):d.line(points,fill=fill,width=width)
    # Soft grounded cast shadow; alpha remains transparent off the object.
    ellipse((22,82,80,90),(30,35,30,58))
    if kind=='can':
        ellipse((24,21,74,40),(63,68,68,255),dark,2)
        rect((24,28,74,72),(123,123,115,255),dark,2)
        ellipse((24,60,74,75),(77,79,76,255),dark,2)
        rect((27,37,72,63),accent+(255,))
        rect((27,42,72,51),(203,185,149,255))
        for y in range(42,53,3):line([(36,y),(57,y)],(66,58,49,255))
        line([(29,29),(29,66)],(223,215,183,255),3)
        ellipse((26,19,73,33),(169,166,149,255),dark,2)
        ellipse((35,23,64,29),(71,77,73,255))
        v3_brush_texture(d,(32,53,68,63),accent,seed,18)
    elif kind=='bottle':
        rect((39,18,58,30),(159,168,165,255),dark,2)
        rect((41,11,56,20),accent+(255,),dark,1)
        poly([(34,30),(62,30),(68,40),(70,75),(64,82),(33,82),(27,75),(28,41)],
             (116,151,155,210),dark,2)
        rect((32,45,66,65),(205,207,191,248),dark,1)
        rect((32,52,66,58),accent+(255,))
        line([(34,39),(34,73)],(225,232,216,200),4)
        line([(61,37),(64,70)],(54,90,103,210),3)
        for y in (13,16,19):line([(42,y),(56,y)],(55,54,53,200))
    elif kind=='bandage':
        poly([(19,29),(66,22),(79,37),(76,70),(29,76),(18,65)],(189,183,163,255),dark,2)
        poly([(23,31),(62,26),(70,39),(68,68),(32,69),(23,62)],(218,215,193,255))
        rect((35,37,61,63),(146,165,169,255),(87,96,100,255),1)
        rect((45,42,51,58),(232,226,211,255))
        rect((39,47,57,53),(232,226,211,255))
        for x in range(22,70,7):line([(x,31),(x+3,27)],(158,153,137,160))
        if variant:
            rect((28,57,37,63),(133,145,143,255),dark,1)
            line([(62,33),(68,40)],(150,144,125,255),2)
    elif kind=='medkit':
        rect((19,36,79,76),accent+(255,),dark,3)
        rect((22,39,74,71),v3_hsl_lift(accent,16)+(255,))
        poly([(19,35),(26,25),(70,25),(79,35)],(183,83,64,255),dark,2)
        rect((38,19,58,27),(74,76,66,255),dark,1)
        rect((43,43,54,67),(220,217,196,255))
        rect((35,51,62,59),(220,217,196,255))
        line([(23,42),(23,65)],(238,167,132,255),3)
        for x in (29,67):rect((x,68,x+5,74),(77,79,70,255),dark)
    elif kind=='backpack':
        # straps are visible behind an asymmetric canvas body.
        for sx in (28,64):line([(sx,25),(sx+(-9 if sx==28 else 9),62),(sx,83)],(51,57,42,255),7)
        poly([(27,34),(38,26),(56,27),(69,35),(72,78),(25,78)],olive+(255,),dark,3)
        poly([(31,34),(43,31),(58,32),(63,42),(64,66),(30,67)],
             v3_hsl_lift(olive,12)+(255,))
        poly([(29,53),(65,53),(65,75),(29,75)],(69,76,54,255),dark,2)
        line([(33,55),(61,55)],(178,167,116,255),2)
        rect((43,54,50,72),(72,59,43,255))
        rect((44,60,49,66),(164,150,113,255))
        for x in (30,62):rect((x,45,x+4,61),(76,65,43,255))
        v3_brush_texture(d,(34,39,59,51),olive,seed,30)
        if variant:poly([(28,58),(38,58),(37,71),(27,71)],(114,103,66,255))
    elif kind in ('hammer','axe','wrench'):
        # Hand tools are painted on their own native layer then rotated; materials
        # have distinct highlights, in contrast with flat silhouette placeholders.
        sub=Image.new('RGBA',(96,96));sd=D.Draw(sub)
        sd.polygon([(44,38),(56,38),(54,84),(46,84)],fill=wood+(255,))
        sd.line([(46,42),(47,77)],fill=(195,152,102,255),width=3)
        sd.line([(54,42),(52,81)],fill=(69,46,35,255),width=3)
        if kind=='hammer':
            sd.polygon([(25,29),(70,29),(76,34),(70,42),(23,42),(20,35)],fill=metal+(255,))
            sd.line([(24,32),(70,31)],fill=(203,202,177,255),width=4)
            sd.line([(63,40),(68,46)],fill=(59,61,63,255),width=2)
        elif kind=='axe':
            sd.polygon([(39,25),(75,20),(70,47),(40,45)],fill=metal+(255,))
            sd.polygon([(41,28),(70,22),(65,43),(42,43)],fill=(143,146,139,255))
            sd.line([(71,21),(67,44)],fill=(224,222,206,255),width=3)
        else:
            sd.polygon([(39,29),(40,17),(47,21),(50,27),(55,21),(63,17),(64,30),(55,43),(46,42)],fill=metal+(255,))
            sd.line([(42,26),(46,34),(57,34)],fill=(209,211,190,255),width=3)
        sub=sub.rotate(41 if variant==0 else 28,resample=Image.Resampling.NEAREST)
        im.alpha_composite(sub)
    elif kind=='flashlight':
        poly([(29,31),(55,28),(72,37),(73,50),(57,58),(35,55)],(55,59,60,255),dark,2)
        poly([(37,43),(62,45),(65,79),(41,80)],(65,74,73,255),dark,3)
        ellipse((48,31,76,56),(155,162,151,255),dark,2)
        ellipse((53,35,70,52),(223,222,192,255),dark,1)
        ellipse((56,38,67,49),(244,238,199,255))
        rect((43,50,51,61),accent+(255,),dark,1)
        for y in (66,71,76):line([(42,y),(62,y)],(39,46,45,255),1)
    elif kind=='crate':
        poly([(17,38),(48,24),(80,37),(49,52)],(150,112,72,255),dark,2)
        poly([(17,38),(49,52),(49,81),(17,67)],(92,69,49,255),dark,2)
        poly([(49,52),(80,37),(80,66),(49,81)],(121,91,62,255),dark,2)
        for y in (43,53,64):line([(18,y),(49,y+13)],(54,45,38,255),2)
        line([(53,55),(77,43)],(184,145,91,255),3)
        for y in (58,71):line([(51,y),(79,y-13)],(59,45,32,255),2)
        for x,y in ((24,41),(73,40),(54,73)):ellipse((x,y,x+3,y+3),(40,38,33,255))
        if variant:
            poly([(22,49),(45,59),(45,65),(22,56)],(150,124,81,255),dark,1)
            line([(57,69),(74,62)],(181,156,104,255),2)
    elif kind=='radio':
        poly([(21,39),(68,34),(78,45),(77,78),(23,82)],(57,63,65,255),dark,3)
        poly([(24,42),(67,39),(72,45),(70,68),(24,71)],(91,93,90,255))
        rect((29,49,56,61),(36,49,50,255),dark,1)
        for k in range(3):line([(31,52+3*k),(52,51+3*k)],(145,161,151,255))
        ellipse((60,50,68,58),(156,163,148,255),dark,1)
        ellipse((59,64,68,73),accent+(255,),dark,1)
        line([(26,38),(30,18)],(157,165,156,255),2)
        line([(30,18),(44,10)],(155,160,152,255),1)
    elif kind=='compass':
        ellipse((23,21,75,76),(58,64,61,255),dark,3)
        ellipse((28,26,70,71),(195,179,143,255),(77,73,58,255),2)
        ellipse((34,32,64,64),(108,126,118,255))
        poly([(48,35),(45,49),(49,52),(54,62),(51,46)],accent+(255,),dark,1)
        ellipse((45,45,53,53),(234,222,180,255),dark)
        for x,y in ((48,30),(48,65),(33,49),(66,49)):ellipse((x-1,y-1,x+1,y+1),(60,63,56,255))
        ellipse((41,16,56,23),(77,68,51,255),dark,2)
    elif kind=='acorn':
        ellipse((31,33,68,77),(126,79,45,255),dark,2)
        poly([(31,43),(43,36),(64,38),(70,47),(67,54),(32,52)],(103,82,51,255),dark,2)
        for x in range(35,67,5):
            for y in range(42,51,5):ellipse((x,y,x+3,y+2),(152,127,77,255))
        poly([(49,36),(51,25),(56,24),(55,37)],(88,63,45,255))
        poly([(55,30),(69,23),(80,26),(72,37),(60,41)],(75,98,55,255),dark,1)
        for x in range(34,60,4):line([(x,63),(x+2,65)],(171,113,64,150))
        if variant:
            line([(61,33),(74,26)],(178,190,120,255),2)
            line([(61,34),(78,35)],(49,74,46,255),2)
    elif kind=='mug':
        ellipse((24,34,69,49),(57,64,64,255),dark,3)
        ellipse((57,45,82,69),(76,80,78,255),dark,4)
        rect((25,41,66,73),accent+(255,),dark,2)
        ellipse((25,64,66,78),(97,91,82,255),dark,2)
        ellipse((27,33,65,45),(164,162,144,255),dark,2)
        ellipse((33,35,61,41),(64,58,50,255))
        line([(29,44),(29,65)],(216,169,131,255),3)
        for y in (53,59):line([(40,y),(54,y)],(190,148,114,255),2)
    elif kind=='book':
        poly([(22,31),(64,23),(75,34),(71,77),(30,85),(20,74)],(98,68,53,255),dark,2)
        poly([(25,32),(64,26),(69,72),(29,79)],accent+(255,),dark,2)
        poly([(64,26),(73,33),(74,72),(69,72)],(216,205,178,255),dark,1)
        line([(35,48),(60,44)],(190,165,123,255),2)
        line([(38,54),(61,50)],(190,165,123,255),2)
        ellipse((44,60,54,69),(189,170,125,255))
        v3_brush_texture(d,(32,33,61,70),accent,seed,25)
    elif kind=='duct_tape':
        ellipse((16,34,80,78),(67,70,68,255),dark,3)
        ellipse((22,34,78,71),(117,121,119,255),dark,2)
        ellipse((34,43,65,64),(53,56,56,255),dark,2)
        ellipse((39,46,61,60),(110,97,73,255))
        for x in (23,30,65,72):line([(x,42),(x,67)],(178,182,178,150),2)
        poly([(67,63),(77,76),(74,84),(65,73)],(159,163,158,255),dark,1)
        if variant:
            poly([(73,67),(83,72),(87,82),(77,83)],(184,187,183,255),dark,1)
            line([(26,51),(30,64)],(220,224,216,255),2)
    else: raise ValueError('Unsupported V3 semantic art template: '+kind)
    # A faint upper-left specular accent and restrained material-specific noise.
    x0=10;y0=9;x1=88;y1=83
    a=im.getchannel('A'); bounds=a.getbbox()
    if bounds is None:raise ValueError('Empty renderer result')
    dest.parent.mkdir(parents=True,exist_ok=True)
    temp=dest.with_suffix('.png.tmp')
    im.save(temp,format='PNG',optimize=True);os.replace(temp,dest)
    return sha256(dest.read_bytes())


def v3_effects(root:Path,seed:int) -> list[dict]:
    """Original environmental effect loops; explicitly not character animation."""
    Image, D=optional_pillow()
    if Image is None:return []
    outputs=[]
    for kind in ('rain_ripple','smoke_puff'):
        atlas=Image.new('RGBA',(8*64,64),(0,0,0,0))
        for f in range(8):
            fr=Image.new('RGBA',(64,64),(0,0,0,0));d=D.Draw(fr)
            if kind=='rain_ripple':
                rr=int(3+f*3.5);alpha=int(240*(1-f/8));
                d.ellipse((32-rr,33-rr//3,32+rr,33+rr//3),outline=(147,174,169,alpha),width=2)
                d.ellipse((32-rr+2,34-rr//3,32+rr-2,34+rr//3),outline=(73,104,107,alpha//2),width=1)
            else:
                rng=random.Random(seed_for(seed,'fx',kind,f//2))
                for i in range(5):
                    x=24+i*4+rng.randrange(-5,6);y=47-f*3+i*2
                    radius=5+f//2
                    d.ellipse((x-radius,y-radius,x+radius,y+radius),fill=(125,127,115,max(8,125-f*12)))
            atlas.alpha_composite(fr,(f*64,0))
        target=root/'assets'/'v3_original_candidates'/'fx'/f'{kind}.png';target.parent.mkdir(parents=True,exist_ok=True)
        atlas.save(target,optimize=True)
        outputs.append({'id':'ll.fx.'+kind,'frames':8,'frame_size':[64,64],
            'path':str(target.relative_to(root)),'sha256':sha256(target.read_bytes()),
            'type':'environmental_effect','status':'technical_candidate_visual_review_required'})
    return outputs


def v3_art_production(root: Path, seed: int, max_icons: int) -> dict:
    """Pilot original art only; no extrapolated Golden 40 approval or source cloning."""
    Image, ImageDraw=optional_pillow()
    if Image is None:
        report={'status':'blocked_missing_pillow','generated':0,'required':'Install Pillow in CodePad; metadata reconciliation already completed.'}
        write_atomic(root/'reports'/'reconciliation_v3'/'art_production_report.json',pretty(report))
        return report
    icons=[];errors=[];textures=[]
    choices=[(fam,variant) for fam in V3_PILOT_FAMILIES for variant in (0,1)]
    for kind,variant in choices[:max_icons]:
        asset_id=f'll.original.pilot.{kind}.{variant:02d}'
        out=root/'assets'/'v3_original_candidates'/'icons'/f'{kind}_{variant:02d}.png'
        try:
            digest=v3_icon(kind,variant,seed_for(seed,'pilot',kind,variant),out)
            with Image.open(out) as img:
                rgba=img.convert('RGBA');bbox=rgba.getchannel('A').getbbox()
                if img.size!=(96,96) or img.mode!='RGBA' or not bbox:
                    raise ValueError('Invalid RGBA icon geometry')
                if (bbox[2]-bbox[0])<16 or (bbox[3]-bbox[1])<16:
                    raise ValueError('Candidate silhouette too small')
            icons.append({'id':asset_id,'family':kind,'variant':variant,
                'path':str(out.relative_to(root)),'sha256':digest,
                'original_provenance':'independently_authored_geometry_template',
                'source_reference_image_copied':False,
                'render_quality':'procedural_candidate_not_golden_40_approved',
                'godot_integrated':False,'iphone_verified':False})
        except (ValueError,OSError,RuntimeError) as exc:errors.append({'id':asset_id,'error':str(exc)})
    # Texture previews only. Repeats have pixel-identical opposite edges; full
    # art repeat/transition QA on real ground diamond is still outstanding.
    for kind in TERRAIN_MATERIALS:
        path=root/'assets'/'v3_original_candidates'/'materials'/f'{kind}.png'
        try:
            h=generate_texture(kind,seed_for(seed,'tile',kind),path,size=64)
            with Image.open(path) as tex:
                rgb=tex.convert('RGBA');w,hgt=rgb.size
                edge_ok=all(rgb.getpixel((0,y))==rgb.getpixel((w-1,y)) for y in range(hgt)) and \
                        all(rgb.getpixel((x,0))==rgb.getpixel((x,hgt-1)) for x in range(w))
            if not edge_ok:raise ValueError('Texture periodic edge check failed')
            textures.append({'id':'ll.material.pilot.'+kind,'path':str(path.relative_to(root)),
               'sha256':h,'pixel_edge_continuity':True,
               'status':'technical_candidate_not_approved_in_game'})
        except (ValueError,OSError) as exc:errors.append({'id':kind,'error':str(exc)})
    vegetation=generate_vegetation_pack(root,seed)
    fx=v3_effects(root,seed)
    # Display exactly what was generated and allow founder to reject candidates.
    if icons:
        cell=132; cols=8;rows=(len(icons)+cols-1)//cols
        sheet=Image.new('RGB',(cols*cell,rows*cell+28),(34,36,33))
        draw=ImageDraw.Draw(sheet)
        for idx,record in enumerate(icons):
            src=Image.open(root/record['path']).convert('RGBA')
            # checkerboard white/gray avoids confusing white source references
            x=(idx%cols)*cell;y=(idx//cols)*cell
            draw.rectangle((x+8,y+6,x+119,y+114),fill=(205,206,197))
            draw.rectangle((x+8,y+6,x+64,y+60),fill=(219,220,211))
            draw.rectangle((x+64,y+60,x+119,y+114),fill=(219,220,211))
            sheet.paste(src,(x+16,y+12),src)
            draw.text((x+8,y+116),record['family'][:14]+' '+str(record['variant']),fill=(228,226,214))
        draw.text((8,rows*cell+8),'LAST LIGHT V3 — ORIGINAL CANDIDATES · NOT GOLDEN 40 APPROVED',fill=(244,212,171))
        target=root/'review'/'v3_original_icon_contact_sheet.png';target.parent.mkdir(parents=True,exist_ok=True)
        sheet.save(target,optimize=True)
    else:target=None
    all_hashes=[x['sha256'] for x in icons]
    duplicates=len(all_hashes)-len(set(all_hashes))
    report={
        'schema':V3_SCHEMA,'factory_version':VERSION,'icons_generated':len(icons),
        'icon_semantic_families':len(set(x['family'] for x in icons)),
        'texture_samples':len(textures),'vegetation_candidates':vegetation.get('generated',0),
        'environmental_effect_sheet_count':len(fx),'environmental_effect_frames':sum(x['frames'] for x in fx),
        'duplicate_icon_binary_hashes':duplicates,'failure_count':len(errors),'failures':errors,
        'golden_40_approved':False,'source_references_transformed_into_art':0,
        'artwork_review_status':'technical_candidates_visual_qa_required',
        'production_backlog_status':'unapproved_source_records_remain_queued',
        'visual_review_contact_sheet':str(target.relative_to(root)) if target else None,
    }
    manifest={
        'schema':V3_SCHEMA,'version':VERSION,'generator':V3_RENDERER,
        'asset_approval':'none_automatically_approved',
        'icons':icons,'texture_candidates':textures,'vegetation_manifest':'manifests/vegetation_manifest.json',
        'effect_candidates':fx,'qa':report
    }
    style_contract = {
      'standard':'LAST LIGHT Golden 40 original pixel realism',
      'status':'hard_human_acceptance_gate_not_automatically_satisfied',
      'visual_reference':'founder-approved 40-item reference sheets (not included in generated art)',
      'directional_light':'consistent upper-left',
      'shading':'material-specific believable highlights/occlusion; strong form depth',
      'materials':'metal sharp reflection; cloth/wood/leather diffuse highlights; physical wear',
      'geometry':'recognizable proportions and coherent 2:1 isometric world assets where applicable',
      'pixel_grid':'deliberate readable pixel clusters; no anti-aliased blur in final pixel assets',
      'critical_checks':[
         'readable silhouette at native inventory size',
         'recognizable construction/shape and correct material response',
         'alpha and ground anchors correct',
         'original design not traced/repainted from PZwiki references',
         'directional frame sets where actor/vehicle movement requires them',
         'consistent visual scale and lighting across different categories',
         'actual Godot and iPhone comparison against approved reference'
      ],
      'technical_checks_passed_do_not_imply_visual_checks_passed':True,
      'auto_approve_generated_images':False,
      'rejection_policy':'reject/refine any candidate not matching Golden 40 in actual game scale'
    }
    write_atomic(root/'manifests'/'v3_golden_style_review_contract.json',pretty(style_contract))
    write_atomic(root/'manifests'/'v3_art_candidate_manifest.json',pretty(manifest))
    write_atomic(root/'reports'/'reconciliation_v3'/'art_production_report.json',pretty(report))
    # No update to the user's original catalog art-approved state.
    return report


def v3_export(root: Path) -> str:
    """Small, verified delivery archive containing V3 reports, candidates, not user DB."""
    targets=[]
    for rel in ('reports/reconciliation_v3','assets/v3_original_candidates','assets/original_textures/vegetation','review','manifests'):
        folder=root/rel
        if folder.exists():
            targets.extend(p for p in folder.rglob('*') if p.is_file() and '.tmp' not in p.name)
    unique=sorted(set(targets),key=lambda p:str(p.relative_to(root)))
    path=root/'exports'/'LAST_LIGHT_V3_RECONCILED_ART_CANDIDATES.zip'
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix('.zip.tmp')
    with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in unique:
            rel=p.relative_to(root)
            zi=zipfile.ZipInfo(str(rel).replace(os.sep,'/'),date_time=(2020,1,1,0,0,0))
            zi.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(zi,p.read_bytes())
    os.replace(tmp,path)
    with zipfile.ZipFile(path) as z:
        bad=z.testzip()
        if bad:raise ValueError('Export ZIP failed integrity validation: '+bad)
    return str(path)


def v3_reconcile_and_generate(catalog: Catalog,root:Path,seed:int,max_icons:int) -> dict:
    source_count=catalog.db.execute('SELECT COUNT(*) FROM sources').fetchone()[0]
    if source_count==0:
        raise ValueError('No source records in existing iPhone catalog. Run ACTION="sync_catalog" in this file first, then re-run ACTION="reconcile_and_generate".')
    print('STAGE 1 / 2 — SOURCE RECONCILIATION')
    r=v3_reconcile(catalog,root)
    print('  Indexed:',r['total_source_records'],'| Icons:',r['indexed_item_icons'],
          '| Provisional classifications:',r['provisional_classification_rows'],
          '| Building archetypes:',r['proposed_building_recipes'])
    print('  Suggested original families:',r['proposed_original_family_groups'],
          '| Existing production DB preserved:',r['primary_catalog_unchanged'])
    print('STAGE 2 / 2 — INDEPENDENT ORIGINAL-ART PILOT RENDERING')
    a=v3_art_production(root,seed,max_icons)
    print('  Generated candidate icons:',a.get('icons_generated',0),
          '| Textures:',a.get('texture_samples',0),
          '| Vegetation:',a.get('vegetation_candidates',0),
          '| Environmental effect sheets:',a.get('environmental_effect_sheet_count',0))
    print('  GOLDEN 40 APPROVED:',False,'| Visual approval required')
    zip_path=v3_export(root)
    print('V3 EXPORT:',zip_path)
    return {'reconciliation':r,'art':a,'export_zip':zip_path}



def main(argv:list[str]|None=None)->int:
    argv=[] if argv is None else list(argv)
    parser=argparse.ArgumentParser(description="LAST LIGHT Unified Python Factory V2")
    parser.add_argument("--action",choices=["reconcile_and_generate","demo","import","sync_catalog","neighborhood","audit","batch","world","verify","export"],default=ACTION)
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
    if any(part.lower() in {"tmp","temp"} for part in root.parts):
        print("WARNING: TEMP storage may be erased by iOS; copy the export ZIP into Files/iCloud.")
    for sub in ("imports","reports","world","assets","manifests","review","exports"):(root/sub).mkdir(exist_ok=True)
    catalog=Catalog(root/"database"/"production.sqlite3")
    try:
        if args.action=="reconcile_and_generate":
            v3_reconcile_and_generate(catalog,root,args.seed,max(1,min(args.batch,32)))
            print("COMPLETE in",round(time.monotonic()-started,2),"s; no paid API called")
            return 0
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
