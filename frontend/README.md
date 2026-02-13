# Hexgate — Cube Solver & AI Educational Frontend

An interactive website that teaches AI and Computer Vision concepts using our Rubik's cube solver project. Built with **Three.js** for 3Blue1Brown-style visualizations.

## Features

- **Solve Your Cube** — Webcam capture → backend API → step-by-step solution
- **3D Rubik's Cube** — Interactive cube showing structure (6 faces, 54 stickers)
- **Pipeline Overview** — Vision → Color Classification → State → Solver → Robot
- **K-Means Visualization** — Pixels in RGB space, k=1 finds dominant color
- **KNN Visualization** — Drag the query point; k=3 neighbors vote for color
- **CV Pipeline** — Grayscale → Blur → Canny Edges → Contours
- **Codebase Map** — Module overview and relationships

## Run

### Frontend only (explore visualizations)

```bash
npm install
npm run dev
```

Open http://localhost:5173

### Full stack (Solve feature)

1. **Start the API** (from project root):

```bash
pip install -r requirements.txt
python api.py
```

2. **Start the frontend**:

```bash
cd frontend && npm run dev
```

3. Open http://localhost:5173, scroll to **Solve Your Cube**, and capture 6 faces.

## Build

```bash
npm run build
```

Output in `dist/`.

For production deployment (Vercel, Netlify, etc.), set `VITE_API_URL` to your backend API URL. See [DEPLOY.md](../DEPLOY.md) in the project root.
