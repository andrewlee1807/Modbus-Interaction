import cv2
import jetson.inference
import jetson.utils
import threading
import sys
from officialCodeCrop import *

HEIGHT = 256
WIDTH = 256
ROOT_MODEL = "models/"  # Storage all models in this path
MODEL_ARG = "--model="  # argv for load model by jetson


class status:
    PROCESSING = 1
    FAILED = 2
    FINISHED = 3


class Service:
    def __init__(self):
        # Get model name from args
        # ['predict.py', '--model=models/resnet18.onnx', '--input_blob=input_0', '--output_blob=output_0', '--labels=labels.txt']
        self.model_name = "resnet18.onnx"
        self._params = ['--input_blob=input_0', '--output_blob=output_0', '--labels=labels.txt']

        # for (i, param) in enumerate(self._params):
        #    if "--model" in param:
        #        self.model_name = self._params[i].split(MODEL_ARG + ROOT_MODEL)[-1]  # --model=models/
        #        break
        # del sys.argv[i]

        self.__load_model()
        self.model_name_rev = None  # model receive from PLC

        self.url = None  # handle url to download
        self.download_thread = None  # thread to handle the download: Value=None or Thread

    def load_img(self):
        """Read img from camera"""
        try:
            cam = cv2.VideoCapture(0)

            cam.set(cv2.CAP_PROP_FRAME_WIDTH, HEIGHT)
            cam.set(cv2.CAP_PROP_FRAME_HEIGHT, WIDTH)

            r, frame = cam.read()
            if not r:
                print("failed to grab frame")

            cv2.imshow("test", frame)

            cam.release()
        except Exception as e:
            print("CAMERA cannot work successfully")
            print(e)
            pass

    def __load_model(self):
        # load the recognition network
        try:
            net = jetson.inference.imageNet("", self._params + list(MODEL_ARG + ROOT_MODEL + self.model_name))
            font = jetson.utils.cudaFont()
        except Exception as e:
            print(e)
            return status.FAILED
        else:
            self.net = net
            self.font = font
            return status.FINISHED

    def classification(self, path_img='0039.jpg'):
        """Classification image: OK or DEFECTIVE
        path_img: string path
        """

        # Load Image
        # # by Jetson utils
        # img = jetson.utils.loadImage()

        # by opencv
        # img = cv2.imread(path_img)
        # img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        # img = jetson.utils.cudaFromNumpy(img)  # convert numpy to Jetson type

        """new preprocessing"""
        I = cv2.imread(path_img)  # load file by opencv
        c = apple_detect(I)
        if c is not None:
            I = cv2.cvtColor(c, cv2.COLOR_BGR2RGB)
            img = jetson.utils.cudaFromNumpy(I)  # convert image from numpy
        else:
            print('Apple is not detected!')
            return -1  # ERROR
        # finish preprocessing

        # classify the image
        class_id, confidence = self.net.Classify(img)
        # find the object description
        class_desc = self.net.GetClassDesc(class_id)
        # overlay the result on the image
        self.font.OverlayText(img, img.width, img.height, "{:05.2f}% {:s}".format(confidence * 100, class_desc), 5, 5,
                              self.font.White, self.font.Gray40)
        # Save output image
        jetson.utils.saveImage('0039_out.jpg', img)
        print('Network name: ' + self.net.GetNetworkName())
        print('Network speed: ' + str(self.net.GetNetworkFPS()))
        self.net.PrintProfilerTimes()
        return class_id

    def __download_model(self, url):
        import wget
        try:
            wget.download(url, bar=False)  # self.download_thread = Thread()
        except Exception as e:
            print("Download was failed")
            print(e)
            self.download_thread = None  # Failed

    def check_download_status(self):
        try:
            if self.download_thread is None:  # no thread
                return status.FAILED
            elif self.download_thread.is_alive():  # downloading
                return status.PROCESSING
            else:
                self.download_thread = None  # reset WITH ONE TIME CHECK STATUS SUCCESSFULLY
                return status.FINISHED
        except Exception as e:
            print(e)

    def download_model(self, url):
        """""Download model by URL
        Only 1 model can be downloaded at a time
        """""
        if self.check_download_status() == status.FAILED or self.check_download_status() == status.FINISHED:
            return -1  # RETURN Error when request many time to download model
        else:  # Free thread to download
            # Create New Thread
            if self.download_thread is None:
                self.download_thread = threading.Thread(target=self.__download_model, args=url)
                self.download_thread.start()

    def change_model_name(self, model_name: str):
        self.model_name_rev = model_name

    def change_model(self):
        # Check model is available on local
        import os
        if self.model_name_rev is not None and os.path.isfile(ROOT_MODEL + self.model_name_rev):  # model exists
            self.model_name = self.model_name_rev
            self.model_name_rev = None  # reset model_name_rev
            # load new model
            error = self.__load_model()
        else:
            return -1  # ERROR cannot change name of model
