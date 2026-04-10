from __future__ import annotations

import json
import re
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
    version="2.0.0",
    description="Backend for Air Drawing Studio — Phase 2 Collab",
)

ALLOWED_ORIGIN_PATTERNS = [
    re.compile(r"^https://newgesture.*\.vercel\.app$"),
    re.compile(r"^https://.*\.vercel\.app$"),
    re.compile(r"^http://localhost(:\d+)?$"),
    re.compile(r"^http://127\.0\.0\.1(:\d+)?$"),
]

ALLOWED_ORIGINS_EXACT = [
    "https://newgesture.vercel.app",
    "https://air-drawing-frontend.onrender.com",
]


def is_allowed_origin(origin: str) -> bool:
    if origin in ALLOWED_ORIGINS_EXACT:
        return True
    return any(p.match(origin) for p in ALLOWED_ORIGIN_PATTERNS)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Models ───────────────────────────────────────────────────────────────────

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


# ─── Solo WebSocket Manager (legacy) ──────────────────────────────────────────

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


# ─── Room Manager (Phase 2) ────────────────────────────────────────────────────

class RoomManager:
    """
    Manages collaborative rooms.
    Each room holds up to 2 WebSocket connections.
    Relays strokes + WebRTC signalling between peers.
    """

    def __init__(self) -> None:
        # room_id -> list of (ws, user_id)
        self.rooms: dict[str, list[dict[str, Any]]] = {}
        # room_id -> list of strokes drawn so far (for late-joiner sync)
        self.room_strokes: dict[str, list[dict[str, Any]]] = {}

    def create_room(self) -> str:
        room_id = uuid.uuid4().hex[:8]
        self.rooms[room_id] = []
        self.room_strokes[room_id] = []
        return room_id

    def room_exists(self, room_id: str) -> bool:
        return room_id in self.rooms

    def room_full(self, room_id: str) -> bool:
        return len(self.rooms.get(room_id, [])) >= 2

    async def join(self, room_id: str, ws: WebSocket, user_id: str) -> bool:
        """Returns True if joined successfully."""
        await ws.accept()
        if not self.room_exists(room_id):
            await ws.send_json({"type": "error", "message": "Room not found"})
            return False
        if self.room_full(room_id):
            await ws.send_json({"type": "error", "message": "Room is full (max 2 users)"})
            return False

        self.rooms[room_id].append({"ws": ws, "user_id": user_id})
        peer_count = len(self.rooms[room_id])

        # Tell joiner their role + existing strokes for sync
        await ws.send_json({
            "type": "joined",
            "room_id": room_id,
            "user_id": user_id,
            "role": "host" if peer_count == 1 else "guest",
            "peer_count": peer_count,
            "strokes": self.room_strokes[room_id],
        })

        # Notify existing peer that someone joined
        if peer_count == 2:
            other = self.rooms[room_id][0]
            await other["ws"].send_json({
                "type": "peer_joined",
                "peer_id": user_id,
            })

        return True

    def leave(self, room_id: str, ws: WebSocket) -> str | None:
        """Remove ws from room, return user_id of leaver."""
        if room_id not in self.rooms:
            return None
        leaver_id = None
        self.rooms[room_id] = [
            p for p in self.rooms[room_id] if p["ws"] != ws
        ]
        # cleanup empty rooms
        if not self.rooms[room_id]:
            del self.rooms[room_id]
            self.room_strokes.pop(room_id, None)
        return leaver_id

    async def relay(self, room_id: str, sender_ws: WebSocket, message: dict[str, Any]) -> None:
        """Send message to everyone in the room EXCEPT the sender."""
        if room_id not in self.rooms:
            return
        dead = []
        for peer in self.rooms[room_id]:
            if peer["ws"] is sender_ws:
                continue
            try:
                await peer["ws"].send_json(message)
            except Exception:
                dead.append(peer)
        for p in dead:
            self.rooms[room_id].remove(p)

    async def broadcast_room(self, room_id: str, message: dict[str, Any]) -> None:
        """Send message to ALL peers in the room."""
        if room_id not in self.rooms:
            return
        dead = []
        for peer in self.rooms[room_id]:
            try:
                await peer["ws"].send_json(message)
            except Exception:
                dead.append(peer)
        for p in dead:
            self.rooms[room_id].remove(p)

    def get_room_info(self, room_id: str) -> dict[str, Any]:
        if room_id not in self.rooms:
            return {"exists": False}
        return {
            "exists": True,
            "room_id": room_id,
            "peer_count": len(self.rooms[room_id]),
            "full": self.room_full(room_id),
        }


room_manager = RoomManager()


# ─── Helpers ──────────────────────────────────────────────────────────────────

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


# ─── REST Endpoints ────────────────────────────────────────────────────────────

@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Air Drawing API v2 running 🎨", "docs": "/docs"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


@app.post("/api/rooms")
def create_room() -> JSONResponse:
    """Create a new collaboration room and return its ID."""
    room_id = room_manager.create_room()
    return JSONResponse({"room_id": room_id}, status_code=201)


@app.get("/api/rooms/{room_id}")
def get_room(room_id: str) -> JSONResponse:
    info = room_manager.get_room_info(room_id)
    if not info["exists"]:
        return JSONResponse({"error": "Room not found"}, status_code=404)
    return JSONResponse(info)


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


# ─── Legacy Solo WebSocket ─────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    await websocket.send_json({
        "type": "welcome",
        "message": "Connected to Air Drawing WebSocket",
        "time": datetime.utcnow().isoformat(),
    })
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


# ─── Collaborative Room WebSocket ─────────────────────────────────────────────

@app.websocket("/ws/room/{room_id}")
async def room_websocket(websocket: WebSocket, room_id: str) -> None:
    """
    Collaborative room WebSocket.
    Handles:
      - stroke relay (draw events)
      - WebRTC signalling (offer / answer / ice-candidate)
      - clear canvas
      - undo
      - cursor position
    """
    user_id = uuid.uuid4().hex[:6]
    joined = await room_manager.join(room_id, websocket, user_id)
    if not joined:
        return

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "")

            # ── Drawing events ──────────────────────────────────────
            if msg_type == "stroke":
                # Save stroke for late-joiner sync
                if room_id in room_manager.room_strokes:
                    room_manager.room_strokes[room_id].append(data.get("stroke", {}))
                data["sender"] = user_id
                await room_manager.relay(room_id, websocket, data)

            elif msg_type == "clear":
                if room_id in room_manager.room_strokes:
                    room_manager.room_strokes[room_id] = []
                data["sender"] = user_id
                await room_manager.relay(room_id, websocket, data)

            elif msg_type == "undo":
                if room_id in room_manager.room_strokes and room_manager.room_strokes[room_id]:
                    room_manager.room_strokes[room_id].pop()
                data["sender"] = user_id
                await room_manager.relay(room_id, websocket, data)

            elif msg_type == "cursor":
                data["sender"] = user_id
                await room_manager.relay(room_id, websocket, data)

            # ── WebRTC signalling ───────────────────────────────────
            elif msg_type in ("offer", "answer", "ice-candidate"):
                data["sender"] = user_id
                await room_manager.relay(room_id, websocket, data)

            # ── Ping ────────────────────────────────────────────────
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong", "time": datetime.utcnow().isoformat()})

    except WebSocketDisconnect:
        room_manager.leave(room_id, websocket)
        await room_manager.broadcast_room(room_id, {
            "type": "peer_left",
            "peer_id": user_id,
        })
