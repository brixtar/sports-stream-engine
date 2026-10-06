@echo off
chcp 65001 >nul
title STREAM MASTER STUDIO PRO - CONTROL DEPORTIVO
color 0B

echo ======================================================================
echo    🚀 INICIANDO STREAM MASTER STUDIO PRO (SERVIDOR + OBS CONNECTOR)
echo ======================================================================
echo.

cd /d "%~dp0"

echo [*] Verificando entorno de Python y dependencias...
python -m pip install -r requirements.txt >nul 2>&1

echo [*] Obteniendo dirección IP local para conectar celulares...
python scripts/show_qr.py

echo.
echo [*] Configurando perfiles, escenas y máxima calidad en OBS Studio...
python scripts/setup_obs_profiles.py
python scripts/configurar_calidad_maxima_obs.py

echo.
echo [*] Abriendo paneles de control en tu navegador...
start http://localhost:8080
start http://localhost:8081

echo.
echo ======================================================================
echo  [✔] SERVICIOS ACTIVOS Y DESACOPLADOS:
echo      ⚽ FÚTBOL:     http://localhost:8080  (Overlay OBS: :8080/overlay/scoreboard.html)
echo      🏀 BÁSQUETBOL: http://localhost:8081  (Overlay OBS: :8081/overlay/scoreboard.html)
echo  📱 Conecta cualquier celular a la red WiFi y abre cualquiera de los enlaces.
echo  ⚠️  NO CIERRES ESTA VENTANA MIENTRAS TRANSMITAS O CONTROLES EL PARTIDO.
echo ======================================================================
echo.

python run_dual_servers.py
pause
