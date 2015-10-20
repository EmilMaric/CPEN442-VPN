import socket
import threading
import struct
from logger import Logger

class Sender(threading.Thread):

    def __init__(self, socket, queue, conn):
        threading.Thread.__init__(self)
        self.socket = socket
        self.queue = queue
        self.conn = conn
        self.keep_alive = True

    def run(self):
        self.socket.setblocking(0)
        while (self.keep_alive):
            if not self.queue.empty():
                msg = self.queue.get()
                msg = struct.pack('>I', len(msg)) + msg
                try:
                    self.socket.sendall(msg)
                    Logger.log("Sending message over socket: "+ msg, self.conn.is_server)
                except socket.error:
                    self.conn.broken_conn_callback()
        self.socket.close()

    def close(self):
        self.keep_alive = False
