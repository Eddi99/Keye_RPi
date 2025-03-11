import os  # Importiert das OS-Modul für den direkten Zugriff auf /dev/hidrawX

class RelaisControl:
    def __init__(self, hidraw_path="/dev/hidraw0"):
        """ Initialisiert das Relais-Kontrollsystem und stellt die Verbindung her. """
        self.hidraw_path = hidraw_path  # Speichert den Pfad zum HIDRAW-Gerät
        self.device = None  # Initialisiert die Gerät-Variable als None
        self.connect()  # Stellt die Verbindung zum Relais her

    def connect(self):
        """ Öffnet das HIDRAW-Gerät zum Schreiben. """
        try:
            self.device = open(self.hidraw_path, "wb")  # Öffnet das Gerät im Binär-Schreibmodus
            print("Device connected successfully")  # Gibt eine Erfolgsmeldung aus
        except Exception as e:
            print(f"Failed to open device: {e}")  # Falls ein Fehler auftritt, wird er ausgegeben
            self.device = None  # Setzt das Gerät auf None, falls die Verbindung fehlschlägt

    def close_device(self):
        """ Schließt die Verbindung zum Relais. """
        if self.device:  # Überprüft, ob das Gerät geöffnet ist
            self.device.close()  # Schließt das HIDRAW-Gerät
            self.device = None  # Setzt die Gerätevariable zurück
            print("Device closed")  # Bestätigungsausgabe

    def write_data(self, buffer):
        """ Sendet einen Befehl an das Relais. """
        if self.device:  # Stellt sicher, dass das Gerät verbunden ist
            try:
                self.device.write(bytes(buffer))  # Sendet die Byte-Daten an das Relais
                self.device.flush()  # Stellt sicher, dass die Daten sofort übertragen werden
                return True  # Gibt True zurück, falls der Schreibvorgang erfolgreich war
            except Exception as e:
                print(f"Failed to write data: {e}")  # Gibt eine Fehlermeldung aus, falls ein Fehler auftritt
                return False  # Gibt False zurück, falls der Befehl nicht gesendet werden konnte
        else:
            print("Device not connected")  # Falls das Gerät nicht verbunden ist, gibt es eine Warnung aus
            return False  # Gibt False zurück, da kein Befehl gesendet wurde

    def on_all(self):
        """ Schaltet alle Relais ein. """
        if self.write_data([0x00, 0xFE, 0, 0, 0, 0, 0, 0, 1]):  # Sendet das Einschaltkommando
            print("All relays turned ON")  # Bestätigungsausgabe
            return True  # Gibt True zurück, falls erfolgreich
        else:
            print("Cannot turn ON all relays")  # Falls der Befehl fehlschlägt, wird eine Warnung ausgegeben
            return False  # Gibt False zurück

    def off_all(self):
        """ Schaltet alle Relais aus. """
        if self.write_data([0x00, 0xFC, 0, 0, 0, 0, 0, 0, 1]):  # Sendet das Ausschaltkommando
            print("All relays turned OFF")  # Bestätigungsausgabe
            return True  # Gibt True zurück, falls erfolgreich
        else:
            print("Cannot turn OFF all relays")  # Falls der Befehl fehlschlägt, wird eine Warnung ausgegeben
            return False  # Gibt False zurück
