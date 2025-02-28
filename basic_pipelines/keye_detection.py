import gi  # Importiert GObject-Introspection für die Nutzung von GStreamer
import os  # Importiert das OS-Modul für Betriebssystem-Interaktionen
import numpy as np  # Importiert NumPy für numerische Berechnungen
import cv2  # Importiert OpenCV für Bildverarbeitung
import hailo  # Importiert die Hailo-Bibliothek für KI-gestützte Objekterkennung
from hailo_apps_infra.hailo_rpi_common import (
    get_caps_from_pad,  # Funktion zum Abrufen der Eigenschaften des Videostreams
    get_numpy_from_buffer,  # Konvertiert den Video-Buffer in ein NumPy-Array
    app_callback_class,  # Basis-Klasse für Callback-Funktionen
)
from hailo_apps_infra.detection_pipeline import GStreamerDetectionApp  # Importiert die Hailo GStreamer App-Klasse
from gpiozero import LED  # Importiert GPIOZero zur Steuerung der LEDs

gi.require_version('Gst', '1.0')  # Stellt sicher, dass GStreamer mit Version 1.0 geladen wird
from gi.repository import Gst, GLib  # Importiert GStreamer und GLib für Medienverarbeitung

# Benutzerdefinierte Callback-Klasse für die Objekterkennung
class user_app_callback_class(app_callback_class): 
    def __init__(self):
        super().__init__()  # Ruft den Konstruktor der Basisklasse auf
        self.target_object = "person"  # Das zu erkennende Objekt (z. B. "person")
        
        # Definition der ersten Region of Interest (ROI)
        self.zone1_x_min = 0.6  # Linke Grenze der ROI
        self.zone1_x_max = 1.0  # Rechte Grenze der ROI
        self.zone1_y_min = 0.0  # Obere Grenze der ROI
        self.zone1_y_max = 1.0  # Untere Grenze der ROI
        
        # Definition der zweiten Region of Interest (ROI)
        self.zone2_x_min = 0.0  # Linke Grenze der zweiten ROI
        self.zone2_x_max = 0.4  # Rechte Grenze der zweiten ROI
        self.zone2_y_min = 0.0  # Obere Grenze der zweiten ROI
        self.zone2_y_max = 1.0  # Untere Grenze der zweiten ROI
        
        # Variablen zur Frame-Überwachung für stabilere Erkennung
        self.in_zone_frames = 0  # Anzahl aufeinanderfolgender Frames mit Objekt in einer der Zonen
        self.out_zone_frames = 0  # Anzahl aufeinanderfolgender Frames ohne Objekt in einer der Zonen
        
        # Statusvariable für die Aktivierung des Relais
        self.is_it_active = False

