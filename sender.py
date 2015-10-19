import socket
import threading
import struct


class Sender(threading.Thread):

    def __init__(self, socket, queue):
        threading.Thread.__init__(self)
        self.socket = socket
        self.keep_alive = True
        self.queue = queue

    def run(self):
        while (self.keep_alive):
            if not self.queue.empty():
                msg = self.queue.get()
                msg = struct.pack('>I', len(msg)) + msg
                self.socket.sendall(msg)
        self.socket.close()

    def close(self):
        self.keep_alive = False
