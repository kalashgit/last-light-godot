"use strict";
const $ = (id) => document.getElementById(id);
const escapeHTML = (s) => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"})[c]);
const REVIEW_SCHEMA = "A00_CLASSIFICATION_REVIEW_V1";
const REVIEW_CHOICES = ["PHYSICAL_MASTER_CANDIDATE","NEEDS_VISUAL_EVIDENCE","TILE_OR_ATLAS_COMPONENT","APPEARANCE_VARIANT","NON_PHYSICAL_RESEARCH","RESEARCH_COMPOSITE","STATE_OF_PARENT","MODEL_VIEW_OF_PARENT","ANIMATION_REFERENCE","UI_ICON_ONLY","MATERIAL_TEXTURE","DUPLICATE_ALIAS","OUT_OF_SCOPE","COMPOSITION_REFERENCE","CANONICAL_MASTER_CANDIDATE","MEANINGFUL_VARIANT","STATE_OR_DIRECTION"];
const state = { catalog: null, byId: new Map(), decisions: new Map(), matches: [], displayed: 0, selected: -1, db: null, reviewer: "" };

function imageURL(name) { return "https://pzwiki.net/wiki/Special:Redirect/file/" + encodeURIComponent(name.replace(/ /g,"_")); }
function sourceURL(r) { return /^https:\/\/pzwiki\.net\/wiki\/File:/i.test(r.url) ? r.url : "https://pzwiki.net/wiki/Category:Files"; }
function prettify(s) { return (s || "Unrouted").replace(/_/g," ").replace(/\b\w/g, c=>c.toUpperCase()); }

function openDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open("last-light-a00-reviews",1);
    req.onupgradeneeded = () => req.result.createObjectStore("decisions",{keyPath:"source_page_id"});
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}
function storePut(record) { return new Promise((resolve,reject)=> { const tx=state.db.transaction("decisions","readwrite"); tx.objectStore("decisions").put(record); tx.oncomplete=resolve; tx.onerror=()=>reject(tx.error); }); }
function storeAll() { return new Promise((resolve,reject)=> { const tx=state.db.transaction("decisions","readonly"), req=tx.objectStore("decisions").getAll(); req.onsuccess=()=>resolve(req.result); req.onerror=()=>reject(req.error); }); }

async function boot() {
  try {
    if(!window.__A00_CATALOG_GZIP || typeof DecompressionStream==="undefined") throw Error("Compressed catalog requires a modern browser");
    const bytes=Uint8Array.from(atob(window.__A00_CATALOG_GZIP),c=>c.charCodeAt(0));
    const stream=new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip"));
    state.catalog=JSON.parse(await new Response(stream).text());
    if(state.catalog.schema !== "A00_VISUAL_CATALOG_V1" || state.catalog.records.length !== 21025) throw new Error("Catalog integrity failed");
    state.byId = new Map(state.catalog.records.map(r=>[r.id,r]));
    try {
      state.db = await openDB();
      (await storeAll()).forEach(d=> { if(state.byId.get(d.source_page_id)?.sig===d.source_signature) state.decisions.set(d.source_page_id,d); });
      $("save-status").textContent = "On-device ledger ready";
    } catch(err) {
      $("save-status").textContent = "Private storage unavailable — export every session";
      alert("Browser storage is unavailable. Decisions work during this session only. Export before leaving.");
    }
    $("total-count").textContent = state.catalog.archive_count.toLocaleString();
    $("flagged-count").textContent = state.catalog.r02_count.toLocaleString();
    const types = [...new Set(state.catalog.records.map(r=>r.proposal))].sort();
    $("classification").insertAdjacentHTML("beforeend",types.map(t=>`<option value="${escapeHTML(t)}">${escapeHTML(prettify(t))}</option>`).join(""));
    $("override").innerHTML = REVIEW_CHOICES.map(t=>`<option value="${t}">${prettify(t)}</option>`).join("");
    const families = [...new Set(state.catalog.records.map(r=>r.family).filter(Boolean))].sort();
    $("family").insertAdjacentHTML("beforeend",families.map(f=>`<option value="${escapeHTML(f)}">${escapeHTML(f)}</option>`).join(""));
    bind(); filter();
  } catch(err) { $("result-title").textContent="Catalog unavailable"; $("cards").textContent=String(err.message); $("save-status").textContent="Load failed"; }
}

