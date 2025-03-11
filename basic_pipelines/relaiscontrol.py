import pywinusb.hid as hid  # Bibliothek für USB-HID-Kommunikation

class RelaisControl:
    def __init__(self, vendor_id=0x16c0, device_id=0x05DF):
        self.vendor_id = vendor_id  # Speichert die Vendor ID
        self.device_id = device_id  # Speichert die Device ID
        self.device = None  # Initialisiert das Gerät als None
        self.report = None  # Initialisiert das Report-Objekt als None
        self.get_hid_usb_relay()  # Ruft die Geräteerkennung auf
        self.open_device()  # Öffnet das Gerät

    def get_hid_usb_relay(self): #Sucht nach einem USB-Relais mit den gegebenen Vendor und Device IDs."""
        filter = hid.HidDeviceFilter(vendor_id=self.vendor_id, product_id=self.device_id)
        devices = filter.get_devices()
        if devices:
            self.device = devices[0]  # Speichert das erste gefundene Gerät

    def open_device(self): #Öffnet die Verbindung zum USB-Relais, falls es verfügbar ist.
        if self.device and not self.device.is_opened():
            self.device.open()
            self.get_report()
            #self.on_all() # schaltet das Relais zu anfang an, damit der Sicherheitskreis geschlossen ist

    def close_device(self): #Schließt die Verbindung zum USB-Relais, falls es geöffnet ist.
        if self.device and self.device.is_opened():
            self.off_all()
            self.device.close()

    def get_report(self): #Liest das Report-Objekt des Geräts aus.
        if self.device:
            reports = self.device.find_output_reports() + self.device.find_feature_reports()
            if reports:
                self.report = reports[0]  # Speichert das erste gefundene Report-Objekt

    def write_row_data(self, buffer): #Sendet ein Steuerkommando an das Relais.
        if self.report is not None:
            self.report.send(raw_data=buffer)
            return True
        else:
            print("Cannot write to the report. Check if your device is still plugged in.")
            return False

    def on_all(self): #Schaltet alle Relais ein.
        if self.write_row_data([0, 0xFE, 0, 0, 0, 0, 0, 0, 1]):
            #print("on_all: Relaiskreislauf eingeschaltet!")
            return
        else:
            print("Cannot turn ON relays")
            return False

    def off_all(self): #Schaltet alle Relais aus.
        if self.write_row_data([0, 0xFC, 0, 0, 0, 0, 0, 0, 1]):
            #print("off_all: Relaiskreislauf ausgeschaltet!")
            return
        else:
            print("Cannot turn OFF relays")
            return False
