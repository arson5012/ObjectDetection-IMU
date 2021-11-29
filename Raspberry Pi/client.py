import columns as col
import smbus
import math
import datetime
import time
import cv2
import numpy as np
import socket
import struct
import pickle
from random import *
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from itertools import count
import pandas as pd
import openpyxl
from os.path import exists
import sys

cnt = 0

x_1 = []
y_1 = []

x_2 = []
y_2 = []

x_3 = []
y_3 = []

index = count()


power_mgmt_1 = 0x6b
power_mgmt_2 = 0x6c


def read_byte(reg):
    return bus.read_byte_data(address, reg)
def read_word(reg):
    h = bus.read_byte_data(address, reg)
    l = bus.read_byte_data(address, reg + 1)
    value = (h << 8) + l
    return value
def read_word_2c(reg):
    val = read_word(reg)
    if (val >= 0x8000):
        return -((65535 - val) + 1)
    else:
        return val

def dist(a, b):
    return math.sqrt((a * a) + (b * b))

def get_y_rotation(x, y, z):
    radians = math.atan2(x, dist(y, z))
    return -math.degrees(radians)

def get_x_rotation(x, y, z):
    radians = math.atan2(y, dist(x, z))
    return math.degrees(radians)

def animate(i):
    x_1.append(next(index))
    y_1.append(read_word_2c(0x3b) / 16384)  # x가속도

    x_2.append(next(index))
    y_2.append(read_word_2c(0x3d) / 16384)  # y가속도

    x_3.append(next(index))
    y_3.append(read_word_2c(0x3f) / 16384)  # z가속도

    plt.cla()

    plt.title('Graph', fontsize=30)

    plt.plot(x_1, y_1, label='X')
    plt.plot(x_2, y_2, label='Y')
    plt.plot(x_3, y_3, label="Z")
    plt.xlabel('Count')
    plt.ylabel('Acceleration')

    plt.legend(loc='upper left', ncol=1)
    #그래프
   

bus = smbus.SMBus(1)  # bus = smbus.SMBus(0) fuer Revision 1
address = 0x68  # via i2cdetect

# Aktivieren, um das Modul ansprechen zu koennen
bus.write_byte_data(address, power_mgmt_1, 0)
while True:
    ip = '172.30.1.51'  #1번  ip 주소
    port = 3333  # 1번 port 번호


    # 1번 소켓 객체를 생성 및 연결
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((ip, port))
    
    
    ip2 = '172.30.1.51'  #2번 ip 주소
    port2 = 3333  #2번 port 번호

    # 2번 소켓 객체를 생성 및 연결
    client_socket2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket2.connect((ip2, port2))


    # 카메라 선택
    camera = cv2.VideoCapture(0)

    # 크기 지정
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640);  # 가로
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480);  # 세로

 
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
    while True:
        
        ret, frame = camera.read()
        result, frame = cv2.imencode('.jpg', frame, encode_param) 
        data = pickle.dumps(frame, 0) 
        size = len(data)

        # 데이터(프레임) 전송
        client_socket.sendall(struct.pack(">L", size) + data)
       
        
        time.sleep(0.1)
        print("가속도")
        print("---------------------")

        beschleunigung_xout = read_word_2c(0x3b)
        beschleunigung_yout = read_word_2c(0x3d)
        beschleunigung_zout = read_word_2c(0x3f)

        acc_xscale = beschleunigung_xout / 16384.0
        acc_yscale = beschleunigung_yout / 16384.0
        acc_zscale = beschleunigung_zout / 16384.0

        print("가속도계_xout: ", ("%6d" % beschleunigung_xout), " 단위 변환: ", acc_xscale)
        print("가속도계_yout: ", ("%6d" % beschleunigung_yout), " 단위 변환: ", acc_yscale)
        print("가속도계_zout: ", ("%6d" % beschleunigung_zout), " 단위 변환: ", acc_zscale)

               
        cntx = list([acc_xscale])
        cnty = list([acc_yscale])
        cntz = list([acc_zscale])
        x12 = np.mean(cntx)
        y12 = np.mean(cnty)
        z12 = np.mean(cntz)
        print(x12," ",y12," ",z12)
        #평균
        
        f=open("start.txt",'w')
        for i in range(0,6):
            print("x:",x12,"y:",y12,"z:",z12,file=f)
        f.close()
       #시작 가속도 값 txt 파일 생성
        

       
        
        if (-0.1 >= acc_xscale or 0.1 <= acc_xscale) or (-0.1 >= acc_yscale or 0.1 <= acc_yscale) or (
                -0.1 >= acc_zscale or 0.1 <= acc_zscale):
            cnt = 0
        if (cnt == 1):
            continue
        if (-0.1 < x12 < 0.1) and (-1.0 < y12 < 1.0) and (-1.0 < z12 < 1.0):
            print("Capture On")  # 정지시
            cnt =1
   
            msg1 = '정지'
            client_socket2.sendall(msg1.encode(encoding='utf-8'))
            
            f2=open("stop.txt",'w')
            for i in range(0,6):
                print("x:",x12,"y:",y12,"z:",z12,file=f2)
            f2.close()
           #정지 시 가속도 값 txt 파일 생성

        else:
            msg2 = '움직임'
            client_socket2.sendall(msg2.encode(encoding='utf-8'))
           
            
                                 
                