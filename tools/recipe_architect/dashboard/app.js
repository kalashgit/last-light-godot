"use strict";
const $ = (id) => document.getElementById(id);
const current = { rooms: [], filtered: [], page: 0, size: 40, selected: null, angle: 0 };
function stateName(room) {
  if (room.golden_approved) return "Golden approved";
  if (room.technical_pass) return "Technical model · review needed";
  if ((room.status || "").includes("FAIL")) return "Technical failure";
  return "Source review pending";
}
function element(name, cls, value) {
  const node = document.createElement(name);
  if (cls) node.className = cls;
  if (value !== undefined) node.textContent = String(value);
  return node;
}
function renderCards() {
  const total = current.filtered.length;
  const pages = Math.max(1, Math.ceil(total / current.size));
  current.page = Math.min(current.page, pages - 1);
  const slice = current.filtered.slice(current.page * current.size, (current.page + 1) * current.size);
  const fragment = document.createDocumentFragment();
  for (const room of slice) {
    const card = element("button", "asset-card");
    card.type = "button";
    card.setAttribute("aria-label", "Inspect " + room.title);
    const thumb = element("div", "asset-thumb");
    if (room.preview) {
      const img = document.createElement("img");
      img.src = room.preview;
      img.alt = "Rendered inventory view";
      img.loading = "lazy";
      thumb.appendChild(img);
    } else thumb.appendChild(element("div", "placeholder-geometry"));
    const body = element("div", "card-content");
    body.appendChild(element("div", "card-ref", room.source_reference_id));
    body.appendChild(element("strong", "card-title", room.title));
    body.appendChild(element("div", "card-family", String(room.family || "Unknown family").replaceAll("_", " ")));
    const badge = element("div", "card-status" + (room.technical_pass ? " built" : (room.status || "").includes("FAIL") ? " failed" : ""), stateName(room));
    body.appendChild(badge);
    card.append(thumb, body);
    card.addEventListener("click", () => openRoom(room));
    fragment.appendChild(card);
  }
  $("cards").replaceChildren(fragment);
  $("empty").hidden = total > 0;
  $("visible-count").textContent = `(${total})`;
  $("page-label").textContent = `Page ${current.page + 1} of ${pages}`;
  $("prev").disabled = current.page === 0;
  $("next").disabled = current.page + 1 >= pages;
}
function filterRooms() {
  const text = $("search").value.trim().toLowerCase();
  const state = $("state").value;
  current.filtered = current.rooms.filter(room => {
    if (state === "built" && !room.technical_pass) return false;
    if (state === "waiting" && (room.technical_pass || (room.status || "").includes("FAIL"))) return false;
    if (state === "failed" && !(room.status || "").includes("FAIL")) return false;
    return [room.title, room.family, room.source_reference_id, room.candidate_id].some(v => String(v || "").toLowerCase().includes(text));
  });
  current.page = 0;
  renderCards();
}
function displayAngle() {
  const room = current.selected;
  if (!room) return;
  const image = $("heading-img");
  const list = room.headings || [];
  const available = list.length === 16;
  image.hidden = !available;
  $("viewer-placeholder").hidden = available;
  $("angle").disabled = !available;
  $("rotate-left").disabled = !available;
  $("rotate-right").disabled = !available;
  $("angle").value = String(current.angle);
  $("view-label").textContent = available ? `${current.angle + 1} / 16 · ${(current.angle * 22.5).toFixed(1)}°` : "No geometry";
  if (available) image.src = list[current.angle];
}
function safeDownload(anchorId, room, key) {
  const path = room.files?.[key];
  const anchor = $(anchorId);
  anchor.hidden = !path;
  if (path) { anchor.href = path; anchor.setAttribute("download", `${room.room_id}_${key}.${key === "glb" ? "glb" : "blend"}`); }
  else { anchor.removeAttribute("href"); anchor.removeAttribute("download"); }
}
function openRoom(room) {
  current.selected = room;
  current.angle = 0;
  $("detail-ref").textContent = room.room_id;
  $("detail-title").textContent = room.title;
  $("detail-state").textContent = stateName(room);
  $("detail-id").textContent = room.candidate_id || "Not assigned";
  $("detail-source").textContent = room.source_reference_id;
  $("detail-integrity").textContent = room.source_sha256 ? room.source_sha256.slice(0, 16) + "…" : room.source_sheet_sha256?.slice(0, 16) + "…" || "Unverified";
  $("detail-geometry").textContent = room.mesh_objects ? `${room.mesh_objects} mesh objects · ${Number(room.triangles_estimate).toLocaleString()} estimated triangles` : "Not yet built";
  $("detail-compare").textContent = room.reference_vs_render_measured_this_run ? "Measured" : "Not measured in this run";
  $("detail-approval").textContent = room.golden_approved ? "Founder approved" : "Pending exact-file founder review";
  safeDownload("download-glb", room, "glb");
  safeDownload("download-blend", room, "blend");
  displayAngle();
  $("detail").showModal();
}
function exportReviewNote() {
  const room = current.selected;
  if (!room) return;
  const payload = {
    schema: "last-light.founder-review-note.v1",
    source_reference_id: room.source_reference_id,
    candidate_id: room.candidate_id,
    glb_sha256: room.model_glb_sha256,
    room_id: room.room_id,
    founder_golden_approved: false,
    review_status: "EXACT_MODEL_AND_SOURCE_COMPARISON_REQUIRED",
    note: "Exported for founder review. This is not an authentication or admission event."
  };
  const blob = new Blob([JSON.stringify(payload, null, 2) + "\n"], {type: "application/json"});
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url; anchor.download = `${room.room_id}_review_note.json`;
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
async function init() {
  try {
    const response = await fetch("manifest.json", {cache: "no-store"});
    if (!response.ok) throw new Error(`Manifest HTTP ${response.status}`);
    const data = await response.json();
    if (data.schema !== "last-light.mesh-workspace.v1" || !Array.isArray(data.rooms) || data.rooms.length > 100) throw new Error("Unrecognized workspace data");
    current.rooms = data.rooms;
    $("total").textContent = String(data.room_count);
    $("built").textContent = String(data.rooms.filter(r => r.technical_pass).length);
    $("review").textContent = String(data.rooms.filter(r => !r.golden_approved).length);
    $("golden").textContent = String(data.rooms.filter(r => r.golden_approved).length);
    if (data.kind === "verified_founder_sheet_reference_metadata") $("warning").textContent = "Reference staging only: labels are provisional, original images remain private, and no geometry has been generated in this workspace.";
    else $("warning").textContent = "Real CPU-produced GLB and Blender masters are available in the rooms below. Source-image comparison and founder approval are still outstanding.";
    $("warning").hidden = false;
    filterRooms();
  } catch (error) {
    $("warning").textContent = "Could not open a validated mesh workspace: " + error.message;
    $("warning").hidden = false;
  }
}
$("search").addEventListener("input", filterRooms);
$("state").addEventListener("change", filterRooms);
$("page-size").addEventListener("change", event => {current.size = Number(event.target.value);current.page = 0;renderCards()});
$("prev").addEventListener("click", () => {current.page -= 1;renderCards()});
$("next").addEventListener("click", () => {current.page += 1;renderCards()});
$("close").addEventListener("click", () => $("detail").close());
$("angle").addEventListener("input", event => {current.angle = Number(event.target.value);displayAngle()});
$("rotate-left").addEventListener("click", () => {current.angle = (current.angle + 15) % 16;displayAngle()});
$("rotate-right").addEventListener("click", () => {current.angle = (current.angle + 1) % 16;displayAngle()});
$("export-note").addEventListener("click", exportReviewNote);
init();
