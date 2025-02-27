import sys
import cv2
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QSlider, QPushButton, QLabel, QHBoxLayout, QFileDialog, QStatusBar, QMessageBox, QLineEdit
)
from PyQt6.QtGui import QImage, QPixmap, QColorDialog, QPainter, QPen
from PyQt6.QtCore import Qt, QTimer, QPoint
from datetime import datetime


class ImageEditor(QWidget):
    def __init__(self, image=None):
        super().__init__()
        self.setWindowTitle("Редактор изображений")
        self.image = image
        self.temp_image = None
        self.drawing = False
        self.last_point = QPoint()
        self.pen_color = Qt.GlobalColor.black
        self.tool = "pen"
        self.text_input = QLineEdit(self)
        self.text_input.setPlaceholderText("Введите текст и нажмите Enter")
        self.text_input.returnPressed.connect(self.add_text)
        self.text_input.hide()

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        self.image_label = QLabel(self)
        layout.addWidget(self.image_label)

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
        self.setLayout(layout)

        if self.image is not None:
            self.set_image(self.image)

    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите изображение", "", "Images (*.png *.jpg *.jpeg)")
        if file_path:
            self.image = cv2.imread(file_path)
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
        if tool == "text":
            self.text_input.show()

    def select_color(self):
        color = QColorDialog.getColor(self.pen_color, self)
        if color.isValid():
            self.pen_color = color


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
        self.setGeometry(100, 100, 800, 600)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Элементы управления
        self.captureButton = QPushButton('Захват кадра')
        self.captureButton.clicked.connect(self.captureFrame)

        self.openEditorButton = QPushButton('Открыть редактор')
        self.openEditorButton.clicked.connect(self.openImageEditor)  # Кнопка для открытия редактора

        layout.addWidget(self.captureButton)
        layout.addWidget(self.openEditorButton)

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        self.timer.timeout.connect(self.updateFrame)
        self.startVideoCapture()

    def startVideoCapture(self):
        # Подключение к камере
        self.capture = cv2.VideoCapture('http://<IP_Raspberry_Pi>:5000/video_feed')  # Вставьте IP Raspberry Pi
        self.timer.start(30)

    def updateFrame(self):
        if self.capture is not None:
            ret, frame = self.capture.read()
            if ret:
                self.image = frame  # Сохраняем захваченное изображение
                # Отображаем его на экране в интерфейсе (можно добавить сюда обработку через QPixmap)

    def captureFrame(self):
        if self.capture is not None:
            ret, frame = self.capture.read()
            if ret:
                # Сохраняем кадр в файл
                now = datetime.now()
                timestamp = now.strftime("%Y.%m.%d-%H.%M.%S")
                file_path = f"{self.save_directory}/captured_frame_{timestamp}.png"
                cv2.imwrite(file_path, frame)
                QMessageBox.information(self, 'Захват кадра', f'Кадр сохранён: {file_path}')

                # Открытие редактора с захваченным изображением
                self.openImageEditor(frame)

    def openImageEditor(self, frame=None):
        if frame is None and self.image is None:
            QMessageBox.warning(self, "Ошибка", "Нет изображения для открытия в редакторе!")
            return

        editor = ImageEditor(image=frame if frame is not None else self.image)  # Передаем захваченное изображение в редактор
        editor.show()

    def chooseDirectory(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения кадра")
        if folder:
            self.save_directory = folder
            QMessageBox.information(self, 'Выбор папки', f'Папка выбрана: {folder}')
        else:
            QMessageBox.warning(self, 'Выбор папки', 'Папка не выбрана.')

    def closeEvent(self, event):
        if self.capture is not None:
            self.capture.release()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MicroscopeControl()
    ex.show()
    sys.exit(app.exec())