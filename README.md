# Sports Stream Engine - Motor de Marcadores Deportivos y Automatización para OBS Studio

Sistema backend y panel web desarrollado en **Python (FastAPI)** para la gestión y actualización en tiempo real de marcadores deportivos, grafismos y overlays interactivos en transmisiones en vivo mediante **OBS Studio (WebSocket v5)**.

Diseñado para operadores de streaming en producciones deportivas locales, torneos de fútbol, básquetbol y vóley.

## ⚡ Características Principales

- **Integración Nativa con OBS Studio:** Control directo de fuentes, textos, escenas y visibilidad mediante el protocolo `obsws-python` (OBS WebSocket 5.x).
- **Servidor FastAPI & WebSockets:** Comunicación bidireccional de bajísima latencia para actualizar tanteador, tiempos, faltas y tarjetas al instante.
- **Detección Automática de Red (Zeroconf / mDNS):** Autodescubrimiento en la red local y generación de código QR para operar la mesa de control desde dispositivos móviles.
- **Overlays Gráficos para Transmisión:** Vistas web HTML5/CSS3 listas para incrustar como fuentes de navegador (Browser Source) en OBS.
- **Mando Dual y Operación Remota:** Soporte para múltiples operadores en simultáneo (relojero y anotador de incidencias).

## 🛠️ Tecnologías

- **Lenguaje:** Python 3.10+
- **Framework Web:** FastAPI + Uvicorn
- **Integración OBS:** `obsws-python` (WebSocket API v5)
- **Tiempo Real:** WebSockets (`websockets`)
- **Red & Descubrimiento:** `zeroconf`, `qrcode`
- **Configuración:** Pydantic Settings & `python-dotenv`

## 📂 Estructura del Proyecto

```
sports-stream-engine/
├── app/
│   ├── main.py              # Punto de entrada FastAPI y rutas REST / WS
│   ├── api/                 # Endpoints de marcadores, partidos y configuración
│   ├── core/                # Lógica del motor, conexión OBS y estado
│   ├── services/            # Servicios de streaming y sincronización
│   ├── static/              # Overlays HTML/CSS/JS y panel de control móvil
│   └── data/                # Almacenamiento local de configuraciones
├── scripts/                 # Scripts de prueba y automatización
├── INICIAR_STREAM_MASTER.bat # Lanzador de producción para Windows
├── requirements.txt         # Dependencias del proyecto
└── .env.example             # Plantilla de variables de entorno
```

## 🚀 Instalación y Puesta en Marcha

1. Clonar el repositorio y crear un entorno virtual:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # En Windows
   pip install -r requirements.txt
   ```
2. Copiar `.env.example` a `.env` y configurar los datos de tu OBS:
   ```bash
   copy .env.example .env
   ```
3. Iniciar el motor:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   O ejecutar el archivo `INICIAR_STREAM_MASTER.bat`.
