from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from app.services.obs_service import obs_service
from app.core.ws_manager import ws_manager

router = APIRouter(prefix="/switcher", tags=["Switcher & Cameras"])

class SwitchSceneRequest(BaseModel):
    scene_name: str

@router.get("/scenes", response_model=List[str])
async def get_scenes():
    return obs_service.get_scenes()

@router.get("/health")
async def get_health():
    """Retorna estado en tiempo real de emisión, grabación y rendimiento de OBS"""
    return obs_service.get_stream_health()

@router.post("/switch")
async def switch_scene(req: SwitchSceneRequest):
    success = obs_service.switch_scene(req.scene_name)
    if success:
        await ws_manager.broadcast("scene_switched", {"current_scene": req.scene_name})
        return {"status": "ok", "scene": req.scene_name}
    return {"status": "error", "message": "No se pudo cambiar la escena"}

@router.post("/stream/toggle")
async def toggle_stream():
    """Inicia o detiene la transmisión en vivo en OBS"""
    res = obs_service.toggle_stream()
    return res

@router.post("/record/toggle")
async def toggle_record():
    """Inicia o detiene la grabación local en OBS"""
    res = obs_service.toggle_record()
    return res

@router.post("/replay")
async def trigger_replay(duration: int = 12):
    """Dispara el guardado de buffer de repetición y conmuta a la escena de Replay con auto-retorno"""
    res = obs_service.trigger_replay_buffer(auto_return_seconds=duration)
    return res
