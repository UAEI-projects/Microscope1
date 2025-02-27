import sys
import cv2
import numpy as np
from PyQt6.QtWidgets import QMainWindow, QLabel, QPushButton, QFileDialog, QMessageBox
from PyQt6.QtGui import QPixmap, QImage, QPainter, QPen
from PyQt6.QtCore import Qt, QPoint

class ImageEditor(QMainWindow):
    def init(self, image_path):
        """Редактор изображений с функциями рисования и калибровки."""
        super().init()
        self.setWindowTitle("Редактор изображений")
        self.setGeometry(200, 200, 900, 700)

        # Оригинальное изображение
        self.image_path = image_path
        self.original_pixmap = QPixmap(self.image_path)

        # Метка для отображения изображения
        self.image_label = QLabel(self)
        self.image_label.setPixmap(self.original_pixmap)
        self.image_label.setGeometry(20, 20, self.original_pixmap.width(), self.original_pixmap.height())

        # Кнопки инструментов
        self.pen_btn = QPushButton("Карандаш", self)
        self.pen_btn.setGeometry(750, 50, 120, 30)
        self.pen_btn.clicked.connect(lambda: self.set_tool("pen"))

        self.eraser_btn = QPushButton("Ластик", self)
        self.eraser_btn.setGeometry(750, 90, 120, 30)
        self.eraser_btn.clicked.connect(lambda: self.set_tool("eraser"))

        self.measure_btn = QPushButton("Измерить", self)
        self.measure_btn.setGeometry(750, 130, 120, 30)
        self.measure_btn.clicked.connect(lambda: self.set_tool("measure"))

        self.calibrate_btn = QPushButton("Калибровка", self)
        self.calibrate_btn.setGeometry(750, 170, 120, 30)
        self.calibrate_btn.clicked.connect(self.calibrate)

        self.save_btn = QPushButton("Сохранить", self)
        self.save_btn.setGeometry(750, 210, 120, 30)
        self.save_btn.clicked.connect(self.save_image)

        # Настройки рисования
        self.tool = "pen"
        self.drawing = False
        self.last_point = QPoint()
        self.image = self.original_pixmap.toImage()

    def set_tool(self, tool):
        """Выбор инструмента (карандаш, ластик, измерение)."""
        self.tool = tool

    def mousePressEvent(self, event):
        """Обработка начала рисования."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = True
            self.last_point = event.position().toPoint()

    def mouseMoveEvent(self, event):
        """Рисование или стирание."""
        if self.drawing and self.tool in ["pen", "eraser"]:
            painter = QPainter(self.image)
            pen = QPen(Qt.GlobalColor.red, 3) if self.tool == "pen" else QPen(Qt.GlobalColor.white, 10)
            painter.setPen(pen)
            painter.drawLine(self.last_point, event.position().toPoint())
            self.last_point = event.position().toPoint()
            self.update_image()

    def mouseReleaseEvent(self, event):
        """Завершение рисования."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = False

    def update_image(self):
        """Обновление изображения после рисования."""
        self.image_label.setPixmap(QPixmap.fromImage(self.image))

    def calibrate(self):
        """Запуск калибровки с использованием линейки."""
        QMessageBox.information(self, "Калибровка", "Выберите эталонный объект для настройки масштаба.")

    def save_image(self):
        """Сохранение изображения."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить изображение", "", "PNG (*.png);;JPEG (*.jpg)")
        if file_path:
            self.image.save(file_path)

if name == "main":
    app = QApplication(sys.argv)
    editor = ImageEditor("captured_frame.png")
    editor.show()
    sys.exit(app.exec())