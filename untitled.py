import sys
from io import BytesIO
from PIL import Image, ImageQt
from PyQt5 import uic
import requests
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLCDNumber, QMainWindow
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QLabel, QLineEdit, QCheckBox, QPlainTextEdit
import math


class Example(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("fucking_maps.ui", self)
        self.setFixedSize(self.width(), self.height())
        self.r_major = 6378137.000
        self.r_minor = 6356752.3142
        self.param_l = 'map'
        self.point = ''
        self.z = 13
        self.top()

        self.map.clicked.connect(self.change_layer)
        self.sat.clicked.connect(self.change_layer)
        self.skl.clicked.connect(self.change_layer)
        self.drop.clicked.connect(self.drop_def)
        self.on.toggled.connect(self.on_off_postal_code)
        self.off.toggled.connect(self.on_off_postal_code)

        self.find.clicked.connect(self.top)

    def change_layer(self):
        if self.sender().text() == 'Карта':
            self.param_l = 'map'
        elif self.sender().text() == 'Спутник':
            self.param_l = 'sat'
        elif self.sender().text() == 'Гибрид':
            self.param_l = 'sat,skl'
        self.regenerate()

    def top(self):
        geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"
        geocoder_params = {
            "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
            "geocode": self.input.text(),
            "format": "json"}
        response = requests.get(geocoder_api_server, params=geocoder_params)
        if not response:
            return
        json_response = response.json()
        if not json_response["response"]["GeoObjectCollection"]["featureMember"]:
            return
        toponym = json_response["response"]["GeoObjectCollection"][
            "featureMember"][0]["GeoObject"]
        toponym_coodrinates = toponym["Point"]["pos"]
        toponym_address = toponym["metaDataProperty"]["GeocoderMetaData"]["text"]
        toponym_postal_code = toponym["metaDataProperty"]["GeocoderMetaData"]['Address'].get('postal_code', '')
        if self.on.isChecked() and toponym_postal_code:
            toponym_address += ', ' + toponym_postal_code
        self.full.setText(toponym_address)
        if 'Point' not in json_response["response"]["GeoObjectCollection"]['metaDataProperty']['GeocoderResponseMetaData'].keys():
            self.toponym_longitude, self.toponym_lattitude = toponym_coodrinates.split(" ")
        self.point = ",".join(toponym_coodrinates.split(" ")) + ',pmwtm'
        self.regenerate()

    def regenerate(self):
        map_params = {
            "ll": ",".join([self.toponym_longitude, self.toponym_lattitude]),
            "l": self.param_l,
            "z": str(self.z)
        }
        if self.point:
            map_params.update({'pt': self.point})
        map_api_server = "http://static-maps.yandex.ru/1.x/"
        response = requests.get(map_api_server, params=map_params)
        if not response:
            return
        self.a = Image.open(BytesIO(response.content))
        self.b = ImageQt.ImageQt(self.a)
        self.pix = QPixmap.fromImage(self.b)
        self.label.setPixmap(self.pix)

    def drop_def(self):
        self.point = ''
        self.input.setText('')
        self.full.setText('')
        self.regenerate()

    def on_off_postal_code(self, checked):
        if checked:
            self.top()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_PageUp:
            self.z -= 1
            if self.z < 0:
                self.z = 0
            self.regenerate()
        elif event.key() == Qt.Key_PageDown:
            self.z += 1
            if self.z > 17:
                self.z = 17
            self.regenerate()
        elif event.key() == Qt.Key_W:
            y = self.merc_y(float(self.toponym_lattitude))
            new_lat = self.merc_lat((y * self.get_k() + 450 * 2) / self.get_k())
            if new_lat > 85.0842:
                new_lat = 85.0842
            self.toponym_lattitude = str(new_lat)
            self.regenerate()
        elif event.key() == Qt.Key_S:
            y = self.merc_y(float(self.toponym_lattitude))
            new_lat = self.merc_lat((y * self.get_k() - 450 * 2) / self.get_k())
            if new_lat < -85.0842:
                new_lat = -85.0842
            self.toponym_lattitude = str(new_lat)
            self.regenerate()
        elif event.key() == Qt.Key_A:
            x = self.merc_x(float(self.toponym_longitude))
            new_lon = self.merc_lon((x * self.get_k() - 600 * 2) / self.get_k())
            if new_lon < -180:
                new_lon = -180
            self.toponym_longitude = str(new_lon)
            self.regenerate()
        elif event.key() == Qt.Key_D:
            x = self.merc_x(float(self.toponym_longitude))
            new_lon = self.merc_lon((x * self.get_k() + 600 * 2) / self.get_k())
            if new_lon > 180:
                new_lon = 180
            self.toponym_longitude = str(new_lon)
            self.regenerate()

    def mousePressEvent(self, event):
        if 10 < event.x() < 610 and 20 < event.y() < 470:
            if event.button() == Qt.LeftButton or event.button() == Qt.RightButton:
                x0 = self.merc_x(float(self.toponym_longitude)) * self.get_k() + (event.x() - 310) * 2
                y0 = self.merc_y(float(self.toponym_lattitude)) * self.get_k() + (245 - event.y()) * 2
                lon = self.merc_lon(x0 / self.get_k())
                lat = self.merc_lat(y0 / self.get_k())
                self.input.setText(','.join(map(str, [lon, lat])))
                self.top()
                if event.button() == Qt.RightButton:
                    search_api_server = "https://search-maps.yandex.ru/v1/"
                    api_key = "dda3ddba-c9ea-4ead-9010-f43fbc15c6e3"
                    search_params = {
                        "apikey": api_key,
                        "text": self.full.text(),
                        "lang": "ru_RU",
                        "type": "biz"
                    }
                    response = requests.get(search_api_server, params=search_params)
                    if not response:
                        self.drop_def()
                        return
                    json_response = response.json()
                    organization = json_response["features"][0]
                    org_name = organization["properties"]["CompanyMetaData"]["name"]
                    org_address = organization["properties"]["CompanyMetaData"]["address"]
                    point = organization["geometry"]["coordinates"]
                    org_point = "{0},{1}".format(point[0], point[1])
                    # print((lon, lat), tuple(map(float, org_point.split(','))))
                    # print(self.lonlat_distance((lon, lat), tuple(map(float, org_point.split(',')))))
                    if self.lonlat_distance((lon, lat), tuple(map(float, org_point.split(',')))) <= 50:
                        self.point = org_point + ',pmwtm'
                        self.full.setText(self.full.text() + ' ' + org_name)
                        self.regenerate()

    def lonlat_distance(self, a, b):
        degree_to_meters_factor = 111 * 1000
        a_lon, a_lat = a
        b_lon, b_lat = b
        radians_lattitude = math.radians((a_lat + b_lat) / 2.)
        lat_lon_factor = math.cos(radians_lattitude)
        dx = abs(a_lon - b_lon) * degree_to_meters_factor * lat_lon_factor
        dy = abs(a_lat - b_lat) * degree_to_meters_factor
        distance = math.sqrt(dx * dx + dy * dy)
        return distance

    def merc_x(self, lon):
        return self.r_major * math.radians(lon)

    def merc_lon(self, x):
        return math.degrees(x / self.r_major)

    def merc_lat(self, y):
        iz_lon = y / self.r_major
        temp = self.r_minor / self.r_major
        eccent = math.sqrt(1 - temp ** 2)
        lon = 0
        for e in range(100):
            lon = -2 * math.atan((math.e ** -iz_lon) *
                                 (((1 - eccent * math.sin(lon)) / (1 + eccent * math.sin(lon))) ** (
                                         eccent / 2))) + math.pi / 2
        return round(math.degrees(lon), 7)

    def merc_y(self, lat):
        if lat > 89.5: lat = 89.5
        if lat < -89.5: lat = -89.5
        temp = self.r_minor / self.r_major
        eccent = math.sqrt(1 - temp ** 2)
        phi = math.radians(lat)
        sinphi = math.sin(phi)
        con = eccent * sinphi
        com = eccent / 2
        con = ((1.0 - con) / (1.0 + con)) ** com
        ts = math.tan((math.pi / 2 + phi) / 2) * con
        y = self.r_major * math.log(ts)
        return y

    def get_k(self):
        return 2 ** (8 + self.z) / self.r_major / math.pi


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example()
    ex.show()
    sys.exit(app.exec())
