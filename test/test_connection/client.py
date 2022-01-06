import socket

class Stream:
    def __init__(self):
        self.SERVER_IP = '192.168.0.37'
        self.SERVER_PORT = 1234
        self.client = None

    def init_connection(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((self.SERVER_IP, self.SERVER_PORT))

    def send_msg(self, msg):
        self.client.send(str(msg).encode())
        from_server = self.client.recv(4096).decode()
        return from_server

    def close_connection(self):
        self.client.close()

    def __del__(self):
        self.close_connection()


stream = Stream()
stream.init_connection()
while True:
    msg = input("text: ")
    rep_msg = stream.send_msg(msg)
    print(rep_msg)



