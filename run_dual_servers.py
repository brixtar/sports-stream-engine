import subprocess
import sys
import os
import time
import signal

def run():
    sys.stdout.reconfigure(encoding='utf-8')
    project_dir = os.path.dirname(os.path.abspath(__file__))

    print("=" * 68)
    print("   🚀 STREAM MASTER PRO - SERVIDOR DUAL (FÚTBOL + BÁSQUET)")
    print("=" * 68)
    print("")
    print("  ⚽ FÚTBOL (Puerto 8080):")
    print("     -> Panel Web: http://localhost:8080")
    print("     -> Overlay OBS: http://127.0.0.1:8080/overlay/scoreboard.html")
    print("")
    print("  🏀 BÁSQUETBOL NBA (Puerto 8081):")
    print("     -> Panel Web: http://localhost:8081")
    print("     -> Overlay OBS: http://127.0.0.1:8081/overlay/scoreboard.html")
    print("=" * 68)
    print("")

    env_futbol = os.environ.copy()
    env_futbol["SPORT_DEFAULT"] = "futbol"
    env_futbol["APP_PORT"] = "8080"

    env_basquet = os.environ.copy()
    env_basquet["SPORT_DEFAULT"] = "basquet"
    env_basquet["APP_PORT"] = "8081"

    python_bin = sys.executable

    p_futbol = subprocess.Popen(
        [python_bin, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"],
        cwd=project_dir,
        env=env_futbol
    )

    time.sleep(1.5)

    p_basquet = subprocess.Popen(
        [python_bin, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8081"],
        cwd=project_dir,
        env=env_basquet
    )

    def shutdown(sig, frame):
        print("\n[*] Cerrando servidores...")
        p_futbol.terminate()
        p_basquet.terminate()
        p_futbol.wait()
        p_basquet.wait()
        print("[✔] Servidores cerrados.")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        while True:
            time.sleep(1)
            if p_futbol.poll() is not None and p_basquet.poll() is not None:
                break
    except KeyboardInterrupt:
        shutdown(None, None)

if __name__ == "__main__":
    run()
