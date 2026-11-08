# F01 V4 — Intermediate atlas and metadata export

**Executed**, candidate-only factory interoperability checkpoint. F01 did not change Notion's canonical registry, amend W05/W07 contracts, overwrite 360 sources or edit the playable Godot map.

## Output

- Refrigerator: 7 real source PNG frames → fixed 3640×516 RGBA atlas with 2px edge extrusion, 4px spacing, individual frame bounds, stable untrimmed origin pivot proposal (256,256), proposed 75ms/frame and 0 to −105° hinge angles.
- Bookcase: one actual 512² RGBA frame → 516² padded RGBA atlas, one verified source hash and storage/occlusion metadata proposal.
- Mattress: one actual 512² RGBA frame → 516² padded RGBA atlas, one verified source hash and movable sleep-surface metadata proposal.
- All metadata says **INTERMEDIATE_ATLAS_NOT_F12_APPROVED**, retains A00 Content ID and source revision, and keeps `Godot Tested` and founder sign-off false.
- 128×128 fridge diagnostic is an unapproved readability sample, not an assumed native-resolution game sprite.

## Reproduce and test

```bash
python tools/factory/furniture/pack_f01_frames.py --frames build/f01_calibration/refrigerator_v3 --output build/f01_calibration/refrigerator_v4_export
python tools/factory/furniture/pack_static_f01.py --family bookcase --source build/f01_calibration/bookcase_v3/bookcase_empty_world.png --output build/f01_calibration/bookcase_v4_export
python tools/factory/furniture/pack_static_f01.py --family mattress --source build/f01_calibration/mattress/mattress_world.png --output build/f01_calibration/mattress_v4_export
python -m unittest discover -s tests/factory/furniture -v
```

Source tests check alpha, uncut silhouettes, distinct fridge frames, atlas bounds, nonoverlap, pivot invariance and explicitly unapproved statuses. Run the existing 360-source inventory independently as well.

## Outstanding blocking QA

1. F12 must verify native scale, pixel finishing, crop/anchor coordinates, atlas conventions and alpha edge handling. This packer is a compatible **proposal**, not the F12 shared standard.
2. W05/W07 must review the door swing collision shape, event timing, storage-access enablement and persisted mechanical state.
3. F11 must validate original PBR surface quality, true UV/bake channels and controlled wear; material simplification is obvious in native-size views.
4. W09 independent technical QA, founder Golden visual approval, Godot integration and physical iPhone/Xogot testing are absent.
5. A00 requires a frozen reviewed work-order snapshot and source/rights gate for canonical release. The source images that inspired the taxonomy are not imported or redistributed.
