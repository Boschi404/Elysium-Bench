"""HTML templates for Elysium-Bench UI — single-file, no build step."""

# ═══════════════════════════════════════════════════════════════════════════
# SHARED STYLES
# ═══════════════════════════════════════════════════════════════════════════

STYLES = """
<style>
  :root {
    --bg: #0b1120; --card: #111827; --border: #1e293b;
    --text: #e2e8f0; --muted: #94a3b8; --dim: #475569;
    --cyan: #22d3ee; --blue: #3b82f6; --purple: #a78bfa;
    --green: #34d399; --red: #f87171; --amber: #fbbf24;
  }
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family: -apple-system, 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; }
  nav { background: var(--card); border-bottom: 1px solid var(--border); padding: 0 2rem; display:flex; align-items:center; gap:1.5rem; height: 56px; position:sticky; top:0; z-index:100; }
  nav a { color: var(--muted); text-decoration:none; font-size:.9rem; font-weight:500; transition:color .2s; }
  nav a:hover, nav a.active { color: var(--cyan); }
  nav .brand { font-weight:700; font-size:1.1rem; color: var(--cyan); margin-right:auto; }
  main { max-width: 1200px; margin: 2rem auto; padding: 0 1.5rem; }
  .card { background: var(--card); border:1px solid var(--border); border-radius:12px; padding:1.5rem; margin-bottom:1.5rem; }
  .card h2 { font-size:1.2rem; color: var(--cyan); margin-bottom:1rem; }
  .grid { display:grid; gap:1.5rem; }
  .grid-2 { grid-template-columns: repeat(2, 1fr); }
  .grid-3 { grid-template-columns: repeat(3, 1fr); }
  .stat { text-align:center; }
  .stat .value { font-size:2rem; font-weight:700; }
  .stat .label { font-size:.8rem; color: var(--muted); margin-top:.25rem; }
  .stat.green .value { color: var(--green); }
  .stat.red .value { color: var(--red); }
  .stat.cyan .value { color: var(--cyan); }
  table { width:100%; border-collapse:collapse; }
  th { text-align:left; padding:.75rem 1rem; color: var(--muted); font-size:.8rem; text-transform:uppercase; letter-spacing:.05em; border-bottom:1px solid var(--border); }
  td { padding:.6rem 1rem; border-bottom:1px solid var(--border); font-size:.9rem; }
  tr:hover td { background: rgba(255,255,255,0.02); }
  .badge { display:inline-block; padding:.2rem .6rem; border-radius:6px; font-size:.75rem; font-weight:600; }
  .badge-yes { background:#064e3b; color:var(--green); }
  .badge-no { background:#451a03; color:var(--amber); }
  .btn { display:inline-block; padding:.6rem 1.4rem; border-radius:8px; font-weight:600; font-size:.9rem; cursor:pointer; border:none; transition:all .2s; text-decoration:none; }
  .btn-cyan { background: var(--cyan); color:#0b1120; }
  .btn-cyan:hover { background:#67e8f9; }
  .btn-outline { background:transparent; border:1px solid var(--border); color:var(--muted); }
  .btn-outline:hover { border-color:var(--cyan); color:var(--cyan); }
  select, input { background:var(--bg); border:1px solid var(--border); color:var(--text); padding:.5rem .75rem; border-radius:6px; font-size:.9rem; }
  select:focus, input:focus { outline:none; border-color:var(--cyan); }
  .progress-bar { background:var(--border); border-radius:6px; height:6px; overflow:hidden; margin:.5rem 0; }
  .progress-bar .fill { background:linear-gradient(90deg,var(--cyan),var(--purple)); height:100%; border-radius:6px; transition:width .3s; }
  .log-line { font-family:monospace; font-size:.85rem; padding:.3rem 0; color:var(--muted); border-bottom:1px solid rgba(255,255,255,0.03); }
  .log-line .phase { color:var(--cyan); font-weight:600; }
  .log-line .score { color:var(--green); font-weight:600; }
  canvas { width:100% !important; }
  @media (max-width: 768px) { .grid-2, .grid-3 { grid-template-columns: 1fr; } }
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
    <a href="/" class="brand">🚀 Elysium-Bench</a>
    <a href="/">Dashboard</a>
    <a href="/run">Run</a>
    <a href="/compare">Compare</a>
  </nav>
  <main>
    {content}
  </main>
</body>
</html>"""