# Callback-Funktion, die aufgerufen wird, wenn neue Videodaten ankommen
def app_callback(pad, info, user_data):
    buffer = info.get_buffer()  # Extrahiert den Video-Buffer
    if buffer is None:
        return Gst.PadProbeReturn.OK  # Falls kein gültiger Buffer vorhanden ist, fortfahren
    
    user_data.increment()  # Erhöht den internen Frame-Zähler
    
    # Holt das Videoformat und die Abmessungen des Videostreams
    format, width, height = get_caps_from_pad(pad)
    frame = None  # Variable zur Speicherung des Videoframes
    
    if user_data.use_frame and format is not None and width is not None and height is not None:
        frame = get_numpy_from_buffer(buffer, format, width, height)  # Konvertiert den Buffer in ein NumPy-Array
    
    # Holt die Objekterkennungs-Region aus dem Videostream
    roi = hailo.get_roi_from_buffer(buffer)  # Extrahiert die Region of Interest (ROI) für die Objekterkennung
    detections = roi.get_objects_typed(hailo.HAILO_DETECTION)  # Holt erkannte Objekte aus der ROI
    
    object_in_zone = False  # Variable zur Überprüfung, ob das Zielobjekt in einer der definierten Zonen ist
    detection_string = ""  # String zur Anzeige der Erkennungsergebnisse
    
    for detection in detections:
        label = detection.get_label()  # Holt die Objektklasse des erkannten Objekts
        confidence = detection.get_confidence()  # Vertrauenswürdigkeit der Erkennung
        
        # Falls das erkannte Objekt das Zielobjekt ist und die Konfidenz hoch genug ist
        if confidence > 0.4 and label == user_data.target_object:
            bbox = detection.get_bbox()  # Holt die Bounding Box des erkannten Objekts
            x_min = bbox.xmin()  # Linke obere X-Koordinate der Bounding Box
            y_min = bbox.ymin()  # Linke obere Y-Koordinate der Bounding Box
            box_width = bbox.width()  # Breite der Bounding Box
            box_height = bbox.height()  # Höhe der Bounding Box
            
            x_max = x_min + box_width  # Rechte untere X-Koordinate
            y_max = y_min + box_height  # Rechte untere Y-Koordinate
            
            # Berechnung der Mitte der Bounding Box
            center_x = x_min + (box_width / 2)
            center_y = (y_min + (box_height / 2) - 0.22) * 1.83  # Skalierung und Offset-Korrektur

            # Speichert die Erkennungsdetails als Debug-String
            detection_string += (f"{label.capitalize()} detected!\n"
                               f"Position: center=({center_x:.2f}, {center_y:.2f})\n"
                               f"Bounds: xmin={x_min:.2f}, ymin={y_min:.2f}, xmax={x_max:.2f}, ymax={y_max:.2f}\n"
                               f"Confidence: {confidence:.2f}\n")
            
            # Prüft, ob das erkannte Objekt sich in einer der Zielzonen befindet
            if ((user_data.zone1_x_min <= center_x <= user_data.zone1_x_max and 
                user_data.zone1_y_min <= center_y <= user_data.zone1_y_max) or 
                (user_data.zone2_x_min <= center_x <= user_data.zone2_x_max and 
                user_data.zone2_y_min <= center_y <= user_data.zone2_y_max)):
                object_in_zone = True  # Setzt die Variable auf True, falls das Objekt in einer der Zonen liegt
                detection_string += "Object is in target zone!\n"
    
    # Falls sich das Objekt in einer der Zonen befindet, erhöhe den Zähler für in-zone Frames
    if object_in_zone:
        user_data.in_zone_frames += 1
        user_data.out_zone_frames = 0  # Setzt den Zähler für Frames ohne Objekt zurück
        
        # Wenn das Objekt 4 aufeinanderfolgende Frames lang in der Zone erkannt wird, schalte das Relais ab
        if user_data.in_zone_frames >= 4 and not user_data.is_it_active:
            user_data.is_it_active = True
            print(f"{user_data.target_object.capitalize()} in Gefahrenzone, Sicherheitskreis wird abgeschaltet!")
            
    else:
        user_data.out_zone_frames += 1
        user_data.in_zone_frames = 0  # Setzt den Zähler für Frames mit Objekt zurück
        
        # Falls das Objekt für 5 aufeinanderfolgende Frames nicht mehr in der Zone erkannt wird, Reaktivierung
        if user_data.out_zone_frames >= 5 and user_data.is_it_active:
            user_data.is_it_active = False  # Setzt den Status zurück
            print(f"{user_data.target_object} nicht mehr in Gefahrenzone, Sicherheitskreis einschalten?!")
    
    # Druckt die Erkennungsdetails nur, wenn eine Erkennung stattfand
    if detection_string:
        print(detection_string, end='')
    
    return Gst.PadProbeReturn.OK  # Setzt die GStreamer Pipeline fort

# Hauptprogramm, das die Anwendung startet
if __name__ == "__main__":
    user_data = user_app_callback_class()  # Erstellt ein Objekt der Callback-Klasse
    app = GStreamerDetectionApp(app_callback, user_data)  # Erstellt die GStreamer-Anwendung mit dem Callback
    app.run()  # Startet die Anwendung
