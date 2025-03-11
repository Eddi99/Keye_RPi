
import threading  # Für parallele Threads
from keye_detection import ObjectDetection  # Import der Objekterkennung
from relaiscontrol import RelaisControl  # Import der Relaissteuerung

class DecisionLogic:
    def __init__(self):
        """Initialisiert die Steuerlogik, Objekterkennung und Relaissteuerung."""
        self.detector = ObjectDetection()  # Erstellt ein Objekt für die Objekterkennung
        self.relais = RelaisControl()  # Erstellt ein Objekt für die Relaissteuerung
        self.detector.set_detection_callback(self.handle_detection)  # Setzt die Callback-Funktion für die Erkennung
        self.roi1 = None  # Speichert die erste ROI (Region of Interest)
        self.roi2 = None  # Speichert die zweite ROI (Region of Interest)
        self.detection_thread = None  # Speichert den Thread für die Erkennung

    def set_rois(self, roi1, roi2):
        """Speichert die definierten ROIs und übergibt sie an die Objekterkennung."""
        self.roi1 = roi1  # Setzt die erste ROI
        self.roi2 = roi2  # Setzt die zweite ROI
        self.detector.set_rois(roi1, roi2)  # Übergibt die ROIs an die Objekterkennung
        #print("Decision_logic.set_rois:", roi1, roi2)  # Gibt eine Bestätigung aus

    def start_detection(self):
        """Startet die Objekterkennung in einem separaten Thread, wenn ROIs gesetzt sind."""
        if self.roi1 and self.roi2:  # Überprüft, ob ROIs vorhanden sind
            if not self.detection_thread or not self.detection_thread.is_alive():  # Verhindert mehrfaches Starten
                self.detection_thread = threading.Thread(target=self.detector.run, daemon=True)  # Erstellt neuen Thread
                self.detection_thread.start()  # Startet die Erkennung
                self.relais.on_all() # startet bei Start der Detection initial das Relais ein
                #print("start_detection: Erkennung gestartet...")
        else:
            print("ROIs müssen zuerst gesetzt werden!")  # Falls keine ROIs gesetzt wurden

    def stop_detection(self):
        """Beendet die laufende Objekterkennung sicher."""
        if self.detector.running:  # Prüft, ob die Erkennung läuft
            self.detector.stop()  # Setzt die Steuerungsvariable auf False
            if self.detection_thread:
                self.detection_thread.join()  # Wartet auf das Beenden des Threads

    def handle_detection(self, detected):
        """Callback-Funktion, die von der Objekterkennung aufgerufen wird."""
        if detected:
            #print("handle_detection: Relais aus")
            self.relais.off_all()  # Schaltet das Relais aus, wenn eine Person erkannt wird
        else:
            #print("handle_detection: Relais ein")
            self.relais.on_all()  # Schaltet das Relais ein, wenn keine Person erkannt wird

    def shutdown(self):
        """Beendet das gesamte System sicher."""
        print("System wird heruntergefahren...")
        self.stop_detection()  # Beendet die Erkennung
        self.relais.close_device() # Beendet die Verbindung zum Relais
