import obsws_python as obs
import logging
from typing import Optional, Dict, Any, List
from app.core.config import get_settings

import time

logger = logging.getLogger("OBSService")

class OBSService:
    def __init__(self):
        self.settings = get_settings()
        self.client: Optional[obs.ReqClient] = None
        self.is_connected: bool = False
        self._last_attempt_time: float = 0.0
        self._attempt_cooldown: float = 8.0

    def connect(self) -> bool:
        """Conecta con el servidor WebSocket v5 de OBS Studio con fallback de autenticación"""
        self._last_attempt_time = time.time()
        try:
            # Primero intentar con contraseña si está configurada
            if self.settings.OBS_PASSWORD:
                try:
                    self.client = obs.ReqClient(
                        host=self.settings.OBS_HOST,
                        port=self.settings.OBS_PORT,
                        password=self.settings.OBS_PASSWORD,
                        timeout=2
                    )
                except Exception:
                    # Fallback sin contraseña por si OBS tiene autenticación desactivada
                    self.client = obs.ReqClient(
                        host=self.settings.OBS_HOST,
                        port=self.settings.OBS_PORT,
                        timeout=2
                    )
            else:
                self.client = obs.ReqClient(
                    host=self.settings.OBS_HOST,
                    port=self.settings.OBS_PORT,
                    timeout=2
                )

            version_info = self.client.get_version()
            self.is_connected = True
            logger.info(f"Conectado exitosamente a OBS Studio v{version_info.obs_version} (WS v{version_info.obs_web_socket_version})")
            return True
        except Exception as e:
            self.is_connected = False
            self.client = None
            logger.warning(f"No se pudo conectar a OBS WebSocket ({self.settings.OBS_HOST}:{self.settings.OBS_PORT}): {e}")
            return False

    def ensure_connected(self) -> bool:
        if not self.is_connected or not self.client:
            now = time.time()
            if now - self._last_attempt_time < self._attempt_cooldown:
                return False
            return self.connect()
        return True

    def get_scenes(self) -> List[str]:
        if not self.ensure_connected():
            return []
        try:
            res = self.client.get_scene_list()
            scenes = []
            raw_scenes = getattr(res, "scenes", [])
            for s in raw_scenes:
                if isinstance(s, dict):
                    name = s.get("sceneName") or s.get("scene_name")
                else:
                    name = getattr(s, "scene_name", getattr(s, "sceneName", str(s)))
                if name:
                    scenes.append(name)
            return scenes
        except Exception as e:
            self.is_connected = False
            self.client = None
            logger.error(f"Error obteniendo lista de escenas: {e}")
            return []

    def switch_scene(self, scene_name: str) -> bool:
        if not self.ensure_connected():
            return False
        try:
            available = self.get_scenes()
            target = scene_name
            if scene_name not in available:
                # Mapeo inteligente entre prefijos de nombres de escenas
                if ("FUTBOL_CAM_" in scene_name or "BASQUET_CAM_" in scene_name):
                    cam_suffix = scene_name[-1]
                    candidate = f"EN_VIVO_CAM_{cam_suffix}"
                    if candidate in available:
                        target = candidate
                elif "EN_VIVO_CAM_" in scene_name:
                    cam_suffix = scene_name[-1]
                    for pfx in ["FUTBOL_CAM_", "BASQUET_CAM_"]:
                        candidate = f"{pfx}{cam_suffix}"
                        if candidate in available:
                            target = candidate
                            break

            self.client.set_current_program_scene(target)
            logger.info(f"Escena cambiada a: {target}")
            return True
        except Exception as e:
            self.is_connected = False
            self.client = None
            logger.error(f"Error cambiando a escena '{scene_name}': {e}")
            return False

    def set_source_visibility(self, scene_name: str, scene_item_id: int, visible: bool) -> bool:
        if not self.ensure_connected():
            return False
        try:
            self.client.set_scene_item_enabled(scene_name, scene_item_id, visible)
            return True
        except Exception as e:
            self.is_connected = False
            self.client = None
            logger.error(f"Error cambiando visibilidad en escena {scene_name} (item {scene_item_id}): {e}")
            return False

    def set_input_mute(self, input_name: str, muted: bool) -> bool:
        if not self.ensure_connected():
            return False
        try:
            self.client.set_input_mute(input_name, muted)
            return True
        except Exception as e:
            self.is_connected = False
            self.client = None
            logger.error(f"Error muteando entrada de audio '{input_name}': {e}")
            return False

    def get_current_program_scene(self) -> Optional[str]:
        if not self.ensure_connected():
            return None
        try:
            res = self.client.get_current_program_scene()
            if hasattr(res, "current_program_scene_name"):
                return res.current_program_scene_name
            elif hasattr(res, "scene_name"):
                return res.scene_name
            return str(res)
        except Exception as e:
            logger.warning(f"Error obteniendo escena de programa actual: {e}")
            return None

    def trigger_replay_buffer(self, auto_return_seconds: int = 12) -> Dict[str, Any]:
        """
        1. Guarda la escena previa en vivo.
        2. Guarda el búfer de repetición activo (últimos N segundos).
        3. Conmuta a la escena de Repetición.
        4. Si auto_return_seconds > 0, programa el regreso automático a la escena previa.
        """
        if not self.ensure_connected():
            return {"success": False, "error": "OBS no conectado"}
        
        try:
            prev_scene = self.get_current_program_scene()
            try:
                self.client.save_replay_buffer()
            except Exception as e_replay:
                logger.warning(f"Aviso Replay Buffer (¿está activo en OBS?): {e_replay}")

            if self.settings.MIC_SOURCE_NAME:
                self.set_input_mute(self.settings.MIC_SOURCE_NAME, True)
            
            self.switch_scene(self.settings.REPLAY_SCENE_NAME)

            if auto_return_seconds > 0 and prev_scene and prev_scene != self.settings.REPLAY_SCENE_NAME:
                import threading
                def _auto_return():
                    import time
                    time.sleep(auto_return_seconds)
                    self.switch_scene(prev_scene)
                    if self.settings.MIC_SOURCE_NAME:
                        self.set_input_mute(self.settings.MIC_SOURCE_NAME, False)
                    logger.info(f"Auto-retorno de Replay a escena previa: {prev_scene}")
                
                t = threading.Thread(target=_auto_return, daemon=True)
                t.start()

            return {
                "success": True, 
                "message": f"Replay disparado. Regreso automático a '{prev_scene}' en {auto_return_seconds}s",
                "auto_return_seconds": auto_return_seconds,
                "prev_scene": prev_scene
            }
        except Exception as e:
            self.is_connected = False
            self.client = None
            logger.error(f"Error al disparar Instant Replay: {e}")
            return {"success": False, "error": str(e)}

    def get_stream_health(self) -> Dict[str, Any]:
        """Obtiene métricas en tiempo real de transmisión, grabación y rendimiento de OBS"""
        if not self.ensure_connected():
            return {
                "connected": False,
                "streaming": False,
                "recording": False,
                "recording_paused": False,
                "stream_timecode": "00:00:00",
                "record_timecode": "00:00:00",
                "bitrate_kbps": 0,
                "fps": 0.0,
                "cpu_usage": 0.0,
                "memory_mb": 0.0,
                "dropped_frames": 0,
                "total_frames": 0,
                "dropped_pct": 0.0
            }

        try:
            # 1. Stream status
            st_active = False
            st_timecode = "00:00:00"
            st_bytes = 0
            st_duration = 0
            try:
                st = self.client.get_stream_status()
                st_active = bool(getattr(st, "output_active", False))
                st_timecode = getattr(st, "output_timecode", "00:00:00")
                st_bytes = getattr(st, "output_bytes", 0)
                st_duration = getattr(st, "output_duration", 0)
            except Exception:
                pass

            # 2. Record status
            rec_active = False
            rec_paused = False
            rec_timecode = "00:00:00"
            try:
                rec = self.client.get_record_status()
                rec_active = bool(getattr(rec, "output_active", False))
                rec_paused = bool(getattr(rec, "output_paused", False))
                rec_timecode = getattr(rec, "output_timecode", "00:00:00")
            except Exception:
                pass

            # 3. Performance stats
            fps = 60.0
            cpu = 0.0
            mem = 0.0
            dropped = 0
            total = 0
            try:
                stats = self.client.get_stats()
                fps = round(float(getattr(stats, "active_fps", 60.0)), 1)
                cpu = round(float(getattr(stats, "cpu_usage", 0.0)), 1)
                mem = round(float(getattr(stats, "memory_usage", 0.0)), 1)
                dropped = int(getattr(stats, "output_skipped_frames", 0))
                total = int(getattr(stats, "output_total_frames", 0))
            except Exception:
                pass

            # Calcular bitrate aproximado si hay duración
            bitrate_kbps = 0
            if st_active and st_duration > 0 and st_bytes > 0:
                bitrate_kbps = int((st_bytes * 8) / (st_duration / 1000) / 1000)

            dropped_pct = round((dropped / total * 100), 2) if total > 0 else 0.0

            return {
                "connected": True,
                "streaming": st_active,
                "recording": rec_active,
                "recording_paused": rec_paused,
                "stream_timecode": st_timecode,
                "record_timecode": rec_timecode,
                "bitrate_kbps": bitrate_kbps,
                "fps": fps,
                "cpu_usage": cpu,
                "memory_mb": mem,
                "dropped_frames": dropped,
                "total_frames": total,
                "dropped_pct": dropped_pct
            }
        except Exception as e:
            logger.warning(f"Error consultando stream health de OBS: {e}")
            return {"connected": False, "error": str(e)}

    def toggle_stream(self) -> Dict[str, Any]:
        if not self.ensure_connected():
            return {"success": False, "error": "OBS no conectado"}
        try:
            res = self.client.toggle_stream()
            active = getattr(res, "output_active", False)
            return {"success": True, "output_active": active}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def toggle_record(self) -> Dict[str, Any]:
        if not self.ensure_connected():
            return {"success": False, "error": "OBS no conectado"}
        try:
            res = self.client.toggle_record()
            active = getattr(res, "output_active", False)
            return {"success": True, "output_active": active}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def set_profile(self, profile_name: str) -> bool:
        """Cambia el perfil activo en OBS Studio"""
        if not self.ensure_connected():
            return False
        try:
            self.client.set_current_profile(profile_name)
            logger.info(f"Perfil de OBS cambiado a: {profile_name}")
            return True
        except Exception as e:
            logger.warning(f"No se pudo cambiar al perfil de OBS '{profile_name}': {e}")
            return False

    def set_scene_collection(self, collection_name: str) -> bool:
        """Cambia la colección de escenas activa en OBS Studio"""
        if not self.ensure_connected():
            return False
        try:
            self.client.set_current_scene_collection(collection_name)
            logger.info(f"Colección de escenas de OBS cambiada a: {collection_name}")
            return True
        except Exception as e:
            logger.warning(f"No se pudo cambiar la colección de escenas a '{collection_name}': {e}")
            return False

obs_service = OBSService()

