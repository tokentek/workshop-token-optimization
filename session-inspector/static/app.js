"use strict";

// What each colour means. Shown in legend tooltips and the drawer.
const CAT_HELP = {
  tools: "JSON definitions of every tool (name, description, input schema). Sent with every request.",
  system: "Claude Code's system prompt.",
  instructions: "CLAUDE.md files and other project or user instructions.",
  skills: "The list of available skills, and the full text of skills that were loaded.",
  reminders: "Injected context: environment, git status, date, deferred tool lists, token reminders, notices.",
  user: "What the human typed (prompts and slash commands).",
  assistant: "Text the model wrote back.",
  thinking: "The model's thinking blocks. Hidden thinking is sized by the thinking tokens the response reported.",
  tool_use: "Tool calls the model made (tool name + input).",
  tool_result: "What the tools returned (file contents, command output, subagent results).",
  compaction: "Summary that replaced the conversation after a compaction.",
  unattributed: "Input tokens that could not be matched to logged content. In older logs this is mostly the system prompt and tool definitions, which are not written to the log.",
};
const STATE_INFO = {
  verified: ["✓", "ok", "Payload rebuilt from the log and verified against the request digest."],
  mismatch: ["!", "warn", "Payload rebuilt, but it does not match the request digest. Shown anyway."],
  unverified: ["·", "", "Payload rebuilt; no digest to check against."],
  pending: ["…", "warn", "Some parts of this request are not in the log yet."],
  estimated: ["≈", "", "Older log format: context inferred from the transcript."],
};

const $ = (sel) => document.querySelector(sel);
const el = (tag, cls, text) => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
};

const store = (() => {
  const get = (k, d) => { try { const v = localStorage.getItem("si." + k); return v == null ? d : JSON.parse(v); } catch (_) { return d; } };
  const set = (k, v) => { try { localStorage.setItem("si." + k, JSON.stringify(v)); } catch (_) { /* ignore */ } };
  return { get, set };
})();

const S = {
  sessions: [],
  latest: null,
  current: null,
  model: null,
  revision: -1,
  generation: null,
  view: store.get("view", "grouped"),
  scale: store.get("scale", "peak"),
  showAgents: store.get("showAgents", true),
  autoscroll: store.get("autoscroll", true),
  follow: store.get("follow", true),
  highlight: null,
  focus: null,          // {t: "main"|agentId, i: row index}
  expanded: new Set(),  // expanded subagent groups
  es: null,
  fetching: false,
  refetch: false,
  colors: {},
  rowRecs: [],
};

// ---------------------------------------------------------------- formatting
function fmtTok(n) {
  if (n == null) return "–";
  const a = Math.abs(n);
  if (a < 1000) return String(Math.round(n));
  if (a < 1e6) return (n / 1000).toFixed(a < 10000 ? 1 : 0) + "k";
  return (n / 1e6).toFixed(2) + "M";
}
function fmtInt(n) { return n == null ? "–" : Math.round(n).toLocaleString("en-US"); }
function fmtCost(n) {
  if (n == null) return "n/a";
  if (Math.abs(n) < 0.01) return "$" + n.toFixed(4);
  if (Math.abs(n) < 10) return "$" + n.toFixed(3);
  return "$" + n.toFixed(2);
}
function fmtPct(x) { return x == null ? "–" : (x * 100).toFixed(x >= 0.995 || x < 0.1 ? 1 : 0) + "%"; }
function fmtTime(ts) {
  if (!ts) return "";
  const d = new Date(ts);
  return isNaN(d) ? "" : d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23" });
}
function relTime(sec) {
  const d = Date.now() / 1000 - sec;
  if (d < 60) return "just now";
  if (d < 3600) return Math.round(d / 60) + " min ago";
  if (d < 86400) return Math.round(d / 3600) + " h ago";
  return Math.round(d / 86400) + " d ago";
}
function catName(cat) {
  const c = (S.model ? S.model.categories : []).find((x) => x[0] === cat);
  return c ? c[1] : cat;
}

// ---------------------------------------------------------------- data
async function api(path) {
  const res = await fetch(path, { cache: "no-store" });
  if (!res.ok) throw new Error(path + " → " + res.status);
  return res.json();
}

function prepareTranscript(t) {
  for (const r of t.rows) {
    r.entries = r.base != null ? t.rows[r.base].entries.slice(0, r.keep).concat(r.add) : r.add;
    let sum = r.unattributed || 0;
    for (const e of r.entries) sum += e[1];
    r.size = r.total != null ? r.total : sum;
  }
}

function transcriptOf(key) {
  if (!S.model) return null;
  if (key === "main") return S.model.main;
  return S.model.agents.find((a) => a.id === key) || null;
}

async function loadSessions() {
  const data = await api("/api/sessions");
  S.sessions = data.sessions;
  S.latest = data.latest;
  renderSessionSelect();
  return data;
}

function renderSessionSelect() {
  const sel = $("#session-select");
  const groups = new Map();
  for (const s of S.sessions.slice(0, 400)) {
    const key = s.cwd || s.projectDir;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(s);
  }
  sel.textContent = "";
  for (const [key, list] of groups) {
    const og = document.createElement("optgroup");
    og.label = list[0].project + (key && key !== list[0].project ? "  —  " + key : "");
    for (const s of list) {
      const o = document.createElement("option");
      o.value = s.id;
      o.textContent = (s.title || s.id.slice(0, 8)) + "  ·  " + relTime(s.mtime) + (s.id === S.latest ? "  (latest)" : "");
      og.appendChild(o);
    }
    sel.appendChild(og);
  }
  if (S.current) sel.value = S.current;
}

