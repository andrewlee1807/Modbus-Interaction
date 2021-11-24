from PyQt5.QtCore import QObject
from PyQt5.QtGui import QPixmap , QImage
import numpy
import cv2

class ImageViewer(QObject):

    def __init__(self,cam):
        self.cam0 = cam

    # 이미지 출력 함수
    def display_img(self,img_array):
        if type(img_array) == numpy.ndarray:
            scale = self.get_scale(img_array)
            scaled_img = self.image_resizing(img_array,scale)
            img_qt_format = self.array_to_qimage(scaled_img)
            pixmap=QPixmap(img_qt_format)
            self.cam0.setPixmap(pixmap)

    # 이미지를 리사이즈할 비율 구하기 함수(self,이미지(배열))
    def get_scale(self,img_array):
        img_height,img_width,_ = img_array.shape
        window_width = self.cam0.frameSize().width()
        window_height = self.cam0.frameSize().height()
        scale_width = float(window_width)/float(img_width)
        scale_height = float(window_height)/float(img_height)
        scale = min([scale_width,scale_height])
        return scale
    
    # 이미지 리사이즈 함수(self,이미지(배열상태),비율)
    def image_resizing(self,img_array,scale):
        scaled_img = cv2.resize(img_array,None,fx=scale,fy=scale, interpolation=cv2.INTER_CUBIC)
        return scaled_img
    
    # 배열 상태의 이미지를 QImage로 변환 함수
    def array_to_qimage(self,img_array):
        height, width, bpc = img_array.shape
        bpl = bpc * width
        result = QImage(img_array,width,height,bpl,QImage.Format_RGB888)
        return result
