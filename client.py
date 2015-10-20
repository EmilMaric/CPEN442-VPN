import socket
import threading

from Queue import Queue
from auth import Authentication
from sender import Sender
from receiver import Receiver


class VpnClient(object):

    def __init__(self, ip_addr, port, shared_key, broken_conn_callback):
        self.ip_addr = ip_addr
        self.port = port
        self.shared_key = shared_key
        self.broken_conn_callback = broken_conn_callback
        self.send_queue = Queue()
        self.receive_queue = Queue()
        self.waiting = True

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
            auth = Authentication(self.shared_key, self, True, is_server=False)
            self.bind() # Added because we need the send/recv threads running for authentication
            if (auth.mutualauth()):
                print "Server Authenticated!"
                authenticated = True
                return (0, "Connected to (%s, %i)" % (self.ip_addr, self.port))
            else:
                print "Could not authenticate"
                authenticated = False
                self.broken_conn_callback()
                return (-1, "Authentication failed")
        except socket.error:
            return (-1, "Could not connect to (%s, %i)" % (self.ip_addr, self.port))

        return (-1, "Could not connect to (%s, %i)" % (self.ip_addr, self.port))


    def send(self, msg):
        self.send_queue.put(msg)

    def bind(self):
        self.sender = Sender(self.socket, self.send_queue, self)
        self.receiver = Receiver(self.socket, self.receive_queue, self)
        self.sender.start()
        self.receiver.start()

    def close(self):
        self.sender.close()
        self.receiver.close()

    def receive(self):
        if (not self.receive_queue.empty()):
            return self.receive_queue.get()
        else:
            return None
