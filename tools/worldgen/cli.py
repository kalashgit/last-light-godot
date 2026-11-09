"""LAST LIGHT quick world creator (W04-E), command-line edition.

  python3 tools/llworld.py list
  python3 tools/llworld.py generate --preset w04_demo_suburb [--seed N] [--out DIR] [--png FILE]
  python3 tools/llworld.py generate --recipe my_recipe.json --out DIR
  python3 tools/llworld.py verify DIR
  python3 tools/llworld.py inspect DIR [--building ID] [--z 0]
  python3 tools/llworld.py building --program house_small --seed 3      (layout preview, no world)
  python3 tools/llworld.py building --fixture LAB-H02 --z 1
  python3 tools/llworld.py new-recipe --style rural_edge --seed 42 --world-id ll.world.mine --out my_recipe.json
  python3 tools/llworld.py set-lot my_recipe.json --lot 3 --program workshop | --fixture LAB-W01 | --vacant | --clear
  python3 tools/llworld.py benchmark --preset w04_demo_suburb
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path

from .buildings import fixture_building, generate_building
from .catalog import catalog
from .core import DATA, ROOT, SCHEMA_RECIPE, GenerationError, atomic_write, dumps, load_json
from .export import export_world
from .loader import load_export, verify_export
from .neighborhood import generate_world, validate_world
from .preview import ascii_floor, png_world

RECIPES = DATA / "recipes"
GENERATED = DATA / "generated"


def load_recipe(args):
    path = Path(args.recipe) if args.recipe else RECIPES / f"{args.preset}.json"
    recipe = load_json(path)
    if args.seed is not None:
        recipe["world_seed"] = args.seed
        recipe["world_id"] = f"{recipe['world_id']}.s{args.seed}"
    return recipe


def cmd_list(_args):
    cat = catalog()
    print("presets:", ", ".join(sorted(p.stem for p in RECIPES.glob("*.json"))))
    print("styles:", ", ".join(sorted(cat["styles"]["styles"])))
    print("programs:", ", ".join(f"{k}->{v['archetype_id']}" for k, v in sorted(cat["programs"].items())))
    print("lab_a fixtures:", ", ".join(f"{k} ({v['name']})" for k, v in sorted(cat["lab_a"]["buildings"].items())))
    print("archetypes (60 canonical):", len(cat["archetypes"]))
    return 0


def cmd_generate(args):
    recipe = load_recipe(args)
    t0 = time.perf_counter()
    world = generate_world(recipe)
    report = validate_world(world)
    out = Path(args.out) if args.out else GENERATED / (args.preset or Path(args.recipe).stem)
    manifest = export_world(world, report, out, args.chunk_size)
    dt = time.perf_counter() - t0
    for c in report["checks"]:
        print(("PASS " if c["ok"] else "FAIL ") + c["check"] + (f" — {c['detail']}" if c["detail"] else ""))
    print(f"world {manifest['world_id']} seed={manifest['world_seed']} version={manifest['generator_version']}")
    print(f"buildings={len(manifest['buildings'])} chunks={len(manifest['chunks'])} bounds={manifest['bounds']} blueprint={manifest['blueprint_sha256'][:16]} ({dt:.2f}s)")
    print("output:", out)
    if args.png:
        print("preview:", args.png if png_world(world, args.png) else "Pillow not installed; skipped")
    return 0 if report["ok"] else 2


def cmd_verify(args):
    manifest, world, problems = verify_export(args.dir)
    report = validate_world(world)
    for c in report["checks"]:
        if not c["ok"]:
            problems.append(f"{c['check']}: {c['detail']}")
    for p in problems:
        print("FAIL", p)
    print(("PASS" if not problems else "FAIL"), manifest["world_id"], f"buildings={len(world['buildings'])}",
          f"checks={len(report['checks'])}", f"blueprint={manifest['blueprint_sha256'][:16]}")
    return 0 if not problems else 2


def cmd_inspect(args):
    _, world, _ = load_export(args.dir)
    if not args.building:
        for lot in world["lots"]:
            print(f"{lot['id']} {lot['rect']} front={lot['front']} zoning={lot['zoning']} building={lot.get('building_id')}")
        return 0
    b = next((b for b in world["buildings"] if b["id"] == args.building or b["id"].startswith(args.building)), None)
    if not b:
        print("unknown building", args.building)
        return 2
    print(f"{b['id']} program={b['program']} template={b['template']} condition={b['condition']} roof={b['roof']['profile']}")
    print(ascii_floor(b, args.z))
    return 0


def cmd_building(args):
    if args.fixture:
        b = fixture_building(args.fixture, f"preview.{args.fixture}")
    else:
        b = generate_building(args.program, f"preview.{args.program}.s{args.seed}", args.seed)
        print("generation:", b["generation"])
    for f in b["floors"]:
        if args.z is None or f["z"] == args.z:
            print(f"-- z={f['z']} size={b['size']} condition={b['condition']}")
            print(ascii_floor(b, f["z"]))
    return 0


def cmd_new_recipe(args):
    recipe = {"schema": SCHEMA_RECIPE, "world_id": args.world_id, "name": args.world_id, "world_seed": args.seed,
              "style": args.style, "lot_overrides": {}}
    atomic_write(Path(args.out), dumps(recipe))
    print("wrote", args.out)
    return 0


def cmd_set_lot(args):
    path = Path(args.recipe_file)
    recipe = load_json(path)
    ov = recipe.setdefault("lot_overrides", {})
    key = str(args.lot)
    if args.clear:
        ov.pop(key, None)
    elif args.vacant:
        ov[key] = {"vacant": True}
    elif args.fixture:
        ov[key] = {"fixture": args.fixture}
    elif args.program:
        ov[key] = {"program": args.program}
    generate_world(recipe)  # reject edits that cannot generate before saving them
    atomic_write(path, dumps(recipe))
    print("updated", path, key, ov.get(key))
    return 0


def cmd_benchmark(args):
    recipe = load_recipe(args)
    t0 = time.perf_counter()
    world = generate_world(recipe)
    t1 = time.perf_counter()
    report = validate_world(world)
    t2 = time.perf_counter()
    print(f"generate {t1 - t0:.3f}s validate {t2 - t1:.3f}s (desktop CPython; not an iPhone measurement)")
    for size in (8, 16, 24, 32):
        with tempfile.TemporaryDirectory() as tmp:
            t3 = time.perf_counter()
            m = export_world(world, report, Path(tmp), size)
            t4 = time.perf_counter()
            files = list(Path(tmp).rglob("chunk_*.json"))
            total = sum(f.stat().st_size for f in files)
            print(f"chunk {size:>2}: {len(files):>3} chunks, mean {total / len(files) / 1024:.1f} KiB, export {t4 - t3:.3f}s")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="llworld", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    for name in ("generate", "benchmark"):
        g = sub.add_parser(name)
        src = g.add_mutually_exclusive_group(required=True)
        src.add_argument("--preset")
        src.add_argument("--recipe")
        g.add_argument("--seed", type=int)
        g.add_argument("--out")
        g.add_argument("--png")
        g.add_argument("--chunk-size", type=int, default=16)
    v = sub.add_parser("verify")
    v.add_argument("dir")
    i = sub.add_parser("inspect")
    i.add_argument("dir")
    i.add_argument("--building")
    i.add_argument("--z", type=int, default=0)
    b = sub.add_parser("building")
    src = b.add_mutually_exclusive_group(required=True)
    src.add_argument("--program")
    src.add_argument("--fixture")
    b.add_argument("--seed", type=int, default=0)
    b.add_argument("--z", type=int)
    n = sub.add_parser("new-recipe")
    n.add_argument("--style", required=True)
    n.add_argument("--seed", type=int, required=True)
    n.add_argument("--world-id", required=True)
    n.add_argument("--out", required=True)
    s = sub.add_parser("set-lot")
    s.add_argument("recipe_file")
    s.add_argument("--lot", required=True)
    grp = s.add_mutually_exclusive_group(required=True)
    grp.add_argument("--program")
    grp.add_argument("--fixture")
    grp.add_argument("--vacant", action="store_true")
    grp.add_argument("--clear", action="store_true")
    args = p.parse_args(argv)
    handler = {"list": cmd_list, "generate": cmd_generate, "verify": cmd_verify, "inspect": cmd_inspect,
               "building": cmd_building, "new-recipe": cmd_new_recipe, "set-lot": cmd_set_lot, "benchmark": cmd_benchmark}[args.cmd]
    try:
        return handler(args)
    except GenerationError as exc:
        print("ERROR", exc.code, exc.detail, file=sys.stderr)
        return 3
