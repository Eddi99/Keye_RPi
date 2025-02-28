import hid  # Importiert die hid-Bibliothek für den Zugriff auf HID-Geräte
from time import sleep  # Importiert die sleep-Funktion, um Verzögerungen zu ermöglichen

class USBRelay:
    def __init__(self, vendor_id=0x16c0, product_id=0x05DF): # Initialisiert das USB-Relais mit den angegebenen Vendor- und Product-IDs
        self.vendor_id = vendor_id  # Hersteller-ID des Relais
        self.product_id = product_id  # Produkt-ID des Relais
        self.device = None  # Variable zur Speicherung des HID-Geräts
        self.connect()  # Verbindung zum Relais beim Erstellen des Objekts herstellen

    def connect(self): # Stellt die Verbindung zum HID-Gerät her
        try:
            self.device = hid.Device(self.vendor_id, self.product_id)  # Versucht, das Gerät zu öffnen
            print("Device connected successfully")  # Gibt eine Erfolgsmeldung aus
        except Exception as e:
            print(f"Failed to open device: {e}")  # Gibt eine Fehlermeldung aus, falls das Gerät nicht verbunden werden kann
            self.device = None  # Setzt das Gerät auf None, falls die Verbindung fehlschlägt

    def close(self): # Schließt die Verbindung zum HID-Gerät
        if self.device:  # Überprüft, ob ein Gerät geöffnet ist
            self.device.close()  # Schließt die Verbindung zum Gerät
            self.device = None  # Setzt die Gerätevariable auf None
            print("Device closed")  # Gibt eine Bestätigung aus

    def write_data(self, buffer): # Sendet Daten an das HID-Gerät
        if self.device:  # Überprüft, ob das Gerät verbunden ist
            try:
                self.device.write(bytes(buffer))  # Schreibt die Daten als Byte-Array an das Gerät
                return True  # Gibt True zurück, wenn der Schreibvorgang erfolgreich war
            except Exception as e:
                print(f"Failed to write data: {e}")  # Gibt eine Fehlermeldung aus, falls der Schreibvorgang fehlschlägt
                return False  # Gibt False zurück, wenn der Schreibvorgang nicht erfolgreich war
        else:
            print("Device not connected")  # Gibt eine Meldung aus, wenn das Gerät nicht verbunden ist
            return False  # Gibt False zurück, wenn kein Gerät verbunden ist

    def turn_on_all(self): # Schaltet alle Relais ein
        if self.write_data([0, 0xFE, 0, 0, 0, 0, 0, 0, 1]):  # Sendet den Befehl zum Einschalten aller Relais
            print("All relays turned ON")  # Gibt eine Bestätigung aus
            return True  # Gibt True zurück, wenn der Befehl erfolgreich gesendet wurde
        else:
            print("Cannot turn ON all relays")  # Gibt eine Fehlermeldung aus, wenn das Einschalten fehlschlägt
            return False  # Gibt False zurück, wenn der Befehl nicht gesendet werden konnte

    def turn_off_all(self): # Schaltet alle Relais aus
        if self.write_data([0, 0xFC, 0, 0, 0, 0, 0, 0, 1]):  # Sendet den Befehl zum Ausschalten aller Relais
            print("All relays turned OFF")  # Gibt eine Bestätigung aus
            return True  # Gibt True zurück, wenn der Befehl erfolgreich gesendet wurde
        else:
            print("Cannot turn OFF all relays")  # Gibt eine Fehlermeldung aus, wenn das Ausschalten fehlschlägt
            return False  # Gibt False zurück, wenn der Befehl nicht gesendet werden konnte
