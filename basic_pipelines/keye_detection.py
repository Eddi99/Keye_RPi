import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import hailo  # Importiert die Hailo-Bibliothek für KI-gestützte Objekterkennung
from hailo_apps_infra.detection_pipeline import GStreamerDetectionApp
from hailo_apps_infra.hailo_rpi_common import get_caps_from_pad, get_numpy_from_buffer, app_callback_class
import cv2  # Wird für das Zeichnen der Bounding Boxes weiterhin benötigt
import threading
import numpy as np


class ObjectDetection(app_callback_class):
	def __init__(self, model_path="yolo11s_ncnn_model"):
		Gst.init(None)  # GStreamer initialisieren
		self.frame_count = 0

		self.target_object = "person"  # Das zu erkennende Objekt
		self.frame_callback = None
		self.detection_callback = None
		self.running = False
		self.roi1 = None
		self.roi2 = None
		
		self.frame = None # Varable zum Speichern des Videoframes
		self.label = None
		self.x_min = 0.0
		self.y_min = 0.0
		self.x_max = 0.0
		self.y_max = 0.0

		self.object_in_zone1 = False
		self.object_in_zone2 = False
		self.in_zone1_frames = 0
		self.out_zone1_frames = 0
		self.in_zone2_frames = 0
		self.out_zone2_frames = 0
		self.is_active = False

	def set_detection_callback(self, callback):
		"""Setzt eine externe Callback-Funktion für erkannte Objekte."""
		self.detection_callback = callback

	def set_frame_callback(self, callback):
		"""Setzt eine Callback-Funktion für das aktuelle Erkennungsbild."""
		self.frame_callback = callback

	def set_rois(self, roi1, roi2):
		"""Speichert die ROIs für die Erkennung."""
		self.roi1 = roi1
		self.roi2 = roi2
		self.r1xmin, self.r1ymin, self.r1xmax, self.r1ymax = self.roi1 # speichert die Grenzen der ROI in einzelne Werte ab (nur zur Übersichtlichkeit)
		self.r2xmin, self.r2ymin, self.r2xmax, self.r2ymax = self.roi2
		print("keye_detection: ROIs für die Erkennung aktualisiert: ", roi1, roi2)

	def detect_objects(self, pad, info, user_data):
		"""Führt die Objekterkennung mit YOLO durch, zeichnet Bounding Boxes und prüft, ob eine Person in den ROIs ist."""
		buffer = info.get_buffer()  # Extrahiert den Video-Buffer
		if buffer is None:
			return Gst.PadProbeReturn.OK  # Falls kein gültiger Buffer vorhanden ist, fortfahren
			
		user_data.increment()  # Erhöht den internen Frame-Zähler
		
		# Holt das Videoformat und die Abmessungen des Videostreams
		format, width, height = get_caps_from_pad(pad)
		
		if user_data.use_frame and format is not None and width is not None and height is not None:
			self.frame = get_numpy_from_buffer(buffer, format, width, height)  # Konvertiert den Buffer in ein NumPy-Array
		
		# Holt die Objekterkennungs-Region aus dem Videostream
		roi = hailo.get_roi_from_buffer(buffer)  # Extrahiert die Region of Interest (ROI) für die Objekterkennung
		detections = roi.get_objects_typed(hailo.HAILO_DETECTION)  # Holt erkannte Objekte aus der ROI

		if self.roi1 and self.roi2: # stellt sicher, dass die ROIs vorhanden sind
			for det in detections: # für jedes erkannte Objekt wird die schleife einmal durchlaufen
				self.label = detection.get_label()  # Holt die Objektklasse des erkannten Objekts
				confidence = detection.get_confidence()  # Vertrauenswürdigkeit der Erkennung
				
				bbox = detection.get_bbox()  # Holt die Bounding Box des erkannten Objekts
				self.x_min = bbox.xmin()  # Linke obere X-Koordinate der Bounding Box
				self.y_min = bbox.ymin()  # Linke obere Y-Koordinate der Bounding Box
				box_width = bbox.width()  # Breite der Bounding Box
				box_height = bbox.height()  # Höhe der Bounding Box
				self.x_max = x_min + box_width  # Rechte untere X-Koordinate
				self.y_max = y_min + box_height  # Rechte untere Y-Koordinate
				
				if self.label == self.target_object: # nur wenn eine Person erkannt wird, geht es weiter
					#print("Erkanntes Objekt ist Person!")

					if self.x_max/1280 < self.r1xmin or self.x_min/1280 > self.r1xmax or self.y_max/720 < self.r1ymin or self.y_min/720 > self.r1ymax: # überprüft, ob sich die Person außerhalb der ersten ROI befindet
						self.object_in_zone1 = False # wenn sich die Person außerhalb der ROI befindet, wird die variable auf falsch gesetzt
					else:
						#print("detect_objects: Objekt in Zone1")
						self.object_in_zone1 = True # wenn sich die Person innerhalb der ROI befindet, wird die variable auf true gesetzt

					if self.x_max/1280 < self.r2xmin or sefl.x_min/1280 > self.r2xmax or self.y_max/720 < self.r2ymin or self.y_min/720 > self.r2ymax: # überprüft, ob sich die Person außerhalb der zweiten ROI befindet
						self.object_in_zone2 = False # wenn sich die Person außerhalb der ROI befindet, wird die variable auf falsch gesetzt
					else:
						#print("detect_objects: Objekt in Zone2")
						self.object_in_zone2 = True # wenn sich die Person innerhalb der ROI befindet, wird die variable auf true gesetzt

			if self.object_in_zone1 or self.object_in_zone2: # wenn sich eine Person in einer der ROIs befindet, wird eine Variable hochgezählt die sicherstellt, dass bei einer kurzen Falscherkennung nicht das Relais direkt schaltet
				if self.object_in_zone1:
					self.in_zone1_frames += 1 # zählt bei Person in der Zone hoch
					self.out_zone1_frames = 0 # wird bei Person in der Zone auf null gesetzt
				if self.object_in_zone2:
					self.in_zone2_frames += 1
					self.out_zone2_frames = 0

				if (self.in_zone1_frames >= 4 or self.in_zone2_frames >= 4) and not self.is_active: # überprüft, ob die erkannte Person während den letzten vier Frames in der ROI erkannt wurde
					self.is_active = True # zeigt an, ob bereits eine Person erkannt wurde
					print("detect_objects: Person seit mehr als 4 Frames in ROI")
					if self.detection_callback:
						self.detection_callback(True) # gibt an die decision per Callback True aus, damit das Relais ausgeschaltet wird

			else: # wenn sich die Person wieder außerhalb der ROI befindet, wird ebenfalls nicht direkt geschaltet, um bei fehlerhafter erkennung außerhalb der ROI nicht direkt wieder einzuschalten
				self.out_zone1_frames += 1 # zählt hoch, wenn sich die Person, die zuvor in der ROI war aus der ROI rausbewegt
				self.in_zone1_frames = 0 # wird bei Person außerhalb der Zone wieder auf null gesetzt
				self.out_zone2_frames += 1
				self.in_zone2_frames = 0

				if (self.out_zone1_frames >= 4 and self.out_zone2_frames >= 4) and self.is_active: # überprüft, ob die erkannte Person während den letzten vier Frames außerhalb der ROI erkannt wurde
					self.is_active = False
					print("detect_objects: Person seit min. 4 Frames nicht mehr in ROI")
					if self.detection_callback:
						self.detection_callback(False) # gibt an die decision per Callback False aus, damit das Relais eingeschaltet wird

		# Zeichne Bounding Boxes auf dem Kamerabild
		for det in detections:  # Durchläuft alle erkannten Objekte in den Detektionen
			cv2.rectangle(self.frame, (int(self.x_min), int(self.y_min)), (int(self.x_max), int(self.y_max)), (0, 255, 0), 2)  # Zeichnet ein grünes Rechteck um das erkannte Objekt
			cv2.putText(self.frame, self.label, (int(self.x_min), int(self.y_min) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0),2)  # Fügt die Label-Beschriftung über der Bounding Box hinzu

		# Zeichne die ROIs als Rechtecke
		height, width, _ = self.frame.shape  # Bestimmt die Höhe und Breite des aktuellen Frames
		roi1_px = (int(self.roi1[0] * width), int(self.roi1[1] * height), int(self.roi1[2] * width),
				   int(self.roi1[3] * height))  # Berechnet die ROI 1-Koordinaten in Pixeln
		roi2_px = (int(self.roi2[0] * width), int(self.roi2[1] * height), int(self.roi2[2] * width),
				   int(self.roi2[3] * height))  # Berechnet die ROI 2-Koordinaten in Pixeln

		cv2.rectangle(frame, (roi1_px[0], roi1_px[1]), (roi1_px[2], roi1_px[3]), (255, 0, 0), 2)  # Zeichnet ein blaues Rechteck für ROI 1
		cv2.rectangle(frame, (roi2_px[0], roi2_px[1]), (roi2_px[2], roi2_px[3]), (0, 0, 255), 2)  # Zeichnet ein rotes Rechteck für ROI 2

		return self.frame  # Gibt das annotierte Frame zurück

	def run(self):
		"""Startet die GStreamer-Pipeline für die Objekterkennung."""
		self.running = True
		if not self.roi1 or not self.roi2:
			print("ROIs nicht gesetzt! Starte nicht.")
			return
			
		try:
			print("Erkennung läuft mit GStreamer...")
			user_data = ObjectDetection()  # Erstellt ein Objekt der Callback-Klasse
			self.app = GStreamerDetectionApp(self.detect_objects, user_data)
			self.app.run()
		except Exception as e:
			print("Fehler bei der Erkennung:", e)
		finally:
			self.running = False

	def stop_detection(self):
		"""Stoppt die GStreamer-Pipeline sicher."""
		if self.running:
			print("Erkennung wird gestoppt...")
			self.app.stop()
			self.running = False

if __name__ == "__main__":
	try:
		print("Erkennung läuft mit GStreamer...")
		user_data = ObjectDetection()  # Erstellt ein Objekt der Callback-Klasse
		app = GStreamerDetectionApp(user_data.detect_objects, user_data)
		app.run()
	except Exception as e:
		print("Fehler bei der Erkennung:", e)
