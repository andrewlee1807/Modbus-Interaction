# 개발 일자 : 2021.10. 01
# 개발자 : 김용래
# 제작사 : (주)리눅스아이티

from lib.modbus.config import config
from lib.modbus.util import util


class modbus_register:
    def __init__(self):
        super().__init__()
        self.config = config
        self.config.MODBUS_ADDRESS = bytearray(0x0500)
        self.util = util

    def readRegister(self, startAddress, register):
        count = register * 2
        startAddress *= 2
        value = self.config.MODBUS_ADDRESS[startAddress: (startAddress + count)]

        return {
            "COUNT": count,
            "VALUE": value
        }

    def writeRegister(self, startAddress, count, value):
        startAddress = int.from_bytes(startAddress, byteorder='big')
        startAddress *= 2
        if count > 2:
            for i in range(0, count):
                self.config.MODBUS_ADDRESS[startAddress + i] = value[i]
        else:
            self.config.MODBUS_ADDRESS[startAddress] = value[0]
            self.config.MODBUS_ADDRESS[startAddress + 1] = value[1]

    def readHoldingReigster(self, msg):
        splits = self.util.splits(msg)
        recv_mbap = splits["MBAP"]
        fc = splits["FC"]
        data = splits["DATA"]

        startAddress = int.from_bytes(data[0:2], byteorder='big')
        register = int.from_bytes(data[2:4], byteorder='big')

        adu = self.readRegister(startAddress, register)
        mbap_len = len(bytes([recv_mbap[6]]) + bytes([fc]) + bytes([adu["COUNT"]]) + adu["VALUE"])
        mbap_len = self.util.int_to_2bytes(mbap_len)
        mbap = recv_mbap[:4] + mbap_len + bytes([recv_mbap[6]])

        return {
            "MBAP": mbap,
            "FC": fc,
            "COUNT": adu["COUNT"],
            "VALUE": adu["VALUE"]
        }

    def readInputRegister(self, msg):
        splits = self.util.splits(msg)
        recv_mbap = splits["MBAP"]
        fc = splits["FC"]
        data = splits["DATA"]

        startAddress = int.from_bytes(data[0:2], byteorder='big')
        register = int.from_bytes(data[2:4], byteorder='big')

        adu = self.readRegister(startAddress, register)
        mbap_len = len(bytes([recv_mbap[6]]) + bytes([fc]) + bytes([adu["COUNT"]]) + adu["VALUE"])
        mbap_len = self.util.int_to_2bytes(mbap_len)
        mbap = recv_mbap[:4] + mbap_len + bytes([recv_mbap[6]])

        return {
            "MBAP": mbap,
            "FC": fc,
            "COUNT": adu["COUNT"],
            "VALUE": adu["VALUE"]
        }

    def writeSingleRegister(self, msg):
        splits = self.util.splits(msg)
        recv_mbap = splits["MBAP"]
        fc = splits["FC"]
        data = splits["DATA"]

        startAddress = data[0:2]
        value = data[2:4]
        self.writeRegister(startAddress, 2, value)
        mbap_len = len(bytes([recv_mbap[6]]) + bytes([fc]) + startAddress + value)
        mbap_len = self.util.int_to_2bytes(mbap_len)
        mbap = recv_mbap[:4] + mbap_len + bytes([recv_mbap[6]])
        return {
            "MBAP": mbap,
            "FC": fc,
            "ADDRESS": startAddress,
            "VALUE": value
        }

    def writeMultipleRegister(self, msg):
        splits = self.util.splits(msg)
        recv_mbap = splits["MBAP"]
        fc = splits["FC"]
        data = splits["DATA"]

        register = data[2:4]
        count = data[4]
        value = data[5:]
        startAddress = data[0:2]
        self.writeRegister(startAddress, count, value)
        mbap_len = len(bytes([recv_mbap[6]]) + bytes([fc]) + startAddress + register)
        print(mbap_len)
        mbap_len = self.util.int_to_2bytes(mbap_len)
        mbap = recv_mbap[:4] + mbap_len + bytes([recv_mbap[6]])
        return {
            "MBAP": mbap,
            "FC": fc,
            "ADDRESS": startAddress,
            "REGISTERS": register
        }