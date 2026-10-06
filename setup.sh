#!/usr/bin/env bash
# ==============================================================================
# Sports Stream OBS Engine - Instalador y Auto-Configuración en Ubuntu Linux
# ==============================================================================
set -e

echo "=== [1/5] Instalando dependencias del sistema y Avahi mDNS ==="
sudo apt update
sudo apt install -y python3 python3-pip python3-venv avahi-daemon libnss-mdns git

echo "=== [2/5] Habilitando mDNS y Firewall ==="
sudo systemctl enable --now avahi-daemon
sudo ufw allow 8080/tcp || true
sudo ufw allow 5353/udp || true

echo "=== [3/5] Creando entorno virtual de Python e instalando librerías ==="
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

echo "=== [4/5] Creando servicio systemd para inicio automático ==="
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CURRENT_USER=$(whoami)

sudo bash -c "cat > /etc/systemd/system/sports-stream.service <<EOF
[Unit]
Description=Sports Stream OBS Engine Server
After=network.target avahi-daemon.service

[Service]
Type=simple
User=${CURRENT_USER}
WorkingDirectory=${PROJECT_DIR}
ExecStart=${PROJECT_DIR}/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF"

sudo systemctl daemon-reload
sudo systemctl enable sports-stream.service
sudo systemctl restart sports-stream.service

echo "=== [5/5] Inicializando escenas en OBS Studio ==="
python3 scripts/init_obs_scenes.py || echo "[!] Si OBS no estaba abierto, ejecuta luego: python3 scripts/init_obs_scenes.py"

echo ""
echo "=================================================================="
echo " ¡INSTALACIÓN COMPLETADA CON ÉXITO!"
echo " -> Panel de Control Web: http://streamcontrol.local:8080"
echo " -> O ingresa por IP:    http://$(hostname -I | awk '{print \$1}'):8080"
echo " -> Fuente OBS Overlay:  http://127.0.0.1:8080/overlay/scoreboard.html"
echo "=================================================================="
