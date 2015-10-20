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

from server import VpnServer
from client import VpnClient
from receiver import MessageReceiver


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

    def write_message(self, name, message):
        time = datetime.datetime.now().time().strftime('%H:%M')
        header = "(%s) [%s]     " %(time, name)
        self.write(header + message)


class VpnApp(App):

    def __init__(self, **kwargs):
        super(VpnApp, self).__init__(**kwargs)
        self.client = None
        self.server = None
        self.message_receiver = None

    def client_connected_callback(self, ip_addr, port):
        self.enable_disable_widgets(
            chat_input = True,
            send_button = True
        )
        sender = "SERVER"
        conn = self.client
        chat_panel = self.chat_panel
        if self.servermode.state == "down":
            self.chat_panel.write_info("Client connected from (%s, %i)" % (ip_addr, port))
            sender = "CLIENT"
            conn = self.server
        self.message_receiver = MessageReceiver(sender, conn, chat_panel)
        self.message_receiver.start()

    # specify which widgets to enable. All unspecified widgets will get disabled
    def enable_disable_widgets(
            self, 
            clientmode=None, 
            servermode=None, 
            ip_address=None,
            port=None,
            shared_value=None,
            connect=None,
            disconnect=None,
            chat_panel=None,
            chat_input=None,
            send_button=None,
    ):

        def enable_widget(enable, widget):
            if enable is None:
                return
            if enable:
                widget.disabled = False
            else:
                widget.disabled = True

        enable_widget(clientmode, self.clientmode)
        enable_widget(servermode, self.servermode)
        enable_widget(ip_address, self.ip_address)
        enable_widget(port, self.port)
        enable_widget(shared_value, self.shared_value)
        enable_widget(connect, self.connect)
        enable_widget(disconnect, self.disconnect)
        enable_widget(chat_panel, self.chat_panel)
        enable_widget(chat_input, self.chat_input)
        enable_widget(send_button, self.send_button)


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
                    self.chat_panel.write_info("Invalid port: " + child.text)
                    return

        # get the shared key value
        shared_key = ""
        for child in self.shared_value.children:
            if isinstance(child, TextInput):
                shared_key = str(child.text)
                if not shared_key:
                    self.chat_panel.write_info("Shared key must have some value")
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
            self.server = VpnServer(
                    port, 
                    shared_key,
                    self.client_connected_callback,
                    self.broken_conn_callback,
            )
            error, message = self.server.setup()
            if (error != 0):
                # error while setting up socket
                self.chat_panel.write_info(message)
                return
            else:
                self.chat_panel.write_info(message)
                self.enable_disable_widgets(
                    clientmode=False,
                    servermode=False,
                    port=False,
                    shared_value=False,
                    connect=False,
                    disconnect=True,
                    chat_input=False,
                    send_button=False,
                )
                self.server.start(callback=self.client_connected_callback)
        else:
            # vpn is in 'client' mode 
            self.client = VpnClient(
                    ip_address, 
                    port, 
                    shared_key,
                    self.broken_conn_callback,
            )
            error, message = self.client.connect()
            if (error != 0):
                self.chat_panel.write_info(message)
                return
            else:
                self.chat_panel.write_info(message)
                self.enable_disable_widgets(
                    clientmode=False,
                    servermode=False,
                    ip_address=False,
                    port=False,
                    shared_value=False,
                    connect=False,
                    disconnect=True,
                    chat_input=False,
                    send_button=False,
                )
                self.client_connected_callback(ip_address, port)
        
    def disconnect_callback(self, instance):
        if self.servermode.state == 'down':
            self.server.close()
            self.chat_panel.write_info("Closing Server...")
        else:
            self.client.close()
            self.chat_panel.write_info("Disconnecting from server...")
        if self.message_receiver:
            self.message_receiver.close()
        self.clientmode.disabled=False
        self.servermode.disabled=False
        self.ip_address.disabled=False
        self.port.disabled=False
        self.shared_value.disabled=False
        self.connect.disabled=False
        self.disconnect.disabled=True
        self.chat_input.disabled=True
        self.send_button.disabled=True

    def send_msg(self, btn):
        msg = self.chat_input.text
        if self.servermode.state == 'down':
            self.chat_panel.write_server(msg)
            self.server.send(msg)
        else:
            self.chat_panel.write_client(msg)
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
        self.chat_input.disabled=True
        self.send_button.disabled=True
        return self.root

    def broken_conn_callback(self):
        if self.message_receiver:
            self.message_receiver.close()
        if self.server:
            self.server.send_queue.queue.clear()
            self.server.receive_queue.queue.clear()
            self.server.sender.close()
            self.server.receiver.close()
            self.server.waiting = True
            self.server.start(callback=self.client_connected_callback)
            self.chat_panel.write_info("Client disconnected")
            self.chat_panel.write_info("Listening for connections...")
            self.enable_disable_widgets(
                chat_input=False,
                send_button=False,
            )
        else:
            self.client.send_queue.queue.clear()
            self.client.receive_queue.queue.clear()
            self.client.sender.close()
            self.client.receiver.close()
            self.client.waiting = True
            self.enable_disable_widgets(
                clientmode=True,
                servermode=True,
                ip_address=True,
                port=True,
                shared_value=True,
                connect=True,
                disconnect=False,
                chat_input=False,
                send_button=False,
            )
            self.chat_panel.write_info("Lost connection to server")
        

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


if __name__ == "__main__":
    app = VpnApp()
    app.run()
    app.close()
