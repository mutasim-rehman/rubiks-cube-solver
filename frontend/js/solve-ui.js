/**
 * Hexgate Solve UI — Webcam capture + API solve flow
 */
const FACE_ORDER = ['U', 'L', 'F', 'R', 'B', 'D'];
const FACE_NAMES = {
  U: 'Up (White)',
  L: 'Left (Green)',
  F: 'Front (Red)',
  R: 'Right (Blue)',
  B: 'Back (Orange)',
  D: 'Down (Yellow)',
};
const FACE_COLORS = {
  U: '#ffffff',
  L: '#22c55e',
  F: '#ef4444',
  R: '#2563eb',
  B: '#f97316',
  D: '#eab308',
};
const ROTATION_GUIDES = {
  U: "Rotate so RED face is at BOTTOM",
  L: "Rotate so WHITE face is at TOP",
  F: "Rotate so WHITE face is at TOP",
  R: "Rotate so WHITE face is at TOP",
  B: "Rotate so WHITE face is at TOP",
  D: "Rotate so RED face is at TOP",
};

export function initSolveUI() {
  const startEl = document.getElementById('solve-start');
  const startNetEl = document.getElementById('solve-start-net');
  const startBtn = document.getElementById('solve-start-btn');
  const captureEl = document.getElementById('solve-capture');
  const videoEl = document.getElementById('solve-video');
  const overlayEl = document.getElementById('solve-overlay');
  const instructionEl = document.getElementById('solve-instruction');
  const netDiagramEl = document.getElementById('solve-net-diagram');
  const rotationGuideEl = document.getElementById('solve-rotation-guide');
  const colorPreviewEl = document.getElementById('solve-color-preview');
  const facesEl = document.getElementById('solve-faces');
  const captureBtn = document.getElementById('solve-capture-btn');
  const submitBtn = document.getElementById('solve-submit-btn');
  const resetBtn = document.getElementById('solve-reset-btn');
  const resultEl = document.getElementById('solve-result');
  const solutionTextEl = document.getElementById('solve-solution-text');
  const stepsEl = document.getElementById('solve-steps');
  const againBtn = document.getElementById('solve-again-btn');
  const errorEl = document.getElementById('solve-error');
  const loadingEl = document.getElementById('solve-loading');

  if (!startEl || !captureEl) return;

  const CLASSIFY_COLORS = { R: '#ef4444', G: '#22c55e', B: '#2563eb', Y: '#eab308', O: '#f97316', W: '#ffffff' };
  let stream = null;
  let capturedFaces = {};
  let capturedFacesColors = {}; // 3x3 color arrays per face
  let livePreviewColors = null; // 3x3 from current frame
  let currentFaceIdx = 0;
  let previewInterval = null;

  function getAPIBase() {
    // In dev: '' uses Vite proxy. In prod: VITE_API_URL (e.g. https://your-api.onrender.com)
    return import.meta.env.VITE_API_URL || '';
  }

  function show(el, visible = true) {
    if (el) el.hidden = !visible;
  }

  function showError(msg) {
    if (errorEl) {
      errorEl.textContent = msg;
      errorEl.hidden = false;
    }
  }

  function hideError() {
    if (errorEl) errorEl.hidden = true;
  }

  function renderStartNet() {
    if (!startNetEl) return;
    const layout = [
      { code: 'U', row: 0, col: 1, label: '1. Up (White)' },
      { code: 'L', row: 1, col: 0, label: '2. Left (Green)' },
      { code: 'F', row: 1, col: 1, label: '3. Front (Red)' },
      { code: 'R', row: 1, col: 2, label: '4. Right (Blue)' },
      { code: 'B', row: 1, col: 3, label: '5. Back (Orange)' },
      { code: 'D', row: 2, col: 1, label: '6. Down (Yellow)' },
    ];
    startNetEl.innerHTML = layout.map(({ code, row, col, label }) => `
      <div class="solve-net-face" data-face="${code}" style="grid-row:${row + 1};grid-column:${col + 1};--face-color:${FACE_COLORS[code]}">
        <div class="solve-net-grid">
          ${Array(9).fill('<div class="solve-net-cell"></div>').join('')}
        </div>
        <span class="solve-net-num">${FACE_ORDER.indexOf(code) + 1}</span>
        <span class="solve-net-label">${label}</span>
      </div>
    `).join('');
  }

  function getFaceColorsForNet(code) {
    if (code in capturedFacesColors) return capturedFacesColors[code];
    if (code === FACE_ORDER[currentFaceIdx] && livePreviewColors) return livePreviewColors;
    return null;
  }

  function renderCubeNet() {
    if (!netDiagramEl) return;
    const currentCode = FACE_ORDER[currentFaceIdx];
    let nextCode = null;
    for (let i = 1; i <= 6; i++) {
      const idx = (currentFaceIdx + i) % 6;
      if (!(FACE_ORDER[idx] in capturedFaces)) {
        nextCode = FACE_ORDER[idx];
        break;
      }
    }
    const layout = [
      { code: 'U', row: 0, col: 1, label: 'Up (White)' },
      { code: 'L', row: 1, col: 0, label: 'Left (Green)' },
      { code: 'F', row: 1, col: 1, label: 'Front (Red)' },
      { code: 'R', row: 1, col: 2, label: 'Right (Blue)' },
      { code: 'B', row: 1, col: 3, label: 'Back (Orange)' },
      { code: 'D', row: 2, col: 1, label: 'Down (Yellow)' },
    ];
    netDiagramEl.innerHTML = layout.map(({ code, row, col, label }) => {
      const done = code in capturedFaces;
      const isCurrent = code === currentCode;
      const isNext = code === nextCode;
      const num = FACE_ORDER.indexOf(code) + 1;
      let cls = 'solve-net-face';
      if (isCurrent) cls += ' current';
      else if (isNext) cls += ' next';
      else if (done) cls += ' done';
      const faceColors = getFaceColorsForNet(code);
      const cellsHtml = faceColors
        ? faceColors.flat().map((c) =>
            `<div class="solve-net-cell" style="background:${CLASSIFY_COLORS[c] || '#333'}"></div>`
          ).join('')
        : Array(9).fill('<div class="solve-net-cell"></div>').join('');
      return `
        <div class="${cls}" data-face="${code}" style="grid-row:${row + 1};grid-column:${col + 1};--face-color:${FACE_COLORS[code]}">
          <div class="solve-net-grid">
            ${cellsHtml}
          </div>
          <span class="solve-net-num">${num}</span>
          <span class="solve-net-label">${label}</span>
        </div>
      `;
    }).join('');
    if (rotationGuideEl) {
      rotationGuideEl.textContent = ROTATION_GUIDES[currentCode];
    }
  }

  function renderFaces() {
    if (!facesEl) return;
    facesEl.innerHTML = FACE_ORDER.map((code) => {
      const done = code in capturedFaces;
      const isCurrent = FACE_ORDER[currentFaceIdx] === code;
      return `
        <div class="solve-face-item ${done ? 'done' : ''} ${isCurrent ? 'current' : ''}">
          <span class="face-code">${code}</span>
          <span class="face-name">${FACE_NAMES[code]}</span>
          ${done ? '<span class="face-check">✓</span>' : ''}
        </div>
      `;
    }).join('');
    const count = Object.keys(capturedFaces).length;
    if (submitBtn) {
      submitBtn.disabled = count < 6;
      submitBtn.textContent = `Solve (${count}/6)`;
    }
  }

  function getVideoFrameAsBase64() {
    if (!videoEl || videoEl.readyState < 2) return null;
    const canvas = document.createElement('canvas');
    const size = Math.min(videoEl.videoWidth, videoEl.videoHeight) * 0.4;
    const cx = videoEl.videoWidth / 2;
    const cy = videoEl.videoHeight / 2;
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(
      videoEl,
      cx - size / 2, cy - size / 2, size, size,
      0, 0, size, size
    );
    return canvas.toDataURL('image/jpeg', 0.9);
  }

  async function fetchLivePreview() {
    const img = getVideoFrameAsBase64();
    if (!img || !colorPreviewEl) return;
    try {
      const res = await fetch(`${getAPIBase()}/api/classify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: img }),
      });
      if (!res.ok) return;
      const data = await res.json();
      const face = data.face;
      if (face && Array.isArray(face)) {
        livePreviewColors = face;
        colorPreviewEl.innerHTML = face.flat().map((c) =>
          `<div class="solve-preview-cell" style="background:${CLASSIFY_COLORS[c] || '#333'}"></div>`
        ).join('');
        renderCubeNet();
      }
    } catch (_) {}
  }

  function startPreviewLoop() {
    stopPreviewLoop();
    fetchLivePreview();
    previewInterval = setInterval(fetchLivePreview, 400);
  }

  function stopPreviewLoop() {
    if (previewInterval) {
      clearInterval(previewInterval);
      previewInterval = null;
    }
    if (colorPreviewEl) colorPreviewEl.innerHTML = '<div class="solve-preview-placeholder">Start webcam to see live detection</div>';
  }

  async function startWebcam() {
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment', width: 640, height: 480 } });
      videoEl.srcObject = stream;
      show(startEl, false);
      show(captureEl, true);
      hideError();
      capturedFaces = {};
      capturedFacesColors = {};
      livePreviewColors = null;
      currentFaceIdx = 0;
      renderFaces();
      renderCubeNet();
      updateInstruction();
      startPreviewLoop();
    } catch (e) {
      showError('Could not access webcam. Please allow camera permission.');
    }
  }

  function stopWebcam() {
    stopPreviewLoop();
    if (stream) {
      stream.getTracks().forEach((t) => t.stop());
      stream = null;
    }
    if (videoEl) videoEl.srcObject = null;
  }

  function updateInstruction() {
    const code = FACE_ORDER[currentFaceIdx];
    const guide = ROTATION_GUIDES[code];
    if (instructionEl) {
      instructionEl.innerHTML = `Position the <strong>${FACE_NAMES[code]}</strong> face in the box. ${guide} Press Capture.`;
    }
  }

  async function capture() {
    const img = getVideoFrameAsBase64();
    if (!img) {
      showError('Could not capture frame. Try again.');
      return;
    }
    const code = FACE_ORDER[currentFaceIdx];
    capturedFaces[code] = img;
    try {
      const res = await fetch(`${getAPIBase()}/api/classify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: img }),
      });
      if (res.ok) {
        const data = await res.json();
        if (data.face && Array.isArray(data.face)) {
          capturedFacesColors[code] = data.face;
        }
      }
    } catch (_) {}
    hideError();
    livePreviewColors = null;
    for (let i = 1; i <= 6; i++) {
      const next = (currentFaceIdx + i) % 6;
      if (!(FACE_ORDER[next] in capturedFaces)) {
        currentFaceIdx = next;
        break;
      }
    }
    renderFaces();
    renderCubeNet();
    updateInstruction();
  }

  async function solve() {
    if (Object.keys(capturedFaces).length !== 6) return;
    show(loadingEl, true);
    hideError();
    show(resultEl, false);
    try {
      const faces = FACE_ORDER.map((code) => ({
        face: code,
        image: capturedFaces[code],
      }));
      const res = await fetch(`${getAPIBase()}/api/solve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ faces }),
      });
      const data = await res.json();
      show(loadingEl, false);
      if (!res.ok) {
        showError(data.error || 'Solve failed');
        return;
      }
      stopWebcam();
      show(captureEl, false);
      show(resultEl, true);
      if (solutionTextEl) solutionTextEl.textContent = data.solution || '(Already solved)';
      if (stepsEl) {
        stepsEl.innerHTML = (data.steps || []).map((move, i) =>
          `<span class="solve-step" data-move="${move}">${i + 1}. ${move}</span>`
        ).join('');
      }
    } catch (e) {
      show(loadingEl, false);
      showError('API error. Is the backend running? Run: python api.py');
    }
  }

  function reset() {
    stopWebcam();
    capturedFaces = {};
    capturedFacesColors = {};
    livePreviewColors = null;
    currentFaceIdx = 0;
    show(captureEl, false);
    show(resultEl, false);
    show(startEl, true);
    hideError();
  }

  function solveAgain() {
    reset();
    setTimeout(() => startWebcam(), 100);
  }

  renderStartNet();
  startBtn?.addEventListener('click', startWebcam);
  captureBtn?.addEventListener('click', capture);
  submitBtn?.addEventListener('click', solve);
  resetBtn?.addEventListener('click', reset);
  againBtn?.addEventListener('click', solveAgain);

  return {
    dispose: () => {
      stopPreviewLoop();
      stopWebcam();
      startBtn?.removeEventListener('click', startWebcam);
      captureBtn?.removeEventListener('click', capture);
      submitBtn?.removeEventListener('click', solve);
      resetBtn?.removeEventListener('click', reset);
      againBtn?.removeEventListener('click', solveAgain);
    },
  };
}
