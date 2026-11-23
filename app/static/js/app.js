/**
 * Carbon-Aware CI/CD Scheduler Dashboard Application
 * Handles real-time telemetry, 5 view switching, jobs table, analytics charts,
 * simulation control room, settings persistence, and terminal streaming.
 */

const AppState = {
  activeView: 'dashboard',
  currentIntensity: 142.0,
  currentMode: 'amber',
  thresholds: { green: 100, amber: 250 },
  simulationEnabled: false,
  simulatedIntensity: 142,
  provider: 'NESO National Grid UK',
  isSimulated: false,
  autoScrollTerminal: true,
  jobsFilter: { search: '', mode: 'all', status: 'all' },
  historyChart: null,
  efficiencyChart: null,
  pollTimer: null
};

// Initialize Application on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  initTerminal();
  initSimulationControls();
  initSettingsForm();
  initQuickActions();
  initNewJobModal();
  
  // Initial data load
  fetchStatus();
  fetchJobs();
  fetchAnalytics();
  fetchSettings();

  // Polling every 5 seconds
  AppState.pollTimer = setInterval(() => {
    fetchStatus(true);
  }, 5000);

  // Handle URL hash changes
  window.addEventListener('hashchange', handleHashRouting);
  if (window.location.hash) {
    handleHashRouting();
  }
});

/* ==========================================================================
   Navigation Router
   ========================================================================== */
function initNavigation() {
  const navLinks = document.querySelectorAll('.nav-link');
  navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const targetView = link.getAttribute('data-view');
      switchView(targetView);
      window.location.hash = targetView;
    });
  });

  // Mobile menu toggle
  const mobileMenuBtn = document.getElementById('btn-mobile-menu');
  const sidebar = document.getElementById('app-sidebar');
  if (mobileMenuBtn && sidebar) {
    mobileMenuBtn.addEventListener('click', () => {
      sidebar.classList.toggle('hidden');
      sidebar.classList.toggle('flex');
    });
  }
}

function handleHashRouting() {
  const hash = window.location.hash.replace('#', '');
  const validViews = ['dashboard', 'pipelines', 'analytics', 'simulation', 'settings'];
  if (validViews.includes(hash)) {
    switchView(hash);
  }
}

function switchView(viewName) {
  AppState.activeView = viewName;

  // Update nav links active class
  document.querySelectorAll('.nav-link').forEach(link => {
    if (link.getAttribute('data-view') === viewName) {
      link.classList.add('active');
    } else {
      link.classList.remove('active');
    }
  });

  // Show/Hide views
  document.querySelectorAll('.view-section').forEach(section => {
    section.classList.add('hidden');
  });

  const targetSection = document.getElementById(`view-${viewName}`);
  if (targetSection) {
    targetSection.classList.remove('hidden');
  }

  // Refresh view specific components
  if (viewName === 'analytics') {
    fetchAnalytics();
  } else if (viewName === 'pipelines') {
    fetchJobs();
  } else if (viewName === 'dashboard') {
    fetchStatus();
  }
}

/* ==========================================================================
   Status & Telemetry Updates
   ========================================================================== */
async function fetchStatus(isBackground = false) {
  try {
    const res = await fetch('/api/v1/status');
    if (!res.ok) throw new Error('Status fetch failed');
    const data = await res.json();
    
    AppState.currentIntensity = data.carbon_intensity_gco2_kwh;
    AppState.currentMode = data.pipeline_mode;
    AppState.thresholds = data.thresholds || AppState.thresholds;
    AppState.isSimulated = data.is_simulated;
    AppState.simulationEnabled = data.simulation_enabled;
    AppState.provider = data.provider;

    updateHeaderStatus(data);
    updateDashboardMetrics(data);
    updateSimulationPreview(AppState.currentIntensity);

  } catch (err) {
    if (!isBackground) {
      console.warn('Network or API status error:', err);
    }
  }
}

function updateHeaderStatus(data) {
  const badgeEl = document.getElementById('header-status-badge');
  const simPill = document.getElementById('header-sim-pill');
  const providerEl = document.getElementById('header-provider-name');

  if (providerEl) {
    providerEl.textContent = data.provider || 'National Grid UK';
  }

  if (simPill) {
    if (data.is_simulated) {
      simPill.classList.remove('hidden');
      simPill.classList.add('flex');
    } else {
      simPill.classList.add('hidden');
      simPill.classList.remove('flex');
    }
  }

  if (badgeEl) {
    badgeEl.className = 'px-2.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1.5 ' +
      (data.pipeline_mode === 'green' ? 'badge-green' : data.pipeline_mode === 'amber' ? 'badge-amber' : 'badge-red');
    
    badgeEl.innerHTML = `
      <span class="pulse-light pulse-${data.pipeline_mode}"></span>
      <span>${data.pipeline_mode.toUpperCase()} MODE</span>
    `;
  }
}

