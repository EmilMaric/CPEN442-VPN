import socket
import threading

from Queue import Queue
from auth import Authentication

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
            auth = Authentication(self.shared_key, self)
            self.bind()
            if (auth.mutualauth("client")):
                authenticated = True
                return (0, "Connected to (%s, %i)" % (self.ip_addr, self.port))
        except socket.error:
            return (-1, "Could not connect to (%s, %i)" % (self.ip_addr, self.port))

        return (-1, "Could not connect to (%s, %i)" % (self.ip_addr, self.port))


    def send(self, msg):
        self.send_queue.put(msg)

    def bind(self, sender_print_callback=None, receiver_print_callback=None):
        self.sender = Sender(self.socket, self.send_queue, print_callback=sender_print_callback)
        self.receiver = Receiver(self.socket, self.receive_queue, print_callback=receiver_print_callback)
        self.sender.start()
        self.receiver.start()

    def close(self):
        self.socket.close()

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


class Sender(threading.Thread):

    def __init__(self, socket, queue, print_callback=None):
        threading.Thread.__init__(self)
        self.socket = socket
        self.keep_alive = True
        self.queue = queue
        self.print_callback = print_callback

    def run(self):
        while (self.keep_alive):
            if not self.queue.empty():
                msg = self.queue.get()
                self.socket.send(msg)
                if self.print_callback is not None:
                    self.print_callback(msg)
        self.socket.close()

    def close(self):
        self.keep_alive = False


class Receiver(threading.Thread):

    def __init__(self, socket, queue, print_callback=None):
        threading.Thread.__init__(self)
        self.socket = socket
        self.print_callback = print_callback
        self.queue = queue
        self.keep_alive = True

    def run(self):
        while (self.keep_alive):
            msg = self.socket.recv(1024)
            if (msg):
                self.queue.put(msg)
                self.print_callback(msg)
        self.socket.close()

    def close(self):
        self.keep_alive = False
