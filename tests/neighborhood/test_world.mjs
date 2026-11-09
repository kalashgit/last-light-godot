import {test} from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {resolve} from "node:path";
import {buildWorld} from "../../tools/neighborhood/build_all_archetypes.mjs";

const root=resolve(import.meta.dirname??new URL("../..",import.meta.url).pathname,"../..");
const base=resolve(process.cwd());
const catalog=JSON.parse(readFileSync(resolve(base,"assets/buildings/building_archetypes_v1.json"),"utf8"));
const houseSeed=JSON.parse(readFileSync(resolve(base,"data/generated/neighborhood_v2.json"),"utf8"));
const committed=JSON.parse(readFileSync(resolve(base,"data/generated/all_archetypes_neighborhood_v1.json"),"utf8"));
const build=()=>buildWorld(catalog,houseSeed,20261109);
const rectsOverlap=(a,b)=>a[0]<b[0]+b[2]&&b[0]<a[0]+a[2]&&a[1]<b[1]+b[3]&&b[1]<a[1]+a[3];
const catIds=Object.values(catalog.archetypes).flat().map(x=>x.id);

test("existing canonical catalog contains exactly 60 unique design archetypes",()=>{
 assert.equal(catIds.length,60);assert.equal(new Set(catIds).size,60);
});
test("generated review scene includes all 60 plus 3 house variants",()=>{
 const world=build();
 assert.equal(world.buildings.length,63);
 assert.equal(world.catalog_coverage.unique_archetypes,60);
 assert.deepEqual(new Set(world.catalog_coverage.all_catalog_ids),new Set(catIds));
 assert.equal(world.house_row.ids.length,3);
});
test("all six original categories exist in a navigable zone",()=>{
 const w=build();
 assert.deepEqual(w.districts.map(d=>d.category),
 ["residential","commercial","civic","industrial","recreation","special"]);
 for(const d of w.districts) {
   assert.ok(d.access_point.every(Number.isFinite));
   assert.ok(d.building_count>=6&&d.building_count<=16);
 }
});
test("house row really preserves separate existing 3-house room layouts",()=>{
 const w=build();
 const houses=w.house_row.ids.map(id=>w.buildings.find(b=>b.id===id));
 assert.deepEqual(houses.map(x=>x.display_name),["STARTER HOME","BRICK FAMILY HOME","RURAL HOME"]);
 assert.equal(new Set(houses.map(x=>x.house_variant)).size,3);
 assert.equal(new Set(houses.map(x=>x.materials.wall)).size,3);
 houses.forEach((house,i)=>{
   assert.equal(house.lab_origin_id,houseSeed.buildings[i].id);
   assert.deepEqual(house.rooms.map(x=>x.type),houseSeed.buildings[i].rooms.map(x=>x.type));
   assert.equal(house.interior_doors.length,houseSeed.buildings[i].interior_doors.length);
   assert.equal(house.furnishings.length,houseSeed.buildings[i].furnishings.length);
 });
});
test("world IDs are stable and all 63 footprints and doors fit the world",()=>{
 const w=build(), seen=new Set();
 for(const b of w.buildings){
   assert.ok(!seen.has(b.id),b.id);seen.add(b.id);
   const [x,y,width,height]=b.footprint;
   assert.ok(x>=0&&y>=0&&x+width<=w.bounds[2]&&y+height<=w.bounds[3],b.id);
   assert.equal(b.art_status,"UNAPPROVED_PROCEDURAL_DEBUG_PLACEHOLDER");
   assert.ok(b.rooms.length>0&&b.hall);
   assert.ok(b.entry.pos[0]>x&&b.entry.pos[0]<x+width);
   assert.equal(b.entry.pos[1],y+height);
   for(const r of b.rooms){
     const [rx,ry,rw,rh]=r.rect;
     assert.ok(rx>=x-.01&&ry>=y-.01&&rx+rw<=x+width+.01&&ry+rh<=y+height+.01,JSON.stringify({id:b.id,room:r}));
   }
 }
 for(let i=0;i<w.buildings.length;i++)for(let j=i+1;j<w.buildings.length;j++)
   assert.ok(!rectsOverlap(w.buildings[i].footprint,w.buildings[j].footprint),
     w.buildings[i].id+" overlaps "+w.buildings[j].id);
});
test("identical seed and catalog generate byte-identical committed review JSON",()=>{
 assert.equal(JSON.stringify(build()),JSON.stringify(committed));
 assert.notEqual(buildWorld(catalog,houseSeed,7).buildings[0].seed,committed.buildings[0].seed);
});
test("catalog uses 80 by 40 isometric logical tile and no false approval",()=>{
 const w=build();
 assert.deepEqual(w.logical_tile_px,[80,40]);
 assert.match(w.art_status,/UNAPPROVED/);
 assert.equal(w.main_scene_unchanged,true);
 assert.equal(w.full_gameplay_status,"NOT_CERTIFIED");
 assert.ok(w.limitations.length>2);
});
test("all catalog room modules and material kits are reused, not guessed",()=>{
 const w=build();
 const ids=new Set(catIds);
 for(const b of w.buildings){
   assert.ok(ids.has(b.archetype_id),b.archetype_id);
   assert.ok(catalog.material_kits[b.material_kit_id],b.material_kit_id);
   for(const r of b.rooms)assert.ok(catalog.room_modules[r.type],r.type);
 }
});
test("roads, portals and exit path are deterministic",()=>{
 const w=build();
 assert.equal(w.roads.length,47);
 assert.equal(new Set(w.roads.map(r=>r.id)).size,w.roads.length);
 for(const b of w.buildings){
   assert.deepEqual(b.road_access_path[0],b.entry.pos);
   assert.ok(b.road_access_path[1][1]>=b.entry.pos[1]);
 }
});
