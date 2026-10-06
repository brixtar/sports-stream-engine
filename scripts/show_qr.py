import qrcode
import socket
import os

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def main():
    ip = get_ip()
    url_futbol = f"http://{ip}:8080"
    url_basquet = f"http://{ip}:8081"

    print("=" * 66)
    print("      🚀 STREAM MASTER STUDIO PRO - CONTROL REMOTO DUAL")
    print("=" * 66)
    print(f"\n  ⚽ FÚTBOL (Puerto 8080):")
    print(f"     📱 Panel Móvil / Web : {url_futbol}")
    print(f"     📺 Overlay OBS       : http://127.0.0.1:8080/overlay/scoreboard.html")
    print(f"\n  🏀 BÁSQUETBOL NBA (Puerto 8081):")
    print(f"     📱 Panel Móvil / Web : {url_basquet}")
    print(f"     📺 Overlay OBS       : http://127.0.0.1:8081/overlay/scoreboard.html")
    print("-" * 66)
    print("  Escanea este código QR para abrir el Panel Principal:")
    print("-" * 66)

    qr = qrcode.QRCode(border=1)
    qr.add_data(url_futbol)
    qr.print_ascii(invert=True)
    print("-" * 66)

if __name__ == "__main__":
    main()

