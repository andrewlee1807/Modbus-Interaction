from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage
import numpy
import cv2
import threading
from PyQt5.QtWidgets import QApplication
import sys

mainwindowUiForm = uic.loadUiType("cameraview_PYTHON/ui/mainwindow.ui")[0]


class CameraConnectorClass(QObject):
    cam_data = pyqtSignal(numpy.ndarray)

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.cam_on_off = True
        self.file_num = 0
        self.captureSwitch = False

        self.cam_data.connect(self.parent.update_imageviewer)

    def cam_start(self, camera):
        self.t = threading.Thread(target=self.__cam_one_start, args=(camera,))
        self.t.start()

    def cam_capture_switch(self):
        pass

    def __cam_one_start(self, camera):
        # Initialize the camera
        # self.camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        # self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        # converter = pylon.ImageFormatConverter()
        # converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
        # converter.OutputPixelFormat = pylon.PixelType_RGB8packed
        # self.cam_on_off = True
        while True:
            self.img = camera.get_image()
            if self.img == -1:
                break
            self.cam_data.emit(self.img)

    def cam_stop(self):
        self.cam_on_off = False


class ImageViewer(QObject):
    def __init__(self, cam):
        self.cam0 = cam

    # 이미지 출력 함수
    def display_img(self, img_array):
        if type(img_array) == numpy.ndarray:
            scale = self.get_scale(img_array)
            scaled_img = self.image_resizing(img_array, scale)
            img_qt_format = self.array_to_qimage(scaled_img)
            pixmap = QPixmap(img_qt_format)
            self.cam0.setPixmap(pixmap)

    # 이미지를 리사이즈할 비율 구하기 함수(self,이미지(배열))
    def get_scale(self, img_array):
        img_height, img_width, _ = img_array.shape
        window_width = self.cam0.frameSize().width()
        window_height = self.cam0.frameSize().height()
        scale_width = float(window_width) / float(img_width)
        scale_height = float(window_height) / float(img_height)
        scale = min([scale_width, scale_height])
        return scale

    # 이미지 리사이즈 함수(self,이미지(배열상태),비율)
    def image_resizing(self, img_array, scale):
        scaled_img = cv2.resize(img_array, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        return scaled_img

    # 배열 상태의 이미지를 QImage로 변환 함수
    def array_to_qimage(self, img_array):
        height, width, bpc = img_array.shape
        bpl = bpc * width
        result = QImage(img_array, width, height, bpl, QImage.Format_RGB888)
        return result


class MainWindowClass(QMainWindow, mainwindowUiForm):
    def __init__(self, camera):
        QMainWindow.__init__(self)
        self.setupUi(self)

        self.btn_viewerStart.clicked.connect(self.cam_start)
        self.btn_viewerStop.clicked.connect(self.cam_stop)
        self.btnCapture.clicked.connect(self.cam_capture)
        self.mycam0 = ImageViewer(self.lb_imageViewer)
        self.camera_seacher = CameraConnectorClass(self)
        self.camera = camera

    def cam_capture(self):
        self.camera_seacher.cam_capture_switch()

    def cam_start(self):
        self.camera_seacher.cam_start(self.camera)

    def cam_stop(self):
        self.camera_seacher.cam_stop()

    def update_imageviewer(self, img):
        self.mycam0.display_img(img)

# app = QApplication(sys.argv)
# mainwindow = MainWindowClass()
# mainwindow.show()
