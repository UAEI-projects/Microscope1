import sys
import cv2
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QColorDialog, QSlider, QPushButton, QLabel, QHBoxLayout,
    QFileDialog, QStatusBar, QMessageBox, QLineEdit, QFormLayout, QInputDialog
)
from PyQt6.QtGui import QImage, QPixmap,  QPainter, QPen
from PyQt6.QtCore import Qt, QTimer, QPoint
from datetime import datetime

# Класс для редактирования изображений
class ImageEditor(QWidget):
    def __init__(self, image=None):  # Инициализация редактора изображений
        super().__init__()
        self.setWindowTitle("Редактор изображений")
        self.image = image  # Исходное изображение
        self.temp_image = image.copy() if image is not None else None  # Копия изображения для редактирования
        self.drawing = False  # Флаг для рисования
        self.last_point = QPoint()  # Последняя точка, где был курсор
        self.pen_color = Qt.GlobalColor.black  # Цвет пера по умолчанию
        self.tool = "pen"  # Инструмент по умолчанию
        self.points = []  # Список точек для расчета площади и периметра
        self.scale_factor = 1  # Фактор масштабирования для калибровки
        self.area = 0  # Площадь
        self.perimeter = 0  # Периметр
        self.scale_line_start = None  # Начало линии для калибровки
        self.scale_line_end = None  # Конец линии для калибровки
        self.scale_length_real = None  # Реальная длина линии для калибровки
        self.is_scaling = False  # Флаг для калибровки
        self.initUI()  # Инициализация интерфейса

    def initUI(self):
        layout = QVBoxLayout(self)  # Основной вертикальный макет

        self.image_label = QLabel(self)  # Метка для отображения изображения
        layout.addWidget(self.image_label)

        # Панель инструментов
        btn_layout = QHBoxLayout()
        self.load_btn = QPushButton("Загрузить")
        self.load_btn.clicked.connect(self.load_image)  # Кнопка загрузки изображения
        btn_layout.addWidget(self.load_btn)

        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save_image)  # Кнопка сохранения изображения
        btn_layout.addWidget(self.save_btn)

        self.pen_btn = QPushButton("Карандаш")
        self.pen_btn.clicked.connect(lambda: self.select_tool("pen"))  # Кнопка выбора карандаша
        btn_layout.addWidget(self.pen_btn)

        self.eraser_btn = QPushButton("Ластик")
        self.eraser_btn.clicked.connect(lambda: self.select_tool("eraser"))  # Кнопка выбора ластика
        btn_layout.addWidget(self.eraser_btn)

        self.arrow_btn = QPushButton("Стрелка")
        self.arrow_btn.clicked.connect(lambda: self.select_tool("arrow"))  # Кнопка выбора стрелки
        btn_layout.addWidget(self.arrow_btn)

        self.text_btn = QPushButton("Текст")
        self.text_btn.clicked.connect(lambda: self.select_tool("text"))  # Кнопка добавления текста
        btn_layout.addWidget(self.text_btn)

        self.color_btn = QPushButton("Цвет")
        self.color_btn.clicked.connect(self.select_color)  # Кнопка выбора цвета
        btn_layout.addWidget(self.color_btn)

        layout.addLayout(btn_layout)

        # Калибровка
        calib_layout = QFormLayout()
        self.scale_input = QLineEdit(self)
        self.scale_input.setPlaceholderText("Введите калибровку (см/пиксель)")
        calib_layout.addRow("Калибровка:", self.scale_input)
        self.scale_input.returnPressed.connect(self.set_scale_factor)  # Установка масштаба
        layout.addLayout(calib_layout)

        # Отображение площади и периметра
        self.area_label = QLabel(f"Площадь: {self.area} см²", self)
        self.perimeter_label = QLabel(f"Периметр: {self.perimeter} см", self)
        layout.addWidget(self.area_label)
        layout.addWidget(self.perimeter_label)

        self.setLayout(layout)

        if self.image is not None:
            self.set_image(self.image)  # Установка изображения, если оно есть

    def load_image(self):
        # Загрузка изображения из файла
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите изображение", "", "Images (*.png *.jpg *.jpeg)")
        if file_path:
            self.image = cv2.imread(file_path)
            self.temp_image = self.image.copy()  # Сохраняем копию для редактирования
            self.set_image(self.image)

    def set_image(self, image):
        # Установка изображения в интерфейсе
        height, width, ch = image.shape
        bytes_per_line = ch * width
        q_img = QImage(image.data, width, height, bytes_per_line, QImage.Format.Format_BGR888)
        pixmap = QPixmap.fromImage(q_img)
        self.image_label.setPixmap(pixmap)

    def save_image(self):
        # Сохранение изображения
        if self.image is not None:
            file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить изображение", "", "Images (*.png *.jpg *.jpeg)")
            if file_path:
                cv2.imwrite(file_path, self.image)
                QMessageBox.information(self, "Сохранено", "Изображение успешно сохранено!")

    def select_tool(self, tool):
        # Выбор инструмента
        self.tool = tool

    def select_color(self):
        # Выбор цвета
        color = QColorDialog.getColor(self.pen_color, self)
        if color.isValid():
            self.pen_color = color

    def set_scale_factor(self):
        # Установка масштаба для калибровки
        try:
            scale = float(self.scale_input.text())
            if scale > 0:
                self.scale_factor = scale
            else:
                QMessageBox.warning(self, "Ошибка", "Невозможно установить отрицательное значение!")
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Введите числовое значение для калибровки!")

    def mousePressEvent(self, event):
        # Обработка нажатия мыши
        if event.button() == Qt.MouseButton.LeftButton:
            self.last_point = event.pos()
            if self.tool == "pen":
                self.drawing = True
            elif self.tool == "scale" and self.is_scaling:
                self.scale_line_start = event.pos()  # Начало линии для калибровки
            elif self.tool == "text":
                pass  # Добавление текста

    def mouseMoveEvent(self, event):
        # Обработка движения мыши
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
        # Обработка отпускания мыши
        if self.drawing and self.tool == "pen":
            self.drawing = False
            self.points.append(self.last_point)  # Добавление точки
            self.update_area_and_perimeter()  # Пересчет площади и периметра

        elif self.tool == "scale" and self.is_scaling:
            self.is_scaling = False
            self.scale_line_end = event.pos()
            self.update()
            self.ask_for_scale_length()  # Запрос реальной длины для калибровки

    def ask_for_scale_length(self):
        # Запрос реальной длины для калибровки
        length, ok = QInputDialog.getDouble(self, "Введите длину линейки", "Длина (см):", 1, 0, 1000, 2)
        if ok and length > 0:
            self.scale_length_real = length
            self.calculate_scale_factor()  # Расчет масштаба

    def calculate_scale_factor(self):
        # Расчет масштаба
        pixel_distance = np.linalg.norm(
            np.array([self.scale_line_end.x(), self.scale_line_end.y()]) -
            np.array([self.scale_line_start.x(), self.scale_line_start.y()])
        )
        self.scale_factor = pixel_distance / self.scale_length_real
        self.scale_input.setText(f"{self.scale_factor:.2f}")

    def update_area_and_perimeter(self):
        # Обновление площади и периметра
        if len(self.points) < 3:
            self.area = 0
            self.perimeter = 0
        else:
            contours = np.array([[(point.x(), point.y()) for point in self.points]], dtype=np.int32)
            area = cv2.contourArea(contours)
            perimeter = cv2.arcLength(contours, True)
            self.area = area / (self.scale_factor ** 2)  # Площадь в см²
            self.perimeter = perimeter / self.scale_factor  # Периметр в см

        self.area_label.setText(f"Площадь: {self.area:.2f} см²")
        self.perimeter_label.setText(f"Периметр: {self.perimeter:.2f} см")

    def paintEvent(self, event):
        # Отрисовка изображения и элементов
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.image_label.pixmap())  # Отображение изображения

        if self.points:
            pen = QPen(self.pen_color)
            pen.setWidth(5)
            painter.setPen(pen)
            for point in self.points:
                painter.drawEllipse(point, 5, 5)  # Отображение точек

        if self.scale_line_start and self.scale_line_end:
            painter.setPen(QPen(Qt.GlobalColor.red, 3, Qt.PenStyle.DashLine))
            painter.drawLine(self.scale_line_start, self.scale_line_end)  # Отображение линии калибровки

        painter.end()

