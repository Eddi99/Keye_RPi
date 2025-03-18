"""Für diesen Teil des Projektes wurde als Vorlage ein Programm von Core-electronics verwendet, dass unter folgendem Link zu finden ist:
https://core-electronics.com.au/guides/raspberry-pi/yolo-object-detection-on-the-raspberry-pi-ai-hat-writing-custom-python/
Das Programm wurde stark verändert, verbessert und auf die Situation angepasst, dennoch bot es eine ausgezeichnete Grundlage für die Objekterkennung mit YOLO"""
import cv2  # OpenCV für Bildverarbeitung
import threading
from ultralytics import YOLO  # YOLO für Objekterkennung


class ObjectDetection:
	def __init__(self, model_path="yolo11s_ncnn_model"):
		self.cap = cv2.VideoCapture(0)  # Öffnet die Kamera mit Index 0, falls kamera  nicht erkannt ggf. ändern
		self.model_path = model_path # speichert den Pfad zum Yolo-Modell, dass an die Klasse übergeben wird
		self.model = None # PLatzhalter für das Yolo-Modell
		self.cap.set(3, 1280)  # Setzt die Breite des Kamera-Frames auf 1280 Pixel
		self.cap.set(4, 720)  # Setzt die Höhe des Kamera-Frames auf 720 Pixel
		self.frame_callback = None  # Callback-Funktion für die GUI-Einbettung des Personenerkennungsbildes
		self.detection_callback = None  # Speichert die Callback-Funktion
		self.target_object = "person"  # Definiert das Zielobjekt als "Person"
		self.running = False  # Kontrollvariable für das Hauptprogramm (Start erst nach GUI-Klick)
		threading.Thread(target=self.load_model, daemon=True).start() # Starte das Modell-Laden asynchron

		# ROIs als Platzhalter
		self.roi1 = None # hier werden die Grenzen der ersten ROI gespeichert
		self.roi2 = None # hier werden die Grenzen der zweiten ROI gespeichert

		self.object_in_zone1 = False # bool, die anzeigt, ob sich in der ersten ROI eine Person befindet
		self.object_in_zone2 = False # bool, die anzeigt, ob sich in der zweiten ROI eine Person befindet
		self.in_zone1_frames = 0  # Anzahl erkannter Frames in der ersten ROI
		self.out_zone1_frames = 0  # Anzahl der nicht erkannten Frames in der ersten ROI
		self.in_zone2_frames = 0  # Anzahl erkannter Frames in der zweiten ROI
		self.out_zone2_frames = 0  # Anzahl der nicht erkannten Frames in der zweiten ROI
		self.is_active = False  # Gibt an, ob aktuell eine Person erkannt wurde

	def load_model(self):
		"""Lädt das YOLO-Modell im Hintergrund, um den Start zu beschleunigen."""
		print("Lade YOLO-Modell...")
		try:
			self.model = YOLO(self.model_path, task='detect') # versucht YOLO-Modell aus dem Pfad zu laden

			print("YOLO-Modell geladen!")
		except Exception as e:
			print("YOLO-Modell konnte nicht geladen werden")

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
		print("keye_detection: ROIs für die Erkennung aktualisiert: ", roi1, roi2)

	def detect_objects(self, frame):
		"""Führt die Objekterkennung mit YOLO durch, zeichnet Bounding Boxes und prüft, ob eine Person in den ROIs ist."""
		results = self.model(frame, imgsz=320, verbose=False) # führt die Objekterkennung durch und speichert die Ergebnisse
		detections = results[0].boxes.data.cpu().numpy()  # Extrahiert erkannte Objekte

		if self.roi1 and self.roi2: # stellt sicher, dass die ROIs vorhanden sind
			for det in detections: # für jedes erkannte Objekt wird die schleife einmal durchlaufen
				x_min, y_min, x_max, y_max, conf, cls = det[:6] # speichert die Bounding Box des Objektes, die Sicherheit der Erkennung und das Label
				r1xmin, r1ymin, r1xmax, r1ymax = self.roi1 # speichert die Grenzen der ROI in einzelne Werte ab (nur zur Übersichtlichkeit)
				r2xmin, r2ymin, r2xmax, r2ymax = self.roi2

				if self.model.names[int(cls)] == self.target_object: # nur wenn eine Person erkannt wird, geht es weiter

					if x_max/1280 < r1xmin or x_min/1280 > r1xmax or y_max/720 < r1ymin or y_min/720 > r1ymax: # überprüft, ob sich die Person außerhalb der ersten ROI befindet
						self.object_in_zone1 = False # wenn sich die Person außerhalb der ROI befindet, wird die variable auf falsch gesetzt
					else:
						self.object_in_zone1 = True # wenn sich die Person innerhalb der ROI befindet, wird die variable auf true gesetzt

					if x_max/1280 < r2xmin or x_min/1280 > r2xmax or y_max/720 < r2ymin or y_min/720 > r2ymax: # überprüft, ob sich die Person außerhalb der zweiten ROI befindet
						self.object_in_zone2 = False # wenn sich die Person außerhalb der ROI befindet, wird die variable auf falsch gesetzt
					else:
						self.object_in_zone2 = True # wenn sich die Person innerhalb der ROI befindet, wird die variable auf true gesetzt

			if self.object_in_zone1 or self.object_in_zone2: # wenn sich eine Person in einer der ROIs befindet, wird eine Variable hochgezählt die sicherstellt, dass bei einer kurzen Falscherkennung nicht das Relais direkt schaltet
				if self.object_in_zone1:
					self.in_zone1_frames += 1 # zählt bei Person in der Zone hoch
					self.out_zone1_frames = 0 # wird bei Person in der Zone auf null gesetzt
				if self.object_in_zone2:
					self.in_zone2_frames += 1
					self.out_zone2_frames = 0

				if (self.in_zone1_frames >= 3 or self.in_zone2_frames >= 3) and not self.is_active: # überprüft, ob die erkannte Person während den letzten n Frames in der ROI erkannt wurde
					self.is_active = True # zeigt an, ob bereits eine Person erkannt wurde
					print("detect_objects: Person seit mehr als 4 Frames in ROI")
					if self.detection_callback:
						self.detection_callback(True) # gibt an die decision per Callback True aus, damit das Relais ausgeschaltet wird

			else: # wenn sich die Person wieder außerhalb der ROI befindet, wird ebenfalls nicht direkt geschaltet, um bei fehlerhafter erkennung außerhalb der ROI nicht direkt wieder einzuschalten
				self.out_zone1_frames += 1 # zählt hoch, wenn sich die Person, die zuvor in der ROI war aus der ROI rausbewegt
				self.in_zone1_frames = 0 # wird bei Person außerhalb der Zone wieder auf null gesetzt
				self.out_zone2_frames += 1
				self.in_zone2_frames = 0

				if (self.out_zone1_frames >= 3 and self.out_zone2_frames >= 3) and self.is_active: # überprüft, ob die erkannte Person während den letzten n Frames außerhalb der ROI erkannt wurde
					self.is_active = False
					print("detect_objects: Person seit min. 4 Frames nicht mehr in ROI")
					if self.detection_callback:
						self.detection_callback(False) # gibt an die decision per Callback False aus, damit das Relais eingeschaltet wird

		# Zeichne Bounding Boxes auf dem Kamerabild
		for det in detections:  # Durchläuft alle erkannten Objekte in den Detektionen
			x_min, y_min, x_max, y_max, conf, cls = det[:6]  # Extrahiert die Bounding-Box-Koordinaten, die Konfidenz und die Klasse
			label = f"{self.model.names[int(cls)]}: {conf:.2f}"  # Erstellt eine Label-Beschriftung mit Klassenname und Konfidenzwert
			cv2.rectangle(frame, (int(x_min), int(y_min)), (int(x_max), int(y_max)), (0, 255, 0), 2)  # Zeichnet ein grünes Rechteck um das erkannte Objekt
			cv2.putText(frame, label, (int(x_min), int(y_min) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0),2)  # Fügt die Label-Beschriftung über der Bounding Box hinzu

		# Zeichne die ROIs als Rechtecke
		height, width, _ = frame.shape  # Bestimmt die Höhe und Breite des aktuellen Frames
		roi1_px = (int(self.roi1[0] * width), int(self.roi1[1] * height), int(self.roi1[2] * width),
				   int(self.roi1[3] * height))  # Berechnet die ROI 1-Koordinaten in Pixeln
		roi2_px = (int(self.roi2[0] * width), int(self.roi2[1] * height), int(self.roi2[2] * width),
				   int(self.roi2[3] * height))  # Berechnet die ROI 2-Koordinaten in Pixeln

		cv2.rectangle(frame, (roi1_px[0], roi1_px[1]), (roi1_px[2], roi1_px[3]), (255, 0, 0), 2)  # Zeichnet ein blaues Rechteck für ROI 1
		cv2.rectangle(frame, (roi2_px[0], roi2_px[1]), (roi2_px[2], roi2_px[3]), (255, 0, 0), 2)  # Zeichnet ein blaues Rechteck für ROI 2

		return frame  # Gibt das annotierte Frame zurück

	def run(self):
		"""Startet die Objekterkennung in einer Schleife."""
		if not self.roi1 or not self.roi2:  # Prüft, ob die ROIs gesetzt sind
			print("ROIs nicht gesetzt! Starte nicht.")  # Gibt eine Fehlermeldung aus, wenn keine ROIs definiert sind
			return  # Beendet die Funktion, falls keine ROIs vorhanden sind

		self.running = True  # Setzt den Status auf "laufend"
		print("Erkennung läuft...")  # Gibt eine Statusmeldung aus

		while self.cap.isOpened() and self.running:  # Schleife läuft, solange die Kamera geöffnet ist und das Programm aktiv bleibt
			ret, frame = self.cap.read()  # Liest ein Bild von der Kamera
			if not ret:  # Falls kein Bild gelesen werden kann, wird die Schleife beendet
				break

			frame_rgb = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)  # Spiegelt das Bild horizontal und konvertiert es von BGR nach RGB
			frame_annotated = self.detect_objects(frame_rgb)  # Ruft die Objekterkennung auf und annotiert das Bild

			# Übergibt das verarbeitete Bild an die GUI
			if self.frame_callback:
				self.frame_callback(frame_annotated)  # Führt die Callback-Funktion aus, falls vorhanden

		self.cap.release()  # Gibt die Kameraressourcen frei
		print("Erkennung gestoppt.")  # Gibt eine Statusmeldung aus

	def stop(self):
		"""Stoppt die Objekterkennung sicher."""
		self.running = False  # Setzt den Status auf "nicht laufend"
		print("Erkennung wird gestoppt...")  # Gibt eine Statusmeldung aus
