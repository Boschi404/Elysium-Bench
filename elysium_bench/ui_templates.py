"""HTML templates for Elysium-Bench UI — dark theme, GitHub-inspired palette."""
# ═══════════════════════════════════════════════════════════════════════════
# SHARED STYLES — GitHub Dark Palette
# ═══════════════════════════════════════════════════════════════════════════

STYLES = """
<style>
  :root {
    --bg: #0d1117; --bg-elevated: #161b22; --card: #161b22;
    --border: #30363d; --border-hover: #38bdf8;
    --text: #e6edf3; --text-secondary: #c9d1d9; --muted: #8b949e; --dim: #484f58;
    --azure: #38bdf8; --azure-dim: rgba(56,189,248,0.15);
    --blue: #3b82f6; --blue-dim: rgba(59,130,246,0.15);
    --green: #3fb950; --green-dim: rgba(63,185,80,0.15);
    --red: #f85149; --red-dim: rgba(248,81,73,0.15);
    --amber: #d29922; --amber-dim: rgba(210,153,34,0.15);
    --purple: #a371f7; --purple-dim: rgba(163,113,247,0.15);
    --radius: 8px; --radius-lg: 12px;
  }

  * { margin:0; padding:0; box-sizing:border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
    background: var(--bg); color: var(--text); min-height: 100vh;
    line-height: 1.5; -webkit-font-smoothing: antialiased;
  }

  /* ── Navigation ──────────────────────────────────────────────────── */
  nav {
    background: var(--bg-elevated); border-bottom: 1px solid var(--border);
    padding: 0 2rem; display:flex; align-items:center; gap:1.5rem;
    height: 56px; position:sticky; top:0; z-index:100;
    backdrop-filter: blur(12px);
  }
  nav a { color: var(--muted); text-decoration:none; font-size:.875rem; font-weight:500; transition:color .15s; }
  nav a:hover, nav a.active { color: var(--azure); }
  nav .brand { font-weight:700; font-size:1.05rem; color: var(--azure); margin-right:auto; display:flex; align-items:center; gap:.4rem; }
  nav .brand .dot { width:8px; height:8px; border-radius:50%; background:var(--azure); box-shadow:0 0 6px var(--azure); }

  /* ── Layout ──────────────────────────────────────────────────────── */
  main { max-width: 1320px; margin: 2rem auto; padding: 0 1.5rem; }

  .card {
    background: var(--card); border:1px solid var(--border);
    border-radius:var(--radius-lg); padding:1.5rem; margin-bottom:1.25rem;
    transition: border-color .2s;
  }
  .card:hover { border-color: var(--border-hover); }
  .card h2 { font-size:1.05rem; color: var(--azure); margin-bottom:.75rem; font-weight:600; display:flex; align-items:center; gap:.5rem; }
  .card h3 { font-size:.9rem; color: var(--text-secondary); margin-bottom:.5rem; font-weight:600; }

  .grid { display:grid; gap:1.25rem; }
  .grid-2 { grid-template-columns: repeat(2, 1fr); }
  .grid-3 { grid-template-columns: repeat(3, 1fr); }
  .grid-4 { grid-template-columns: repeat(4, 1fr); }
  .grid-5 { grid-template-columns: repeat(5, 1fr); }

  /* ── Stats ────────────────────────────────────────────────────────── */
  .stat { text-align:center; padding:.75rem; }
  .stat .value { font-size:1.75rem; font-weight:700; line-height:1.2; }
  .stat .label { font-size:.75rem; color: var(--muted); margin-top:.2rem; text-transform:uppercase; letter-spacing:.05em; }
  .stat.green .value { color: var(--green); }
  .stat.red .value { color: var(--red); }
  .stat.azure .value { color: var(--azure); }
  .stat.amber .value { color: var(--amber); }

  /* ── Tables ───────────────────────────────────────────────────────── */
  table { width:100%; border-collapse:collapse; }
  th {
    text-align:left; padding:.6rem .75rem; color: var(--muted); font-size:.75rem;
    text-transform:uppercase; letter-spacing:.05em; border-bottom:1px solid var(--border);
    background: rgba(48,54,61,0.3); position:sticky; top:0;
  }
  td { padding:.55rem .75rem; border-bottom:1px solid rgba(48,54,61,0.5); font-size:.875rem; }
  tbody tr:hover td { background: rgba(56,189,248,0.04); }

  /* ── Badges ───────────────────────────────────────────────────────── */
  .badge { display:inline-block; padding:.15rem .55rem; border-radius:999px; font-size:.7rem; font-weight:600; letter-spacing:.03em; }
  .badge-yes { background:var(--green-dim); color:var(--green); border:1px solid rgba(63,185,80,0.3); }
  .badge-no { background:var(--amber-dim); color:var(--amber); border:1px solid rgba(210,153,34,0.3); }
  .badge-azure { background:var(--azure-dim); color:var(--azure); border:1px solid rgba(56,189,248,0.3); }
  .badge-running { background:var(--blue-dim); color:var(--blue); border:1px solid rgba(59,130,246,0.3); }
  .badge-done { background:var(--green-dim); color:var(--green); border:1px solid rgba(63,185,80,0.3); }
  .badge-pending { background:rgba(139,148,158,0.1); color:var(--dim); border:1px solid rgba(139,148,158,0.15); }

  /* ── Buttons ──────────────────────────────────────────────────────── */
  .btn { display:inline-block; padding:.55rem 1.2rem; border-radius:var(--radius); font-weight:600; font-size:.85rem; cursor:pointer; border:none; transition:all .15s; text-decoration:none; }
  .btn-azure { background: var(--azure); color:#0d1117; }
  .btn-azure:hover { background: #7dd3fc; transform:translateY(-1px); box-shadow:0 2px 8px rgba(56,189,248,0.3); }
  .btn-outline { background:transparent; border:1px solid var(--border); color:var(--muted); }
  .btn-outline:hover { border-color:var(--azure); color:var(--azure); }
  .btn-sm { padding:.25rem .6rem; font-size:.72rem; border-radius:6px; }

  /* ── Forms ────────────────────────────────────────────────────────── */
  select, input {
    background:var(--bg); border:1px solid var(--border); color:var(--text);
    padding:.5rem .75rem; border-radius:var(--radius); font-size:.875rem;
    transition:border-color .15s;
  }
  select:focus, input:focus { outline:none; border-color:var(--azure); box-shadow:0 0 0 3px rgba(56,189,248,0.12); }

  /* ── Progress ─────────────────────────────────────────────────────── */
  .progress-bar { background:var(--border); border-radius:999px; height:5px; overflow:hidden; margin:.4rem 0; }
  .progress-bar .fill {
    background:linear-gradient(90deg, var(--azure), var(--blue));
    height:100%; border-radius:999px; transition:width .4s ease;
  }
  .progress-bar .fill.green-fill { background:linear-gradient(90deg, var(--azure), var(--green)); }

  /* ── Category Cards Grid ──────────────────────────────────────────── */
  .cat-grid { display:grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap:.75rem; }
  .cat-card {
    background: var(--bg-elevated); border:1px solid var(--border);
    border-radius:var(--radius-lg); padding:1rem;
    transition: all .2s; position:relative; overflow:hidden;
  }
  .cat-card:hover { border-color: var(--azure); }
  .cat-card.active { border-color: var(--azure); box-shadow: 0 0 12px rgba(56,189,248,0.1); }
  .cat-card.done { border-color: var(--green); opacity: 0.85; }
  .cat-card .cat-name { font-size:.85rem; font-weight:600; color:var(--text); margin-bottom:.4rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .cat-card .cat-score { font-size:1.6rem; font-weight:700; color:var(--azure); }
  .cat-card .cat-status { font-size:.7rem; text-transform:uppercase; letter-spacing:.05em; margin-top:.3rem; }
  .cat-card .cat-progress { margin-top:.5rem; }
  .cat-card .cat-sub { font-size:.7rem; color:var(--muted); margin-top:.25rem; }
  .cat-card .pulse-dot {
    position:absolute; top:.6rem; right:.6rem; width:8px; height:8px;
    border-radius:50%; background:var(--azure); animation:pulse 1.5s infinite;
  }
  .cat-card.done .pulse-dot { background:var(--green); animation:none; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }

  /* ── Phase Timeline ───────────────────────────────────────────────── */
  .phase-steps { display:flex; gap:.25rem; flex-wrap:wrap; margin-bottom:1rem; }
  .phase-step {
    padding:.35rem .7rem; border-radius:var(--radius); font-size:.75rem;
    font-weight:600; background: var(--bg); border:1px solid var(--border);
    color: var(--dim); transition:all .2s;
  }
  .phase-step.current { border-color:var(--azure); color:var(--azure); background:var(--azure-dim); }
  .phase-step.done { border-color:var(--green); color:var(--green); background:var(--green-dim); }
  .phase-step.failed { border-color:var(--red); color:var(--red); background:var(--red-dim); }

  /* ── Log Lines ────────────────────────────────────────────────────── */
  .log-container { max-height:400px; overflow-y:auto; font-family:'JetBrains Mono','Fira Code','Cascadia Code',monospace; font-size:.8rem; }
  .log-line { padding:.25rem .5rem; color:var(--muted); border-bottom:1px solid rgba(255,255,255,0.015); display:flex; gap:.5rem; align-items:baseline; }
  .log-line .ts { color:var(--dim); font-size:.7rem; min-width:70px; }
  .log-line .phase-tag { color:var(--azure); font-weight:600; min-width:80px; }
  .log-line .score-good { color:var(--green); font-weight:600; }
  .log-line .cat-tag { color:var(--blue); }

  /* ── Charts ───────────────────────────────────────────────────────── */
  canvas { width:100% !important; }

  /* ── System Status ────────────────────────────────────────────────── */
  .sys-row { display:flex; gap:.75rem; align-items:center; flex-wrap:wrap; }
  .sys-metric { display:flex; align-items:center; gap:.4rem; font-size:.8rem; color:var(--muted); }
  .sys-metric .dot { width:6px; height:6px; border-radius:50%; }
  .sys-metric .dot.on { background:var(--green); box-shadow:0 0 4px var(--green); }
  .sys-metric .dot.off { background:var(--dim); }

  /* ── Section Header ───────────────────────────────────────────────── */
  .section-header {
    display:flex; align-items:center; justify-content:space-between;
    margin-bottom:1rem; padding-bottom:.75rem; border-bottom:1px solid var(--border);
  }
  .section-header h2 { margin-bottom:0 !important; }

  /* ── Toast ────────────────────────────────────────────────────────── */
  .toast {
    position:fixed; bottom:1.5rem; right:1.5rem; z-index:999;
    background:var(--bg-elevated); border:1px solid var(--green);
    border-radius:var(--radius-lg); padding:.75rem 1.25rem;
    color:var(--green); font-size:.85rem; font-weight:600;
    opacity:0; transform:translateY(10px); transition:all .3s;
    box-shadow:0 4px 16px rgba(0,0,0,0.4);
  }
  .toast.show { opacity:1; transform:translateY(0); }

  /* ── Responsive ───────────────────────────────────────────────────── */
  @media (max-width: 900px) {
    .grid-3, .grid-4 { grid-template-columns: repeat(2, 1fr); }
    .cat-grid { grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); }
  }
  @media (max-width: 600px) {
    .grid-2, .grid-3, .grid-4, .grid-5 { grid-template-columns: 1fr; }
    nav { padding:0 1rem; gap:.75rem; }
    main { padding:0 .75rem; }
    .phase-steps { flex-direction:column; }
  }
</style>
"""

