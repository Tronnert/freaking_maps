import sys
from io import BytesIO
from PIL import Image, ImageQt
from PyQt5 import uic
import requests
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLCDNumber, QMainWindow
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QLabel, QLineEdit, QCheckBox, QPlainTextEdit



class Example(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("fucking_maps.ui", self)
        self.setFixedSize(self.width(), self.height())
        self.speed = 1.4
        self.delta = "0.005"
        self.param_l = 'map'
        self.point = ''
        self.top()

        self.map.clicked.connect(self.change_layer)
        self.sat.clicked.connect(self.change_layer)
        self.skl.clicked.connect(self.change_layer)

        self.find.clicked.connect(self.top)

    def change_layer(self):
        if self.sender().text() == 'Карта':
            self.param_l = 'map'
        elif self.sender().text() == 'Спутник':
            self.param_l = 'sat'
        elif self.sender().text() == 'Гибрид':
            self.param_l = 'skl'
        self.regenerate()

    def top(self):
        geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"
        geocoder_params = {
            "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
            "geocode": self.lineEdit.text(),
            "format": "json"}
        response = requests.get(geocoder_api_server, params=geocoder_params)
        json_response = response.json()
        toponym = json_response["response"]["GeoObjectCollection"][
            "featureMember"][0]["GeoObject"]
        toponym_coodrinates = toponym["Point"]["pos"]
        self.toponym_longitude, self.toponym_lattitude = toponym_coodrinates.split(" ")
        self.point = ",".join([self.toponym_longitude, self.toponym_lattitude]) + ',pmwtm1'
        self.regenerate()

    def regenerate(self):
        map_params = {
            "ll": ",".join([self.toponym_longitude, self.toponym_lattitude]),
            "spn": ",".join([self.delta, self.delta]),
            "l": self.param_l,
        }
        if self.point:
            map_params.update({'pt': self.point})
        map_api_server = "http://static-maps.yandex.ru/1.x/"
        response = requests.get(map_api_server, params=map_params)
        self.a = Image.open(BytesIO(response.content))
        self.b = ImageQt.ImageQt(self.a)
        self.pix = QPixmap.fromImage(self.b)
        self.label.setPixmap(self.pix)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_PageUp:
            self.delta = str(float(self.delta) * self.speed)
            if float(self.delta) >= 89:
                self.delta = '89.0'
            self.regenerate()
        elif event.key() == Qt.Key_PageDown:
            self.delta = str(float(self.delta) / self.speed)
            if float(self.delta) <= 0.000001:
                self.delta = '0.000001'
            self.regenerate()
        elif event.key() == Qt.Key_W:
            self.toponym_lattitude = float(self.toponym_lattitude)
            self.toponym_lattitude += float(self.delta)
            if self.toponym_lattitude >= 89 - float(self.delta):
                self.toponym_lattitude = 89 - float(self.delta)
            self.toponym_lattitude = str(self.toponym_lattitude)
            self.regenerate()
        elif event.key() == Qt.Key_S:
            self.toponym_lattitude = float(self.toponym_lattitude)
            self.toponym_lattitude -= float(self.delta)
            if self.toponym_lattitude <= -89 + float(self.delta):
                self.toponym_lattitude = -89 + float(self.delta)
            self.toponym_lattitude = str(self.toponym_lattitude)
            self.regenerate()
        elif event.key() == Qt.Key_A:
            self.toponym_longitude = float(self.toponym_longitude)
            self.toponym_longitude -= float(self.delta) * 2
            if self.toponym_longitude < -179:
                self.toponym_longitude = -179
            self.toponym_longitude = str(self.toponym_longitude)
            self.regenerate()
        elif event.key() == Qt.Key_D:
            self.toponym_longitude = float(self.toponym_longitude)
            self.toponym_longitude += float(self.delta) * 2
            if self.toponym_longitude > 179:
                self.toponym_longitude = 179
            self.toponym_longitude = str(self.toponym_longitude)
            self.regenerate()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example()
    ex.show()
    sys.exit(app.exec())
