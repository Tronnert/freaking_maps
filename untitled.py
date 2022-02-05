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
        self.speed = 1.4
        self.top()
        self.delta = "0.005"
        self.regenerate()

    def top(self):
        geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"
        geocoder_params = {
            "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
            "geocode": 'москва',
            "format": "json"}
        response = requests.get(geocoder_api_server, params=geocoder_params)
        json_response = response.json()
        toponym = json_response["response"]["GeoObjectCollection"][
            "featureMember"][0]["GeoObject"]
        toponym_coodrinates = toponym["Point"]["pos"]
        self.toponym_longitude, self.toponym_lattitude = toponym_coodrinates.split(" ")

    def regenerate(self):
        map_params = {
            "ll": ",".join([self.toponym_longitude, self.toponym_lattitude]),
            "spn": ",".join([self.delta, self.delta]),
            "l": "map"
        }
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



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example()
    ex.show()
    sys.exit(app.exec())