# ═══════════════════════════════════════════════════════════════════════════
# PAGE SHELL (nav + main container)
# ═══════════════════════════════════════════════════════════════════════════

PAGE_SHELL = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  {styles}
</head>
<body>
  <nav>
    <a href="/" class="brand"><span class="dot"></span>Elysium-Bench</a>
    <a href="/">Dashboard</a>
    <a href="/run">Run</a>
    <a href="/compare">Compare</a>
    <span id="navStatus" style="margin-left:auto;font-size:.75rem;color:var(--dim);display:flex;align-items:center;gap:.35rem">
      <span class="dot off" style="width:6px;height:6px;border-radius:50%;display:inline-block"></span>
      <span id="navStatusText">idle</span>
    </span>
  </nav>
  <main>
    {content}
  </main>
  <div class="toast" id="toast"></div>
</body>
</html>"""


# ═══════════════════════════════════════════════════════════════════════════
# DASHBOARD PAGE — Run History + System Status
# ═══════════════════════════════════════════════════════════════════════════

DASHBOARD_PAGE = """
<!-- ── System Status Panel ────────────────────────────────────────────── -->
<div class="card" id="sysStatusCard">
  <div class="section-header">
    <h2>🖥️ System Status</h2>
    <span style="font-size:.75rem;color:var(--dim)" id="sysRefreshed">loading...</span>
  </div>
  <div class="grid grid-3" style="margin-bottom:.75rem">
    <div style="border:1px solid var(--border);border-radius:var(--radius);padding:.75rem">
      <div style="font-size:.7rem;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;margin-bottom:.4rem">Hermes Agent</div>
      <div class="sys-row"><span class="sys-metric"><span class="dot" id="hermesDot"></span><span id="hermesStatus">—</span></span></div>
      <div style="font-size:.75rem;color:var(--muted);margin-top:.25rem" id="hermesProvider">Provider: —</div>
      <div style="font-size:.75rem;color:var(--muted)" id="hermesModel">Model: —</div>
    </div>
    <div style="border:1px solid var(--border);border-radius:var(--radius);padding:.75rem">
      <div style="font-size:.7rem;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;margin-bottom:.4rem">System Resources</div>
      <div class="sys-row">
        <span class="sys-metric">CPU <strong id="sysCpu">—</strong>%</span>
        <span class="sys-metric">RAM <strong id="sysRam">—</strong>%</span>
        <span class="sys-metric">Disk <strong id="sysDisk">—</strong>%</span>
      </div>
    </div>
    <div style="border:1px solid var(--border);border-radius:var(--radius);padding:.75rem">
      <div style="font-size:.7rem;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;margin-bottom:.4rem">Elysium-Bench</div>
      <div class="sys-row">
        <span class="sys-metric">Runs: <strong id="sysRunCount">—</strong></span>
        <span class="sys-metric">Active: <strong id="sysActiveRun">—</strong></span>
      </div>
      <div style="font-size:.75rem;color:var(--muted);margin-top:.25rem" id="sysVersion">Version: —</div>
    </div>
  </div>
