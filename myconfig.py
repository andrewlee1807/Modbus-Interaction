# 개발 일자 : 2021.10. 01
# 개발자 : 김용래
# 제작사 : (주)리눅스아이티

class myconfig:
    # IP = "192.168.0.156"

    ''' 액션 코드 정의'''
    MODBUS_ACTION_CODE = {
        "1":"판별 시작",
        "2":"판별 취소",
        "3":"판별 재시작",
        "4":"판별 일시 정지"
    }

    '''주소 정의'''
    # 0x20(32) : action_code
    MODBUS_ADDRESS_ACTION_CODE = 0x20
    # 0x21(33) : 판별 결과 값
    MODBUS_ADDRESS_RESULT = 0x21
    # 0x22(34) = 모델 변경
    MODBUS_ADDRESS_MODEL_CHANGE = 0x22
    # 0x23(35) = 모델 변경 결과값
    MODBUS_ADDRESS_MODEL_CHANGE_RESULT = 0x23
    # 0x24(36) = 모델 다운로드
    MODBUS_ADDRESS_MODEL_DOWNLOAD = 0x24
    # 0x25(37) = 모델 다운로드 결과 값
    MODBUS_ADDRESS_MODEL_DOWNLOAD_RESULT = 0x25
    # 0x26(38) = 수집기 또는 판별기 전환---->현재 미사용중.
    MODBUS_ADDRESS_COLL_DISC = 0x26
    # 0x27(39) = 수집기 또는 판별기 전환 결과 요청
    MODBUS_ADDRESS_COLL_DISC_RESULT = 0x27
    # 0x30 ~ 0xff = spare
    MODBUS_ADDRESS_SPARE_START = 0x30
    MODBUS_ADDRESS_SPARE_END = 0xff
    # 0x100(256) = 다운로드 url(200문자)
    MODBUS_ADDRESS_DOWNLOAD_URL = 0x0100
    # 0x200(512) = 모델이름(200문자)
    MODBUS_ADDRESS_MODEL_NAME = 0x0200
    # MODBUS_ADDRESS = bytearray(768)