function updateDashboardMetrics(data) {
  // Update Large Metric Number
  const intensityValEl = document.getElementById('metric-intensity-val');
  const intensityCardEl = document.getElementById('card-carbon-intensity');
  const statusLightEl = document.getElementById('dashboard-status-light');
  const statusTitleEl = document.getElementById('dashboard-status-title');
  const statusDescEl = document.getElementById('dashboard-status-desc');
  const modeBadgeEl = document.getElementById('dashboard-mode-badge');
  const gaugePin = document.getElementById('dashboard-gauge-pin');

  if (intensityValEl) {
    intensityValEl.textContent = Math.round(data.carbon_intensity_gco2_kwh);
    
    // Glowing color classes
    intensityValEl.classList.remove('glow-green', 'glow-amber', 'glow-red');
    intensityValEl.classList.add(`glow-${data.pipeline_mode}`);
  }

  // Update Status Light and text
  if (statusLightEl) {
    statusLightEl.className = `pulse-light pulse-${data.pipeline_mode}`;
  }

  if (modeBadgeEl) {
    modeBadgeEl.className = `px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider badge-${data.pipeline_mode}`;
    modeBadgeEl.textContent = `${data.pipeline_mode} Execution Mode`;
  }

  if (statusTitleEl && data.mode_details) {
    statusTitleEl.textContent = data.mode_details.title;
  }
  if (statusDescEl && data.mode_details) {
    statusDescEl.textContent = data.mode_details.description;
  }

  // Position the gauge needle (range 0 to 400 gCO2/kWh)
  if (gaugePin) {
    const clamped = Math.max(0, Math.min(400, data.carbon_intensity_gco2_kwh));
    const pct = (clamped / 400) * 100;
    gaugePin.style.left = `${pct}%`;
  }

  // Update Companion Cards
  if (data.summary) {
    const savedEl = document.getElementById('stat-saved-kg');
    const jobsCountEl = document.getElementById('stat-jobs-count');
    const deferredEl = document.getElementById('stat-deferred-count');
    
    if (savedEl) savedEl.textContent = `${data.summary.total_saved_kg} kg`;
    if (jobsCountEl) jobsCountEl.textContent = data.summary.total_jobs;
    if (deferredEl) deferredEl.textContent = data.summary.deferred_count;
  }
}

/* ==========================================================================
   Interactive Terminal & Console Logging
   ========================================================================== */
function initTerminal() {
  const terminalBody = document.getElementById('terminal-body');
  const btnClear = document.getElementById('btn-terminal-clear');
  const btnCopy = document.getElementById('btn-terminal-copy');
  const btnAutoScroll = document.getElementById('btn-terminal-autoscroll');
  const terminalForm = document.getElementById('terminal-cli-form');
  const terminalInput = document.getElementById('terminal-cli-input');

  if (btnClear && terminalBody) {
    btnClear.addEventListener('click', () => {
      terminalBody.innerHTML = `
        <div class="log-line text-slate-500">// Terminal cleared by user. GreenOps dispatcher daemon listening...</div>
      `;
      showToast('Terminal logs cleared', 'info');
    });
  }

  if (btnCopy && terminalBody) {
    btnCopy.addEventListener('click', () => {
      const text = terminalBody.innerText;
      navigator.clipboard.writeText(text).then(() => {
        showToast('Console logs copied to clipboard', 'success');
      }).catch(() => {
        showToast('Failed to copy to clipboard', 'warning');
      });
    });
  }

  if (btnAutoScroll) {
    btnAutoScroll.addEventListener('click', () => {
      AppState.autoScrollTerminal = !AppState.autoScrollTerminal;
      btnAutoScroll.textContent = `Auto-Scroll: ${AppState.autoScrollTerminal ? 'ON' : 'OFF'}`;
      btnAutoScroll.classList.toggle('text-emerald-400', AppState.autoScrollTerminal);
      btnAutoScroll.classList.toggle('text-slate-400', !AppState.autoScrollTerminal);
    });
  }

  if (terminalForm && terminalInput) {
    terminalForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const cmd = terminalInput.value.trim();
      if (!cmd) return;
      handleTerminalCommand(cmd);
      terminalInput.value = '';
    });
  }
}

function appendTerminalLog(message, type = 'info') {
  const terminalBody = document.getElementById('terminal-body');
  if (!terminalBody) return;

  const now = new Date();
  const timeStr = now.toTimeString().split(' ')[0];

  const lineEl = document.createElement('div');
  lineEl.className = 'log-line';

  let typeClass = 'log-info';
  if (type === 'success' || type === 'green') typeClass = 'log-success';
  else if (type === 'warning' || type === 'amber') typeClass = 'log-warning';
  else if (type === 'danger' || type === 'red' || type === 'alert') typeClass = 'log-danger';
  else if (type === 'meta') typeClass = 'log-meta';

  lineEl.innerHTML = `
    <span class="log-timestamp">[${timeStr}]</span>
    <span class="${typeClass}">${escapeHtml(message)}</span>
  `;

  terminalBody.appendChild(lineEl);

  if (AppState.autoScrollTerminal) {
    terminalBody.scrollTop = terminalBody.scrollHeight;
  }
}

