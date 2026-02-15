/**
 * Hexgate — Cube Solver & AI Educational Frontend
 * Initializes all visualizations with Intersection Observer for performance.
 */
import { initCube3D } from './js/cube3d.js';
import { initKMeansViz } from './js/kmeans-viz.js';
import { initKnnViz } from './js/knn-viz.js';
import { initCvViz } from './js/cv-viz.js';
import { initKociembaViz } from './js/kociemba-viz.js';
import { initSolveUI } from './js/solve-ui.js';

const instances = {};

function initSection(id, init, options = {}) {
  const el = document.getElementById(id);
  if (!el || instances[id]) return;
  try {
    instances[id] = init(el, options);
  } catch (e) {
    console.warn(`Failed to init ${id}:`, e);
  }
}

function disposeSection(id) {
  if (instances[id]?.dispose) {
    instances[id].dispose();
    delete instances[id];
  }
}

const sections = [
  { id: 'hero-cube', init: initCube3D, options: {} },
  { id: 'cube-3d', init: initCube3D, options: { scramble: true } },
  { id: 'kmeans-viz', init: initKMeansViz },
  { id: 'knn-viz', init: initKnnViz },
  { id: 'cv-viz', init: initCvViz },
  { id: 'kociemba-viz', init: initKociembaViz },
];

const observer = new IntersectionObserver(
  (entries) => {
    for (const entry of entries) {
      const section = sections.find((s) => s.id === entry.target.id);
      if (!section) continue;
      const { id, init, options = {} } = section;
      if (entry.isIntersecting) {
        initSection(id, init, options);
      } else {
        disposeSection(id);
      }
    }
  },
  { rootMargin: '100px', threshold: 0.1 }
);

for (const { id } of sections) {
  const el = document.getElementById(id);
  if (el) observer.observe(el);
}

// Initial load: ensure hero is in view
const hero = document.getElementById('hero-cube');
if (hero) {
  const rect = hero.getBoundingClientRect();
  if (rect.top < window.innerHeight) initSection('hero-cube', initCube3D);
}

// Solve UI (always init)
initSolveUI();

// Hero video loading overlay — hide when video can play
const heroVideo = document.getElementById('hero-video');
const heroLoading = document.getElementById('hero-video-loading');
if (heroVideo && heroLoading) {
  function hideHeroLoading() {
    heroLoading.classList.add('hidden');
  }
  if (heroVideo.readyState >= 3) {
    hideHeroLoading();
  } else {
    heroVideo.addEventListener('canplay', hideHeroLoading, { once: true });
    heroVideo.addEventListener('error', hideHeroLoading, { once: true });
    setTimeout(hideHeroLoading, 8000);
  }
}
