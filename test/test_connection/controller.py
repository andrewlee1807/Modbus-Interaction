import jetson.inference
import socket
from threading import Thread
from multiprocessing import Pool
import threading
import asyncio
import time

serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

serv.bind(('0.0.0.0', 1234))
serv.listen(5)
thread_load = None
net = None


class myThread(threading.Thread):
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter

    def run(self):
        print("Starting " + self.name)
        # print_time(self.name, 5, self.counter)
        load_model()
        print("Exiting " + self.name)

    # def start(self):
    #     load_model()


def load_model():
    _params = ['--input_blob=input_0', '--output_blob=output_0', '--labels=labels/apple.txt',
               '--model=models/Apple_Eff.onnx']
    net = jetson.inference.imageNet("", _params)
    print("Loaded model")


def check_thread_alive(thread):
    try:
        if thread is None:  # no thread started before
            return -1
        elif thread.is_alive():  # alive
            return 0
        else:  # finish
            return 1
    except Exception as e:
        print(e)


try:
    pool = Pool(processes=4)
    # thread_class = myThread(1, "Load model", 1)
    print("start server")
    while True:
        conn, addr = serv.accept()
        print("connected : ", addr)
        while True:
            data = conn.recv(4096).decode()
            if not data: break
            print("from client: ", data)

            if data == 'load_model':
                r1 = pool.apply_async(load_model)
                # thread_class.start()
                # thread_load = Thread(target=load_model)
                # thread_load.start()
            elif data == 'check':
                status = check_thread_alive(thread_load)
                print("Status: ", status)

            conn.send("I am SERVER\n".encode())
        conn.close()
        print("client disconnected")
except Exception as e:
    print("error")
    serv.close()
