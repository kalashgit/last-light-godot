"""Validate genuine Godot OpenGL captures from the isolated real house."""
import json
from pathlib import Path
from PIL import Image, ImageStat, ImageChops

ROOT=Path(__file__).resolve().parents[2]
SCREEN=ROOT/"build"/"f09_godot_stage"/"f09_graphical_qa"

def main():
    imgs=[]
    stats={}
    for filename in ("house_outdoor_actual.png","house_indoor_actual.png"):
        path=SCREEN/filename
        assert path.exists() and path.stat().st_size>=18000,filename
        image=Image.open(path).convert("RGB")
        assert image.width>=1000 and image.height>=650,(filename,image.size)
        thumb=image.resize((160,90),Image.Resampling.BOX)
        colors=thumb.getcolors(14400)
        distinct=len(colors) if colors else 14400
        assert distinct>=120,(filename,"image appears blank",distinct)
        std=ImageStat.Stat(thumb).stddev
        assert max(std)>=15,(filename,"no recognizable scene variation",std)
        imgs.append(image)
        stats[filename]={"dimensions":list(image.size),"unique_thumb_colors":distinct,
                         "rgb_stddev":[round(x,2) for x in std]}
    difference=ImageChops.difference(imgs[0],imgs[1])
    assert difference.getbbox() is not None,"indoor/outdoor are identical"
    (SCREEN/"visual_capture_qa.json").write_text(json.dumps({
        "status":"REAL_OPENGL_SOFTWARE_RENDER_UNAPPROVED",
        "render_target":"Xvfb Mesa Godot 4.3 GL compatibility, NOT iPhone",
        "screenshots":stats},indent=2)+"\n")
    print("F09_REAL_OPENGL_SCREENSHOT_QA_PASS 2 frames",flush=True)

if __name__=="__main__":main()
