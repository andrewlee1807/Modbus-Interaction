import threading
import socket
from myconfig import myconfig
from lib.modbus.config import config

from lib.modbus.modbus_coil import modbus_coil
from lib.modbus.modbus_register import modbus_register

from jetson_api import Service

# Action code
AI_ACTION_CODE_START = 0x01 * 2
AI_ACTION_CODE_STOP = 0x02 * 2
AI_ACTION_CODE_RESUME = 0x03 * 2
AI_ACTION_CODE_SUSPEND = 0x04 * 2

# Error code
ERROR_CODE_NO_PRODUCT = 0x01 * 2
ERROR_CODE_NO_MODEL = 0x02 * 2
ERROR_CODE_NO_WORK = 0x03 * 2


class status:
    PROCESSING = 1
    FAILED = 2  # defect in case classification
    FINISHED = 3  # Ok in case classification
    OFF = 0
    ON = 1
    NO_FILE = 4 # no file available


def hex2int(hex):
    return int(hex, 16)  # int.from_bytes(hex)


def int_to_2_bytes(int_value):
    return bytes([0, int_value])


# Define forward functions
def updateClient(addr, isConnect=False):
    """Connection of client's status"""
    if isConnect:
        client_info = "The client has connected. The IP address is " + str(
            addr[0]) + " and the access port is " + str(addr[1])
        print(client_info)


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
        if thread is None:  # no thread
            return status.FAILED
        elif thread.is_alive():  # alive
            return status.PROCESSING
        else:
            thread = None  # reset WITH ONE TIME CHECK STATUS SUCCESSFULLY
            return status.FINISHED
    except Exception as e:
        print(e)


