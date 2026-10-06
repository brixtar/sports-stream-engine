import obsws_python as obs
import time
import os
import json

OBS_HOST = "127.0.0.1"
OBS_PORT = 4455
OBS_PASS = "obs_password"

def get_client():
    try:
        return obs.ReqClient(host=OBS_HOST, port=OBS_PORT, password=OBS_PASS, timeout=3)
    except Exception:
        return obs.ReqClient(host=OBS_HOST, port=OBS_PORT, timeout=3)

def setup():
    print("[*] Conectando a OBS WebSocket...")
    cl = get_client()
    print("[+] Conectado con éxito.")

    # 1. PERFILES
    prof_data = cl.get_profile_list()
    existing_profiles = getattr(prof_data, 'profiles', [])
    print(f"Perfiles existentes: {existing_profiles}")

    for prof in ["Futbol", "Basquetbol"]:
        if prof not in existing_profiles:
            try:
                cl.create_profile(prof)
                print(f"[+] Perfil '{prof}' creado.")
            except Exception as e:
                print(f"[!] Error creando perfil '{prof}': {e}")
        else:
            print(f"[*] Perfil '{prof}' ya existe.")

    # 2. COLECCIONES DE ESCENAS
    col_data = cl.get_scene_collection_list()
    existing_cols = getattr(col_data, 'scene_collections', [])
    print(f"Colecciones existentes: {existing_cols}")

    collections = {
        "Futbol": [
            "FUTBOL_CAM_1",
            "FUTBOL_CAM_2",
            "FUTBOL_CAM_3",
            "REPETICION",
            "PUBLICIDAD_FULLSCREEN",
            "PANTALLA_ESPERA"
        ],
        "Basquetbol": [
            "BASQUET_CAM_1",
            "BASQUET_CAM_2",
            "BASQUET_CAM_3",
            "REPETICION",
            "PUBLICIDAD_FULLSCREEN",
            "PANTALLA_ESPERA"
        ]
    }

    for col_name, scenes in collections.items():
        try:
            cl = get_client()
        except Exception:
            pass

        if col_name not in existing_cols:
            try:
                cl.create_scene_collection(col_name)
                print(f"[+] Colección '{col_name}' creada.")
                time.sleep(2.0)
            except Exception as e:
                print(f"[!] Error creando colección '{col_name}': {e}")
        else:
            print(f"[*] Colección '{col_name}' ya existe.")
            try:
                cl.set_current_scene_collection(col_name)
            except Exception:
                pass
            time.sleep(2.0)

        # Reconectar tras cambio de colección
        try:
            cl = get_client()
        except Exception:
            time.sleep(1.0)
            cl = get_client()

        # Crear escenas en la colección activa
        for sc in scenes:
            try:
                cl.create_scene(sc)
                print(f"  -> Escena '{sc}' creada en '{col_name}'.")
            except Exception:
                pass

        # Agregar Browser Source Overlay a todas las escenas de cámara y repetición
        overlay_target_scenes = [s for s in scenes if ("_CAM_" in s or s == "REPETICION")]
        source_name = "OVERLAY_MARCADOR_FUTBOL" if col_name == "Futbol" else "OVERLAY_MARCADOR_BASQUET"
        overlay_url = "http://127.0.0.1:8080/overlay/scoreboard.html" if col_name == "Futbol" else "http://127.0.0.1:8081/overlay/scoreboard.html"

        for cam_scene in overlay_target_scenes:
            try:
                cl.create_input(
                    sceneName=cam_scene,
                    inputName=source_name,
                    inputKind="browser_source",
                    inputSettings={
                        "url": overlay_url,
                        "width": 1920,
                        "height": 1080,
                        "fps": 60,
                        "css": "body { background-color: rgba(0, 0, 0, 0); margin: 0px auto; overflow: hidden; }"
                    },
                    sceneItemEnabled=True
                )
                print(f"  -> Fuente '{source_name}' ({overlay_url}) agregada a '{cam_scene}'.")
            except Exception:
                try:
                    cl.create_scene_item(sceneName=cam_scene, sourceName=source_name, sceneItemEnabled=True)
                    print(f"  -> Fuente existente '{source_name}' vinculada a '{cam_scene}'.")
                except Exception:
                    pass

    # Dejar seleccionado Fútbol por defecto
    try:
        cl = get_client()
        cl.set_current_profile("Futbol")
        try:
            cl.set_current_scene_collection("Futbol")
        except Exception:
            pass
        time.sleep(1.5)
        cl = get_client()
        cl.set_current_program_scene("FUTBOL_CAM_1")
    except Exception as e:
        print("Set default error:", e)

    print("\n[✔] Perfiles y Colecciones de Escenas configurados en OBS Studio.")

if __name__ == "__main__":
    setup()
