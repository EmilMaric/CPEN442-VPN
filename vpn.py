import threading
import ipaddress
import datetime

from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ListProperty
from kivy.graphics import Color, Rectangle
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.button import Button
from kivy.uix.behaviors import ToggleButtonBehavior
from TCPconnection import TCPconnection
from server import VpnServer
from client import VpnClient


class ColoredBoxLayout(BoxLayout):

    def __init__(self, background_color=(160,160,160,0.5), **kwargs):
        super(ColoredBoxLayout, self).__init__(**kwargs)
        self.background_color = background_color
        with self.canvas:
            Color(*background_color)
            self.rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self.update_rect,
                  size=self.update_rect)
    
    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class ClientServerToggle(ToggleButtonBehavior, Button):

    def __init__(self, **kwargs):
        super(ClientServerToggle, self).__init__(**kwargs)


class ChatPanel(TextInput):

    def __init__(self, **kwargs):
        self.lock = threading.Lock()
        super(ChatPanel, self).__init__(**kwargs)

    def write(self, message):
        self.lock.acquire()
        self.text += message + "\n"
        self.lock.release()

    def write_info(self, message):
        time = datetime.datetime.now().time().strftime('%H:%M')
        info_msg = "(%s) [INFO]     " % (time)
        self.write(info_msg + message)

    def write_client(self, message):
        time = datetime.datetime.now().time().strftime('%H:%M')
        client_msg = "(%s) [CLIENT]     " % (time)
        self.write(client_msg + message)

    def write_server(self, message):
        time = datetime.datetime.now().time().strftime('%H:%M')
        server_msg = "(%s) [SERVER]     " % (time)
        self.write(server_msg + message)


