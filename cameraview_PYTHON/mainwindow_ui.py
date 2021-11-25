from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow
from image_viewer import ImageViewer


from camera_connector import CameraConnectorClass


mainwindowUiForm = uic.loadUiType("ui/mainwindow.ui")[0]

class MainWindowClass(QMainWindow,mainwindowUiForm):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setupUi(self)

        self.btn_viewerStart.clicked.connect(self.cam_start)
        self.btn_viewerStop.clicked.connect(self.cam_stop)
        self.btnCapture.clicked.connect(self.cam_capture)
        self.mycam0 = ImageViewer(self.lb_imageViewer)
        self.camera_seacher = CameraConnectorClass(self)

    def cam_capture(self):
        self.camera_seacher.cam_capture_switch(True)

    def cam_start(self):
        self.camera_seacher.cam_start()
    def cam_stop(self):
        self.camera_seacher.cam_stop()

    def update_imageviewer(self,img):
        self.mycam0.display_img(img)
