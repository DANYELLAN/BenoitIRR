const api = '/api';

async function apiCall(path, opts = {}) {
  const response = await fetch(`${api}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail);
  }
  return response.json();
}

document.getElementById('login-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = new FormData(event.target);
  const payload = {
    adp_number: form.get('adp_number'),
    workstation: form.get('workstation'),
  };
  try {
    const data = await apiCall('/login', { method: 'POST', body: JSON.stringify(payload) });
    document.getElementById('login-output').textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    document.getElementById('login-output').textContent = `Error: ${err.message}`;
  }
});

document.getElementById('inspection-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = new FormData(event.target);
  const key = String(form.get('measurement_key'));
  const value = Number(form.get('measurement_value'));
  const payload = {
    adp_number: String(form.get('adp_number')),
    inspector_name: String(form.get('inspector_name')),
    operator_name: String(form.get('operator_name')),
    workstation: String(form.get('workstation')),
    work_order: String(form.get('work_order')),
    connection: String(form.get('connection')),
    pipe_number: Number(form.get('pipe_number')),
    fai_number: String(form.get('fai_number')),
    drawing_number: String(form.get('drawing_number')),
    measurements: { [key]: value },
    manager_approved: String(form.get('manager_approved')) === 'true',
    tier_code: String(form.get('tier_code') || '') || null,
    nonconformance: String(form.get('nonconformance') || '') || null,
    immediate_containment: String(form.get('immediate_containment') || '') || null,
  };

  try {
    const data = await apiCall('/inspections', { method: 'POST', body: JSON.stringify(payload) });
    document.getElementById('inspection-output').textContent = JSON.stringify(data, null, 2);
    await refreshNcrs();
  } catch (err) {
    document.getElementById('inspection-output').textContent = `Error: ${err.message}`;
  }
});

async function markSynced(id) {
  await apiCall(`/ncrs/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ sharepoint_sync_status: 'SYNCED' }),
  });
  await refreshNcrs();
}

async function refreshNcrs() {
  const rows = await apiCall('/ncrs');
  const table = document.getElementById('ncr-table');
  table.innerHTML = '';
  rows.forEach((row) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${row.id}</td>
      <td>${row.inspection_id}</td>
      <td>${row.tier_code}</td>
      <td>${row.status}</td>
      <td>${row.sharepoint_sync_status}</td>
      <td>${row.sharepoint_sync_status === 'PENDING' ? `<button data-id="${row.id}">Mark Synced</button>` : 'Synced'}</td>
    `;
    const button = tr.querySelector('button');
    if (button) {
      button.addEventListener('click', () => markSynced(button.dataset.id));
    }
    table.appendChild(tr);
  });
}

document.getElementById('refresh-ncrs').addEventListener('click', refreshNcrs);
refreshNcrs().catch(() => {});
