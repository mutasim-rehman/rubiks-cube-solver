/**
 * KNN 3D: Points in RGB feature space, draggable query, k=3 neighbors
 * Pizzazz: glow, animated dashed lines, smooth transitions, pulse
 */
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

const SCALE = 4 / 255;
const OFFSET = -2;

function rgbToScene(r, g, b) {
  return new THREE.Vector3(
    r * SCALE + OFFSET,
    g * SCALE + OFFSET,
    b * SCALE + OFFSET
  );
}

const COLORS = {
  R: [239, 68, 68],
  G: [34, 197, 94],
  B: [37, 99, 235],
  Y: [234, 179, 8],
  O: [249, 115, 22],
  W: [248, 250, 252],
};

// Training points in RGB space (cube colors)
const training = [
  { rgb: COLORS.R, label: 'R' },
  { rgb: COLORS.G, label: 'G' },
  { rgb: COLORS.B, label: 'B' },
  { rgb: COLORS.Y, label: 'Y' },
  { rgb: COLORS.O, label: 'O' },
  { rgb: COLORS.W, label: 'W' },
].map(t => ({ ...t, pos: rgbToScene(...t.rgb) }));

function dist3(a, b) {
  return Math.sqrt(
    (a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2
  );
}

export function initKnnViz(container) {
  if (!container) return null;

  const width = container.clientWidth;
  const height = container.clientHeight;
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0d0f14);

  const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
  camera.position.set(4, 4, 4);

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setSize(width, height);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  container.appendChild(renderer.domElement);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.05;

  const raycaster = new THREE.Raycaster();
  const mouse = new THREE.Vector2();
  const dragPlane = new THREE.Plane();
  const dragNormal = new THREE.Vector3();
  const dragIntersect = new THREE.Vector3();

  const labelEl = document.createElement('div');
  labelEl.style.cssText = 'position:absolute;bottom:12px;left:12px;color:#9ca3af;font:11px JetBrains Mono,sans-serif;pointer-events:none;transition:opacity 0.3s';
  labelEl.textContent = 'Predicted: ? (k=3) — drag the center sphere to move';
  container.style.position = 'relative';
  container.appendChild(labelEl);

  // Query point (start in center of RGB cube)
  let queryPos = new THREE.Vector3(0, 0, 0);
  const queryGeom = new THREE.SphereGeometry(0.18, 24, 24);

  function knn(k = 3) {
    const withDist = training.map(t => ({
      ...t,
      d: dist3(t.pos, queryPos),
    }));
    withDist.sort((a, b) => a.d - b.d);
    return withDist.slice(0, k);
  }

  function majorityVote(neighbors) {
    const votes = {};
    for (const n of neighbors) votes[n.label] = (votes[n.label] || 0) + 1;
    let best = 'R', bestCount = 0;
    for (const [label, c] of Object.entries(votes)) {
      if (c > bestCount) { bestCount = c; best = label; }
    }
    return best;
  }

  const predicted = majorityVote(knn(3));
  const queryMat = new THREE.MeshBasicMaterial({
    color: new THREE.Color(
      COLORS[predicted][0] / 255,
      COLORS[predicted][1] / 255,
      COLORS[predicted][2] / 255
    ),
  });
  const queryMesh = new THREE.Mesh(queryGeom, queryMat);
  queryMesh.position.copy(queryPos);
  queryMesh.userData.isQuery = true;
  scene.add(queryMesh);

  // Glow sphere behind query
  const glowGeom = new THREE.SphereGeometry(0.35, 20, 20);
  const glowMat = new THREE.MeshBasicMaterial({
    color: 0x00d4aa,
    transparent: true,
    opacity: 0.15,
  });
  const glowMesh = new THREE.Mesh(glowGeom, glowMat);
  glowMesh.position.copy(queryPos);
  glowMesh.userData.isGlow = true;
  scene.add(glowMesh);

  const trainingMeshes = [];
  const pointGeom = new THREE.SphereGeometry(0.12, 16, 16);
  for (const t of training) {
    const mat = new THREE.MeshBasicMaterial({
      color: new THREE.Color(
        t.rgb[0] / 255, t.rgb[1] / 255, t.rgb[2] / 255
      ),
    });
    const m = new THREE.Mesh(pointGeom, mat);
    m.position.copy(t.pos);
    m.userData = { training: t };
    scene.add(m);
    trainingMeshes.push(m);
  }

  const lineGeometries = [];
  const lineMeshes = [];
  let time = 0;

  function updateLines() {
    for (const lm of lineMeshes) {
      lm.geometry.dispose();
      lm.material.dispose();
      scene.remove(lm);
    }
    lineMeshes.length = 0;
    lineGeometries.length = 0;

    const neighbors = knn(3);
    const predictedLabel = majorityVote(neighbors);
    queryMat.color.setRGB(
      COLORS[predictedLabel][0] / 255,
      COLORS[predictedLabel][1] / 255,
      COLORS[predictedLabel][2] / 255
    );
    glowMat.color.setRGB(
      COLORS[predictedLabel][0] / 255,
      COLORS[predictedLabel][1] / 255,
      COLORS[predictedLabel][2] / 255
    );

    const lineColors = [0x00d4aa, 0x00ffcc, 0x00b894];
    neighbors.forEach((n, i) => {
      const geom = new THREE.BufferGeometry().setFromPoints([
        queryPos.clone(),
        n.pos.clone(),
      ]);
      const lineMat = new THREE.LineDashedMaterial({
        color: lineColors[i % 3],
        dashSize: 0.15,
        gapSize: 0.08,
      });
      const line = new THREE.Line(geom, lineMat);
      line.computeLineDistances();
      lineGeometries.push(geom);
      line.userData.dashOffset = Math.random() * 10;
      scene.add(line);
      lineMeshes.push(line);
    });
  }
  updateLines();

  // RGB cube wireframe with subtle glow
  const cubeGeom = new THREE.EdgesGeometry(new THREE.BoxGeometry(4, 4, 4));
  const cubeMat = new THREE.LineBasicMaterial({ color: 0x333333 });
  const cubeWire = new THREE.LineSegments(cubeGeom, cubeMat);
  scene.add(cubeWire);

  let dragging = false;

  function onPointerDown(e) {
    const rect = renderer.domElement.getBoundingClientRect();
    mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
    raycaster.setFromCamera(mouse, camera);
    const hits = raycaster.intersectObject(queryMesh);
    if (hits.length) {
      dragging = true;
      dragPlane.setFromNormalAndCoplanarPoint(
        camera.getWorldDirection(dragNormal),
        queryMesh.position.clone()
      );
    }
  }

  function onPointerMove(e) {
    if (!dragging) return;
    const rect = renderer.domElement.getBoundingClientRect();
    mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
    raycaster.setFromCamera(mouse, camera);
    if (raycaster.intersectPlane(dragPlane, dragIntersect)) {
      // Clamp to RGB cube bounds (-2 to 2)
      queryPos.x = Math.max(-2, Math.min(2, dragIntersect.x));
      queryPos.y = Math.max(-2, Math.min(2, dragIntersect.y));
      queryPos.z = Math.max(-2, Math.min(2, dragIntersect.z));
      queryMesh.position.copy(queryPos);
      glowMesh.position.copy(queryPos);
      updateLines();
      if (labelEl) labelEl.textContent = `Predicted: ${majorityVote(knn(3))} (k=3) — drag the center sphere`;
    }
  }

  function onPointerUp() {
    dragging = false;
  }

  renderer.domElement.addEventListener('pointerdown', onPointerDown);
  renderer.domElement.addEventListener('pointermove', onPointerMove);
  renderer.domElement.addEventListener('pointerup', onPointerUp);
  renderer.domElement.addEventListener('pointerleave', onPointerUp);

  function animate() {
    requestAnimationFrame(animate);
    time += 0.016;
    if (!dragging) controls.update();
    // Pulse glow
    glowMesh.scale.setScalar(1 + 0.08 * Math.sin(time * 3));
    glowMesh.position.copy(queryPos);
    // Animate dashed lines
    lineMeshes.forEach((line, i) => {
      if (line.material.dashOffset !== undefined) {
        line.material.dashOffset = -(time * 2 + (i * 0.5)) % 1;
      }
    });
    // Subtle pulse on neighbor points
    const neighbors = knn(3);
    const neighborLabels = new Set(neighbors.map(n => n.label));
    trainingMeshes.forEach((m) => {
      const isNeighbor = neighborLabels.has(m.userData.training.label);
      const pulse = isNeighbor ? 1 + 0.12 * Math.sin(time * 4) : 1;
      m.scale.setScalar(pulse);
    });
    renderer.render(scene, camera);
  }
  animate();

  function onResize() {
    const w = container.clientWidth;
    const h = container.clientHeight;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
  }
  window.addEventListener('resize', onResize);

  return {
    dispose: () => {
      window.removeEventListener('resize', onResize);
      renderer.domElement.removeEventListener('pointerdown', onPointerDown);
      renderer.domElement.removeEventListener('pointermove', onPointerMove);
      renderer.domElement.removeEventListener('pointerup', onPointerUp);
      renderer.domElement.removeEventListener('pointerleave', onPointerUp);
      lineMeshes.forEach(lm => {
        lm.geometry.dispose();
        lm.material.dispose();
        scene.remove(lm);
      });
      if (labelEl.parentNode) labelEl.remove();
      renderer.dispose();
      container.removeChild(renderer.domElement);
    },
  };
}
