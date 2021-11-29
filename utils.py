import sys
import logging
import logging.config
import time
import os


class Status:
    PROCESSING = 1
    FAILED = 2
    FINISHED = 3
    DEFECTIVE = 2  # defect in case classification
    GOOD = 3  # Ok in case classification
    OFF = 0
    ON = 1
    NO_FILE = 4  # no file available
    COLLECTOR = 1  # close camera
    DETECTOR = 2  # open camera


class Notice:
    INFO = 1
    WARNING = 2
    DEBUG = 3
    EXCEPTION = 4
    ERROR = 5
    CRITICAL = 6


class ErrorCode:
    NO_PRODUCT = 0x01
    NO_MODEL = 0x02
    NO_WORK = 0x03


class AI_ACTION_CODE:
    # Action code
    START = 0x01 * 2
    STOP = 0x02 * 2
    RESUME = 0x03 * 2
    SUSPEND = 0x04 * 2


def hex2int(hex):
    return int(hex, 16)  # int.from_bytes(hex)


def two_bytes(int_value):
    """Generate 2 bytes from integer value"""
    return bytes([0, int_value])


def getStringFromAddress(config, start, end):
    temp = config.MODBUS_ADDRESS[start:end]
    print(len(temp))
    temp_str = ""
    for i in range(0, len(temp), 2):
        temp_hex = (temp[i] << 8) + temp[i + 1]
        temp_str += chr(temp_hex)
    print(temp_str)
    print(len(temp_str))
    return temp_str


def check_thread_alive(thread):
    try:
        if thread is None:  # no thread started before
            return Status.FAILED
        elif thread.is_alive():  # alive
            return Status.PROCESSING
        else:
            # thread = None  # reset WITH ONE TIME CHECK STATUS SUCCESSFULLY
            return Status.FINISHED
    except Exception as e:
        print(e)


def check_file_available(path):
    return os.path.isfile(path)


class Logger:
    def __init__(self):
        file_name = time.strftime("%Y%m%d%H%M%S") + '.log'
        formatter = logging.Formatter(fmt='%(asctime)s %(module)s |Line: %(lineno)d %(levelname)8s | %(message)s',
                                      datefmt='%Y/%m/%d %H:%M:%S')  # %I:%M:%S %p AM|PM format
        logging.basicConfig(filename=file_name,
                            format='%(asctime)s %(module)s,line: %(lineno)d %(levelname)8s | %(message)s',
                            datefmt='%Y/%m/%d %H:%M:%S', filemode='w', level=logging.INFO)
        log_obj = logging.getLogger()
        log_obj.setLevel(logging.DEBUG)
        # log_obj = logging.getLogger().addHandler(logging.StreamHandler())

        # console printer
        screen_handler = logging.StreamHandler(stream=sys.stdout)  # stream=sys.stdout is similar to normal print
        screen_handler.setFormatter(formatter)
        logging.getLogger().addHandler(screen_handler)

        log_obj.info("Logger object created successfully..")
        self.log_obj = log_obj

    def export_message(self, msg, level=0):
        if level == Notice.INFO:
            self.log_obj.info(msg)
        elif level == Notice.WARNING:
            self.log_obj.warning(msg)
        elif level == Notice.DEBUG:
            self.log_obj.debug(msg)
        elif level == Notice.EXCEPTION:
            self.log_obj.exception(msg)
        elif level == Notice.ERROR:
            self.log_obj.error(msg)
        elif level == Notice.CRITICAL:
            self.log_obj.critical(msg)
        else:
            print(msg)


log_obj = Logger()