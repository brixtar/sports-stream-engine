import obsws_python as obs
import sys

OBS_HOST = "127.0.0.1"
OBS_PORT = 4455
OBS_PASS = "obs_password"

def configure_max_quality():
    print("=" * 60)
    print("  🚀 OPTIMIZADOR DE CALIDAD DE TRANSMISIÓN OBS STUDIO")
    print("=" * 60)
    print(f"[*] Conectando a OBS Studio en {OBS_HOST}:{OBS_PORT}...")
    
    cl = None
    try:
        cl = obs.ReqClient(host=OBS_HOST, port=OBS_PORT, timeout=3)
    except Exception:
        try:
            cl = obs.ReqClient(host=OBS_HOST, port=OBS_PORT, password=OBS_PASS, timeout=3)
        except Exception as e:
            print(f"[!] No se pudo conectar a OBS Studio: {e}")
            print("    -> Abre OBS Studio.")
            print("    -> En el menú superior: Herramientas -> Configuración del servidor WebSocket.")
            print("    -> Activa 'Habilitar el servidor WebSocket' (Puerto 4455).")
            return

    print("[+] Conectado a OBS Studio con éxito.")

    # 1. Configuración de Video (1080p 60 FPS)
    try:
        cl.set_video_settings(
            fps_numerator=60,
            fps_denominator=1,
            base_width=1920,
            base_height=1080,
            output_width=1920,
            output_height=1080
        )
        print("  [✔] Resolución configurada: 1920x1080 Full HD a 60 FPS reales.")
    except Exception as e:
        print(f"  [!] Ajuste de video: {e}")

    # 2. Informar parámetros recomendados para la máxima nitidez
    print("\n" + "=" * 60)
    print("  ⭐ PARÁMETROS DE EMISIÓN DE MÁXIMA CALIDAD (BROADCAST):")
    print("=" * 60)
    print("  1. Bitrate de Video:       6500 a 8000 Kbps (Máxima nitidez para deportes rápidos)")
    print("  2. Control de Frecuencia:  CBR (Constant Bitrate)")
    print("  3. Intervalo Fotogramas:   2 segundos (Obligatorio para YouTube / Twitch / FB)")
    print("  4. Codificador:            NVIDIA NVENC H.264 (o x264 'veryfast' si no hay GPU dedicada)")
    print("  5. Perfil (Profile):       High")
    print("  6. Audio Bitrate:          192 Kbps / 320 Kbps Stereo")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    configure_max_quality()
