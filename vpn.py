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

import TCPconnection

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


class VpnApp(App):
    
    def connect_fnc(self, btn):
        #if self.TCPconn != None:
        if self.servermode.state == 'down':
            self.TCPconn = TCPconnection.TCPconnection(True, '', int(self.port_textinput.text))
        else:
            self.TCPconn = TCPconnection.TCPconnection(False, self.ip_textinput.text, int(self.port_textinput.text))
        addr = self.TCPconn.connect()
        if (addr):
            if self.clientmode.state == 'down':
                self.chat_panel.text += "Connected to "+self.ip_textinput.text+" at port "+self.port_textinput.text+"\n"
            else:
                self.chat_panel.text += "Connected to client "+str(addr)+"\n"
        else:
            self.chat_panel.text+="Failed to connect. Please check your parameters and try again \n"

    
    def SettingsEntry(self,text=None):
        boxlayout = BoxLayout(orientation="vertical", padding=30)
        self.label = Label(text=text, size=(300, 50),size_hint=(1, None))
        boxlayout.add_widget(self.label)
        self.textinput = TextInput(multiline=False, size=(300, 50), size_hint=(1, None))
        boxlayout.add_widget(self.textinput)
        return boxlayout

    def build(self):
        root = BoxLayout(orientation="horizontal",
                         spacing=10,
                         padding=10)

        # create settings panel
        settings_panel = ColoredBoxLayout(orientation="vertical",
                                        background_color=(0,169,184,0.5),
                                        size_hint=(0.3, 1),
                                        padding=10)
        root.add_widget(settings_panel)

        self.clientmode = ToggleButton(text='Client', group='mode', state='down')
        self.servermode = ToggleButton(text='Server', group='mode')
        settings_panel.add_widget(self.clientmode)
        settings_panel.add_widget(self.servermode)

        '''ip_address = self.SettingsEntry(text="VPN Server IP Address")
        settings_panel.add_widget(ip_address)'''
        ip_address = BoxLayout(orientation="vertical", padding=30)
        self.ip_label = Label(text="VPN Server IP Address", size=(300, 50),size_hint=(1, None))
        ip_address.add_widget(self.ip_label)
        self.ip_textinput = TextInput(multiline=False, size=(300, 50), size_hint=(1, None))
        ip_address.add_widget(self.ip_textinput)
        settings_panel.add_widget(ip_address)

        '''port = self.SettingsEntry(text="VPN Server Port")
        settings_panel.add_widget(port)'''
        port = BoxLayout(orientation="vertical", padding=30)
        self.port_label = Label(text="VPN Server Port", size=(300, 50),size_hint=(1, None))
        port.add_widget(self.port_label)
        self.port_textinput = TextInput(multiline=False, size=(300, 50), size_hint=(1, None))
        port.add_widget(self.port_textinput)
        settings_panel.add_widget(port)
        

        shared_secret_value = self.SettingsEntry(text="Shared Secret Value")
        settings_panel.add_widget(shared_secret_value)

        connect = Button(text="Connect", color=(0,1,0))
        connect.bind(on_press=self.connect_fnc)
        disconnect = Button(text="Disconnect", color=(1,0,0))
        '''disconnect.bind(on_press=self.disconnect_fnc)'''
        settings_panel.add_widget(connect)
        settings_panel.add_widget(disconnect)

        empty_widget = Widget()
        settings_panel.add_widget(empty_widget)

        # create chat panel
        self.chat_layout = BoxLayout(orientation="vertical",
                                spacing=10,
                                size_hint=(0.7, 1))
        self.chat_panel = TextInput(readonly=True,
                               disabled=True)
        self.input_layout = BoxLayout(orientation="horizontal",
                                 spacing=10,
                                 size=(0, 50),
                                 size_hint=(1, None))
        self.chat_input = TextInput(size_hint=(0.8, 1))
        '''self.chat_input.bind(on_text_validate=self.send_msg)'''
        self.input_button = Button(size_hint=(0.2, 1),
                              text="Send")
        '''self.input_button.bind(on_press=self.send_msg)'''
        self.input_layout.add_widget(self.chat_input)
        self.input_layout.add_widget(self.input_button)
        self.chat_layout.add_widget(self.chat_panel)
        self.chat_layout.add_widget(self.input_layout)
        root.add_widget(self.chat_layout)
        return root

if __name__ == "__main__":
    VpnApp().run()
