import socket
import threading

from Queue import Queue
from auth import Authentication
from listener import Listener
from sender import Sender
from receiver import Receiver


class VpnServer(object):

    def __init__(self, port, shared_key, connected_callback, broken_conn_callback):
        self.port = port
        self.shared_key = shared_key
        self.connected_callback = connected_callback
        self.broken_conn_callback = broken_conn_callback
        self.send_queue = Queue()
        self.receive_queue = Queue()
        self.authenticated = False
        self.waiting = True
        self.sender = None
        self.receiver = None

    def setup(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error:
            return (-1, "Could not create socket")

        try:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('', self.port))
            self.socket.listen(1) 
        except socket.error:
            return (-1, "Could not bind socket to port " + str(self.port))

        return (0, "VPN server set to listen on port " + str(self.port))

    def send(self, msg):
        self.send_queue.put(msg)

    def start(self, callback=None):
        self.listener = Listener(self.socket, self.shared_key, self, self.connected_callback)
        self.listener.start()

    def bind(self, client_socket):
        self.sender = Sender(client_socket, self.send_queue, self)
        self.receiver = Receiver(client_socket, self.receive_queue, self)
        self.sender.start()
        self.receiver.start()

    def broken_conn(self, client_socket):
        self.sender.close()
        self.send_queue.queue.clear()
        self.receiver.close()
        self.receive_queue.queue.clear()
        self.waiting = True

    def close(self):
        self.listener.close()
        if self.sender:
            self.sender.close()
        if self.receiver
        self.receiver.close()

    def receive(self):
        if not self.receive_queue.empty():
            return self.receive_queue.get()
        else:
            return None
