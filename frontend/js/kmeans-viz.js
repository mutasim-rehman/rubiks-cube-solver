/**
 * K-Means 3D: Pixels in RGB space → centroid = dominant color
 * Pizzazz: convergence lines, pulse ring, smooth transitions, particle flow
 */
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

// Map 0–255 to scene coords
const SCALE = 4 / 255;
const OFFSET = -2;

function rgbToScene(r, g, b) {
  return new THREE.Vector3(
    r * SCALE + OFFSET,
    g * SCALE + OFFSET,
    b * SCALE + OFFSET
  );
}

function genPixels(baseRgb, count = 100) {
  const pts = [];
  const [r, g, b] = baseRgb;
  for (let i = 0; i < count; i++) {
    const noise = () => (Math.random() - 0.5) * 70;
    pts.push([
      Math.max(0, Math.min(255, r + noise())),
      Math.max(0, Math.min(255, g + noise())),
      Math.max(0, Math.min(255, b + noise())),
    ]);
  }
  return pts;
}

function centroid(pts) {
  let sr = 0, sg = 0, sb = 0;
  for (const [r, g, b] of pts) {
    sr += r; sg += g; sb += b;
  }
  const n = pts.length;
  return [sr / n, sg / n, sb / n];
}

export function initKMeansViz(container) {
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
  container.style.position = 'relative';
  container.appendChild(renderer.domElement);

  const labelEl = document.createElement('div');
  labelEl.style.cssText = 'position:absolute;bottom:12px;left:12px;color:#9ca3af;font:11px JetBrains Mono,sans-serif;pointer-events:none';
  labelEl.textContent = 'RGB space — pixels (noise) → K-means k=1 → centroid = dominant color';
  container.appendChild(labelEl);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.05;

  // RGB cube wireframe
  const cubeGeom = new THREE.EdgesGeometry(new THREE.BoxGeometry(4, 4, 4));
  const cubeMat = new THREE.LineBasicMaterial({ color: 0x333333 });
  const cubeWire = new THREE.LineSegments(cubeGeom, cubeMat);
  cubeWire.position.set(0, 0, 0);
  scene.add(cubeWire);

  const baseColors = [
    [255, 50, 50], [50, 255, 50], [50, 80, 255],
  ];
  let pixels = genPixels(baseColors[0]);
  let center = centroid(pixels);

  const pointGeom = new THREE.SphereGeometry(0.08, 8, 8);
  const pixelMeshes = [];
  for (const [r, g, b] of pixels) {
    const mat = new THREE.MeshBasicMaterial({
      color: new THREE.Color(r / 255, g / 255, b / 255),
    });
    const m = new THREE.Mesh(pointGeom, mat);
    m.position.copy(rgbToScene(r, g, b));
    scene.add(m);
    pixelMeshes.push({ mesh: m, rgb: [r, g, b] });
  }

  const centroidGeom = new THREE.SphereGeometry(0.2, 16, 16);
  const centroidMat = new THREE.MeshBasicMaterial({
    color: new THREE.Color(center[0] / 255, center[1] / 255, center[2] / 255),
  });
  const centroidMesh = new THREE.Mesh(centroidGeom, centroidMat);
  centroidMesh.position.copy(rgbToScene(center[0], center[1], center[2]));
  scene.add(centroidMesh);

  // Glow behind centroid
  const glowGeom = new THREE.SphereGeometry(0.4, 20, 20);
  const glowMat = new THREE.MeshBasicMaterial({
    color: 0x00d4aa,
    transparent: true,
    opacity: 0.12,
  });
  const glowMesh = new THREE.Mesh(glowGeom, glowMat);
  glowMesh.position.copy(centroidMesh.position);
  scene.add(glowMesh);

  const ringGeom = new THREE.RingGeometry(0.22, 0.28, 32);
  const ringMat = new THREE.MeshBasicMaterial({
    color: 0x00d4aa,
    side: THREE.DoubleSide,
    transparent: true,
    opacity: 0.9,
  });
  const ringMesh = new THREE.Mesh(ringGeom, ringMat);
  ringMesh.position.copy(centroidMesh.position);
  ringMesh.lookAt(camera.position);
  scene.add(ringMesh);

  // Convergence lines: pixel → centroid (subset for performance)
  const lineMeshes = [];
  const lineMat = new THREE.LineBasicMaterial({
    color: 0x00d4aa,
    transparent: true,
    opacity: 0.25,
  });
  const lineCount = 12;
  for (let i = 0; i < lineCount; i++) {
    const geom = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(0, 0, 0),
      new THREE.Vector3(0, 0, 0),
    ]);
    const line = new THREE.Line(geom, lineMat);
    scene.add(line);
    lineMeshes.push(line);
  }

  let phase = 0;
  let time = 0;
  let animId = 0;

  function updateConvergenceLines() {
    const centroidPos = rgbToScene(center[0], center[1], center[2]);
    const step = Math.max(1, Math.floor(pixels.length / lineCount));
    lineMeshes.forEach((line, i) => {
      const idx = (i * step) % pixels.length;
      const [r, g, b] = pixels[idx];
      const pixelPos = rgbToScene(r, g, b);
      line.geometry.setFromPoints([pixelPos, centroidPos]);
      line.geometry.attributes.position.needsUpdate = true;
    });
  }
  updateConvergenceLines();

  function animate() {
    animId = requestAnimationFrame(animate);
    time += 0.016;
    phase += 0.012;
    if (phase >= 1) {
      phase = 0;
      const idx = Math.floor(Math.random() * baseColors.length);
      pixels = genPixels(baseColors[idx]);
      center = centroid(pixels);
      pixelMeshes.forEach((pm, i) => {
        const [r, g, b] = pixels[i] || pixels[0];
        pm.mesh.position.copy(rgbToScene(r, g, b));
        pm.mesh.material.color.setRGB(r / 255, g / 255, b / 255);
      });
      centroidMesh.position.copy(rgbToScene(center[0], center[1], center[2]));
      centroidMesh.material.color.setRGB(center[0] / 255, center[1] / 255, center[2] / 255);
      glowMat.color.setRGB(center[0] / 255, center[1] / 255, center[2] / 255);
    }
    const centroidPos = rgbToScene(center[0], center[1], center[2]);
    glowMesh.position.copy(centroidPos);
    glowMesh.scale.setScalar(1 + 0.1 * Math.sin(time * 2.5));
    ringMesh.position.copy(centroidPos);
    ringMesh.lookAt(camera.position);
    ringMesh.scale.setScalar(1 + 0.05 * Math.sin(time * 3));
    ringMat.opacity = 0.7 + 0.2 * Math.sin(time * 4);
    updateConvergenceLines();
    controls.update();
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
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', onResize);
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
