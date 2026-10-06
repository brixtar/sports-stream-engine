from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Body
from typing import List, Optional
from pathlib import Path
import os
import shutil
import uuid
import json
from app.api.v1.scoreboard import state as scoreboard_state, Player
from app.core.ws_manager import ws_manager

router = APIRouter(prefix="/teams", tags=["Teams and Logos"])

STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"
UPLOAD_DIR = STATIC_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
TEAMS_DB_PATH = DATA_DIR / "teams_library.json"

def _load_teams_db() -> list:
    if not TEAMS_DB_PATH.exists():
        # Crear equipos iniciales de ejemplo
        initial = [
            {
                "id": "team_1",
                "name": "EQUIPO LOCAL",
                "logo_url": "/uploads/default_local.png",
                "players": [
                    {"id": "p1", "number": 1, "name": "Arquero Titular", "is_starter": True, "position": "ARQ"},
                    {"id": "p2", "number": 2, "name": "Defensor Central", "is_starter": True, "position": "DEF"},
                    {"id": "p3", "number": 5, "name": "Mediocampista", "is_starter": True, "position": "MED"},
                    {"id": "p4", "number": 10, "name": "Delantero Estrella", "is_starter": True, "position": "DEL"},
                    {"id": "p5", "number": 18, "name": "Suplente Ingreso", "is_starter": False, "position": "DEL"},
                    {"id": "p6", "number": 22, "name": "Suplente Arquero", "is_starter": False, "position": "ARQ"}
                ]
            },
            {
                "id": "team_2",
                "name": "EQUIPO VISITANTE",
                "logo_url": "/uploads/default_visitante.png",
                "players": [
                    {"id": "p7", "number": 1, "name": "Arquero Rival", "is_starter": True, "position": "ARQ"},
                    {"id": "p8", "number": 4, "name": "Defensor Rival", "is_starter": True, "position": "DEF"},
                    {"id": "p9", "number": 8, "name": "Volante Rival", "is_starter": True, "position": "MED"},
                    {"id": "p10", "number": 9, "name": "Goleador Rival", "is_starter": True, "position": "DEL"},
                    {"id": "p11", "number": 14, "name": "Suplente Rival", "is_starter": False, "position": "MED"},
                    {"id": "p12", "number": 19, "name": "Delantero Banco", "is_starter": False, "position": "DEL"}
                ]
            }
        ]
        with open(TEAMS_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(initial, f, ensure_ascii=False, indent=2)
        return initial

    try:
        with open(TEAMS_DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def _save_teams_db(teams: list):
    with open(TEAMS_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(teams, f, ensure_ascii=False, indent=2)

@router.get("/library")
async def get_teams_library():
    """Devuelve todos los equipos guardados en la biblioteca"""
    teams = _load_teams_db()
    return {"status": "ok", "teams": teams}

@router.post("/library/save")
async def save_team_to_library(team_data: dict = Body(...)):
    """Crea o actualiza un equipo con su logo y lista de jugadores en la biblioteca"""
    teams = _load_teams_db()
    team_id = team_data.get("id")
    if not team_id:
        team_id = f"team_{uuid.uuid4().hex[:8]}"
        team_data["id"] = team_id

    # Buscar si ya existe para actualizar
    found = False
    for i, t in enumerate(teams):
        if t.get("id") == team_id:
            teams[i] = team_data
            found = True
            break
    if not found:
        teams.append(team_data)

    _save_teams_db(teams)
    return {"status": "ok", "team": team_data}

@router.post("/library/delete")
async def delete_team_from_library(team_id: str):
    """Elimina un equipo de la biblioteca"""
    teams = _load_teams_db()
    teams = [t for t in teams if t.get("id") != team_id]
    _save_teams_db(teams)
    return {"status": "ok", "deleted_id": team_id}

@router.post("/library/assign")
async def assign_team_from_library(team_id: str, role: str):
    """Asigna un equipo de la biblioteca al rol de LOCAL o VISITANTE en el partido activo"""
    teams = _load_teams_db()
    team = next((t for t in teams if t.get("id") == team_id), None)
    if not team:
        raise HTTPException(status_code=404, detail="Equipo no encontrado en la biblioteca")

    parsed_players = []
    for p in team.get("players", []):
        parsed_players.append(Player(
            id=str(p.get("id", uuid.uuid4().hex[:6])),
            number=int(p.get("number", 0)),
            name=str(p.get("name", "Jugador")),
            is_starter=bool(p.get("is_starter", True)),
            position=str(p.get("position", "JUG"))
        ))

    if role == "local":
        scoreboard_state.local_name = team.get("name", "LOCAL")
        scoreboard_state.local_logo = team.get("logo_url", "/uploads/default_local.png")
        if team.get("color"):
            scoreboard_state.local_color = team.get("color")
        scoreboard_state.local_players = parsed_players
    elif role == "visitante":
        scoreboard_state.visitante_name = team.get("name", "VISITANTE")
        scoreboard_state.visitante_logo = team.get("logo_url", "/uploads/default_visitante.png")
        if team.get("color"):
            scoreboard_state.visitante_color = team.get("color")
        scoreboard_state.visitante_players = parsed_players
    else:
        raise HTTPException(status_code=400, detail="Rol inválido (debe ser 'local' o 'visitante')")

    await ws_manager.broadcast("scoreboard_updated", scoreboard_state.model_dump())
    return {
        "status": "ok",
        "role": role,
        "team_name": team.get("name"),
        "team_color": team.get("color"),
        "players_count": len(parsed_players)
    }

@router.post("/upload_generic_logo")
async def upload_generic_logo(file: UploadFile = File(...)):
    """Sube una imagen de logo para un equipo y devuelve la URL"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Archivo inválido")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ('.png', '.jpg', '.jpeg', '.webp', '.svg'):
        raise HTTPException(status_code=400, detail="Formato no soportado (usa PNG, JPG, WebP o SVG)")

    filename = f"club_{uuid.uuid4().hex[:8]}{ext}"
    filepath = UPLOAD_DIR / filename
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"status": "ok", "url": f"/uploads/{filename}"}

@router.post("/upload_logo")
async def upload_team_logo(team: str = Form(...), file: UploadFile = File(...)):
    """Sube un logo y lo asigna inmediatamente al equipo en vivo"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Archivo inválido")
    
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ('.png', '.jpg', '.jpeg', '.webp', '.svg'):
        raise HTTPException(status_code=400, detail="Formato no soportado (usa PNG, JPG, WebP o SVG)")
    
    unique_id = uuid.uuid4().hex[:8]
    filename = f"logo_{team}_{unique_id}{ext}"
    filepath = UPLOAD_DIR / filename
    
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    web_url = f"/uploads/{filename}"
    if team == "local":
        scoreboard_state.local_logo = web_url
    elif team == "visitante":
        scoreboard_state.visitante_logo = web_url

    await ws_manager.broadcast("scoreboard_updated", scoreboard_state.model_dump())
    return {"status": "ok", "url": web_url, "team": team}

@router.post("/set_roster")
async def set_roster(team: str, players: List[dict] = Body(...)):
    """Guarda la lista de jugadores directamente para el equipo en vivo"""
    parsed_players = []
    for p in players:
        try:
            parsed_players.append(Player(**p))
        except Exception:
            parsed_players.append(Player(
                id=str(p.get("id", uuid.uuid4().hex[:6])),
                number=int(p.get("number", 0)),
                name=str(p.get("name", "Jugador")),
                is_starter=bool(p.get("is_starter", True)),
                position=str(p.get("position", "JUG"))
            ))
            
    if team == "local":
        scoreboard_state.local_players = parsed_players
    else:
        scoreboard_state.visitante_players = parsed_players
    
    await ws_manager.broadcast("scoreboard_updated", scoreboard_state.model_dump())
    return {"status": "ok", "team": team, "total": len(parsed_players)}
