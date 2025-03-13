import os
import cv2  # OpenCV für Bildverarbeitung
import threading  # Für paralleles Ausführen der Objekterkennung
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QDialog  # PyQt6 für GUI-Elemente
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen  # PyQt6 für Bildverarbeitung und Zeichnen
from PyQt5.QtCore import Qt  # PyQt6 für Fenstersteuerung und Punktkoordinaten


class GUIApp(QWidget):
	def __init__(self, logic):
		super().__init__()
		self.logic = logic  # Speichert die Referenz zur Entscheidungslogik

		# Initialisierung aller Instanzvariablen vor UI-Aufbau
		self.roi_points = []  # Liste zum Speichern der gesetzten ROI-Punkte
		self.temp_roi = None  # Temporäres Rechteck während des Aufziehens
		self.image = None  # Variable zum Speichern des aktuellen Kamerabilds
		self.current_roi = 1  # Speichert, welche ROI aktuell gesetzt wird
		self.label = None  # GUI-Element zur Anzeige des Kamerabilds
		self.retake_picture_button= None # Button zumwiederholen des Fotos
		self.confirm_button = None  # Button zum Bestätigen der ROIs
		self.roi_reset_button = None  # Button zum Zurücksetzen der ROIs
		self.relais_on_button = None  # Button zum Einschalten des Relais
		self.relais_off_button = None  # Button zum Ausschalten des Relais
		self.confirm_button_bool = True  # Überprüfungsvariable zum nur einmaligen Abschicken der ROI

		self.initUI()  # Initialisiert die Benutzeroberfläche

	def initUI(self):
		"""Initialisiert die UI mit Button-Anordnung und Bildgröße"""
		self.setWindowTitle("Keye UI")  

		# Bildschirmgröße abrufen
		screen_size = QApplication.primaryScreen().size()
		screen_width = screen_size.width()
		screen_height = screen_size.height()

		# Fenstergröße anpassen
		self.setGeometry(0, 0, int(screen_width * 0.9), int(screen_height * 0.9))
		self.image_width = int(screen_width * 0.85)
		self.image_height = int(screen_height * 0.85)  

		# Bildanzeige-Label (zentriert)
		self.label = QLabel(self)
		self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.label.setFixedSize(self.image_width, self.image_height)  

		# Button-Höhe berechnen (10% der Bildschirmhöhe)
		button_height = int(screen_height * 0.1)

		# BUTTONS ERSTELLEN (feste Reihenfolge & Höhe)
		self.retake_picture_button = QPushButton("Bild erneut aufnehmen", self)
		self.retake_picture_button.setFixedHeight(button_height)
		self.retake_picture_button.setStyleSheet("background-color: gray; color: white; font-weight: bold; border: none;")
		self.retake_picture_button.clicked.connect(self.capture_frame)  # Bild erneut aufnehmen

		self.roi_reset_button = QPushButton("ROI Reset", self)
		self.roi_reset_button.setFixedHeight(button_height)
		self.roi_reset_button.setStyleSheet("background-color: gray; color: white; font-weight: bold; border: none;")
		self.roi_reset_button.clicked.connect(self.roi_reset)  # ROI zurücksetzen

		self.confirm_button = QPushButton("Bestätigen und Starten", self)
		self.confirm_button.setFixedHeight(button_height)
		self.confirm_button.setStyleSheet("background-color: gray; color: white; font-weight: bold; border: none;")
		self.confirm_button.setVisible(False)  # Anfangs unsichtbar
		self.confirm_button.clicked.connect(self.confirm_rois)  # ROIs bestätigen und starten

		self.relais_on_button = QPushButton("Relais EIN", self)
		self.relais_on_button.setFixedHeight(button_height)
		self.relais_on_button.setStyleSheet("background-color: green; color: white; font-weight: bold; border: none;")
		self.relais_on_button.setVisible(False)  # Anfangs unsichtbar
		self.relais_on_button.clicked.connect(self.logic.relais.on_all)  # Relais einschalten

		self.relais_off_button = QPushButton("Relais AUS", self)
		self.relais_off_button.setFixedHeight(button_height)
		self.relais_off_button.setStyleSheet("background-color: red; color: white; font-weight: bold; border: none;")
		self.relais_off_button.setVisible(False)  # Anfangs unsichtbar
		self.relais_off_button.clicked.connect(self.logic.relais.off_all)  # Relais ausschalten

		self.exit_button = QPushButton("Beenden", self)
		self.exit_button.setFixedHeight(button_height)
		self.exit_button.setStyleSheet("background-color: gray; color: white; font-weight: bold; border: none;")
		self.exit_button.clicked.connect(self.closeEvent)  # Programm sicher beenden

		# BUTTON-ANORDNUNG (HORIZONTAL & FESTE REIHENFOLGE)
		button_layout = QHBoxLayout()
		button_layout.addWidget(self.retake_picture_button)
		button_layout.addWidget(self.confirm_button)
		button_layout.addWidget(self.roi_reset_button)
		button_layout.addWidget(self.relais_on_button)
		button_layout.addWidget(self.relais_off_button)
		button_layout.addWidget(self.exit_button)

		# HAUPTLAYOUT (BILD OBEN, BUTTONS UNTEN)
		layout = QVBoxLayout()
		layout.addStretch()  # Platz vor dem Bild für Zentrierung
		layout.addWidget(self.label, alignment=Qt.AlignmentFlag.AlignCenter)
		layout.addStretch()  # Platz nach dem Bild
		layout.addLayout(button_layout)

		self.setLayout(layout)
		self.capture_frame()

	def capture_frame(self):
		"""Nimmt Einzelbild zum Setzen der ROIs auf"""
		cap = self.logic.detector.cap  # Nutze das bereits geöffnete Kamera-Objekt aus keye_detection.py
		cap.set(3, 1280)  # Setzt die Breite des Kamera-Frames auf 1280 Pixel
		cap.set(4, 720)  # Setzt die Höhe des Kamera-Frames auf 720 Pixel
		ret, frame = cap.read()  # Nimmt ein Einzelbild auf

		if ret:
			frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Konvertiert das Bild in RGB
			frame = cv2.flip(frame, 1)  # Spiegelt das Bild horizontal
			self.image = cv2.resize(frame, (self.image_width, self.image_height))  # Skaliert das Bild auf die Fenstergröße
			self.show_frame()  # Zeigt das Bild im GUI-Fenster an

		else:
			print("Kamerabild konnte nicht geladen werden")  # Fehlerausgabe, falls kein Bild aufgenommen werden konnte

	def show_frame(self):
		"""Zeigt das Bild aus capture_frame zum Setzen der ROIs in der UI an"""
		if self.image is not None:
			height, width, channel = self.image.shape  # Bestimmt Bildhöhe, -breite und Kanäle
			bytes_per_line = 3 * width  # Berechnet die Byte-Anzahl pro Zeile
			q_img = QImage(self.image.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)  # Erstellt ein QImage aus dem Kamerabild
			pixmap = QPixmap.fromImage(q_img)  # Wandelt das QImage in ein QPixmap um

			if len(self.roi_points) >= 2 or self.temp_roi:
				pixmap = self.draw_rois(pixmap)  # Zeichnet gesetzte ROIs ein

			self.label.setPixmap(pixmap)  # Zeigt das Bild mit ROIs im Label an

	def draw_rois(self, pixmap):
		"""Zeichnet die gesetzten ROIs auf das Bild."""
		painter = QPainter(pixmap)  # Erstellt einen Painter für das Bild
		pen = QPen(Qt.GlobalColor.red)  # Setzt die Zeichenfarbe auf Rot
		pen.setWidth(2)  # Setzt die Stiftbreite auf 2 Pixel
		painter.setPen(pen)  # Übernimmt den Stift in den Painter

		for i in range(0, len(self.roi_points), 2):  # Iteriert über die ROI-Punkte in Zweierschritten
			if i + 1 < len(self.roi_points):  # Prüft, ob ein vollständiges Rechteck vorhanden ist
				x1, y1 = self.roi_points[i]  # Erstes Eckpunktpaar
				x2, y2 = self.roi_points[i + 1]  # Zweites Eckpunktpaar
				painter.drawRect(x1, y1, x2 - x1, y2 - y1)  # Zeichnet das Rechteck

		if self.temp_roi:
			x1, y1, x2, y2 = self.temp_roi
			painter.drawRect(x1, y1, x2 - x1, y2 - y1)

		painter.end()  # Beendet den Painter
		return pixmap  # Gibt das geänderte Bild zurück

	def mousePressEvent(self, event):
		"""Erfasst die Mausposition, speichert die ROI-Punkte und zeigt ein temporäres Rechteck an."""
		if len(self.roi_points) < 4:
			x = int(event.pos().x() - self.label.geometry().x())
			y = int(event.pos().y() - self.label.geometry().y())  # Korrigiert die Mausposition relativ zum Bild
			x = max(0, min(x, self.label.width() - 1))
			y = max(0, min(y, self.label.height() - 1))
			self.roi_points.append((x, y))
			self.temp_roi = (x, y, x, y)  # Setzt das temporäre Rechteck
			print(f"mousePressEvent: ROI {self.current_roi}: Punkt {len(self.roi_points) % 2 + 1} gesetzt: {x}, {y}")
			self.show_frame()  # zeigt das Bild aktualisiert mit den aktuellen ROIs an, falls es welche gibt
			if len(self.roi_points) >= 4 and self.confirm_button_bool:
				self.confirm_button.setVisible(True)  # aktiviert den confirm_button, falls die ROI gesetzt wurden
				self.retake_picture_button.setVisible(False)  # Blendet den Bild-wiederholen-Button aus
			else:
				self.retake_picture_button.setVisible(True)  # Blendet den Bild-wiederholen-Button ein
				self.confirm_button.setVisible(False)  # deaktiviert den confirm_button, falls die ROI resettet wurden

	def confirm_rois(self):
		"""Bestätigt die gesetzten ROIs und übergibt sie an die Entscheidungslogik."""
		roi1 = (self.roi_points[0][0] / self.image_width, self.roi_points[0][1] / self.image_height, # ROI Koordinaten in absolute Werte zwischen 0 und 1 umrechnen und speichern
				self.roi_points[1][0] / self.image_width, self.roi_points[1][1] / self.image_height)
		roi2 = (self.roi_points[2][0] / self.image_width, self.roi_points[2][1] / self.image_height,
				self.roi_points[3][0] / self.image_width, self.roi_points[3][1] / self.image_height)

		# Ändert die Buttons von den ROI reset und Start zu Relais ein und aus
		self.confirm_button.setVisible(False)  # Blendet den Start-Button aus
		self.confirm_button_bool = False  # deaktiviert den confirm_button dauerhaft
		self.roi_reset_button.setVisible(False)  # Blendet den ROI-Reset-Button aus
		self.retake_picture_button.setVisible(False)  # Blendet den Bild-wiederholen-Button aus
		self.relais_on_button.setVisible(True)  # Zeigt den Relais-EIN-Button an
		self.relais_off_button.setVisible(True)  # Zeigt den Relais-AUS-Button an

		self.logic.set_rois(roi1, roi2)  # ROI werte an die decision_logic übergeben

		self.logic.detector.set_frame_callback(self.update_frame) # Setzt das Frame-Update-Callback für das Live-Bild der Erkennung
		detection_thread = threading.Thread(target=self.logic.start_detection)  # Startet die Personenerkennung als separaten Thread, damit andere Teile des Programms weiterlaufen können
		detection_thread.start()

	def roi_reset(self):
		self.roi_points.clear()  # leert die Liste der gesetzten ROI-punkte
		self.show_frame()  # zeigt das Bild aktualisiert ohne ROIs
		self.retake_picture_button.setVisible(True) # aktiviert den Bild noch einmal aufnehmen Button
		self.confirm_button.setVisible(False)  # deaktiviert den confirm_button

	def update_frame(self, frame):
		"""Aktualisiert das Bild in der GUI mit einem neuen Frame."""
		if frame is not None:
			# Bild auf die Größe des QLabel-Widgets skalieren (keine Farbänderung!)
			frame_resized = cv2.resize(frame, (self.label.width(), self.label.height()), interpolation=cv2.INTER_AREA)

			height, width, channel = frame_resized.shape  # Bilddimensionen bestimmen
			bytes_per_line = 3 * width  # Byte-Anzahl pro Zeile berechnen (RGB = 3 Kanäle)

			q_img = QImage(frame_resized.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)  # QImage aus den Bilddaten erstellen
			pixmap = QPixmap.fromImage(q_img)  # QPixmap für PyQt erzeugen

			self.label.setPixmap(pixmap)  # Das Bild im GUI-Label aktualisieren

	def closeEvent(self, event=None):
		"""Zeigt ein eigenes Dialogfenster für das Beenden an."""
		dialog = QDialog(self)
		dialog.setWindowTitle("Beenden")
		dialog.setFixedSize(int(self.image_width / 1.5), int(self.image_height / 3))  # Größe für Touchscreen optimiert

		# Nachrichtentext (zentriert)
		label = QLabel("Möchtest du das Fenster schließen oder den Raspberry Pi herunterfahren?", dialog)
		label.setStyleSheet("font-size: 18px;")  # Größere Schrift für bessere Lesbarkeit
		label.setAlignment(Qt.AlignCenter)  # Zentriert den Text horizontal & vertikal

		# Buttons mit fester Reihenfolge und Touchscreen-Größe
		button_size = (int(self.image_width / 5), int(self.image_height / 8))

		close_button = QPushButton("Fenster schließen", dialog)
		close_button.setFixedSize(*button_size)
		close_button.setStyleSheet("background-color: gray; color: white; border: none;")
		close_button.clicked.connect(lambda: dialog.done(1))  # Code 1 → Fenster schließen

		shutdown_button = QPushButton("RPi herunterfahren", dialog)
		shutdown_button.setFixedSize(*button_size)
		shutdown_button.setStyleSheet("background-color: gray; color: white; border: none;")
		shutdown_button.clicked.connect(lambda: dialog.done(2))  # Code 2 → Pi herunterfahren

		cancel_button = QPushButton("Abbrechen", dialog)
		cancel_button.setFixedSize(*button_size)
		cancel_button.setStyleSheet("background-color: gray; color: white; border: none;")
		cancel_button.clicked.connect(lambda: dialog.done(0))  # Code 0 → Abbrechen

		# Layout für Buttons (feste Reihenfolge)
		button_layout = QHBoxLayout()
		button_layout.addWidget(close_button)
		button_layout.addWidget(shutdown_button)
		button_layout.addWidget(cancel_button)

		# Hauptlayout
		layout = QVBoxLayout(dialog)
		layout.addWidget(label)
		layout.addLayout(button_layout)
		dialog.setLayout(layout)

		# Zeige den Dialog und warte auf die Auswahl
		result = dialog.exec()

		if result == 1:  # Fenster schließen
			self.logic.shutdown()
			self.close()
		elif result == 2:
			self.logic.shutdown()
			os.system("sudo shutdown -h now")
			self.close()
			

