# IMU 센서를 사용한 정지 영상 객체 검출
2021년 프로젝트 LAB(2)
IMU센서를 사용한 정지 영상 객체 검출
---
<!-------------------------------------------------------------Part 1------------------------------------------------------------------------------------------>

## 프로젝트 구동 과정

 * **PC**
 
 1. server_main.py 실행 시 아래와 같은 Pyqt5를 사용한 UI 출력함 \
   ![GUI](https://blogger.googleusercontent.com/img/a/AVvXsEge5TWFalJIvNUyoPAgyDQHXo6Dlafuvpwv7vqLZ6EFzLluFOna4vHB98mDYWXvPNnGZMQAFJ-Je-qb8FlPrNSBEFWrLdwB69HmhadYmStd8MolG8OA2AWt916reu_chTZR2NrVPLSI2XKZ-XghHFJnw3oBs9Yg9Q-yt63GjTM63phUKWCG34g6SIQt1w=w450-h266)
 2. 서버 켜짐 버튼 클릭 시 멀티스레드를 사용한 다중 소켓 통신 대기 상태 돌입함
 3. 클라이언트 측에서 소켓 통신 성공 시 "클라이언트 연결 성공" 출력함
 4. "클라이언트 연결 성공" 출력과 동시에 UI 왼쪽 패널에 클라이언트 측 카메라 영상 수신함 \
   ![영상 수신]()
 5. 클라이언트 측 IMU 센서 정지 시 UI 오른쪽 패널에 정지 순간 영상 수신함
 6. 5번 수신과 동시에 UI 오른쪽 패널에서 Yolo를 사용한 객체 검출 결과 출력함 \
   ![정지 객체 검출]()
 7. 서버 꺼짐 버튼을 클릭 시 다중 소켓 연결에 종료되고 영상 수신 종료함
 8. 7번과 동시에 같은 디렉토리 안에 객체 검출 정보가 담긴 "Detection_sheet.xlsx" 엑셀 파일 저장함 \
   ![엑셀 저장]()
 9. 2번에서 8번까지 일련의 과정을 연속해서 소켓에 할당 가능하며 프로그램 종료 버튼 클릭 시 UI가 종료 됨
 
 * **Client 라즈베리파이**
 
 1. 라즈베리파이 안 Client.py 실행 시 서버 연결 대기 상태에 돌입함
 2. 1번 클라이언트(1번 IP와 포트), 2번 클라이언트(2번 IP와 포트)를 각각 서버에 연결함 
 3. 서버 연결 성공 시 1번 클라이언트가 실시간 USB카메라 영상을 서버에 송신함
 4. 3번 후 IMU 센서 구동을 하며 자이로 값에 따른 가속도 값을 출력함
 5. 4번 후 시작 가속도 정보를 같은 디렉토리에 "start.txt" 파일을 만들어 저장함 \
   ![start.txt 저장]()
 6. 4번의 가속도 값에 대해 한번 더 평균 값을 산출하여 평균 값에 대한 범위를 지정함
 7. 5번의 범위안에 도달하면 정지라 판단하고 챕처 이벤트를 시작함 \
   ![정지 이벤트 시작]()
 8. 만약 6번 과정에 도달하지 못했다면 4번에서 5번의 과정을 반복함
 9. 6번 정지 이벤트 시 2번 클라이언트에 정지 이벤트를 서버에 송신함 \
   ![정지 이벤트 송신]()
 10. 8번 후 정지 가속도 정보를 같은 디렉토리에 "stop.txt" 파일을 만들어 저장함 \
   ![stop.txt 저장]()

 ---

 <!-------------------------------------------------------------Part 2------------------------------------------------------------------------------------------>
 ## 알고리즘 설명


 
 ---
 <!-------------------------------------------------------------Part 3------------------------------------------------------------------------------------------>
 ## 소스코드 설명
 
 * **PC**

 **클라이언트 연결 측**
 ```python
ip = 'ip 주소'  # ip 주소
port = 3333  # port 번호

server_soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_soc.bind((ip, port))
server_soc.listen()
print("클라이언트 연결 대기")

c_soc, addr = server_soc.accept()
print(addr) #1번 클라이언트 연결

s_soc, addr2 = server_soc.accept()
print(addr2) #2번 클라이언트 연결
print("클라이언트 연결 성공")
 ```
 **실시간 영상 수신 측**
 ```python
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

frame = pickle.loads(frame_data, fix_imports=True,encoding="bytes")
# 직렬화되어 있는 binary file로 부터 객체로 역직렬화
frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)  # 프레임 디코딩
frame = cv2.resize(frame, None, fx=0.4, fy=0.4)
 ```
  **정지 이벤트 수신 측**
 ```python
 with open("figure.names", "r") as f:
        classes = [line.strip() for line in f.readlines()]

layer_names = net.getLayerNames()
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

                     ***
                     
cf=copy.deepcopy(frame)
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

    cnt = 0
 ```
  **GUI 출력 측**
 ```python
 class video(QObject):
    sendImage = pyqtSignal(QImage)
    sendImage2 = pyqtSignal(QImage)


    def __init__(self, widget, size):
        super().__init__()
        self.widget = widget
        self.size = size
        self.sendImage.connect(self.widget.recvImage)
        self.sendImage2.connect(self.widget.recvImage_2)
        
           ***
 
   rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
   h, w, ch = rgb.shape
   bytesPerLine = ch * w
   img = QImage(rgb.data, w, h, bytesPerLine, QImage.Format_RGB888)
   resizedImg = img.scaled(self.size.width(), self.size.height(), Qt.KeepAspectRatio)
   self.sendImage.emit(resizedImg)

   rgb2 = cv2.cvtColor(cf, cv2.COLOR_BGR2RGB)
   h, w, ch = rgb2.shape
   bytesPerLine2 = ch * w
   img2 = QImage(rgb2.data, w, h, bytesPerLine2, QImage.Format_RGB888)
   resizedImg2 = img2.scaled(self.size.width(), self.size.height(), Qt.KeepAspectRatio)
   self.sendImage2.emit(resizedImg2)

 ```
  **서버 꺼짐 버튼 클릭 시**
 ```python
def stopCam(self):
    self.bThread = False
    print("소켓 통신 종료")
        
    ***
    if self.bThread == False:
        wb.save('Detection_sheet.xlsx')
        wb.close()
        c_soc.close()
        s_soc.close()
        break
 ```


