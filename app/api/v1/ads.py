from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from pathlib import Path
import os
import shutil
import uuid
import json
from app.services.obs_service import obs_service
from app.core.ws_manager import ws_manager

router = APIRouter(prefix="/ads", tags=["Publicidad y Patrocinadores"])

STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"
UPLOAD_DIR = STATIC_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
SPONSORS_DB_PATH = DATA_DIR / "sponsors_library.json"

def _load_sponsors_db() -> list:
    if not SPONSORS_DB_PATH.exists():
        initial = [
            {
                "id": "sp_1",
                "title": "Patrocinador Oficial",
                "image_url": "",
                "type": "banner"
            }
        ]
        with open(SPONSORS_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(initial, f, ensure_ascii=False, indent=2)
        return initial

    try:
        with open(SPONSORS_DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def _save_sponsors_db(sponsors: list):
    with open(SPONSORS_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(sponsors, f, ensure_ascii=False, indent=2)

class BannerRequest(BaseModel):
    banner_id: Optional[str] = None
    title: Optional[str] = "Patrocinador"
    image_url: Optional[str] = ""
    duration: int = 10  # segundos en pantalla

@router.get("/library")
async def get_sponsors_library():
    """Devuelve la lista de sponsors y publicidades guardadas"""
    sponsors = _load_sponsors_db()
    return {"status": "ok", "sponsors": sponsors}

@router.post("/upload")
async def upload_sponsor(title: str = Form(...), type: str = Form("banner"), file: UploadFile = File(...)):
    """Sube la imagen o logo de un nuevo sponsor (PNG, JPG, WebP) y lo guarda en la biblioteca"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Archivo inválido")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ('.png', '.jpg', '.jpeg', '.webp', '.svg'):
        raise HTTPException(status_code=400, detail="Formato no soportado (usa PNG, JPG, WebP o SVG)")

    sponsor_id = f"sp_{uuid.uuid4().hex[:8]}"
    filename = f"sponsor_{sponsor_id}{ext}"
    filepath = UPLOAD_DIR / filename

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    image_url = f"/uploads/{filename}"
    new_sp = {
        "id": sponsor_id,
        "title": title,
        "image_url": image_url,
        "type": type
    }

    sponsors = _load_sponsors_db()
    sponsors.append(new_sp)
    _save_sponsors_db(sponsors)

    return {"status": "ok", "sponsor": new_sp}

@router.post("/delete")
async def delete_sponsor(sponsor_id: str):
    """Elimina un sponsor de la biblioteca"""
    sponsors = _load_sponsors_db()
    sponsors = [s for s in sponsors if s.get("id") != sponsor_id]
    _save_sponsors_db(sponsors)
    return {"status": "ok", "deleted_id": sponsor_id}

@router.post("/trigger")
async def trigger_banner(req: BannerRequest):
    """Muestra el banner de sponsor en pantalla en el overlay"""
    await ws_manager.broadcast("show_sponsor_banner", {
        "banner_id": req.banner_id,
        "title": req.title,
        "image_url": req.image_url,
        "duration": req.duration
    })
    return {"status": "ok", "title": req.title, "image_url": req.image_url, "duration": req.duration}

@router.post("/hide")
async def hide_banner():
    """Oculta el sponsor de la pantalla inmediatamente"""
    await ws_manager.broadcast("hide_sponsor_banner", {})
    return {"status": "ok"}
