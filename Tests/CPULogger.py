import psutil
import time

def log_system_usage():
    while True:
        cpu_usage = psutil.cpu_percent(interval=1)  # CPU-Auslastung in Prozent (1 Sekunde Mittelwert)
        ram_usage = psutil.virtual_memory().percent  # RAM-Auslastung in Prozent
        print(f"CPU: {cpu_usage}% | RAM: {ram_usage}%")
        time.sleep(4)  # 4 Sekunden warten, da `cpu_percent(interval=1)` bereits 1 Sekunde verbraucht

if __name__ == "__main__":
    log_system_usage()