function streamTerminalLogs(logsArray, delay = 80) {
  let index = 0;
  function printNext() {
    if (index >= logsArray.length) return;
    const line = logsArray[index];
    let type = 'info';
    if (line.includes('OPTIMAL') || line.includes('SUCCESS') || line.includes('GREEN') || line.includes('APPROVED')) {
      type = 'success';
    } else if (line.includes('AMBER') || line.includes('MODERATE') || line.includes('Throttled')) {
      type = 'warning';
    } else if (line.includes('RED') || line.includes('ALERT') || line.includes('DEFERRED') || line.includes('deferred')) {
      type = 'danger';
    }
    appendTerminalLog(line, type);
    index++;
    setTimeout(printNext, delay);
  }
  printNext();
}

function handleTerminalCommand(cmd) {
  appendTerminalLog(`$ ${cmd}`, 'meta');
  const lower = cmd.toLowerCase();

  if (lower === 'help') {
    appendTerminalLog('Available commands:');
    appendTerminalLog('  green-ci status       - View live telemetry & threshold mode');
    appendTerminalLog('  green-ci run [name]   - Trigger a test CI/CD job');
    appendTerminalLog('  green-ci jobs         - Print recent pipelines list');
    appendTerminalLog('  green-ci clear        - Clear log buffer');
    appendTerminalLog('  green-ci sim <val>    - Quickly set simulated intensity (e.g. 75 or 320)');
  } else if (lower.includes('status')) {
    appendTerminalLog(`Current Intensity: ${AppState.currentIntensity} gCO2/kWh | Mode: ${AppState.currentMode.toUpperCase()}`);
    appendTerminalLog(`Thresholds: Green < ${AppState.thresholds.green} | Amber < ${AppState.thresholds.amber} | Red >= ${AppState.thresholds.amber}`);
    appendTerminalLog(`Provider: ${AppState.provider} (Simulated: ${AppState.isSimulated})`);
  } else if (lower.startsWith('green-ci sim ') || lower.startsWith('sim ')) {
    const parts = cmd.split(' ');
    const val = parseFloat(parts[parts.length - 1]);
    if (!isNaN(val)) {
      applySimulation(val);
      appendTerminalLog(`Simulation override applied: ${val} gCO2/kWh`, 'success');
    } else {
      appendTerminalLog('Invalid number. Usage: green-ci sim 85', 'warning');
    }
  } else if (lower.startsWith('green-ci run') || lower.startsWith('run')) {
    const jobName = cmd.replace(/^green-ci run|^run/i, '').trim() || 'CLI Triggered PyTest Suite';
    triggerJobDispatch(jobName, 'main');
  } else if (lower.includes('clear')) {
    document.getElementById('btn-terminal-clear').click();
  } else if (lower.includes('jobs')) {
    appendTerminalLog('Fetching jobs table to Pipelines view...');
    switchView('pipelines');
  } else {
    appendTerminalLog(`Command not recognized: '${cmd}'. Type 'help' for options.`, 'warning');
  }
}

/* ==========================================================================
   Quick Actions & Job Dispatch
   ========================================================================== */
function initQuickActions() {
  const btnRunTest = document.getElementById('btn-run-test-job');
  const btnRunFromNav = document.getElementById('btn-nav-run-job');

  if (btnRunTest) {
    btnRunTest.addEventListener('click', () => {
      openJobModal();
    });
  }
  if (btnRunFromNav) {
    btnRunFromNav.addEventListener('click', () => {
      openJobModal();
    });
  }
}

async function triggerJobDispatch(jobName, branch = 'main', force = false, simulateVal = null) {
  try {
    appendTerminalLog(`>>> Dispatching job '${jobName}' on branch '${branch}'...`, 'info');
    showToast(`Dispatching '${jobName}'...`, 'info');

    const payload = {
      job_name: jobName,
      branch: branch,
      force: force
    };
    if (simulateVal !== null) {
      payload.simulate_intensity = simulateVal;
    }

    const res = await fetch('/api/v1/jobs/dispatch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (data.status === 'success') {
      if (data.console_output && data.console_output.length > 0) {
        streamTerminalLogs(data.console_output);
      }
      
      const job = data.job;
      if (job.status.includes('Deferred')) {
        showToast(`Job deferred: High carbon intensity (${job.intensity} gCO2/kWh)`, 'warning');
      } else {
        showToast(`Job executed successfully under ${job.mode.toUpperCase()} mode!`, 'success');
      }

      // Refresh data
      fetchJobs();
      fetchAnalytics();
      fetchStatus();
    } else {
      showToast(data.message || 'Dispatch failed', 'error');
    }
  } catch (err) {
    console.error('Job dispatch error:', err);
    showToast('Failed to contact scheduler API', 'error');
  }
}

/* ==========================================================================
   Pipelines & Jobs Manager
   ========================================================================== */
async function fetchJobs() {
  try {
    const search = AppState.jobsFilter.search;
    const mode = AppState.jobsFilter.mode;
    const status = AppState.jobsFilter.status;

    let url = `/api/v1/jobs?`;
    if (search) url += `search=${encodeURIComponent(search)}&`;
    if (mode && mode !== 'all') url += `mode=${encodeURIComponent(mode)}&`;
    if (status && status !== 'all') url += `status=${encodeURIComponent(status)}&`;

    const res = await fetch(url);
    const data = await res.json();
    renderJobsTable(data.jobs || []);
  } catch (err) {
    console.error('Error fetching jobs:', err);
  }
}