# Класс для управления микроскопом
class MicroscopeControl(QMainWindow):
    def __init__(self):
        super().__init__()
        self.capture = None  # Захват видео
        self.timer = QTimer()  # Таймер для обновления кадров
        self.save_directory = None  # Директория для сохранения
        self.image = None  # Захваченное изображение
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Microscope Control')
        self.setGeometry(100, 100, 1700, 700)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Элементы управления
        self.captureButton = QPushButton('Захват кадра')
        self.captureButton.clicked.connect(self.captureFrame)  # Кнопка захвата кадра

        self.openEditorButton = QPushButton('Открыть редактор')
        self.openEditorButton.clicked.connect(self.openImageEditor)  # Кнопка открытия редактора

        layout.addWidget(self.captureButton)
        layout.addWidget(self.openEditorButton)

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        self.timer.timeout.connect(self.updateFrame)
        self.startVideoCapture()

    def startVideoCapture(self):
        # Запуск захвата видео
        self.capture = cv2.VideoCapture('http://<IP_Raspberry_Pi>:5000/video_feed')  # Подключение к камере
        self.timer.start(30)

    def updateFrame(self):
        # Обновление кадра
        if self.capture is not None:
            ret, frame = self.capture.read()
            if ret:
                self.image = frame  # Сохранение кадра

    def captureFrame(self):
        # Захват кадра
        if self.capture is not None:
            ret, frame = self.capture.read()
            if ret:
                now = datetime.now()
                timestamp = now.strftime("%Y.%m.%d-%H.%M.%S")
                file_path = f"{self.save_directory}/captured_frame_{timestamp}.png"
                cv2.imwrite(file_path, frame)
                QMessageBox.information(self, 'Захват кадра', f'Кадр сохранён: {file_path}')
                self.openImageEditor(frame)  # Открытие редактора с захваченным кадром

    def openImageEditor(self, frame=None):
        # Открытие редактора изображений
        if frame is None and self.image is None:
            QMessageBox.warning(self, "Ошибка", "Нет изображения для открытия в редакторе!")
            return

        editor = ImageEditor(image=frame if frame is not None else self.image)
        editor.show()

    def chooseDirectory(self):
        # Выбор директории для сохранения
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения кадра")
        if folder:
            self.save_directory = folder
            QMessageBox.information(self, 'Выбор папки', f'Папка выбрана: {folder}')
        else:
            QMessageBox.warning(self, 'Выбор папки', 'Папка не выбрана.')

    def closeEvent(self, event):
        # Закрытие приложения
        if self.capture is not None:
            self.capture.release()
        event.accept()

# Запуск приложения
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MicroscopeControl()
    ex.show()
    sys.exit(app.exec())