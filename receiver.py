import socket
import threading
import errno
import struct
from logger import Logger


class Receiver(threading.Thread):

    def __init__(self, socket, queue, conn):
        threading.Thread.__init__(self)
        self.socket = socket
        self.queue = queue
        self.conn = conn
        self.keep_alive = True

    def run(self):
        self.socket.setblocking(0)
        size_data = ''
        size_total = None
        payload = ''
        leftover = ''
        while (self.keep_alive):
            try:
                msg = self.socket.recv(8192)
                if len(msg) == 0:
                    raise socket.error(errno.ENOTCONN)
                msg = leftover + msg
                leftover = ''
                if not size_total:
                    remaining = 4 - len(size_data)
                    if len(msg) >= remaining:
                        size_data += msg[:remaining]
                        size_total = struct.unpack('>I', size_data)[0]
                        msg = msg[remaining:]
                    else:
                        size_data += msg
                if size_total:
                    remaining = size_total - len(payload)
                    if len(msg) >= remaining:
                        payload += msg[:remaining]
                        leftover += msg[remaining:]
                        self.queue.put(payload)
                        size_data = ''
                        size_total = None
                        payload = ''
                    else:
                        payload += msg
            except socket.error as e:
                err = e.args[0]
                if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                    continue
                else:
                    self.conn.broken_conn_callback()
        self.socket.close()

    def close(self):
        self.keep_alive = False


class MessageReceiver(threading.Thread):

    def __init__(self, name, conn, chat_panel):
        threading.Thread.__init__(self)
        self.name = name
        self.conn = conn
        self.queue = self.conn.receive_queue
        self.chat_panel = chat_panel
        self.keep_alive = True

    def run(self):
        while self.keep_alive:
            msg = self.conn.receive()
            if msg:
                self.chat_panel.write_message(self.name, msg)

    def close(self):
        self.keep_alive = False
