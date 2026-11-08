"""Synthetic and adversarial tests for A00 R04. No external assets or art needed."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from gate_v2 import COHORT, GateError, check, receipts

class GateContract(unittest.TestCase):
 def setUp(self):
  t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);p=Path(t.name)
  self.queue=p/'queue.json';self.geom=p/'geom.json';self.handoff=p/'handoff.jsonl';self.receipt=p/'receipt.jsonl'
  ids=sorted(COHORT)
  self.models=[{'asset_id':i,'glb_sha256':hashlib.sha256(i.encode()).hexdigest(),'actual_bounds_m':[.2,.4,.6]} for i in ids]
  self.models +=[{'asset_id':f'fake_{i}','glb_sha256':'0'*64,'actual_bounds_m':[1,1,1]} for i in range(345)]
  self.geometry={'generated_3d_source_count':360,'source_plan_unique_count':360,'items':self.models}
  self.orders=[]
  sha_map={x['asset_id']:x['glb_sha256'] for x in self.models}
  for i,master in enumerate(ids):
   fam='F01' if master.startswith('ll_furniture_') else 'F09'
   self.orders.append(dict(master_id=master,queue=fam,work_order_id=f'A00-R03-{fam}-{master}-v1',priority='P0',existing_geometry_id=master,notion_semantic_verification='Canonical Verified',classification_admission='EXISTING_A00_CANONICAL_VERIFIED_ID',dispatch_permission='ORIGINAL_REFINEMENT_AND_TECHNICAL_SOURCE_QA_ONLY',machine_worker_start_allowed=True,source_rights='THE_INDIE_STONE_COPYRIGHT__RESEARCH_ONLY__NO_DIRECT_REUSE',source_page_status='HTTP_200_TITLE_AND_FILE_METADATA_CHECKED_2026_11_09',notion_url=f'https://app.notion.com/p/{i:032x}',source_page_url=f'https://pzwiki.net/wiki/File:{i}.png',source_image_link_research_only=f'https://pzwiki.net/w/images/{i}.png',source_reference_ids_raw=str(i),geometry_source_manifest_sha256=sha_map[master],geometry_source_bounds_m=[.2,.4,.6],quality_focus='An original reference silhouette and rig validation contract',cross_family_dependencies='F12 and W01',validation_before_release=['technical','render','materials','visual','engine','device','rights'],**{k:False for k in ('source_pixel_comparison_verified','geometry_image_comparison_verified','rights_reviewed','founder_visual_approved','technical_qa_passed','godot_tested','iphone_verified','canonical_new_id_created')}))
  self.orders.sort(key=lambda x:(x['queue'],x['priority'],x['master_id']))
  self.matrix=[{'queue':f'F{i:02d}','dispatched_master_ids':[x['master_id'] for x in self.orders if x['queue']==f'F{i:02d}'],'dispatch_count':sum(x['queue']==f'F{i:02d}' for x in self.orders)} for i in range(1,13)]
  self.family=[{'family':f'F{i:02d}','direct_master_count':sum(x['queue']==f'F{i:02d}' for x in self.orders),'tasks':[{'task':'ORIGINAL_GEOMETRY_AND_MATERIAL_REFINEMENT','master_id':x['master_id']} for x in self.orders if x['queue']==f'F{i:02d}'],'release_authorized':False,'may_invent_canonical_ids':False} for i in range(1,13)]
  self.p={'schema':'A00_PRODUCTION_ADMISSION_R03_V1','source_index_count':21025,'source_r02_count':6072,'geometry_source_count':360,'already_verified_a00_masters_at_review':22,'dispatch_total':15,'no_merge_no_deploy':True,'work_orders':self.orders,'queue_matrix':self.matrix}
  self.save()
 def save(self):
  self.queue.write_text(json.dumps(self.p));self.geom.write_text(json.dumps(self.geometry));self.handoff.write_text('\n'.join(map(json.dumps,self.family))+'\n')
 def verify(self):return check(self.queue,self.geom,self.handoff)
 def test_valid_queue(self):self.assertEqual(len(self.verify()),15)
 def test_geometry_tamper(self):
  self.orders[0]['geometry_source_manifest_sha256']='f'*64;self.save()
  with self.assertRaises(GateError):self.verify()
 def test_invented_id(self):
  self.orders[0]['master_id']='ll_fake';self.save()
  with self.assertRaises(GateError):self.verify()
 def test_not_golden(self):
  self.orders[0]['founder_visual_approved']=True;self.save()
  with self.assertRaises(GateError):self.verify()
 def test_family_injection(self):
  self.family[2]['tasks'].append({'task':'ORIGINAL_GEOMETRY_AND_MATERIAL_REFINEMENT','master_id':'ll_tools_hand_saw'});self.save()
  with self.assertRaises(GateError):self.verify()
 def test_rights_boundary(self):
  self.orders[0]['source_rights']='REUSE_ALLOWED';self.save()
  with self.assertRaises(GateError):self.verify()
 def test_receipt_never_approves(self):
  o=self.orders[0]
  a={'schema':'A00_WORKER_REFINEMENT_RECEIPT_V1','master_id':o['master_id'],'work_order_id':o['work_order_id'],'family':o['queue'],'input_glb_sha256':o['geometry_source_manifest_sha256'],'output_glb_sha256':'a'*64,'status':'SUBMITTED_FOR_INDEPENDENT_QA','evidence':{k:'artifacts/x' for k in ('original_blend_path','original_glb_path','render_contact_sheet_path','material_report_path','scale_collision_report_path')},**{k:False for k in ('rights_approval','golden_approval','technical_qa_passed','godot_tested','iphone_verified')}}
  self.receipt.write_text(json.dumps(a)+'\n');self.assertEqual(receipts(self.receipt,self.verify()),1)
  a['golden_approval']=True;self.receipt.write_text(json.dumps(a)+'\n')
  with self.assertRaises(GateError):receipts(self.receipt,self.verify())

if __name__=='__main__':unittest.main()
