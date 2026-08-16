/**
 * Needs Management, Goal Planner, Affordability, and Smart Insights
 */

let planningCache = {
  needs: [],
  goals: [],
  summary: null,
  selectedGoalId: null,
};

function formatRupee(amount) {
  return '₹' + parseFloat(amount || 0).toFixed(2);
}

async function apiFetch(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || `HTTP ${response.status}`);
  }
  return data;
}

async function loadPlanningDashboard() {
  try {
    const [needsRes, goalsRes, summaryRes, insightsRes] = await Promise.all([
      apiFetch('/api/needs'),
      apiFetch('/api/personal-goals?status=active'),
      apiFetch('/api/savings/summary'),
      apiFetch('/api/insights'),
    ]);

    planningCache.needs = needsRes.needs || [];
    planningCache.goals = goalsRes.goals || [];
    planningCache.summary = summaryRes.summary || null;

    renderNeeds(planningCache.needs, planningCache.summary);
    renderPersonalGoals(planningCache.goals);
    renderGoalProgressWidget(planningCache.goals);
    renderInsights(insightsRes.insights || []);
    renderFreeSavings(planningCache.summary);

    if (needsRes.show_setup) {
      await showNeedsSetupOverlay();
    }
  } catch (e) {
    console.error('[PLANNING] Load error:', e.message);
  }
}

async function showNeedsSetupOverlay() {
  const overlay = document.getElementById('needsSetupOverlay');
  const list = document.getElementById('needsSetupList');

  if (!overlay || !list) return;

  try {
    const data = await apiFetch('/api/needs/templates');

    list.innerHTML = (data.templates || []).map(t => `
      <label
        class="
          group flex min-h-[56px] w-full cursor-pointer
          items-center justify-start gap-3
          rounded-xl border border-slate-700
          bg-slate-800/50 px-4 py-3
          transition-all duration-200
          hover:border-purple-500/60
          hover:bg-slate-800
        "
      >

        <input
          type="checkbox"
          class="
            need-setup-check
            h-4 w-4 shrink-0
            cursor-pointer
            rounded
            border-slate-600
            bg-slate-700
            text-purple-600
            focus:ring-2
            focus:ring-purple-500
          "
          value="${t.name}"
          checked
        >

        <span
          class="
            truncate
            text-sm font-medium
            text-slate-200
            transition-colors
            group-hover:text-white
          "
        >
          ${t.name}
        </span>

      </label>
    `).join('');

    // IMPORTANT: flex is required for true center alignment
    overlay.classList.remove('hidden');
    overlay.classList.add('flex');

  } catch (e) {
    console.error('[NEEDS SETUP]', e.message);
  }
}

async function submitNeedsSetup() {
  const checks = document.querySelectorAll('.need-setup-check:checked');
  const names = Array.from(checks).map(c => c.value);
  if (!names.length) {
    showAlert('Select at least one need', 'warning');
    return;
  }
  try {
    const data = await apiFetch('/api/needs/setup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ names }),
    });
    if (data.success) {
      showAlert(data.message || 'Needs saved', 'success');
      document.getElementById('needsSetupOverlay').classList.add('hidden');
      await loadPlanningDashboard();
    } else {
      showAlert(data.error || 'Setup failed', 'danger');
    }
  } catch (e) {
    showAlert('Setup error: ' + e.message, 'danger');
  }
}

async function skipNeedsSetup() {
  try {
    await apiFetch('/api/needs/setup/skip', { method: 'POST' });
    document.getElementById('needsSetupOverlay')?.classList.add('hidden');
  } catch (e) {
    showAlert('Could not skip setup: ' + e.message, 'danger');
  }
}