function selectSession(id) {
  if (!id || id === S.current) return;
  S.current = id;
  S.model = null;
  S.revision = -1;
  S.generation = null;
  S.focus = null;
  S.highlight = null;
  S.expanded = new Set();
  closeDrawer();
  $("#session-select").value = id;
  renderEmpty("Loading session…");
  connectEvents(id);
  fetchModel(true);
}

function connectEvents(id) {
  if (S.es) S.es.close();
  const es = new EventSource("/api/events?id=" + encodeURIComponent(id));
  S.es = es;
  es.onopen = () => setLive(true);
  es.onerror = () => setLive(false);
  es.addEventListener("session", (ev) => {
    const d = JSON.parse(ev.data);
    if (d.id === S.current && (d.revision !== S.revision || d.generation !== S.generation)) fetchModel(false);
  });
  es.addEventListener("sessions", async (ev) => {
    const d = JSON.parse(ev.data);
    await loadSessions().catch(() => {});
    if (S.follow && d.latest && d.latest !== S.current) selectSession(d.latest);
  });
}

function setLive(on) {
  const live = $("#live");
  live.classList.toggle("on", on);
  live.classList.toggle("off", !on);
  $("#live-text").textContent = on ? "live" : "reconnecting";
}

async function fetchModel(first) {
  if (S.fetching) { S.refetch = true; return; }
  S.fetching = true;
  const id = S.current;
  try {
    const model = await api("/api/session?id=" + encodeURIComponent(id));
    if (id !== S.current) return;  // user switched session meanwhile
    if (model.generation === S.generation && model.revision < S.revision) return;  // stale answer
    const nearBottom = window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 160;
    prepareTranscript(model.main);
    for (const a of model.agents) prepareTranscript(a);
    S.model = model;
    if (S.generation && model.generation !== S.generation) closeDrawer();  // item numbers may have changed
    S.revision = model.revision;
    S.generation = model.generation;
    render();
    const noScroll = new URLSearchParams(location.search).get("scroll") === "0";
    if (S.autoscroll && !noScroll && (first || nearBottom)) window.scrollTo(0, document.documentElement.scrollHeight);
  } catch (err) {
    renderEmpty("Could not load the session: " + err.message);
  } finally {
    S.fetching = false;
    if (S.refetch) { S.refetch = false; fetchModel(false); }
  }
}

// ---------------------------------------------------------------- render
function readColors() {
  const css = getComputedStyle(document.documentElement);
  const cols = {};
  for (const name of ["tools", "system", "instructions", "skills", "reminders", "user", "assistant", "thinking",
    "tool_use", "tool_result", "compaction", "unattributed"]) {
    cols[name] = css.getPropertyValue("--c-" + name).trim();
  }
  for (const name of ["plot", "ink", "ink-2", "muted", "hatch", "mark", "mark-edge", "cache-read", "cache-write",
    "cache-none", "grid", "font-ui"]) {
    cols[name] = css.getPropertyValue("--" + name).trim();
  }
  S.colors = cols;
  hatchCache = {};
}

// Sticky offsets and the hero horizon depend on rendered sizes (wrapping, fonts, window width).
function measureLayout() {
  const root = document.documentElement.style;
  root.setProperty("--topbar-h", $("#topbar").offsetHeight + "px");
  root.setProperty("--keybar-h", $("#keybar").offsetHeight + "px");
  $("#scene").style.setProperty("--horizon", Math.max(40, $("#kpis").offsetTop - 10) + "px");
}

function renderEmpty(msg) {
  const rows = $("#rows");
  rows.textContent = "";
  rows.appendChild(el("div", "empty", msg));
}

function render() {
  readColors();
  renderMeta();
  renderKpis();
  renderLegend();
  renderRows();
  renderTop();
  measureLayout();
}

function renderMeta() {
  const m = S.model;
  const box = $("#meta");
  box.textContent = "";
  box.appendChild(el("span", "title", m.main.title || m.session.title || m.session.id.slice(0, 8)));
  const path = el("span", "path", m.session.cwd || m.session.project);
  path.title = m.session.cwd || "";
  box.appendChild(path);
  const rows = m.main.rows;
  if (m.main.mode === "request") {
    const ok = rows.filter((r) => r.state === "verified").length;
    const b = el("span", "badge exact", "✓ Exact payloads · " + ok + "/" + rows.length + " verified");
    b.title = "Claude Code logged each API request. The dashboard rebuilt every payload and checked it against its digest.";
    box.appendChild(b);
  } else {
    const b = el("span", "badge est", "≈ Estimated from transcript");
    b.title = "This log has no request records (older Claude Code). The context is inferred from the transcript.";
    box.appendChild(b);
  }
  if (m.agents.length) box.appendChild(el("span", "badge", m.agents.length + " subagent" + (m.agents.length > 1 ? "s" : "")));
  const errors = m.main.errors.concat(...m.agents.map((a) => a.errors));
  if (errors.length) {
    const b = el("button", "badge est", "! " + errors.length + " API error" + (errors.length > 1 ? "s" : ""));
    b.title = "Responses that failed. They are not counted as requests. Click to see them.";
    b.onclick = () => {
      const body = openDrawer([el("div", null, "API errors"), el("div", "sub", "Failed responses in this session")]);
      for (const e of errors) {
        body.appendChild(el("h3", null, fmtTime(e.ts)));
        body.appendChild(el("pre", "content", e.text));
      }
    };
    box.appendChild(b);
  }
  if (m.main.lastTs) box.appendChild(el("span", "badge", "last write " + fmtTime(m.main.lastTs)));
}

function kpi(label, value, sub, title, gauge) {
  const k = el("div", "kpi" + (gauge != null ? " kpi--hero" : ""));
  k.appendChild(el("div", "label", label));
  k.appendChild(el("div", "value", value));
  if (gauge != null) {
    const g = el("div", "gauge" + (gauge > 0.8 ? " high" : ""));
    const fill = el("i");
    fill.style.width = Math.min(100, gauge * 100).toFixed(1) + "%";
    g.appendChild(fill);
    k.appendChild(g);
  }
  if (sub) k.appendChild(el("div", "sub", sub));
  if (title) k.title = title;
  return k;
}

