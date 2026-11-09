"""Create an isolated Godot project with only the three F09 baked GLBs and 48 sprites."""
import json
import shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/"build"/"f09_integration_fixture"
DST=ROOT/"build"/"f09_godot_stage"
IDS=("ll_tools_hand_saw","ll_tools_adjustable_wrench","ll_tools_socket_handle")
def main():
    DST.mkdir(parents=True,exist_ok=True)
    (DST/"project.godot").write_text(
        'config_version=5\n[application]\nconfig/name="F09 Isolated Candidate Gameplay QA"\n'
        '[rendering]\nrenderer/rendering_method="gl_compatibility"\n'
        'renderer/rendering_method.mobile="gl_compatibility"\n')
    (DST/"fixture.gd").write_text(
        (ROOT/"tools"/"weapons_tools"/"f09_godot_fixture.gd").read_text())
    # Reuse the real LAST LIGHT gameplay source, without changing it.
    # This is an isolated copy, not the main game's running scene.
    shutil.copytree(ROOT/"scripts",DST/"scripts",dirs_exist_ok=True)
    shutil.copytree(ROOT/"data",DST/"data",dirs_exist_ok=True)
    shutil.copyfile(ROOT/"main.tscn",DST/"main.tscn")
    (DST/"main_game_fixture.gd").write_text(
        (ROOT/"tools"/"weapons_tools"/"f09_main_game_fixture.gd").read_text())
    (DST/"f09_candidate_16_heading_atlas.png").write_bytes(
        (SRC/"f09_candidate_16_heading_atlas.png").read_bytes())
    (DST/"f09_candidate_16_heading_atlas.json").write_bytes(
        (SRC/"f09_candidate_16_heading_atlas.json").read_bytes())
    for ident in IDS:
        source=SRC/ident
        out=DST/"sprites"/ident
        out.mkdir(parents=True,exist_ok=True)
        for heading in range(16):
            name=f"h{heading:02}.png"
            shutil.copyfile(source/"world_sprite_96"/name,out/name)
        models=DST/"models"
        models.mkdir(exist_ok=True)
        shutil.copyfile(source/"preview_albedo_baked.glb",models/(ident+".glb"))
    (DST/"candidate_manifest.json").write_text(json.dumps({
        "status":"ISOLATED_GODOT_CANDIDATE_NOT_MAIN_GAME",
        "tools":list(IDS),"sprite_count":48,"baked_glbs":3},indent=2)+"\n")
    print("F09_GODOT_STAGE_PACK_PASS",DST,flush=True)
if __name__=="__main__":main()