function renderJobsTable(jobs) {
  const tbody = document.getElementById('jobs-table-body');
  const countEl = document.getElementById('jobs-count-badge');
  if (!tbody) return;

  if (countEl) {
    countEl.textContent = `${jobs.length} Jobs`;
  }

  if (jobs.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" class="px-6 py-12 text-center text-slate-400">
          <i class="fa-solid fa-inbox text-3xl mb-3 block text-slate-600"></i>
          No CI/CD pipeline jobs found matching the active filter criteria.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = jobs.map(job => {
    const isDeferred = job.status.toLowerCase().includes('defer') || job.status.toLowerCase().includes('pause');
    const triggerDate = new Date(job.trigger_time);
    const timeAgo = formatTimeAgo(triggerDate);
    
    let modeBadge = '';
    if (job.mode === 'green') {
      modeBadge = `<span class="badge-green px-2.5 py-0.5 rounded-full text-xs font-semibold inline-flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-emerald-400"></span>GREEN</span>`;
    } else if (job.mode === 'amber') {
      modeBadge = `<span class="badge-amber px-2.5 py-0.5 rounded-full text-xs font-semibold inline-flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-amber-400"></span>AMBER</span>`;
    } else {
      modeBadge = `<span class="badge-red px-2.5 py-0.5 rounded-full text-xs font-semibold inline-flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-red-400"></span>RED</span>`;
    }

    let statusPill = '';
    if (isDeferred) {
      statusPill = `<span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-xs font-medium bg-red-950/80 text-red-300 border border-red-800/60"><i class="fa-solid fa-clock-rotate-left"></i> Deferred (Paused)</span>`;
    } else if (job.status.includes('Forced')) {
      statusPill = `<span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-xs font-medium bg-amber-950/80 text-amber-300 border border-amber-800/60"><i class="fa-solid fa-bolt"></i> Executed (Forced)</span>`;
    } else {
      statusPill = `<span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-xs font-medium bg-emerald-950/80 text-emerald-300 border border-emerald-800/60"><i class="fa-solid fa-circle-check"></i> Executed</span>`;
    }

    return `
      <tr class="border-b border-slate-800/60 hover:bg-slate-800/30 transition-colors">
        <td class="px-5 py-4">
          <div class="font-semibold text-white flex items-center gap-2">
            <i class="fa-solid fa-cube text-slate-500 text-sm"></i>
            <span>${escapeHtml(job.name)}</span>
          </div>
          <div class="text-xs text-slate-400 font-mono mt-0.5 flex items-center gap-2">
            <span class="text-indigo-400"><i class="fa-solid fa-code-branch text-[10px]"></i> ${escapeHtml(job.branch)}</span>
            <span class="text-slate-600">•</span>
            <span class="text-slate-400">#${escapeHtml(job.commit || 'head')}</span>
          </div>
        </td>
        <td class="px-5 py-4 text-xs text-slate-300">
          <div>${timeAgo}</div>
          <div class="text-[11px] text-slate-500">${triggerDate.toLocaleTimeString()}</div>
        </td>
        <td class="px-5 py-4">
          <div class="font-mono text-sm font-bold text-slate-200">
            ${Math.round(job.intensity)} <span class="text-[10px] font-normal text-slate-400">gCO2/kWh</span>
          </div>
        </td>
        <td class="px-5 py-4">
          ${modeBadge}
        </td>
        <td class="px-5 py-4">
          ${statusPill}
          ${isDeferred && job.deferral_reason ? `<div class="text-[11px] text-slate-500 mt-1 max-w-xs truncate" title="${escapeHtml(job.deferral_reason)}">${escapeHtml(job.deferral_reason)}</div>` : ''}
        </td>
        <td class="px-5 py-4 text-right">
          <div class="flex items-center justify-end gap-2">
            <button class="btn-view-logs text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-2.5 py-1.5 rounded border border-slate-700 transition" data-job-id="${job.id}" title="View Terminal Logs">
              <i class="fa-solid fa-terminal mr-1"></i> Logs
            </button>
            ${isDeferred ? `
              <button class="btn-force-run text-xs bg-amber-600/20 hover:bg-amber-600/30 text-amber-300 border border-amber-600/40 px-2.5 py-1.5 rounded transition" data-job-id="${job.id}" title="Bypass Red Deferral">
                <i class="fa-solid fa-bolt mr-1"></i> Force Run
              </button>
            ` : ''}
          </div>
        </td>
      </tr>
    `;
  }).join('');

  // Attach event listeners for buttons in table
  tbody.querySelectorAll('.btn-view-logs').forEach(btn => {
    btn.addEventListener('click', () => {
      const jid = btn.getAttribute('data-job-id');
      const job = jobs.find(j => j.id === jid);
      if (job && job.logs) {
        switchView('dashboard');
        appendTerminalLog(`=== LOGS FOR PIPELINE ${job.name} (${job.id}) ===`, 'meta');
        streamTerminalLogs(job.logs, 40);
        showToast(`Showing logs for ${job.name}`, 'info');
      }
    });
  });

  tbody.querySelectorAll('.btn-force-run').forEach(btn => {
    btn.addEventListener('click', async () => {
      const jid = btn.getAttribute('data-job-id');
      try {
        const res = await fetch(`/api/v1/jobs/${jid}/force`, { method: 'POST' });
        const resData = await res.json();
        if (resData.status === 'success') {
          showToast(`Force dispatched ${jid} successfully!`, 'success');
          fetchJobs();
          fetchAnalytics();
        } else {
          showToast('Failed to force job: ' + (resData.message || 'error'), 'error');
        }
      } catch (err) {
        showToast('Error calling force endpoint', 'error');
      }
    });
  });
}

function initJobFilters() {
  const searchInput = document.getElementById('jobs-search-input');
  const modeSelect = document.getElementById('jobs-filter-mode');
  const statusSelect = document.getElementById('jobs-filter-status');

  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      AppState.jobsFilter.search = e.target.value;
      fetchJobs();
    });
  }
  if (modeSelect) {
    modeSelect.addEventListener('change', (e) => {
      AppState.jobsFilter.mode = e.target.value;
      fetchJobs();
    });
  }
  if (statusSelect) {
    statusSelect.addEventListener('change', (e) => {
      AppState.jobsFilter.status = e.target.value;
      fetchJobs();
    });
  }
}

