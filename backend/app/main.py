from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
SESSIONS_FILE = DATA_DIR / "sessions.json"

app = FastAPI(
    title="Air Drawing API",
    version="1.0.0",
    description="Backend for Air Drawing Studio",
)

ALLOWED_ORIGINS = [
    "https://newgesture.vercel.app",
    "https://air-drawing-frontend.onrender.com",
    "https://newgesture-2.onrender.com",
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://127.0.0.1",
    "http://127.0.0.1:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class StrokePoint(BaseModel):
    x: float
    y: float


class Stroke(BaseModel):
    color: str
    size: int
    points: list[StrokePoint]


class SessionIn(BaseModel):
    name: str = Field(default_factory=lambda: f"session-{uuid.uuid4().hex[:8]}")
    strokes: list[Stroke] = []
    created_at: str | None = None


class SessionOut(SessionIn):
    id: str


class ConnectionManager:
    def __init__(self) -> None:
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket) -> None:
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, message: dict[str, Any]) -> None:
        dead: list[WebSocket] = []
        for ws in self.active:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


def read_sessions() -> list[dict[str, Any]]:
    if not SESSIONS_FILE.exists():
        return []
    try:
        return json.loads(SESSIONS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def write_sessions(items: list[dict[str, Any]]) -> None:
    SESSIONS_FILE.write_text(
        json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8"
    )


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Air Drawing API running 🎨", "docs": "/docs"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


@app.get("/api/sessions")
def list_sessions() -> list[dict[str, Any]]:
    return read_sessions()


@app.post("/api/sessions", status_code=201)
async def create_session(session: SessionIn) -> JSONResponse:
    items = read_sessions()
    payload = session.model_dump()
    payload["id"] = uuid.uuid4().hex[:12]
    payload["created_at"] = payload.get("created_at") or datetime.utcnow().isoformat()
    items.append(payload)
    write_sessions(items)
    await manager.broadcast(
        {"type": "session_saved", "session_id": payload["id"], "name": payload["name"]}
    )
    return JSONResponse(payload, status_code=201)


@app.get("/api/sessions/{session_id}")
def get_session(session_id: str) -> JSONResponse:
    for item in read_sessions():
        if item["id"] == session_id:
            return JSONResponse(item)
    return JSONResponse({"error": "Session not found"}, status_code=404)


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str) -> JSONResponse:
    items = read_sessions()
    new_items = [s for s in items if s["id"] != session_id]
    if len(new_items) == len(items):
        return JSONResponse({"error": "Not found"}, status_code=404)
    write_sessions(new_items)
    await manager.broadcast({"type": "session_deleted", "session_id": session_id})
    return JSONResponse({"deleted": session_id})


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    await websocket.send_json(
        {
            "type": "welcome",
            "message": "Connected to Air Drawing WebSocket",
            "time": datetime.utcnow().isoformat(),
        }
    )
    try:
        while True:
            data = await websocket.receive_json()
            event = data.get("type", "")
            if event == "ping":
                await websocket.send_json(
                    {"type": "pong", "time": datetime.utcnow().isoformat()}
                )
            elif event == "broadcast":
                await manager.broadcast(
                    {"type": "broadcast", "payload": data.get("payload")}
                )
    except WebSocketDisconnect:
        manager.disconnect(websocket)