function renderKpis() {
  const sum = S.model.summary;
  const main = sum.main, all = sum.all;
  const box = $("#kpis");
  box.textContent = "";
  const lastMain = [...S.model.main.rows].reverse().find((r) => r.total != null);
  const win = lastMain && lastMain.contextWindow;
  const used = lastMain && win ? lastMain.total / win : 0;
  box.appendChild(kpi("Current context", lastMain ? fmtTok(lastMain.total) : "–",
    lastMain ? (win ? (used > 0.8 ? "! " : "") + fmtPct(used) + " of " + fmtTok(win) + " window · " : "") +
      "request #" + (lastMain.index + 1) : "no requests yet",
    "Input tokens of the latest main-thread request.", used));
  box.appendChild(kpi("Peak context", fmtTok(main.peak),
    win ? fmtPct(main.peak / win) + " of window" : "biggest single request",
    "Input tokens of the biggest main-thread request."));
  box.appendChild(kpi("Requests", fmtInt(main.requests),
    sum.agentCount ? "+ " + fmtInt(sum.agents.requests) + " in " + sum.agentCount + " subagents" : "main thread",
    "Number of API requests with a logged response."));
  box.appendChild(kpi("Input tokens read", fmtTok(all.input), "sum over all requests",
    "Every request re-reads the whole context. This is the sum of all of them (main + subagents)."));
  box.appendChild(kpi("Cache hit", fmtPct(all.cacheHit), fmtTok(all.cacheWrite) + " written to cache",
    "Cache read tokens / all input tokens, weighted by size."));
  box.appendChild(kpi("Output tokens", fmtTok(all.output), "incl. thinking", "Tokens the model generated."));
  const saved = all.uncachedCost - all.cost;
  box.appendChild(kpi("Est. cost (API)", fmtCost(all.cost),
    (saved >= 0 ? "cache saved " + fmtCost(saved) : "cache cost " + fmtCost(-saved) + " extra") +
      (all.costUnknown ? " · " + all.costUnknown + " n/a" : ""),
    "Estimated API-equivalent USD from pricing.json (" + (S.model.pricing.source || "") + ", checked " +
      (S.model.pricing.checked || "?") + "). Subscription plans are not billed this way."));
}

function presentCats() {
  const used = new Set();
  const scan = (t) => { for (const r of t.rows) for (const c in r.cats) if (r.cats[c] > 0) used.add(c); };
  scan(S.model.main);
  if (S.showAgents) S.model.agents.forEach(scan);
  return S.model.categories.filter(([c]) => used.has(c));
}

function renderLegend() {
  const box = $("#legend");
  box.textContent = "";
  for (const [cat, name] of presentCats()) {
    const chip = el("button", "chip");
    chip.setAttribute("aria-pressed", String(S.highlight === cat));
    const sw = el("span", "sw" + (cat === "unattributed" ? " hatch" : ""));
    sw.style.backgroundColor = S.colors[cat];
    chip.appendChild(sw);
    chip.appendChild(el("span", null, name));
    chip.title = CAT_HELP[cat] + "\nClick to highlight.";
    if (S.highlight) chip.classList.add(S.highlight === cat ? "on" : "dim");
    chip.onclick = () => { S.highlight = S.highlight === cat ? null : cat; renderLegend(); redrawAll(); };
    box.appendChild(chip);
  }
  box.appendChild(el("span", "sep"));
  box.appendChild(el("span", "ctl-label", "Cache"));
  for (const [key, name, help] of [
    ["cache-read", "Read", "Input read from the prompt cache (cheapest). Dark part of the strip."],
    ["cache-write", "Write", "Input written to the cache this request (costs extra once). Mid part of the strip."],
    ["cache-none", "Not cached", "Input processed at full price. Bright part of the strip."],
  ]) {
    const chip = el("span", "chip static");
    const sw = el("span", "sw");
    sw.style.backgroundColor = S.colors[key];
    chip.appendChild(sw);
    chip.appendChild(el("span", null, name));
    chip.title = help + " Thin strip under each bar. Exact numbers.";
    box.appendChild(chip);
  }
}

function scaleMax() {
  const m = S.model;
  let peak = 1, win = 0;
  const scan = (t) => { for (const r of t.rows) { peak = Math.max(peak, r.size); win = Math.max(win, r.contextWindow || 0); } };
  scan(m.main);
  if (S.showAgents) m.agents.forEach(scan);
  return S.scale === "window" && win ? Math.max(win, peak) : peak;
}

let observer = null;
function renderRows() {
  const box = $("#rows");
  box.textContent = "";
  if (observer) observer.disconnect();
  observer = new IntersectionObserver((entries) => {
    for (const en of entries) if (en.isIntersecting) { const rec = en.target._rec; if (rec && !rec.drawn) drawRow(rec); }
  }, { rootMargin: "300px 0px" });
  S.rowRecs = [];
  S.scaleMax = scaleMax();
  const m = S.model;
  if (!m.main.rows.length) {
    box.appendChild(el("div", "empty", "No requests in this session yet."));
  }
  const children = new Map();  // parent key -> list of agents
  for (const a of m.agents) {
    const key = a.parent == null ? "unlinked" : a.parent + ":" + a.parentRow;
    if (!children.has(key)) children.set(key, []);
    children.get(key).push(a);
  }
  const emitTranscript = (t, key, depth) => {
    for (const r of t.rows) {
      box.appendChild(makeRow(t, key, r, depth));
      if (!S.showAgents) continue;
      for (const a of children.get(key + ":" + r.index) || []) emitAgent(a, depth + 1);
    }
  };
  const emitAgent = (a, depth) => {
    box.appendChild(makeGroupHead(a, depth));
    if (S.expanded.has(a.id)) emitTranscript(a, a.id, depth);
  };
  emitTranscript(m.main, "main", 0);
  const unlinked = children.get("unlinked") || [];
  if (S.showAgents && unlinked.length) {
    box.appendChild(el("div", "section-head", "Subagents not linked to a request"));
    for (const a of unlinked) emitAgent(a, 1);
  }
}

