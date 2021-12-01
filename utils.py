import sys
import logging
import logging.config
import time
import os
import inspect


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
    NO_PRODUCT = b'0x01'
    NO_MODEL = b'0x02'
    NO_WORK = b'0x03'


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
        timestamp = time.strftime("%Y%m%d%H%M%S")
        ERR_FILE = 'logs/' + 'errors_' + timestamp + '.log'
        LOG_FILE = 'logs/' + 'log_' + timestamp + '.log'
        # formatter = logging.Formatter(fmt='%(asctime)s %(module)s |Line: %(lineno)d %(levelname)8s | %(message)s',
        #                               datefmt='%Y/%m/%d %H:%M:%S')  # %I:%M:%S %p AM|PM format
        # logging.basicConfig(filename=LOG_FILE,
        #                     format='%(asctime)s %(module)s,line: %(lineno)d %(levelname)8s | %(message)s',
        #                     datefmt='%Y/%m/%d %H:%M:%S', filemode='w', level=logging.INFO)
        # log_obj = logging.getLogger()
        # log_obj.setLevel(logging.DEBUG)
        self.log_obj = self.__setup_logger(LOG_FILE, logging.INFO)
        self.log_err = self.__setup_logger(ERR_FILE, logging.ERROR)

        log_obj.info("Logger object created successfully..")

    def __setup_logger(self, log_file, level=logging.INFO):
        """To setup as many loggers as you want"""
        formatter = logging.Formatter(fmt='%(asctime)s %(module)s |Line: %(lineno)d %(levelname)8s | %(message)s',
                                      datefmt='%Y/%m/%d %H:%M:%S')  # %I:%M:%S %p AM|PM format
        logging.basicConfig(filename=log_file,
                            format='%(asctime)s %(module)s,line: %(lineno)d %(levelname)8s | %(message)s',
                            datefmt='%Y/%m/%d %H:%M:%S', filemode='w', level=logging.INFO)
        logger = logging.getLogger()
        logger.setLevel(level)

        # console printer
        screen_handler = logging.StreamHandler(stream=sys.stdout)  # stream=sys.stdout is similar to normal print
        screen_handler.setFormatter(formatter)
        logging.getLogger().addHandler(screen_handler)

        return logger

    def export_message(self, msg, level=0, *args):
        cf = inspect.currentframe()
        line = f"{inspect.stack()[1][1]}:{cf.f_back.f_lineno}"
        print(line , *args)
        if level == Notice.INFO:
            self.log_obj.info(msg)
        elif level == Notice.WARNING:
            self.log_obj.warning(msg)
        elif level == Notice.DEBUG:
            self.log_err.debug(line)
            self.log_err.debug(msg)
        elif level == Notice.EXCEPTION:
            self.log_err.exception(line)
            self.log_err.exception(msg)
        elif level == Notice.ERROR:
            self.log_err.error(line)
            self.log_err.error(msg)
        elif level == Notice.CRITICAL:
            self.log_err.critical(line)
            self.log_err.critical(msg)
        else:
            print(msg)


log_obj = Logger()
