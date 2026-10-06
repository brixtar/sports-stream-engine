import obsws_python as obs

cl = obs.ReqClient(host="127.0.0.1", port=4455, password="obs_password", timeout=3)
col_info = cl.get_scene_collection_list()
print("Colección actual:", getattr(col_info, 'current_scene_collection_name', 'N/A'))
print("Colecciones disponibles:", getattr(col_info, 'scene_collections', []))

sc_info = cl.get_scene_list()
print("Escena actual:", getattr(sc_info, 'current_program_scene_name', 'N/A'))
scenes = [s['sceneName'] for s in getattr(sc_info, 'scenes', [])]
print("Lista de escenas:", scenes)

for sc in scenes:
    items = cl.get_scene_item_list(sc).scene_items
    print(f"\nEscena '{sc}':")
    for it in items:
        source_name = it['sourceName']
        item_id = it['sceneItemId']
        enabled = it['sceneItemEnabled']
        print(f"  - Item ID: {item_id}, Source: '{source_name}', Enabled: {enabled}")
        try:
            settings = cl.get_input_settings(source_name)
            print(f"    Settings: {settings.input_settings}")
        except Exception:
            pass
