from zeroconf import IPVersion, ServiceInfo, Zeroconf
import socket
import logging
from app.core.config import get_settings

logger = logging.getLogger("mDNSService")

class MDNSService:
    def __init__(self):
        self.settings = get_settings()
        self.zeroconf: Zeroconf | None = None
        self.service_info: ServiceInfo | None = None

    def _get_local_ip(self) -> str:
        # Intento 1: Conexión saliente rápida (funciona si hay gateway)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            if ip and not ip.startswith("127."):
                return ip
        except Exception:
            pass

        # Intento 2: Buscar en interfaces locales no-loopback
        try:
            hostname = socket.gethostname()
            for ip in socket.gethostbyname_ex(hostname)[2]:
                if not ip.startswith("127.") and not ip.startswith("169.254."):
                    return ip
        except Exception:
            pass

        return "127.0.0.1"

    def start(self):
        try:
            import os
            sport = os.getenv("SPORT_DEFAULT", "futbol").lower()
            port = int(os.getenv("APP_PORT", str(self.settings.APP_PORT)))
            local_ip = self._get_local_ip()
            logger.info(f"Iniciando anuncio mDNS en IP: {local_ip}:{port} ({sport})")
            
            self.zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
            svc_name = f"{self.settings.MDNS_SERVICE_NAME}_{sport}"
            self.service_info = ServiceInfo(
                type_=self.settings.MDNS_SERVICE_TYPE,
                name=f"{svc_name}.{self.settings.MDNS_SERVICE_TYPE}",
                addresses=[socket.inet_aton(local_ip)],
                port=port,
                properties={"app": "SportsStream", "sport": sport, "version": "2.0"},
                server=f"{sport}.local."
            )
            self.zeroconf.register_service(self.service_info)
            logger.info(f"mDNS activo: http://{sport}.local:{port}")
        except Exception as e:
            logger.warning(f"No se pudo iniciar mDNS: {e}")

    def stop(self):
        if self.zeroconf and self.service_info:
            try:
                logger.info("Deteniendo anuncio mDNS...")
                self.zeroconf.unregister_service(self.service_info)
                self.zeroconf.close()
            except Exception as e:
                logger.error(f"Error cerrando mDNS: {e}")

mdns_service = MDNSService()
