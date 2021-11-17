# 개발 일자 : 2021.10. 01
# 개발자 : 김용래
# 제작사 : (주)리눅스아이티

from lib.modbus.config import config
from lib.modbus.util import util

class modbus_coil:

    def __init__(self):
        super().__init__()
        self.config = config
        self.util = util

    # 입력 값: 시작주소,비트길이

    def readCoil(self, msg):
        splits = self.util.splits(msg)
        recv_mbap = splits["MBAP"]
        fc = splits["FC"]
        data = splits["DATA"]

        addr = int.from_bytes(data[0:2])
        length = int.from_bytes(data[2:4])

        adu = self.util.readBit(self.config, addr, length)
        mbap_len = len(bytes([recv_mbap[6]])+bytes([fc])+bytes([adu["COUNT"]])+adu["VALUE"])
        mbap_len = self.util.int_to_2bytes(mbap_len)
        mbap=recv_mbap[:4]+ mbap_len + bytes([recv_mbap[6]])

        return {
            "MBAP":mbap,
            "FC":fc,
            "COUNT": adu["COUNT"],
            "VALUE": adu["VALUE"]
        }
        
    def readDiscreteInput(self, msg):
        splits = self.util.splits(msg)
        recv_mbap = splits["MBAP"]
        fc = splits["FC"]
        data = splits["DATA"]

        addr = int.from_bytes(data[0:2])
        length = int.from_bytes(data[2:4])

        adu = self.util.readBit(self.config, addr, length)
        mbap_len = len(bytes([recv_mbap[6]])+bytes([fc])+bytes([adu["COUNT"]])+adu["VALUE"])
        mbap_len = self.util.int_to_2bytes(mbap_len)
        mbap=recv_mbap[:4]+ mbap_len + bytes([recv_mbap[6]])

        return {
            "MBAP":mbap,
            "FC":fc,
            "COUNT": adu["COUNT"],
            "VALUE": adu["VALUE"]
        }

   
    # n번째 비트가 True/False인지 확인 용도

    def writeSingleCoil(self, msg):
        splits = self.util.splits(msg)
        recv_mbap = splits["MBAP"]
        fc = splits["FC"]
        data = splits["DATA"]
        addr = data[0:2]
        value=data[2:4]

        # addr_int = int.from_bytes(data[0:2])
        startAddress = data[0:2]
        # value_int = int.from_bytes(data[2:4])
        value = data[2:4]

        self.util.writeBit(self.config, startAddress,value)
        mbap_len = len(bytes([recv_mbap[6]])+bytes([fc])+startAddress+value)
        mbap_len = self.util.int_to_2bytes(mbap_len)
        mbap=recv_mbap[:4]+ mbap_len + bytes([recv_mbap[6]])

        return {
            "MBAP":mbap,
            "FC":fc,
            "ADDRESS": addr,
            "length": value
        }

    def writeMultipleCoil(self, msg):
        splits = self.util.splits(msg)
        recv_mbap = splits["MBAP"]
        fc = splits["FC"]
        data = splits["DATA"]

        # addr = int.from_bytes(data[0:2],byteorder='big')
        addr = data[0:2]
        bitcount = int.from_bytes(data[2:4],byteorder='big')
        bytecount = data[4]
        value = data[5:]

        self.util.writeBit(self.config,addr,value,bitcount,bytecount)
        mbap_length = len(msg[7:14])
        mbap_length = self.util.int_to_2bytes(mbap_length)
        mbap = recv_mbap[:4] + mbap_length + bytes([recv_mbap[6]])
        return{
            "MBAP":mbap,
            "FC":fc,
            "ADDRESS":data[:2],
            "length":data[2:4]
        }
    


        if int_value < 256:
            return_value = bytes([0,int_value])
        elif int_value >= 256:
            return_value =  bytes([int_value//256,int_value%256])
        return return_value