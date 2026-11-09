"""Fail-closed visual-slot intake for the two newly recovered founder JPEGs.

A visual slot is only a reference pointer, NOT a unique model, canonical ID,
license, artistic approval, or authorization to reuse image pixels. The
coming Notion physical recipe is mandatory before original Blender modeling.
"""
import json,hashlib,argparse
from pathlib import Path
from PIL import Image

SHEETS={
  'UNMAPPED_50': {'filename':'founder_extra_50_cells_unmapped.jpeg','cols':10,'rows':5,'slot_count':50,
                  'sha256':'d53b35680feddc28314096eec987e310d3f65c17a44bbc65a2c2db691c4efa5f',
                  'numbering':'UNRESOLVED_ADDITIONAL_GRID'},
  'DENSE_200': {'filename':'founder_401_600_dense_overview.jpeg','cols':20,'rows':10,'slot_count':200,
                  'sha256':'7f03d66822e53d5bf0bc594763edee9d8b1d44931c0aee2334130f5f395d91b8',
                  'numbering':'VISUAL_ROUGH_401_TO_600_NEEDS_CANONICAL_RECONCILIATION'},
}

def intake(source:Path,output:Path):
    orders=[];report={'schema':'last-light.reference-supplement-queue.v1','source_sheet_count':2,
                     'status':'REFERENCE_ONLY_AWAITING_NOTION','model_count':0,'golden_3d_approved_count':0,
                     'total_reference_slots':0,'visual_slots_not_unique_models':True}
    for name,config in SHEETS.items():
        p=source/config['filename']
        if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=config['sha256']:
            raise ValueError('founder image source does not match exact original JPEG SHA: '+name)
        with Image.open(p) as im:
            if im.format!='JPEG' or im.size!=(1536,1024):raise ValueError('unexpected founder sheet size '+name)
            width,height=im.size
        cols,rows=config['cols'],config['rows']
        for i in range(config['slot_count']):
            x,y=i%cols,i//cols
            box=[int(width*x/cols),int(height*y/rows),int(width*(x+1)/cols),int(height*(y+1)/rows)]
            key=f'LL-SUP-20261110-{name}-{i+1:03}'
            orders.append({
                'schema':'last-light.reference-workorder.v1','reference_id':key,
                'image_path':'data/foundry_reference_catalog/supplement_20261110/'+config['filename'],
                'image_sha256':config['sha256'],'sheet_section':name,
                'cell_row':y,'cell_column':x,'cell_box_xyxy':box,'proposed_sequence_number':401+i if name=='DENSE_200' else None,
                'numbering_reliability':config['numbering'],'working_label':None,
                'canonical_notion_id':None,'canonical_recipe_status':'AWAITING_NOTION',
                'physical_unique_model_status':'UNVERIFIED_POSSIBLE_VARIANT_OR_DUPLICATE',
                'rights_reviewed':False,'source_pixels_reusable':False,
                'original_3d_model_built':False,'founder_golden_approved':False,
                'next_action':'Notion identity/physical-part recipe; rights and distinct-mesh review before Blender authoring'
            })
    if len(orders)!=250 or len({x['reference_id'] for x in orders})!=250:
        raise ValueError('supplemental reference slot count mismatch')
    output.mkdir(parents=True,exist_ok=True)
    (output/'supplemental_reference_queue.jsonl').write_text(''.join(json.dumps(x,sort_keys=True)+'\n' for x in orders))
    report['total_reference_slots']=len(orders)
    report['sections']={k:v['slot_count'] for k,v in SHEETS.items()}
    (output/'supplemental_intake_report.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    d=intake(a.source,a.output)
    print('LL_REFERENCE_SUPPLEMENTAL_QUEUE_PASS',json.dumps(d,sort_keys=True))