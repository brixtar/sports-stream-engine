import obsws_python as obs
import time
import sys

OBS_HOST = "127.0.0.1"
OBS_PORT = 4455
OBS_PASS = "obs_password"

def init_obs():
    print(f"[*] Conectando a OBS Studio en {OBS_HOST}:{OBS_PORT}...")
    try:
        cl = obs.ReqClient(host=OBS_HOST, port=OBS_PORT, timeout=3)
    except Exception:
        try:
            cl = obs.ReqClient(host=OBS_HOST, port=OBS_PORT, password=OBS_PASS, timeout=3)
        except Exception as e:
            print(f"[!] Error de conexión: {e}")
            return

    print("[+] Conexión establecida con éxito.")

    scenes_to_create = [
        "EN_VIVO_CAM_1",
        "EN_VIVO_CAM_2",
        "EN_VIVO_CAM_3",
        "REPETICION",
        "PUBLICIDAD_FULLSCREEN",
        "PANTALLA_ESPERA"
    ]

    for scene in scenes_to_create:
        try:
            cl.create_scene(sceneName=scene)
            print(f"  -> Escena creada: {scene}")
        except Exception:
            print(f"  -> Escena '{scene}' ya verificada.")

    # Agregar Browser Source Overlay a la Escena Principal
    try:
        cl.create_input(
            sceneName="EN_VIVO_CAM_1",
            inputName="OVERLAY_MARCADOR",
            inputKind="browser_source",
            inputSettings={
                "url": "http://127.0.0.1:8080/overlay/scoreboard.html",
                "width": 1920,
                "height": 1080,
                "fps": 60,
                "css": "body { background-color: rgba(0, 0, 0, 0); margin: 0px auto; overflow: hidden; }"
            },
            sceneItemEnabled=True
        )
        print("  -> Fuente Browser Source 'OVERLAY_MARCADOR' agregada con éxito a EN_VIVO_CAM_1.")
    except Exception as e:
        print(f"  -> Overlay: {e}")

    # Replay buffer
    try:
        cl.start_replay_buffer()
        print("[+] Replay buffer iniciado.")
    except Exception as e:
        print("  -> Nota Replay Buffer: Para activarlo, en OBS ve a Ajustes -> Salida -> Modo Avanzado -> Búfer de Repetición (Activar).")

    print("\n[✔] Configuración de OBS Studio completada con éxito.")

if __name__ == "__main__":
    init_obs()