class VpnApp(App):

    def __init__(self, **kwargs):
        self.client = None
        self.server = None
        super(VpnApp, self).__init__(**kwargs)

    def client_connected_callback(self, client_socket, ip_addr, port):
        self.chat_panel.write_info("Client connected from (%s, %i)" % (ip_addr, port))
        self.server.bind(client_socket, sender_print_callback=self.chat_panel.write_server, receiver_print_callback=self.chat_panel.write_client)

    # called when 'Client' toggle button is pressed
    def client_callback(self, *args):
        state = args[1]
        if state == "down":
            self.settings_panel.add_widget(self.ip_address, 5)
            self.chat_panel.write_info("Switched to Client Mode")
    
    # called when 'Server' toggle button is pressed
    def server_callback(self, *args):
        state = args[1]
        if state == "down":
            self.settings_panel.remove_widget(self.ip_address)
            self.chat_panel.write_info("Switched to Server Mode")

    # called when 'Connect' button is pressed
    def connect_callback(self, btn):
        self.disconnect.disabled = True

        # get inserted port number
        port = 0

        for child in self.port.children:
            if isinstance(child, TextInput):
                try:
                    port = int(child.text)
                except ValueError:
                    # TODO: print error to chat panel
                    self.chat_panel.write_info("Invalid port: " + child.text)
                    return

        shared_key = 0
        for child in self.shared_value.children:
            if isinstance(child, TextInput):
                try:
                    shared_key = int(child.text)
                except ValueError:
                    # TODO: print error to chat panel
                    self.chat_panel.write_info("Invalid port: " + child.text)
                    return

        # get the inserted ip address
        if (self.clientmode.state == 'down'):
            ip_address = ""
            for child in self.ip_address.children:
                if isinstance(child, TextInput):
                    try:
                        ip_address = child.text
                        ipaddress.ip_address(unicode(child.text, 'utf-8'))
                    except ValueError:
                        #TODO: print error to chat panel
                        self.chat_panel.write_info("Invalid IP Address: " + child.text)
                        return

        if (self.servermode.state == 'down'):
            # vpn is in 'server' mode
            self.server = VpnServer(port, shared_key)
            error, message = self.server.setup()
            #TODO: Write to chat panel
            
            if (error != 0):
                # error while setting up socket
                self.chat_panel.write_info(message)
                return
            else:
                self.clientmode.disabled=True
                self.servermode.disabled=True
                self.port.disabled=True
                self.shared_value.disabled=True
                self.connect.disabled=True
                self.disconnect.disabled=False
                self.chat_panel.write_info(message)
                self.server.start(callback=self.client_connected_callback)
        else:
            # vpn is in 'client' mode 
            self.client = VpnClient(ip_address, port, shared_key)
            error, message = self.client.connect()

            if (error != 0):
                self.chat_panel.write_info(message)
                return
            else:
                self.clientmode.disabled=True
                self.servermode.disabled=True
                self.ip_address.disabled=True
                self.port.disabled=True
                self.shared_value.disabled=True
                self.connect.disabled=True
                self.disconnect.disabled=False
                self.chat_panel.write_info(message)
                self.client.bind(sender_print_callback=self.chat_panel.write_client, receiver_print_callback=self.chat_panel.write_server)
        
    def disconnect_callback(self, instance):
        if self.servermode.state == 'down':
            self.server.close()
            self.chat_panel.write_info("Closing Server...")
        else:
            self.client.close()
            self.chat_panel.write_info("Disconnecting from server...")

        self.clientmode.disabled=False
        self.servermode.disabled=False
        self.ip_address.disabled=False
        self.port.disabled=False
        self.shared_value.disabled=False
        self.connect.disabled=False
        self.disconnect.disabled=True

    def send_msg(self, btn):
        msg = self.chat_input.text
        if self.servermode.state == 'down':
            self.server.send(msg)
        else:
            self.client.send(msg)
        self.chat_input.text = ""
    
    def SettingsEntry(self,text=None):
        boxlayout = BoxLayout(orientation="vertical", padding=30)
        self.label = Label(text=text, size=(300, 50),size_hint=(1, None))
        boxlayout.add_widget(self.label)
        self.textinput = TextInput(multiline=False, size=(300, 50), size_hint=(1, None))
        boxlayout.add_widget(self.textinput)
        return boxlayout

    def build(self):
        # create the root window for the app
        self.root = BoxLayout(
                orientation="horizontal",
                spacing=10,
                padding=10
        )

        # create settings panel
        self.settings_panel = ColoredBoxLayout(
                            orientation="vertical",
                            background_color=(0,169,184,0.5),
                            size_hint=(0.3, 1),
                            padding=10,
        )
        self.root.add_widget(self.settings_panel)

        # client and server toggle buttons
        self.clientmode = ClientServerToggle(
                text='Client', 
                group='mode', 
                state='down',
                allow_no_selection=False,
                size=(300,100),
                size_hint=(1, None)
        )
        self.servermode = ClientServerToggle(
                text='Server', 
                group='mode', 
                allow_no_selection=False,
                size=(300,100),
                size_hint=(1, None)
        )
        self.clientmode.bind(state=self.client_callback)
        self.servermode.bind(state=self.server_callback)
        self.settings_panel.add_widget(self.clientmode)
        self.settings_panel.add_widget(self.servermode)

        # add empty space
        empty_widget = Widget()
        self.settings_panel.add_widget(empty_widget)

        # add ip address input
        self.ip_address = self.SettingsEntry(text="VPN Server IP Address")
        self.settings_panel.add_widget(self.ip_address)

        # add port input
        self.port = self.SettingsEntry(text="VPN Server Port")
        self.settings_panel.add_widget(self.port)
        
        # add shared value 
        self.shared_value = self.SettingsEntry(text="Shared Secret Value")
        self.settings_panel.add_widget(self.shared_value)

        # add empty space
        empty_widget = Widget()
        self.settings_panel.add_widget(empty_widget)

        # add connect and disconnect buttons
        self.connect = Button(
                text="Connect", 
                background_color=(0,1,0,1),
                size=(300, 150),
                size_hint=(1, None)
        )
        self.connect.bind(on_press=self.connect_callback)
        self.disconnect = Button(
                text="Disconnect", 
                background_color=(1,0,0,1),
                size=(300, 150),
                size_hint=(1, None),
                disabled=True,
        )
        self.disconnect.bind(on_press=self.disconnect_callback)
        self.settings_panel.add_widget(self.connect)
        self.settings_panel.add_widget(self.disconnect)

        # create chat panel
        self.chat_layout = BoxLayout(
                orientation="vertical",
                spacing=10,
                size_hint=(0.7, 1)
        )
        self.chat_panel = ChatPanel(
                markup=True,
                readonly=True,
                scroll_y=1,
                focused=True,
                cursor_color=(0,0,0,0),
                bar_color=(1,0,0,1),
        )
        self.input_layout = BoxLayout(
                orientation="horizontal",
                spacing=10,
                size=(0, 50),
                size_hint=(1, None)
        )
        self.chat_input = TextInput(size_hint=(0.8, 1))
        self.send_button = Button(size_hint=(0.2, 1), text="Send")
        self.send_button.bind(on_press=self.send_msg)
        self.input_layout.add_widget(self.chat_input)
        self.input_layout.add_widget(self.send_button)
        self.chat_layout.add_widget(self.chat_panel)
        self.chat_layout.add_widget(self.input_layout)
        self.root.add_widget(self.chat_layout)
        return self.root

    def close(self):
        if self.server:
            self.server.close()
            if self.server.sender:
                self.server.sender.close()
            if self.server.receiver:
                self.server.receiver.close()
        if self.client:
            self.client.close()
            if self.client.sender:
                self.client.sender.close()
            if self.client.receiver:
                self.client.receiver.close()

    class MessageReceiver(threading.Thread):
        def __init__(self, app, connection):
            threading.Thread.__init__(self)
            self.keep_alive = True
            self.conn = connection
            self.app = app

        def run(self):
            while (self.keep_alive and self.app.connection_state):
                msg = None
                msg = self.conn.receive()
                if (msg):
                    self.app.chat_panel.text += "Received: " + msg + "\n"

        def close(self):
            self.keep_alive = False


if __name__ == "__main__":
    app = VpnApp()
    app.run()
    app.close()
