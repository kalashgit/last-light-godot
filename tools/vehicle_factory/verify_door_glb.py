"""Verify a real exported GLB contains an animated rotation track."""
import argparse
import json
import struct
from pathlib import Path


def audit(path):
    data=path.read_bytes()
    assert len(data)>20 and data[:4]==b"glTF"
    magic,version,total=struct.unpack_from("<III",data,0)
    assert version==2 and total==len(data)
    length,kind=struct.unpack_from("<II",data,12)
    assert kind==0x4E4F534A
    payload=json.loads(data[20:20+length].decode("utf-8"))
    animations=payload.get("animations",[])
    matches=[]
    for animation in animations:
        for channel in animation.get("channels",[]):
            if channel.get("target",{}).get("path")!="rotation":
                continue
            sampler=animation["samplers"][channel["sampler"]]
            key_count=payload["accessors"][sampler["input"]]["count"]
            if key_count>=5:
                matches.append({"animation":animation.get("name"),"keys":key_count})
    assert matches,"No >=5-key rotation animation in exported GLB"
    print("F10_HERO_GLB_ANIMATION_PASS",len(animations),matches)
    return matches


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("glb",type=Path)
    audit(parser.parse_args().glb)
