import socket
import threading

from auth import Authentication


class Listener(threading.Thread):
    server_str = "SERVER" #TODO find better place for this

    def __init__(self, socket, shared_key, server, connected_callback, app):
        threading.Thread.__init__(self)
        self.keep_alive = True
        self.socket = socket
        self.shared_key = shared_key
        self.server = server
        self.connected_callback = connected_callback
        self.app = app
        self.auth = None

    def run(self):
        self.socket.setblocking(0)
        self.server.authenticated = False

        while (self.keep_alive and self.server.authenticated == False):
            try:
                client_socket, addr = self.socket.accept()
                self.server.waiting = False
                self.auth = Authentication(self.shared_key, self.server, self.app, debug=True, is_server=True)
                self.server.bind(client_socket) 
                self.app.debug_continue.disabled = False
                if (self.auth.mutualauth()):
                    print "Client Authenticated!"
                    self.server.authenticated = True
                    self.server.auth = self.auth
                    self.connected_callback(addr[0], addr[1])
                    self.server.clear_queues()
                else:
                    print "Unable to authenticate"
                    self.server.authenticated=False
                    self.auth=False
                    self.server.broken_conn_callback()
        
            except socket.error:
                pass
        if not self.keep_alive:
            self.socket.close()

    def broken_conn(self):
        self.authenticated = False
        self.auth=None

        if self.server is not None:
            self.server.auth = None

    def close(self):
        self.keep_alive = False
        self.server.authenticated = False
        self.auth=None

        if self.server is not None:
            self.server.auth = None
