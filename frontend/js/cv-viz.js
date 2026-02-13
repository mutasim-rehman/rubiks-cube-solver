/**
 * Computer Vision Pipeline Visualization
 * Simulated steps: Original → Grayscale → Blur → Edges → Contours
 */
export function initCvViz(container) {
  if (!container) return null;

  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  let width = 0, height = 0;
  let highlightStep = 0;
  let animId = 0;
  let lastStepTime = performance.now();

  // Fixed cube face pattern (one color per face for clarity)
  const faceGrid = [
    [0, 1, 0], [1, 2, 1], [0, 1, 0],  // R,G,R / G,B,G / R,G,R
  ];
  const colors = ['#ef4444', '#22c55e', '#2563eb', '#eab308', '#f97316', '#f8fafc'];

  function drawCubeFace(ctx, x, y, w, h, mode) {
    const cellW = w / 3;
    const cellH = h / 3;

    for (let i = 0; i < 3; i++) {
      for (let j = 0; j < 3; j++) {
        const cx = x + j * cellW;
        const cy = y + i * cellH;
        const c = colors[faceGrid[i]?.[j] ?? 0];

        if (mode === 'original') {
          ctx.fillStyle = c;
          ctx.fillRect(cx + 2, cy + 2, cellW - 4, cellH - 4);
        } else if (mode === 'grayscale') {
          const gray = 0.3 * parseInt(c.slice(1, 3), 16) / 255
            + 0.59 * parseInt(c.slice(3, 5), 16) / 255
            + 0.11 * parseInt(c.slice(5, 7), 16) / 255;
          ctx.fillStyle = `rgb(${gray*255|0},${gray*255|0},${gray*255|0})`;
          ctx.fillRect(cx + 2, cy + 2, cellW - 4, cellH - 4);
        } else if (mode === 'blur') {
          ctx.fillStyle = 'rgba(128,128,128,0.6)';
          ctx.fillRect(cx + 2, cy + 2, cellW - 4, cellH - 4);
        } else if (mode === 'edges') {
          ctx.strokeStyle = '#00d4aa';
          ctx.lineWidth = 2;
          ctx.strokeRect(cx, cy, cellW, cellH);
        } else if (mode === 'contours') {
          ctx.strokeStyle = '#00d4aa';
          ctx.lineWidth = 2;
          ctx.strokeRect(cx, cy, cellW, cellH);
          ctx.fillStyle = 'rgba(0,212,170,0.1)';
          ctx.fillRect(cx, cy, cellW, cellH);
        }
      }
    }
  }

  const steps = [
    { name: 'Original', mode: 'original' },
    { name: 'Grayscale', mode: 'grayscale' },
    { name: 'Gaussian Blur', mode: 'blur' },
    { name: 'Canny Edges', mode: 'edges' },
    { name: 'Contours (squares)', mode: 'contours' },
  ];

  function draw() {
    ctx.fillStyle = '#0d0f14';
    ctx.fillRect(0, 0, width, height);

    const pad = 20;
    const boxW = (width - pad * 2) / steps.length - pad;
    const boxH = height - pad * 2 - 30;

    for (let i = 0; i < steps.length; i++) {
      const x = pad + i * (boxW + pad);
      const s = steps[i];
      const active = i === highlightStep;

      ctx.fillStyle = active ? 'rgba(0,212,170,0.15)' : 'rgba(255,255,255,0.02)';
      ctx.fillRect(x, pad, boxW, boxH);
      ctx.strokeStyle = active ? '#00d4aa' : 'rgba(255,255,255,0.1)';
      ctx.lineWidth = 1;
      ctx.strokeRect(x, pad, boxW, boxH);

      drawCubeFace(ctx, x + 10, pad + 10, boxW - 20, boxH - 50, s.mode);

      ctx.fillStyle = active ? '#00d4aa' : '#6b7280';
      ctx.font = '11px JetBrains Mono';
      ctx.textAlign = 'center';
      ctx.fillText(s.name, x + boxW / 2, height - 12);
    }
    ctx.textAlign = 'left';
  }

  function animate(now = 0) {
    if (now - lastStepTime > 2500) {
      lastStepTime = now;
      highlightStep = (highlightStep + 1) % steps.length;
    }
    draw();
    animId = requestAnimationFrame(animate);
  }

  function resize() {
    const rect = container.getBoundingClientRect();
    width = rect.width;
    height = rect.height;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = width + 'px';
    canvas.style.height = height + 'px';
    ctx.scale(dpr, dpr);
  }

  resize();
  container.appendChild(canvas);
  animate();

  const ro = new ResizeObserver(resize);
  ro.observe(container);

  return {
    dispose: () => {
      cancelAnimationFrame(animId);
      ro.disconnect();
      container.removeChild(canvas);
    },
  };
}
