#!/bin/bash
echo "Starte Umgebung..."
source /home/EdgarCoy/Keye_RPi/setup_env.sh  # Setzt die Umgebung

echo "Starte Python-Programm..."
python3 /home/EdgarCoy/Keye_RPi/main.py  # Starte das Hauptskript

echo "Programm beendet. Drücke eine Taste zum Schließen..."
read -n 1 -s  # Wartet auf Tastendruck