function bind() {
  for(const id of ["scope","classification","family","review-state","has-parent","has-model","sort"]) $(id).addEventListener("change",filter);
  $("search").addEventListener("input",filter);
  $("load-more").addEventListener("click",()=>renderPage(true));
  $("reset-filters").addEventListener("click",()=> {$("search").value="";$("scope").value="r02";$("classification").value="all";$("family").value="all";$("review-state").value="all";$("has-parent").checked=false;$("has-model").checked=false;filter();});
  $("close-detail").addEventListener("click",closeDetail);
  $("dialog").addEventListener("click",e=> { if(e.target===$("dialog")) closeDetail(); });
  document.addEventListener("keydown",e=> {if(e.key==="Escape") closeDetail();if(!$("dialog").classList.contains("hidden") && e.target.tagName!=="INPUT"&&e.target.tagName!=="TEXTAREA"){if(e.key==="ArrowLeft")navigate(-1);if(e.key==="ArrowRight")navigate(1);}});
  $("previous").addEventListener("click",()=>navigate(-1));
  $("next").addEventListener("click",()=>navigate(1));
  $("accept").addEventListener("click",()=>decide("accepted"));
  $("reject").addEventListener("click",()=>decide("rejected"));
  $("needs-evidence").addEventListener("click",()=>decide("needs_evidence"));
  $("export-button").addEventListener("click",exportDecisions);
  $("import-button").addEventListener("click",()=>$("import-file").click());
  $("import-file").addEventListener("change",importDecisions);
}