function makeGroupHead(a, depth) {
  const head = el("button", "group-head");
  head.setAttribute("aria-expanded", String(S.expanded.has(a.id)));
  head.style.paddingLeft = (12 + depth * 20) + "px";
  const open = S.expanded.has(a.id);
  head.appendChild(el("span", "caret", open ? "▾" : "▸"));
  head.appendChild(el("span", "kind", "Subagent · " + a.type));
  head.appendChild(el("span", null, a.description));
  let cost = 0, peak = 0, unknown = 0;
  for (const r of a.rows) {
    peak = Math.max(peak, r.total || 0);
    if (r.cost == null) unknown += r.usage ? 1 : 0; else cost += r.cost;
  }
  const costText = unknown && !cost ? "cost n/a" : fmtCost(cost) + (unknown ? " + " + unknown + " n/a" : "");
  head.appendChild(el("span", "badge", a.rows.length + " requests · peak " + fmtTok(peak) + " · " + costText));
  if (a.mode !== "request") head.appendChild(el("span", "badge est", "estimated"));
  head.onclick = () => {
    if (S.expanded.has(a.id)) S.expanded.delete(a.id); else S.expanded.add(a.id);
    const y = window.scrollY;
    renderRows();
    window.scrollTo(0, y);
  };
  return head;
}

function makeRow(t, key, r, depth) {
  const row = el("div", "row" + (depth ? " agent" : ""));
  if (depth) row.style.paddingLeft = (12 + depth * 20) + "px";
  if (S.focus && S.focus.t === key && S.focus.i === r.index) row.classList.add("focus");
  const lbl = el("button", "lbl");
  const l1 = el("div", "l1");
  l1.appendChild(el("span", "num", "#" + (r.index + 1)));
  l1.appendChild(el("span", "time", "·"));
  l1.appendChild(el("span", "size", (r.total == null ? "≈" : "") + fmtTok(r.size)));
  const st = r.total == null ? ["…", "warn", "Waiting for the response."] : (STATE_INFO[r.state] || ["", "", r.state]);
  const stEl = el("span", "st " + st[1], st[0]);
  stEl.title = st[2];
  l1.appendChild(stEl);
  const prev = t.rows[r.index - 1];
  if (!prev || prev.model !== r.model) l1.appendChild(el("span", "badge", r.modelLabel || r.model || "?"));
  if (r.source && r.source !== "main" && r.source !== "repl_main_thread") l1.appendChild(el("span", "badge", r.source));
  lbl.appendChild(l1);
  const u = r.usage;
  const l2 = el("div", "l2");
  l2.appendChild(el("span", "time", fmtTime(r.ts)));
  if (u && r.total) {
    const hit = u.cacheRead / r.total;
    const low = hit < 0.8 && r.index > 0;  // the first request cannot reuse this session's cache yet
    l2.appendChild(document.createTextNode(" · "));
    const c = el("span", low ? "lowcache" : null, (low ? "! " : "") + fmtPct(hit) + " cache");
    if (low) c.title = "Low cache hit: most of this request was paid at full price or written to the cache.";
    l2.appendChild(c);
  }
  if (r.cost != null) l2.appendChild(document.createTextNode(" · " + fmtCost(r.cost)));
  lbl.appendChild(l2);
  lbl.title = "Click for request details";
  lbl.onclick = () => openRequest(t, key, r);
  const canvas = document.createElement("canvas");
  canvas.tabIndex = 0;
  canvas.setAttribute("role", "button");
  canvas.setAttribute("aria-label", "Request " + (r.index + 1) + ": " + fmtTok(r.size) + " input tokens. Press Enter for details.");
  canvas.addEventListener("keydown", (ev) => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); openRequest(t, key, r); } });
  row.appendChild(lbl);
  row.appendChild(canvas);
  const rec = { t, key, r, row, canvas, drawn: false, segs: [] };
  canvas._rec = rec;
  canvas.addEventListener("mousemove", (ev) => hover(rec, ev));
  canvas.addEventListener("mouseleave", hideTip);
  canvas.addEventListener("click", (ev) => clickBar(rec, ev));
  S.rowRecs.push(rec);
  observer.observe(canvas);
  return row;
}

function redrawAll() {
  for (const rec of S.rowRecs) {
    rec.drawn = false;
    const b = rec.canvas.getBoundingClientRect();
    if (b.bottom > -300 && b.top < window.innerHeight + 300) drawRow(rec);
  }
}

// Build segments for one row. Grouped: one per category in fixed order.
// Payload order: consecutive items of the same category are merged.
function rowSegments(rec) {
  const { t, r } = rec;
  const segs = [];
  if (S.view === "grouped") {
    for (const [cat] of S.model.categories) {
      const tok = r.cats[cat] || 0;
      if (tok > 0) segs.push({ cat, tok, grouped: true });
    }
    return segs;
  }
  let cur = null;
  r.entries.forEach((e, n) => {
    const cat = t.items[e[0]][0];
    const isNew = n >= r.keep && r.base != null;
    if (cur && cur.cat === cat && cur.isNew === isNew) {
      cur.tok += e[1];
      cur.idx.push(n);
    } else {
      cur = { cat, tok: e[1], idx: [n], isNew, start: n };
      segs.push(cur);
    }
  });
  if (r.unattributed > 0) {
    // Older logs: the unmatched part is mostly system prompt + tools, which come first in the payload.
    const seg = { cat: "unattributed", tok: r.unattributed, idx: [] };
    if (t.mode === "fallback") segs.unshift(seg); else segs.push(seg);
  }
  return segs;
}

