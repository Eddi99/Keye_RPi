import cv2  # OpenCV für Bildverarbeitung
import threading  # Für paralleles Ausführen der Objekterkennung
from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget, QHBoxLayout  # PyQt6 für GUI-Elemente
from PyQt6.QtGui import QPixmap, QImage, QPainter, QPen  # PyQt6 für Bildverarbeitung und Zeichnen
from PyQt6.QtCore import Qt  # PyQt6 für Fenstersteuerung und Punktkoordinaten


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
        self.confirm_button = None  # Button zum Bestätigen der ROIs
        self.roi_reset_button = None  # Button zum Zurücksetzen der ROIs
        self.relais_on_button = None  # Button zum Einschalten des Relais
        self.relais_off_button = None  # Button zum Ausschalten des Relais
        self.confirm_button_bool = True  # Überprüfungsvariable zum nur einmaligen Abschicken der ROI

        self.initUI()  # Initialisiert die Benutzeroberfläche

    def initUI(self):
        """initialisiert die Bestandteile der UI"""
        self.setWindowTitle("Keye UI")  # Setzt den Fenstertitel
        self.setGeometry(100, 100, 900, 700)  # Erhöht die Fenstergröße für bessere Anpassung

        self.label = QLabel(self)  # Erstellt ein Label für das Bild
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Zentriert das Bild im Label
        self.label.setFixedSize(1280, 720)  # Setzt eine feste Größe für das Bild

        # Initial sichtbare Buttons zur ROI Festlegung und zum Starten des Programms
        self.confirm_button = QPushButton("Bestätigen und Starten", self)  # Erstellt einen Bestätigungsbutton
        self.confirm_button.setEnabled(False)  # Deaktiviert den Button initial
        self.confirm_button.clicked.connect(self.confirm_rois)  # Verbindet den Button mit der Bestätigungsfunktion

        self.roi_reset_button = QPushButton("ROI Reset", self)  # Erstellt einen Button, der die ROIs zurücksetzt
        self.roi_reset_button.setEnabled(True)  # aktiviert den Button initial
        self.roi_reset_button.clicked.connect(self.roi_reset)  # Verbindet den Button mit der roi_reset-Funktion

        # Neue Buttons zur Relais-Steuerung (anfangs ausgeblendet)
        self.relais_on_button = QPushButton("Relais EIN", self)
        self.relais_on_button.setStyleSheet("background-color: green; color: white;")  # Grüne Farbe für EIN
        self.relais_on_button.clicked.connect(self.logic.relais.on_all)  # Schaltet Relais ein
        self.relais_on_button.setVisible(False)  # Anfangs nicht sichtbar

        self.relais_off_button = QPushButton("Relais AUS", self)
        self.relais_off_button.setStyleSheet("background-color: red; color: white;")  # Rote Farbe für AUS
        self.relais_off_button.clicked.connect(self.logic.relais.off_all)  # Schaltet Relais aus
        self.relais_off_button.setVisible(False)  # Anfangs nicht sichtbar

        layout = QVBoxLayout()  # Erstellt ein vertikales Layout

        image_layout = QHBoxLayout() # Neues zentriertes Layout für das Bild
        image_layout.addStretch()  # Platz vor dem Bild hinzufügen
        image_layout.addWidget(self.label)  # Bild einfügen
        image_layout.addStretch()  # Platz nach dem Bild hinzufügen

        layout.addLayout(image_layout)  # Füge das horizontale Layout in das Hauptlayout ein
        layout.addWidget(self.confirm_button)  # Fügt den Bestätigungsbutton zum Layout hinzu
        layout.addWidget(self.roi_reset_button)  # Fügt den ROI-reset-Button zum Layout hinzu
        layout.addWidget(self.relais_on_button)  # Fügt den Relais-EIN-Button hinzu
        layout.addWidget(self.relais_off_button)  # Fügt den Relais-AUS-Button hinzu
        self.setLayout(layout)  # Setzt das Layout für das Fenster

        self.capture_frame()  # Nimmt ein Standbild von der Kamera auf

    def capture_frame(self):
        """Nimmt Einzelbild zum Setzen der ROIs auf"""
        cap = cv2.VideoCapture(1)  # Öffnet die Kamera mit Index 1
        cap.set(3, 1280)  # Setzt die Breite des Kamera-Frames auf 1280 Pixel
        cap.set(4, 720)  # Setzt die Höhe des Kamera-Frames auf 720 Pixel
        ret, frame = cap.read()  # Nimmt ein Einzelbild auf
        cap.release()  # Schließt die Kamera

        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Konvertiert das Bild in RGB
            frame = cv2.flip(frame, 1)  # Spiegelt das Bild horizontal
            self.image = cv2.resize(frame, (1280, 720))  # Skaliert das Bild auf die Fenstergröße
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
            x = int(event.position().x() - self.label.geometry().x())
            y = int(event.position().y() - self.label.geometry().y())  # Korrigiert die Mausposition relativ zum Bild
            x = max(0, min(x, self.label.width() - 1))
            y = max(0, min(y, self.label.height() - 1))
            self.roi_points.append((x, y))
            self.temp_roi = (x, y, x, y)  # Setzt das temporäre Rechteck
            # print(f"mousePressEvent: ROI {self.current_roi}: Punkt {len(self.roi_points) % 2 + 1} gesetzt: {x}, {y}")
            self.show_frame()  # zeigt das Bild aktualisiert mit den aktuellen ROIs an, falls es welche gibt
            if len(self.roi_points) == 4 and self.confirm_button_bool:
                self.confirm_button.setEnabled(True)  # aktiviert den confirm_button, falls die ROI gesetzt wurden
            else:
                self.confirm_button.setEnabled(False)  # deaktiviert den confirm_button, falls die ROI resettet wurden

    def confirm_rois(self):
        """Bestätigt die gesetzten ROIs und übergibt sie an die Entscheidungslogik."""
        roi1 = (self.roi_points[0][0] / 1280, self.roi_points[0][1] / 720,
                # ROI Koordinaten in absolute Werte zwischen 0 und 1 umrechnen und speichern
                self.roi_points[1][0] / 1280, self.roi_points[1][1] / 720)
        roi2 = (self.roi_points[2][0] / 1280, self.roi_points[2][1] / 720,
                self.roi_points[3][0] / 1280, self.roi_points[3][1] / 720)

        # Ändert die Buttons von den ROI reset und Start zu Relais ein und aus
        self.confirm_button.setEnabled(False)  # deaktiviert den confirm_button
        self.confirm_button_bool = False  # deaktiviert den confirm_button dauerhaft
        self.roi_reset_button.setEnabled(False)  # verhindert den ROI-reset, wenn die Objekterkennung gestartet wurde
        self.confirm_button.setVisible(False)  # Blendet den Start-Button aus
        self.roi_reset_button.setVisible(False)  # Blendet den ROI-Reset-Button aus
        self.relais_on_button.setVisible(True)  # Zeigt den Relais-EIN-Button an
        self.relais_off_button.setVisible(True)  # Zeigt den Relais-AUS-Button an

        self.logic.set_rois(roi1, roi2)  # ROI werte an die decision_logic übergeben

        self.logic.detector.set_frame_callback(self.update_frame) # Setzt das Frame-Update-Callback für das Live-Bild der Erkennung
        detection_thread = threading.Thread(target=self.logic.start_detection)  # Startet die Personenerkennung als separaten Thread, damit andere Teile des Programms weiterlaufen können
        detection_thread.start()

    def roi_reset(self):
        self.roi_points.clear()  # leert die Liste der gesetzten ROI-punkte
        self.show_frame()  # zeigt das Bild aktualisiert ohne ROIs
        self.confirm_button.setEnabled(False)  # deaktiviert den confirm_button

    def update_frame(self, frame):
        """Aktualisiert das Bild in der GUI mit einem neuen Frame."""
        height, width, channel = frame.shape  # Bestimmt die Höhe, Breite und Anzahl der Farbkanäle des Bildes
        bytes_per_line = 3 * width  # Berechnet die Anzahl der Bytes pro Zeile (3 Bytes pro Pixel für RGB)
        q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)  # Erstellt ein QImage-Objekt aus den Bilddaten für die Anzeige in der GUI
        pixmap = QPixmap.fromImage(q_img)  # Wandelt das QImage in ein QPixmap um, das in PyQt-Anwendungen genutzt wird

        self.label.setPixmap(pixmap)  # Setzt das aktualisierte Bild im GUI-Label

    def closeEvent(self, event):
        """Führt die Funktion zum sicheren Beenden beim Schließen des Fensters aus"""
        self.logic.shutdown()  # beendet die decision_logic Instanz
        self.close()  # schließt das Fenster
