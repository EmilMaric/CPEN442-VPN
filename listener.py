import socket
import threading

from auth import Authentication


class Listener(threading.Thread):
    server_str = "SERVER" #TODO find better place for this

    def __init__(self, socket, shared_key, server, connected_callback):
        threading.Thread.__init__(self)
        self.keep_alive = True
        self.socket = socket
        self.shared_key = shared_key
        self.server = server
        self.connected_callback = connected_callback

    def run(self):
        self.socket.setblocking(0)
        authenticated = False

        while (self.keep_alive and authenticated == False):
            try:
                client_socket, addr = self.socket.accept()
                self.server.waiting = False
                auth = Authentication(self.shared_key, self.server, debug=True, is_server=True)
                self.server.bind(client_socket) 
                if (auth.mutualauth()):
                    print "Client Authenticated!"
                    authenticated = True
                    self.connected_callback(addr[0], addr[1])
                else:
                    print "Unable to authenticate"
                    self.server.broken_conn_callback()
            except socket.error:
                pass
        if not self.keep_alive:
            self.socket.close()

    def close(self):
        self.keep_alive = False
