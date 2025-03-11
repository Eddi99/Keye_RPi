import sys  # Für die Steuerung des Programms und Zugriff auf Systemargumente
from PyQt5.QtWidgets import QApplication  # Importiert die Hauptklasse für die GUI-Anwendung
from decision_logic import DecisionLogic  # Importiert die Steuerlogik für Objekterkennung & Relaissteuerung
from GUI import GUIApp  # Importiert die grafische Benutzeroberfläche

if __name__ == "__main__":  # Prüft, ob das Skript direkt ausgeführt wird
    logic = DecisionLogic()  # Erstellt eine Instanz der Entscheidungslogik

    # Startet die GUI direkt im Hauptthread (wichtig für PyQt)
    app = QApplication(sys.argv)  # Erstellt eine QApplication-Instanz für die GUI-Steuerung
    window = GUIApp(logic)  # Erstellt das Hauptfenster der GUI und übergibt die Steuerlogik
    window.showMaximized()  # Zeigt die GUI maximiert an
    sys.exit(app.exec())  # Startet die GUI-Eventloop und hält das Programm am Laufen
