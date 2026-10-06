from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "Sports Stream OBS Engine"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8080
    
    # OBS WebSocket v5 Config
    OBS_HOST: str = "127.0.0.1"
    OBS_PORT: int = 4455
    OBS_PASSWORD: str = "obs_password"
    
    # mDNS Service Discovery
    MDNS_SERVICE_NAME: str = "SportsStreamEngine"
    MDNS_SERVICE_TYPE: str = "_http._tcp.local."
    MDNS_HOSTNAME: str = "streamcontrol.local."

    # Configuración de repetición y audio
    REPLAY_SCENE_NAME: str = "REPETICION"
    MIC_SOURCE_NAME: str = "Mic/Aux"
    REPLAY_CLIP_DURATION: int = 15

    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
