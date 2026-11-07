"""Hatchback atlas checks independent of Blender; verify 16 headings and fixed world pivots."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"/"vehicle_factory"))
from pack import process

class GoldenVehicleV1(unittest.TestCase):
    def test_synthetic_sixteen_heading_pack(self):
        with tempfile.TemporaryDirectory() as d:
            raw=Path(d)/"raw";raw.mkdir()
            records=[]
            for i in range(16):
                im=Image.new("RGBA",(768,768),(0,0,0,0))
                ImageDraw.Draw(im).ellipse((255+i%4,260,490,500),fill=(100+i*5,135,120,255))
                name=f"heading_{i:02}.png"
                im.save(raw/name)
                records.append(dict(index=i,angle_deg=22.5*i,source_png=name,
                       fixed_world_pivot_px=[384,384],source_canvas_px=[768,768]))
            manifest=dict(schema_version=1,tile_px=[80,40],directions=16,
                          asset_id="ll_vehicle_hatchback_test",
                          original_source="original_source_test",
                          declared_dimensions_m=[3.86,1.69,1.46],wheelbase_m=2.48,
                          frames=records)
            (raw/"manifest.json").write_text(json.dumps(manifest))
            result=process(raw,Path(d)/"out")
            self.assertEqual(result["heading_count"],16)
            self.assertEqual(len(list((Path(d)/"out").glob("heading_*.png"))),16)
            self.assertTrue(result["anchor_px"][0]>0)
            self.assertEqual(Image.open(Path(d)/"out"/result["atlas"]).size,
                             (result["cell_px"][0]*4,result["cell_px"][1]*4))
            self.assertEqual(result["status"],"RENDERED_CANDIDATE_NOT_FOUNDER_APPROVED_NOT_GODOT_INTEGRATED")

    def test_no_missing_directions(self):
        with tempfile.TemporaryDirectory() as d:
            raw=Path(d)/"raw";raw.mkdir()
            frames=[]
            for i in range(15):
                im=Image.new("RGBA",(768,768),(0,0,0,0))
                ImageDraw.Draw(im).rectangle((270,280,490,490),fill=(160,190,115,255))
                im.save(raw/f"{i}.png")
                frames.append(dict(index=i,source_png=f"{i}.png",fixed_world_pivot_px=[384,384]))
            (raw/"manifest.json").write_text(json.dumps(dict(directions=16,tile_px=[80,40],frames=frames)))
            with self.assertRaises(ValueError):
                process(raw,Path(d)/"out")

if __name__=="__main__":
    unittest.main()
