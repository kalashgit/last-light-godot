"""Canonical LAST LIGHT reusable refinement acceptance contract V2.

No Blender runtime dependency; Codex/CI can read this schema from anywhere.
The model, material and rendered sprite are separate artifacts and stage gates.
V2 rules apply to ALL families in the full census once it is reconciled.
"""
FAMILY_RULES={
 "version":"ll-full-fidelity-refinement-v2.0",
 "world_tile_px":[80,40],
 "environment_condition_levels":[0,1,2,3],
 "founder_reference":"Golden40 and Master Sprite Bible V2 original Grounded Pixel Realism",
 "locked_camera":"existing project instrumented 30deg elevation, 2:1 projection",
 "source_rights":"original artwork; external game imagery research-only",
 "source_replay":"never overwrite first-pass .blend/.glb; exact hashes/reversible upgrades",
 "category_rules":{
   "golden40":dict(skills=["LL-082","LL-083","LL-084","LL-085","LL-086","LL-087","LL-090","LL-095","LL-106","LL-111"],
     checks=["reference-specific silhouette identity","functional grip/cavity/neck/geometry",
             "original noncopied unseen geometry","readable native world/inventory pixel form"]),
   "catalog":dict(skills=["LL-082","LL-083","LL-084","LL-086","LL-090","LL-095","LL-106","LL-110"],
     checks=["distinct non-clone category silhouettes","appropriate physical dimensions",
             "real taper/closures/openings","source variant grammar supports 3 extremes"]),
   "furniture":dict(skills=["LL-082","LL-083","LL-084","LL-085","LL-088","LL-089","LL-097","LL-099"],
     checks=["genuine construction shell and thickness","separate functioning hinge and cavities",
             "cloth tension/cushion sag where applicable","proper seating/door clearance"]),
   "actor":dict(skills=["LL-082","LL-083","LL-084","LL-085","LL-092","LL-093","LL-094","LL-099"],
     checks=["anatomically plausible head/limb torso transitions","proper rig and bone weighting",
             "clothing layers follow pose","human zombie silhouettes distinct at world zoom"]),
   "vehicle":dict(skills=["LL-082","LL-083","LL-084","LL-085","LL-087","LL-091","LL-098","LL-107"],
     checks=["original chassis not stretched generic clone","roof/windshield curvature and rake",
             "wheelbase track arches proper contact","real door seams/window glass zones",
             "sixteen stable direction silhouettes"]),
 },
 "cross_cutting_skills":["LL-081","LL-104","LL-105","LL-108","LL-109","LL-110","LL-111",
                         "LL-112","LL-113","LL-114","LL-115","LL-116"],
 "acceptance":{
  "geometry":{"minimum":"editable Blender source, GLB reimport, physically interpretable parts",
      "tests":["bounds","transform scale","normals/topology","true hinges/cavity where required",
               "multiple calibrated silhouette views","visual comparison at game size"]},
  "material":{"minimum":"family-specific actual UV/PBR/mask recipes, verified material identity",
      "tests":["albedo","roughness","normal","wear zone","condition 0..3","native-scale readability"]},
  "render":{"minimum":"correct locked 2:1 projector, 2.5D original RGBA sprite",
      "tests":["anchor","alpha halo","shared crop","4/8/16 heading continuity",
               "native 100/220/325% readability"]},
  "gameplay":{"minimum":"real Godot interaction, collisions, inventory and persistence where applicable",
      "tests":["scene load","Y sort","reach/action queue","save reload","phone proof separately"]},
 }
}
STAGES=[
 {"id":"G0","meaning":"source provenance and stable canonical semantic asset ID"},
 {"id":"G1","meaning":"base editable 3D geometry/GLB with source hash"},
 {"id":"G2","meaning":"refined geometry passes independently measured scale and silhouette QA"},
 {"id":"M","meaning":"UV/material/PBR/condition stages validated without redoing good geometry"},
 {"id":"R","meaning":"fixed-isometric 2.5D pixels, transparency and multi-view atlas validated"},
 {"id":"V","meaning":"founder Golden visual sign-off, never automated by CI"},
 {"id":"E","meaning":"Godot asset integration and applicable gameplay E2E tested"},
 {"id":"D","meaning":"separate iPhone/Xogot real-device proof"},
]

def required_skills(job):
    name=job.get("category","")
    template=FAMILY_RULES["category_rules"].get(name)
    if template is None:raise ValueError("unknown source asset category "+name)
    return sorted(set(template["skills"]+FAMILY_RULES["cross_cutting_skills"]))

def defects_for(job):
    category=job.get("category")
    r=FAMILY_RULES["category_rules"].get(category)
    if r is None:raise ValueError("unmapped category "+str(category))
    checks=list(r["checks"])
    subtype=job.get("geometry_family","")
    if category=="catalog" and subtype in {"screwdriver","knife","chisel","crowbar","blade"}:
        checks.extend(["shaft/handle ratio","actual taper and material junction",
                       "small tip distinguishability at 32/48/64px"])
    if category=="vehicle":
        checks.append("each family validated across all sixteen fixed headings before Golden approval")
    if category=="furniture" and subtype in ("refrigerator","cabinet"):
        checks.extend(["hollow interior true geometry","hinge animation no self-interpenetration"])
    return checks
