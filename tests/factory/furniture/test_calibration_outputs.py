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

    def test_isolated_godot_fixture_is_ready_but_not_executed(self):
        fixture=Path(__file__).resolve().parent/"godot_fixture"
        self.assertTrue((fixture/"project.godot").is_file())
        self.assertTrue((fixture/"main.tscn").is_file())
        source=(fixture/"verify_import.gd").read_text()
        self.assertIn("F01_GODOT_GLTF_IMPORT_PASS",source)
        self.assertIn("AnimationPlayer",source)
        self.assertFalse((fixture/"model.glb").exists(),"fixture source must not be committed as final game asset")

    def test_v8_hollow_fridge_and_independent_drawer_rig(self):
        folder=BASE/"refrigerator_v8b"
        report=json.loads((folder/"calibration_report.json").read_text())
        self.assertGreaterEqual(report["mesh_count"],70)
        self.assertEqual(report["crisper_tray_meshes"],7)
        self.assertEqual(report["crisper_slide_travel_proposed_m"],.19)
        self.assertEqual(report["checks"]["closed_door_raycast"],"door.enamel_panel")
        self.assertEqual(report["checks"]["open_cavity_raycast"],"liner.back")
        self.assertTrue(report["glb_hinge_pivot_exported"])
        data=(folder/"refrigerator_refined_calibration.glb").read_bytes()
        gltf=json.loads(data[20:20+struct.unpack_from("<I",data,12)[0]])
        self.assertEqual(len(gltf["animations"]),1)
        self.assertTrue(any(n.get("name")=="slide_local.crisper_drawer" for n in gltf["nodes"]))
        self.assertTrue(any(n.get("name")=="hinge_local.main_door" for n in gltf["nodes"]))

    def test_v8_native_scale_alpha_and_contact_sheet(self):
        folder=BASE/"refrigerator_v8b"
        report=json.loads((folder/"render_qa.json").read_text())
        self.assertEqual(report["frame_count"],7)
        self.assertGreaterEqual(min(report["clear_margins_px"]),12)
        self.assertTrue(report["adjacent_frames_visibly_distinct"])
        with Image.open(folder/"qa_contact_sheet_v8.png") as sheet:
            self.assertEqual(sheet.size,(1708,584))

    def test_v9_original_pbr_images_export_to_glb(self):
        folder=BASE/"refrigerator_v9c"
        manifest=json.loads((folder/"calibration_report.json").read_text())
        self.assertGreaterEqual(manifest["portable_texture_count"],2)
        self.assertEqual(len(manifest["original_texture_images"]),2)
        self.assertIn("NOT_F11_VALIDATED",manifest["material_finish"])
        for name in manifest["original_texture_images"]:
            path=folder/name
            with Image.open(path) as texture:
                self.assertEqual(texture.size,(256,256))
                extrema=texture.convert("RGB").getextrema()
                self.assertTrue(all(low>50 and high-low>0 for low,high in extrema),
                                "Black/constant texture is not a portable PBR material")
        glb=(folder/"refrigerator_refined_calibration.glb").read_bytes()
        gltf=json.loads(glb[20:20+struct.unpack_from("<I",glb,12)[0]])
        self.assertGreaterEqual(len(gltf.get("textures",[])),2)
        self.assertGreaterEqual(len(gltf.get("images",[])),2)
        self.assertTrue(all(any("TEXCOORD_0" in p.get("attributes",{}) for p in mesh["primitives"])
                            for mesh in gltf["meshes"]))
        self.assertEqual(len(gltf["animations"]),1)
        visual=json.loads((folder/"render_qa.json").read_text())
        self.assertGreaterEqual(min(visual["clear_margins_px"]),12)

    def test_v10_independent_animations_and_full_material_portability(self):
        folder=BASE/"refrigerator_v10"
        manifest=json.loads((folder/"calibration_report.json").read_text())
        self.assertEqual(manifest["crisper_frames"],7)
        self.assertTrue(manifest["freezer_hinge_present"])
        self.assertEqual(set(manifest["animation_clip_names"]),{"F01_Door_Open","F01_Crisper_Open"})
        self.assertEqual(len(manifest["original_texture_images"]),18)
        for name in manifest["original_texture_images"]:
            with Image.open(folder/name) as pbr:
                self.assertGreater(min(v[0] for v in pbr.convert("RGB").getextrema()),6)
        glb=(folder/"refrigerator_refined_calibration.glb").read_bytes()
        gltf=json.loads(glb[20:20+struct.unpack_from("<I",glb,12)[0]])
        self.assertEqual({clip["name"] for clip in gltf["animations"]},
                         {"F01_Door_Open","F01_Crisper_Open"})
        self.assertGreaterEqual(len(gltf["images"]),18)
        self.assertTrue(any(n.get("name")=="hinge_local.freezer_flap" for n in gltf["nodes"]))

    def test_v10_crisper_frames_change_in_rgb_even_when_alpha_is_static(self):
        from PIL import ImageChops
        folder=BASE/"refrigerator_v10"
        frames=[Image.open(folder/f"crisper_open_{i:02d}.png").convert("RGBA") for i in range(7)]
        for left,right in zip(frames,frames[1:]):
            self.assertIsNotNone(ImageChops.difference(left.convert("RGB"),right.convert("RGB")).getbbox())
        report=json.loads((folder/"render_qa_crisper.json").read_text())
        self.assertEqual(report["motion"],"crisper_open")
        self.assertTrue(report["adjacent_frames_visibly_distinct"])
        source=(Path(__file__).resolve().parent/"godot_fixture/verify_import.gd").read_text()
        self.assertIn("F01_GODOT_INTERACTION_PASS",source)
        self.assertIn("door_move_during_drawer",source)


if __name__=="__main__":unittest.main()