class ServerSocket():
    def __init__(self):
        self.service = Service()  # AI service

        self.modbus_bit = modbus_coil()
        self.modbus_register = modbus_register()
        self.config = config

        self.myConfig = myconfig
        self.fc_list = self.config.fc_list
        # ActionCode
        self.action_code = (self.myConfig.MODBUS_ADDRESS_ACTION_CODE) * 2
        # Classify result
        self.get_result_classification = (self.myConfig.MODBUS_ADDRESS_RESULT) * 2
        # Model change result
        self.get_result_change_model = (self.myConfig.MODBUS_ADDRESS_MODEL_CHANGE_RESULT) * 2
        # Model download completion result value
        self.model_download_result = (self.myConfig.MODBUS_ADDRESS_MODEL_DOWNLOAD_RESULT) * 2
        self.coll_disc_trans = (self.myConfig.MODBUS_ADDRESS_COLL_DISC) * 2
        self.coll_disc_result = (self.myConfig.MODBUS_ADDRESS_COLL_DISC_RESULT) * 2
        # change model
        self.start_model_change = (self.myConfig.MODBUS_ADDRESS_MODEL_CHANGE) * 2
        # Download model
        self.start_model_download = (self.myConfig.MODBUS_ADDRESS_MODEL_DOWNLOAD) * 2
        # Download url
        self.set_download_url = (self.myConfig.MODBUS_ADDRESS_DOWNLOAD_URL) * 2
        # model name
        self.set_model_name = (self.myConfig.MODBUS_ADDRESS_MODEL_NAME) * 2

        self.bListen = False
        self.clients = []
        self.ip = []
        self.thread_connections = []

        # inference from jetson api
        self.last_detection_result = None

        self.thread_change_model = None

        self.thread_inference = None  # includes: Action(start, stop,..)
        self.thread_downloading = None  # special thread to download model

    def getStringFromAddress(self, start, end):
        temp = self.config.MODBUS_ADDRESS[start:end]
        value_recv = ""
        for i in range(0, len(temp), 2):
            temp_hex = (temp[i] << 8) + temp[i + 1]
            value_recv += chr(temp_hex)
        print("Received from client:", value_recv)
        return value_recv

    def __extract(self, msg):
        """Extract the request information"""
        functionCode = msg[self.config.FUNCTION_CODE_INDEX]
        data = None
        packet = None
        if functionCode == 1:
            # msg = bytes([0,0,0,0,0,6,1,1,0,1,0,17])
            data = self.modbus_bit.readCoil(msg)
            packet = data["MBAP"] + bytes([data["FC"]]) + bytes([data["COUNT"]]) + data["VALUE"]
        elif functionCode == 2:
            data = self.modbus_bit.readDiscreteInput(msg)
            packet = data["MBAP"] + bytes([data["FC"]]) + data["COUNT"] + data["VALUE"]
        elif functionCode == 3:
            data = self.modbus_register.readHoldingReigster(msg)
            packet = data["MBAP"] + bytes([data["FC"]]) + data["COUNT"] + data["VALUE"]
        elif functionCode == 4:
            data = self.modbus_register.readInputRegister(msg)

        elif functionCode == 5:
            data = self.modbus_bit.writeSingleCoil(msg)
            packet = data["MBAP"] + bytes([data["FC"]]) + data["ADDRESS"] + data["length"]
        elif functionCode == 6:
            data = self.modbus_register.writeSingleRegister(msg)

        elif functionCode == 15:
            data = self.modbus_bit.writeMultipleCoil(msg)
            packet = data["MBAP"] + bytes([data["FC"]]) + data["ADDRESS"] + data["length"]
        elif functionCode == 16:
            data = self.modbus_register.writeMultipleRegister(msg)

        return data

    def inference(self):
        self.last_detection_result = self.service.classification()
        # self.last_detection_result = status.FINISHED 

    def do_request(self, data):  # control the jetson's jobs
        if type(data) == dict:
            func_name = self.fc_list[data["FC"]]
            func_int = data["FC"]
            temp_msg = f"{func_name} ({func_int}) : "
            registers_int = hex
            # write
            if "ADDRESS" in data:
                startAddress = int.from_bytes(data["ADDRESS"], byteorder='big')
                startAddress *= 2
                # Get the URL, Model Name
                if startAddress in [self.set_download_url, self.set_model_name]:
                    print("Get the URL, Model Name")
                    endAddress = startAddress + (int.from_bytes(data["REGISTERS"], byteorder='big')) * 2
                    value = self.getStringFromAddress(startAddress, endAddress)
                    if startAddress == self.set_download_url:
                        self.service.set_download_url(value)
                    else:
                        self.service.set_model_name(value)
                    packet = data["MBAP"] + bytes([data["FC"]]) + data["ADDRESS"] + data["REGISTERS"]
                    return packet
                # Action Code
                elif startAddress == self.action_code:
                    action_value = int.from_bytes(data["VALUE"], byteorder='big') * 2
                    if action_value in [AI_ACTION_CODE_START, AI_ACTION_CODE_RESUME]:  # inference
                        print("Do inference")
                        # create thread to execute
                        if self.thread_inference is None:
                            self.thread_inference = threading.Thread(target=self.inference())
                            self.thread_inference.start()

                    # elif action_value in [AI_ACTION_CODE_STOP, AI_ACTION_CODE_SUSPEND]:  # stop or pause
                    #     pass
                    # else:
                    #     return -1  # ERROR
                    return data["MBAP"] + bytes([data["FC"]]) + data["ADDRESS"] + data["VALUE"]  # same with do_request
                # Start to download model from url
                elif startAddress in [self.start_model_download]:
                    print("Start to download model from url")
                    value_int = int.from_bytes(data["VALUE"], byteorder='big')
                    if value_int == status.ON:
                        self.service.download_model()
                    return data["MBAP"] + bytes([data["FC"]]) + data["ADDRESS"] + data["VALUE"]  # same with do_request
                elif startAddress in [self.start_model_change]:
                    print("Start to change model")
                    self.thread_change_model = threading.Thread(target=self.service.change_model)
                    self.thread_change_model.start()
                # Get result Classification
                elif startAddress in [self.get_result_classification]:
                    print("Get result Classification")
                    check_thread = check_thread_alive(self.thread_inference)
                    # finished thread
                    if self.last_detection_result is not None:
                    #if check_thread == status.FINISHED:
                        packet = data["MBAP"] + bytes([data["FC"]]) + bytes([2]) + int_to_2_bytes(self.last_detection_result)
                        #self.last_detection_result = None  # reset result
                        return packet
                    else:  # processing
                        packet = data["MBAP"] + bytes([data["FC"]]) + bytes([2]) + int_to_2_bytes(status.PROCESSING)
                        return packet
                elif startAddress in [self.get_result_change_model]:
                    print("get_result_change_model")
                    check_thread = check_thread_alive(self.thread_change_model)
                    packet = data["MBAP"] + bytes([data["FC"]]) + data["ADDRESS"] + int_to_2_bytes(check_thread)
                    return packet
                elif startAddress in [self.model_download_result]:
                    print("model_download_result")
                    check_thread = check_thread_alive(self.thread_downloading)
                    # if check_thread == status.FINISHED and 
                    packet = data["MBAP"] + bytes([data["FC"]]) + data["ADDRESS"] + int_to_2_bytes(check_thread)
                    return packet

                else:
                    return -1

    def start(self, port=502):
        """Open port to listen all connections"""
        ip = self.get_ip_address()
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server.bind((ip, port))  # # Bind the IP address and the port number
        except Exception as e:
            print('Bind Error : ', e)
            return False
        else:
            self.bListen = True
            t = threading.Thread(target=self.listen, args=(self.server, ip, port))
            t.start()
            # self.listen(self.server, ip, port)
            print('Server Listening...')
            print(f'ip : {ip}, port : {port}')
        return True

    def get_ip_address(self):
        """Get the owner ip address"""

        try:
            host_ip = socket.gethostbyname('www.google.com')  # what is my ip?
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host_ip, 80))
        except:
            try:
                from subprocess import check_output
                return check_output(['hostname', '-I']).decode("utf-8").split()[0]
            except:
                return "127.0.0.1"
        else:
            ip_address = sock.getsockname()[0]
            sock.close()
            return ip_address

    def stop(self):
        try:
            if self.clients:
                self.removeAllClients()
            self.bListen = False
            self.server.shutdown(socket.SHUT_RDWR)
            self.server.close()
            print('Server Closing...')
            return False
        except Exception as e:
            print("Server Stop() Error : ", e)
            return True

    def listen(self, server, ip, port):
        """Catch the connection"""
        while self.bListen:
            server.listen(5)  # Listen for incoming connections
            try:
                client, addr = server.accept()
            except Exception as e:
                print('Accept() Error : ', e)
                break
            else:
                """ Create new threading to handle new connection"""
                self.clients.append(client)
                self.ip.append(addr)
                updateClient(addr, True)

                # Establish connection and create new thread to handle the COMMUNICATION
                t = threading.Thread(target=self.receive, args=(addr, client))
                self.thread_connections.append(t)
                t.start()

                # self.receive(addr, client)

        self.removeAllClients()
        self.server.close()

    def receive(self, addr, client):
        """Communicate Server with Client ~Thread after connected"""
        while True:
            try:
                # This is message from client
                msg = client.recv(1024)
            except Exception as e:
                print('Receive message function Error :', e)
                break
            else:
                print("Receive packet from PLC: ")
                for i in msg:
                    print(i, end=" ")
                print()
                if msg:
                    data = self.__extract(msg)
                    print(data)
                    # Do the request
                    packet_response = self.do_request(data)
                    self.send(packet_response)
                if not msg:
                    break
        self.removeClient(addr, client)
        # self.removeAllClients()

    def send(self, msg):
        """Reply to Client"""
        try:
            print("Server reply to clients: ", msg)
            for c in self.clients:  # send to all clients
                c.send(msg)
        except Exception as e:
            print('Send message function Error : ', e)

    def removeClient(self, addr, client):
        idx = -1
        for k, v in enumerate(self.clients):
            if v == client:
                idx = k
                break
        print(f"{addr} client exit")
        client.close()
        self.ip.remove(addr)
        self.clients.remove(client)
        del (self.thread_connections[idx])

    def removeAllClients(self):
        for c in self.clients:
            c.close()

        for addr in self.ip:
            updateClient(addr, False)

        self.ip.clear()
        self.clients.clear()
        self.thread_connections.clear()


if __name__ == '__main__':
    jetson_server = ServerSocket()
    jetson_server.start()
