import {readFileSync,writeFileSync,mkdirSync} from "node:fs";
import {resolve,dirname} from "node:path";
import {fileURLToPath} from "node:url";

// LAST LIGHT -- canonical archetype showcase compiler.
// Outputs review-only structural world records; it does not approve art assets.
export const buildWorld = function buildWorld(cat, proto, seed=20261109) {
  const categoryOrder=["residential","commercial","civic","industrial","recreation","special"];
  const districtLabels=["House Quarter","Market Street","Civic Center","Industry & Farms","Parks & Recreation","Special Facilities"];
  const tabs=["HOMES","MARKET","CIVIC","WORKS","PARKS","SPECIAL"];
  const origins=categoryOrder.map((category,i)=>({category,label:districtLabels[i],tab:tabs[i],origin:[18+(i%2)*210,18+Math.floor(i/2)*190],grid:[4,4]}));
  const arch={};
  const sortedNames=[];
  for(const category of categoryOrder)for(const item of cat.archetypes[category]) {if(arch[item.id])throw Error("Duplicate canonical archetype");arch[item.id]={...item,category};sortedNames.push(item.id);}
  if(sortedNames.length!==60)throw Error("Expected 60 archetypes, got "+sortedNames.length);
  if(proto.buildings.length!==3)throw Error("Existing three-house prototype missing");
  const rawHash=text=>{let h=2166136261;for(let i=0;i<text.length;i++){h^=text.charCodeAt(i);h=Math.imul(h,16777619)>>>0;}return h>>>0;};
  const rounded=n=>Math.round(n*1000)/1000;
  const transformRect=(r,old,newFoot)=>[rounded(newFoot[0]+(r[0]-old[0])*newFoot[2]/old[2]),rounded(newFoot[1]+(r[1]-old[1])*newFoot[3]/old[3]),rounded(r[2]*newFoot[2]/old[2]),rounded(r[3]*newFoot[3]/old[3])];
  const transformPoint=(p,old,newFoot)=>[rounded(newFoot[0]+(p[0]-old[0])*newFoot[2]/old[2]),rounded(newFoot[1]+(p[1]-old[1])*newFoot[3]/old[3])];
  const houses=[
    {id:"ll.house_row.starter",type:"STARTER HOME",archetype_id:"house_small",w:10,h:11,wall:"plaster_cream",roof:"shingle_asphalt",floor:"wood_oak",stories:1,style:"starter_plaster"},
    {id:"ll.house_row.brick",type:"BRICK FAMILY HOME",archetype_id:"house_large",w:14,h:12,wall:"brick_aged",roof:"shingle_asphalt",floor:"wood_oak",stories:2,style:"brick_two_storey"},
    {id:"ll.house_row.rural",type:"RURAL HOME",archetype_id:"farm",w:12,h:11,wall:"timber_siding",roof:"green_metal",floor:"wood_oak",stories:1,style:"rural_timbers"}
  ];
  const roadSegments=[];
  const buildings=[];
  const placedCatalog=[];
  const districts=[];
  const lots=[];
  const housesIDs=[];
  const regionOrigins=new Map(origins.map(x=>[x.category,x]));
  const palette={"residential":"#a49a83","commercial":"#927d70","civic":"#a3a7a2","industrial":"#898c83","recreation":"#788f70","special":"#898a82"};
  function makeBuilding(entry, catGroup, slot, district, variant=null, original=null) {
    const x=district.origin[0]+(slot%4)*45;
    const y=district.origin[1]+Math.floor(slot/4)*39;
    const width=variant?variant.w:entry.footprint_hint[0];
    const height=variant?variant.h:entry.footprint_hint[1];
    if(width>38||height>33)throw Error("Footprint exceeds district pitch "+entry.id);
    const foot=[x,y,width,height],door=[rounded(x+width*.5),y+height];
    const id=variant?variant.id:"ll.world."+entry.id;
    const kit=cat.material_kits[entry.kit];
    if(!kit)throw Error("Unknown kit "+entry.kit);
    const kind=variant?"house_variant":(["park","stadium","sports_field","campground","construction_site","storage_yard","trailer_park"].includes(entry.id)?"site":"structure");
    let rooms=[],hall={},interiorDoors=[],furnishings=[];
    if(original){
      const r0=original.footprint;
      rooms=original.rooms.map((r,i)=>({...r,id:id+".room."+i,rect:transformRect(r.rect,r0,foot),source_room_id:r.id}));
      hall={id:id+".hall",rect:transformRect(original.hall.rect,r0,foot)};
      interiorDoors=original.interior_doors.map((d,i)=>({id:id+".door."+i,pos:transformPoint(d.pos,r0,foot),source_door_id:d.id,room_id:rooms[i%rooms.length].id}));
      furnishings=original.furnishings.map((f,i)=>({...f,id:id+".furniture."+i,pos:transformPoint(f.pos,r0,foot),status:"unapproved_debug_placeholder"}));
    } else {
      const modules=cat.room_profiles[entry.profile];
      if(!modules||!modules.length)throw Error("Unknown room profile "+entry.profile);
      const rows=Math.ceil(modules.length/2), roomW=(width-1.8)/2,roomH=(height-1.8)/rows;
      rooms=modules.map((type,i)=>{const rx=x+.9+(i%2)*roomW,ry=y+.9+Math.floor(i/2)*roomH;return {id:id+".room."+i,type,rect:[rounded(rx),rounded(ry),rounded(roomW),rounded(roomH)],systems:cat.room_modules[type].systems,prop_roles:cat.room_modules[type].props};});
      hall={id:id+".hall",rect:[rounded(x+width*.47),rounded(y+.4),rounded(Math.max(.6,width*.06)),rounded(height-.8)]};
      interiorDoors=rooms.map((r,i)=>({id:id+".door."+i,room_id:r.id,pos:[rounded(x+width*.5),rounded(r.rect[1]+r.rect[3]*.5)]}));
      furnishings=rooms.map((r,i)=>({id:id+".fixture."+i,pos:[rounded(r.rect[0]+Math.min(.6,r.rect[2]*.25)),rounded(r.rect[1]+Math.min(.7,r.rect[3]*.25))],type:r.type,asset_role:r.prop_roles[0]||"none",status:"unapproved_debug_placeholder"}));
    }
    const number=rawHash(`${seed}:${id}`);
    const material=variant?{wall:variant.wall,roof:variant.roof,floor:variant.floor,stories:variant.stories}: {wall:kit.wall,roof:kit.roof,floor:kit.floor,stories:entry.id==="apartment_block"||entry.id==="hotel"?3:entry.id==="townhouse"||entry.id==="house_large"?2:1};
    const streetY=district.origin[1]+Math.floor(slot/4)*39+35.5;
    const b={
      id,archetype_id:entry.id,catalog_family:entry.category,district:catGroup,
      archetype_reference_only:true,material_kit_id:entry.kit,
      house_variant:variant?variant.style:null,lab_origin_id:original?original.id:null,
      display_name:variant?variant.type:entry.id.replaceAll("_"," ").toUpperCase(),
      footprint:foot,entry:{id:id+".entry",pos:door,connects:["outside","hall"],kind:"front_door"},
      road_access_path:[door,[door[0],streetY]],
      materials:material,profile:entry.profile,room_modules:cat.room_profiles[entry.profile],
      rooms,hall,interior_doors:interiorDoors,furnishings,
      footprint_kind:kind,roof:{enabled:true,type:material.roof},
      condition:["intact","weathered","damaged"][number%3],
      zombie_spawn_budget:rawHash(`${id}:zombie:${seed}`)%5,
      loot_profile:entry.profile,
      collision_status:"shell_only",
      art_status:"UNAPPROVED_PROCEDURAL_DEBUG_PLACEHOLDER",
      gameplay_status:"SCAFFOLD_INTERACTION_ONLY",
      color:palette[catGroup],seed:(number>>>0),lot_id:catGroup+"-"+slot
    };
    buildings.push(b);lots.push({id:b.lot_id,footprint:b.footprint,district:catGroup});
    if(variant)housesIDs.push(id);else placedCatalog.push(entry.id);
    return b;
  }
  for(const district of origins){
    const catName=district.category;
    const reserved=catName==="residential"?3:0;
    let slot=reserved;
    if(catName==="residential"){
      for(let i=0;i<3;i++) makeBuilding(arch[houses[i].archetype_id],catName,i,district,houses[i],proto.buildings[i]);
    }
    for(const entry of cat.archetypes[catName])makeBuilding(arch[entry.id],catName,slot++,district);
    if(slot>16)throw Error("Zone overflow "+catName);
    districts.push({id:"ll.district."+catName,category:catName,name:district.label,tab:district.tab,origin:district.origin,
                    access_point:[district.origin[0]+5,district.origin[1]+36],building_count:slot,
                    guide:"UNAPPROVED_ARCHETYPES_FOR_TECHNICAL_REVIEW"});
    for(let row=0;row<4;row++){
      const rr={id:"ll.road."+catName+".lane."+row,rect:[district.origin[0]-5,district.origin[1]+row*39+34,184,4],kind:"access_lane",material:"asphalt_worn"};
      roadSegments.push(rr);
    }
    for(let col=0;col<3;col++){
      roadSegments.push({id:"ll.road."+catName+".cross."+col,rect:[district.origin[0]+col*45+39,district.origin[1]-4,4,158],kind:"service_lane",material:"asphalt_worn"});
    }
  }
  for(let i=0;i<4;i++)roadSegments.push({id:"ll.road.spine.horizontal."+i,rect:[0,5+i*190,420,7],kind:"connector",material:"asphalt_worn"});
  roadSegments.push({id:"ll.road.spine.vertical",rect:[205,0,9,610],kind:"connector",material:"asphalt_worn"});
  const countByCategory=Object.fromEntries(categoryOrder.map(x=>[x,cat.archetypes[x].length]));
  if(placedCatalog.length!==60||new Set(placedCatalog).size!==60||housesIDs.length!==3)throw Error("Coverage did not pass");
  return {
    schema:"last_light.all_archetypes_neighborhood.v1",version:1,seed,projection:"80x40_2to1",logical_tile_px:[80,40],
    art_status:"UNAPPROVED_DEBUG_GEOMETRY_NOT_GOLDEN",
    full_gameplay_status:"NOT_CERTIFIED",
    main_scene_unchanged:true,
    source_catalog:"assets/buildings/building_archetypes_v1.json",
    source_three_house_seed:"data/generated/neighborhood_v2.json",
    bounds:[0,0,420,610],
    player_spawn:[rounded(18+houses[0].w*.5),rounded(18+houses[0].h+2)],
    districts,
    neighborhood_center:"Three-house showcase plus six walkable design districts",
    house_row:{name:"Three House Styles",ids:housesIDs,styles:houses.map(x=>x.style),source_count:3},
    roads:roadSegments,
    buildings,
    catalog_coverage:{unique_archetypes:60,all_catalog_ids:placedCatalog,counts_by_family:countByCategory,additional_house_variants:3,total_placed_buildings:buildings.length},
    limitations:["All archetype structures are procedural design scaffolds and visual placeholders, not Golden-approved F02 objects.",
                 "Building-shell collision and teleport door access only; interior partitions and furniture do not yet have complete collisions.",
                 "Damage, loot and zombies are metadata budgets, not playable systems for all 63 lots.",
                 "iPhone device and independent Golden visual QA pending."]
  };
};

if (process.argv[1] && resolve(process.argv[1])===fileURLToPath(import.meta.url)) {
  const root=resolve(dirname(fileURLToPath(import.meta.url)), "../..");
  const catalog=JSON.parse(readFileSync(resolve(root,"assets/buildings/building_archetypes_v1.json"),"utf8"));
  const prototype=JSON.parse(readFileSync(resolve(root,"data/generated/neighborhood_v2.json"),"utf8"));
  const seed=process.argv[2]===undefined?20261109:Number(process.argv[2]);
  if (!Number.isSafeInteger(seed))throw Error("Seed must be a safe integer");
  const world=buildWorld(catalog,prototype,seed);
  const output=resolve(root,"data/generated/all_archetypes_neighborhood_v1.json");
  mkdirSync(dirname(output),{recursive:true});
  writeFileSync(output,JSON.stringify(world,null,2)+"\n","utf8");
  console.log(JSON.stringify({status:"WORLD_60_ARCHETYPES_COMPILED",seed,buildings:world.buildings.length,catalog:world.catalog_coverage.unique_archetypes,house_row:world.house_row.ids.length,output}));
}
