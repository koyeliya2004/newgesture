# ✋ Air Drawing Studio

A full-stack real-time hand gesture drawing app using **MediaPipe Hands** (frontend) and **FastAPI** (backend).

## Features
- 🖐️ Two-hand skeleton tracking (21 landmarks per hand)
- ✏️ Air drawing with index finger
- 🧹 Erase mode — open palm
- 🤏 Move strokes — pinch gesture
- 🎨 Color picker + brush size slider
- 💾 Save sessions to FastAPI backend (JSON store)
- 🔌 WebSocket-ready for live collaboration

## Project Structure
```
newgesture/
├── frontend/
│   └── index.html          # Full single-file frontend
├── backend/
│   ├── app/
│   │   └── main.py         # FastAPI app
│   ├── data/
│   │   └── sessions.json   # Persisted sessions
│   └── requirements.txt
└── README.md
```

## Run Locally

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
# Runs at http://127.0.0.1:8000
```

### Frontend
Open `frontend/index.html` in Chrome/Edge.
Allow camera access and click **Start Camera**.

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/sessions` | List all sessions |
| POST | `/api/sessions` | Save a new session |
| GET | `/api/sessions/{id}` | Get session by ID |
| WS | `/ws` | WebSocket connection |

## Gestures
| Gesture | Action |
|---------|--------|
| ☝️ Index finger only | Draw |
| 🤚 Open palm (4+ fingers) | Erase nearby |
| 🤏 Pinch (thumb + index) | Move stroke |
| ✊ Fist / other | Idle |

## Tech Stack
- **Frontend**: Vanilla JS, MediaPipe Hands CDN, Canvas API
- **Backend**: FastAPI, Pydantic v2, Uvicorn, WebSockets
- **Storage**: JSON file (can be upgraded to SQLite/PostgreSQL)

---
Built by [@koyeliya2004](https://github.com/koyeliya2004)
