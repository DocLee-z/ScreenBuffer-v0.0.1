import sys, socket, os
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from ui.ScreenRecorder import Ui_ScreenRecorder
import numpy as np
import threading
from PIL import ImageGrab


def get_path(your_file):
    base_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
    real_path = os.path.join(base_dir, your_file)
    return real_path


class ScreenRecorder(QWidget, Ui_ScreenRecorder):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle('ScreenBuffer')
        self.setWindowIcon(QIcon(get_path('pics/logo.ico')))
        self.setMaximumSize(self.size())
        self.setMinimumSize(self.size())
        self.share_screen.clicked.connect(self.start_display)
        self.other_settings.clicked.connect(self.cancel_display)
        self.connect_btn.clicked.connect(self.run_connection)
        self.frame_count = 0
        self.cb_1.setChecked(False)
        self.running = True
        self.init_display()

        self.connect_flag = False
        self.connect_btn.setEnabled(self.connect_flag)
        self.temp_dir = 'temp_frame'
        self.temp_format = 'temp.jpg'
        self.temp_path = get_path(os.path.join(self.temp_dir, self.temp_format))

    def init_display(self):
        self.logo = QPixmap(get_path('pics/logo_display.png')).scaled(self.display_area.size())
        self.display_area.setPixmap(self.logo)

    def start_display(self):
        self.connect_flag = True
        self.connect_btn.setEnabled(self.connect_flag)
        self.fps_set(100)
        self.update_screen()

    def fps_set(self, fps):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_screen)
        self.timer.start(fps)
        index_fps = round((1 / fps) * 1000, 2)
        self.index_fps.setText(str(index_fps))

    def update_screen(self):
        # 截取屏幕
        self.screenshot = ImageGrab.grab()  # type PIL.Image.Image
        self.send_pic = self.screenshot.resize((160, 128))

        # 将截图转换为QImage
        self.new_qt_image = QImage(self.screenshot.tobytes(), self.screenshot.size[0], self.screenshot.size[1],
                                   QImage.Format.Format_RGB888)

        if self.cb_1.isChecked():
            # 二值化处理
            img_array = np.array(self.screenshot.convert('L'))  # 转为灰度图
            binary_img = (img_array > 128) * 255  # 简单阈值处理
            binary_image = QImage(binary_img.astype(np.uint8), self.screenshot.size[0], self.screenshot.size[1],
                                  QImage.Format.Format_Grayscale8)

            self.display_area.clear()  # 清除之前展示的帧
            self.display_area.setPixmap(QPixmap.fromImage(binary_image).scaled(320, 256,
                                                                               transformMode=Qt.TransformationMode.SmoothTransformation))
        else:
            self.display_area.clear()  # 清除之前展示的帧
            self.display_area.setPixmap(QPixmap.fromImage(self.new_qt_image).scaled(320, 256,
                                                                                    transformMode=Qt.TransformationMode.SmoothTransformation))

    def cancel_display(self):

        self.connect_flag = False
        self.connect_btn.setEnabled(self.connect_flag)

        self.display_area.clear()
        if self.timer:  # 如果定时器存在，停止定时器
            self.timer.stop()
            self.timer = None
        self.logo = QPixmap(get_path('pics/logo_display.png')).scaled(self.display_area.size())
        self.display_area.setPixmap(self.logo)

    def run_connection(self):
        t_connect = threading.Thread(target=self.connect_device)
        t_connect.start()

    def connect_device(self):

        self.ip = '0.0.0.0'
        self.port = self.lineEdit.text()
        self.addr = (self.ip, int(self.port))
        self.socket_server = socket.socket()
        self.socket_server.bind(self.addr)
        self.socket_server.listen(2)
        self.client_socket, self.client_address = self.socket_server.accept()

        while self.running:

            self.msg = self.client_socket.recv(1024)

            if self.msg.decode() == 'CPP':
                if self.cb_1.isChecked():
                    self.send_pic.convert('L').save(self.temp_path)
                    self.file_size = int(os.path.getsize(self.temp_path))
                    self.client_socket.send(self.file_size.to_bytes(2, byteorder='little', signed=True))
                else:
                    self.send_pic.save(self.temp_path)
                    self.file_size = int(os.path.getsize(self.temp_path))
                    self.client_socket.send(self.file_size.to_bytes(2, byteorder='little', signed=True))

            elif self.msg.decode() == 'PY':
                self.file = open(self.temp_path, 'rb+')
                while self.file_size > 512:
                    self.chunk = self.file.read(512)
                    self.client_socket.send(self.chunk)
                    self.file_size -= 512
                self.chunk = self.file.read(self.file_size)
                self.client_socket.send(self.chunk)
                self.file.close()


if __name__ == '__main__':

    temp_frame_dir = get_path('temp_frame')
    if not os.path.exists(temp_frame_dir):
        os.makedirs(temp_frame_dir)

    app = QApplication(sys.argv)
    screenRecorder = ScreenRecorder()
    screenRecorder.show()
    sys.exit(app.exec())