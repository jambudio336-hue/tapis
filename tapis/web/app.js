const $ = (s) => document.querySelector(s);
const state = { token: localStorage.getItem("tapis_token") || "", target: null, ws: null, map: null, marks: [] };

if (state.token) $("#token").value = state.token;
$("#muat").onclick = () => { state.token = $("#token").value.trim(); localStorage.setItem("tapis_token", state.token); muatTarget(); sambung(); };

const api = (p, o = {}) => fetch("/api/v1" + p, { ...o, headers: { Authorization: "Bearer " + state.token, ...(o.headers || {}) } });

function peta() {
  if (state.map) return;
  state.map = L.map("peta").setView([-2.5, 118], 5);
  L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", { maxZoom: 19 }).addTo(state.map);
}

async function muatTarget() {
  const r = await api("/targets");
  if (!r.ok) return;
  const list = await r.json();
  $("#targets").innerHTML = "";
  list.forEach((t) => {
    const li = document.createElement("li");
    li.innerHTML = `<b>${t.msisdn}</b><div class="op">${t.operator || "operator tak dikenal"}</div>`;
    li.onclick = () => pilih(t);
    $("#targets").append(li);
  });
}

async function pilih(t) {
  state.target = t.id;
  $("#judul").textContent = t.msisdn;
  $("#events").innerHTML = ""; $("#audio").innerHTML = ""; $("#cells").innerHTML = "";
  peta();
  const [ev, au, ce] = await Promise.all([
    api(`/targets/${t.id}/events`).then((x) => x.json()),
    api(`/targets/${t.id}/audio`).then((x) => x.json()),
    api(`/targets/${t.id}/cell`).then((x) => x.json()),
  ]);
  ev.forEach(renderEvent); au.forEach(renderAudio); ce.forEach(renderCell);
}

function renderEvent(e) {
  const d = document.createElement("div");
  d.innerHTML = `<b>${e.jenis}</b> ${new Date(e.terjadi_pada).toLocaleString("id-ID")}`;
  $("#events").prepend(d);
}

function renderAudio(a) {
  const w = document.createElement("div");
  w.innerHTML = `<audio controls src="/api/v1/audio/${a.id}/berkas?t=${state.token}"></audio>
    <div style="color:var(--dim);font-size:10px">${a.sha256.slice(0, 16)}…</div>`;
  $("#audio").prepend(w);
}

function renderCell(c) {
  const d = document.createElement("div");
  d.textContent = `${c.cid} · ${new Date(c.pada).toLocaleTimeString("id-ID")}`;
  $("#cells").prepend(d);
  if (c.lat == null || !state.map) return;
  const m = L.circleMarker([c.lat, c.lon], { radius: 6, color: "#2ea3a3" }).addTo(state.map);
  m.bindPopup(`${c.sumber} · ±${Math.round(c.akurasi || 0)} m`);
  state.marks.push(m);
  state.map.setView([c.lat, c.lon], 15);
}

function sambung() {
  if (state.ws) state.ws.close();
  const proto = location.protocol === "https:" ? "wss" : "ws";
  state.ws = new WebSocket(`${proto}://${location.host}/api/v1/ws`);
  state.ws.onopen = () => $("#status").classList.add("on");
  state.ws.onclose = () => { $("#status").classList.remove("on"); setTimeout(sambung, 3000); };
  state.ws.onmessage = (m) => {
    const d = JSON.parse(m.data);
    if (d.target_id !== state.target) return;
    if (d.event) renderEvent(d.event);
    if (d.audio) renderAudio(d.audio);
    if (d.cell) renderCell(d.cell);
  };
}

$("#form").onsubmit = async (e) => {
  e.preventDefault();
  const body = { msisdn: $("#msisdn").value, imei: $("#imei").value || null };
  const r = await api("/targets", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const d = await r.json();
  if (!r.ok) return alert(d.detail || "gagal");
  $("#msisdn").value = ""; $("#imei").value = "";
  await muatTarget();
  pilih(d);
};

peta();
if (state.token) { muatTarget(); sambung(); }
