"""Regional layout (W04-G): a fictional region grid of district slots.

World -> Region -> District. Only the requested district is compiled into
local streets/parcels; every other slot is a deterministic specification
(zone, biome, density, seed) ready for later lazy compilation. Original
fictional geography only; no real-world or Project Zomboid map data.
"""
from __future__ import annotations

from .core import SCHEMA_REGION, Rng, stream_seed
from .terrain import fbm

REGION_GRID = (8, 8)


def region_spec(world_seed, region_id="ll.region.r00", name="Harlan Valley (fictional)"):
    rseed = stream_seed(world_seed, "region", region_id)
    rng = Rng(rseed)
    gw, gh = REGION_GRID
    towns = sorted({(rng.randint(2, gw - 3), rng.randint(2, gh - 3)) for _ in range(2)})
    slots = []
    for j in range(gh):
        for i in range(gw):
            elev = fbm(rseed, i * 6, j * 6, 20.0)
            moist = fbm(rseed + 13, i * 6, j * 6, 16.0)
            d = min(abs(i - tx) + abs(j - ty) for tx, ty in towns)
            if elev < 0.28 and d > 1:
                zone, style = "water", None
            elif d == 0:
                zone, style = "town_center", "old_town_dense"
            elif d == 1:
                zone, style = "residential", "suburban_detached"
            elif d == 2:
                zone, style = "agricultural" if moist < 0.55 else "rural_residential", "rural_edge"
            else:
                zone, style = "wilderness" if moist > 0.5 else "agricultural", None
            slots.append({"slot": [i, j], "district_id": f"ll.{region_id.split('.')[-1]}.d{i}{j}",
                          "zone": zone, "district_style": style, "elevation": round(elev, 4), "moisture": round(moist, 4),
                          "district_seed": stream_seed(world_seed, "district", region_id, i, j),
                          "compiled": False})
    links = []
    for a, b in zip(towns, towns[1:]):
        path = []
        x, y = a
        while (x, y) != b:
            path.append([x, y])
            x += (b[0] > x) - (b[0] < x)
            if x == b[0]:
                y += (b[1] > y) - (b[1] < y)
        path.append(list(b))
        links.append({"id": f"{region_id}.hwy{len(links):02d}", "kind": "highway", "slots": path})
    return {"schema": SCHEMA_REGION, "region_id": region_id, "name": name, "region_seed": rseed,
            "grid": list(REGION_GRID), "slot_tiles": [96, 96], "towns": [list(t) for t in towns],
            "slots": slots, "links": links,
            "status": "specification: only slots marked compiled=true have local street/parcel data"}


def pick_slot(region, style):
    for s in region["slots"]:
        if s["district_style"] == style:
            return s
    return region["slots"][0]