# ═══════════════════════════════════════════════════════════════════════════
# DASHBOARD PAGE
# ═══════════════════════════════════════════════════════════════════════════

DASHBOARD_PAGE = """
<div class="card">
  <h2>📊 Run History</h2>
  <div style="height:300px;"><canvas id="historyChart"></canvas></div>
</div>

<div class="card">
  <h2>📋 Recent Runs</h2>
  <table>
    <thead><tr>
      <th>Date</th><th>Baseline</th><th>Loop 1</th><th>Re-Test</th><th>Δ</th><th>Learning?</th><th>Duration</th><th></th>
    </tr></thead>
    <tbody id="runsTable"><tr><td colspan="8" style="text-align:center;color:var(--muted)">Loading...</td></tr></tbody>
  </table>
</div>

<div class="grid grid-3" id="statsGrid"></div>

<script>
async function loadDashboard() {
  const resp = await fetch('/api/runs');
  const runs = await resp.json();

  // Chart
  const ctx = document.getElementById('historyChart').getContext('2d');
  const labels = runs.slice(0, 20).reverse().map(r => r.timestamp ? r.timestamp.slice(0,16).replace('T',' ') : r.id.slice(0,15));
  new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        { label: 'Re-Test', data: runs.slice(0,20).reverse().map(r => r.overall_score || 0), borderColor: '#22d3ee', backgroundColor: 'rgba(34,211,238,0.1)', fill: true, tension: 0.3 },
        { label: 'Loop 1', data: runs.slice(0,20).reverse().map(r => r.loop1_score || 0), borderColor: '#a78bfa', borderDash: [4,4], tension: 0.3 },
        { label: 'Baseline', data: runs.slice(0,20).reverse().map(r => r.baseline_score || 0), borderColor: '#475569', borderDash: [2,2], tension: 0.3 },
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { labels: { color: '#94a3b8' } } },
      scales: {
        x: { ticks: { color: '#475569', maxTicksLimit: 10 }, grid: { color: 'rgba(255,255,255,0.03)' } },
        y: { ticks: { color: '#475569' }, grid: { color: 'rgba(255,255,255,0.03)' }, min: 0, max: 100 }
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
      <td style="color:var(--cyan);font-weight:600">${(r.overall_score||0).toFixed(1)}</td>
      <td style="color:${(r.improvement||0)>=0?'var(--green)':'var(--red)'}">${(r.improvement||0) >= 0 ? '+' : ''}${(r.improvement||0).toFixed(1)}</td>
      <td><span class="badge badge-${r.learning_detected?'yes':'no'}">${r.learning_detected?'YES':'NO'}</span></td>
      <td>${(r.duration_seconds/60).toFixed(0)}m</td>
      <td><a href="/results/${r.id}" class="btn btn-outline" style="padding:.2rem .6rem;font-size:.75rem">View</a></td>
    </tr>
  `).join('') || '<tr><td colspan="8" style="text-align:center;color:var(--muted)">No runs yet — <a href="/run" style="color:var(--cyan)">start one</a></td></tr>';

  // Stats
  const grid = document.getElementById('statsGrid');
  if (runs.length > 0) {
    const withLearning = runs.filter(r => r.learning_detected).length;
    const bestScore = Math.max(...runs.map(r => r.overall_score || 0));
    const avgImprovement = runs.filter(r => r.improvement).reduce((s,r) => s + r.improvement, 0) / runs.filter(r => r.improvement).length || 0;
    grid.innerHTML = `
      <div class="card stat cyan"><div class="value">${runs.length}</div><div class="label">Total Runs</div></div>
      <div class="card stat green"><div class="value">${withLearning}</div><div class="label">With Learning</div></div>
      <div class="card stat"><div class="value" style="color:var(--purple)">${(avgImprovement).toFixed(1)}</div><div class="label">Avg Δ Improvement</div></div>
    `;
  }
}
loadDashboard();
</script>
"""


# ═══════════════════════════════════════════════════════════════════════════
# RUN PAGE
# ═══════════════════════════════════════════════════════════════════════════

