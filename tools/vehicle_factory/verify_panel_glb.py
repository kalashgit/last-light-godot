"""Validate genuine key times/angles on exported F10 bonnet and hatch GLBs."""
import argparse
import json
import math
import struct
from pathlib import Path

from verify_door_glb import accessor_floats
CLIPS={
    "bonnet":{"hinge":"F10 HERO bonnet rear transverse hinge PROTOTYPE","open_deg":56},
    "rear_hatch":{"hinge":"F10 HERO rear hatch roof transverse hinge PROTOTYPE","open_deg":70},
}


def audit(path:Path,clip:str):
    params=CLIPS[clip]
    data=path.read_bytes()
    assert data[:4]==b"glTF"
    assert struct.unpack_from("<I",data,8)[0]==len(data)
    length,kind=struct.unpack_from("<II",data,12)
    assert kind==0x4E4F534A
    document=json.loads(data[20:20+length])
    offset=20+length
    binary_length,binary_kind=struct.unpack_from("<II",data,offset)
    assert binary_kind==0x004E4942
    binary=data[offset+8:offset+8+binary_length]
    target=[i for i,node in enumerate(document.get("nodes",[]))
            if node.get("name")==params["hinge"]]
    assert len(target)==1, f"Hinge node missing for {clip}"
    expected=(0,params["open_deg"]*.33,params["open_deg"]*.67,
              params["open_deg"],params["open_deg"])
    matches=[]
    for animation in document.get("animations",[]):
        for channel in animation["channels"]:
            if channel["target"]!={"node":target[0],"path":"rotation"}:
                continue
            sampler=animation["samplers"][channel["sampler"]]
            times=[x[0] for x in accessor_floats(document,binary,sampler["input"])]
            quats=accessor_floats(document,binary,sampler["output"])
            assert len(times)==len(quats) and len(times)>=5
            assert abs(times[-1]-times[0]-.4)<.015
            angles=[]
            for frame,expect in enumerate(expected):
                at=min(range(len(times)),key=lambda i:abs(times[i]-(times[0]+frame*.1)))
                assert abs(times[at]-(times[0]+frame*.1))<.015
                x,y,z,w=quats[at]
                length=math.sqrt(x*x+y*y+z*z+w*w)
                assert abs(length-1)<.01
                # Blender's transverse Y axis becomes a glTF Z axis.
                assert abs(x)<.025 and abs(y)<.025
                angle=math.degrees(2*math.atan2(abs(z),abs(w)))
                assert abs(angle-expect)<2.5,(clip,frame,angle,expect)
                angles.append(round(angle,2))
            matches.append({"clip":clip,"angles_deg":angles,"duration_s":.4})
    assert len(matches)==1,f"Missing unique {clip} hinge animation"
    print("F10_PANEL_GLB_PASS",json.dumps(matches[0]))
    return matches[0]


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--clip",required=True,choices=list(CLIPS))
    p.add_argument("glb",type=Path)
    args=p.parse_args()
    audit(args.glb,args.clip)
