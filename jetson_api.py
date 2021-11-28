import jetson.inference
import jetson.utils
import threading
from officialCodeCrop import *
from utils import *
from pypylon import pylon

HEIGHT = 256
WIDTH = 256
ROOT_MODEL = "models/"  # Storage all models in this path
MODEL_ARG = "--model="  # argv for load model by jetson


class ModelA:
    """FOR Apple DETECTION"""

    def __init__(self, model_name="resnet18.onnx"):
        self.model_dir = ROOT_MODEL + model_name
        self._params = ['--input_blob=input_0', '--output_blob=output_0', '--labels=labels.txt'] + \
                       [MODEL_ARG + self.model_dir]
        self.__network = None

    def load_model(self):
        # load the recognition network
        try:
            default_params = ['--model=resnet-exp1/resnet18.onnx', '--input_blob=input_0', '--output_blob=output_0',
                              '--labels=labels.txt']
            # net = jetson.inference.imageNet("", self._params + list(MODEL_ARG + ROOT_MODEL + self.model_name))
            net = jetson.inference.imageNet("", self._params)
            # font = jetson.utils.cudaFont()
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
            self.__network = net
            # self.font = font
            log_obj.export_message("LOADED MODEL SUCCESSFULLY", Notice.INFO)
            return Status.FINISHED

    def get_network(self):
        return self.__network

    def kill(self):
        # TODO:
        # release memory when change model
        pass

    def __del__(self):
        del self.__network


class ModelB:
    def __init__(self):
        pass


class Camera:
    def __init__(self, camera_id=1):
        """
        camera_id: 1: Apple (Basler pulse), 2: Human (regular camera)
        """
        self.camera_id = camera_id
        self.device = None
        self.converter = None

    def load_camera(self):
        try:
            if self.camera_id == 1:
                if self.device is None:
                    camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
                    camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
                    converter = pylon.ImageFormatConverter()
                    converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
                    converter.OutputPixelFormat = pylon.PixelType_RGB8packed
                    self.device = camera
                    self.converter = converter
                return Status.FINISHED
            else:
                cam = cv2.VideoCapture(0)
                cam.set(cv2.CAP_PROP_FRAME_WIDTH, HEIGHT)
                cam.set(cv2.CAP_PROP_FRAME_HEIGHT, WIDTH)

                r, frame = cam.read()
                if not r:
                    log_obj.export_message("CANNOT CAPTURE THE IMAGE BY OPENCV", Notice.CRITICAL)
                else:
                    cv2.imshow("frame", frame)

                cam.release()
        except Exception as e:
            log_obj.export_message("CAMERA cannot work successfully", Notice.CRITICAL)
            log_obj.export_message(e, Notice.CRITICAL)
            return Status.FAILED

    def get_image(self):
        try:
            if self.device.IsGrabbing():
                grabResult = self.device.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
                if grabResult.GrabSucceeded():
                    image = self.converter.Convert(grabResult)
                    img = image.GetArray()
                    return img
            else:
                log_obj.export_message("Camera was closed", Notice.WARNING)
                return -1
        except Exception as e:
            log_obj.export_message(e, Notice.EXCEPTION)
            log_obj.export_message("Cannot open camera", Notice.EXCEPTION)
            return -1

    def inject_camera(self):
        try:
            if self.device is not None:
                self.device.StopGrabbing()
            return Status.FINISHED
        except Exception as e:
            log_obj.export_export("CANNOT INJECT THE CAMERA", Notice.ERROR)
            log_obj.export_export(e, Notice.ERROR)
            return Status.FAILED

    def __del__(self):
        del self.device
        del self.converter


class Service:
    def __init__(self):
        # Initialize model
        self.model_name = "resnet18.onnx"
        self.__status_load_model = self.__load_model()
        self.font = jetson.utils.cudaFont()
        self.network = None

        # Camera control
        self.camera = Camera()  # default is camera_id: 1: Apple (Basler pulse)
        self.camera_status = Status.FAILED  # check camera open/ close/ processing...
        self.open_camera()

        self.model_name_change = None  # model receive from PLC

        self.url = None  # handle url to download
        self.__download_model_result = Status.FAILED

    def __load_model(self, model_name=None, model_id=1):
        """
        model_id : 1: ModelA, 2: modelB
        """
        status = Status.FINISHED
        if model_name is None:
            model_name = self.model_name
        if model_id == 1:
            model = ModelA(model_name)
            status = model.load_model()
            if status == Status.FINISHED:  # keep the previous model to prevent the system crash
                self.network = model.get_network()
        else:
            pass

        return status

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

    def classification(self):
        """Classification image: OK or DEFECTIVE
        """
        # example_photo = 'data/defective/23945062_20211015_133117_956.tiff'
        # I = cv2.imread(example_photo)  # load file by opencv

        if self.network is None:  # No model is loaded
            return ErrorCode.NO_MODEL
        if self.camera_status != Status.FINISHED:
            log_obj.export_message("NO CAMERA IS READY", Notice.ERROR)
            return ErrorCode.NO_WORK

        I = self.camera.get_image()
        if I == -1:
            return Status.FAILED
        # Preprocessing
        c = apple_detect(I)
        if (c.size != 0):
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
        print('Network name: ' + self.network.GetNetworkName())
        print('Network speed: ' + str(self.network.GetNetworkFPS()))
        print("class_id", class_id)
        # self.network.PrintProfilerTimes()
        return Status.DEFECTIVE if class_id == 0 else Status.GOOD

    def __download_model(self):
        import wget
        try:
            wget.download(self.url, out=ROOT_MODEL, bar=False)
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
            self.__status_load_model = self.__load_model(self.model_name_change)
            if self.__status_load_model == Status.FINISHED:
                self.model_name = self.model_name_change
                # self.model_name_change = None  # reset model_name_rev
        else:
            log_obj.export_message("Cannot do change name of model", Notice.ERROR)