</div>

<!-- ── Run History Chart ──────────────────────────────────────────────── -->
<div class="card">
  <h2>📊 Run History</h2>
  <div style="height:320px;"><canvas id="historyChart"></canvas></div>
</div>

<!-- ── Recent Runs Table ──────────────────────────────────────────────── -->
<div class="card">
  <h2>📋 Recent Runs</h2>
  <table>
    <thead><tr>
      <th>Date</th><th>Baseline</th><th>Loop 1</th><th>Re-Test</th><th>&Delta;</th><th>Learning?</th><th>Duration</th><th></th>
    </tr></thead>
    <tbody id="runsTable"><tr><td colspan="8" style="text-align:center;color:var(--muted)">Loading...</td></tr></tbody>
  </table>
</div>

<div class="grid grid-3" id="statsGrid"></div>

<script>
// ── System Status ──────────────────────────────────────────────────────
async function refreshSystemStatus() {
  try {
    const resp = await fetch('/api/system-status');
    const s = await resp.json();

    document.getElementById('sysRefreshed').textContent = 'updated ' + new Date().toLocaleTimeString();

    // Hermes
    const hd = document.getElementById('hermesDot');
    if (s.hermes.available) {
      hd.className = 'dot on';
      document.getElementById('hermesStatus').textContent = 'connected';
      document.getElementById('hermesProvider').textContent = 'Provider: ' + s.hermes.provider;
      document.getElementById('hermesModel').textContent = 'Model: ' + s.hermes.model;
      document.getElementById('navStatusText').textContent = s.hermes.provider + ' / ' + s.hermes.model;
      document.querySelector('#navStatus .dot').className = 'dot on';
    } else {
      hd.className = 'dot off';
      document.getElementById('hermesStatus').textContent = 'not detected';
      document.getElementById('hermesProvider').textContent = 'Provider: —';
      document.getElementById('hermesModel').textContent = 'Model: —';
    }

    // System
    document.getElementById('sysCpu').textContent = s.system.cpu_percent;
    document.getElementById('sysRam').textContent = s.system.ram_percent;
    document.getElementById('sysDisk').textContent = s.system.disk_percent;

    // Bench
    document.getElementById('sysRunCount').textContent = s.bench.total_runs;
    document.getElementById('sysActiveRun').textContent = s.bench.active_run ? '1 running' : 'none';
    document.getElementById('sysVersion').textContent = 'Version: ' + s.bench.version;
  } catch(e) {
    document.getElementById('sysRefreshed').textContent = 'offline';
  }
}

