# ✋ Air Drawing Studio

A full-stack real-time hand gesture drawing app.

**Frontend** → MediaPipe Hands + Canvas API (Vanilla JS, no frameworks)  
**Backend** → FastAPI + Pydantic v2 + WebSockets (Python)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

---

## ✨ Features
- 🖐️ Two-hand skeleton tracking (21 landmarks per hand)
- ✏️ Air drawing with index finger
- 🧹 Erase mode — open palm
- 🤏 Move strokes — pinch gesture
- 🎨 7 colors + adjustable brush size
- ↩️ Undo last stroke
- 💾 Save drawing as PNG
- 🔌 Save sessions to FastAPI backend
- 🔁 WebSocket live events

---

## 📁 Project Structure
```
newgesture/
├── render.yaml              ← Render IaC config (auto-deploys both services)
├── frontend/
│   └── index.html           ← Full single-file frontend app
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py          ← FastAPI app
│   ├── data/
│   │   └── sessions.json    ← Session storage (JSON)
│   └── requirements.txt
└── README.md
```

---

## 🚀 Deploy on Render (Step by Step)

### Step 1 — Deploy Backend (FastAPI)
1. Go to [render.com](https://render.com) → **New → Web Service**
2. Connect your GitHub repo: `koyeliya2004/newgesture`
3. Fill in:
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Click **Create Web Service**
5. Wait for deploy → copy your backend URL (e.g. `https://air-drawing-api.onrender.com`)

### Step 2 — Update Frontend API URL
In `frontend/index.html`, find this line:
```js
const API_BASE = 'http://127.0.0.1:8000';
```
Replace with your actual Render backend URL:
```js
const API_BASE = 'https://air-drawing-api.onrender.com';
```
Commit and push this change.

### Step 3 — Deploy Frontend (Static Site)
1. Go to Render → **New → Static Site**
2. Connect same repo: `koyeliya2004/newgesture`
3. Fill in:
   - **Root Directory**: `frontend`
   - **Publish Directory**: `.`
   - **Build Command**: *(leave empty)*
4. Click **Create Static Site**
5. Your app is live at `https://air-drawing-frontend.onrender.com` 🎉

### Optional: One-click deploy via render.yaml
If your Render plan supports Blueprints, click the **Deploy to Render** button above — it will read `render.yaml` and create both services automatically.

---

## 🏃 Run Locally

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
# → http://127.0.0.1:8000
# → Swagger docs: http://127.0.0.1:8000/docs
```

### Frontend
Open `frontend/index.html` in Chrome or Edge. Allow camera access.

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Root info |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Swagger UI |
| `GET` | `/api/sessions` | List all sessions |
| `POST` | `/api/sessions` | Save a new session |
| `GET` | `/api/sessions/{id}` | Get session by ID |
| `DELETE` | `/api/sessions/{id}` | Delete session |
| `WS` | `/ws` | WebSocket (live events) |

---

## ✋ Gesture Guide

| Gesture | Action |
|---------|--------|
| ☝️ Index finger only | Draw |
| 🤚 Open palm (4+ fingers up) | Erase nearby |
| 🤏 Pinch (thumb + index close) | Move stroke |
| ✊ Fist or other | Idle |

---

## 🛠️ Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | Vanilla JS, Canvas API, MediaPipe Hands |
| Backend | FastAPI, Pydantic v2, Uvicorn |
| Storage | JSON file (upgradeable to SQLite/PostgreSQL) |
| Hosting | Render (free tier) |

---
Built by [@koyeliya2004](https://github.com/koyeliya2004)
