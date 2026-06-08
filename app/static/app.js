const $ = (sel) => document.querySelector(sel);

async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok && res.status !== 204) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail; } catch (_) {}
    throw new Error(detail);
  }
  return res.status === 204 ? null : res.json();
}

let toastTimer;
function toast(msg) {
  const el = $("#toast");
  el.textContent = msg;
  el.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (el.hidden = true), 2600);
}

function fmtDate(iso) {
  // iso = "YYYY-MM-DD"
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d).toLocaleDateString(undefined, {
    weekday: "short", month: "short", day: "numeric",
  });
}

// --- Config / schedule note ----------------------------------------------
async function loadConfig() {
  try {
    const cfg = await api("/api/config");
    const hh = String(cfg.pick_hour).padStart(2, "0");
    const mm = String(cfg.pick_minute).padStart(2, "0");
    $("#schedule-note").textContent =
      `// a fresh dinner is served daily @ ${hh}:${mm} - ${cfg.timezone}`;
  } catch (_) {}
}

// --- Today ---------------------------------------------------------------
async function loadToday(animate = false) {
  const { selection } = await api("/api/today");
  const pickEl = $("#today-pick");
  const metaEl = $("#today-meta");
  if (selection) {
    pickEl.textContent = selection.name;
    const t = new Date(selection.chosen_at + "Z").toLocaleTimeString(undefined, {
      hour: "numeric", minute: "2-digit",
    });
    metaEl.textContent = selection.manual
      ? `chosen manually at ${t}`
      : `auto-picked at ${t}`;
  } else {
    pickEl.textContent = "not picked yet";
    metaEl.textContent = "roll now, or wait for the daily pick.";
  }
  if (animate) {
    pickEl.classList.remove("spin");
    void pickEl.offsetWidth; // restart animation
    pickEl.classList.add("spin");
  }
}

// --- Dinners -------------------------------------------------------------
async function loadDinners() {
  const dinners = await api("/api/dinners");
  const list = $("#dinner-list");
  list.innerHTML = "";
  $("#dinner-empty").hidden = dinners.length > 0;

  for (const d of dinners) {
    const li = document.createElement("li");
    li.className = "dinner-item" + (d.active ? "" : " inactive");

    const chk = document.createElement("span");
    chk.className = "chk" + (d.active ? " on" : "");
    chk.textContent = d.active ? "[x]" : "[ ]";
    chk.title = d.active ? "active — click to pause" : "paused — click to enable";
    chk.onclick = async () => {
      await api(`/api/dinners/${d.id}`, {
        method: "PATCH",
        body: JSON.stringify({ active: !d.active }),
      });
      loadDinners();
    };

    const name = document.createElement("span");
    name.className = "name";
    name.textContent = d.name;
    name.title = "click to rename";
    name.onclick = () => startRename(name, d);

    const del = document.createElement("button");
    del.className = "del";
    del.textContent = "[del]";
    del.title = "delete";
    del.onclick = async () => {
      if (!confirm(`Delete "${d.name}"?`)) return;
      await api(`/api/dinners/${d.id}`, { method: "DELETE" });
      loadDinners();
    };

    li.append(chk, name, del);
    list.appendChild(li);
  }
}

function startRename(nameEl, dinner) {
  nameEl.contentEditable = "true";
  nameEl.focus();
  document.getSelection().selectAllChildren(nameEl);

  const finish = async (save) => {
    nameEl.contentEditable = "false";
    nameEl.onblur = null;
    nameEl.onkeydown = null;
    const newName = nameEl.textContent.trim();
    if (save && newName && newName !== dinner.name) {
      try {
        await api(`/api/dinners/${dinner.id}`, {
          method: "PATCH",
          body: JSON.stringify({ name: newName }),
        });
        toast("Renamed");
      } catch (e) { toast(e.message); }
    }
    loadDinners();
  };

  nameEl.onblur = () => finish(true);
  nameEl.onkeydown = (e) => {
    if (e.key === "Enter") { e.preventDefault(); finish(true); }
    if (e.key === "Escape") { finish(false); }
  };
}

// --- History -------------------------------------------------------------
async function loadHistory() {
  const items = await api("/api/history?limit=30");
  const list = $("#history-list");
  list.innerHTML = "";
  $("#history-empty").hidden = items.length > 0;

  for (const h of items) {
    const li = document.createElement("li");
    li.className = "history-item";

    const date = document.createElement("span");
    date.className = "date";
    date.textContent = fmtDate(h.pick_date);

    const name = document.createElement("span");
    name.className = "name";
    name.textContent = h.name;

    li.append(date, name);
    if (h.manual) {
      const tag = document.createElement("span");
      tag.className = "tag";
      tag.textContent = "[manual]";
      li.append(tag);
    }
    list.appendChild(li);
  }
}

// --- Events --------------------------------------------------------------
$("#add-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = $("#add-input");
  const name = input.value.trim();
  if (!name) return;
  try {
    await api("/api/dinners", { method: "POST", body: JSON.stringify({ name }) });
    input.value = "";
    loadDinners();
  } catch (e) { toast(e.message); }
});

$("#roll-btn").addEventListener("click", async () => {
  try {
    await api("/api/roll", { method: "POST" });
    await loadToday(true);
    loadHistory();
  } catch (e) { toast(e.message); }
});

// --- Init ----------------------------------------------------------------
loadConfig();
loadToday();
loadDinners();
loadHistory();