// ── Dashboard ──────────────────────────────────────────────────────────
async function loadDashboard() {
  const resp = await fetch('/api/runs');
  const runs = await resp.json();

  // Chart
  const ctx = document.getElementById('historyChart').getContext('2d');
  const recent = runs.slice(0, 20).reverse();
  const labels = recent.map(r => r.timestamp ? r.timestamp.slice(0,16).replace('T',' ') : r.id.slice(0,15));

  new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        { label: 'Re-Test', data: recent.map(r => r.overall_score || 0), borderColor: '#38bdf8', backgroundColor: 'rgba(56,189,248,0.08)', fill: true, tension: 0.35, pointRadius: 3, pointBackgroundColor: '#38bdf8' },
        { label: 'Loop 1', data: recent.map(r => r.loop1_score || 0), borderColor: '#a371f7', borderDash: [5,3], tension: 0.3, pointRadius: 2 },
        { label: 'Baseline', data: recent.map(r => r.baseline_score || 0), borderColor: '#484f58', borderDash: [2,2], tension: 0.3, pointRadius: 1 },
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      interaction: { intersect: false, mode: 'index' },
      plugins: { legend: { labels: { color: '#8b949e', usePointStyle: true, padding: 20 } } },
      scales: {
        x: { ticks: { color: '#484f58', maxTicksLimit: 10 }, grid: { color: 'rgba(48,54,61,0.5)' } },
        y: { ticks: { color: '#484f58' }, grid: { color: 'rgba(48,54,61,0.5)' }, min: 0, max: 100 }
      }
    }
  });

  // Table
  const tbody = document.getElementById('runsTable');
  tbody.innerHTML = runs.slice(0, 15).map(r => `
    <tr>
      <td>${(r.timestamp || r.id).slice(0,16).replace('T',' ')}</td>
      <td>${(r.baseline_score||0).toFixed(1)}</td>
      <td>${(r.loop1_score||0).toFixed(1)}</td>
      <td style="color:var(--azure);font-weight:600">${(r.overall_score||0).toFixed(1)}</td>
      <td style="color:${(r.improvement||0)>=0?'var(--green)':'var(--red)'}">${(r.improvement||0) >= 0 ? '+' : ''}${(r.improvement||0).toFixed(1)}</td>
      <td><span class="badge badge-${r.learning_detected?'yes':'no'}">${r.learning_detected?'YES':'NO'}</span></td>
      <td>${(r.duration_seconds/60).toFixed(0)}m</td>
      <td><a href="/results/${r.id}" class="btn btn-outline btn-sm">View</a></td>
    </tr>
  `).join('') || '<tr><td colspan="8" style="text-align:center;color:var(--muted)">No runs yet — <a href="/run" style="color:var(--azure)">start one</a></td></tr>';

  // Stats
  const grid = document.getElementById('statsGrid');
  if (runs.length > 0) {
    const withLearning = runs.filter(r => r.learning_detected).length;
    const bestScore = Math.max(...runs.map(r => r.overall_score || 0));
    const avgImprovement = runs.filter(r => r.improvement).reduce((s,r) => s + r.improvement, 0) / runs.filter(r => r.improvement).length || 0;
    grid.innerHTML = `
      <div class="card stat azure"><div class="value">${runs.length}</div><div class="label">Total Runs</div></div>
      <div class="card stat green"><div class="value">${withLearning}</div><div class="label">With Learning</div></div>
      <div class="card stat"><div class="value" style="color:var(--purple)">${(avgImprovement).toFixed(1)}</div><div class="label">Avg &Delta; Improvement</div></div>
    `;
  }
}

refreshSystemStatus();
loadDashboard();
setInterval(refreshSystemStatus, 15000);
</script>
"""


# ═══════════════════════════════════════════════════════════════════════════
# RUN PAGE — Config + Category Cards + Named Phases + Live Log
# ═══════════════════════════════════════════════════════════════════════════

RUN_PAGE = """
<div class="grid grid-2">
  <!-- ── Config Panel ──────────────────────────────────────────────── -->
  <div class="card">
    <h2>⚙️ Configure Benchmark</h2>
    <form id="runForm" style="display:flex;flex-direction:column;gap:1rem;margin-top:.75rem;">
      <div>
        <label style="color:var(--muted);font-size:.8rem;display:block;margin-bottom:.3rem">Category <span style="color:var(--dim)">(empty = all 10)</span></label>
        <select id="category" style="width:100%">
          <option value="">All 10 categories (100 tasks)</option>
          <optgroup label="── Code Tasks ──">
            <option value="api_development">API Development</option>
            <option value="bug_fixing">Bug Fixing</option>
            <option value="algorithm_implementation">Algorithm Implementation</option>
          </optgroup>
          <optgroup label="── Non-Code Tasks ──">
            <option value="data_analysis">Data Analysis</option>
            <option value="mathematical_reasoning">Mathematical Reasoning</option>
            <option value="logical_deduction">Logical Deduction</option>
            <option value="security_analysis">Security Analysis</option>
            <option value="code_review">Code Review</option>
            <option value="documentation_generation">Documentation</option>
            <option value="configuration_management">DevOps</option>
          </optgroup>
        </select>
      </div>
      <div>
        <label style="color:var(--muted);font-size:.8rem;display:block;margin-bottom:.3rem">Practice Loops</label>
        <input type="number" id="loops" value="10" min="1" max="20" style="width:100%">
      </div>
      <button type="submit" class="btn btn-azure" style="width:100%;padding:.7rem" id="startBtn">▶ Start Benchmark</button>
    </form>
    <p style="color:var(--dim);font-size:.75rem;margin-top:.75rem;line-height:1.5">
      Runs through <strong style="color:var(--azure)">Hermes Agent</strong> with <code style="color:var(--blue)">elysium-swarmloop</code> skill.<br>
      Baseline → Measurement Loop → Practice Loops → Re-Test → Report.
    </p>
  </div>

  <!-- ── Phase Progress Panel ───────────────────────────────────────── -->
  <div class="card" id="progressCard" style="display:none">
    <div class="section-header">
      <h2 id="progressTitle">🔄 Idle</h2>
      <span style="font-size:.75rem;color:var(--muted)" id="progressTimer">00:00</span>
    </div>
    <div class="phase-steps" id="phaseSteps"></div>
    <div class="progress-bar"><div class="fill" id="progressFill" style="width:0%"></div></div>
    <p style="color:var(--muted);font-size:.8rem;margin-top:.35rem" id="progressMsg">Ready to start.</p>
  </div>