let hatchCache = {};
function hatch(ctx, color, bg) {
  const key = color + bg;
  if (hatchCache[key]) return hatchCache[key];
  const c = document.createElement("canvas");
  c.width = c.height = 6;
  const g = c.getContext("2d");
  g.fillStyle = bg; g.fillRect(0, 0, 6, 6);
  g.strokeStyle = color; g.lineWidth = 1;
  g.beginPath(); g.moveTo(0, 6); g.lineTo(6, 0); g.moveTo(-1, 1); g.lineTo(1, -1); g.moveTo(5, 7); g.lineTo(7, 5); g.stroke();
  hatchCache[key] = ctx.createPattern(c, "repeat");
  return hatchCache[key];
}

function drawRow(rec) {
  const c = rec.canvas;
  const w = c.clientWidth;
  if (!w) return;
  const h = 30, dpr = window.devicePixelRatio || 1;
  c.width = Math.round(w * dpr);
  c.height = Math.round(h * dpr);
  const ctx = c.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, w, h);
  const col = S.colors;
  const per = w / S.scaleMax;
  const barY = 3, barH = 17, stripY = 23, stripH = 5;
  // scale guides: behind the bars, visible only in empty space
  const step = S.scaleMax < 400000 ? 50000 : S.scaleMax <= 1000000 ? 100000 : 250000;
  ctx.fillStyle = col.grid;
  for (let g = step; g < S.scaleMax; g += step) ctx.fillRect(Math.round(g * per), barY, 1, stripY + stripH - barY);
  if (S.scale === "window" && rec.r.contextWindow) {
    const wx = Math.round(rec.r.contextWindow * per);
    if (wx <= w) { ctx.fillStyle = col.muted; ctx.fillRect(Math.min(wx, w - 1), barY - 2, 1, stripY + stripH - barY + 2); }
  }
  const segs = rowSegments(rec);
  rec.segs = [];
  let x = 0;
  segs.forEach((s, n) => {
    const sw = s.tok * per;
    const last = n === segs.length - 1;
    const gap = sw >= 5 && !last ? 2 : 0;
    ctx.globalAlpha = S.highlight && S.highlight !== s.cat ? 0.22 : 1;
    ctx.fillStyle = s.cat === "unattributed" ? hatch(ctx, col.hatch, col.unattributed) : col[s.cat];
    const drawW = Math.max(sw - gap, 0.6);
    if (last && drawW > 6 && ctx.roundRect) {
      ctx.beginPath();
      ctx.roundRect(x, barY, drawW, barH, [0, 4, 4, 0]);
      ctx.fill();
    } else {
      ctx.fillRect(x, barY, drawW, barH);
    }
    if (s.isNew && sw >= 1) {
      ctx.globalAlpha = 1;
      ctx.fillStyle = col.mark;
      ctx.fillRect(x, 0, Math.max(drawW, 1), 2);
    }
    rec.segs.push({ ...s, x0: x, x1: x + sw, y0: 0, y1: barY + barH + 1 });
    x += sw;
  });
  ctx.globalAlpha = 1;
  // cache strip (exact)
  const u = rec.r.usage;
  if (u && rec.r.total) {
    const parts = [["cache-read", u.cacheRead, "Cache read"], ["cache-write", u.cacheWrite, "Cache write"], ["cache-none", u.input, "Not cached"]];
    let sx = 0;
    for (const [key, tok, name] of parts) {
      const sw = tok * per;
      if (sw <= 0) continue;
      ctx.fillStyle = col[key];
      ctx.fillRect(sx, stripY, Math.max(sw - (sw > 4 ? 1 : 0), 0.6), stripH);
      rec.segs.push({ cache: true, name, tok, key, x0: sx, x1: sx + sw, y0: stripY - 1, y1: h });
      sx += sw;
    }
  } else if (!u) {
    ctx.fillStyle = col.muted;
    ctx.font = "italic 11px " + col["font-ui"];
    ctx.fillText("waiting for response…", Math.min(x + 6, Math.max(w - 130, 0)), barY + 12);
  }
  // cache breakpoints (payload order only), drawn last so the strip does not cover them
  if (S.view === "timeline" && rec.r.markers.length) {
    const cum = [];
    let acc = rec.t.mode === "fallback" ? rec.r.unattributed : 0;
    for (const e of rec.r.entries) { acc += e[1]; cum.push(acc); }
    ctx.fillStyle = col.mark;
    ctx.strokeStyle = col["mark-edge"];
    ctx.lineWidth = 1;
    for (const mk of rec.r.markers) {
      if (mk.after >= cum.length) continue;
      const mx = cum[mk.after] * per;
      ctx.beginPath();
      ctx.moveTo(mx - 3, barY + barH + 4);
      ctx.lineTo(mx + 3, barY + barH + 4);
      ctx.lineTo(mx, barY + barH);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    }
  }
  rec.drawn = true;
}

function segAt(rec, ev) {
  const b = rec.canvas.getBoundingClientRect();
  const x = ev.clientX - b.left, y = ev.clientY - b.top;
  let best = null, bestD = 1e9;
  for (const s of rec.segs) {
    if (y < s.y0 || y > s.y1) continue;
    const d = x < s.x0 ? s.x0 - x : x > s.x1 ? x - s.x1 : 0;
    if (d < bestD) { bestD = d; best = s; }
  }
  return bestD <= 4 ? best : null;
}

