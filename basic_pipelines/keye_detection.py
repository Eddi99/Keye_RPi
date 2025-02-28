import gi
import os
import numpy as np
import cv2
import hailo
from hailo_apps_infra.hailo_rpi_common import (
    get_caps_from_pad,
    get_numpy_from_buffer,
    app_callback_class,
)
from hailo_apps_infra.detection_pipeline import GStreamerDetectionApp
from gpiozero import LED

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

# Benutzerdefinierte Callback-Klasse für die Objekterkennung
class user_app_callback_class(app_callback_class): 
    def __init__(self):
        super().__init__()
        self.target_object = "person"  # Das zu erkennende Objekt (z. B. "person")
        
        # Definition der ersten ROI (Region of Interest)
        self.zone1_x_min = 0.6  # Linke Grenze der ersten ROI
        self.zone1_x_max = 1.0  # Rechte Grenze der ersten ROI
        self.zone1_y_min = 0.0  # Obere Grenze der ersten ROI
        self.zone1_y_max = 1.0  # Untere Grenze der ersten ROI
        
        # Definition der zweiten ROI
        self.zone2_x_min = 0.0  # Linke Grenze der zweiten ROI
        self.zone2_x_max = 0.4  # Rechte Grenze der zweiten ROI
        self.zone2_y_min = 0.0  # Obere Grenze der zweiten ROI
        self.zone2_y_max = 1.0  # Untere Grenze der zweiten ROI
        
        # Variablen für das Entprellen (Debouncing)
        self.in_zone_frames = 0      # Anzahl aufeinanderfolgender Frames mit Objekt in einer der Zonen
        self.out_zone_frames = 0     # Anzahl aufeinanderfolgender Frames ohne Objekt in einer der Zonen
        
        # Zustand der Erkennung (ob das Relais bereits deaktiviert ist)
        self.is_it_active = False

        # Initialisierung der LEDs zur Signalisierung des Status
        self.green_led = LED(18)  # Grüne LED zeigt Normalbetrieb
        self.red_led = LED(14)    # Rote LED zeigt eine erkannte Gefahr an
        
        self.red_led.off()
        self.green_led.on()

# Callback-Funktion, die aufgerufen wird, wenn neue Videodaten ankommen
def app_callback(pad, info, user_data):
    buffer = info.get_buffer()
    if buffer is None:
        return Gst.PadProbeReturn.OK  # Falls kein gültiger Buffer vorhanden ist, einfach weitermachen
    
    user_data.increment()  # Erhöht den internen Frame-Zähler
    
    # Extrahiert das Videoformat und die Abmessungen des Videostreams
    format, width, height = get_caps_from_pad(pad)
    frame = None
    if user_data.use_frame and format is not None and width is not None and height is not None:
        frame = get_numpy_from_buffer(buffer, format, width, height)
    
    # Holt die Erkennungs-ROI aus dem Videostream
    roi = hailo.get_roi_from_buffer(buffer)
    detections = roi.get_objects_typed(hailo.HAILO_DETECTION)
    
    object_in_zone = False  # Variable zur Überprüfung, ob das Zielobjekt in einer der definierten Zonen ist
    detection_string = ""  # String zur Anzeige der Erkennungsergebnisse
    
    for detection in detections:
        label = detection.get_label()  # Name des erkannten Objekts
        confidence = detection.get_confidence()  # Konfidenz der Erkennung
        
        # Falls das erkannte Objekt das Zielobjekt ist und die Konfidenz hoch genug ist
        if confidence > 0.4 and label == user_data.target_object:
            bbox = detection.get_bbox()
            x_min = bbox.xmin()
            y_min = bbox.ymin()
            box_width = bbox.width()
            box_height = bbox.height()
            
            x_max = x_min + box_width
            y_max = y_min + box_height
            
            # Berechnung der Mitte der Bounding Box
            center_x = x_min + (box_width / 2)
            center_y = (y_min + (box_height / 2) - 0.22) * 1.83  # Skalierung und Offset-Korrektur

            # Speichert die Erkennungsdetails als String für Debugging-Zwecke
            detection_string += (f"{label.capitalize()} detected!\n"
                               f"Position: center=({center_x:.2f}, {center_y:.2f})\n"
                               f"Bounds: xmin={x_min:.2f}, ymin={y_min:.2f}, xmax={x_max:.2f}, ymax={y_max:.2f}\n"
                               f"Confidence: {confidence:.2f}\n")
            
            # Prüft, ob das erkannte Objekt sich in einer der Zielzonen befindet
            if ((user_data.zone1_x_min <= center_x <= user_data.zone1_x_max and 
                user_data.zone1_y_min <= center_y <= user_data.zone1_y_max) or 
                (user_data.zone2_x_min <= center_x <= user_data.zone2_x_max and 
                user_data.zone2_y_min <= center_y <= user_data.zone2_y_max)):
                object_in_zone = True
                detection_string += "Object is in target zone!\n"
    
    # Falls sich das Objekt in einer der Zonen befindet, erhöhe den Zähler für in-zone Frames
    if object_in_zone:
        user_data.in_zone_frames += 1
        user_data.out_zone_frames = 0
        
        # Wenn das Objekt 4 aufeinanderfolgende Frames lang in der Zone erkannt wird, schalte das Relais ab
        if user_data.in_zone_frames >= 4 and not user_data.is_it_active:
            user_data.red_led.on()
            user_data.green_led.off()
            user_data.is_it_active = True
            print(f"{user_data.target_object.capitalize()} in Gefahrenzone, Sicherheitskreis wird abgeschaltet!")
    else:
        user_data.out_zone_frames += 1
        user_data.in_zone_frames = 0
        
        # Falls das Objekt für 5 aufeinanderfolgende Frames nicht mehr in der Zone erkannt wird, reaktiviere das Relais
        if user_data.out_zone_frames >= 5 and user_data.is_it_active:
            user_data.red_led.off()
            user_data.green_led.on()
            user_data.is_it_active = False
            print(f"{user_data.target_object} nicht mehr in Gefahrenzone, Sicherheitskreis einschalten?!")

    # Drucke die Erkennungsdetails nur, wenn eine Erkennung stattfand
    if detection_string:
        print(detection_string, end='')
    
    return Gst.PadProbeReturn.OK  # Setzt die GStreamer Pipeline fort


# Hauptprogramm, das die Anwendung startet
if __name__ == "__main__":
    user_data = user_app_callback_class()
    
    app = GStreamerDetectionApp(
        app_callback, user_data
    )
    app.run()
