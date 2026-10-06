from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path
import asyncio
import logging
import os

from app.core.config import get_settings
from app.core.ws_manager import ws_manager
from app.services.obs_service import obs_service
from app.services.mdns_service import mdns_service
from app.api.v1.scoreboard import router as scoreboard_router
import app.api.v1.scoreboard as sb_module
from app.api.v1.switcher import router as switcher_router
from app.api.v1.ads import router as ads_router
from app.api.v1.system import router as system_router
from app.api.v1.teams import router as teams_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("SportsStreamServer")

settings = get_settings()

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = STATIC_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

async def scoreboard_timer_loop():
    """Timer en segundo plano con soporte para conteo ascendente (fútbol), regresivo (básquet) y reloj de posesión (Shot Clock 24s/14s)"""
    while True:
        await asyncio.sleep(1)
        state_changed = False
        cur_state = sb_module.state
        
        # 1. Reloj Principal de Juego
        if cur_state.timer_running:
            if cur_state.sport == "basquet":
                if cur_state.timer_seconds > 0:
                    cur_state.timer_seconds -= 1
                else:
                    cur_state.timer_running = False
                    state_changed = True
                    await ws_manager.broadcast("play_sound_cue", {"cue_type": "buzzer"})
            else: # Fútbol
                cur_state.timer_seconds += 1

        # 2. Reloj de Posesión (Shot Clock de Básquetbol)
        if cur_state.sport == "basquet" and cur_state.shot_clock_running:
            if cur_state.shot_clock_seconds > 0:
                cur_state.shot_clock_seconds -= 1
                if cur_state.shot_clock_seconds == 0:
                    cur_state.shot_clock_running = False
                    state_changed = True
                    # Disparar chicharra de fin de posesión automáticamente
                    await ws_manager.broadcast("play_sound_cue", {"cue_type": "buzzer"})
            else:
                cur_state.shot_clock_running = False

        if state_changed:
            await ws_manager.broadcast("scoreboard_updated", cur_state.model_dump())

        if cur_state.timer_running or (cur_state.sport == "basquet" and cur_state.shot_clock_running):
            await ws_manager.broadcast("scoreboard_timer_tick", {
                "timer_seconds": cur_state.timer_seconds,
                "timer_running": cur_state.timer_running,
                "shot_clock_seconds": cur_state.shot_clock_seconds,
                "shot_clock_running": cur_state.shot_clock_running
            })

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando Sports Stream Engine v2.0...")
    mdns_service.start()
    obs_service.connect()
    timer_task = asyncio.create_task(scoreboard_timer_loop())
    yield
    logger.info("Cerrando Sports Stream Engine...")
    timer_task.cancel()
    mdns_service.stop()

app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar Routers de la API
app.include_router(scoreboard_router, prefix="/api/v1")
app.include_router(teams_router, prefix="/api/v1")
app.include_router(switcher_router, prefix="/api/v1")
app.include_router(ads_router, prefix="/api/v1")
app.include_router(system_router, prefix="/api/v1")

# WebSocket Endpoint para sincronización en tiempo real
@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        # Enviar estado completo inmediatamente al conectar
        await websocket.send_json({"topic": "init_state", "data": sb_module.state.model_dump()})
        while True:
            msg = await websocket.receive_json()
            topic = msg.get("topic")
            payload = msg.get("data", {})
            if topic:
                await ws_manager.broadcast(topic, payload)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"Conexión WebSocket cerrada: {e}")
        ws_manager.disconnect(websocket)

# Montar frontend estático, uploads y directorio static para máxima compatibilidad
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static_dir")
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static_root")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=True)

