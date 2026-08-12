let lastEventId = 0;
let ready = false;

async function pollEvents() {
  try {
    const res = await fetch('/api/events?since=' + lastEventId);
    const events = await res.json();
    events.forEach((e) => {
      lastEventId = Math.max(lastEventId, e.id);
      if (!ready) return;
      showToast(e);
    });
    ready = true;
  } catch (err) {}
}

function showToast(e) {
  const colors = { PRESENT: 'success', LATE_NOT_ACCEPTED: 'warning', UNKNOWN_FACE: 'secondary', UNCLEAR_FACE: 'info' };
  const msgs = {
    PRESENT: `${e.name} (${e.roll}) marked PRESENT`,
    LATE_NOT_ACCEPTED: `${e.name} (${e.roll}) late — not accepted`,
    UNKNOWN_FACE: 'Not enrolled / unknown face detected',
    UNCLEAR_FACE: 'Unclear face detected'
  };
  const zone = document.getElementById('toastZone');
  if (!zone) return;
  const div = document.createElement('div');
  div.className = `alert alert-${colors[e.type] || 'dark'} py-2 small shadow`;
  div.innerHTML = `<button type="button" class="btn-close float-end" onclick="this.parentElement.remove()"></button><strong>${e.time}</strong><br>${msgs[e.type] || e.type}`;
  zone.appendChild(div);
  setTimeout(() => div.remove(), 8000);
  if (typeof window.speakToast === 'function' && ['PRESENT','LATE_NOT_ACCEPTED'].includes(e.type)) {
    window.speakToast(e);
  }
}

pollEvents();
setInterval(pollEvents, 4000);
