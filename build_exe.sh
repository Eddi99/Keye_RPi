#!/bin/bash

# Erstelle die .exe-Datei mit PyInstaller
pyinstaller --onefile --noconsole --icon=icon.ico main.py

echo "Build abgeschlossen. Die .exe befindet sich im dist/ Verzeichnis."
