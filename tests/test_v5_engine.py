import hashlib, importlib.util, json, tempfile, unittest, zipfile, os
from pathlib import Path
from PIL import Image

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent if (HERE.parent/'tools'/'LAST_LIGHT_V5_MATERIAL_ENGINE.py').exists() else HERE
SOURCE=(ROOT/'tools'/'LAST_LIGHT_V5_MATERIAL_ENGINE.py') if (ROOT/'tools'/'LAST_LIGHT_V5_MATERIAL_ENGINE.py').exists() else (HERE/'LAST_LIGHT_V5_MATERIAL_ENGINE.py')
SPEC=importlib.util.spec_from_file_location('ll5',SOURCE)
mod=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(mod)
ZIP=Path(os.environ.get('LL_V4_CANDIDATE_ZIP', str((ROOT/'review/v4_benchmark_12/LAST_LIGHT_V4_BENCHMARK_12_CANDIDATES.zip') if (ROOT/'review/v4_benchmark_12/LAST_LIGHT_V4_BENCHMARK_12_CANDIDATES.zip').exists() else (HERE/'input/LAST_LIGHT_V4_BENCHMARK_12_CANDIDATES.zip'))))

class MaterialV5Test(unittest.TestCase):
 def test_all_twelve_alpha_and_distinct(self):
  fingerprints=set()
  with zipfile.ZipFile(ZIP) as z:
   for n in z.namelist():
    if not n.startswith('candidates/') or not n.endswith('.png'):continue
    with z.open(n) as f:original=Image.open(f).convert('RGBA')
    master,stats=mod.material_enhance_legacy(original,Path(n).stem)
    sprite=mod.nearest_export(master)
    mod.qa_png(sprite,orig=original)
    self.assertTrue(stats)
    fingerprints.add(hashlib.sha256(sprite.tobytes()).hexdigest())
  self.assertEqual(len(fingerprints),12)
 def test_deterministic_packaging(self):
  with tempfile.TemporaryDirectory() as t:
   dest=Path(t)
   a=mod.produce_from_zip(ZIP,dest)
   b=mod.produce_from_zip(ZIP,dest)
   self.assertEqual(a['sha256'],b['sha256'])
   self.assertEqual(a['count'],12)
   self.assertEqual(len(list((dest/'candidates_128').glob('*.png'))),12)
   self.assertEqual(len(list((dest/'candidates_64').glob('*.png'))),12)
   self.assertEqual(len(list((dest/'reviews').glob('*.png'))),6)
   with zipfile.ZipFile(dest/a['zip'].split('/')[-1]) as z:self.assertIsNone(z.testzip())
 def test_no_automatic_approval(self):
  with tempfile.TemporaryDirectory() as t:
   mod.produce_from_zip(ZIP,Path(t))
   data=json.loads((Path(t)/'manifest.json').read_text())
  self.assertEqual(data['founder_approved_count'],0)
  self.assertEqual(data['godot_integrated_count'],0)
  self.assertTrue(all(i['visual']=='candidate_reject_pending_founder_review' for i in data['items']))
 def test_recipe_renders_independent_transparent_asset(self):
  recipe={'id':'ll.prototype.original_ingot','size':[64,64],
          'approval':'candidate_needs_founder_review',
          'rights':'original_independent_design','materials':['steel','aluminum'],
          'layers':[
          {'name':'bottom','shape':'polygon','material':'steel','tone':1,'points':[[8,34],[49,26],[57,36],[52,53],[11,56]]},
          {'name':'top','shape':'polygon','material':'aluminum','tone':3,'points':[[8,34],[29,20],[49,26],[57,36],[36,39]]},
          {'name':'lip','shape':'line','material':'aluminum','tone':5,'points':[[9,34],[29,21],[48,27]]}]}
  pic=mod.nearest_export(mod.render_recipe(recipe))
  self.assertTrue(mod.qa_png(pic)['technical_valid'])
 def test_face_normal_and_wear_validation(self):
  mask=Image.new('L',(32,32),255); img=Image.new('RGBA',(32,32),(120,120,120,255))
  with self.assertRaises(ValueError):mod._material_pass(img,mask,'steel',42,face_normal=[0,0])
  with self.assertRaises(ValueError):mod._material_pass(img,mask,'steel',42,wear_state='stolen')
  with self.assertRaises(ValueError):mod._material_pass(img,mask,'steel',42,roughness=3)
 def test_authored_three_unique_originals(self):
  source=(ROOT/'data/factory/v5_authored_showcase_3.json') if (ROOT/'data/factory/v5_authored_showcase_3.json').exists() else (HERE/'data/v5_authored_showcase_3.json')
  with tempfile.TemporaryDirectory() as t:
   first=mod.produce_from_recipes(source,Path(t))
   second=mod.produce_from_recipes(source,Path(t))
   self.assertEqual(first['sha256'],second['sha256'])
   m=json.loads((Path(t)/'manifest.json').read_text())
   self.assertEqual(m['count'],3)
   self.assertEqual(m['founder_approved_count'],0)
   self.assertEqual(len(list((Path(t)/'candidates_128').glob('*.png'))),3)
   self.assertTrue(all(i['component_count']>=20 for i in m['items']))
   self.assertEqual(len(set(i['sha256'] for i in m['items'])),3)

 def test_authored_duplicate_ids_cannot_package(self):
  source=(ROOT/'data/factory/v5_authored_showcase_3.json') if (ROOT/'data/factory/v5_authored_showcase_3.json').exists() else (HERE/'data/v5_authored_showcase_3.json')
  payload=json.loads(source.read_text())
  payload['recipes'][1]['id']=payload['recipes'][0]['id']
  with tempfile.TemporaryDirectory() as t:
   target=Path(t)/'invalid.json'
   target.write_text(json.dumps(payload))
   with self.assertRaises(ValueError):mod.produce_from_recipes(target,Path(t)/'out')

 def test_mobile_one_file_no_arg_entrypoint(self):
  import subprocess,sys
  with tempfile.TemporaryDirectory() as tmp:
   home=Path(tmp)/'home'; home.mkdir()
   job=Path(tmp)/'job';job.mkdir()
   (job/'v5_authored_showcase_3.json').write_bytes(((ROOT/'data/factory/v5_authored_showcase_3.json') if (ROOT/'data/factory/v5_authored_showcase_3.json').exists() else (HERE/'data/v5_authored_showcase_3.json')).read_bytes())
   # The single-file script can run directly from a CodePad-writable folder.
   from shutil import copy2
   copy2(SOURCE,job/'LAST_LIGHT_V5_MATERIAL_ENGINE.py')
   env=dict(os.environ,HOME=str(home))
   result=subprocess.run([sys.executable,str(job/'LAST_LIGHT_V5_MATERIAL_ENGINE.py')],cwd=job,env=env,capture_output=True,text=True,timeout=20)
   self.assertEqual(result.returncode,0,result.stderr)
   self.assertTrue((home/'Documents/LAST_LIGHT_FACTORY/exports/LAST_LIGHT_V5_REVIEW_ONLY/manifest.json').is_file())

 def test_reject_invalid_approval(self):
  with self.assertRaises(ValueError):mod.render_recipe({'approval':'founder_approved','rights':'original_independent_design'})
 def test_source_unchanged(self):
  before=hashlib.sha256(ZIP.read_bytes()).hexdigest()
  with Image.open(mod.io.BytesIO(zipfile.ZipFile(ZIP).read('candidates/amethyst_crystal.png'))) as original:
   self.assertEqual(original.mode,'RGBA')
  self.assertEqual(before,hashlib.sha256(ZIP.read_bytes()).hexdigest())

if __name__=='__main__':unittest.main()
