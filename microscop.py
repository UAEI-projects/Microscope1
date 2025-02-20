from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QSlider,
    QPushButton,
    QLabel,
    QHBoxLayout,
    QFileDialog,
    QStatusBar,
    QMessageBox,
    QLineEdit,
    QColorDialog,
    QInputDialog,
    QFormLayout
)
from PyQt6.QtGui import QImage, QPixmap,  QPainter, QPen
from PyQt6.QtCore import Qt, QTimer, QPoint
import sys
import cv2
import numpy as np
from datetime import datetime
from math import sqrt


class ImageEditor(QWidget):
    def __init__(self, image=None):
        super().__init__()
        self.setWindowTitle("Редактор изображений")
        self.image = image
        self.temp_image = image.copy() if image is not None else None
        self.drawing = False
        self.last_point = QPoint()
        self.pen_color = Qt.GlobalColor.black
        self.tool = "pen"
        self.points = []  # Список точек, которые будут добавляться
        self.scale_factor = 1  # Фактор для калибровки (см. шаг калибровки)
        self.area = 0
        self.perimeter = 0
        self.scale_line_start = None
        self.scale_line_end = None  # Начало и конец линии линейки
        self.scale_length_real = None  # Реальная длина линейки
        self.is_scaling = False  # Флаг для калибровки
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        self.image_label = QLabel(self)
        layout.addWidget(self.image_label)

        # Инструменты
        btn_layout = QHBoxLayout()
        self.load_btn = QPushButton("Загрузить")
        self.load_btn.clicked.connect(self.load_image)
        btn_layout.addWidget(self.load_btn)

        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save_image)
        btn_layout.addWidget(self.save_btn)

        self.pen_btn = QPushButton("Карандаш")
        self.pen_btn.clicked.connect(lambda: self.select_tool("pen"))
        btn_layout.addWidget(self.pen_btn)

        self.eraser_btn = QPushButton("Ластик")
        self.eraser_btn.clicked.connect(lambda: self.select_tool("eraser"))
        btn_layout.addWidget(self.eraser_btn)

        self.arrow_btn = QPushButton("Стрелка")
        self.arrow_btn.clicked.connect(lambda: self.select_tool("arrow"))
        btn_layout.addWidget(self.arrow_btn)

        self.text_btn = QPushButton("Текст")
        self.text_btn.clicked.connect(lambda: self.select_tool("text"))
        btn_layout.addWidget(self.text_btn)

        self.color_btn = QPushButton("Цвет")
        self.color_btn.clicked.connect(self.select_color)
        btn_layout.addWidget(self.color_btn)

        layout.addLayout(btn_layout)

        # Калибровка
        calib_layout = QFormLayout()
        self.scale_input = QLineEdit(self)
        self.scale_input.setPlaceholderText("Введите калибровку (см/пиксель)")
        calib_layout.addRow("Калибровка:", self.scale_input)
        self.scale_input.returnPressed.connect(self.set_scale_factor)
        layout.addLayout(calib_layout)

        # Площадь и периметр
        self.area_label = QLabel(f"Площадь: {self.area} см²", self)
        self.perimeter_label = QLabel(f"Периметр: {self.perimeter} см", self)
        layout.addWidget(self.area_label)
        layout.addWidget(self.perimeter_label)

        self.setLayout(layout)

        if self.image is not None:
            self.set_image(self.image)

    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите изображение", "", "Images (*.png *.jpg *.jpeg)")
        if file_path:
            self.image = cv2.imread(file_path)
            self.temp_image = self.image.copy()  # сохраняем копию для редактирования
            self.set_image(self.image)

    def set_image(self, image):
        height, width, ch = image.shape
        bytes_per_line = ch * width
        q_img = QImage(image.data, width, height, bytes_per_line, QImage.Format.Format_BGR888)
        pixmap = QPixmap.fromImage(q_img)

        self.image_label.setPixmap(pixmap)

    def save_image(self):
        if self.image is not None:
            file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить изображение", "", "Images (*.png *.jpg *.jpeg)")
            if file_path:
                cv2.imwrite(file_path, self.image)
                QMessageBox.information(self, "Сохранено", "Изображение успешно сохранено!")

    def select_tool(self, tool):
        self.tool = tool

    def select_color(self):
        color = QColorDialog.getColor(self.pen_color, self)
        if color.isValid():
            self.pen_color = color

    def set_scale_factor(self):
        try:
            scale = float(self.scale_input.text())
            if scale > 0:
                self.scale_factor = scale
            else:
                QMessageBox.warning(self, "Ошибка", "Невозможно установить отрицательное значение!")
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Введите числовое значение для калибровки!")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.last_point = event.pos()
            if self.tool == "pen":
                self.drawing = True
            elif self.tool == "scale" and self.is_scaling:
                # Начало рисования линейки
                self.scale_line_start = event.pos()
            elif self.tool == "text":
                # Место для добавления текста
                pass

    def mouseMoveEvent(self, event):
        if self.drawing and self.tool == "pen":
            painter = QPainter(self.temp_image)
            painter.setPen(QPen(self.pen_color, 5, Qt.PenStyle.SolidLine))
            painter.drawLine(self.last_point, event.pos())
            self.last_point = event.pos()
            self.update()

        elif self.tool == "scale" and self.is_scaling:
            self.scale_line_end = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if self.drawing and self.tool == "pen":
            self.drawing = False
            self.points.append(self.last_point)  # Добавляем точку

            # Пересчитываем площадь и периметр
            self.update_area_and_perimeter()

        elif self.tool == "scale" and self.is_scaling:
            self.is_scaling = False
            self.scale_line_end = event.pos()  # Конец линейки
            self.update()

            # Расчет реальной длины линии
            self.ask_for_scale_length()

    def ask_for_scale_length(self):
        # Диалог для ввода реальной длины линии
        length, ok = QInputDialog.getDouble(self, "Введите длину линейки", "Длина (см):", 1, 0, 1000, 2)
        if ok and length > 0:
            self.scale_length_real = length  # Сохраняем длину линейки в см
            self.calculate_scale_factor()

    def calculate_scale_factor(self):
        # Вычисляем калибровку: пиксели на 1 см
        pixel_distance = np.linalg.norm(
            np.array([self.scale_line_end.x(), self.scale_line_end.y()]) -
            np.array([self.scale_line_start.x(), self.scale_line_start.y()])
        )
        self.scale_factor = pixel_distance / self.scale_length_real  # Калибровка: пиксели/см
        self.scale_input.setText(f"{self.scale_factor:.2f}")

    def update_area_and_perimeter(self):
        if len(self.points) < 3:
            self.area = 0
            self.perimeter = 0
        else:
            # Вычисляем периметр и площадь по точкам
            contours = np.array([[(point.x(), point.y()) for point in self.points]], dtype=np.int32)
            area = cv2.contourArea(contours)
            perimeter = cv2.arcLength(contours, True)

            # Переводим в реальные единицы с учетом калибровки
            self.area = area / (self.scale_factor ** 2)  # Площадь в см²
            self.perimeter = perimeter / self.scale_factor  # Периметр в см

        self.area_label.setText(f"Площадь: {self.area:.2f} см²")
        self.perimeter_label.setText(f"Периметр: {self.perimeter:.2f} см")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.image_label.pixmap())  # Отображаем изображение

        if self.points:
            pen = QPen(self.pen_color)
            pen.setWidth(5)
            painter.setPen(pen)
            for point in self.points:
                painter.drawEllipse(point, 5, 5)  # Отображаем точки

        # Отображаем линейку
        if self.scale_line_start and self.scale_line_end:
            painter.setPen(QPen(Qt.GlobalColor.red, 3, Qt.PenStyle.DashLine))
            painter.drawLine(self.scale_line_start, self.scale_line_end)  # Рисуем линейку

        painter.end()


class MicroscopeControl(QMainWindow):
    def __init__(self):
        super().__init__()
        self.capture = None
        self.timer = QTimer()
        self.save_directory = None  # Путь для сохранения
        self.image = None  # Добавлено для хранения захваченного изображения
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Microscope Control')
        self.setGeometry(100, 100, 1280, 720)
        # Остальная логика для управления захватом кадров

app = QApplication(sys.argv)
window = MicroscopeControl()
window.show()
sys.exit(app.exec())