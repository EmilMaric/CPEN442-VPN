import socket
import threading

from Queue import Queue
from auth import Authentication
from sender import Sender
from receiver import Receiver


class VpnClient(object):

    def __init__(self, ip_addr, port, shared_key):
        self.ip_addr = ip_addr
        self.port = port
        self.send_queue = Queue()
        self.receive_queue = Queue()
        self.shared_key = shared_key

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except socket.error:
            return (-1, "Could not create socket")

        try:
            self.socket.connect((self.ip_addr, self.port))
            auth = Authentication(self.shared_key, self, True, is_server=False)
            self.bind() # Added because we need the send/recv threads running for authentication
            if (auth.mutualauth()):
                print "Server Authenticated!"
                authenticated = True
                return (0, "Connected to (%s, %i)" % (self.ip_addr, self.port))
        except socket.error:
            return (-1, "Could not connect to (%s, %i)" % (self.ip_addr, self.port))

        return (-1, "Could not connect to (%s, %i)" % (self.ip_addr, self.port))


    def send(self, msg):
        self.send_queue.put(msg)

    def bind(self):
        self.sender = Sender(self.socket, self.send_queue)
        self.receiver = Receiver(self.socket, self.receive_queue)
        self.sender.start()
        self.receiver.start()

    def close(self):
        self.socket.close()

    def receive(self):
        if (not self.receive_queue.empty()):
            return self.receive_queue.get()
        else:
            return None
