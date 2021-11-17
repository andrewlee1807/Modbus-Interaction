class util:
    def splits(msg):
        # mbap
        mbap = msg[0:7]

        # 펑션 코드
        fc = msg[7]
        
        # 데이터
        adu = msg[8:]

        return {
            "MBAP":mbap,
            "FC":fc,
            "DATA":adu
        }

    def readBit(config, start, length):
        count = 0
        if (length % 8) >0:
            count = (length // 8)+1
        elif (length % 8) == 0:
            count = (length // 8)
        value = config.MODBUS_ADDRESS[start:(start+count)]
        return {
            "COUNT": count,
            "VALUE": value
        }

    def writeBit(config, addr,value,bit_count=None,byte_count=None):
        # addr_int = addr
        addr_int = int.from_bytes(addr,byteorder='big')
        start_byte = addr_int // 8
        start_bit = addr_int % 8
        if start_bit > 0:
                start_byte += 1
        # writesinglecoil
        if bit_count == None or bit_count == 1 :
            temp_byte = config.MODBUS_ADDRESS[start_byte]
            temp_bit = int(bin(1<<(start_bit-1)))
            if value[0] ==255:
                result_byte = temp_byte | temp_bit
            elif value[0] == 0:
                temp_bit = temp_bit ^ 255
                result_byte = temp_byte & temp_bit
            config.MODBUS_ADDRESS[start_byte] = result_byte
        # writemultiplecoils
        else:
            while_on_off = True
            value_byte_index = 0
            value_bit_index = 0
            while_cnt=0
            while while_on_off:
                if value_byte_index == len(value) or bit_count == (while_cnt):
                    while_on_off =False
                if start_bit > 7:
                    start_bit = 0
                    start_byte += 1
                if value_bit_index > 8:
                    value_byte_index += 1
                    value_bit_index =0
                temp_byte = config.MODBUS_ADDRESS[start_byte]
                if self.get_nth_bit(value[value_byte_index],value_bit_index) == True:
                    temp_bit = int(bin(1<<(value_bit_index)),2)
                    result_byte = temp_byte | temp_bit
                    config.MODBUS_ADDRESS[start_byte] = result_byte
                    start_bit += 1
                    value_bit_index += 1
                elif self.get_nth_bit(value[value_byte_index],value_bit_index) == True:
                    if self.get_nth_bit(temp_byte,start_bit) == True:
                        temp_bit = temp_bit ^ 255
                        result_byte = temp_byte & temp_bit
                        config.MODBUS_ADDRESS[start_byte] = result_byte
                    start_bit += 1
                    value_bit_index += 1
                while_cnt+=1

    def get_nth_bit(n, nth):
        return bool(n & (1 << nth))

    def int_to_2bytes(int_value):
        if int_value < 256:
            return_value = bytes([0,int_value])
        elif int_value >= 256:
            return_value =  bytes([int_value//256,int_value%256])
        return return_value