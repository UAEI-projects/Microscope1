import sys
import cv2
import numpy as np
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QLabel
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import QTimer
from editor import ImageEditor  # Подключаем редактор изображений

class MicroscopeApp(QMainWindow):
    def init(self):
        """Основной класс приложения управления микроскопом."""
        super().init()
        self.setWindowTitle("Микроскоп - Захват и Анализ")
        self.setGeometry(100, 100, 800, 600)

        # Кнопка захвата кадра
        self.capture_btn = QPushButton("Захватить кадр", self)
        self.capture_btn.setGeometry(50, 500, 200, 40)
        self.capture_btn.clicked.connect(self.capture_frame)

        # Кнопка загрузки изображения
        self.load_btn = QPushButton("Загрузить изображение", self)
        self.load_btn.setGeometry(300, 500, 200, 40)
        self.load_btn.clicked.connect(self.load_image)

        # Метка для отображения видео
        self.video_label = QLabel(self)
        self.video_label.setGeometry(50, 50, 640, 480)

        # Инициализация камеры
        self.camera = cv2.VideoCapture(0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_frame(self):
        """Обновляет кадр с камеры в реальном времени."""
        ret, frame = self.camera.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            self.video_label.setPixmap(QPixmap.fromImage(q_img))

    def capture_frame(self):
        """Захватывает кадр и передает его в редактор."""
        ret, frame = self.camera.read()
        if ret:
            file_name = "captured_frame.png"
            cv2.imwrite(file_name, frame)
            self.open_editor(file_name)

    def load_image(self):
        """Загружает изображение с диска и открывает его в редакторе."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Выбрать изображение", "", "Изображения (*.png *.jpg *.jpeg)")
        if file_path:
            self.open_editor(file_path)

    def open_editor(self, file_path):
        """Открывает редактор изображений."""
        self.editor = ImageEditor(file_path)
        self.editor.show()

    def closeEvent(self, event):
        """Закрытие приложения и освобождение камеры."""
        self.camera.release()
        event.accept()

if name == "main":
    app = QApplication(sys.argv)
    window = MicroscopeApp()
    window.show()
    sys.exit(app.exec())