// image-style for ComfyUI: /command autocomplete and a live preview under the "request" box.
// It never rewrites your graph. It only reads the request text and the node's settings, and asks
// the node's own Python code (/imagestyle/expand) what the result would be, so the rules live in one place.
import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

const OUR_NODES = new Set(["ImageStylePrompt", "ImageStylePromptAllRatios"]);
const SETTINGS = ["style", "default_ratio", "megapixels", "ratio_pick", "extra_negative",
  "add_base_negative", "fold_negatives_into_prompt", "plain_english"];
const MAX_SUGGESTIONS = 8;

let commands = null;          // [{n, c, p}] from the server
let panel = null;             // floating box (suggestions + preview)
let sugEl = null;
let prevEl = null;
let active = null;            // { el: textarea, node }
let items = [];               // current suggestions
let selected = 0;
let timer = null;
let reqSeq = 0;
let hideTimer = null;

async function loadCommands() {
  if (commands) return commands;
  try {
    const r = await api.fetchApi("/imagestyle/commands");
    commands = r.ok ? await r.json() : [];
  } catch (e) {
    commands = [];
  }
  return commands;
}

function ensurePanel() {
  if (panel) return;
  const css = document.createElement("style");
  css.textContent = `
    .imgstyle-panel{position:fixed;z-index:10000;display:none;box-sizing:border-box;max-height:42vh;overflow:auto;
      background:#1b1b22;color:#e8e6f4;border:1px solid #4b4690;border-radius:8px;box-shadow:0 8px 24px #0009;
      font:12px/1.45 system-ui,sans-serif}
    .imgstyle-sug{border-bottom:1px solid #34324d}
    .imgstyle-row{display:flex;gap:8px;padding:5px 9px;cursor:pointer;align-items:baseline}
    .imgstyle-row.sel,.imgstyle-row:hover{background:#34306b}
    .imgstyle-name{font:600 12px ui-monospace,Consolas,monospace;color:#ff9ee6;white-space:nowrap}
    .imgstyle-cat{color:#8f8bc4;font-size:10px;white-space:nowrap}
    .imgstyle-phrase{color:#bdb9dc;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
    .imgstyle-prev{padding:7px 9px;white-space:pre-wrap;word-break:break-word}
    .imgstyle-prev b{color:#9ad8c8}
    .imgstyle-prev .dim{color:#8f8bc4}`;
  document.head.appendChild(css);
  panel = document.createElement("div");
  panel.className = "imgstyle-panel";
  sugEl = document.createElement("div");
  sugEl.className = "imgstyle-sug";
  prevEl = document.createElement("div");
  prevEl.className = "imgstyle-prev";
  panel.append(sugEl, prevEl);
  // keep the textarea focused while clicking suggestions
  panel.addEventListener("mousedown", (e) => e.preventDefault());
  document.body.appendChild(panel);
}

function ownerNode(el) {
  if (!el || el.tagName !== "TEXTAREA") return null;
  const graph = app.graph;
  if (!graph) return null;
  const holder = el.closest("[data-node-id]");           // newer card-style nodes
  if (holder) {
    const n = graph.getNodeById(Number(holder.dataset.nodeId));
    if (n && OUR_NODES.has(n.type)) return n;
  }
  for (const n of graph._nodes || []) {                   // classic nodes
    if (!OUR_NODES.has(n.type)) continue;
    for (const w of n.widgets || []) {
      if (w.inputEl === el) return n;
    }
  }
  return null;
}

function isRequestBox(node, el) {
  // only the "request" box gets help (not extra_negative)
  const holder = el.closest("[data-node-id]");
  if (holder) {
    const all = holder.querySelectorAll("textarea");   // request is the first textarea, extra_negative the second
    return all.length > 0 && all[0] === el;
  }
  const w = (node.widgets || []).find((x) => x.name === "request");
  return !!w && w.inputEl === el;
}

function widgetValue(node, name) {
  const w = (node.widgets || []).find((x) => x.name === name);
  return w ? w.value : undefined;
}

function place() {
  if (!panel || panel.style.display === "none" || !active) return;
  const r = active.el.getBoundingClientRect();
  const width = Math.min(Math.max(r.width, 340), window.innerWidth - 16);
  panel.style.width = width + "px";
  panel.style.left = Math.max(8, Math.min(r.left, window.innerWidth - width - 8)) + "px";
  const below = r.bottom + 4;
  const room = window.innerHeight - below;
  if (room < 160 && r.top > room) {                       // flip above when there is no room
    panel.style.top = "";
    panel.style.bottom = (window.innerHeight - r.top + 4) + "px";
  } else {
    panel.style.bottom = "";
    panel.style.top = below + "px";
  }
}

function loop() {
  place();
  if (panel && panel.style.display !== "none") requestAnimationFrame(loop);
}

function show() {
  ensurePanel();
  clearTimeout(hideTimer);
  if (panel.style.display === "none" || !panel.style.display) {
    panel.style.display = "block";
    requestAnimationFrame(loop);
  }
  place();
}

function hide() {
  if (panel) panel.style.display = "none";
  active = null;
  items = [];
}

