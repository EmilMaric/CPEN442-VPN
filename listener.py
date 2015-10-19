import socket
import threading

from auth import Authentication


class Listener(threading.Thread):
    server_str = "SERVER" #TODO find better place for this

    def __init__(self, socket, shared_key, server):
        threading.Thread.__init__(self)
        self.keep_alive = True
        self.socket = socket
        self.shared_key = shared_key
        self.server = server

    def run(self):
        self.socket.setblocking(0)
        authenticated = False

        while (self.keep_alive and authenticated == False):
            try:
                client_socket, addr = self.socket.accept()
                auth = Authentication(self.shared_key, self.server, debug=True, is_server=True)
                self.server.bind(client_socket) 
                if (auth.mutualauth()):
                    print "Client Authenticated!"
                    authenticated = True
                else:
                    print "Unable to authenticate"
            except socket.error:
                pass
        if not self.keep_alive:
            self.socket.close()

    def close(self):
        self.keep_alive = False
