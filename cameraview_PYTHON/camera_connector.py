from pypylon import pylon
from PyQt5.QtCore import  pyqtSignal, QObject
import numpy
import threading 

class CameraConnectorClass(QObject):
    cam_data = pyqtSignal(numpy.ndarray)

    def __init__(self,parent):
        super().__init__()
        self.parent = parent
        self.cam_on_off = True

        self.cam_data.connect(self.parent.update_imageviewer)        

    def cam_start(self):
        self.t = threading.Thread(target=self.cam_one_start, args=())
        self.t.start()

    def cam_one_start(self):
        camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        converter = pylon.ImageFormatConverter()
        converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
        converter.OutputPixelFormat = pylon.PixelType_RGB8packed
        self.cam_on_off = True
        while camera.IsGrabbing() and self.cam_on_off:
            grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
            if grabResult.GrabSucceeded():
                print(grabResult)
                # Access the image data
                image = converter.Convert(grabResult)
                img = image.GetArray()
                self.cam_data.emit(img)
            grabResult.Release()
        camera.StopGrabbing()

    def cam_stop(self):
        self.cam_on_off=False