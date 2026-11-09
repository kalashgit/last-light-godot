"""F12 sprite PNG quality gate: alpha, clipping, empty frames and pivot drift.

Static diagnostics only; not a substitute for art direction or Godot QA.
"""
import argparse
import json
from pathlib import Path
from PIL import Image

def inspect(manifest, source_dir, margin=2, max_anchor_drift=3):
    if type(margin) is not int or margin < 0:
        raise ValueError("invalid margin")
    if type(max_anchor_drift) not in (int,float) or max_anchor_drift < 0:
        raise ValueError("invalid drift threshold")
    frames=manifest.get("frames")
    if not isinstance(frames,list) or not frames:
        raise ValueError("empty manifest")
    source_dir=Path(source_dir)
    findings=[]
    centers=[]
    for f in frames:
        name=f.get("file")
        if not isinstance(name,str) or Path(name).name!=name or name in (".",".."):
            raise ValueError("unsafe file")
        with Image.open(source_dir/name) as img:
            if img.mode!="RGBA" or img.size!=(f["width"],f["height"]):
                raise ValueError("invalid RGBA dimensions")
            alpha=img.getchannel("A")
            bounds=alpha.getbbox()
            if bounds is None:
                findings.append({"key":f["key"],"code":"EMPTY_ALPHA"})
                continue
            left,top,right,bottom=bounds
            if left<margin or top<margin or right>img.width-margin or bottom>img.height-margin:
                findings.append({"key":f["key"],"code":"ALPHA_TOUCHES_SAFE_MARGIN","bbox":[left,top,right,bottom]})
            # The alpha-weighted centroid is a diagnostic, not a true ground anchor.
            weights=list(alpha.getdata())
            mass=sum(weights)
            cx=sum((i%img.width)*a for i,a in enumerate(weights))/mass
            cy=sum((i//img.width)*a for i,a in enumerate(weights))/mass
            centers.append((f["key"],cx,cy))
    # A rotating asymmetric asset naturally changes silhouette centroid. Report
    # variation for review, but do not incorrectly fail valid directional renders.
    drift=0.0
    if centers:
        mx=sum(v[1] for v in centers)/len(centers)
        my=sum(v[2] for v in centers)/len(centers)
        drift=max(((v[1]-mx)**2+(v[2]-my)**2)**0.5 for v in centers)
    return {"status":"PNG_QA_PASS" if not findings else "PNG_QA_FAIL",
            "frame_count":len(frames),"alpha_centroid_variation_px":round(drift,3),
            "alpha_centroid_warning":drift>max_anchor_drift,
            "centroid_is_not_ground_pivot":True,"findings":findings}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("manifest",type=Path)
    p.add_argument("--source-dir",type=Path,required=True)
    p.add_argument("--margin",type=int,default=2)
    args=p.parse_args()
    report=inspect(json.loads(args.manifest.read_text()),args.source_dir,args.margin)
    print(json.dumps(report,indent=2))
    if report["status"]!="PNG_QA_PASS":
        raise SystemExit(1)

if __name__=="__main__":
    main()
