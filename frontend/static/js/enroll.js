document.addEventListener('DOMContentLoaded', () => {
  const search = document.getElementById('search');
  const table = document.getElementById('studentTable');
  if (search && table) {
    search.addEventListener('keyup', function () {
      const q = this.value.toLowerCase();
      table.querySelectorAll('tbody tr').forEach((row) => {
        row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
      });
    });
  }

  const modalEl = document.getElementById('enrollModal');
  if (modalEl) {
    modalEl.addEventListener('hidden.bs.modal', () => {
      if (window.currentStream) {
        window.currentStream.getTracks().forEach((t) => t.stop());
      }
    });
  }

  const captureBtn = document.getElementById('captureBtn');
  if (captureBtn) {
    captureBtn.onclick = async () => {
      const video = document.getElementById('enrollVideo');
      const canvas = document.getElementById('snapCanvas');
      if (!video || !canvas) return;
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      canvas.getContext('2d').drawImage(video, 0, 0);
      const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
      const msg = document.getElementById('enrollMsg');
      msg.textContent = 'Processing face...';

      const res = await fetch('/enroll_capture', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ student_id: window.currentStudentId, image: dataUrl })
      });
      const out = await res.json();

      if (out.ok) {
        msg.innerHTML = '<span class="text-success">DONE! ' + out.message + '</span>';
        setTimeout(() => location.reload(), 1200);
      } else {
        msg.innerHTML = '<span class="text-danger">' + out.error + '</span>';
      }
    };
  }
});

window.currentStream = null;
window.currentStudentId = null;

async function startCamera(deviceId) {
  if (window.currentStream) {
    window.currentStream.getTracks().forEach((t) => t.stop());
  }
  window.currentStream = await navigator.mediaDevices.getUserMedia({
    video: deviceId ? { deviceId: { exact: deviceId } } : true
  });
  document.getElementById('enrollVideo').srcObject = window.currentStream;
}

async function openEnroll(id, name, roll) {
  window.currentStudentId = id;
  document.getElementById('enrollStudentLabel').textContent = name + ' (' + roll + ')';
  document.getElementById('enrollMsg').textContent = 'Starting camera...';
  new bootstrap.Modal(document.getElementById('enrollModal')).show();
  try {
    await startCamera(null);
    const devices = await navigator.mediaDevices.enumerateDevices();
    const cams = devices.filter((d) => d.kind === 'videoinput');
    const sel = document.getElementById('cameraSelect');
    sel.innerHTML = '';
    cams.forEach((c, i) => {
      const opt = document.createElement('option');
      opt.value = c.deviceId;
      opt.textContent = c.label || ('Camera ' + (i + 1));
      sel.appendChild(opt);
    });
    sel.onchange = () => startCamera(sel.value);
    document.getElementById('enrollMsg').textContent = 'Look straight at the camera, good light on your face.';
  } catch (e) {
    document.getElementById('enrollMsg').innerHTML = '<span class="text-danger">Camera permission denied.</span>';
  }
}