function renderNeeds(needs, summary) {
  const list = document.getElementById('needsList');
  const empty = document.getElementById('needsEmpty');
  const totalLabel = document.getElementById('needs-total-label');
  if (!list) return;

  if (totalLabel && summary) {
    totalLabel.textContent = 'Total: ' + formatRupee(summary.needs_total);
  }

  if (!needs.length) {
    list.innerHTML = '';
    empty?.classList.remove('hidden');
    return;
  }
  empty?.classList.add('hidden');

  list.innerHTML = needs.map(n => `
    <div class="flex items-center justify-between p-2 border border-slate-700 rounded-lg ${n.is_active ? '' : 'opacity-50'}">
      <div>
        <p class="text-sm font-medium text-slate-100 m-0">${n.name}</p>
        <p class="text-xs text-slate-500 m-0">${formatRupee(n.default_amount)}/mo</p>
      </div>
      <div class="flex items-center gap-1">
        <button type="button" onclick="toggleNeed(${n.id}, ${!n.is_active})" class="px-2 py-1 text-xs rounded bg-slate-700 text-slate-300 hover:bg-slate-600" title="Toggle">${n.is_active ? 'On' : 'Off'}</button>
        <button type="button" onclick="openEditNeed(${n.id})" class="px-2 py-1 text-xs rounded bg-blue-600/80 text-white hover:bg-blue-600">Edit</button>
        <button type="button" onclick="deleteNeed(${n.id})" class="px-2 py-1 text-xs rounded bg-red-600/80 text-white hover:bg-red-600">×</button>
      </div>
    </div>
  `).join('');
}

async function addNeed() {
  const name = document.getElementById('needName')?.value?.trim();
  const amount = document.getElementById('needAmount')?.value;
  if (!name) {
    showAlert('Enter a need name', 'warning');
    return;
  }
  const formData = new FormData();
  formData.append('name', name);
  formData.append('default_amount', amount || '0');
  try {
    const data = await apiFetch('/api/needs', { method: 'POST', body: formData });
    if (data.success) {
      showAlert(data.message, 'success');
      document.getElementById('needName').value = '';
      document.getElementById('needAmount').value = '';
      await loadPlanningDashboard();
    } else {
      showAlert(data.error, 'danger');
    }
  } catch (e) {
    showAlert('Error: ' + e.message, 'danger');
  }
}

function openEditNeed(id) {
  const need = planningCache.needs.find(n => n.id === id);
  if (!need) return;
  document.getElementById('editNeedId').value = id;
  document.getElementById('editNeedName').value = need.name;
  document.getElementById('editNeedAmount').value = need.default_amount;
  document.getElementById('editNeedOverlay').classList.remove('hidden');
}

function closeEditNeed() {
  document.getElementById('editNeedOverlay')?.classList.add('hidden');
}