RUN_PAGE = """
<div class="grid grid-2">
  <div class="card">
    <h2>⚙️ Configure Benchmark</h2>
    <form id="runForm" style="display:flex;flex-direction:column;gap:1rem;margin-top:1rem;">
      <div>
        <label style="color:var(--muted);font-size:.85rem">Category (empty = all 11)</label>
        <select id="category" style="width:100%">
          <option value="">All categories (110 tasks)</option>
          <optgroup label="Code">
            <option value="api_development">API Development (10)</option>
            <option value="bug_fixing">Bug Fixing (10)</option>
            <option value="algorithm_implementation">Algorithm Implementation (10)</option>
          </optgroup>
          <optgroup label="Non-Code">
            <option value="data_analysis">Data Analysis (10)</option>
            <option value="mathematical_reasoning">Mathematical Reasoning (10)</option>
            <option value="logical_deduction">Logical Deduction (10)</option>
            <option value="security_analysis">Security Analysis (10)</option>
            <option value="code_review">Code Review (10)</option>
            <option value="documentation_generation">Documentation (10)</option>
            <option value="configuration_management">DevOps (10)</option>
          </optgroup>
        </select>
      </div>
      <div>
        <label style="color:var(--muted);font-size:.85rem">Number of Loops</label>
        <input type="number" id="loops" value="10" min="1" max="20" style="width:100%">
      </div>
      <button type="submit" class="btn btn-cyan" style="width:100%;padding:.8rem">▶ Start Benchmark</button>
    </form>
    <p style="color:var(--dim);font-size:.8rem;margin-top:.75rem">
      Hermes Agent must be running with <code style="color:var(--cyan)">elysium-swarmloop</code> skill loaded.<br>
      LLM provider is configured via <code>hermes config</code> — the benchmark sends tasks via <code>hermes chat</code>.
    </p>
  </div>

  <div class="card" id="progressCard" style="display:none">
    <h2 id="progressTitle">🔄 Running...</h2>
    <div class="progress-bar"><div class="fill" id="progressFill" style="width:0%"></div></div>
    <p style="color:var(--muted);font-size:.85rem" id="progressMsg">Starting...</p>
    <div id="progressLog" style="max-height:400px;overflow-y:auto;margin-top:.5rem"></div>
  </div>
</div>

<script>
let currentRunId = null;
let eventSource = null;

document.getElementById('runForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const category = document.getElementById('category').value;
  const loops = document.getElementById('loops').value;

  const resp = await fetch(`/api/runs/start?category=${encodeURIComponent(category)}&loops=${loops}`, { method:'POST' });
  const data = await resp.json();
  currentRunId = data.run_id;

  document.getElementById('progressCard').style.display = '';
  document.getElementById('progressFill').style.width = '0%';
  document.getElementById('progressLog').innerHTML = '';

  // SSE stream
  let phaseCount = 0;
  let totalPhases = parseInt(loops) + 2; // baseline + N loops + retest
  eventSource = new EventSource(`/api/runs/${currentRunId}/stream`);
  eventSource.onmessage = (evt) => {
    const msg = JSON.parse(evt.data);
    const log = document.getElementById('progressLog');
    const fill = document.getElementById('progressFill');

    if (msg.type === 'phase_start') {
      phaseCount++;
      fill.style.width = Math.min(95, (phaseCount / totalPhases * 100)) + '%';
      log.innerHTML += `<div class="log-line"><span class="phase">▶ ${msg.label}</span></div>`;
      document.getElementById('progressTitle').textContent = `🔄 ${msg.label}`;
      document.getElementById('progressMsg').textContent = `Phase ${phaseCount}/${totalPhases}`;
      log.scrollTop = log.scrollHeight;
    } else if (msg.type === 'phase_end') {
      log.innerHTML += `<div class="log-line">   Score: <span class="score">${msg.score}/100</span></div>`;
      log.scrollTop = log.scrollHeight;
    } else if (msg.type === 'status') {
      document.getElementById('progressMsg').textContent = msg.message;
    } else if (msg.type === 'complete') {
      fill.style.width = '100%';
      document.getElementById('progressTitle').textContent = '✅ Complete!';
      document.getElementById('progressMsg').innerHTML = `Benchmark finished. <a href="/results/${currentRunId}" style="color:var(--cyan)">View results →</a>`;
      eventSource.close();
    } else if (msg.type === 'error') {
      document.getElementById('progressTitle').textContent = '❌ Error';
      document.getElementById('progressMsg').textContent = msg.message;
      eventSource.close();
    }
  };
  eventSource.onerror = () => { eventSource.close(); };
});
</script>
"""


# ═══════════════════════════════════════════════════════════════════════════
# RESULTS PAGE (single run detail)
# ═══════════════════════════════════════════════════════════════════════════

