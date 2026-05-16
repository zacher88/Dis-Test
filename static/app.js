const form = document.querySelector('#watch-form');
const formMessage = document.querySelector('#form-message');
const watchlist = document.querySelector('#watchlist');
const opportunities = document.querySelector('#opportunities');

const typeLabels = {
  dining: 'Dining',
  lightning_lane: 'Lightning Lane',
  dvc: 'DVC',
};

function formToPayload(formElement) {
  return Object.fromEntries(new FormData(formElement).entries());
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || 'Request failed');
  }
  return payload;
}

function renderEmpty(target, message) {
  target.innerHTML = `<li class="card muted">${message}</li>`;
}

async function loadWatchlist() {
  const watches = await api('/api/watchlist');
  if (!watches.length) {
    renderEmpty(watchlist, 'No alerts yet. Add one above to get started.');
    return;
  }
  watchlist.innerHTML = watches.map((watch) => `
    <li class="card">
      <strong>${watch.item_name}</strong>
      <span>${typeLabels[watch.watch_type]} · ${watch.destination}</span><br />
      <span class="muted">${watch.start_date} to ${watch.end_date} · party of ${watch.party_size}</span>
    </li>
  `).join('');
}

async function loadOpportunities() {
  const found = await api('/api/opportunities');
  if (!found.length) {
    renderEmpty(opportunities, 'No openings stored yet. Try “Check now” with mock matches like Ohana, TRON, or BoardWalk.');
    return;
  }
  opportunities.innerHTML = found.map((item) => `
    <li class="card">
      <strong>${item.item_name}</strong>
      <span>${item.available_date} · ${item.available_time}</span><br />
      <span class="muted">${item.notes}</span><br />
      <a href="${item.booking_url}" target="_blank" rel="noreferrer">Open booking page</a>
    </li>
  `).join('');
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  formMessage.textContent = 'Saving alert…';
  try {
    await api('/api/watchlist', {
      method: 'POST',
      body: JSON.stringify(formToPayload(form)),
    });
    form.reset();
    form.destination.value = 'Walt Disney World';
    form.party_size.value = '2';
    formMessage.textContent = 'Alert saved.';
    await loadWatchlist();
  } catch (error) {
    formMessage.textContent = error.message;
  }
});

document.querySelector('#refresh-watchlist').addEventListener('click', loadWatchlist);
document.querySelector('#check-now').addEventListener('click', async () => {
  await api('/api/check', { method: 'POST', body: '{}' });
  await loadOpportunities();
});

await loadWatchlist();
await loadOpportunities();
