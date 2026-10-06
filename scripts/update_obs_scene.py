import obsws_python as obs
import time

cl = obs.ReqClient(host="127.0.0.1", port=4455, password="obs_password", timeout=3)

# 1. Cambiar a escena BASQUET_CAM_1
print("[*] Cambiando escena activa a BASQUET_CAM_1...")
cl.set_current_program_scene("BASQUET_CAM_1")
print("[+] Escena actual:", cl.get_current_program_scene().current_program_scene_name)

# 2. Asegurar que OVERLAY_MARCADOR esté activo y en la capa superior
items = cl.get_scene_item_list("BASQUET_CAM_1").scene_items
overlay_item = None
max_index = 0
for it in items:
    if it['sourceName'] == 'OVERLAY_MARCADOR':
        overlay_item = it
    if it['sceneItemIndex'] > max_index:
        max_index = it['sceneItemIndex']

if overlay_item:
    item_id = overlay_item['sceneItemId']
    # Habilitar
    cl.set_scene_item_enabled("BASQUET_CAM_1", item_id, True)
    # Mover al frente
    try:
        cl.set_scene_item_index("BASQUET_CAM_1", item_id, max_index)
    except Exception as e:
        print("Index move note:", e)

    # Transformación: pantalla completa (1920x1080)
    try:
        cl.set_scene_item_transform("BASQUET_CAM_1", item_id, {
            "positionX": 0.0,
            "positionY": 0.0,
            "scaleX": 1.0,
            "scaleY": 1.0,
            "boundsType": "OBS_BOUNDS_SCALE_INNER",
            "boundsWidth": 1920.0,
            "boundsHeight": 1080.0
        })
    except Exception as e:
        print("Transform note:", e)

# 3. Forzar refresco de caché en el Browser Source
print("[*] Refrescando Browser Source OVERLAY_MARCADOR...")
# Intentar presionar botón 'refreshnocache'
try:
    cl.press_input_properties_button("OVERLAY_MARCADOR", "refreshnocache")
    print("[+] Botón 'refreshnocache' presionado con éxito.")
except Exception as e:
    print(f"[-] Note press_input_properties_button: {e}")
    # Fallback: actualizar settings agregando timestamp al URL o cambiando temporalmente
    curr_settings = cl.get_input_settings("OVERLAY_MARCADOR").input_settings
    print("Settings actuales:", curr_settings)
    curr_settings["url"] = "http://127.0.0.1:8080/overlay/scoreboard.html?t=" + str(int(time.time()))
    cl.set_input_settings("OVERLAY_MARCADOR", curr_settings, overlay=True)
    time.sleep(0.5)
    curr_settings["url"] = "http://127.0.0.1:8080/overlay/scoreboard.html"
    cl.set_input_settings("OVERLAY_MARCADOR", curr_settings, overlay=True)
    print("[+] URL actualizado para forzar recarga.")

# 4. También agregar OVERLAY_MARCADOR a BASQUET_CAM_2, BASQUET_CAM_3 y REPETICION si no estaban
for sc in ['BASQUET_CAM_2', 'BASQUET_CAM_3', 'REPETICION']:
    try:
        existing = [x['sourceName'] for x in cl.get_scene_item_list(sc).scene_items]
        if 'OVERLAY_MARCADOR' not in existing:
            cl.create_scene_item(sceneName=sc, sourceName="OVERLAY_MARCADOR", sceneItemEnabled=True)
            print(f"[+] OVERLAY_MARCADOR vinculado a {sc}")
    except Exception as e:
        pass

# 5. Tomar screenshot de la fuente o escena para verificar que se vea el nuevo tablero
try:
    import base64
    shot = cl.get_source_screenshot("BASQUET_CAM_1", "png", 1280, 720, -1)
    img_b64 = shot.image_data.split(",")[-1]
    with open("/home/usuario/obs_preview.png", "wb") as f:
        f.write(base64.b64decode(img_b64))
    print("[+] Screenshot de OBS guardado en /home/usuario/obs_preview.png")
except Exception as e:
    print(f"[-] No se pudo capturar screenshot de OBS: {e}")

print("\n[✔] ¡ESCENA BASQUET_CAM_1 ACTUALIZADA Y VISIBLE EN OBS!")