RESULTS_PAGE = """
<div class="card">
  <h2>📊 Results: {run_id}</h2>
  <div style="height:300px;"><canvas id="phasesChart"></canvas></div>
</div>

<div class="grid grid-2">
  <div class="card">
    <h2>📈 Score Progression</h2>
    <table id="phasesTable"><tr><td style="color:var(--muted)">Loading...</td></tr></table>
  </div>
  <div class="card">
    <h2>🎯 Improvement</h2>
    <table id="improvementTable"><tr><td style="color:var(--muted)">Loading...</td></tr></table>
  </div>
</div>

<div class="card">
  <h2>📋 Task Details</h2>
  <table id="taskDetails"><tr><td style="color:var(--muted)">Loading...</td></tr></table>
</div>

<script>
async function loadResults() {{
  const resp = await fetch('/api/runs/{run_id}');
  const data = await resp.json();
  if (data.error) {{ document.body.innerHTML = '<main><div class="card"><h2>Not Found</h2></div></main>'; return; }}

  const phases = data.phases;
  const imp = data.improvement;

  // Chart
  const labels = ['Baseline','Loop 1'];
  const scores = [phases.baseline.average, phases.loop1.average];
  (phases.practice || []).forEach(p => {{ labels.push('Loop '+p.loop); scores.push(p.average); }});
  labels.push('Re-Test'); scores.push(phases.retest.average);

  new Chart(document.getElementById('phasesChart'), {{
    type: 'bar',
    data: {{
      labels, datasets: [{{
        data: scores,
        backgroundColor: scores.map((s,i) => i===0 ? '#475569' : i===scores.length-1 ? '#22d3ee' : '#a78bfa'),
        borderRadius: 6
      }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ display: false }} }},
      scales: {{
        x: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ display: false }} }},
        y: {{ ticks: {{ color: '#475569' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }}, min: 0, max: 100 }}
      }}
    }}
  }});

  // Score progression table
  let phaseRows = `<tr><th>Phase</th><th>Score</th></tr>
    <tr><td>Baseline (no Elysium)</td><td>${{phases.baseline.average}}/100</td></tr>
    <tr><td>Loop 1 (Elysium)</td><td>${{phases.loop1.average}}/100</td></tr>`;
  (phases.practice || []).forEach(p => phaseRows += `<tr><td>Loop ${{p.loop}} (practice)</td><td>${{p.average}}/100</td></tr>`);
  phaseRows += `<tr><td style="color:var(--cyan);font-weight:600">Re-Test</td><td style="color:var(--cyan);font-weight:600">${{phases.retest.average}}/100</td></tr>`;
  document.getElementById('phasesTable').innerHTML = phaseRows;

  // Improvement table
  const deltaSign = imp.delta_retest_vs_loop1 >= 0 ? '+' : '';
  const blSign = imp.delta_retest_vs_baseline >= 0 ? '+' : '';
  document.getElementById('improvementTable').innerHTML = `
    <tr><th>Metric</th><th>Value</th></tr>
    <tr><td>Δ Re-Test vs Loop 1</td><td style="color:${{imp.delta_retest_vs_loop1>=0?'var(--green)':'var(--red)'}};font-weight:600">${{deltaSign}}${{imp.delta_retest_vs_loop1}}</td></tr>
    <tr><td>Δ Re-Test vs Baseline</td><td style="color:var(--cyan)">${{blSign}}${{imp.delta_retest_vs_baseline}}</td></tr>
    <tr><td>Learning Detected</td><td><span class="badge badge-${{imp.learning_detected?'yes':'no'}}">${{imp.learning_detected?'YES':'NO'}}</span></td></tr>
    <tr><td>Transfer Efficiency</td><td>${{imp.transfer_efficiency}}</td></tr>
    <tr><td>Duration</td><td>${{(data.duration_seconds/60).toFixed(1)}} min</td></tr>
  `;

  // Task details
  const baselineScores = phases.baseline.scores || {{}};
  const retestScores = phases.retest.scores || {{}};
  let taskRows = '<tr><th>Task</th><th>Baseline</th><th>Re-Test</th><th>Δ</th></tr>';
  for (const [tid, s] of Object.entries(retestScores)) {{
    const bl = baselineScores[tid];
    const rt = s.total;
    const blTotal = bl ? bl.total : 0;
    const delta = rt - blTotal;
    taskRows += `<tr>
      <td>${{tid}}</td>
      <td>${{blTotal.toFixed(1)}}</td>
      <td style="color:var(--cyan)">${{rt.toFixed(1)}}</td>
      <td style="color:${{delta>=0?'var(--green)':'var(--red)'}}">${{delta >= 0 ? '+' : ''}}${{delta.toFixed(1)}}</td>
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
    <p style="color:var(--muted);margin-bottom:1rem">Select two runs to compare side-by-side.</p>
    <div style="display:flex;flex-direction:column;gap:.75rem">
      <div>
        <label style="color:var(--muted);font-size:.85rem">Run A (earlier)</label>
        <select id="runA" style="width:100%"><option value="">-- Select --</option></select>
      </div>
      <div>
        <label style="color:var(--muted);font-size:.85rem">Run B (later)</label>
        <select id="runB" style="width:100%"><option value="">-- Select --</option></select>
      </div>
      <button class="btn btn-cyan" onclick="compareRuns()">Compare</button>
    </div>
  </div>
  <div class="card" id="comparisonResult" style="display:none">
    <h2 id="comparisonTitle">Comparison</h2>
    <div style="height:250px"><canvas id="compareChart"></canvas></div>
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

  // Pre-select from URL params
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

  // Update URL
  history.pushState({{}}, '', `/compare?a=${{a}}&b=${{b}}`);

  const [respA, respB] = await Promise.all([
    fetch('/api/runs/' + a),
    fetch('/api/runs/' + b),
  ]);
  const runA = await respA.json();
  const runB = await respB.json();

  document.getElementById('comparisonResult').style.display = '';
  document.getElementById('comparisonTitle').textContent = `${{a.slice(0,16)}} vs ${{b.slice(0,16)}}`;

  // Chart
  if (compareChart) compareChart.destroy();
  const labels = ['Baseline','Loop 1','Re-Test'];
  const dataA = [runA.phases.baseline.average, runA.phases.loop1.average, runA.phases.retest.average];
  const dataB = [runB.phases.baseline.average, runB.phases.loop1.average, runB.phases.retest.average];

  compareChart = new Chart(document.getElementById('compareChart'), {{
    type: 'bar',
    data: {{
      labels, datasets: [
        {{ label: a.slice(0,12)+'...', data: dataA, backgroundColor: '#475569', borderRadius: 6 }},
        {{ label: b.slice(0,12)+'...', data: dataB, backgroundColor: '#22d3ee', borderRadius: 6 }},
      ]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ labels: {{ color: '#94a3b8' }} }} }},
      scales: {{
        x: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ display: false }} }},
        y: {{ ticks: {{ color: '#475569' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }}, min: 0, max: 100 }}
      }}
    }}
  }});

  // Comparison table
  const impA = runA.improvement;
  const impB = runB.improvement;
  document.getElementById('compareTable').innerHTML = `
    <tr><th>Metric</th><th>Run A</th><th>Run B</th><th>Δ A→B</th></tr>
    <tr><td>Re-Test Score</td><td>${{runA.phases.retest.average}}/100</td><td style="color:var(--cyan)">${{runB.phases.retest.average}}/100</td>
      <td style="color:${{(runB.phases.retest.average-runA.phases.retest.average)>=0?'var(--green)':'var(--red)'}}">${{(runB.phases.retest.average-runA.phases.retest.average)>=0?'+':''}}${{(runB.phases.retest.average-runA.phases.retest.average).toFixed(1)}}</td></tr>
    <tr><td>Δ vs Loop 1</td><td>${{impA.delta_retest_vs_loop1}}</td><td>${{impB.delta_retest_vs_loop1}}</td><td>${{(impB.delta_retest_vs_loop1-impA.delta_retest_vs_loop1).toFixed(1)}}</td></tr>
    <tr><td>Learning?</td><td><span class="badge badge-${{impA.learning_detected?'yes':'no'}}">${{impA.learning_detected?'YES':'NO'}}</span></td>
      <td><span class="badge badge-${{impB.learning_detected?'yes':'no'}}">${{impB.learning_detected?'YES':'NO'}}</span></td><td></td></tr>
    <tr><td>Duration</td><td>${{(runA.duration_seconds/60).toFixed(0)}}m</td><td>${{(runB.duration_seconds/60).toFixed(0)}}m</td><td></td></tr>
  `;
}}
</script>
"""
