import socket
import threading
import errno
import struct


class Receiver(threading.Thread):

    def __init__(self, socket, queue):
        threading.Thread.__init__(self)
        self.socket = socket
        self.queue = queue
        self.keep_alive = True

    def run(self):
        size_data = ''
        size_total = None
        payload = ''
        leftover = ''
        while (self.keep_alive):
            try:
                msg = self.socket.recv(8192)
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
                    self.keep_alive=False

        self.socket.close()

    def close(self):
        self.keep_alive = False

