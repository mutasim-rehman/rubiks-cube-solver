/**
 * Kociemba as U-Net — Encoder-decoder with zoomable Phase 1 & Phase 2
 */
import { MOVES, apply } from './kociemba-moves.js';

const SCRAMBLE = 'DRLUUBFBRBLURRLRUBLRDDFDLFUFUFFDBRDUBRUFLLFDDBFLUBLRBD';
const SOLUTION = "D2 R' D' F2 B D R2 D2 R' F2 D' F2 U' B2 L2 U2 D R2 U".split(' ');
const SOLVED = 'UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB';

const COL_HEX = {
  U: '#ffffff', R: '#2563eb', F: '#ef4444',
  D: '#eab308', L: '#22c55e', B: '#f97316',
};

function getStateAfter(idx) {
  let s = SCRAMBLE;
  for (let i = 0; i < idx; i++) {
    const m = SOLUTION[i];
    const key = m.endsWith("'") ? m[0] + "'" : m;
    s = apply(s, MOVES[key] || MOVES[m]);
  }
  return s;
}

export function initKociembaViz(container) {
  if (!container) return null;

  const G1_STATE_IDX = 10;
  const g1State = getStateAfter(G1_STATE_IDX);

  const wrapper = document.createElement('div');
  wrapper.className = 'kociemba-wrapper';
  wrapper.style.cssText = 'position:relative;cursor:pointer';
  container.appendChild(wrapper);

  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  const dpr = Math.min(window.devicePixelRatio || 1, 2);

  const cell = 5;
  const gridW = 9 * (cell + 1);
  const gridH = 6 * (cell + 1);
  const blockW = 28;
  const blockH = 60;

  let layout = { encX: 0, encY: 0, encW: 0, encH: 0, decX: 0, decY: 0, decW: 0, decH: 0 };
  let zoomedPhase = 0;

  function drawBlockArray(state, x, y, label, color) {
    ctx.save();
    ctx.translate(x, y);
    ctx.shadowColor = 'rgba(0,0,0,0.4)';
    ctx.shadowBlur = 8;
    ctx.shadowOffsetY = 3;
    ctx.fillStyle = 'rgba(30,35,45,0.9)';
    ctx.fillRect(0, 0, gridW + 12, gridH + 24);
    ctx.shadowBlur = 0;
    ctx.font = '10px JetBrains Mono';
    ctx.fillStyle = color || '#74c0fc';
    ctx.fillText(label, 6, 14);
    for (let f = 0; f < 6; f++) {
      for (let i = 0; i < 9; i++) {
        const idx = f * 9 + i;
        const letter = state[idx];
        const fc = f % 3, fr = Math.floor(f / 3);
        const c = i % 3, r = Math.floor(i / 3);
        const px = 6 + fc * (3 * (cell + 1) + 2) + c * (cell + 1);
        const py = 18 + fr * (3 * (cell + 1) + 2) + r * (cell + 1);
        ctx.fillStyle = COL_HEX[letter] || '#333';
        ctx.fillRect(px, py, cell, cell);
        ctx.strokeStyle = 'rgba(255,255,255,0.2)';
        ctx.strokeRect(px, py, cell, cell);
      }
    }
    ctx.restore();
  }

  function drawProcBlock(x, y, w, h, label, color) {
    const grad = ctx.createLinearGradient(x, y, x + w, y + h);
    grad.addColorStop(0, color || '#7c3aed');
    grad.addColorStop(1, '#4c1d95');
    ctx.save();
    ctx.shadowColor = 'rgba(0,0,0,0.3)';
    ctx.shadowBlur = 6;
    ctx.shadowOffsetY = 2;
    ctx.fillStyle = grad;
    ctx.fillRect(x, y, w, h);
    ctx.shadowBlur = 0;
    ctx.strokeStyle = 'rgba(255,255,255,0.15)';
    ctx.strokeRect(x, y, w, h);
    ctx.fillStyle = 'rgba(255,255,255,0.9)';
    ctx.font = '9px JetBrains Mono';
    ctx.textAlign = 'center';
    ctx.fillText(label, x + w / 2, y + h / 2 + 3);
    ctx.textAlign = 'left';
    ctx.restore();
  }

  function drawArrow(x1, y1, x2, y2, color) {
    ctx.strokeStyle = color || 'rgba(59, 130, 246, 0.6)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
    const angle = Math.atan2(y2 - y1, x2 - x1);
    const head = 8;
    ctx.beginPath();
    ctx.moveTo(x2, y2);
    ctx.lineTo(x2 - head * Math.cos(angle - 0.4), y2 - head * Math.sin(angle - 0.4));
    ctx.lineTo(x2 - head * Math.cos(angle + 0.4), y2 - head * Math.sin(angle + 0.4));
    ctx.closePath();
    ctx.fillStyle = color || 'rgba(59, 130, 246, 0.8)';
    ctx.fill();
  }

  function drawSkipConnection(x1, y1, x2, y2) {
    const midX = (x1 + x2) / 2;
    ctx.strokeStyle = 'rgba(34, 197, 94, 0.5)';
    ctx.lineWidth = 1.5;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.bezierCurveTo(midX + 40, y1, midX + 40, y2, x2, y2);
    ctx.stroke();
    ctx.setLineDash([]);
  }

  function drawNode(x, y, w, h, label, sublabel, color) {
    const r = 8;
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + w - r, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + r);
    ctx.lineTo(x + w, y + h - r);
    ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    ctx.lineTo(x + r, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - r);
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.closePath();
    ctx.fillStyle = color;
    ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,0.25)';
    ctx.lineWidth = 1.5;
    ctx.stroke();
    ctx.fillStyle = 'rgba(255,255,255,0.95)';
    ctx.font = 'bold 10px JetBrains Mono';
    ctx.textAlign = 'center';
    ctx.fillText(label, x + w / 2, y + h / 2 - (sublabel ? 6 : 0));
    if (sublabel) {
      ctx.font = '9px JetBrains Mono';
      ctx.fillStyle = 'rgba(200,220,255,0.85)';
      ctx.fillText(sublabel, x + w / 2, y + h / 2 + 8);
    }
    ctx.restore();
  }

  function drawNodeConnections(nodes, color) {
    for (let i = 0; i < nodes.length - 1; i++) {
      const a = nodes[i], b = nodes[i + 1];
      const x1 = a.x + a.w, y1 = a.y + a.h / 2;
      const x2 = b.x, y2 = b.y + b.h / 2;
      drawArrow(x1, y1, x2, y2, color);
    }
  }

  function drawBranchMerge(fromNodes, toNode, color) {
    const tx = toNode.x + toNode.w / 2;
    const ty = toNode.y;
    fromNodes.forEach((n) => {
      const x1 = n.x + n.w / 2;
      const y1 = n.y + n.h;
      const midY = (y1 + ty) / 2;
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.bezierCurveTo(x1, midY, tx, midY, tx, ty);
      ctx.stroke();
    });
    const angle = -Math.PI / 2;
    const head = 6;
    ctx.beginPath();
    ctx.moveTo(tx, ty);
    ctx.lineTo(tx - head * Math.cos(angle - 0.35), ty - head * Math.sin(angle - 0.35));
    ctx.lineTo(tx - head * Math.cos(angle + 0.35), ty - head * Math.sin(angle + 0.35));
    ctx.closePath();
    ctx.fillStyle = color;
    ctx.fill();
  }

  function renderZoom(w, h) {
    ctx.fillStyle = '#0a0c10';
    ctx.fillRect(0, 0, w, h);

    const nw = 90;
    const nh = 44;
    const gap = 28;
    const arrowColor = 'rgba(99, 102, 241, 0.7)';
    const arrowColor2 = 'rgba(13, 148, 136, 0.7)';

    if (zoomedPhase === 1) {
      ctx.fillStyle = '#7c3aed';
      ctx.font = 'bold 14px JetBrains Mono';
      ctx.textAlign = 'center';
      ctx.fillText('Phase 1: Reduction to G₁', w / 2, 28);

      const totalW = 5 * nw + 4 * gap;
      let ox = (w - totalW) / 2;
      const baseY = 55;

      const nodes = [
        { x: ox, y: baseY, w: nw, h: nh, label: '54', sublabel: 'facelets', color: 'rgba(34, 197, 94, 0.5)' },
        { x: ox += nw + gap, y: baseY, w: nw, h: nh, label: 'Coord', sublabel: 'map', color: 'rgba(124, 58, 237, 0.55)' },
        { x: ox += nw + gap, y: baseY, w: nw, h: nh, label: 'Twist', sublabel: '0–2186', color: 'rgba(109, 40, 217, 0.5)' },
        { x: ox += nw + gap, y: baseY, w: nw, h: nh, label: 'Flip', sublabel: '0–2047', color: 'rgba(109, 40, 217, 0.5)' },
        { x: ox += nw + gap, y: baseY, w: nw, h: nh, label: 'UD-slice', sublabel: '0–494', color: 'rgba(109, 40, 217, 0.5)' },
      ];
      nodes.forEach((n) => drawNode(n.x, n.y, n.w, n.h, n.label, n.sublabel, n.color));
      drawNodeConnections(nodes.slice(0, 2), arrowColor);
      drawNodeConnections(nodes.slice(1, 5), arrowColor);

      const row2Y = baseY + nh + 50;
      const pruneNode = { x: (w - nw * 3 - gap * 2) / 2, y: row2Y, w: nw * 3 + gap * 2, h: nh, label: 'Prune lookup', sublabel: 'h₁', color: 'rgba(91, 33, 182, 0.5)' };
      drawNode(pruneNode.x, pruneNode.y, pruneNode.w, pruneNode.h, 'Prune lookup', 'h₁ heuristic', pruneNode.color);
      drawBranchMerge(nodes.slice(2), pruneNode, arrowColor);

      const idaNode = { x: pruneNode.x + pruneNode.w / 2 - nw / 2, y: row2Y + nh + 35, w: nw, h: nh, label: 'IDA*', sublabel: '18 moves', color: 'rgba(79, 70, 229, 0.55)' };
      drawNode(idaNode.x, idaNode.y, idaNode.w, idaNode.h, 'IDA*', '18 moves', idaNode.color);
      drawArrow(pruneNode.x + pruneNode.w / 2, pruneNode.y + pruneNode.h, idaNode.x + idaNode.w / 2, idaNode.y, arrowColor);

      const g1Node = { x: idaNode.x, y: idaNode.y + nh + 35, w: nw, h: nh, label: 'G₁', sublabel: 'state', color: 'rgba(245, 158, 11, 0.5)' };
      drawNode(g1Node.x, g1Node.y, g1Node.w, g1Node.h, 'G₁', 'state', g1Node.color);
      drawArrow(idaNode.x + idaNode.w / 2, idaNode.y + idaNode.h, g1Node.x + g1Node.w / 2, g1Node.y, arrowColor);
    } else if (zoomedPhase === 2) {
      ctx.fillStyle = '#0d9488';
      ctx.font = 'bold 14px JetBrains Mono';
      ctx.textAlign = 'center';
      ctx.fillText('Phase 2: Solve within G₁', w / 2, 28);

      const totalW = 4 * nw + 3 * gap;
      let ox = (w - totalW) / 2;
      const baseY = 55;

      const nodes = [
        { x: ox, y: baseY, w: nw, h: nh, label: 'G₁', sublabel: 'state', color: 'rgba(245, 158, 11, 0.5)' },
        { x: ox += nw + gap, y: baseY, w: nw, h: nh, label: 'Coord', sublabel: 'map', color: 'rgba(13, 148, 136, 0.5)' },
        { x: ox += nw + gap, y: baseY, w: nw, h: nh, label: 'Corner', sublabel: 'Edge+Slice', color: 'rgba(15, 118, 110, 0.5)' },
        { x: ox += nw + gap, y: baseY, w: nw, h: nh, label: 'IDA*', sublabel: '6 moves', color: 'rgba(17, 94, 89, 0.55)' },
      ];
      nodes.forEach((n) => drawNode(n.x, n.y, n.w, n.h, n.label, n.sublabel, n.color));
      drawNodeConnections(nodes, arrowColor2);

      const row2Y = baseY + nh + 45;
      const solvedNode = { x: nodes[3].x + nw / 2 - nw / 2, y: row2Y, w: nw, h: nh, label: 'Solved', sublabel: '54', color: 'rgba(239, 68, 68, 0.5)' };
      drawNode(solvedNode.x, solvedNode.y, solvedNode.w, solvedNode.h, 'Solved', '54', solvedNode.color);
      drawArrow(nodes[3].x + nw / 2, nodes[3].y + nh, solvedNode.x + nw / 2, solvedNode.y, arrowColor2);

      ctx.fillStyle = 'rgba(13, 148, 136, 0.4)';
      ctx.font = '9px JetBrains Mono';
      ctx.textAlign = 'center';
      ctx.fillText('U D R2 L2 F2 B2', w / 2, row2Y + nh + 22);
    }

    ctx.fillStyle = 'rgba(255,255,255,0.12)';
    ctx.fillRect(w - 50, 12, 32, 28);
    ctx.strokeStyle = 'rgba(255,255,255,0.3)';
    ctx.strokeRect(w - 50, 12, 32, 28);
    ctx.fillStyle = '#e8eaed';
    ctx.font = '18px JetBrains Mono';
    ctx.textAlign = 'center';
    ctx.fillText('×', w - 34, 30);
    ctx.textAlign = 'left';

    ctx.fillStyle = '#6b7280';
    ctx.font = '10px JetBrains Mono';
    ctx.textAlign = 'center';
    ctx.fillText('click anywhere to close', w / 2, h - 20);
  }

  function render() {
    const w = container.clientWidth;
    const h = 420;
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    canvas.style.width = w + 'px';
    canvas.style.height = h + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    if (zoomedPhase) {
      renderZoom(w, h);
      return;
    }

    ctx.fillStyle = '#0a0c10';
    ctx.fillRect(0, 0, w, h);

    const cx = w / 2;
    const inputX = Math.max(20, w * 0.03);
    const outputX = w - Math.max(20, w * 0.03) - gridW - 12;
    const encX = inputX + gridW + Math.max(20, w * 0.04);
    const bottleneckX = cx - (gridW + 12) / 2;
    const decX = bottleneckX + gridW + Math.max(30, w * 0.05);
    const baseY = 80;

    layout.encX = encX;
    layout.encY = baseY + 12;
    layout.encW = 3 * (blockW + 12) + blockW;
    layout.encH = blockH + 16;
    layout.decX = decX;
    layout.decY = baseY + 12;
    layout.decW = 3 * (blockW + 12) + blockW;
    layout.decH = blockH + 16;

    drawBlockArray(SCRAMBLE, inputX, baseY, 'input', '#22c55e');

    drawProcBlock(encX, baseY + 20, blockW, blockH, 'Coord', '#7c3aed');
    drawProcBlock(encX + blockW + 12, baseY + 20, blockW, blockH, 'Phase 1', '#6d28d9');
    drawProcBlock(encX + 2 * (blockW + 12), baseY + 20, blockW, blockH, '→ G₁', '#5b21b6');

    drawArrow(inputX + gridW + 12, baseY + gridH / 2 + 12, encX, baseY + blockH / 2 + 20, 'rgba(59, 130, 246, 0.7)');
    drawArrow(encX + blockW, baseY + blockH / 2 + 20, encX + blockW + 12, baseY + blockH / 2 + 20, 'rgba(59, 130, 246, 0.7)');
    drawArrow(encX + blockW + 12 + blockW, baseY + blockH / 2 + 20, encX + 2 * (blockW + 12), baseY + blockH / 2 + 20, 'rgba(59, 130, 246, 0.7)');

    drawBlockArray(g1State, bottleneckX, baseY, 'G₁', '#f59e0b');
    drawArrow(encX + 2 * (blockW + 12) + blockW, baseY + blockH / 2 + 20, bottleneckX, baseY + gridH / 2 + 12, 'rgba(59, 130, 246, 0.7)');

    drawProcBlock(decX, baseY + 20, blockW, blockH, 'Phase 2', '#0d9488');
    drawProcBlock(decX + blockW + 12, baseY + 20, blockW, blockH, 'Perm', '#0f766e');
    drawProcBlock(decX + 2 * (blockW + 12), baseY + 20, blockW, blockH, 'Solve', '#115e59');

    drawArrow(bottleneckX + gridW + 12, baseY + gridH / 2 + 12, decX, baseY + blockH / 2 + 20, 'rgba(59, 130, 246, 0.7)');
    drawArrow(decX + blockW, baseY + blockH / 2 + 20, decX + blockW + 12, baseY + blockH / 2 + 20, 'rgba(59, 130, 246, 0.7)');
    drawArrow(decX + blockW + 12 + blockW, baseY + blockH / 2 + 20, decX + 2 * (blockW + 12), baseY + blockH / 2 + 20, 'rgba(59, 130, 246, 0.7)');
    drawArrow(decX + 2 * (blockW + 12) + blockW, baseY + blockH / 2 + 20, outputX, baseY + gridH / 2 + 12, 'rgba(59, 130, 246, 0.7)');

    drawBlockArray(SOLVED, outputX, baseY, 'output', '#ef4444');

    drawSkipConnection(inputX + gridW + 12, baseY + 30, decX + 2 * (blockW + 12) + blockW / 2, baseY + blockH + 30);
    drawSkipConnection(encX + blockW / 2, baseY + 20, decX + blockW + 12 + blockW / 2, baseY + blockH + 20);

    ctx.fillStyle = '#9ca3af';
    ctx.font = '11px JetBrains Mono';
    ctx.fillText('Encoder (Phase 1) — click to zoom', encX - 10, baseY + 8);
    ctx.fillText('Decoder (Phase 2) — click to zoom', decX - 10, baseY + 8);
  }

  wrapper.addEventListener('click', (e) => {
    const rect = canvas.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * container.clientWidth;
    const y = ((e.clientY - rect.top) / rect.height) * 420;
    if (zoomedPhase) {
      zoomedPhase = 0;
      render();
    } else if (x >= layout.encX && x <= layout.encX + layout.encW && y >= layout.encY && y <= layout.encY + layout.encH) {
      zoomedPhase = 1;
      render();
    } else if (x >= layout.decX && x <= layout.decX + layout.decW && y >= layout.decY && y <= layout.decY + layout.decH) {
      zoomedPhase = 2;
      render();
    }
  });

  wrapper.appendChild(canvas);
  const ro = new ResizeObserver(render);
  ro.observe(container);
  render();

  return {
    dispose: () => {
      ro.disconnect();
      wrapper.remove();
    },
  };
}
