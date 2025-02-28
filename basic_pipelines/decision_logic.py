import threading
import queue
from relay_control.relaissteuerung import USBRelay
from basic_pipelines.keye_detection import user_app_callback_class

class DecisionLogic:
    def __init__(self):
        self.relay = USBRelay()  # Initialisiert das Relais-Steuermodul
        self.detection = user_app_callback_class()  # Initialisiert die Objekterkennung
        self.event_queue = queue.Queue()  # Warteschlange zur Synchronisation von Events

    def process_detection(self, detected_object, in_danger_zone):
        """Verarbeitet die Detektion und steuert das Relais basierend auf der Position"""
        if in_danger_zone and not self.relay.is_active:
            print(f"[⚠️] {detected_object} in Gefahr! Relais wird abgeschaltet.")
            self.relay.turn_off_all()
        elif not in_danger_zone and self.relay.is_active:
            print(f"[✅] {detected_object} hat die Gefahrenzone verlassen. Relais wird wieder eingeschaltet.")
            self.relay.turn_on_all()

    def detection_listener(self):
        """Läuft als Hintergrund-Thread und empfängt Daten von keye_detection"""
        while True:
            try:
                detected_object, in_danger_zone = self.event_queue.get()
                self.process_detection(detected_object, in_danger_zone)
            except Exception as e:
                print(f"[❌] Fehler in der Entscheidungslogik: {e}")

    def start(self):
        """Startet die Entscheidungslogik und die Detektion in Threads"""
        threading.Thread(target=self.detection_listener, daemon=True).start()

        # Hier würde das Keye-Detection-Skript in einer Schleife laufen
        # Alternativ könnte keye_detection so angepasst werden, dass es Daten aktiv an die event_queue sendet

decision_logic = DecisionLogic()
decision_logic.start()
