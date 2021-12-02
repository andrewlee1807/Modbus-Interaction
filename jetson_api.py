import jetson.inference
import jetson.utils
from RGB_order_OfficialCodeCrop import *
from utils import *
from pypylon import pylon

SAMPLE_DIR = "samples/"
ROOT_MODEL = "models/"  # Storage all models in this path
MODEL_ARG = "--model="  # argv for load model by jetson


class Model:
    def __init__(self, model_name):
        self.model_dir = ROOT_MODEL + model_name
        self._params = None
        self.__network = None

    def load_model(self):
        # load the recognition network
        net = None
        try:
            net = jetson.inference.imageNet("", self._params)
            self.__network = net
        except Exception as e:
            log_obj.export_message(e, Notice.EXCEPTION)
            # Check file exists or not
            if check_file_available(self.model_dir):
                log_obj.export_message("CANNOT LOAD MODEL", Notice.EXCEPTION)
                return Status.FAILED
            else:
                log_obj.export_message("MODEL FILE IS NOT EXIST", Notice.EXCEPTION)
                return Status.NO_FILE
        else:
            log_obj.export_message("LOADED MODEL SUCCESSFULLY", Notice.INFO)
            return Status.FINISHED

    def get_network(self):
        return self.__network

    def __del__(self):
        del self.__network


class ModelA(Model):
    """FOR Apple DETECTION"""

    def __init__(self, model_name="resnet18.onnx"):
        super().__init__(model_name)
        # self.model_dir = ROOT_MODEL + model_name
        self._params = ['--input_blob=input_0', '--output_blob=output_0', '--labels=labels/apple.txt'] + \
                       [MODEL_ARG + self.model_dir]
        # self.__network = None

    # def load_model(self):
    #     # load the recognition network
    #     net = None
    #     try:
    #         default_params = ['--model=resnet-exp1/resnet18.onnx', '--input_blob=input_0', '--output_blob=output_0',
    #                           '--labels=labels.txt']
    #         # net = jetson.inference.imageNet("", self._params + list(MODEL_ARG + ROOT_MODEL + self.model_name))
    #         net = jetson.inference.imageNet("", self._params)
    #         self.__network = net
    #         # font = jetson.utils.cudaFont()
    #     except Exception as e:
    #         log_obj.export_message(e, Notice.EXCEPTION)
    #         # Check file exists or not
    #         if check_file_available(self.model_dir):
    #             log_obj.export_message("CANNOT LOAD MODEL", Notice.EXCEPTION)
    #             return Status.FAILED
    #         else:
    #             log_obj.export_message("MODEL FILE IS NOT EXIST", Notice.EXCEPTION)
    #             return Status.NO_FILE
    #     else:
    #         # self.font = font
    #         log_obj.export_message("LOADED MODEL SUCCESSFULLY", Notice.INFO)
    #         return Status.FINISHED
    #
    # def get_network(self):
    #     return self.__network
    #
    # def __del__(self):
    #     del self.__network


class ModelB(Model):
    """FOR Mask Detection"""

    def __init__(self, model_name="mb1-ssd.onnx"):
        super().__init__(model_name)
        # self.model_dir = ROOT_MODEL + model_name
        self._params = ['--input_blob=input_0', '--output-cvg=scores', '--output-bbox=boxes',
                        '--labels=labels/mask.txt'] + \
                       [MODEL_ARG + self.model_dir]

    def load_model(self):
        try:
            net = jetson.inference.detectNet("", self._params, 0.5)
            self.__network = net
        except Exception as e:
            log_obj.export_message(e, Notice.EXCEPTION)
            # Check file exists or not
            if check_file_available(self.model_dir):
                log_obj.export_message("CANNOT LOAD MODELL", Notice.EXCEPTION)
                return Status.FAILED
            else:
                log_obj.export_message("MODEL FILE IS NOT EXISTT", Notice.EXCEPTION)
                return Status.NO_FILE
        else:
            log_obj.export_message("LOADED MODEL SUCCESSFULLYY", Notice.INFO)
            return Status.FINISHED

    def get_network(self):
        return self.__network

    def __del__(self):
        del self.__network


