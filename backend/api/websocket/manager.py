import json
import time
import logging
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: set[WebSocket] = set()
        self._log_subscribers: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WS client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        self._log_subscribers.discard(websocket)
        logger.info(f"WS client disconnected. Total: {len(self.active_connections)}")

    def subscribe_logs(self, websocket: WebSocket):
        self._log_subscribers.add(websocket)

    def unsubscribe_logs(self, websocket: WebSocket):
        self._log_subscribers.discard(websocket)

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
        data = json.dumps(message, default=str)
        disconnected = set()
        for ws in list(self.active_connections):
            try:
                await ws.send_text(data)
            except Exception:
                disconnected.add(ws)
        for ws in disconnected:
            self.disconnect(ws)

    async def broadcast_event(self, event_type: str, data: dict | list):
        await self.broadcast({
            "type": event_type,
            "data": data,
            "timestamp": time.time(),
        })

    async def broadcast_log(self, level: str, message: str):
        if not self._log_subscribers:
            return
        payload = json.dumps({
            "type": "log_line",
            "data": {"level": level, "message": message, "timestamp": time.time()},
        }, default=str)
        disconnected = set()
        for ws in list(self._log_subscribers):
            try:
                await ws.send_text(payload)
            except Exception:
                disconnected.add(ws)
        for ws in disconnected:
            self.disconnect(ws)
