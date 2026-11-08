"""Pack F07 NONCANONICAL render studies and perform image-level checks.

Run: python tools/factory/animals/pack_calibration.py /absolute/output/directory
"""
import hashlib
import json
import sys
from pathlib import Path
from PIL import Image, ImageDraw

root = Path(sys.argv[1]).resolve()
frames_dir = root / 'frames'
poses = ('idle', 'walk_a', 'walk_b')
manifest = {'status':'NONCANONICAL_CALIBRATION_ONLY','species':{},'image_checks':{}}
preview = Image.new('RGBA',(8*120,6*120),(54,57,52,255))
for si,species in enumerate(('cow','chicken')):
    atlas = Image.new('RGBA',(8*256,3*256),(0,0,0,0))
    entries=[]
    for row,pose in enumerate(poses):
        for heading in range(8):
            file=frames_dir/f'{species}_{heading:02d}_{pose}.png'
            with Image.open(file) as im:
                image=im.convert('RGBA')
            assert image.size==(256,256),str(file)
            alpha=image.getchannel('A')
            bbox=alpha.getbbox()
            assert bbox is not None, f'blank image {file}'
            # Distinguish camera framing from physical contact/pivot acceptance.
            assert bbox[0]>0 and bbox[1]>0 and bbox[2]<256 and bbox[3]<256, f'cropped {file}: {bbox}'
            atlas.alpha_composite(image,(heading*256,row*256))
            preview.alpha_composite(image.resize((120,120),Image.Resampling.LANCZOS),(heading*120,(si*3+row)*120))
            entries.append({'name':file.name,'rect':[heading*256,row*256,256,256],
                            'heading_index':heading,'pose':pose,'alpha_bbox':list(bbox),
                            'ground_anchor_status':'UNVERIFIED_F12','foot_contact_status':'UNVERIFIED_IK'})
    path=root/f'{species}_calibration_atlas.png'
    atlas.save(path,optimize=True)
    manifest['species'][species]={'atlas':path.name,'frame_count':len(entries),'frames':entries,
                                   'atlas_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    manifest['image_checks'][species]={'dimensions_pass':True,'alpha_nonempty_pass':True,'cropping_pass':True,
                                       'native_iPhone_readability':'NOT_RUN','foot_plant':'NOT_RUN'}
preview.save(root/'calibration_contact_sheet.png',optimize=True)
(root/'atlas_manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({s:manifest['species'][s]['frame_count'] for s in manifest['species']}))