function currentToken(el) {
  const pos = el.selectionStart ?? el.value.length;
  const before = el.value.slice(0, pos);
  const m = before.match(/(^|\s)\/([^\s/]*)$/);
  return m ? { start: pos - m[2].length - 1, end: pos, prefix: m[2].toLowerCase() } : null;
}

function renderSuggestions(tok) {
  sugEl.textContent = "";
  items = [];
  if (!tok || !commands) return;
  const p = tok.prefix.replace(/[\s_-]+/g, "");
  const starts = [], inside = [];
  for (const c of commands) {
    const n = c.n.toLowerCase();
    if (p === "" || n.startsWith(p)) starts.push(c);
    else if (n.includes(p)) inside.push(c);
  }
  items = starts.concat(inside).slice(0, MAX_SUGGESTIONS);
  selected = 0;
  items.forEach((c, i) => {
    const row = document.createElement("div");
    row.className = "imgstyle-row" + (i === selected ? " sel" : "");
    const name = document.createElement("span");
    name.className = "imgstyle-name";
    name.textContent = "/" + c.n;
    const cat = document.createElement("span");
    cat.className = "imgstyle-cat";
    cat.textContent = c.c;
    const phrase = document.createElement("span");
    phrase.className = "imgstyle-phrase";
    phrase.textContent = c.p;
    row.append(name, cat, phrase);
    row.addEventListener("click", () => insert(i));
    sugEl.appendChild(row);
  });
  sugEl.style.display = items.length ? "block" : "none";
}

function highlight() {
  [...sugEl.children].forEach((r, i) => r.classList.toggle("sel", i === selected));
  const r = sugEl.children[selected];
  if (r && r.scrollIntoView) r.scrollIntoView({ block: "nearest" });
}

function insert(i) {
  if (!active || !items[i]) return;
  const el = active.el;
  const tok = currentToken(el);
  if (!tok) return;
  const text = "/" + items[i].n + " ";
  el.value = el.value.slice(0, tok.start) + text + el.value.slice(tok.end);
  const caret = tok.start + text.length;
  el.setSelectionRange(caret, caret);
  el.dispatchEvent(new Event("input", { bubbles: true }));  // lets ComfyUI store the new value
}

function schedulePreview() {
  clearTimeout(timer);
  timer = setTimeout(runPreview, 250);
}

async function runPreview() {
  if (!active) return;
  const { el, node } = active;
  const body = { request: el.value };
  for (const k of SETTINGS) {
    const v = widgetValue(node, k);
    if (v !== undefined) body[k] = v;
  }
  const seq = ++reqSeq;
  let data = null;
  try {
    const r = await api.fetchApi("/imagestyle/expand", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
    });
    data = r.ok ? await r.json() : null;
  } catch (e) {
    data = null;
  }
  if (seq !== reqSeq || !active) return;                  // a newer request already replaced this one
  prevEl.textContent = "";
  if (!data) {
    prevEl.textContent = "Preview unavailable (restart ComfyUI so the node's helper routes load).";
    return;
  }
  const add = (label, text) => {
    const b = document.createElement("b");
    b.textContent = label + " ";
    const t = document.createTextNode(text + "\n");
    prevEl.append(b, t);
  };
  add("positive:", data.positive);
  add("negative:", data.negative || "(none)");
  add("size:", data.width + " x " + data.height);
  const rep = document.createElement("div");
  rep.className = "dim";
  rep.style.marginTop = "5px";
  rep.textContent = data.report;
  prevEl.appendChild(rep);
  place();
}

async function onFocusIn(e) {
  const node = ownerNode(e.target);
  if (!node || !isRequestBox(node, e.target)) return;
  await loadCommands();
  active = { el: e.target, node };
  show();
  renderSuggestions(currentToken(e.target));
  sugEl.style.display = items.length ? "block" : "none";
  schedulePreview();
}

function onInput(e) {
  if (!active || e.target !== active.el) return;
  renderSuggestions(currentToken(active.el));
  place();
  schedulePreview();
}

function onKeyDown(e) {
  if (!active || e.target !== active.el || !items.length) return;
  if (e.key === "ArrowDown") { selected = (selected + 1) % items.length; highlight(); e.preventDefault(); e.stopPropagation(); }
  else if (e.key === "ArrowUp") { selected = (selected - 1 + items.length) % items.length; highlight(); e.preventDefault(); e.stopPropagation(); }
  else if (e.key === "Tab" || e.key === "Enter") { insert(selected); e.preventDefault(); e.stopPropagation(); }
  else if (e.key === "Escape") { renderSuggestions(null); sugEl.style.display = "none"; e.stopPropagation(); }
}

function onFocusOut(e) {
  if (!active || e.target !== active.el) return;
  hideTimer = setTimeout(hide, 150);
}

app.registerExtension({
  name: "ImageStyle.CommandHelper",
  setup() {
    document.addEventListener("focusin", onFocusIn, true);
    document.addEventListener("focusout", onFocusOut, true);
    document.addEventListener("input", onInput, true);
    document.addEventListener("keydown", onKeyDown, true);
    // settings changes (style, megapixels...) also refresh the preview
    document.addEventListener("change", () => active && schedulePreview(), true);
    document.addEventListener("click", () => active && schedulePreview(), true);
  },
});