class Camera:
    def __init__(self, camera_id=1):
        """
        camera_id: 1: Apple (Basler pulse), 2: Human (regular camera)
        """
        self.camera_id = camera_id
        self.device_bp = None
        self.converter = None
        self.device_cv = None

    def load_camera(self):
        try:
            if self.camera_id == 1:
                if self.device_bp is None:
                    camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
                    camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
                    converter = pylon.ImageFormatConverter()
                    converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
                    converter.OutputPixelFormat = pylon.PixelType_RGB8packed
                    self.device_bp = camera
                    self.converter = converter
                    log_obj.export_message("Camera opened", Notice.INFO)
                return Status.FINISHED
            else:
                def make_480p():
                    cam.set(3, 640)
                    cam.set(4, 480)

                # if self.device is not None: self.device.StopGrabbing()  # release previous camera
                cam = cv2.VideoCapture(0)
                make_480p()
                self.device_cv = cam
                return Status.FINISHED
        except Exception as e:
            log_obj.export_message("CAMERA cannot work successfully", Notice.CRITICAL)
            log_obj.export_message(e, Notice.CRITICAL)
            return Status.FAILED

    def get_image(self):
        try:
            if self.camera_id == 1:
                if self.device_bp.IsGrabbing():
                    grabResult = self.device_bp.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
                    if grabResult.GrabSucceeded():
                        image = self.converter.Convert(grabResult)
                        img = image.GetArray()
                        return img
                else:
                    log_obj.export_message("Camera was closed", Notice.WARNING)
                    return -1
            else:
                r, frame = self.device_cv.read()
                if not r:
                    log_obj.export_message("CANNOT CAPTURE THE IMAGE BY OPENCV", Notice.CRITICAL)
                    return -1
                return frame
        except Exception as e:
            log_obj.export_message(e, Notice.EXCEPTION)
            log_obj.export_message("Cannot open camera", Notice.EXCEPTION)
            return -1

    def inject_camera(self):
        try:
            if self.camera_id == 1:
                if self.device_bp is not None:
                    self.device_bp.StopGrabbing()
            else:
                if self.device_cv is not None:
                    self.device_cv.release()
            log_obj.export_message("Camera was closed", Notice.INFO)
            return Status.FINISHED
        except Exception as e:
            log_obj.export_export("CANNOT INJECT THE CAMERA", Notice.ERROR)
            log_obj.export_export(e, Notice.ERROR)
            return Status.FAILED

    def __del__(self):
        del self.device_bp
        del self.converter
        del self.device_cv