/* ==========================================================================
   Analytics & Carbon Savings
   ========================================================================== */
async function fetchAnalytics() {
  try {
    const res = await fetch('/api/v1/analytics');
    const json = await res.json();
    if (json.status !== 'success') return;

    const data = json.data;
    renderAnalyticsCards(data.summary);
    render24HourCurve(data.history_24h);
    renderEfficiencyDonut(data.breakdown);
  } catch (err) {
    console.error('Error fetching analytics:', err);
  }
}

function renderAnalyticsCards(summary) {
  if (!summary) return;

  const totalSavedEl = document.getElementById('analytics-total-saved-kg');
  const treesEl = document.getElementById('analytics-trees-equiv');
  const milesEl = document.getElementById('analytics-ev-miles');
  const greenPctEl = document.getElementById('analytics-green-pct');
  const totalEmittedEl = document.getElementById('analytics-total-emitted');
  const baselineEmittedEl = document.getElementById('analytics-baseline-emitted');

  if (totalSavedEl) totalSavedEl.textContent = `${summary.total_saved_kg} kg`;
  if (treesEl) treesEl.textContent = summary.trees_equivalent;
  if (milesEl) milesEl.textContent = `${summary.ev_miles_equivalent} mi`;
  if (greenPctEl) greenPctEl.textContent = `${summary.green_window_ratio_pct}%`;
  if (totalEmittedEl) totalEmittedEl.textContent = `${(summary.total_emitted_g / 1000).toFixed(2)} kg`;
  if (baselineEmittedEl) baselineEmittedEl.textContent = `${(summary.total_baseline_g / 1000).toFixed(2)} kg`;
}

function render24HourCurve(history) {
  const canvas = document.getElementById('chart-history-24h');
  const fallbackContainer = document.getElementById('chart-history-fallback');
  if (!canvas) return;

  if (window.Chart) {
    if (AppState.historyChart) {
      AppState.historyChart.destroy();
    }

    const ctx = canvas.getContext('2d');
    const greenLimit = history.green_threshold || 100;
    const amberLimit = history.amber_threshold || 250;

    AppState.historyChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: history.labels,
        datasets: [
          {
            label: 'Grid Carbon Intensity (gCO2/kWh)',
            data: history.intensity,
            borderColor: '#38bdf8',
            backgroundColor: 'rgba(56, 189, 248, 0.1)',
            borderWidth: 2.5,
            fill: true,
            tension: 0.35,
            pointRadius: 3,
            pointBackgroundColor: '#38bdf8'
          },
          {
            label: 'Green Threshold (100)',
            data: history.labels.map(() => greenLimit),
            borderColor: '#10b981',
            borderWidth: 1.5,
            borderDash: [5, 5],
            pointRadius: 0,
            fill: false
          },
          {
            label: 'Alert Threshold (250)',
            data: history.labels.map(() => amberLimit),
            borderColor: '#ef4444',
            borderWidth: 1.5,
            borderDash: [5, 5],
            pointRadius: 0,
            fill: false
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: { color: '#94a3b8', boxWidth: 12 }
          },
          tooltip: {
            backgroundColor: '#0f172a',
            borderColor: '#334155',
            borderWidth: 1
          }
        },
        scales: {
          x: {
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { color: '#64748b' }
          },
          y: {
            beginAtZero: true,
            max: 350,
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { color: '#64748b' }
          }
        }
      }
    });
  } else if (fallbackContainer) {
    // High-fidelity SVG Sparkline fallback when offline or Chart.js CDN is unavailable
    renderSvgLineChart(fallbackContainer, history);
  }
}

