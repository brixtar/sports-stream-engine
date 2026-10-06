from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import socket
from app.services.obs_service import obs_service
from app.core.ws_manager import ws_manager
from app.core.config import get_settings

router = APIRouter(prefix="/system", tags=["System & Controls"])

class BitrateAdjustRequest(BaseModel):
    target_bitrate_kbps: int

def get_local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

@router.get("/network-info")
async def get_network_info():
    """Retorna la IP local de la máquina y enlaces para conectar celulares en la misma red WiFi"""
    settings = get_settings()
    ip = get_local_ip()
    port = settings.APP_PORT
    return {
        "status": "ok",
        "local_ip": ip,
        "port": port,
        "remote_control_url": f"http://{ip}:{port}",
        "mdns_url": f"http://streamcontrol.local:{port}",
        "overlay_url": f"http://127.0.0.1:{port}/overlay/scoreboard.html",
        "obs_connected": obs_service.is_connected
    }

@router.post("/obs/reconnect")
async def reconnect_obs():
    """Intenta reconectar con el WebSocket de OBS Studio"""
    success = obs_service.connect()
    scenes = obs_service.get_scenes() if success else []
    return {
        "status": "ok" if success else "error",
        "connected": success,
        "scenes": scenes,
        "message": "Conectado a OBS Studio con éxito" if success else "No se pudo conectar a OBS. Asegúrate de que OBS esté abierto con Herramientas -> Configuración del servidor WebSocket activo en el puerto 4455."
    }

@router.post("/replay")
async def trigger_replay():
    """Dispara el búfer de repetición de OBS y conmuta a la escena de replay"""
    res = obs_service.trigger_replay_buffer()
    await ws_manager.broadcast("replay_triggered", res)
    return res

@router.post("/bitrate/dynamic-hook")
async def dynamic_bitrate_hook(req: BitrateAdjustRequest):
    """
    Hook preparado para scripts de monitoreo de red en Linux
    Ajusta el bitrate dinámicamente según la congestión de la red
    """
    await ws_manager.broadcast("bitrate_adjusted", {"bitrate": req.target_bitrate_kbps})
    return {"status": "ok", "bitrate_applied": req.target_bitrate_kbps}