const tip = () => $("#tooltip");
function hideTip() { tip().style.display = "none"; }
function hover(rec, ev) {
  const s = segAt(rec, ev);
  if (!s) { hideTip(); return; }
  const t = tip();
  t.textContent = "";
  const head = el("div", "h");
  const sw = el("span", "sw");
  const r = rec.r;
  if (s.cache) {
    sw.style.backgroundColor = S.colors[s.key];
    head.appendChild(sw);
    head.appendChild(el("span", null, s.name + ": " + fmtInt(s.tok) + " tokens"));
    t.appendChild(head);
    t.appendChild(el("div", "d", fmtPct(s.tok / r.total) + " of this request's input (exact)"));
  } else {
    sw.style.backgroundColor = S.colors[s.cat];
    head.appendChild(sw);
    head.appendChild(el("span", null, catName(s.cat) + ": ≈" + fmtTok(s.tok) + " tokens"));
    t.appendChild(head);
    t.appendChild(el("div", "d", fmtPct(s.tok / r.size) + " of request #" + (r.index + 1)));
    if (s.idx && s.idx.length === 1) t.appendChild(el("div", "d", rec.t.items[r.entries[s.idx[0]][0]][1]));
    else if (s.idx && s.idx.length > 1) t.appendChild(el("div", "d", s.idx.length + " items" + (s.isNew ? " (new in this request)" : "")));
    if (s.grouped) {
      const n = r.entries.filter((e) => rec.t.items[e[0]][0] === s.cat).length;
      if (n) t.appendChild(el("div", "d", n + " item" + (n > 1 ? "s" : "")));
    }
    t.appendChild(el("div", "d", "Click to see the content"));
  }
  t.style.display = "block";
  const pad = 14;
  let left = ev.clientX + pad, top = ev.clientY + pad;
  const tw = t.offsetWidth, th = t.offsetHeight;
  if (left + tw > window.innerWidth - 8) left = ev.clientX - tw - pad;
  if (top + th > window.innerHeight - 8) top = ev.clientY - th - pad;
  t.style.left = Math.max(8, left) + "px";
  t.style.top = Math.max(8, top) + "px";
}

function clickBar(rec, ev) {
  const s = segAt(rec, ev);
  if (!s || s.cache) { openRequest(rec.t, rec.key, rec.r); return; }
  openSegment(rec, s);
}

// ---------------------------------------------------------------- drawer
function openDrawer(titleNodes) {
  const title = $("#drawer-title");
  title.textContent = "";
  for (const n of titleNodes) title.appendChild(n);
  $("#drawer-body").textContent = "";
  if (!$("#drawer").classList.contains("open")) S.returnFocus = document.activeElement;
  $("#drawer").classList.add("open");
  $("#drawer").setAttribute("aria-hidden", "false");
  $("#drawer").inert = false;
  $("#drawer-close").focus({ preventScroll: true });
  hideTip();
  return $("#drawer-body");
}
function closeDrawer() {
  const wasOpen = $("#drawer").classList.contains("open");
  $("#drawer").classList.remove("open");
  $("#drawer").setAttribute("aria-hidden", "true");
  $("#drawer").inert = true;
  if (wasOpen && S.returnFocus && document.contains(S.returnFocus)) S.returnFocus.focus({ preventScroll: true });
}

function rowName(key, r) {
  if (key === "main") return "Request #" + (r.index + 1);
  const a = transcriptOf(key);
  return "Subagent " + (a ? a.type : "") + " · request #" + (r.index + 1);
}

function openSegment(rec, s) {
  const { t, key, r } = rec;
  const name = el("div", null);
  const swatch = el("span", "sw");
  swatch.style.cssText = "display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:6px;vertical-align:-1px;background:" + S.colors[s.cat];
  name.appendChild(swatch);
  name.appendChild(document.createTextNode(catName(s.cat)));
  const sub = el("div", "sub", rowName(key, r) + " · ≈" + fmtInt(s.tok) + " tokens · " + fmtPct(s.tok / r.size) + " of the request");
  const body = openDrawer([name, sub]);
  body.appendChild(el("p", "hint", CAT_HELP[s.cat] || ""));
  if (s.cat === "unattributed") return;
  let idxs;
  if (s.grouped) {
    idxs = [];
    r.entries.forEach((e, n) => { if (t.items[e[0]][0] === s.cat) idxs.push(n); });
    idxs.sort((a, b) => r.entries[b][1] - r.entries[a][1]);
  } else {
    idxs = s.idx;
  }
  renderItemList(body, t, key, r, idxs);
}

function renderItemList(body, t, key, r, idxs) {
  body.appendChild(el("h3", null, idxs.length + " item" + (idxs.length === 1 ? "" : "s")));
  const ul = el("ul", "items");
  const view = el("div");
  const addItems = (list) => { for (const n of list) ul.appendChild(itemLi(n)); };
  const itemLi = (n) => {
    const [itemIdx, tok] = r.entries[n];
    const it = t.items[itemIdx];
    const li = el("li");
    const sw = el("span", "sw");
    sw.style.backgroundColor = S.colors[it[0]];
    const nm = el("span", "nm", it[1]);
    if (it[3] === r.index) nm.appendChild(el("span", "new", "new"));
    else if (it[3] != null) nm.appendChild(el("span", "badge", "since #" + (it[3] + 1)));
    li.appendChild(sw);
    li.appendChild(nm);
    li.appendChild(el("span", "tk", "≈" + fmtTok(tok)));
    li.tabIndex = 0;
    li.setAttribute("role", "button");
    li.onclick = () => {
      ul.querySelectorAll("li.sel").forEach((x) => x.classList.remove("sel"));
      li.classList.add("sel");
      loadItem(view, key, itemIdx, tok);
    };
    li.onkeydown = (ev) => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); li.click(); } };
    return li;
  };
  const LIMIT = 300;
  addItems(idxs.slice(0, LIMIT));
  body.appendChild(ul);
  if (idxs.length > LIMIT) {
    const more = el("button", "icon-btn", "Show all " + idxs.length + " items");
    more.onclick = () => { addItems(idxs.slice(LIMIT)); more.remove(); };
    body.appendChild(more);
  }
  body.appendChild(view);
  if (idxs.length === 1) ul.firstChild.click();
}

