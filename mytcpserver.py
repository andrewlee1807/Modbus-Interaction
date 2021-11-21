# 개발 일자 : 2021.10. 01
# 개발자 : 김용래
# 제작사 : (주)리눅스아이티

# from threading import Thread
import threading
# import mythread
import socket
from myconfig import myconfig
from lib.modbus.config import config

from lib.modbus.modbus_coil import modbus_coil
from lib.modbus.modbus_register import modbus_register


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

class ServerSocket():
    def __init__(self):
        super().__init__()
        # self.test_set = threading.Event()

        self.modbus_bit = modbus_coil()
        self.modbus_register = modbus_register()
        self.config = config

        self.myConfig = myconfig
        self.fc_list = self.config.fc_list
        # ACtionCode
        self.action_code = (self.myConfig.MODBUS_ADDRESS_ACTION_CODE) * 2
        # Classify result
        self.result = (self.myConfig.MODBUS_ADDRESS_RESULT) * 2
        # Model change result
        self.change_result = (self.myConfig.MODBUS_ADDRESS_MODEL_CHANGE_RESULT) * 2
        # Model download completion result value
        self.model_download_result = (self.myConfig.MODBUS_ADDRESS_MODEL_DOWNLOAD_RESULT) * 2
        self.coll_disc_trans = (self.myConfig.MODBUS_ADDRESS_COLL_DISC) * 2
        self.coll_disc_result = (self.myConfig.MODBUS_ADDRESS_COLL_DISC_RESULT) * 2
        # change model
        self.model_change = (self.myConfig.MODBUS_ADDRESS_MODEL_CHANGE) * 2
        # Download model
        self.model_download = (self.myConfig.MODBUS_ADDRESS_MODEL_DOWNLOAD) * 2
        # Download url
        self.download_url = (self.myConfig.MODBUS_ADDRESS_DOWNLOAD_URL) * 2
        # model name
        self.model_name = (self.myConfig.MODBUS_ADDRESS_MODEL_NAME) * 2

        self.bListen = False
        self.clients = []
        self.ip = []
        self.threads = []

    def getStringFromAddress(self, start, end):
        temp = self.config.MODBUS_ADDRESS[start:end]
        print(len(temp))
        temp_str = ""
        for i in range(0, len(temp), 2):
            temp_hex = (temp[i] << 8) + temp[i + 1]
            temp_str += chr(temp_hex)
        print(temp_str)
        print(len(temp_str))
        return temp_str

    def do_request(self, msg):
        if type(msg) == dict:
            fc_name = self.fc_list[msg["FC"]]
            fc_int = msg["FC"]
            temp_msg = f"{fc_name} ({fc_int}) : "
            # write 출력
            if "ADDRESS" in msg:
                startAddress = int.from_bytes(msg["ADDRESS"], byteorder='big')
                startAddress *= 2
                # Download url,Model Name 정보
                if startAddress in [self.download_url, self.model_name]:
                    endAddress = startAddress + (int.from_bytes(msg["REGISTERS"], byteorder='big')) * 2
                    temp_msg += self.getStringFromAddress(startAddress, endAddress)

    def start(self, port=502):
        """Open port to listen all connections"""
        ip = self.get_ip_address()
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server.bind((ip, port))
        except Exception as e:
            print('Bind Error : ', e)
            return False
        else:
            self.bListen = True
            self.t = threading.Thread(target=self.listen, args=(self.server, ip, port))
            self.t.start()
            print('Server Listening...')
            print(f'ip : {ip}, port : {port}')
        return True

    def get_ip_address(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(("pwnbit.kr", 443))
            ip_address = sock.getsockname()[0]
            sock.close()
            return ip_address
        except:
            return "127.0.0.1"

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
            server.listen(5)
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

                """New Thread"""
                t = threading.Thread(target=self.receive, args=(addr, client))
                self.threads.append(t)
                t.start()

                # self.receive(addr, client)

        self.removeAllClients()
        self.server.close()

    def receive(self, addr, client):
        """Communicate Server with Client ~Thread after connected"""
        while True:
            try:
                recv = client.recv(1024)
            except Exception as e:
                print('Recv() Error :', e)
                break
            else:
                # This is message from client
                msg = recv
                print("Receive packet from PLC: ")
                for i in msg:
                    print(i, end=" ")
                print()
                if msg:
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
                        packet = data["MBAP"] + bytes([data["FC"]]) + bytes([data["COUNT"]]) + data["VALUE"]
                    elif functionCode == 5:
                        data = self.modbus_bit.writeSingleCoil(msg)
                        packet = data["MBAP"] + bytes([data["FC"]]) + data["ADDRESS"] + data["length"]
                    elif functionCode == 6:
                        data = self.modbus_register.writeSingleRegister(msg)
                        packet = data["MBAP"] + bytes([data["FC"]]) + data["ADDRESS"] + data["REGISTERS"]
                    elif functionCode == 15:
                        data = self.modbus_bit.writeMultipleCoil(msg)
                        packet = data["MBAP"] + bytes([data["FC"]]) + data["ADDRESS"] + data["length"]
                    elif functionCode == 16:
                        data = self.modbus_register.writeMultipleRegister(msg)
                        packet = data["MBAP"] + bytes([data["FC"]]) + data["ADDRESS"] + data["REGISTERS"]
                    print(data)

                    # Do request from PLC
                    self.do_request(data)

                    self.send(packet)
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
            print('Send() Error : ', e)

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
        del (self.threads[idx])

    def removeAllClients(self):
        for c in self.clients:
            c.close()

        for addr in self.ip:
            updateClient(addr, False)

        self.ip.clear()
        self.clients.clear()
        self.threads.clear()


if __name__ == '__main__':
    jetson_server = ServerSocket()
    jetson_server.start()