function filter() {
  if(!state.catalog)return;
  const q=$("search").value.trim().toLowerCase(), scope=$("scope").value, cls=$("classification").value, family=$("family").value, review=$("review-state").value;
  state.matches = state.catalog.records.filter(r=> {
    if(scope==="r02"&&!r.r02)return false;
    if(cls!=="all"&&r.proposal!==cls)return false;
    if(family!=="all"&&r.family!==family)return false;
    if($("has-parent").checked&&!r.parent)return false;
    if($("has-model").checked&&!r.models?.length)return false;
    const d=state.decisions.get(r.id);
    if(review!=="all" && (review==="unreviewed" ? !!d : d?.decision!==review)) return false;
    if(q&&!`${r.id} ${r.name} ${r.key} ${r.canonical||""} ${r.family||""} ${r.proposal} ${r.categories.join(" ")}`.toLowerCase().includes(q))return false;
    return true;
  });
  if($("sort").value==="name") state.matches.sort((a,b)=>a.name.localeCompare(b.name));
  if($("sort").value==="confidence") state.matches.sort((a,b)=>(a.confidence??0)-(b.confidence??0));
  $("result-title").textContent = `${state.matches.length.toLocaleString()} references`;
  $("result-summary").textContent = scope==="r02" ? "R02 review focus" : "Full source archive";
  state.displayed=0;$("cards").replaceChildren();renderPage(false);updateMetrics();
}
function updateMetrics() {
  $("reviewed-count").textContent=state.decisions.size.toLocaleString();
  const inScope=state.catalog.records.filter(r=>$("scope").value==="all"||r.r02);
  $("remaining-count").textContent=(inScope.length-inScope.filter(r=>state.decisions.has(r.id)).length).toLocaleString();
}
function renderPage(append) {
  if(!append){$("cards").replaceChildren();state.displayed=0;}
  const slice=state.matches.slice(state.displayed,state.displayed+72);
  const frag=document.createDocumentFragment();
  for(const r of slice){
    const card=document.createElement("button");card.className="asset-card";card.type="button";
    const decision=state.decisions.get(r.id);
    card.innerHTML=`<div class="card-image"><span class="fallback">◈</span><img loading="lazy" alt="" referrerpolicy="no-referrer"><span class="card-badge">#${r.id}</span>${decision?`<span class="card-reviewed">${escapeHTML(decision.decision)}</span>`:""}</div><div class="card-body"><strong title="${escapeHTML(r.name)}">${escapeHTML(r.name)}</strong><div class="meta">${escapeHTML(r.family||"—")} · ${r.r02?"R02":"Census"}</div><div class="class">${escapeHTML(prettify(r.proposal))}</div></div>`;
    const img=card.querySelector("img");img.src=imageURL(r.name);img.onerror=()=>{img.remove();};
    card.addEventListener("click",()=>openDetail(state.matches.indexOf(r)));frag.appendChild(card);
  }
  $("cards").appendChild(frag);state.displayed+=slice.length;
  $("loaded-count").textContent=`Showing ${state.displayed.toLocaleString()} of ${state.matches.length.toLocaleString()}`;
  $("load-more").hidden=state.displayed>=state.matches.length;
  if(!state.matches.length)$("cards").textContent="No records match these filters.";
}
function openDetail(index) {
  state.selected=index;
  const r=state.matches[index];if(!r)return;
  $("dialog").classList.remove("hidden");document.body.style.overflow="hidden";
  $("detail-meta").textContent=`FILE PAGE #${r.id} · ${r.r02?"R02 SEMANTIC PASS":"SOURCE CENSUS"}`;
  $("detail-title").textContent=r.name;
  $("detail-class").textContent=prettify(r.proposal);
  $("detail-family").textContent=r.family||"Queue unresolved";
  const img=$("detail-image");$("image-failed").classList.add("hidden");img.classList.remove("hidden");img.onerror=()=>{img.classList.add("hidden");$("image-failed").classList.remove("hidden");};img.src=imageURL(r.name);
  $("original-link").href=sourceURL(r);
  const parent=state.byId.get(r.parent);
  const facts=[
    ["Source class",prettify(r.category)], ["Proposed root",r.key||"Not assigned"],
    ["Parent",parent?`#${parent.id} · ${parent.name}`:(r.parent?`#${r.parent} · unknown parent` :"Not linked")],
    ["Canonical ID",r.canonical||"Not admitted"], ["Existing 360",r.models?.join(", ")||"No source-name match"],
    ["Confidence",r.confidence==null?"Unscored":`${Math.round(r.confidence*100)}% metadata heuristic`],
    ["Categories",r.categories.join(" · ")||"Uncategorized"],["Prior reasoning",r.reason||"Not recorded"],
    ["Rights",r.rights||"Research only"]
  ];
  $("detail-facts").innerHTML=facts.map(([k,v])=>`<dt>${escapeHTML(k)}</dt><dd>${escapeHTML(v)}</dd>`).join("");
  const d=state.decisions.get(r.id);
  $("reviewer").value=d?.reviewer||state.reviewer||"";$("override").value=d?.proposed_classification||r.proposal;$("notes").value=d?.notes||"";
  $("decision-message").textContent=d?`Saved: ${prettify(d.decision)} (${d.reviewed_at})`:"Not yet reviewed";
  $("detail-position").textContent=`${index+1} / ${state.matches.length}`;
  $("previous").disabled=index===0;$("next").disabled=index===state.matches.length-1;
}
function closeDetail(){$("dialog").classList.add("hidden");document.body.style.overflow="";}
function navigate(delta) { const i=state.selected+delta;if(i>=0&&i<state.matches.length)openDetail(i); }
async function decide(decision) {
  const r=state.matches[state.selected],reviewer=$("reviewer").value.trim(),notes=$("notes").value.trim();
  if(!reviewer){$("decision-message").textContent="Enter your reviewer name or ID first.";$("reviewer").focus();return;}
  if(decision==="rejected"&&!notes){$("decision-message").textContent="Provide a reason for rejection.";$("notes").focus();return;}
  const item={schema:REVIEW_SCHEMA,catalog_snapshot:state.catalog.snapshot,source_page_id:r.id,source_signature:r.sig,base_classification:r.proposal,proposed_classification:$("override").value,decision,reviewer,notes,reviewed_at:new Date().toISOString(),production_approval:false,rights_approval:false};
  state.reviewer=reviewer;state.decisions.set(r.id,item);
  if(state.db)try{await storePut(item);}catch(e){$("save-status").textContent="Storage error — export decisions now";}
  $("decision-message").textContent=`Saved locally: ${prettify(decision)}. Export to share with workers.`;
  filter();
  const newIndex=state.matches.findIndex(x=>x.id===r.id);
  if(newIndex>=0)openDetail(newIndex);else closeDetail();
}
function exportDecisions() {
  const lines=[...state.decisions.values()].sort((a,b)=>a.source_page_id-b.source_page_id).map(r=>JSON.stringify(r)).join("\n")+"\n";
  const a=document.createElement("a"),url=URL.createObjectURL(new Blob([lines],{type:"application/x-ndjson"}));
  a.href=url;a.download=`last-light-a00-decisions-${new Date().toISOString().slice(0,10)}.jsonl`;a.click();setTimeout(()=>URL.revokeObjectURL(url),2000);
}
async function importDecisions(event) {
  const file=event.target.files?.[0];if(!file)return;
  try {
    const text=await file.text(), lines=text.split(/\r?\n/).filter(Boolean);let count=0;
    const incoming=lines.map(x=>JSON.parse(x));
    const seen = new Set();
    for(const d of incoming){
      const r=state.byId.get(d.source_page_id);
      if(!r||seen.has(d.source_page_id)||d.schema!==REVIEW_SCHEMA||d.catalog_snapshot!==state.catalog.snapshot||d.source_signature!==r.sig||d.base_classification!==r.proposal||!["accepted","rejected","needs_evidence"].includes(d.decision)||!REVIEW_CHOICES.includes(d.proposed_classification)||typeof d.reviewer!=="string"||!d.reviewer.trim()||d.reviewer.length>80||typeof d.notes!=="string"||d.notes.length>2000||(d.decision==="rejected"&&!d.notes.trim())||typeof d.reviewed_at!=="string"||!Number.isFinite(Date.parse(d.reviewed_at))||d.production_approval!==false||d.rights_approval!==false)throw Error(`Invalid or different-snapshot decision for #${d.source_page_id}`);
      seen.add(d.source_page_id);
    }
    for(const d of incoming){const old=state.decisions.get(d.source_page_id);if(old&&Date.parse(old.reviewed_at)>Date.parse(d.reviewed_at))continue;state.decisions.set(d.source_page_id,d);if(state.db)await storePut(d);count++;}
    filter();alert(`Imported ${count} review decisions. Remember to export after changes.`);
  }catch(e){alert(`Import rejected: ${e.message}`);}finally{event.target.value="";}
}
boot();
