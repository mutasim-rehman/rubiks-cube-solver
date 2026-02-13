/**
 * Interactive 3D Rubik's Cube - Three.js
 * Face order: U R F D L B | Colors: W B R Y G O
 */
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

const FACE_COLORS = {
  U: 0xffffff, // White
  R: 0x2563eb, // Blue
  F: 0xef4444, // Red
  D: 0xeab308, // Yellow
  L: 0x22c55e, // Green
  B: 0xf97316, // Orange
};

const FACE_ORDER = ['U', 'R', 'F', 'D', 'L', 'B'];

export function initCube3D(container) {
  if (!container) return null;

  const width = container.clientWidth;
  const height = container.clientHeight;
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0d0f14);

  const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 1000);
  camera.position.set(5, 4, 5);

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setSize(width, height);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  container.appendChild(renderer.domElement);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.05;
  controls.autoRotate = true;
  controls.autoRotateSpeed = 0.5;

  // Ambient + directional light
  scene.add(new THREE.AmbientLight(0xffffff, 0.5));
  const dirLight = new THREE.DirectionalLight(0xffffff, 0.9);
  dirLight.position.set(5, 10, 5);
  dirLight.castShadow = true;
  scene.add(dirLight);

  const gap = 0.02;
  const size = 0.3;
  const group = new THREE.Group();

  // Build 3x3x3 cube: 27 minicubes, each with colored faces
  const geometry = new THREE.BoxGeometry(size - gap, size - gap, size - gap);
  const blackMat = new THREE.MeshLambertMaterial({ color: 0x1a1a1a });

  for (let x = -1; x <= 1; x++) {
    for (let y = -1; y <= 1; y++) {
      for (let z = -1; z <= 1; z++) {
        const materials = [];
        // right (+x), left (-x), top (+y), bottom (-y), front (+z), back (-z)
        const dirs = [
          [1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1],
        ];
        const faceMap = { '1,0,0': 'R', '-1,0,0': 'L', '0,1,0': 'U', '0,-1,0': 'D', '0,0,1': 'F', '0,0,-1': 'B' };
        for (const [dx, dy, dz] of dirs) {
          const key = `${dx},${dy},${dz}`;
          const face = faceMap[key];
          const isOuter =
            (dx === 1 && x === 1) || (dx === -1 && x === -1) ||
            (dy === 1 && y === 1) || (dy === -1 && y === -1) ||
            (dz === 1 && z === 1) || (dz === -1 && z === -1);
          const mat = isOuter ? new THREE.MeshLambertMaterial({ color: FACE_COLORS[face] }) : blackMat;
          materials.push(mat);
        }
        const mesh = new THREE.Mesh(geometry, materials);
        mesh.position.set(x * size, y * size, z * size);
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        group.add(mesh);
      }
    }
  }

  group.scale.setScalar(1.2);
  scene.add(group);

  function animate() {
    requestAnimationFrame(animate);
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

  return { scene, camera, renderer, controls, group, dispose: () => {
    window.removeEventListener('resize', onResize);
    renderer.dispose();
    container.removeChild(renderer.domElement);
  }};
}
