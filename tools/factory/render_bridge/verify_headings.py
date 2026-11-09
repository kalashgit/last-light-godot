"""F12 directional coverage gate for sprite manifests.

Does not grant A00 approval; enforces consistent directional animation sets.
Each clip must contain every required direction and the same frame indices.
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

def verify_coverage(frames, headings=16):
    if type(headings) is not int or headings not in (1,4,8,16):
        raise ValueError("headings must be 1, 4, 8, or 16")
    if not isinstance(frames,list) or not frames:
        raise ValueError("empty frames")
    groups=defaultdict(lambda:defaultdict(set))
    seen=set()
    for f in frames:
        if not isinstance(f,dict):
            raise ValueError("invalid frame")
        clip=f.get("clip")
        direction=f.get("direction")
        index=f.get("frame_index")
        if not isinstance(clip,str) or not clip:
            raise ValueError("invalid clip")
        if type(direction) is not int or not 0<=direction<headings:
            raise ValueError("direction out of range")
        if type(index) is not int or index<0:
            raise ValueError("invalid frame_index")
        identity=(clip,direction,index)
        if identity in seen:
            raise ValueError("duplicate animation frame")
        seen.add(identity)
        groups[clip][direction].add(index)
    result={}
    for clip,directions in sorted(groups.items()):
        if set(directions)!=set(range(headings)):
            raise ValueError("incomplete headings for "+clip)
        expected=directions[0]
        if expected!=set(range(len(expected))):
            raise ValueError("noncontiguous frame indices for "+clip)
        for direction,indices in directions.items():
            if indices!=expected:
                raise ValueError("unequal animation frame coverage for "+clip)
        result[clip]={"headings":headings,"frames_per_heading":len(expected),
                      "total_frames":headings*len(expected)}
    return {"status":"DIRECTIONAL_COVERAGE_PASS_NOT_ASSET_APPROVAL","clips":result}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("manifest",type=Path)
    p.add_argument("--headings",type=int,default=16)
    a=p.parse_args()
    print(json.dumps(verify_coverage(json.loads(a.manifest.read_text())["frames"],a.headings),indent=2))

if __name__=="__main__":
    main()
