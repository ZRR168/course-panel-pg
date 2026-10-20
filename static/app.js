// 课程安排面板前端：渲染、认领/释放、Supabase Realtime 实时同步
const SUPABASE_URL = window.SUPABASE_URL;
const SUPABASE_ANON_KEY = window.SUPABASE_ANON_KEY;
const ME = window.CURRENT_USER || { id: 0, role: "ta" };
let sessions = [];
let pending = null;

async function loadSessions() {
  try {
    const r = await fetch("/api/sessions");
    sessions = await r.json();
    renderBoard();
  } catch (e) { console.error(e); }
}
async function loadActivity() {
  try {
    const r = await fetch("/api/activity");
    renderFeed(await r.json());
  } catch (e) { console.error(e); }
}

function renderBoard() {
  const board = document.getElementById("board");
  const weeks = {};
  sessions.forEach(s => { (weeks[s.week] = weeks[s.week] || []).push(s); });
  let html = "";
  Object.keys(weeks).sort((a, b) => a - b).forEach(w => {
    const list = weeks[w];
    const mod = list[0].module_name;
    html += `<div class="week"><h4>第${w}周 <span class="wm">${mod}</span></h4>`;
    list.forEach(s => {
      const claimed = s.status === "claimed";
      const locked = s.status === "locked";
      const mine = s.claimed_by === ME.id;
      const cls = locked ? "locked" : (claimed ? "claimed" : "");
      let act = "";
      if (locked) act = `<span class="muted">已锁定（管理员改派）</span>`;
      else if (!claimed) act = `<button class="btn sm primary" onclick="askClaim(${s.id})">认领</button>`;
      else if (mine) act = `<button class="btn sm" onclick="askRelease(${s.id})">释放</button>`;
      else if (ME.role === "admin") act = `<button class="btn sm" onclick="askRelease(${s.id})">改派/释放</button>`;
      else act = `<span class="muted">已被认领</span>`;
      const who = claimed ? `👤 ${s.claimer_name}` : "";
      html += `<div class="scard ${cls}">
        <div class="top"><span class="slot">${s.slot}</span><span class="meta">${s.class_time}</span></div>
        <div class="topic">${s.topic}</div>
        <div class="who">${who}</div>
        <div class="acts">${act}</div>
      </div>`;
    });
    html += `</div>`;
  });
  board.innerHTML = html;
}

function askClaim(id) {
  const s = sessions.find(x => x.id === id); if (!s) return;
  pending = { id, action: "claim" };
  document.getElementById("claimTitle").textContent = "认领席位";
  document.getElementById("claimInfo").textContent = `第${s.week}周 ${s.slot}《${s.topic}》`;
  document.getElementById("claimModal").style.display = "flex";
}
function askRelease(id) {
  const s = sessions.find(x => x.id === id); if (!s) return;
  pending = { id, action: "release" };
  document.getElementById("claimTitle").textContent = "释放席位";
  document.getElementById("claimInfo").textContent = `第${s.week}周 ${s.slot}《${s.topic}》`;
  document.getElementById("claimModal").style.display = "flex";
}
function closeClaim() { document.getElementById("claimModal").style.display = "none"; pending = null; }
document.getElementById("claimOk").onclick = async () => {
  if (!pending) return;
  const r = await fetch("/api/claim", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: pending.id, action: pending.action }),
  });
  const j = await r.json();
  closeClaim();
  if (!j.ok) { alert(j.msg); return; }
  toast(j.msg || "操作成功");
  await loadSessions(); await loadActivity();
};

function renderFeed(items) {
  const ul = document.getElementById("feedList"); if (!ul) return;
  ul.innerHTML = items.length
    ? items.map(a => `<li><span class="time">${a.created_at}</span><b>${a.user}</b> ${a.message}</li>`).join("")
    : '<li class="muted">暂无动态</li>';
}

function toast(msg) {
  const t = document.createElement("div"); t.className = "toast"; t.textContent = msg;
  document.body.appendChild(t);
  requestAnimationFrame(() => t.classList.add("show"));
  setTimeout(() => { t.classList.remove("show"); setTimeout(() => t.remove(), 300); }, 2500);
}

// ---- 实时同步：Supabase Realtime 订阅 sessions / activity_log ----
if (SUPABASE_URL && SUPABASE_ANON_KEY) {
  try {
    const sb = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
    sb.channel("course-sync")
      .on("postgres_changes", { event: "*", schema: "public", table: "sessions" }, () => { loadSessions(); loadActivity(); })
      .on("postgres_changes", { event: "*", schema: "public", table: "activity_log" }, () => { loadActivity(); })
      .subscribe(status => {
        const l = document.getElementById("live");
        if (!l) return;
        if (status === "SUBSCRIBED") { l.textContent = "● 实时同步已连接"; l.style.color = "var(--ok)"; }
        else { l.textContent = "○ 同步未连接（已降级为定时刷新）"; l.style.color = "var(--warn)"; }
      });
  } catch (e) { console.error("realtime init failed", e); }
}
// 兜底：每 20 秒刷新一次（即使 Realtime 不可用也能看到同步）
setInterval(() => { loadSessions(); loadActivity(); }, 20000);

loadSessions();
loadActivity();
