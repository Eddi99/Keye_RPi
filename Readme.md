# Sicherheitssystem für Hochspannungslabore

Ein YOLO-basiertes Sicherheitssystem welches mit Hilfe von Echtzeit Bildauswertung eine Abschaltung auslöst

## Installation

### Voraussetzungen

- Raspberry Pi 5 oder neuer mit min 4GB Arbeitsspeicher
- Min Hat mit Hailo 8L (13 TOPS)
- USB Webcam oder Raspi Cam
- Für dauerhafte Nutzung SSD statt SD Karte

### Setup
Die Umsetzung der Pipelines für den HAILO-AI HAT wurde auf Grundlage der Beispielpipelines und Ressourcen von HAILO.AI und Core Electronics implementiert.
Für eine detaillierte Anleitung zum Setup der hailo-pipelines Core-Electronics Video unter https://youtu.be/Zht2G1htFHA ansehen!
	
	```bash
	git clone https://github.com/Eddi99/Keye-RPi
	/Keye_RPi/. install.sh

### Test
Um das erfolgreiche Installieren der Pipelines und requirements zu verifizieren, testlauf starten:
	```bash
	cd /Keye_RPi
	. setup_env.sh
	basic_pipelines/keye_detection.py --input /dev/video0
	
	

## Autor

Erstellt von Edgar Coy im Rahmen der Bachelor-Thesis an der FH Kiel.