"""Actual filesystem-based F01 pilot QA; no claims of Golden approval."""
import json
import struct
import unittest
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/"build/f01_calibration"


class CalibrationOutputs(unittest.TestCase):
    def test_three_real_blend_and_glb_packages(self):
        for family,stem in (("refrigerator","refrigerator_refined_calibration"),
                            ("bookcase","bookcase_calibration"),
                            ("mattress","mattress_calibration")):
            with self.subTest(family=family):
                folder=BASE/family
                self.assertEqual((folder/(stem+".blend")).read_bytes()[:7],b"BLENDER")
                glb=(folder/(stem+".glb")).read_bytes()
                self.assertEqual(glb[:4],b"glTF")
                self.assertEqual(struct.unpack_from("<I",glb,8)[0],len(glb))
                manifest=json.loads((folder/"calibration_report.json").read_text())
                self.assertFalse("GOLDEN_APPROVED" == manifest.get("status"))
                self.assertGreaterEqual(len(manifest["sha256"]),3)

    def test_fridge_frame_coverage(self):
        folder=BASE/"refrigerator"
        frames=[folder/f"hinge_open_{i:02d}.png" for i in range(7)]
        self.assertTrue(all(p.stat().st_size>1000 for p in frames))
        self.assertEqual(len({p.read_bytes() for p in frames}),7)
        manifest=json.loads((folder/"calibration_report.json").read_text())
        self.assertEqual(manifest["frames"],7)
        self.assertEqual(manifest["hinge_range_deg"],[0,-105])

    def test_v3_material_hardware_and_interchange(self):
        for name,stem,minimum in (("refrigerator_v3","refrigerator_refined_calibration",30),
                                   ("bookcase_v3","bookcase_calibration",35)):
            with self.subTest(name=name):
                folder=BASE/name
                self.assertEqual((folder/(stem+".blend")).read_bytes()[:7],b"BLENDER")
                self.assertEqual((folder/(stem+".glb")).read_bytes()[:4],b"glTF")
                report=json.loads((folder/"calibration_report.json").read_text())
                self.assertGreaterEqual(report["mesh_count"],minimum)
        fridge=json.loads((BASE/"refrigerator_v3/calibration_report.json").read_text())
        self.assertEqual(fridge["door_meshes"],9)

    def test_refrigerator_atlas_metadata_and_alpha(self):
        folder=BASE/"refrigerator_v4_export"
        metadata=json.loads((folder/"atlas_metadata.json").read_text())
        image=Image.open(folder/metadata["atlas"]).convert("RGBA")
        self.assertEqual(metadata["status"],"INTERMEDIATE_ATLAS_NOT_F12_APPROVED")
        self.assertEqual(metadata["frame_count"],7)
        self.assertEqual(len(metadata["frames"]),7)
        self.assertEqual(metadata["frames"][0]["door_angle_deg"],0)
        self.assertEqual(metadata["frames"][-1]["door_angle_deg"],-105)
        self.assertFalse(metadata["godot_tested"])
        rectangles=[]
        for row in metadata["frames"]:
            r=row["rect_px"]
            self.assertEqual((r["w"],r["h"]),(512,512))
            self.assertEqual(row["pivot_px"],{"x":256,"y":256})
            self.assertLessEqual(r["x"]+r["w"],image.width)
            self.assertLessEqual(r["y"]+r["h"],image.height)
            rectangles.append((r["x"],r["x"]+r["w"]))
        for previous,current in zip(rectangles,rectangles[1:]):
            self.assertGreater(current[0]-previous[1],0)
        self.assertEqual(image.getpixel((image.width-1,image.height-1))[3],0)

    def test_static_family_atlases_have_no_invented_states(self):
        for family in ("bookcase","mattress"):
            with self.subTest(family=family):
                folder=BASE/(family+"_v4_export")
                data=json.loads((folder/"atlas_metadata.json").read_text())
                self.assertEqual(data["status"],"INTERMEDIATE_ATLAS_NOT_F12_APPROVED")
                self.assertEqual(len(data["frames"]),1)
                self.assertFalse(data["founder_approved"])
                self.assertFalse(data["godot_tested"])
                atlas=Image.open(folder/(family+"_single_frame_atlas.png")).convert("RGBA")
                self.assertEqual(atlas.size,(516,516))

    def test_v5_real_material_refinement_sources(self):
        for name,stem,minimum in (("refrigerator_v5","refrigerator_refined_calibration",36),
                                   ("bookcase_v5b","bookcase_calibration",39)):
            with self.subTest(name=name):
                folder=BASE/name
                self.assertEqual((folder/(stem+".blend")).read_bytes()[:7],b"BLENDER")
                self.assertEqual((folder/(stem+".glb")).read_bytes()[:4],b"glTF")
                data=json.loads((folder/"calibration_report.json").read_text())
                self.assertGreaterEqual(data["mesh_count"],minimum)
                self.assertFalse(data.get("founder_approved",False))

    def test_v6_glb_preserves_real_hinge_animation(self):
        path=BASE/"refrigerator_v6b/refrigerator_refined_calibration.glb"
        data=path.read_bytes()
        json_size=struct.unpack_from("<I",data,12)[0]
        gltf=json.loads(data[20:20+json_size])
        self.assertEqual(len(gltf.get("animations",[])),1)
        self.assertGreaterEqual(len(gltf["animations"][0]["channels"]),1)
        self.assertTrue(any("hinge_local.main_door" in n.get("name","") for n in gltf["nodes"]))
        report=json.loads((path.parent/"calibration_report.json").read_text())
        self.assertEqual(report["glb_animation_clips"],1)
        self.assertTrue(report["glb_hinge_pivot_exported"])


if __name__=="__main__":unittest.main()
