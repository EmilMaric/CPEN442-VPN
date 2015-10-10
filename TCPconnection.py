from socket import *
import errno
from socket import error as socket_error
import Queue
#in python 3, Queue is renamed to queue
import threading
import time

RECV_LENGTH = 1024


class TCPconnection(object):
    def __init__(self, server, host, port):
        self.host = host
        self.port = int(port)
        self.server = server
        self.send_queue = None
        self.send_thread = None
        self.receive_queue = None
        self.receive_thread = None
    
    def is_alive(self):
        if self.send_thread != None and self.receive_thread != None:
            return (self.send_thread.is_alive() and self.receive_thread.is_alive())
        else:
            return False

    def connect(self):
        if not self.is_alive():
            sock = get_socket()
            self.receive_queue = Queue.Queue()
            self.send_queue = Queue.Queue()

            if self.server:
                arry = server_connect(sock, self.port)
                clientsocket = arry[0]
                return arry[1][0]
            else:
                try:
                    client_connect(sock, self.host, self.port)
                except socket_error as serr:
                    return 0
        return 1

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

















