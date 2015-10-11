from socket import *
import errno
from socket import error as socket_error
import Queue
#in python 3, Queue is renamed to queue
import threading
import time

class TCPconnection(object):
    def __init__(self, server, host, port):
        self.server = server
        self.host = host
        self.port = int(port)
        
        self.send_queue = None
        self.send_thread = None
        self.receive_queue = None
        self.receive_thread = None
    
    def is_alive(self):
        if (self.send_thread != None and self.receive_thread != None):
            return (self.send_thread.is_alive() and self.receive_thread.is_alive())
        else:
            return False
    
    def send(self, msg):
        self.send_queue.put(msg)

    def get_receive(self):
        if (not self.receive_queue.empty()):
            return self.receive_queue.get()
        else:
            return None

    def receive(self):
        msg = None
        while (msg == None):
            msg = self.get_receive()
        return msg

    def connect(self):
        if not self.is_alive():
            sock = get_socket()
            clientsocket = sock
            self.receive_queue = Queue.Queue()
            self.send_queue = Queue.Queue()

            if (self.server):
                arry = server_connect(sock, self.port)
                clientsocket = arry[0]
                return arry[1][0]
            else:
                try:
                    client_connect(sock, self.host, self.port)
                except socket_error as serr:
                    return 0
            self.send_thread = Sender(clientsocket, self.host, self.port, self.send_queue)
            self.send_thread.start()
            self.receive_thread = Receiver(clientsocket, self.host, self.port, self.receive_queue)
            self.receive_thread.start()
        return 1

    def close(self):
        if (self.send_thread != None):
            self.send_thread.close()
            self.send_thread = None
        if (self.receive_thread != None):
            self.receive_thread.close()
            self.receive_thread = None

        self.send_queue = None
        self.receive_queue = None

    def __del__(self):
        self.close()


def get_socket():
    sock = socket(AF_INET, SOCK_STREAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    return sock

def server_connect(sock, port):
    sock.bind(('', port))
    print ('The server is ready to receive connection request')
    sock.listen(1)
    clientsocket, addr = sock.accept()
    print('Connected to {}'.format(addr))
    return [clientsocket, addr]

def client_connect(sock, host, port):
    try:
        sock.connect((host, port))
        print('Connected to {} at port {}'.format(host, port))
    except socket_error as serr:
        print('Error: Connection refused... ')
        raise

class Sender(threading.Thread):
    def __init__(self, socket, host, port, send_queue):
        threading.Thread.__init__(self)
        if (socket == None):
            self.socket = get_socket()
        else:
            self.socket=socket
        self.host = host
        self.port = port
        self.send_queue=send_queue
        self.keep_alive = True

    def run(self):
        while (self.keep_alive):
            if (not self.send_queue.empty()):
                msg = self.send_queue.get()
                self.socket.send(msg)
        self.socket.close()

    def close(self):
        self.keep_alive = False

class Receiver(threading.Thread):
    def __init__(self, socket, host, port, receive_queue):
        threading.Thread.__init__(self)
        if (socket == None):
            self.socket = get_socket
        else:
            self.socket = socket
        self.host = host
        self.port = port
        self.receive_queue = receive_queue
        self.keep_alive = True

    def run(self):
        while (self.keep_alive):
            msg = self.socket.recv(1024)
            if (msg):
                self.receive_queue.put(msg)
                print (msg)
        self.socket.close()

    def close(self):
        self.keep_alive = False

















