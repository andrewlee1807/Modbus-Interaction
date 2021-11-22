# 개발 일자 : 2021.10. 01
# 개발자 : 김용래
# 제작사 : (주)리눅스아이티

class config :
    
    '''펑션 코드'''
    fc_list = {1:"readCoil",
        2:"readDiscreteInput",
        3:"readHoldingReigster",
        4:"readInputRegister",
        5:"writeSingleCoil",
        6:"writeSingleRegister",
        15:"writeMultipleCoil",
        16:"writeMultipleRegister"}

    '''길이 정의'''
    # mbap Define header index start, end and size
    MBAP_INDEX_START = 0
    MBAP_INDEX_END = 7
    MBAP_HEADER_SIZE = 7
    # function code Index and Size Definition
    FUNCTION_CODE_INDEX=7
    FUNCTION_CODE_SIZE=1
    # address index and size
    ADDRESS_INDEX_START = 8
    ADDRESS_INDEX_END = 10
    ADDRESS_SIZE = 2
    # register, bit count length
    RESGISTERS_SIZE = 2
    COUNT_SIZE = 1

    # ADDRESS length is user defined
    MODBUS_ADDRESS = None