class Service:
    def __init__(self):
        # Initialize model
        self.network = None
        self.task = None
        self.model_name = "resnet18.onnx"
        self.__status_load_model = self.__load_model()
        self.font = jetson.utils.cudaFont()

        # Camera control
        self.camera = Camera()  # default is camera_id: 1: Apple (Basler pulse)
        self.camera_status = Status.FAILED  # check camera open/ close/ processing...
        self.open_camera()

        self.model_name_change = None  # model receive from PLC

        self.url = None  # handle url to download
        self.__download_model_result = Status.FAILED

        # real time camera showing...
        import argparse
        parser = argparse.ArgumentParser(description='Process some integers.')
        parser.add_argument("--camera", type=bool, choices=(False, True), default=False, help="Open the visual camera")
        args = parser.parse_args()
        if args.camera:
            import threading
            t = threading.Thread(target=self.__window_camera)
            t.start()

        print("Initialize", self.network)

    def __load_model(self, model_name=None):
        """
        model_id : 1: ModelA, 2: modelB
        """
        status = Status.FINISHED
        if model_name is None:
            model_name = self.model_name
        task_type = TASK.DETECT_DEFECTION
        model = ModelA(model_name)
        status = model.load_model()
        print("StatusA: ", status)

        if status == Status.FAILED:  # try to another model
            log_obj.export_message("TRY TO MODEL B", Notice.INFO)
            model = ModelB(model_name)
            status = model.load_model()
            print("StatusB: ", status)
            task_type = TASK.DETECT_MASK

        print("Status: ", status)

        if status == Status.FINISHED:  # keep the previous model to prevent the system crash
            print("Update model to self")
            self.network = model.get_network()
            self.task = task_type
            print("self.network: ", self.network)

        return status

    def __window_camera(self):
        from PyQt5.QtWidgets import QApplication
        from camera_lib import MainWindowClass
        import sys
        app = QApplication(sys.argv)
        mainwindow = MainWindowClass(self.camera)
        mainwindow.show()

        # app.exec_()
        sys.exit(app.exec_())

    def __save_img(self, img):
        timestamp = time.strftime("%Y%m%d%H%M%S")
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        cv2.imwrite(f"{SAMPLE_DIR + timestamp}.jpg", img)

    def get_model_changed_status(self):
        return self.__status_load_model

    def open_camera(self):
        self.camera_status = Status.PROCESSING
        self.camera_status = self.camera.load_camera()

    def close_camera(self):
        self.camera_status = Status.PROCESSING
        self.camera_status = self.camera.inject_camera()

    def get_camera_status(self):
        return self.camera_status

    def inference(self):
        print("Inference: self.network: ", self.network)
        if self.network is None:  # No model is loaded
            log_obj.export_message("NO MODEL", Notice.ERROR)
            return ErrorCode.NO_MODEL
        if self.camera_status != Status.FINISHED:
            log_obj.export_message("NO CAMERA IS READY", Notice.ERROR)
            return ErrorCode.NO_WORK
        I = self.camera.get_image()
        if type(I) == int:
            return Status.FAILED

        if self.task == TASK.DETECT_DEFECTION:
            print("APPLE")
            result = self.classification(I)
        else:
            print("MASK")
            result = self.mask_detection(I)

        return Status.DEFECTIVE if result == 0 else Status.GOOD

    def classification(self, img):
        """Classification image: OK or DEFECTIVE
        """
        # example_photo = 'data/defective/23945062_20211015_133117_956.tiff'
        # I = cv2.imread(example_photo)  # load file by opencv

        # if self.network is None:  # No model is loaded
        #     log_obj.export_message("NO MODEL", Notice.ERROR)
        #     return ErrorCode.NO_MODEL
        # if self.camera_status != Status.FINISHED:
        #     log_obj.export_message("NO CAMERA IS READY", Notice.ERROR)
        #     return ErrorCode.NO_WORK
        #
        # I = self.camera.get_image()
        #
        # if type(I) == int:
        #     return Status.FAILED

        self.__save_img(img)

        c = apple_detect(img)
        if c.size != 0:
            c = cv2.cvtColor(c, cv2.COLOR_BGR2RGB)  # convert to RGB order
            img = jetson.utils.cudaFromNumpy(c)  # convert image from numpy
        else:
            log_obj.export_message("Apple is not detected!", Notice.WARNING)
            return ErrorCode.NO_PRODUCT
        # finish preprocessing

        # classify the image
        class_id, confidence = self.network.Classify(img)  # class_id=0 or 1
        # find the object description
        class_desc = self.network.GetClassDesc(class_id)
        # # overlay the result on the image to visualize
        # self.font.OverlayText(img, img.width, img.height, "{:05.2f}% {:s}".format(confidence * 100, class_desc), 5, 5,
        #                       self.font.White, self.font.Gray40)
        # Save output image
        # print('Network name: ' + self.network.GetNetworkName())
        # print('Network speed: ' + str(self.network.GetNetworkFPS()))
        print("class_id", class_id)
        # self.network.PrintProfilerTimes()
        return class_id
        # return Status.DEFECTIVE if class_id == 0 else Status.GOOD

    def mask_detection(self, img):
        jetson_img = jetson.utils.cudaFromNumpy(img)  # convert image from numpy

        detections = self.network.Detect(jetson_img, overlay='box,labels,conf')

        opencv_img = jetson.utils.cudaToNumpy(jetson_img)
        # Realtime to detect
        # cv2.imshow("", opencv_img)
        # cv2.waitKey(1)

        self.__save_img(opencv_img)

        print("detected {:d} objects in image".format(len(detections)))

        classID = [int(bbox.ClassID) for bbox in detections]

        if (sum(classID) == len(classID)):
            return 1  # All the mask
        else:
            return 0

    def __download_model(self):
        import wget
        try:
            log_obj.export_message("Start download", Notice.INFO)
            wget.download(self.url, out=ROOT_MODEL, bar=False)
            log_obj.export_message("Done download", Notice.INFO)
            self.__download_model_result = Status.FINISHED
        except Exception as e:
            log_obj.export_message("Download was failed", Notice.WARNING)
            log_obj.export_message(e, Notice.WARNING)
            self.__download_model_result = Status.FAILED  # Failed by url=None or incorrect url

    def set_download_url(self, url):
        self.url = url

    def download_model(self):
        """""Download model by URL
        Only 1 model can be downloaded at a time
        """""
        self.__download_model()

    def get_download_result(self):
        return self.__download_model_result

    def set_model_name(self, model_name: str):
        self.model_name_change = model_name

    def change_model(self):
        if self.model_name_change is not None and self.model_name != self.model_name_change:
            # load new model
            self.__status_load_model = Status.PROCESSING
            self.__status_load_model = self.__load_model(self.model_name_change)
            if self.__status_load_model == Status.FINISHED:
                self.model_name = self.model_name_change
                # self.model_name_change = None  # reset model_name_rev
        else:
            log_obj.export_message("Cannot do change model, plz check name of model was same with old model",
                                   Notice.ERROR)