function renderSvgLineChart(container, history) {
  const width = 800;
  const height = 240;
  const maxVal = 350;
  const pts = history.intensity.map((val, idx) => {
    const x = (idx / (history.intensity.length - 1)) * (width - 40) + 20;
    const y = height - 30 - (val / maxVal) * (height - 60);
    return `${x},${y}`;
  }).join(' ');

  const greenY = height - 30 - (history.green_threshold / maxVal) * (height - 60);
  const redY = height - 30 - (history.amber_threshold / maxVal) * (height - 60);

  container.innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" class="w-full h-full">
      <!-- Threshold lines -->
      <line x1="20" y1="${greenY}" x2="${width - 20}" y2="${greenY}" stroke="#10b981" stroke-dasharray="4" stroke-width="1.5" />
      <text x="${width - 120}" y="${greenY - 6}" fill="#10b981" font-size="11">Green Limit (100)</text>

      <line x1="20" y1="${redY}" x2="${width - 20}" y2="${redY}" stroke="#ef4444" stroke-dasharray="4" stroke-width="1.5" />
      <text x="${width - 120}" y="${redY - 6}" fill="#ef4444" font-size="11">Red Limit (250)</text>

      <!-- Polyline -->
      <polyline fill="none" stroke="#38bdf8" stroke-width="3" points="${pts}" />
      
      <!-- Axis Labels -->
      <text x="20" y="${height - 10}" fill="#64748b" font-size="11">00:00</text>
      <text x="${width / 2}" y="${height - 10}" fill="#64748b" font-size="11">12:00</text>
      <text x="${width - 45}" y="${height - 10}" fill="#64748b" font-size="11">23:00</text>
    </svg>
  `;
}

function renderEfficiencyDonut(breakdown) {
  const canvas = document.getElementById('chart-efficiency-donut');
  const fallbackContainer = document.getElementById('chart-donut-fallback');
  if (!canvas) return;

  const labels = ['Green Window', 'Amber Window', 'Red (Deferred)'];
  const values = [breakdown.green_count, breakdown.amber_count, breakdown.red_count];
  const colors = ['#10b981', '#f59e0b', '#ef4444'];

  if (window.Chart) {
    if (AppState.efficiencyChart) {
      AppState.efficiencyChart.destroy();
    }
    const ctx = canvas.getContext('2d');
    AppState.efficiencyChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [{
          data: values,
          backgroundColor: colors,
          borderColor: '#0f172a',
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: { color: '#94a3b8' }
          }
        },
        cutout: '70%'
      }
    });
  } else if (fallbackContainer) {
    fallbackContainer.innerHTML = `
      <div class="flex items-center justify-around h-full">
        <div class="text-center">
          <div class="text-2xl font-bold text-emerald-400">${breakdown.green_pct}%</div>
          <div class="text-xs text-slate-400">Green Windows</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-amber-400">${breakdown.amber_pct}%</div>
          <div class="text-xs text-slate-400">Amber Windows</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-red-400">${breakdown.red_pct}%</div>
          <div class="text-xs text-slate-400">Red Windows</div>
        </div>
      </div>
    `;
  }
}

/* ==========================================================================
   Simulation & Control Room (Demo Mode)
   ========================================================================== */
function initSimulationControls() {
  const slider = document.getElementById('sim-slider');
  const numberInput = document.getElementById('sim-number-input');
  const masterToggle = document.getElementById('sim-master-toggle');
  const btnApplySim = document.getElementById('btn-apply-simulation');
  const btnResetSim = document.getElementById('btn-reset-simulation');
  const btnTestDispatch = document.getElementById('btn-sim-test-dispatch');

  // Sync Slider and Number Input
  if (slider && numberInput) {
    slider.addEventListener('input', (e) => {
      numberInput.value = e.target.value;
      updateSimulationPreview(parseFloat(e.target.value));
    });
    numberInput.addEventListener('input', (e) => {
      slider.value = e.target.value;
      updateSimulationPreview(parseFloat(e.target.value));
    });
  }

  // Quick Preset Buttons
  document.querySelectorAll('.btn-sim-preset').forEach(btn => {
    btn.addEventListener('click', () => {
      const val = parseFloat(btn.getAttribute('data-value'));
      if (!isNaN(val)) {
        if (slider) slider.value = val;
        if (numberInput) numberInput.value = val;
        updateSimulationPreview(val);
        applySimulation(val);
      }
    });
  });

  if (masterToggle) {
    masterToggle.addEventListener('change', (e) => {
      const isEnabled = e.target.checked;
      const val = slider ? parseFloat(slider.value) : 142;
      if (isEnabled) {
        applySimulation(val);
      } else {
        disableSimulation();
      }
    });
  }

  if (btnApplySim) {
    btnApplySim.addEventListener('click', () => {
      const val = slider ? parseFloat(slider.value) : 142;
      applySimulation(val);
    });
  }

  if (btnResetSim) {
    btnResetSim.addEventListener('click', () => {
      disableSimulation();
    });
  }

  if (btnTestDispatch) {
    btnTestDispatch.addEventListener('click', () => {
      const val = slider ? parseFloat(slider.value) : AppState.currentIntensity;
      switchView('dashboard');
      triggerJobDispatch('Simulated Run: High Intensity Gate Test', 'demo/stress-test', false, val);
    });
  }
}

function updateSimulationPreview(intensity) {
  const previewModeBadge = document.getElementById('sim-preview-mode-badge');
  const previewPolicyTitle = document.getElementById('sim-preview-policy-title');
  const previewPolicyDesc = document.getElementById('sim-preview-policy-desc');
  const previewCard = document.getElementById('sim-preview-card');
  const previewEmissions = document.getElementById('sim-preview-emissions');

  const greenLimit = AppState.thresholds.green || 100;
  const amberLimit = AppState.thresholds.amber || 250;

  let mode = 'green';
  if (intensity < greenLimit) {
    mode = 'green';
  } else if (intensity < amberLimit) {
    mode = 'amber';
  } else {
    mode = 'red';
  }

  // Calculated emissions for 10-minute 50W test build
  const energyKwh = 0.05 * (10 / 60);
  const co2Grams = (energyKwh * intensity).toFixed(2);

  if (previewModeBadge) {
    previewModeBadge.className = `px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider badge-${mode}`;
    previewModeBadge.textContent = `${mode.toUpperCase()} MODE EVALUATED`;
  }

  if (previewEmissions) {
    previewEmissions.textContent = `${co2Grams} gCO2 / 10-min build`;
  }

  if (previewPolicyTitle && previewPolicyDesc) {
    if (mode === 'green') {
      previewPolicyTitle.textContent = 'All CI/CD Pipelines Execute Immediately';
      previewPolicyDesc.textContent = 'Grid carbon is exceptionally clean. Full concurrency enabled for unit tests, Docker packaging, and cloud deployment matrices.';
    } else if (mode === 'amber') {
      previewPolicyTitle.textContent = 'Constrained Dispatch - Priority Jobs Only';
      previewPolicyDesc.textContent = 'Emissions are moderate. Fast PR checks and essential linters run immediately; resource-intensive batch jobs queued or throttled.';
    } else {
      previewPolicyTitle.textContent = 'PIPELINES FROZEN - Non-Urgent Jobs Deferred';
      previewPolicyDesc.textContent = 'Fossil fuels currently dominate the grid. All non-urgent CI jobs are deferred to queue until wind/solar generation surges.';
    }
  }

  if (previewCard) {
    previewCard.style.borderColor = mode === 'green' ? '#10b981' : mode === 'amber' ? '#f59e0b' : '#ef4444';
  }
}

async function applySimulation(intensity) {
  try {
    const res = await fetch('/api/v1/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled: true, intensity: intensity })
    });
    const data = await res.json();
    if (data.status === 'success') {
      showToast(`Simulation Override Active: ${intensity} gCO2/kWh`, 'warning');
      const masterToggle = document.getElementById('sim-master-toggle');
      if (masterToggle) masterToggle.checked = true;
      fetchStatus();
    }
  } catch (err) {
    showToast('Failed to apply simulation override', 'error');
  }
}

async function disableSimulation() {
  try {
    const res = await fetch('/api/v1/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled: false })
    });
    const data = await res.json();
    if (data.status === 'success') {
      showToast('Simulation disabled. Reconnected to live UK National Grid.', 'success');
      const masterToggle = document.getElementById('sim-master-toggle');
      if (masterToggle) masterToggle.checked = false;
      fetchStatus();
    }
  } catch (err) {
    showToast('Failed to reset simulation', 'error');
  }
}

/* ==========================================================================
   Settings & Threshold Configuration
   ========================================================================== */
async function fetchSettings() {
  try {
    const res = await fetch('/api/v1/settings');
    const json = await res.json();
    if (json.status !== 'success') return;
    const s = json.settings;

    const inputGreen = document.getElementById('setting-thresh-green');
    const inputAmber = document.getElementById('setting-thresh-amber');
    const inputPower = document.getElementById('setting-power-kw');
    const inputWait = document.getElementById('setting-max-wait');
    const inputWebhookUrl = document.getElementById('setting-webhook-url');
    const inputWebhookToken = document.getElementById('setting-webhook-token');

    if (inputGreen && s.thresholds) inputGreen.value = s.thresholds.green || 100;
    if (inputAmber && s.thresholds) inputAmber.value = s.thresholds.amber || 250;
    if (inputPower) inputPower.value = s.assumed_power_kw || 0.05;
    if (inputWait) inputWait.value = s.max_wait_seconds || 120;
    if (inputWebhookUrl) inputWebhookUrl.value = s.custom_webhook_url || '';
    if (inputWebhookToken) inputWebhookToken.value = s.webhook_token || '';

    // Provider radio
    if (s.provider === 'custom_webhook') {
      const radioWebhook = document.getElementById('provider-webhook');
      if (radioWebhook) radioWebhook.checked = true;
      toggleWebhookFields(true);
    } else {
      const radioNeso = document.getElementById('provider-neso');
      if (radioNeso) radioNeso.checked = true;
      toggleWebhookFields(false);
    }
  } catch (err) {
    console.error('Error fetching settings:', err);
  }
}

function initSettingsForm() {
  const form = document.getElementById('settings-form');
  const btnResetDefaults = document.getElementById('btn-reset-defaults');
  const radioNeso = document.getElementById('provider-neso');
  const radioWebhook = document.getElementById('provider-webhook');

  if (radioNeso && radioWebhook) {
    radioNeso.addEventListener('change', () => toggleWebhookFields(false));
    radioWebhook.addEventListener('change', () => toggleWebhookFields(true));
  }

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      const greenVal = parseFloat(document.getElementById('setting-thresh-green').value);
      const amberVal = parseFloat(document.getElementById('setting-thresh-amber').value);
      const powerVal = parseFloat(document.getElementById('setting-power-kw').value);
      const waitVal = parseInt(document.getElementById('setting-max-wait').value);
      const provider = document.querySelector('input[name="provider_choice"]:checked')?.value || 'neso_uk';
      const webhookUrl = document.getElementById('setting-webhook-url')?.value || '';
      const webhookToken = document.getElementById('setting-webhook-token')?.value || '';

      const payload = {
        thresholds: { green: greenVal, amber: amberVal },
        assumed_power_kw: powerVal,
        max_wait_seconds: waitVal,
        provider: provider,
        custom_webhook_url: webhookUrl,
        webhook_token: webhookToken
      };

      try {
        const res = await fetch('/api/v1/settings', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const resData = await res.json();
        if (resData.status === 'success') {
          showToast('Configuration saved successfully!', 'success');
          fetchStatus();
        } else {
          showToast('Failed to save configuration', 'error');
        }
      } catch (err) {
        showToast('Error persisting settings', 'error');
      }
    });
  }

  if (btnResetDefaults) {
    btnResetDefaults.addEventListener('click', async () => {
      if (confirm('Reset all carbon thresholds and test data to default values?')) {
        try {
          const res = await fetch('/api/v1/reset', { method: 'POST' });
          const resData = await res.json();
          if (resData.status === 'success') {
            showToast('All settings reset to defaults!', 'info');
            fetchSettings();
            fetchStatus();
            fetchJobs();
            fetchAnalytics();
          }
        } catch (err) {
          showToast('Reset failed', 'error');
        }
      }
    });
  }
}

function toggleWebhookFields(show) {
  const container = document.getElementById('webhook-credentials-container');
  if (container) {
    if (show) {
      container.classList.remove('hidden');
    } else {
      container.classList.add('hidden');
    }
  }
}

/* ==========================================================================
   New Job Modal
   ========================================================================== */
function initNewJobModal() {
  const modal = document.getElementById('modal-new-job');
  const btnClose = document.getElementById('btn-close-job-modal');
  const btnCancel = document.getElementById('btn-cancel-job-modal');
  const form = document.getElementById('form-new-job');
  const btnTriggerNew = document.getElementById('btn-trigger-new-job');

  if (btnTriggerNew) {
    btnTriggerNew.addEventListener('click', openJobModal);
  }

  if (btnClose) btnClose.addEventListener('click', closeJobModal);
  if (btnCancel) btnCancel.addEventListener('click', closeJobModal);

  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const jobName = document.getElementById('input-job-name').value.trim();
      const branch = document.getElementById('input-job-branch').value.trim() || 'main';
      const force = document.getElementById('input-job-force')?.checked || false;

      closeJobModal();
      switchView('dashboard');
      triggerJobDispatch(jobName, branch, force);
    });
  }

  initJobFilters();
}

function openJobModal() {
  const modal = document.getElementById('modal-new-job');
  if (modal) modal.classList.remove('hidden');
}

function closeJobModal() {
  const modal = document.getElementById('modal-new-job');
  if (modal) modal.classList.add('hidden');
}

/* ==========================================================================
   Toast Notification System
   ========================================================================== */
function showToast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;

  let icon = 'fa-circle-check text-emerald-400';
  if (type === 'info') icon = 'fa-circle-info text-sky-400';
  else if (type === 'warning') icon = 'fa-triangle-exclamation text-amber-400';
  else if (type === 'error') icon = 'fa-circle-xmark text-red-400';

  toast.innerHTML = `
    <i class="fa-solid ${icon} text-lg"></i>
    <div class="flex-1 text-sm font-medium text-slate-100">${escapeHtml(message)}</div>
    <button class="text-slate-500 hover:text-slate-300 ml-2" onclick="this.parentElement.remove()">
      <i class="fa-solid fa-xmark"></i>
    </button>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4200);
}

/* ==========================================================================
   Utilities
   ========================================================================== */
function formatTimeAgo(date) {
  const now = new Date();
  const diffSec = Math.floor((now - date) / 1000);
  if (diffSec < 60) return `${diffSec}s ago`;
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHrs = Math.floor(diffMin / 60);
  if (diffHrs < 24) return `${diffHrs}h ago`;
  return `${Math.floor(diffHrs / 24)}d ago`;
}

function escapeHtml(str) {
  if (!str) return '';
  return str.toString()
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

