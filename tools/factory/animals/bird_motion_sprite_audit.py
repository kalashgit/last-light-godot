"""Independent image QA for eight-heading, four-phase noncanonical bird gait.

Checks actual Blender-written RGBA pixels, silhouette changes, and stable
on-canvas bounds. This is not a substitute for visual/Golden approval.
"""
import json
import os
import sys
from PIL import Image, ImageChops

src=os.path.abspath(sys.argv[1])
dst=os.path.abspath(sys.argv[2])
os.makedirs(dst,exist_ok=True)
frames=(1,5,9,13)
metrics={}
for heading in range(8):
    masks=[]
    boxes=[]
    dimensions=[]
    for frame in frames:
        path=os.path.join(src,'bird_heading_%02d_f%02d.png'%(heading,frame))
        image=Image.open(path)
        dimensions.append((image.size,image.mode))
        mask=image.convert('RGBA').getchannel('A').point(lambda a:255 if a>20 else 0)
        masks.append(mask)
        boxes.append(mask.getbbox())
    ratios=[]
    for idx in range(4):
        difference=ImageChops.difference(masks[idx],masks[(idx+1)%4])
        changed=difference.histogram()[255]
        union=sum(1 for a,b in zip(masks[idx].getdata(),masks[(idx+1)%4].getdata())
                  if a or b)
        ratios.append(round(changed/max(1,union),5))
    metrics['%02d'%heading]={
        'images':len(frames),'dimensions_and_modes':dimensions,
        'bbox':boxes,'phase_change_ratios':ratios,
        'all_frames_change':all(d>.006 for d in ratios),
        'all_bbox_on_canvas':all(b and b[0]>1 and b[1]>1 and b[2]<191 and b[3]<191 for b in boxes),
        'all_rgba_192':all(item==((192,192),'RGBA') for item in dimensions),
    }
checks={'eight_headings':len(metrics)==8,
        'thirty_two_rgba_frames':all(m['all_rgba_192'] for m in metrics.values()),
        'gait_changes_visible_all_headings':all(m['all_frames_change'] for m in metrics.values()),
        'sprite_within_frame':all(m['all_bbox_on_canvas'] for m in metrics.values())}
report={'identity':'NONCANONICAL_VISUAL_CALIBRATION_ONLY',
        'headings':metrics,'checks':checks,'passed':all(checks.values())}
with open(os.path.join(dst,'bird_motion_sprite_audit.json'),'w') as f:
    json.dump(report,f,indent=2)
print('F07_BIRD_MOTION_IMAGE_QA',json.dumps(checks),'passed=',report['passed'])
if '--strict' in sys.argv and not report['passed']:sys.exit(2)
