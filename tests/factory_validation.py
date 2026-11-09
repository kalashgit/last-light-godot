"""Regression checks prove the validator rejects broken runtime exports."""
import copy, json, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class FactoryValidation(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(); self.folder=Path(self.temp.name)/'factory'
  shutil.copytree(ROOT/'assets/generated/factory',self.folder,ignore=shutil.ignore_patterns('*.import'))
  self.manifest=json.loads((self.folder/'manifest.json').read_text())
 def tearDown(self): self.temp.cleanup()
 def reject(self):
  (self.folder/'manifest.json').write_text(json.dumps(self.manifest))
  run=subprocess.run([sys.executable,str(ROOT/'tools/asset_factory/validate.py'),str(self.folder)],capture_output=True,text=True)
  self.assertNotEqual(run.returncode,0,'Invalid factory passed validation')
 def test_duplicate_id(self):
  self.manifest['objects'][1]['id']=self.manifest['objects'][0]['id']; self.reject()
 def test_incorrect_crop_anchor(self):
  self.manifest['objects'][0]['frames'][0]['anchor_px'][0]+=3; self.reject()
 def test_missing_sprite(self):
  (self.folder/self.manifest['objects'][0]['frames'][0]['file']).unlink(); self.reject()
 def test_duplicate_icon(self):
  first=next(f for f in self.manifest['objects'][0]['frames'] if f['mode']=='icon')
  second=next(f for f in self.manifest['objects'][1]['frames'] if f['mode']=='icon')
  shutil.copyfile(self.folder/first['file'],self.folder/second['file']); self.reject()
 def test_palette_outlier(self):
  from PIL import Image
  f=self.manifest['objects'][0]['frames'][0]
  image=Image.open(self.folder/f['file']); image.paste((255,0,255,255),(2,2,image.width-2,image.height-2)); image.save(self.folder/f['file']); self.reject()
if __name__=='__main__': unittest.main()