async function loadItem(view, key, itemIdx, tok) {
  const token = {};
  view._token = token;
  const session = S.current;
  view.textContent = "";
  view.appendChild(el("h3", null, "Content"));
  const p = el("p", "hint", "Loading…");
  view.appendChild(p);
  try {
    const d = await api("/api/item?id=" + encodeURIComponent(session) + "&agent=" + encodeURIComponent(key) + "&item=" + itemIdx + "&gen=" + encodeURIComponent(S.generation || ""));
    if (view._token !== token || session !== S.current) return;  // a newer click won
    p.textContent = fmtInt(d.chars) + " characters · ≈" + fmtInt(tok) + " tokens" +
      (d.firstRow != null ? " · first sent in request #" + (d.firstRow + 1) : "") +
      (d.truncated ? " · truncated for display" : "");
    if (d.hidden) view.appendChild(el("p", "note", "Hidden thinking: the text is not returned by the API, only an encrypted signature. Size comes from the reported thinking tokens."));
    view.appendChild(el("pre", "content", d.content || "(empty)"));
  } catch (err) {
    if (view._token === token) p.textContent = "Could not load: " + err.message;
  }
}

function openRequest(t, key, r) {
  S.focus = { t: key, i: r.index };
  document.querySelectorAll(".row.focus").forEach((x) => x.classList.remove("focus"));
  const rec = S.rowRecs.find((x) => x.key === key && x.r.index === r.index);
  if (rec) rec.row.classList.add("focus");
  renderTop();
  const body = openDrawer([el("div", null, rowName(key, r)),
    el("div", "sub", [fmtTime(r.ts), r.modelLabel || r.model, r.effort ? "effort " + r.effort : null, r.source].filter(Boolean).join(" · "))]);
  const st = STATE_INFO[r.state];
  if (st) body.appendChild(el("p", "hint", st[2]));
  if (r.note) body.appendChild(el("p", "note", r.note));
  const u = r.usage;
  body.appendChild(el("h3", null, "Tokens (exact, from the API response)"));
  const kv = el("table", "kv");
  const add = (k, v) => { const tr = el("tr"); tr.appendChild(el("td", null, k)); tr.appendChild(el("td", null, v)); kv.appendChild(tr); };
  if (u) {
    add("Input, total", fmtInt(r.total));
    add("  read from cache", fmtInt(u.cacheRead) + "  (" + fmtPct(u.cacheRead / r.total) + ")");
    add("  written to cache (5 min)", fmtInt(u.cacheWrite5m));
    add("  written to cache (1 h)", fmtInt(u.cacheWrite1h));
    add("  not cached", fmtInt(u.input));
    add("Output", fmtInt(u.output) + (u.thinking ? "  (thinking " + fmtInt(u.thinking) + ")" : ""));
    if (r.contextWindow) add("Context window used", fmtPct(r.total / r.contextWindow) + " of " + fmtTok(r.contextWindow));
    add("Est. cost (API-equivalent)", fmtCost(r.cost));
    add("Same request without cache", fmtCost(r.uncachedCost));
  } else {
    add("Response", "not logged yet");
  }
  body.appendChild(kv);
  body.appendChild(el("h3", null, "Content by type (≈ estimated split) · click a type to see its items"));
  const kv2 = el("table", "kv");
  const cats = Object.entries(r.cats).sort((a, b) => b[1] - a[1]);
  for (const [cat, tok] of cats) {
    const tr = el("tr");
    if (cat !== "unattributed") {
      tr.tabIndex = 0;
      tr.setAttribute("role", "button");
      tr.title = "Show the items of this type";
      tr.style.cursor = "pointer";
      tr.onclick = () => openSegment({ t, key, r }, { cat, tok, grouped: true });
      tr.onkeydown = (ev) => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); tr.click(); } };
    }
    const td = el("td");
    const sw = el("span");
    sw.style.cssText = "display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px;background:" + S.colors[cat];
    td.appendChild(sw);
    td.appendChild(document.createTextNode(catName(cat)));
    tr.appendChild(td);
    tr.appendChild(el("td", null, "≈" + fmtInt(tok) + "  (" + fmtPct(tok / r.size) + ")"));
    kv2.appendChild(tr);
  }
  body.appendChild(kv2);
  if (r.markers.length) body.appendChild(el("p", "hint", r.markers.length + " cache breakpoints in this request (▲ in payload order view)."));
  const newIdx = [];
  r.entries.forEach((e, n) => { if (t.items[e[0]][3] === r.index) newIdx.push(n); });
  if (newIdx.length) {
    body.appendChild(el("h3", null, "New in this request"));
    renderItemList(body, t, key, r, newIdx);
  }
}

