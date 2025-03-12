import os  # Importiert das OS-Modul für den direkten Zugriff auf /dev/hidrawX

class RelaisControl:
    def __init__(self, hidraw_path="/dev/hidraw2"):
        """ Initialisiert das Relais-Kontrollsystem und stellt die Verbindung her. """
        self.hidraw_path = hidraw_path  # Speichert den Pfad zum HIDRAW-Gerät
        self.device = None  # Initialisiert die Gerät-Variable als None
        self.connect()  # Stellt die Verbindung zum Relais her

    def connect(self):
        """ Öffnet das HIDRAW-Gerät zum Schreiben. """
        try:
            self.device = open(self.hidraw_path, "wb")  # Öffnet das Gerät im Binär-Schreibmodus
            print("Relais erfolgreich verbunden :)")  # Gibt eine Erfolgsmeldung aus
        except Exception as e:
            print(f"Relais konnte nicht verbunden werden :(: {e}")  # Falls ein Fehler auftritt, wird er ausgegeben
            self.device = None  # Setzt das Gerät auf None, falls die Verbindung fehlschlägt

    def close_device(self):
        """ Schließt die Verbindung zum Relais. """
        if self.device:  # Überprüft, ob das Gerät geöffnet ist
			# self.off_all() # stellt beim Beenden das Relais aus
            self.device.close()  # Trennt das HIDRAW-Relais
            self.device = None  # Setzt die Gerätevariable zurück
            print("Relais getrennt")  # Bestätigungsausgabe

    def write_data(self, buffer):
        """ Sendet einen Befehl an das Relais. """
        if self.device:  # Stellt sicher, dass das Gerät verbunden ist
            try:
                self.device.write(bytes(buffer))  # Sendet die Byte-Daten an das Relais
                self.device.flush()  # Stellt sicher, dass die Daten sofort übertragen werden
                return True  # Gibt True zurück, falls der Schreibvorgang erfolgreich war
            except Exception as e:
                print(f"Relaisbefehl konnte nicht geschrieben werden: {e}")  # Gibt eine Fehlermeldung aus, falls ein Fehler auftritt
                return False  # Gibt False zurück, falls der Befehl nicht gesendet werden konnte
        else:
            print("Relais ist nicht verbunden")  # Falls das Gerät nicht verbunden ist, gibt es eine Warnung aus
            return False  # Gibt False zurück, da kein Befehl gesendet wurde

    def on_all(self):
        """ Schaltet alle Relais ein. """
        if self.write_data([0x00, 0xFE, 0, 0, 0, 0, 0, 0, 1]):  # Sendet das Einschaltkommando
            print("Relais wurde eingeschaltet")  # Bestätigungsausgabe
            return True  # Gibt True zurück, falls erfolgreich
        else:
            print("Relais kann nicht eingeschaltet werden")  # Falls der Befehl fehlschlägt, wird eine Warnung ausgegeben
            return False  # Gibt False zurück

    def off_all(self):
        """ Schaltet alle Relais aus. """
        if self.write_data([0x00, 0xFC, 0, 0, 0, 0, 0, 0, 1]):  # Sendet das Ausschaltkommando
            print("Relais wurde ausgeschaltet")  # Bestätigungsausgabe
            return True  # Gibt True zurück, falls erfolgreich
        else:
            print("RElais konnte nicht ausgeschaltet werden")  # Falls der Befehl fehlschlägt, wird eine Warnung ausgegeben
            return False  # Gibt False zurück
