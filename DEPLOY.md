# Deployment Guide — Hexgate Frontend & API

Deploy the Hexgate cube solver so others can use it from the web. The frontend is static (Vite); the backend is a Flask API with OpenCV.

---

## Overview

| Component | Tech | Deploy to |
|-----------|------|-----------|
| **Backend API** | Flask, OpenCV, scikit-learn | Render, Railway, Fly.io |
| **Frontend** | Vite, Three.js (static) | Vercel, Netlify, GitHub Pages |

Deploy the **backend first**, then the frontend (it needs the API URL).

---

## 1. Deploy the Backend API

### Option A: Render (recommended, free tier)

1. **Create a Web Service** at [render.com](https://render.com) → New → Web Service.

2. **Connect your GitHub repo** (`mutasim-rehman/rubiks-cube-solver`).

3. **Configure:**
   - **Build Command:** `pip install -r requirements.txt && pip install gunicorn`
   - **Start Command:** `python -m gunicorn -b 0.0.0.0:$PORT api:app`
   - **Instance Type:** Free (or paid for faster cold starts)

4. **Root directory:** Set to repo root (where `api.py` and `requirements.txt` are).

5. After deploy, note the URL, e.g. `https://hexgate-api.onrender.com`.

**Note:** Free tier spins down after inactivity; first request may take 30–60 seconds.

---

### Option B: Railway

1. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub.

2. Select the repo and set:
   - **Root Directory:** `/` (repo root)
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python -m gunicorn -b 0.0.0.0:$PORT api:app`

3. Deploy and copy the public URL.

---

### Option C: Fly.io

1. Install [flyctl](https://fly.io/docs/hands-on/install-flyctl/).

2. In the repo root, create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn
COPY . .

EXPOSE 8080
CMD ["gunicorn", "-b", "0.0.0.0:8080", "api:app"]
```

3. Run:
   ```bash
   fly launch
   fly deploy
   ```

4. Note the app URL (e.g. `https://your-app.fly.dev`).

---

## 2. Deploy the Frontend

### Option A: Vercel (recommended)

1. Go to [vercel.com](https://vercel.com) → Add New → Project.

2. Import the GitHub repo.

3. **Configure:**
   - **Root Directory:** `frontend`
   - **Framework Preset:** Vite
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`

4. **Environment Variable:**
   - Name: `VITE_API_URL`
   - Value: `https://your-api.onrender.com` (your backend URL, no trailing slash)

5. Deploy. Vercel will build and host the site.

---

### Option B: Netlify

1. Go to [netlify.com](https://netlify.com) → Add new site → Import from Git.

2. **Build settings:**
   - **Base directory:** `frontend`
   - **Build command:** `npm run build`
   - **Publish directory:** `frontend/dist`

3. **Environment variable:** `VITE_API_URL` = your backend URL.

4. Deploy.

---

### Option C: GitHub Pages

1. In `frontend/vite.config.js`, add:
   ```js
   base: '/rubiks-cube-solver/',  // or your repo name
   ```

2. Build:
   ```bash
   cd frontend && npm run build
   ```

3. Enable GitHub Pages: repo → Settings → Pages → Source: GitHub Actions (or deploy `dist/` manually).

4. Set `VITE_API_URL` in the build step (e.g. in a GitHub Actions workflow).

---

## 3. Production Checklist

- [ ] Backend deployed and `/api/health` returns `{"status":"ok"}`.
- [ ] `color_model.pkl` is in the repo (backend needs it for classification).
- [ ] Frontend built with `VITE_API_URL` pointing to the backend.
- [ ] CORS: Flask-CORS allows your frontend origin (default allows all; restrict if needed).

---

## 4. Local Production Test

Before deploying, test locally:

```bash
# Terminal 1 — Backend
pip install -r requirements.txt
python -m gunicorn -b 0.0.0.0:5000 api:app

# Terminal 2 — Frontend (built)
cd frontend
VITE_API_URL=http://localhost:5000 npm run build
npx serve dist
```

Open `http://localhost:3000` and try the Solve flow.
