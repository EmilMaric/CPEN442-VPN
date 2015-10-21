import socket
import threading

from Queue import Queue
from auth import Authentication
from listener import Listener
from sender import Sender
from receiver import Receiver
from logger import Logger


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
        self.is_server = True
        self.sessionkey=''

    def setup(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error:
            return (-1, "Could not create socket")

        try:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('', self.port))
            Logger.log("Listening for connections...", self.is_server)
            self.socket.listen(1) 
        except socket.error:
            return (-1, "Could not bind socket to port " + str(self.port))

        return (0, "VPN server set to listen on port " + str(self.port))

    def send(self, msg):
        self.authenticated=self.listener.authenticated
        if (self.authenticated):
            self.sessionkey=self.listener.auth.get_sessionkey()
            Logger.log("sessionkey: " +self.sessionkey, self.is_server)
            emsg = self.listener.auth.encrypt_message(msg, self.sessionkey)
            self.send_queue.put(emsg)
            Logger.log("Put message on send queue: "+ msg, self.is_server)
        else:
            self.send_queue.put(msg)
            Logger.log("Put message on send queue: "+ msg, self.is_server)
    
    def receive(self):
        self.sessionkey = self.listener.auth.get_sessionkey()
        self.authenticated = self.listener.authenticated
        if not self.receive_queue.empty():
            msg = self.receive_queue.get()
            if (self.authenticated):
                msg = self.listener.auth.decrypt_message(msg, self.sessionkey)
                Logger.log("Decrypted msg: "+ msg, self.is_server)
            return msg
        else:
            return None

    def start(self, callback=None):
        self.listener = Listener(self.socket, self.shared_key, self, self.connected_callback)
        self.listener.start()

    def bind(self, client_socket):
        self.sender = Sender(client_socket, self.send_queue, self)
        self.receiver = Receiver(client_socket, self.receive_queue, self)
        self.sender.start()
        self.receiver.start()

    def broken_conn(self):
        Logger.log("Broken connection", self.is_server)
        self.send_queue.queue.clear()
        self.receive_queue.queue.clear()
        self.sender.close()
        self.receiver.close()
        self.waiting = True

    def close(self):
        Logger.log("Connection closing", self.is_server)
        self.send_queue.queue.clear()
        self.receive_queue.queue.clear()
        self.listener.close()
        self.socket.close()
        if self.sender:
            self.sender.close()
        if self.receiver:
            self.receiver.close()


