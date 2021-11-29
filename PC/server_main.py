from PyQt5.QtWidgets import *
from video import *
import cv2
import numpy as np
from os import listdir
from os.path import isfile, join
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from threading import Thread
import time
from PIL import Image
import sys

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)


class CWidget(QWidget):

    def __init__(self):
        super().__init__()
        size = QSize(1280,720)
        self.initUI(size)
        self.video = video(self, QSize(self.frm.width(), self.frm.height()))

    def initUI(self, size):

        vbox = QVBoxLayout()
        self.btn = QPushButton('서버 켜짐', self)
        self.btn.setCheckable(True)
        self.btn.setMaximumHeight(100)
        self.btn.clicked.connect(self.onoffCam)
        vbox.addWidget(self.btn)





        # video area
        self.frm = QLabel(self)
        self.frm.setFrameShape(QFrame.Panel)

        self.frm2 = QLabel(self)
        self.frm2.setFrameShape(QFrame.Panel)



        hbox = QHBoxLayout()
        hbox.addLayout(vbox)
        hbox.addWidget(self.frm, 1)
        hbox.addWidget(self.frm2, 1)
        self.setLayout(hbox)


        self.setFixedSize(size)
        self.move(100, 100)
        self.setWindowTitle('IMU센서_객체검출')
        self.show()

        self.btn2 = QPushButton('프로그램 종료', self)
        vbox.addWidget(self.btn2)
        self.btn2.clicked.connect(CWidget.close)




    def onoffCam(self, e):
        if self.btn.isChecked():
            self.btn.setText('서버 꺼짐')
            self.video.startCam()
        else:
            self.btn.setText('서버 켜짐')
            self.video.stopCam()




    def recvImage(self, img):
        self.frm.setPixmap(QPixmap.fromImage(img))
    def recvImage_2(self, img):
        self.frm2.setPixmap(QPixmap.fromImage(img))

    def closeEvent(self, e):
        self.video.stopCam()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = CWidget()
    sys.exit(app.exec_())
