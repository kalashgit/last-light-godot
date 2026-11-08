#!/usr/bin/env python3
"""Evidence-backed R04 decisions for a bounded 19-image inspection packet.

Run only with the downloaded research images present; no images enter the repo.
"""
import glob
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EVIDENCE = Path('/tmp/a00_visual_r04')
DECISIONS = {
    5812: ('ICON_ONLY_PARENT', 'alcohol_wipes', 'F09', 'Modern icon for a medical consumable; existing geometry aliases ll_medical_alcohol_wipes and ll_golden_alcohol_wipes require canonical ID reconciliation.'),
    23191: ('LEGACY_ICON_VARIANT', 'alcohol_wipes', 'F09', 'Old icon artwork of the same wipes concept; not a separate buildable model.'),
    116139: ('SHARED_OBJECT_MASTER', 'water_bottle', 'F09', 'Reusable bottle shape; content-level fluid quantity, label and liquid shader handled as state.'),
    6605: ('FILL_STATE', 'water_bottle', 'F09', 'Empty-bottle icon; shell remains same as bottle master.'),
    8156: ('FILL_STATE', 'water_bottle', 'F09', 'Full-bottle icon, same cap and silhouette as empty.'),
    2073: ('SHARED_OBJECT_MASTER', 'candle', 'F09', 'Unlit wax candle shape.'),
    2278: ('LIGHTING_BURN_STATE', 'candle', 'F09', 'Lit icon adds flame and illumination; not a second independent candle mesh.'),
    12507: ('MODEL_VIEW_PARENT', 'candle', 'F09', 'Reference render of candle, not a new game identity.'),
    2882: ('SHARED_OBJECT_MASTER', 'duffel_bag', 'F09', 'One bag silhouette with cloth, trim, handle and straps.'),
    115195: ('COLOR_VARIANT', 'duffel_bag', 'F09', 'Red cloth colorway on shared duffel shape.'),
    115225: ('COLOR_VARIANT', 'duffel_bag', 'F09', 'Blue cloth colorway on shared duffel shape.'),
    11393: ('COLOR_VARIANT', 'duffel_bag', 'F09', 'White cloth colorway, not a separate F05 geometry master; equipped presentation is an F05 dependent.'),
    11678: ('GEOMETRY_VARIANT', 'bookcase', 'F01', 'Ornate edge/frame bookshelf; one furniture family but variant geometry required.'),
    11679: ('GEOMETRY_VARIANT', 'bookcase', 'F01', 'Simple shelf design, geometry differs from ornate bookcase; same family with selectable mesh.'),
    9883: ('FURNITURE_MASTER_REPRESENTATION', 'filing_cabinet', 'F01', 'Three-drawer cabinet with storage and collision; correct F09 misrouting to furniture F01.'),
    1025: ('ITEM_ICON_PARENT', 'magazine', 'F09', 'Closed magazine/item icon, physical reading object.'),
    14687: ('OPEN_GEOMETRY_STATE', 'magazine', 'F09', 'Open spread model reference, dependent open geometry/state of reading item; not independent magazine master.'),
    115897: ('SHARED_OBJECT_MASTER', 'bucket', 'F09', 'Blue handled bucket form already admitted as ll_household_bucket.'),
    8136: ('FILL_STATE', 'bucket', 'F09', 'Empty bucket icon retains same shell and handle; fill condition belongs under admitted master.'),
}
NAMES = {
    5812:'AlcoholWipes.png',23191:'AlcoholWipes-old.png',116139:'WaterBottle.png',6605:'WaterBottle_Empty.png',8156:'WaterBottle_Full.png',
    2073:'Candle.png',2278:'CandleLit.png',12507:'Candle_Model.png',2882:'Duffelbag.png',115195:'DuffelBagRed.png',115225:'DuffelBagBlue.png',11393:'DuffelBagWhite.png',
    11678:'Bookcase1.png',11679:'Bookcase2.png',9883:'FilingCabinet2.png',1025:'Magazine.png',14687:'MagazineOpen_Model.png',115897:'Bucket.png',8136:'Bucket_Empty.png'
}

def main():
    source = {}
    for path in ROOT.glob('a00_20261108_b00*_*.jsonl'):
        for line in path.read_text(encoding='utf-8').splitlines():
            r=json.loads(line)
            if 'source_page_id' in r: source[r['source_page_id']]=r
    assert set(DECISIONS)==set(NAMES) and len(DECISIONS)==19
    rows=[]
    for i,(decision,root,family,why) in sorted(DECISIONS.items()):
        record=source[i]
        name=NAMES[i]
        binary=(EVIDENCE/name).read_bytes()
        assert binary[:4] in (b'\x89PNG',b'GIF8')
        rows.append({
            'schema':'A00_R04_VISUAL_EVIDENCE_V1','source_page_id':i,
            'source_title':record['source_title'],'source_url':record['source_url'],
            'image_sha256':hashlib.sha256(binary).hexdigest(),
            'visual_decision':decision,'provisional_semantic_root':root,
            'production_queue':family,'visual_reason':why,
            'review_method':'original wiki file-page image retrieved and visually inspected',
            'rights_cleared':False,'new_master_admitted':False,
            'golden_approved':False,'requires_registry_reconciliation':i in (5812,23191),
        })
    out=ROOT/'a00_r04_visual_decisions_19.jsonl'
    out.write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows),encoding='utf-8')
    print(f'R04: {len(rows)} retrieved images, {len({r["provisional_semantic_root"] for r in rows})} semantic families, SHA-256 evidence recorded')

if __name__=='__main__':main()
