"""Verify an exported GLB plays the actual F10 door-hinge motion."""
import argparse
import json
import math
import struct
from pathlib import Path

HINGE="F10 HERO driver door vertical hinge PROTOTYPE"


def accessor_floats(document,binary,index):
    accessor=document["accessors"][index]
    assert accessor["componentType"]==5126, "Expected float animation data"
    width={"SCALAR":1,"VEC4":4}[accessor["type"]]
    view=document["bufferViews"][accessor["bufferView"]]
    assert view.get("buffer",0)==0 and "sparse" not in accessor
    stride=view.get("byteStride",4*width)
    offset=view.get("byteOffset",0)+accessor.get("byteOffset",0)
    output=[]
    for i in range(accessor["count"]):
        at=offset+stride*i
        assert at+4*width<=len(binary), "Animation accessor out of bounds"
        output.append(struct.unpack_from("<"+"f"*width,binary,at))
    return output


def z_rotation_deg(quaternion):
    x,y,z,w=quaternion
    length=math.sqrt(sum(v*v for v in quaternion))
    assert length>.99 and abs(x/length)<.03 and abs(y/length)<.03
    return (math.degrees(2*math.atan2(z,w))%360)


def audit(path):
    data=path.read_bytes()
    assert len(data)>28 and data[:4]==b"glTF"
    magic,version,total=struct.unpack_from("<III",data,0)
    assert version==2 and total==len(data)
    at=12
    chunks={}
    while at<len(data):
        length,kind=struct.unpack_from("<II",data,at)
        at+=8
        assert at+length<=len(data)
        chunks[kind]=data[at:at+length]
        at+=length
    payload=json.loads(chunks[0x4E4F534A])
    binary=chunks[0x004E4942]
    nodes=payload.get("nodes",[])
    hinge_nodes=[i for i,n in enumerate(nodes) if n.get("name")==HINGE]
    assert len(hinge_nodes)==1, "F10 hinge node missing or duplicated"
    animations=payload.get("animations",[])
    matches=[]
    for animation in animations:
        for channel in animation.get("channels",[]):
            target=channel.get("target",{})
            if target.get("path")!="rotation" or target.get("node")!=hinge_nodes[0]:
                continue
            sampler=animation["samplers"][channel["sampler"]]
            times=[t[0] for t in accessor_floats(payload,binary,sampler["input"])]
            angles=[z_rotation_deg(q) for q in accessor_floats(payload,binary,sampler["output"])]
            assert len(times)>=5 and len(times)==len(angles)
            assert times[0]<.015 and times[-1]>=.39
            assert all(b>a for a,b in zip(times,times[1:]))
            for frame,expected in enumerate((0,22,44,66,66)):
                desired=frame*.1
                nearest=min(range(len(times)),key=lambda i:abs(times[i]-desired))
                assert abs(times[nearest]-desired)<.015, f"No hinge sample at {desired}s"
                delta=((angles[nearest]-expected+180)%360)-180
                assert abs(delta)<3, f"At {desired}s hinge angle is {angles[nearest]:.1f} instead of {expected}"
            matches.append({"animation":animation.get("name"),"keys":len(times),
                            "duration_s":round(times[-1]-times[0],3),
                            "angles_deg":[round(x,2) for x in angles]})
    assert matches,"No verified F10 driver-hinge rotation animation in GLB"
    print("F10_HERO_GLB_ANIMATION_PASS",json.dumps(matches))
    return matches


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("glb",type=Path)
    audit(parser.parse_args().glb)
