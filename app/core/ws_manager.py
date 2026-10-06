from fastapi import WebSocket
from typing import List, Dict, Any
import json
import logging

logger = logging.getLogger("WSManager")

class ConnectionManager:
    """Administrador centralizado de WebSockets para sincronizar dispositivos en tiempo real"""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Cliente conectado. Dispositivos activos: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Cliente desconectado. Dispositivos activos: {len(self.active_connections)}")

    async def broadcast(self, topic: str, payload: Dict[str, Any]):
        """Envía eventos JSON {topic: str, data: dict} a todos los clientes y fuentes de OBS conectadas"""
        if not self.active_connections:
            return
        
        message = json.dumps({"topic": topic, "data": payload})
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Error al enviar mensaje a cliente WS: {e}")
                self.disconnect(connection)

ws_manager = ConnectionManager()
