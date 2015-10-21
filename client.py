import socket
import threading

from Queue import Queue
from auth import Authentication
from sender import Sender
from receiver import Receiver
from logger import Logger
import sys


class VpnClient(object):

    def __init__(self, ip_addr, port, shared_key, broken_conn_callback):
        self.ip_addr = ip_addr
        self.port = port
        self.shared_key = shared_key
        self.broken_conn_callback = broken_conn_callback
        self.send_queue = Queue()
        self.receive_queue = Queue()
        self.waiting = True
        self.is_server=False
        self.authenticated=False

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except socket.error:
            return (-1, "Could not create socket")

        try:
            self.socket.settimeout(10)
            self.socket.connect((self.ip_addr, self.port))
            self.waiting = False
            self.auth = Authentication(self.shared_key, self, True, is_server=False)
            self.sessionkey = self.auth.get_sessionkey()
            self.bind() # Added because we need the send/recv threads running for authentication
            if (self.auth.mutualauth()):
                print "Server Authenticated!"
                Logger.log("Connected to Server", self.is_server)
                self.authenticated = True
                self.sessionkey = self.auth.get_sessionkey()
                Logger.log(str(self.sessionkey), self.is_server)
                Logger.log(str(sys.getsizeof(str(self.sessionkey))))
                return (0, "Connected to (%s, %i)" % (self.ip_addr, self.port))
            else:
                print "Could not authenticate"
                self.authenticated = False
                self.broken_conn_callback()
                return (-1, "Authentication failed")
        except socket.error:
            return (-1, "Could not connect to (%s, %i)" % (self.ip_addr, self.port))

        return (-1, "Could not connect to (%s, %i)" % (self.ip_addr, self.port))


    def send(self, msg):
        if (self.authenticated):
            emsg = self.auth.encrypt_message(msg, self.sessionkey)
            self.send_queue.put(emsg)
            Logger.log("Put message on send queue: " + msg, self.is_server)
        else:
            self.send_queue.put(msg)
            Logger.log("Put message on send queue: " + msg, self.is_server)

    def bind(self):
        self.sender = Sender(self.socket, self.send_queue, self)
        self.receiver = Receiver(self.socket, self.receive_queue, self)
        self.sender.start()
        self.receiver.start()

    def close(self):
        Logger.log("Connection closing", self.is_server)
        self.send_queue.queue.clear()
        self.receive_queue.queue.clear()
        self.sender.close()
        self.receiver.close()
        self.waiting = True

    def receive(self):
        if (not self.receive_queue.empty()):
            msg = self.receive_queue.get()
            if (self.authenticated):
                msg = self.auth.decrypt_message(msg, self.sessionkey)
                Logger.log("Decrypted msg: "+ msg, self.is_server)
            return msg
        else:
            return None
