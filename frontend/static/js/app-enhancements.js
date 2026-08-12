document.addEventListener('DOMContentLoaded', () => {
  const body = document.body;
  if (!body) return;

  const shell = document.querySelector('.page-shell');
  if (!shell) {
    const wrapper = document.createElement('div');
    wrapper.className = 'page-shell';
    while (document.body.firstChild) {
      wrapper.appendChild(document.body.firstChild);
    }
    document.body.appendChild(wrapper);
  }

  body.classList.add('theme-body');
  body.setAttribute('data-density', localStorage.getItem('attendance-density') || 'comfortable');
  body.setAttribute('data-theme', localStorage.getItem('attendance-theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));

  const navbar = document.querySelector('.navbar');
  if (navbar) {
    const navGroup = navbar.querySelector('.navbar-nav') || navbar;
    if (!document.getElementById('themeToggle')) {
      const themeBtn = document.createElement('button');
      themeBtn.id = 'themeToggle';
      themeBtn.className = 'btn btn-sm btn-outline-light theme-toggle';
      themeBtn.type = 'button';
      themeBtn.innerHTML = '<i class="bi bi-sun-fill"></i> <span>Theme</span>';
      themeBtn.addEventListener('click', () => {
        const next = body.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        body.setAttribute('data-theme', next);
        localStorage.setItem('attendance-theme', next);
        themeBtn.innerHTML = next === 'dark' ? '<i class="bi bi-moon-fill"></i> <span>Dark</span>' : '<i class="bi bi-sun-fill"></i> <span>Light</span>';
      });
      navGroup.appendChild(themeBtn);
    }

    if (!document.getElementById('densityToggle')) {
      const densityBtn = document.createElement('button');
      densityBtn.id = 'densityToggle';
      densityBtn.className = 'btn btn-sm btn-outline-light theme-toggle';
      densityBtn.type = 'button';
      densityBtn.innerHTML = '<i class="bi bi-arrows-collapse"></i> <span>Compact</span>';
      densityBtn.addEventListener('click', () => {
        const next = body.getAttribute('data-density') === 'compact' ? 'comfortable' : 'compact';
        body.setAttribute('data-density', next);
        localStorage.setItem('attendance-density', next);
        densityBtn.innerHTML = next === 'compact' ? '<i class="bi bi-arrows-expand"></i> <span>Compact</span>' : '<i class="bi bi-arrows-collapse"></i> <span>Comfort</span>';
      });
      navGroup.appendChild(densityBtn);
    }

    if (!document.getElementById('voiceToggle')) {
      const voiceBtn = document.createElement('button');
      voiceBtn.id = 'voiceToggle';
      voiceBtn.className = 'btn btn-sm btn-outline-light theme-toggle';
      voiceBtn.type = 'button';
      voiceBtn.innerHTML = '<i class="bi bi-mic"></i> <span>Voice</span>';
      voiceBtn.addEventListener('click', () => {
        const enabled = body.getAttribute('data-voice') === 'on';
        const next = enabled ? 'off' : 'on';
        body.setAttribute('data-voice', next);
        localStorage.setItem('attendance-voice', next);
        voiceBtn.innerHTML = next === 'on' ? '<i class="bi bi-mic-fill"></i> <span>Voice On</span>' : '<i class="bi bi-mic"></i> <span>Voice</span>';
        if (next === 'on') {
          window.dispatchVoicePrompt('voice enabled');
        }
      });
      navGroup.appendChild(voiceBtn);
    }
  }

  if (!document.getElementById('copilotPanel')) {
    const panel = document.createElement('div');
    panel.id = 'copilotPanel';
    panel.className = 'copilot-panel';
    panel.innerHTML = '<div class="copilot-header">Attendance Copilot</div><div id="copilotBody" class="copilot-body"></div><div class="copilot-input-row"><input id="copilotInput" class="form-control form-control-sm" placeholder="Ask about today..."><button id="copilotSend" class="btn btn-sm btn-primary">Ask</button></div>';
    document.body.appendChild(panel);
  }

  if (document.getElementById('dashboardGreeting')) {
    const hour = new Date().getHours();
    let label = 'Good evening';
    if (hour < 12) label = 'Good morning';
    if (hour >= 17) label = 'Good evening';
    if (hour >= 12 && hour < 17) label = 'Good afternoon';
    document.getElementById('dashboardGreeting').textContent = label + ' — attendance is ready.';
  }

  const summaryLine = document.getElementById('summaryLine');
  if (summaryLine) {
    summaryLine.classList.add('text-muted');
  }

  const couldBeDense = body.getAttribute('data-density') === 'compact';
  if (couldBeDense) {
    body.classList.add('density-compact');
  } else {
    body.classList.remove('density-compact');
  }

  const parallax = () => {
    const offset = window.scrollY * 0.08;
    const shell = document.querySelector('.page-shell');
    if (shell) shell.style.transform = `translate3d(0, ${offset}px, 0)`;
  };
  window.addEventListener('scroll', parallax, { passive: true });
  parallax();

  const panels = document.querySelectorAll('.card, .alert, .modal-content');
  panels.forEach((panel) => panel.classList.add('elevated'));

  const tableRows = document.querySelectorAll('.table tbody tr');
  tableRows.forEach((row, index) => {
    row.addEventListener('mouseenter', () => row.classList.add('hovered'));
    row.addEventListener('mouseleave', () => row.classList.remove('hovered'));
    if (index < 4) row.classList.add('row-spark');
  });

  const voiceSupport = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (voiceSupport && document.getElementById('voiceToggle')) {
    const recognition = new voiceSupport();
    recognition.lang = 'en-US';
    recognition.continuous = false;
    recognition.interimResults = false;
    let active = false;
    window.dispatchVoicePrompt = (message) => {
      const utter = new SpeechSynthesisUtterance(message);
      utter.rate = 1.02;
      speechSynthesis.cancel();
      speechSynthesis.speak(utter);
    };
    document.getElementById('voiceToggle').addEventListener('click', () => {
      const enabled = body.getAttribute('data-voice') === 'on';
      if (!enabled) return;
      if (active) {
        recognition.stop();
        active = false;
        return;
      }
      recognition.start();
      active = true;
    });
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript.toLowerCase();
      const commands = {
        'start session': () => { window.location.href = '/attendance'; },
        'stop session': () => { window.location.href = '/attendance'; },
        'show reports': () => { window.location.href = '/reports'; },
        'sync sheets': () => { window.location.href = '/datasource'; }
      };
      Object.entries(commands).forEach(([phrase, action]) => {
        if (transcript.includes(phrase)) action();
      });
      active = false;
    };
  }

  const statusBadges = document.querySelectorAll('.badge, .status-pill');
  statusBadges.forEach((badge) => {
    badge.addEventListener('click', () => badge.classList.add('morphed'));
  });
});