function renderTop() {
  const m = S.model;
  let key = "main", t = m.main, r = null;
  if (S.focus) {
    t = transcriptOf(S.focus.t) || m.main;
    key = t === m.main ? "main" : S.focus.t;
    r = t.rows[S.focus.i] || null;
  }
  if (!r) {
    key = "main"; t = m.main;
    r = [...t.rows].reverse().find((x) => x.total != null) || t.rows[t.rows.length - 1];
  }
  const tbody = $("#top-table tbody");
  tbody.textContent = "";
  $("#top-title").textContent = "Largest items";
  if (!r) return;
  $("#top-hint").textContent = rowName(key, r) + " · ≈" + fmtTok(r.size) + " tokens. Click an item to see it.";
  const order = r.entries.map((e, n) => n).sort((a, b) => r.entries[b][1] - r.entries[a][1]).slice(0, 14);
  for (const n of order) {
    const [itemIdx, tok] = r.entries[n];
    const it = t.items[itemIdx];
    const tr = el("tr");
    const td1 = el("td", "name");
    const sw = el("span", "sw");
    sw.style.backgroundColor = S.colors[it[0]];
    td1.appendChild(sw);
    td1.appendChild(document.createTextNode(it[1]));
    td1.appendChild(el("span", "cat", catName(it[0])));
    tr.appendChild(td1);
    tr.appendChild(el("td", "tok", "≈" + fmtTok(tok)));
    tr.title = catName(it[0]) + (it[3] != null ? " · first sent in request #" + (it[3] + 1) : "");
    tr.tabIndex = 0;
    tr.setAttribute("role", "button");
    tr.setAttribute("aria-label", it[1] + ", " + catName(it[0]) + ", about " + fmtTok(tok) + " tokens");
    tr.onkeydown = (ev) => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); tr.click(); } };
    tr.onclick = () => {
      const body = openDrawer([el("div", null, it[1]), el("div", "sub", catName(it[0]) + " · " + rowName(key, r))]);
      body.appendChild(el("p", "hint", CAT_HELP[it[0]] || ""));
      const view = el("div");
      body.appendChild(view);
      loadItem(view, key, itemIdx, tok);
    };
    tbody.appendChild(tr);
  }
  if (r.unattributed > 0) {
    const tr = el("tr");
    const td1 = el("td", "name");
    const sw = el("span", "sw hatch");
    sw.style.backgroundColor = S.colors.unattributed;
    td1.appendChild(sw);
    td1.appendChild(document.createTextNode("Not attributed"));
    tr.appendChild(td1);
    tr.appendChild(el("td", "tok", "≈" + fmtTok(r.unattributed)));
    tr.title = CAT_HELP.unattributed;
    tbody.appendChild(tr);
  }
}

// ---------------------------------------------------------------- controls
function setSeg(attr, value) {
  document.querySelectorAll("[data-" + attr + "]").forEach((b) => {
    b.classList.toggle("on", b.dataset[attr] === value);
    b.setAttribute("aria-pressed", String(b.dataset[attr] === value));
  });
}

// Visual effects (glow, blur, hero scene, animation). Colours never change, so no redraw is needed.
const highContrast = window.matchMedia("(prefers-contrast: more), (forced-colors: active)");
function applyFx() {
  const forcedOff = highContrast.matches || new URLSearchParams(location.search).get("fx") === "0";
  const on = !forcedOff && store.get("fx", true);
  document.documentElement.dataset.fx = on ? "on" : "off";
  $("#fx-btn").setAttribute("aria-pressed", String(on));
  $("#fx-btn").disabled = highContrast.matches;
}

function init() {
  applyFx();
  highContrast.addEventListener("change", applyFx);
  setSeg("view", S.view);
  setSeg("scale", S.scale);
  $("#follow").checked = S.follow;
  $("#show-agents").checked = S.showAgents;
  $("#autoscroll").checked = S.autoscroll;

  document.querySelectorAll("[data-view]").forEach((b) => b.onclick = () => {
    S.view = b.dataset.view; store.set("view", S.view); setSeg("view", S.view); redrawAll();
  });
  document.querySelectorAll("[data-scale]").forEach((b) => b.onclick = () => {
    S.scale = b.dataset.scale; store.set("scale", S.scale); setSeg("scale", S.scale);
    if (S.model) { S.scaleMax = scaleMax(); redrawAll(); }
  });
  $("#follow").onchange = (e) => {
    S.follow = e.target.checked; store.set("follow", S.follow);
    if (S.follow && S.latest) selectSession(S.latest);
  };
  $("#show-agents").onchange = (e) => { S.showAgents = e.target.checked; store.set("showAgents", S.showAgents); if (S.model) render(); };
  $("#autoscroll").onchange = (e) => { S.autoscroll = e.target.checked; store.set("autoscroll", S.autoscroll); };
  $("#session-select").onchange = (e) => {
    if (e.target.value !== S.latest && S.follow) { S.follow = false; $("#follow").checked = false; store.set("follow", false); }
    selectSession(e.target.value);
  };
  $("#fx-btn").onclick = () => {
    store.set("fx", document.documentElement.dataset.fx !== "on");
    applyFx();
  };
  $("#drawer-close").onclick = closeDrawer;
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeDrawer(); });
  let rt = null;
  new ResizeObserver(() => { clearTimeout(rt); rt = setTimeout(() => { if (S.model) redrawAll(); }, 80); }).observe($("#rows"));
  const layout = new ResizeObserver(() => measureLayout());
  for (const id of ["#topbar", "#keybar", "#meta"]) layout.observe($(id));
  if (document.fonts) document.fonts.ready.then(measureLayout);
  readColors();

  loadSessions().then((d) => {
    const params = new URLSearchParams(location.search);
    const want = params.get("session");
    if (want) { S.follow = false; $("#follow").checked = false; }
    const id = want || d.latest;
    if (id) selectSession(id); else renderEmpty("No Claude Code sessions found.");
  }).catch((err) => renderEmpty("Could not reach the server: " + err.message));
}

function showError(msg) {
  const box = $("#rows");
  const note = el("div", "empty", "Something went wrong in the page: " + msg);
  box.prepend(note);
}
window.addEventListener("error", (e) => showError(e.message + " (" + (e.filename || "").split("/").pop() + ":" + e.lineno + ")"));
window.addEventListener("unhandledrejection", (e) => showError(String(e.reason && e.reason.stack || e.reason)));

init();
