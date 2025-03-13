import sys
import threading
from PyQt5.QtWidgets import QApplication
from decision_logic import DecisionLogic
from GUI import GUIApp

if __name__ == "__main__":
    logic = DecisionLogic()  # Erstellt die Steuerlogik

    app = QApplication(sys.argv)  # Erstellt GUI-Instanz
    window = GUIApp(logic)  # Übergibt Entscheidungslogik an GUI
    window.showMaximized()
    
	logic.start_detection()  # Starte die Objekterkennung in eigenem Thread

    sys.exit(app.exec())  # Starte GUI-Eventloop
