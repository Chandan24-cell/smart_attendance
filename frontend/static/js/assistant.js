document.addEventListener('DOMContentLoaded', () => {
  const panel = document.getElementById('copilotPanel');
  const body = document.getElementById('copilotBody');
  const input = document.getElementById('copilotInput');
  const send = document.getElementById('copilotSend');
  if (!panel || !body || !input || !send) return;

  const history = JSON.parse(localStorage.getItem('copilot-history') || '[]');
  const renderHistory = () => {
    body.innerHTML = '';
    history.slice(-6).forEach((item) => {
      const p = document.createElement('p');
      p.className = 'mb-2 small';
      p.innerHTML = `<strong>${item.type}</strong><br>${item.text}`;
      body.appendChild(p);
    });
  };
  renderHistory();

  const addHistory = (text, type = 'assistant') => {
    history.push({ type, text });
    if (history.length > 10) history.shift();
    localStorage.setItem('copilot-history', JSON.stringify(history));
    renderHistory();
  };

  send.addEventListener('click', async () => {
    const q = input.value.trim();
    if (!q) return;
    addHistory(q, 'you');
    input.value = '';
    const res = await fetch(`/api/ask?q=${encodeURIComponent(q)}`);
    const data = await res.json();
    let html = `<div class="text-muted mb-2">${data.answer}</div>`;
    if (Array.isArray(data.table) && data.table.length) {
      html += '<table class="table table-sm mb-2"><tbody>';
      data.table.forEach((row) => {
        if (row.label) html += `<tr><td>${row.label}</td><td>${row.value}</td></tr>`;
        else html += `<tr><td>${row.roll || row.period || '-'}</td><td>${row.name || row.subject || row.pct || row.status || '-'}</td></tr>`;
      });
      html += '</tbody></table>';
    }
    addHistory(html, 'assistant');
  });

  window.speakToast = (e) => {
    const phrase = `${e.name || 'Student'} marked ${e.type === 'PRESENT' ? 'present' : 'late'}`;
    try {
      const utter = new SpeechSynthesisUtterance(phrase);
      utter.rate = 1.05;
      speechSynthesis.cancel();
      speechSynthesis.speak(utter);
    } catch (err) {}
  };

  const audioContext = window.AudioContext || window.webkitAudioContext;
  if (audioContext) {
    window.playBeep = (type = 'success') => {
      const ctx = new audioContext();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = type === 'error' ? 'square' : 'sine';
      osc.frequency.value = type === 'error' ? 220 : 440;
      gain.gain.value = 0.08;
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.12);
    };
  }
});