</div>

<!-- ── Category Cards Grid ──────────────────────────────────────────────── -->
<div class="card" id="catCardsContainer" style="display:none">
  <h2>📂 Category Progress</h2>
  <div class="cat-grid" id="catCards"></div>
</div>

<!-- ── Live Log ─────────────────────────────────────────────────────────── -->
<div class="card" id="logCard" style="display:none">
  <h2>📜 Live Log</h2>
  <div class="log-container" id="progressLog"></div>
</div>

<script>
let currentRunId = null;
let eventSource = null;
let timerInterval = null;
let startTime = null;

// ── Category names map ─────────────────────────────────────────────────
const CAT_NAMES = {
  api_development: 'API Dev',
  bug_fixing: 'Bug Fixing',
  algorithm_implementation: 'Algorithms',
  data_analysis: 'Data Analysis',
  mathematical_reasoning: 'Math',
  logical_deduction: 'Logic',
  security_analysis: 'Security',
  code_review: 'Code Review',
  documentation_generation: 'Docs',
  configuration_management: 'DevOps'
};

// ── Phase definitions ──────────────────────────────────────────────────
function buildPhaseSteps(loops) {
  const phases = [
    { id: 'baseline', label: 'Baseline', short: 'BASE' },
    { id: 'loop1', label: 'Loop 1 — Measure', short: 'L1' },
  ];
  for (let i = 2; i <= parseInt(loops); i++) {
    phases.push({ id: 'loop'+i, label: 'Loop '+i+' — Practice', short: 'L'+i });
  }
  phases.push({ id: 'retest', label: 'Re-Test', short: 'RETEST' });
  return phases;
}

let allPhases = [];

// ── Build category cards ──────────────────────────────────────────────
function initCategoryCards() {
  const container = document.getElementById('catCards');
  container.innerHTML = '';
  for (const [id, name] of Object.entries(CAT_NAMES)) {
    container.innerHTML += `
      <div class="cat-card" id="cat-${id}">
        <div class="pulse-dot" style="display:none"></div>
        <div class="cat-name">${name}</div>
        <div class="cat-score">—</div>
        <div class="cat-progress">
          <div class="progress-bar"><div class="fill" style="width:0%"></div></div>
        </div>
        <div class="cat-sub">task: —</div>
        <div class="cat-status badge badge-pending">pending</div>
      </div>
    `;
  }
  document.getElementById('catCardsContainer').style.display = '';
}

// ── Update category card ──────────────────────────────────────────────
function updateCategoryCard(catId, data) {
  const card = document.getElementById('cat-'+catId);
  if (!card) return;
  if (data.score !== undefined) {
    const scoreEl = card.querySelector('.cat-score');
    scoreEl.textContent = data.score.toFixed(1);
    scoreEl.style.color = data.score >= 60 ? 'var(--green)' : data.score >= 30 ? 'var(--amber)' : 'var(--red)';
  }
  if (data.status) {
    const statusEl = card.querySelector('.cat-status');
    card.className = 'cat-card';
    if (data.status === 'running') {
      card.classList.add('active');
      statusEl.className = 'cat-status badge badge-running';
      statusEl.textContent = 'running';
      card.querySelector('.pulse-dot').style.display = '';
    } else if (data.status === 'done') {
      card.classList.add('done');
      statusEl.className = 'cat-status badge badge-done';
      statusEl.textContent = 'done';
      card.querySelector('.pulse-dot').style.display = '';
    }
  }
  if (data.task) {
    card.querySelector('.cat-sub').textContent = 'task: ' + data.task;
  }
  if (data.progress !== undefined) {
    card.querySelector('.fill').style.width = data.progress + '%';
  }
}

// ── Update phase step ─────────────────────────────────────────────────
function updatePhaseStep(phaseId, status) {
  const steps = document.querySelectorAll('.phase-step');
  steps.forEach(s => {
    if (s.dataset.phase === phaseId) {
      s.className = 'phase-step ' + status;
    }
  });
}

// ── Timer ─────────────────────────────────────────────────────────────
function startTimer() {
  startTime = Date.now();
  if (timerInterval) clearInterval(timerInterval);
  timerInterval = setInterval(() => {
    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    const m = Math.floor(elapsed / 60).toString().padStart(2,'0');
    const s = (elapsed % 60).toString().padStart(2,'0');
    document.getElementById('progressTimer').textContent = m + ':' + s;
  }, 1000);
}

