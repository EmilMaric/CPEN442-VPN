import socket
import threading

from Queue import Queue
from auth import Authentication

class VpnServer(object):

    def __init__(self, port, shared_key):
        self.port = port
        self.send_queue = Queue()
        self.receive_queue = Queue()
        self.authenticated = False
        self.shared_key = shared_key

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
        self.listener = Listener(self.socket, callback, self.shared_key)
        self.listener.start()

    def bind(self, client_socket, sender_print_callback=None, receiver_print_callback=None):
        self.sender = Sender(client_socket, self.send_queue, print_callback=sender_print_callback)
        self.receiver = Receiver(client_socket, self.receive_queue, print_callback=receiver_print_callback)
        self.sender.start()
        self.receiver.start()

    def close(self):
        self.listener.close()

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


class Listener(threading.Thread):

    def __init__(self, socket, callback, shared_key):
        threading.Thread.__init__(self)
        self.socket = socket
        self.keep_alive = True
        self.callback=callback
        self.shared_key = shared_key

    def run(self):
        self.socket.setblocking(0)
        authenticated = False

        while (self.keep_alive and authenticated == False):
            try:
                client_socket, addr = self.socket.accept()

                auth = Authentication(self.shared_key, client_socket)
                if (auth.mutualauth("server")):
                    authenticated = True
                else:
                    print "unable to authenticate"
            except socket.error:
                print "socket errror....."
                pass
        if not self.keep_alive:
            self.socket.close()
        if self.callback:
            self.callback(client_socket, addr[0], addr[1]) # addr[0] = ip, addr[1] = port

    def close(self):
        self.keep_alive = False


class Sender(threading.Thread):

    def __init__(self, socket, queue, print_callback=None):
        threading.Thread.__init__(self)
        self.socket = socket
        self.keep_alive = True
        self.print_callback = print_callback
        self.queue = queue

    def run(self):
        while (self.keep_alive):
            if not self.queue.empty():
                msg = self.queue.get()
                self.socket.send(msg)
                self.print_callback(msg)
        self.socket.close()

    def close(self):
        self.keep_alive = False


class Receiver(threading.Thread):

    def __init__(self, socket, queue, print_callback=None):
        threading.Thread.__init__(self)
        self.socket = socket
        self.socket.setblocking(1)
        self.print_callback = print_callback
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
