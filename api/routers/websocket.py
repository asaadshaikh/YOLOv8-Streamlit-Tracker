"""
WebSocket endpoints for real-time updates
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import json
import asyncio

from services.detection_service import DetectionService
from utils.logger import logger

router = APIRouter(tags=["websocket"])

# Store active connections
active_connections: List[WebSocket] = []

detection_service = DetectionService()


class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                self.disconnect(connection)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "ping":
                    await manager.send_personal_message(
                        json.dumps({"type": "pong"}),
                        websocket
                    )
                elif message_type == "subscribe":
                    # Subscribe to job updates
                    task_id = message.get("task_id")
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "subscribed",
                            "task_id": task_id
                        }),
                        websocket
                    )
                else:
                    await manager.send_personal_message(
                        json.dumps({"type": "error", "message": "Unknown message type"}),
                        websocket
                    )
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    json.dumps({"type": "error", "message": "Invalid JSON"}),
                    websocket
                )
    except WebSocketDisconnect:
        manager.disconnect(websocket)