function stopTimer() {
  if (timerInterval) { clearInterval(timerInterval); timerInterval = null; }
}

// ── Toast notification ────────────────────────────────────────────────
function toast(msg, duration=3000) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'toast show';
  setTimeout(() => { t.className = 'toast'; }, duration);
}

// ── Form submit ──────────────────────────────────────────────────────
document.getElementById('runForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const category = document.getElementById('category').value;
  const loops = document.getElementById('loops').value;

  const resp = await fetch(`/api/runs/start?category=${encodeURIComponent(category)}&loops=${loops}`, { method:'POST' });
  const data = await resp.json();
  currentRunId = data.run_id;

  // Show panels
  document.getElementById('progressCard').style.display = '';
  document.getElementById('progressTitle').textContent = '🔄 Initializing...';
  document.getElementById('progressMsg').textContent = 'Starting benchmark...';
  document.getElementById('progressFill').style.width = '0%';
  document.getElementById('progressLog').innerHTML = '';
  document.getElementById('logCard').style.display = '';

  // Build phase steps
  allPhases = buildPhaseSteps(loops);
  const stepsEl = document.getElementById('phaseSteps');
  stepsEl.innerHTML = allPhases.map(p =>
    `<div class="phase-step" data-phase="${p.id}">${p.short}</div>`
  ).join('') + '<div class="phase-step" data-phase="report">REPORT</div>';
  updatePhaseStep('baseline', 'current');

  // Init category cards
  initCategoryCards();

  // Disable start button
  document.getElementById('startBtn').disabled = true;
  document.getElementById('startBtn').textContent = '⏳ Running...';
  document.getElementById('startBtn').style.opacity = '0.6';

  // Start timer
  startTimer();

  let phaseCount = 0;
  const totalPhases = parseInt(loops) + 2;

  // SSE stream
  eventSource = new EventSource(`/api/runs/${currentRunId}/stream`);
  eventSource.onmessage = (evt) => {
    const msg = JSON.parse(evt.data);
    const log = document.getElementById('progressLog');
    const fill = document.getElementById('progressFill');
    const now = new Date().toLocaleTimeString();

    if (msg.type === 'phase_start') {
      phaseCount++;
      fill.style.width = Math.min(95, (phaseCount / totalPhases * 100)) + '%';

      // Mark previous phase done, current phase as current
      updatePhaseStep(msg.phase, 'current');
      allPhases.forEach(p => {
        if (p.id !== msg.phase && document.querySelector(`.phase-step[data-phase="${p.id}"]`)?.classList.contains('current')) {
          updatePhaseStep(p.id, 'done');
        }
      });

      document.getElementById('progressTitle').textContent = '🔄 ' + msg.label;
      document.getElementById('progressMsg').textContent = `Phase ${phaseCount}/${totalPhases} · ${msg.phase.toUpperCase()}`;

      // Log
      log.innerHTML += `<div class="log-line"><span class="ts">${now}</span><span class="phase-tag">▶ ${msg.phase.toUpperCase()}</span><span>${msg.label}</span></div>`;
      log.scrollTop = log.scrollHeight;

      // Highlight active phase in nav
      document.getElementById('navStatusText').textContent = msg.phase.toUpperCase();

    } else if (msg.type === 'phase_end') {
      updatePhaseStep(msg.phase, 'done');
      log.innerHTML += `<div class="log-line"><span class="ts">${now}</span><span class="phase-tag">✔ ${msg.phase.toUpperCase()}</span><span>Score: <span class="score-good">${msg.score}/100</span></span></div>`;
      log.scrollTop = log.scrollHeight;

    } else if (msg.type === 'category_update') {
      // Per-category progress
      updateCategoryCard(msg.category, {
        score: msg.score,
        status: msg.status,
        task: msg.task,
        progress: msg.progress
      });

    } else if (msg.type === 'status') {
      document.getElementById('progressMsg').textContent = msg.message;

    } else if (msg.type === 'complete') {
      fill.style.width = '100%';
      fill.className = 'fill green-fill';
      updatePhaseStep('report', 'done');
      document.getElementById('progressTitle').textContent = '✅ Benchmark Complete!';
      document.getElementById('progressMsg').innerHTML = `All phases finished. <a href="/results/${currentRunId}" style="color:var(--azure)">View full results →</a>`;
      document.getElementById('navStatusText').textContent = 'idle';
      document.getElementById('startBtn').disabled = false;
      document.getElementById('startBtn').textContent = '▶ Start Benchmark';
      document.getElementById('startBtn').style.opacity = '1';
      stopTimer();
      eventSource.close();
      toast('✅ Benchmark complete!');

      // Mark all category cards as done
      for (const id of Object.keys(CAT_NAMES)) {
        updateCategoryCard(id, { status: 'done' });
      }

    } else if (msg.type === 'error') {
      document.getElementById('progressTitle').textContent = '❌ Error';
      document.getElementById('progressMsg').textContent = msg.message;
      document.getElementById('navStatusText').textContent = 'error';
      document.getElementById('startBtn').disabled = false;
      document.getElementById('startBtn').textContent = '▶ Start Benchmark';
      document.getElementById('startBtn').style.opacity = '1';
      stopTimer();
      eventSource.close();
      toast('❌ ' + msg.message, 5000);
    }
  };

  eventSource.onerror = () => {
    if (eventSource) eventSource.close();
  };
});
</script>
"""


# ═══════════════════════════════════════════════════════════════════════════
# RESULTS PAGE (single run detail)
# ═══════════════════════════════════════════════════════════════════════════

RESULTS_PAGE = """
<div class="card">
  <h2>📊 Results: {run_id}</h2>
  <div style="height:320px;"><canvas id="phasesChart"></canvas></div>
