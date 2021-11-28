import threading
import socket
from myconfig import myconfig
from lib.modbus.config import config

from lib.modbus.modbus_coil import modbus_coil
from lib.modbus.modbus_register import modbus_register

from jetson_api import Service
from utils import *


class ServerSocket():
    def __init__(self):
        self.service = Service()  # AI service
        self.log_obj = log_obj
        """Load modbus api"""
        self.modbus_bit = modbus_coil()
        self.modbus_register = modbus_register()

        """Load the CODE configs"""
        self.myConfig = myconfig
        self.config = config
        self.fc_list = self.config.fc_list
        # ActionCode
        self.action_code = (self.myConfig.MODBUS_ADDRESS_ACTION_CODE) * 2
        # Classify result
        self.get_result_classification = (self.myConfig.MODBUS_ADDRESS_RESULT) * 2
        # Model change result
        self.get_result_change_model = (self.myConfig.MODBUS_ADDRESS_MODEL_CHANGE_RESULT) * 2
        # Model download completion result value
        self.model_download_result = (self.myConfig.MODBUS_ADDRESS_MODEL_DOWNLOAD_RESULT) * 2
        # Collector or Discriminator Transition
        self.coll_disc_trans = (self.myConfig.MODBUS_ADDRESS_COLL_DISC) * 2
        # Collector or Discriminator Transition result
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
        self.last_detection_result = ErrorCode.NO_MODEL

        self.thread_change_model = None  # Change new model
        self.thread_inference = None  # includes: Action(start, stop,..)
        self.thread_downloading = None  # Thread to download model
        self.thread_camera_action = None  # Thread to control camera

    def updateClient(self, addr, isConnect=False):
        """Connection of client's status"""
        if isConnect:
            client_info = "The client has connected. The IP address is " + str(
                addr[0]) + " and the access port is " + str(addr[1])
            self.log_obj.export_message(client_info, Notice.INFO)
        else:
            client_info = f"The client {addr[0]} has disconnected and closed {addr[1]} port"
            self.log_obj.export_message(client_info, Notice.INFO)

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
        elif functionCode == 16:
            data = self.modbus_register.writeMultipleRegister(msg)

        elif functionCode == 15:
            data = self.modbus_bit.writeMultipleCoil(msg)
            packet = data["MBAP"] + bytes([data["FC"]]) + data["ADDRESS"] + data["length"]
        return data, packet

    def __create_error_message(self, data, error_type):  # => MBAP-FC-VALUE
        return data["MBAP"] + bytes([data["FC"] + 0x80]) + two_bytes(error_type)

    def inference(self):
        self.last_detection_result = self.service.classification()
        # self.last_detection_result = status.GOOD

    def do_request(self, data):  # control the jetson's jobs
        if type(data) == dict:
            # write
            if "ADDRESS" in data:
                startAddress = int.from_bytes(data["ADDRESS"], byteorder='big')
                startAddress *= 2
                # Receive new the URL, Model Name => MBAP + FC + ADDRESS + REGISTERS (same with request)
                if startAddress in [self.set_download_url, self.set_model_name]:
                    print("Receive the URL| Model Name ")
                    endAddress = startAddress + (int.from_bytes(data["REGISTERS"], byteorder='big')) * 2
                    value = self.getStringFromAddress(startAddress, endAddress)
                    if startAddress == self.set_download_url:
                        self.service.set_download_url(value)
                    else:
                        self.service.set_model_name(value)
                    packet = data["MBAP"] + bytes([data["FC"]]) + data["ADDRESS"] + data["REGISTERS"]
                    return packet

                # ACTION CODE => MBAP + FC + ADDRESS + REGISTERS (same with request)
                elif startAddress == self.action_code:
                    action_value = int.from_bytes(data["VALUE"], byteorder='big') * 2
                    if action_value in [AI_ACTION_CODE.START, AI_ACTION_CODE.RESUME]:  # inference
                        print("Do inference..")
                        # create thread to execute
                        if self.thread_inference is None:
                            self.thread_inference = threading.Thread(target=self.inference())
                            self.thread_inference.start()
                    return data["MBAP"] + bytes([data["FC"]]) + data["ADDRESS"] + data["VALUE"]  # same with do_request

                # Start to download model from url => MBAP-FC-ADDRESS-VALUE (same with do_request)
                elif startAddress in [self.start_model_download]:
                    print("Start to download model from url")
                    value_int = int.from_bytes(data["VALUE"], byteorder='big')
                    check_thread = check_thread_alive(self.thread_downloading)
                    if value_int == Status.ON and check_thread != Status.PROCESSING:  # Free thread to download
                        self.thread_downloading = threading.Thread(target=self.service.download_model)
                    return data["MBAP"] + bytes([data["FC"]]) + data["ADDRESS"] + data["VALUE"]  # same with do_request

                # Get the result's download url => MBAP-FC-COUNT-VALUE
                elif startAddress in [self.model_download_result]:
                    print("Get the result's download url")
                    check_thread = check_thread_alive(self.thread_downloading)
                    if check_thread == Status.PROCESSING:
                        packet = data["MBAP"] + bytes([data["FC"]]) + bytes([2]) + two_bytes(Status.PROCESSING)
                    else:
                        self.thread_downloading = None  # reset the thread
                        result = self.service.get_download_result()
                        packet = data["MBAP"] + bytes([data["FC"]]) + bytes([2]) + two_bytes(result)
                    return packet

                # Start to change new model
                elif startAddress in [self.start_model_change]:
                    print("Start to change model")
                    value_int = int.from_bytes(data["VALUE"], byteorder='big')
                    check_thread = check_thread_alive(self.thread_change_model)
                    if value_int == Status.ON and check_thread != Status.PROCESSING:
                        self.thread_change_model = threading.Thread(target=self.service.change_model)
                        self.thread_change_model.start()
                    return data["MBAP"] + bytes([data["FC"]]) + data["ADDRESS"] + data["VALUE"]  # same with do_request

                # Get result's Classification => MBAP-FC-COUNT-VALUE
                elif startAddress in [self.get_result_classification]:
                    print("Get result Classification")
                    check_thread = check_thread_alive(self.thread_inference)
                    if check_thread == Status.PROCESSING:
                        packet = data["MBAP"] + bytes([data["FC"]]) + bytes([2]) + two_bytes(Status.PROCESSING)
                    else:
                        if self.last_detection_result == ErrorCode.NO_MODEL:
                            packet = self.__create_error_message(data, ErrorCode.NO_MODEL)
                        elif self.last_detection_result == ErrorCode.NO_PRODUCT:
                            packet = self.__create_error_message(data, ErrorCode.NO_PRODUCT)
                        else:
                            packet = data["MBAP"] + bytes([data["FC"]]) + bytes([2]) + \
                                     two_bytes(self.last_detection_result)
                    return packet

                # Get the result's changing new model => MBAP-FC-COUNT-VALUE
                elif startAddress in [self.get_result_change_model]:
                    print("Get the result's changing model")
                    check_thread = check_thread_alive(self.thread_change_model)
                    if check_thread == Status.PROCESSING:
                        packet = data["MBAP"] + bytes([data["FC"]]) + bytes([2]) + two_bytes(Status.PROCESSING)
                    else:
                        self.thread_change_model = None  # reset thread
                        result = self.service.get_download_result()
                        packet = data["MBAP"] + bytes([data["FC"]]) + bytes([2]) + two_bytes(result)
                    return packet

                # Start to change collector or detector
                elif startAddress in [self.coll_disc_trans]:  # Control camera: open or close
                    print("Control the camera")
                    value_int = int.from_bytes(data["VALUE"], byteorder='big')
                    check_thread = check_thread_alive(self.thread_camera_action)
                    if check_thread != Status.PROCESSING:
                        if value_int == Status.DETECTOR:  # open camera
                            self.thread_camera_action = threading.Thread(target=self.service.open_camera)
                            self.thread_camera_action.start()
                        else:  # close camera
                            self.thread_camera_action = threading.Thread(target=self.service.close_camera)
                            self.thread_camera_action.start()

                    return data["MBAP"] + bytes([data["FC"]]) + data["ADDRESS"] + data["VALUE"]  # same with do_request

                # Get the result's changing collector or detector => MBAP-FC-COUNT-VALUE
                elif startAddress in [self.coll_disc_result]:
                    print("Get the result's changing collector or detector")
                    check_thread = check_thread_alive(self.thread_camera_action)
                    if check_thread == Status.PROCESSING:
                        packet = data["MBAP"] + bytes([data["FC"]]) + bytes([2]) + two_bytes(Status.PROCESSING)
                    else:
                        self.thread_camera_action = None  # reset the thread
                        result = self.service.get_camera_status()
                        packet = data["MBAP"] + bytes([data["FC"]]) + bytes([2]) + two_bytes(result)
                    return packet
                else:
                    log_obj.export_message("ADDRESS IS NOT DEFINED BEFORE", Notice.EXCEPTION)
            else:
                log_obj.export_message("ADDRESS IS NOT DEFINED BEFORE TO DO REQUEST", Notice.EXCEPTION)
        else:
            log_obj.export_message("DATA CANNOT EXTRACT TO DICT", Notice.ERROR)
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
            self.log_obj.export_message("CANNOT START THE SERVER", Notice.CRITICAL)
            self.log_obj.export_message(e, Notice.CRITICAL)
            return False
        else:
            self.bListen = True
            t = threading.Thread(target=self.listen, args=(self.server, ip, port))
            t.start()
            # self.listen(self.server, ip, port)
            print('Server Listening...')
            print(f'ip : {ip}, port : {port}')
            self.log_obj.export_message("SERVER STARTED SUCCESSFULLY..", Notice.INFO)
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
                self.log_obj.export_message("CANNOT PUBLIC PORT ON SERVER!", Notice.CRITICAL)
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
            self.log_obj.export_message("SERVER CANNOT STOP!", Notice.ERROR)
            self.log_obj.export_message(e, Notice.ERROR)
            return True

    def listen(self, server, ip, port):
        """Catch the connection"""
        while self.bListen:
            server.listen(5)  # Listen for incoming connections
            try:
                client, addr = server.accept()
            except Exception as e:
                self.log_obj.export_message("SERVER ESTABLISHED ERROR!", Notice.EXCEPTION)
                self.log_obj.export_message(e, Notice.EXCEPTION)
                break
            else:
                """ Create new threading to handle new connection"""
                self.clients.append(client)
                self.ip.append(addr)
                self.updateClient(addr, True)

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
                self.log_obj.export_message("ERROR RECEIVE DATA FROM CLIENT", Notice.EXCEPTION)
                self.log_obj.export_message(e, Notice.EXCEPTION)
                break
            else:
                self.log_obj.export_message("Received packet from client.", Notice.INFO)
                for i in msg:
                    print(i, end=" ")
                print()
                if msg:
                    try:
                        data, packet_exception = self.__extract(msg)
                        print(data)
                        # Do the request
                        packet_response = self.do_request(data)
                        if packet_response == -1:
                            packet_response = packet_exception
                    except Exception as e:
                        log_obj.export_message("ERROR AT DO REQUEST, DATA IS NON-DICT", Notice.CRITICAL)
                        log_obj.export_message(e, Notice.CRITICAL)
                        packet_response = self.__create_error_message(data,
                                                                      ErrorCode.NO_WORK)  # should be fixed value error
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
            self.log_obj.export_message("CANNOT SEND MESSAGE TO CLIENT", Notice.CRITICAL)
            self.log_obj.export_message(e, Notice.CRITICAL)

    def removeClient(self, addr, client):
        idx = -1
        for k, v in enumerate(self.clients):
            if v == client:
                idx = k
                break
        client.close()
        self.log_obj.export_message(f"Client {addr} exited", Notice.INFO)
        self.ip.remove(addr)
        self.clients.remove(client)
        del (self.thread_connections[idx])

    def removeAllClients(self):
        for c in self.clients:
            c.close()

        for addr in self.ip:
            self.updateClient(addr)

        self.ip.clear()
        self.clients.clear()
        self.thread_connections.clear()


if __name__ == '__main__':
    jetson_server = ServerSocket()
    jetson_server.start()
