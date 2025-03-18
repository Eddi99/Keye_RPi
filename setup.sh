#!/bin/bash

# Setze das hidraw-Relais als /dev/usbrelay
if [ ! -e /dev/usbrelay ]; then
    echo "Erstelle Symlink für das HIDRAW-Relais..."
    sudo ln -s /dev/hidraw0 /dev/usbrelay
fi

echo "Starte die virtuelle Umgebung..."
source setup_env.sh

echo "Installation abgeschlossen."