async function saveEditNeed() {
  const id = document.getElementById('editNeedId').value;
  const name = document.getElementById('editNeedName').value.trim();
  const amount = document.getElementById('editNeedAmount').value;
  try {
    const data = await apiFetch(`/api/needs/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, default_amount: amount }),
    });
    if (data.success) {
      showAlert(data.message, 'success');
      closeEditNeed();
      await loadPlanningDashboard();
    } else {
      showAlert(data.error, 'danger');
    }
  } catch (e) {
    showAlert('Error: ' + e.message, 'danger');
  }
}

async function toggleNeed(id, isActive) {
  try {
    const data = await apiFetch(`/api/needs/${id}/toggle`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_active: isActive }),
    });
    if (data.success) await loadPlanningDashboard();
    else showAlert(data.error, 'danger');
  } catch (e) {
    showAlert('Error: ' + e.message, 'danger');
  }
}

async function deleteNeed(id) {
  if (!confirm('Delete this need?')) return;
  try {
    const data = await apiFetch(`/api/needs/${id}`, { method: 'DELETE' });
    if (data.success) {
      showAlert(data.message, 'success');
      await loadPlanningDashboard();
    } else showAlert(data.error, 'danger');
  } catch (e) {
    showAlert('Error: ' + e.message, 'danger');
  }
}

function renderPersonalGoals(goals) {
  const list = document.getElementById('personalGoalsList');
  const empty = document.getElementById('personalGoalsEmpty');
  if (!list) return;

  if (!goals.length) {
    list.innerHTML = '';
    empty?.classList.remove('hidden');
    return;
  }
  empty?.classList.add('hidden');

  list.innerHTML = goals.map(g => {
    const p = g.projection || {};
    const progress = p.progress_percent || 0;
    return `
      <div class="p-3 border border-slate-700 rounded-lg hover:bg-slate-800/50 cursor-pointer" onclick="selectGoal(${g.id})">
        <div class="flex justify-between items-start gap-2">
          <div>
            <p class="text-sm font-medium text-slate-100 m-0">${g.goal_name}</p>
            <p class="text-xs text-slate-500 m-0">${formatRupee(g.saved_amount)} / ${formatRupee(g.target_amount)} · Target ${g.target_date}</p>
          </div>
          <div class="flex gap-1 flex-shrink-0">
            <button type="button" onclick="event.stopPropagation(); archiveGoal(${g.id})" class="px-2 py-1 text-xs rounded bg-slate-700 text-slate-300">Archive</button>
            <button type="button" onclick="event.stopPropagation(); deletePersonalGoal(${g.id})" class="px-2 py-1 text-xs rounded bg-red-600/80 text-white">×</button>
          </div>
        </div>
        <div class="h-1 bg-slate-800 rounded overflow-hidden mt-2">
          <div class="progress-bar h-full bg-gradient-to-r from-primary to-accent" style="width: ${Math.min(progress, 100)}%"></div>
        </div>
        <small class="text-xs text-slate-400">${progress}% · ${p.goal_status || 'active'}</small>
      </div>
    `;
  }).join('');
}

function selectGoal(id) {
  planningCache.selectedGoalId = id;
  renderGoalProgressWidget(planningCache.goals);
}

function renderGoalProgressWidget(goals) {
  const widget = document.getElementById('goalProgressWidget');
  if (!widget) return;

  let goal = goals.find(g => g.id === planningCache.selectedGoalId);
  if (!goal && goals.length) {
    goal = goals[0];
    planningCache.selectedGoalId = goal.id;
  }
  if (!goal) {
    widget.innerHTML = '<p class="text-sm text-slate-500 m-0">Select or create a goal to see progress.</p>';
    return;
  }

  const p = goal.projection || {};
  widget.innerHTML = `
    <p class="text-sm font-semibold text-slate-100 m-0 mb-1">${goal.goal_name}</p>
    <div class="h-1 bg-slate-800 rounded overflow-hidden mb-2">
      <div class="progress-bar h-full bg-gradient-to-r from-primary to-accent" style="width: ${Math.min(p.progress_percent || 0, 100)}%"></div>
    </div>
    <p class="text-xs text-slate-400 m-0">${p.progress_percent || 0}% complete · Remaining ${formatRupee(p.remaining_amount)}</p>
    <p class="text-xs text-slate-400 mt-1 m-0">${p.months_required != null ? 'Est. ' + p.months_required + ' months' : 'Increase free savings to estimate'}</p>
    <p class="text-xs mt-1 m-0 ${p.goal_achievable ? 'text-emerald-400' : 'text-amber-400'}">${p.goal_achievable ? 'Achievable before target date' : (p.goal_status === 'completed' ? 'Goal completed!' : 'May need adjustment')}</p>
  `;
}

async function createPersonalGoal() {
  const payload = {
    goal_name: document.getElementById('pgGoalName')?.value?.trim(),
    target_amount: document.getElementById('pgTargetAmount')?.value,
    saved_amount: document.getElementById('pgSavedAmount')?.value || 0,
    target_date: document.getElementById('pgTargetDate')?.value,
    priority: document.getElementById('pgPriority')?.value || 3,
  };
  if (!payload.goal_name || !payload.target_amount || !payload.target_date) {
    showAlert('Fill goal name, target amount, and target date', 'warning');
    return;
  }
  try {
    const data = await apiFetch('/api/personal-goals', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (data.success) {
      showAlert(data.message, 'success');
      document.getElementById('pgGoalName').value = '';
      document.getElementById('pgTargetAmount').value = '';
      document.getElementById('pgSavedAmount').value = '0';
      document.getElementById('pgTargetDate').value = '';
      if (data.goal) planningCache.selectedGoalId = data.goal.id;
      await loadPlanningDashboard();
    } else showAlert(data.error, 'danger');
  } catch (e) {
    showAlert('Error: ' + e.message, 'danger');
  }
}

async function archiveGoal(id) {
  try {
    const data = await apiFetch(`/api/personal-goals/${id}/archive`, { method: 'PATCH' });
    if (data.success) {
      showAlert(data.message, 'success');
      await loadPlanningDashboard();
    } else showAlert(data.error, 'danger');
  } catch (e) {
    showAlert('Error: ' + e.message, 'danger');
  }
}

async function deletePersonalGoal(id) {
  if (!confirm('Delete this goal permanently?')) return;
  try {
    const data = await apiFetch(`/api/personal-goals/${id}`, { method: 'DELETE' });
    if (data.success) {
      showAlert(data.message, 'success');
      await loadPlanningDashboard();
    } else showAlert(data.error, 'danger');
  } catch (e) {
    showAlert('Error: ' + e.message, 'danger');
  }
}

async function calculateAffordability() {
  const product_name = document.getElementById('affordProductName')?.value?.trim();
  const product_price = document.getElementById('affordProductPrice')?.value;
  if (!product_price) {
    showAlert('Enter a product price', 'warning');
    return;
  }
  try {
    const data = await apiFetch('/api/affordability/calculate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ product_name, product_price }),
    });
    if (data.success && data.affordability) {
      const a = data.affordability;
      const result = document.getElementById('affordResult');
      result.classList.remove('hidden');
      document.getElementById('affordMessage').textContent = a.affordability_message;
      document.getElementById('affordMonths').textContent = a.months_required != null
        ? `Months required: ${a.months_required}`
        : 'Not affordable at current free savings rate';
      document.getElementById('affordImpact').textContent = a.savings_impact;
    } else showAlert(data.error || 'Calculation failed', 'danger');
  } catch (e) {
    showAlert('Error: ' + e.message, 'danger');
  }
}

function renderInsights(insights) {
  const list = document.getElementById('insightsList');
  if (!list) return;
  if (!insights.length) {
    list.innerHTML = '<p class="text-sm text-slate-500 m-0">Add income and needs to see insights.</p>';
    return;
  }
  const colors = {
    info: 'border-blue-500',
    success: 'border-emerald-500',
    warning: 'border-amber-500',
    danger: 'border-red-500',
  };
  list.innerHTML = insights.map(i => `
    <div class="border-l-4 ${colors[i.severity] || 'border-blue-500'} bg-slate-800/40 p-3 rounded">
      <p class="text-sm text-slate-200 m-0">${i.message}</p>
    </div>
  `).join('');
}

function renderFreeSavings(summary) {
  if (!summary) return;
  const el = document.getElementById('freeSavingsAmount');
  const breakdown = document.getElementById('savingsBreakdown');
  if (el) el.textContent = formatRupee(summary.monthly_free_savings);
  if (breakdown) {
    breakdown.textContent = `${formatRupee(summary.monthly_income)} income − ${formatRupee(summary.needs_total)} needs`;
  }
}

document.addEventListener('DOMContentLoaded', function() {
  const pgDate = document.getElementById('pgTargetDate');
  if (pgDate && !pgDate.value) {
    const d = new Date();
    d.setMonth(d.getMonth() + 6);
    pgDate.value = d.toISOString().split('T')[0];
  }
  if (document.getElementById('needsList')) {
    loadPlanningDashboard();
  }
});
