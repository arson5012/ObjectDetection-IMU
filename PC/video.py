from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from threading import Thread
import threading
import cv2
import time
import sys
import numpy as np
from os import listdir
from os.path import isfile, join
from PIL import Image
import os
import ctypes
import socket
import pickle
import struct
import os
import sys
import openpyxl
import copy


class sendcode():
    def __init__(self):
        self.clients = []  
        # 접속한 클라이언트를 담당하는 Client 객체 저장
    def addClient(self, c):  
        # 클라이언트 하나를 추가
        self.clients.append(c)
    def delClent(self, c):  
        # 클라이언트 하나를 삭제
        self.clients.remove(c)
    def sendAllClients(self, msg):
        for c in self.clients:
            c.sendMsg(msg)


class sendClient():
    def __init__(self, id, soc, ss):
        self.id = id  # 클라이언트 id
        self.soc = soc
        self.sendcode = ss

    def recvMsg(self):
        while True:
            data2 = self.soc.recv(1024)
            msg = self.soc.send(data2)

            if msg == 'stop':
                self.sendMsg(msg) 
                print("소켓 종료")
                break

            msg = self.id + ': ' + (str(msg))
            self.sendcode.sendAllClients(msg)

        self.sendcode.delClent(self)
        self.sendcode.sendAllClients(self.id + '_소켓 종료')

    def sendMsg(self, msg):
        self.soc.sendall(msg.encode(encoding='utf-8'))

    def run(self):
        t = threading.Thread(target=self.recvMsg, args=())
        t.start()


class video(QObject):
    sendImage = pyqtSignal(QImage)
    sendImage2 = pyqtSignal(QImage)

    def __init__(self, widget, size):
        super().__init__()
        self.widget = widget
        self.size = size
        self.sendImage.connect(self.widget.recvImage)
        self.sendImage2.connect(self.widget.recvImage_2)
        self.Separation= sendcode()
        self.server_soc = None

    def setOption(self, option):
        self.option = option

    def startCam(self):
        self.bThread = True
        self.thread = Thread(target=self.threadFunc)
        self.thread.start()

    def stopCam(self):
        self.bThread = False
        print("소켓 통신 종료")

    def threadFunc(self):
        if self.bThread == True:
            wb = openpyxl.Workbook()
            wb.active.title = 'Detection_sheet'
            xls = wb['Detection_sheet']
            xls['{col}{row}'.format(col=chr(ord('A')), row=1)] = 'shape'
            xls['{col}{row}'.format(col=chr(ord('B')), row=1)] = 'left_top_x'
            xls['{col}{row}'.format(col=chr(ord('C')), row=1)] = 'left_top_y'
            xls['{col}{row}'.format(col=chr(ord('D')), row=1)] = 'width'
            xls['{col}{row}'.format(col=chr(ord('E')), row=1)] = 'height'

            net = cv2.dnn.readNet("yolov4-tiny-figure_final.weights", "yolov4-tiny-figure.cfg")
            classes = []
            with open("figure.names", "r") as f:
                classes = [line.strip() for line in f.readlines()]

            layer_names = net.getLayerNames()
            output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

            ip = 'IPV4 주소'  # ip 주소
            port = 3333  # port 번호

            server_soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_soc.bind((ip, port))
            server_soc.listen()
            print("클라이언트 연결 대기")

            c_soc, addr = server_soc.accept()
            print(addr)

            s_soc, addr2 = server_soc.accept()
            print(addr2)
            print("클라이언트 연결 성공")

            cnt = 0

            data = b""  # 수신한 데이터를 넣을 변수
            payload_size = struct.calcsize(">L")

            while True:
                # 프레임 수신
                while len(data) < payload_size:
                    data += c_soc.recv(1024)
                packed_msg_size = data[:payload_size]
                data = data[payload_size:]
                msg_size = struct.unpack(">L", packed_msg_size)[0]
                while len(data) < msg_size:
                    data += c_soc.recv(1024)
                frame_data = data[:msg_size]
                data = data[msg_size:]

                frame = pickle.loads(frame_data, fix_imports=True,encoding="bytes")  # 직렬화되어 있는 binary file로 부터 객체로 역직렬화
                frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)  # 프레임 디코딩
                frame = cv2.resize(frame, None, fx=0.4, fy=0.4)
                cf = copy.deepcopy(frame)

                msg1 = s_soc.recv(1024)
                id2 = msg1.decode()
                print(id2)

                if id2 == '움직임':
                    cnt = 1
                if cnt == 1 and id2 == '정지':

                    height, width, channels = cf.shape

                    blob = cv2.dnn.blobFromImage(cf, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
                    net.setInput(blob)
                    outs = net.forward(output_layers)

                    class_ids = []
                    confidences = []
                    boxes = []
                    for out in outs:
                        for detection in out:
                            scores = detection[5:]
                            class_id = np.argmax(scores)
                            confidence = scores[class_id]
                            if confidence > 0.85:
                                center_x = int(detection[0] * width)
                                center_y = int(detection[1] * height)
                                w = int(detection[2] * width)
                                h = int(detection[3] * height)
                                x = int(center_x - w / 2)
                                y = int(center_y - h / 2)
                                boxes.append([x, y, w, h])
                                confidences.append(float(confidence))
                                class_ids.append(class_id)

                    indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)

                    font = cv2.FONT_HERSHEY_PLAIN
                    for i in range(len(boxes)):
                        x, y, w, h = boxes[i]
                        label = str(classes[class_ids[i]])
                        color = (255, 0, 0)
                        cv2.rectangle(cf, (x, y), (x + w, y + h), color, 2)
                        cv2.putText(cf, label, (x, y + 30), font, 3, color, 3)

                    for i in range(len(boxes)):
                        xls['{col}{row}'.format(col=chr(ord('A')), row=(i + 2))] = str(classes[class_ids[i]])
                        for j in range(0, 4):
                            xls['{col}{row}'.format(col=chr(ord('B') + j), row=(i + 2))] = boxes[i][j]

                    try:
                        rgb2 = cv2.cvtColor(cf, cv2.COLOR_BGR2RGB)
                        h, w, ch = rgb2.shape
                        bytesPerLine2 = ch * w
                        img2 = QImage(rgb2.data, w, h, bytesPerLine2, QImage.Format_RGB888)
                        resizedImg2 = img2.scaled(self.size.width(), self.size.height(), Qt.KeepAspectRatio)
                        self.sendImage2.emit(resizedImg2)
                    except cv2.error:
                        pass

                    cnt = 0

                try:
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w, ch = rgb.shape
                    bytesPerLine = ch * w
                    img = QImage(rgb.data, w, h, bytesPerLine, QImage.Format_RGB888)
                    resizedImg = img.scaled(self.size.width(), self.size.height(), Qt.KeepAspectRatio)
                    self.sendImage.emit(resizedImg)
                except cv2.error:
                    pass

                if self.bThread == False:
                    wb.save('Detection_sheet.xlsx')
                    wb.close()
                    c_soc.close()
                    s_soc.close()
                    break

