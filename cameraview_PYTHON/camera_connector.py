from pypylon import pylon
from PyQt5.QtCore import  pyqtSignal, QObject
import numpy as np
import threading 

class CameraConnectorClass(QObject):
    cam_data = pyqtSignal(np.ndarray)

    def __init__(self,parent):
        super().__init__()
        self.parent = parent
        self.cam_on_off = True
        self.file_num = 0
        self.captureSwitch = False

        self.cam_data.connect(self.parent.update_imageviewer)        

    def cam_start(self):
        self.t = threading.Thread(target=self.__cam_one_start, args=())
        self.t.start()

    def __cam_one_start(self):
        self.camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        converter = pylon.ImageFormatConverter()
        converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
        converter.OutputPixelFormat = pylon.PixelType_RGB8packed
        self.cam_on_off = True
        while self.camera.IsGrabbing() and self.cam_on_off:
            self.grabResult = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
            if self.grabResult.GrabSucceeded():
                image = converter.Convert(self.grabResult)
                self.img = image.GetArray()
                if self.captureSwitch:
                    """ 이미지 저장(.tiff) """
                    # self.__cam_capture_image(self.grabResult,self.img)
                    """ 버퍼 저장(.txt) """
                    self.__cam_capture_buffer(self.grabResult,self.img)
                    """ numpy 저장(.txt) """
                    # self.__cam_capture_numpy(self.grabResult,self.img)
                    self.cam_capture_switch(False)
                self.cam_data.emit(self.img)
            # self.grabResult.Release()
        self.camera.StopGrabbing()

    def cam_stop(self):
        self.cam_on_off=False
    
    def cam_capture_switch(self,trueFalse):
        if trueFalse:
            self.captureSwitch = True
        elif trueFalse == False:
            self.captureSwitch = False

    """ 이미지 저장(.tiff) """
    def __cam_capture_image(self,grabResult,imgArray):
        pylonImage = pylon.PylonImage()
        pylonImage.AttachGrabResultBuffer(grabResult)
        filename = f"test/saved_pypylon_img_{self.file_num}.tiff"
        pylonImage.Save(pylon.ImageFileFormat_Tiff, filename)
        self.file_num += 1

    """ 버퍼 저장(.txt) """
    def __cam_capture_buffer(self,grabResult,imgArray):
        pylonImage = pylon.PylonImage()
        pylonImage.AttachGrabResultBuffer(grabResult)
        img_buffer = pylonImage.GetBuffer()
	    print(type(img_buffer))
        temp = open(f"test/saved_pypylon_buffer_{self.file_num}.txt", "w")
        temp.write(str(img_buffer))
        temp.close()

    """ numpy 저장(.txt) """
    def __cam_capture_numpy(self,grabResult,imgArray):
        height,width,depth = imgArray.shape
        temp_str = f"height : {height}, width : {width}, depth : {depth}\n"
        arrayToFile = open(f"test/saved_pypylon_np_{self.file_num}.txt", "w")
        arrayToFile.write(temp_str)
        for h in range(height):
            for w in range(width):
                temp_str = str(imgArray[h][w]) + "\t"
                arrayToFile.write(temp_str)
            temp_str = "\n"
            arrayToFile.write(temp_str)
        arrayToFile.close()