</div>

<div class="grid grid-2">
  <div class="card">
    <h2>📈 Score Progression</h2>
    <table id="phasesTable"><tr><td style="color:var(--muted)">Loading...</td></tr></table>
  </div>
  <div class="card">
    <h2>🎯 Improvement Metrics</h2>
    <table id="improvementTable"><tr><td style="color:var(--muted)">Loading...</td></tr></table>
  </div>
</div>

<div class="card">
  <h2>📋 Category Breakdown</h2>
  <table id="taskDetails"><tr><td style="color:var(--muted)">Loading...</td></tr></table>
</div>

<script>
async function loadResults() {{
  const resp = await fetch('/api/runs/{run_id}');
  const data = await resp.json();
  if (data.error) {{ document.body.innerHTML = '<main><div class="card"><h2 style="color:var(--red)">Run Not Found</h2><p style="color:var(--muted)">The run "{run_id}" was not found.</p><a href="/" class="btn btn-outline" style="margin-top:1rem">← Back to Dashboard</a></div></main>'; return; }}

  const phases = data.phases;
  const imp = data.improvement;

  // Chart — bar chart of all phases
  const labels = ['Baseline','Loop 1'];
  const scores = [phases.baseline.average, phases.loop1.average];
  (phases.practice || []).forEach(p => {{ labels.push('Loop '+p.loop); scores.push(p.average); }});
  labels.push('Re-Test'); scores.push(phases.retest.average);

  new Chart(document.getElementById('phasesChart'), {{
    type: 'bar',
    data: {{
      labels, datasets: [{{
        data: scores,
        backgroundColor: scores.map((s,i) => i===0 ? '#484f58' : i===scores.length-1 ? '#38bdf8' : '#a371f7'),
        borderRadius: 6, borderSkipped: false,
      }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ display: false }} }},
      scales: {{
        x: {{ ticks: {{ color: '#8b949e', maxTicksLimit: 12 }}, grid: {{ display: false }} }},
        y: {{ ticks: {{ color: '#484f58' }}, grid: {{ color: 'rgba(48,54,61,0.5)' }}, min: 0, max: 100 }}
      }}
    }}
  }});

  // Score progression table
  let phaseRows = `<tr><th>Phase</th><th>Label</th><th>Score</th></tr>
    <tr><td><span class="badge" style="background:rgba(72,79,88,0.2);color:#484f58">BASELINE</span></td><td>Without Elysium</td><td>${{phases.baseline.average}}/100</td></tr>
    <tr><td><span class="badge badge-azure">LOOP 1</span></td><td>Measurement (Elysium)</td><td style="color:var(--azure)">${{phases.loop1.average}}/100</td></tr>`;
  (phases.practice || []).forEach(p => phaseRows += `<tr><td><span class="badge badge-running">LOOP ${{p.loop}}</span></td><td>Practice</td><td>${{p.average}}/100</td></tr>`);
  phaseRows += `<tr><td><span class="badge badge-done">RE-TEST</span></td><td style="font-weight:600">After 10 loops (Elysium)</td><td style="color:var(--azure);font-weight:600">${{phases.retest.average}}/100</td></tr>`;
  document.getElementById('phasesTable').innerHTML = phaseRows;

  // Improvement table
  const deltaSign = imp.delta_retest_vs_loop1 >= 0 ? '+' : '';
  const blSign = imp.delta_retest_vs_baseline >= 0 ? '+' : '';
  document.getElementById('improvementTable').innerHTML = `
    <tr><th>Metric</th><th>Value</th></tr>
    <tr><td>&Delta; Re-Test vs Loop 1</td><td style="color:${{imp.delta_retest_vs_loop1>=0?'var(--green)':'var(--red)'}};font-weight:600">${{deltaSign}}${{imp.delta_retest_vs_loop1.toFixed(1)}}</td></tr>
    <tr><td>&Delta; Re-Test vs Baseline</td><td style="color:var(--azure)">${{blSign}}${{imp.delta_retest_vs_baseline.toFixed(1)}}</td></tr>
    <tr><td>Learning Detected</td><td><span class="badge badge-${{imp.learning_detected?'yes':'no'}}">${{imp.learning_detected?'YES':'NO'}}</span></td></tr>
    <tr><td>Transfer Efficiency</td><td>${{imp.transfer_efficiency.toFixed(3)}}</td></tr>
    <tr><td>Duration</td><td>${{(data.duration_seconds/60).toFixed(1)}} min</td></tr>
  `;

  // Category breakdown
  const baselineScores = phases.baseline.scores || {{}};
  const retestScores = phases.retest.scores || {{}};
  let taskRows = '<tr><th>Task ID</th><th>Baseline</th><th>Re-Test</th><th>&Delta;</th><th>Learning</th></tr>';
  for (const [tid, s] of Object.entries(retestScores)) {{
    const bl = baselineScores[tid];
    const rt = s.total;
    const blTotal = bl ? bl.total : 0;
    const delta = rt - blTotal;
    taskRows += `<tr>
      <td style="font-family:monospace;color:var(--azure)">${{tid}}</td>
      <td>${{blTotal.toFixed(1)}}</td>
      <td>${{rt.toFixed(1)}}</td>
      <td style="color:${{delta>=0?'var(--green)':'var(--red)'}}">${{delta >= 0 ? '+' : ''}}${{delta.toFixed(1)}}</td>
      <td><span class="badge badge-${{delta>=5?'yes':'no'}}">${{delta>=5?'YES':'NO'}}</span></td>
    </tr>`;
  }}
  document.getElementById('taskDetails').innerHTML = taskRows;
}}
loadResults();
</script>
"""


# ═══════════════════════════════════════════════════════════════════════════
# COMPARE PAGE
# ═══════════════════════════════════════════════════════════════════════════

COMPARE_PAGE = """
<div class="grid grid-2">
  <div class="card">
    <h2>📊 Compare Runs</h2>
    <p style="color:var(--muted);margin-bottom:1rem;font-size:.85rem">Select two runs to compare side-by-side.</p>
    <div style="display:flex;flex-direction:column;gap:.75rem">
      <div>
        <label style="color:var(--muted);font-size:.8rem;display:block;margin-bottom:.25rem">Run A <span style="color:var(--dim)">(earlier)</span></label>
        <select id="runA" style="width:100%"><option value="">-- Select --</option></select>
      </div>
      <div>
        <label style="color:var(--muted);font-size:.8rem;display:block;margin-bottom:.25rem">Run B <span style="color:var(--dim)">(later)</span></label>
        <select id="runB" style="width:100%"><option value="">-- Select --</option></select>
      </div>
      <button class="btn btn-azure" onclick="compareRuns()">Compare</button>
    </div>
  </div>
  <div class="card" id="comparisonResult" style="display:none">
    <h2 id="comparisonTitle">Comparison</h2>
    <div style="height:280px"><canvas id="compareChart"></canvas></div>
    <table id="compareTable" style="margin-top:1rem"></table>
  </div>
