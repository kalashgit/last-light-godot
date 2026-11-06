"""LAST LIGHT Master Factory tests. Run: python TEST_MASTER_FACTORY.py -v"""
from __future__ import annotations
import csv
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

SRC=Path(__file__).with_name('LAST_LIGHT_MASTER_FACTORY.py')
spec=importlib.util.spec_from_file_location('ll_master',SRC)
ll=importlib.util.module_from_spec(spec)
spec.loader.exec_module(ll)
Image,_=ll.optional_pillow()

class WorldTests(unittest.TestCase):
    def test_determinism_across_restart(self):
        c1=ll.generate_chunk(1,-2,1234)
        c2=ll.generate_chunk(1,-2,1234)
        self.assertEqual(ll.pretty(c1),ll.pretty(c2))
    def test_distinct_seed(self):
        a=ll.generate_chunk(1,1,777)
        b=ll.generate_chunk(1,1,778)
        self.assertNotEqual(ll.canonical(a),ll.canonical(b))
    def test_large_coordinates(self):
        for x,y in ((-99999,99999),(1_000_000,-1_000_000)):
            ll.validate_chunk(ll.generate_chunk(x,y,999))
    def test_all_positions_and_unique_ids(self):
        for cx,cy in ((0,0),(1,1),(2,0),(-3,4),(6,2)):
            c=ll.generate_chunk(cx,cy,20261106)
            ll.validate_chunk(c)
            self.assertEqual(len(c['terrain_codes']),ll.CHUNK_SIZE)
            self.assertEqual(len(c['lots']),len(c['buildings']))
    def test_road_edge_global_identity(self):
        # Same global point has identical terrain whether sampled from neighboring chunks.
        seed=1234
        a=ll.generate_chunk(0,0,seed)
        b=ll.generate_chunk(1,0,seed)
        for y in range(ll.CHUNK_SIZE):
            self.assertEqual(ll.terrain_kind(47,y,seed),a['material_keys'][str(a['terrain_codes'][y][-1])])
            self.assertEqual(ll.terrain_kind(48,y,seed),b['material_keys'][str(b['terrain_codes'][y][0])])
    def test_region_modes_are_not_all_same(self):
        zones={ll.region_at(x,y,2026)['zone'] for x,y in [(-230,90),(-50,80),(72,72),(140,72),(400,-200),(310,110)]}
        self.assertGreaterEqual(len(zones),4)
        self.assertIn('downtown',zones)
    def test_world_repair_after_corruption(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            a=ll.compile_region(root,123,(0,0),(2,2),preview=False)
            self.assertEqual(a['generated_chunks'],4)
            self.assertEqual({x['status'] for x in a['chunks']},{'written'})
            b=ll.compile_region(root,123,(0,0),(2,2),preview=False)
            self.assertEqual({x['status'] for x in b['chunks']},{'reused'})
            target=root/b['chunks'][0]['file']
            target.write_bytes(b'not json')
            c=ll.compile_region(root,123,(0,0),(2,2),preview=False)
            self.assertEqual(sum(x['status']=='written' for x in c['chunks']),1)
            self.assertTrue(ll.verify_world(root)['technical_qa_passed'])
    def test_invalid_chunk_rejected(self):
        c=ll.generate_chunk(0,0,123)
        c['terrain_codes'][0]=[]
        with self.assertRaises(ValueError):ll.validate_chunk(c)
    def test_batch_limit(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaisesRegex(ValueError,'50,000'):
                ll.compile_region(Path(t),123,(0,0),(300,300),preview=False)

class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.cat=ll.Catalog(self.root/'catalog.sqlite3')
    def tearDown(self):
        self.cat.close();self.temp.cleanup()
    def sample(self):
        return {'id':'ll.original.test-can','name':'Original can','kind':'item','category':'food',
                'description':'cylindrical tin can with folded metallic rim', 'archetype':'can',
                'provenance':'original_internal','approved_original_recipe':True,'rights':'original'}
    def test_record_status(self):
        self.cat.upsert(self.sample());self.cat.db.commit()
        self.assertEqual(self.cat.report()['by_disposition']['ready_for_generation'],1)
        self.assertEqual(len(self.cat.pending(200)),1)
    def test_reference_not_generated(self):
        src={'reference_file':'SyringeEmpty.png','source_index':3801,
             'reference_source_url':'https://pzwiki.net/wiki/File:SyringeEmpty.png',
             'reference_image_url':'https://pzwiki.net/w/images/2/2b/SyringeEmpty.png'}
        self.cat.upsert(src);self.cat.db.commit()
        self.assertEqual(self.cat.report()['reference_source_sets']['pzwiki_item_icons']['indexed'],1)
        self.assertFalse(self.cat.pending(5))
    def test_invalid_source_id(self):
        with self.assertRaisesRegex(ValueError,'unsupported characters'):
            self.cat.upsert({'id':'../../bad','description':'test'})
    def test_conflicting_source_no_overwrite(self):
        row=self.sample();self.cat.upsert(row)
        row['description']='changed'
        with self.assertRaisesRegex(ValueError,'Conflicting'):self.cat.upsert(row)
    def test_import_500_reference_lines_in_streaming_jsonl(self):
        path=self.root/'source_records.jsonl'
        with path.open('w',encoding='utf8') as f:
            for i in range(1,501):
                record={'source_index':i,'reference_file':f'Item{i}.png',
                        'reference_image_url':f'https://example.com/item{i}.png',
                        'source_collection':'pzwiki_item_icons','kind':'item'}
                f.write(json.dumps(record)+'\n')
        good,count,errors=self.cat.import_file(path)
        self.assertEqual((good,count,len(errors)),(500,500,0))
        self.assertEqual(self.cat.report()['total_unique_records'],500)
        good,count,errors=self.cat.import_file(path)
        self.assertEqual((good,count,len(errors)),(500,500,0))
        self.assertEqual(self.cat.report()['total_unique_records'],500)
        self.assertEqual(self.cat.report()['by_disposition']['reference_only_needs_description_and_original_recipe'],500)
    def test_markdown_notion_archive_parser(self):
        content='''| # | Reference filename | Reference image | Source file page | Reported dimensions |
| --- | --- | --- | --- | --- |
| 3801 | SyringeEmpty.png | [Image](https://pzwiki.net/w/images/2/2b/SyringeEmpty.png) | [Source](https://pzwiki.net/wiki/File:SyringeEmpty.png) | 32 × 32; 265 bytes |
| 3802 | TableKnife Forged.png | [Image](https://pzwiki.net/w/images/a/a2/TableKnife_Forged.png) | [Source](https://pzwiki.net/wiki/File:TableKnife_Forged.png) | 32 × 32; 495 bytes |
'''
        f=self.root/'notion_batch_21.md';f.write_text(content)
        self.assertEqual(self.cat.import_file(f),(2,2,[]))
        count=self.cat.db.execute('SELECT COUNT(*) FROM sources').fetchone()[0]
        self.assertEqual(count,2)
        row=self.cat.db.execute('SELECT authoritative_source_json FROM sources WHERE id=?',('pzwiki.icon.003801',)).fetchone()[0]
        raw=json.loads(row)
        self.assertEqual(raw['reference_file'],'SyringeEmpty.png')
        self.assertEqual(raw['reported_dimensions'],'32 × 32; 265 bytes')
    @unittest.skipIf(Image is None,'Pillow unavailable')
    def test_new_object_from_data_recipe_no_python_function(self):
        recipe={"canvas":[64,64],"layers":[
          {"op":"ellipse","box":[9,9,55,55],"material":"steel","shade":"shadow"},
          {"op":"polygon","points":[[31,12],[26,37],[40,38]],"material":"plastic","shade":"highlight"}
        ]}
        row={'id':'ll.original.compass2','name':'Original compass','kind':'item','description':'round navigation instrument',
          'approved_original_recipe':True,'provenance':'original_internal','art_recipe':recipe}
        self.cat.upsert(row);self.cat.db.commit()
        self.assertEqual(len(self.cat.pending(10)),1)
        report=ll.produce_original_icons(self.cat,self.root,10)
        self.assertEqual(report['generated'],1)
        self.assertEqual(report['failures'],0)
        self.assertEqual(self.cat.report()['by_generated_asset_status']['technical_qa_passed'],1)
    @unittest.skipIf(Image is None,'Pillow unavailable')
    def test_art_recipe_does_not_run_injected_code(self):
        recipe={"canvas":[64,64],"layers":[{"op":"eval","expression":"__import__('os').system('echo oops')"}]}
        with self.assertRaisesRegex(ValueError,'Unsupported drawing operation'):
            ll.render_art_recipe(recipe,1,self.root/'bad.png')
        self.assertFalse((self.root/'bad.png').exists())
    def test_unapproved_art_recipe_never_generated(self):
        row={'id':'ref.foo.bar','kind':'item','description':'source image metadata',
           'art_recipe':{'layers':[{'op':'rectangle','box':[1,1,10,10]}]}}
        self.cat.upsert(row);self.cat.db.commit()
        self.assertEqual(self.cat.pending(200),[])
    @unittest.skipIf(Image is None,'Pillow unavailable')
    def test_generated_icons_resume_and_repair(self):
        row=self.sample();self.cat.upsert(row);self.cat.db.commit()
        a=ll.produce_original_icons(self.cat,self.root,200)
        self.assertEqual(a['generated'],1)
        self.assertEqual(ll.produce_original_icons(self.cat,self.root,200)['generated'],0)
        icon=self.root/a['items'][0]['path'];icon.write_bytes(b'bad')
        self.assertEqual(ll.produce_original_icons(self.cat,self.root,200)['generated'],1)
        Image.open(icon).verify()
    @unittest.skipIf(Image is None,'Pillow unavailable')
    def test_all_icon_primitive_renderers(self):
        for kind in sorted(ll.SUPPORTED_ICONS):
            path=self.root/(kind+'.png')
            ll.make_icon(kind,1234,path)
            with Image.open(path) as im:
                self.assertEqual(im.size,(64,64))
                self.assertEqual(im.mode,'RGBA')
                self.assertIsNotNone(im.getchannel('A').getbbox())

class ExportsTests(unittest.TestCase):
    @unittest.skipIf(Image is None,'Pillow unavailable')
    def test_texture_seams_and_variants(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            for kind in ll.TERRAIN_MATERIALS:
                path=root/(kind+'.png')
                ll.generate_texture(kind,1234,path)
                with Image.open(path) as im:
                    for y in range(64):self.assertEqual(im.getpixel((0,y)),im.getpixel((63,y)))
                    for x in range(64):self.assertEqual(im.getpixel((x,0)),im.getpixel((x,63)))
    def test_zip_crc_and_no_sources(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            (root/'world').mkdir()
            (root/'world'/'test.json').write_text('{"seed":123}')
            (root/'imports').mkdir()
            (root/'imports'/'reference_image.png').write_bytes(b'copyrighted reference')
            paths=ll.zip_outputs(root,'test',100)
            self.assertEqual(len(paths),1)
            with zipfile.ZipFile(paths[0]) as z:
                self.assertIsNone(z.testzip())
                self.assertEqual(z.namelist(),['world/test.json'])
    def test_same_zip_identical_bytes(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'world').mkdir()
            (root/'world'/'test.json').write_text('{}')
            a=ll.zip_outputs(root,'test',100)[0];first=Path(a).read_bytes()
            b=ll.zip_outputs(root,'test',100)[0]
            self.assertEqual(first,Path(b).read_bytes())

if __name__=='__main__':unittest.main(verbosity=2)