</div>

<script>
let runsList = [];
let compareChart = null;

async function init() {{
  const resp = await fetch('/api/runs');
  runsList = await resp.json();
  const selectA = document.getElementById('runA');
  const selectB = document.getElementById('runB');

  const params = new URLSearchParams(window.location.search);

  runsList.forEach(r => {{
    const opt = `<option value="${{r.id}}">${{(r.timestamp||r.id).slice(0,16).replace('T',' ')}} — ${{(r.overall_score||0).toFixed(1)}}/100</option>`;
    selectA.innerHTML += opt;
    selectB.innerHTML += opt;
  }});

  if (params.get('a')) selectA.value = params.get('a');
  if (params.get('b')) selectB.value = params.get('b');
  if (params.get('a') && params.get('b')) compareRuns();
}}
init();

async function compareRuns() {{
  const a = document.getElementById('runA').value;
  const b = document.getElementById('runB').value;
  if (!a || !b) return;

  history.pushState({{}}, '', `/compare?a=${{a}}&b=${{b}}`);

  const [respA, respB] = await Promise.all([
    fetch('/api/runs/' + a),
    fetch('/api/runs/' + b),
  ]);
  const runA = await respA.json();
  const runB = await respB.json();

  document.getElementById('comparisonResult').style.display = '';
  document.getElementById('comparisonTitle').textContent = `${{a.slice(0,16)}} vs ${{b.slice(0,16)}}`;

  if (compareChart) compareChart.destroy();
  const labels = ['Baseline','Loop 1','Re-Test'];
  const dataA = [runA.phases.baseline.average, runA.phases.loop1.average, runA.phases.retest.average];
  const dataB = [runB.phases.baseline.average, runB.phases.loop1.average, runB.phases.retest.average];

  compareChart = new Chart(document.getElementById('compareChart'), {{
    type: 'bar',
    data: {{
      labels, datasets: [
        {{ label: a.slice(0,12)+'...', data: dataA, backgroundColor: '#484f58', borderRadius: 6 }},
        {{ label: b.slice(0,12)+'...', data: dataB, backgroundColor: '#38bdf8', borderRadius: 6 }},
      ]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ labels: {{ color: '#8b949e', usePointStyle: true }} }} }},
      scales: {{
        x: {{ ticks: {{ color: '#8b949e' }}, grid: {{ display: false }} }},
        y: {{ ticks: {{ color: '#484f58' }}, grid: {{ color: 'rgba(48,54,61,0.5)' }}, min: 0, max: 100 }}
      }}
    }}
  }});

  const impA = runA.improvement;
  const impB = runB.improvement;
  document.getElementById('compareTable').innerHTML = `
    <tr><th>Metric</th><th>Run A</th><th>Run B</th><th>&Delta; A&rarr;B</th></tr>
    <tr><td>Re-Test Score</td><td>${{runA.phases.retest.average}}/100</td><td style="color:var(--azure)">${{runB.phases.retest.average}}/100</td>
      <td style="color:${{(runB.phases.retest.average-runA.phases.retest.average)>=0?'var(--green)':'var(--red)'}}">${{(runB.phases.retest.average-runA.phases.retest.average)>=0?'+':''}}${{(runB.phases.retest.average-runA.phases.retest.average).toFixed(1)}}</td></tr>
    <tr><td>&Delta; vs Loop 1</td><td>${{impA.delta_retest_vs_loop1.toFixed(1)}}</td><td>${{impB.delta_retest_vs_loop1.toFixed(1)}}</td><td>${{(impB.delta_retest_vs_loop1-impA.delta_retest_vs_loop1).toFixed(1)}}</td></tr>
    <tr><td>Learning?</td><td><span class="badge badge-${{impA.learning_detected?'yes':'no'}}">${{impA.learning_detected?'YES':'NO'}}</span></td>
      <td><span class="badge badge-${{impB.learning_detected?'yes':'no'}}">${{impB.learning_detected?'YES':'NO'}}</span></td><td></td></tr>
    <tr><td>Duration</td><td>${{(runA.duration_seconds/60).toFixed(0)}}m</td><td>${{(runB.duration_seconds/60).toFixed(0)}}m</td><td></td></tr>
  `;
}}
</script>
"""
