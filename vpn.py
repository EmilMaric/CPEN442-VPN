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


def SettingsEntry(text=None):
        boxlayout = BoxLayout(orientation="vertical",
                              padding=30)
        label = Label(text=text,
                      size=(300, 50),
                      size_hint=(1, None))
        boxlayout.add_widget(label)
        textinput = TextInput(multiline=False, 
                              size=(300, 50), 
                              size_hint=(1, None))
        boxlayout.add_widget(textinput)
        return boxlayout


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

        client = ToggleButton(text='Client', group='mode', state='down')
        server = ToggleButton(text='Server', group='mode')
        settings_panel.add_widget(client)
        settings_panel.add_widget(server)

        ip_address = SettingsEntry(text="VPN Server IP Address")
        settings_panel.add_widget(ip_address)

        port = SettingsEntry(text="VPN Server Port")
        settings_panel.add_widget(port)

        shared_secret_value = SettingsEntry(text="Shared Secret Value")
        settings_panel.add_widget(shared_secret_value)

        connect = Button(text="Connect", color=(0,1,0))
        disconnect = Button(text="Disconnect", color=(1,0,0))
        settings_panel.add_widget(connect)
        settings_panel.add_widget(disconnect)

        empty_widget = Widget()
        settings_panel.add_widget(empty_widget)

        # create chat panel
        chat_layout = BoxLayout(orientation="vertical",
                                spacing=10,
                                size_hint=(0.7, 1))
        chat_panel = TextInput(readonly=True, 
                               disabled=True)
        input_layout = BoxLayout(orientation="horizontal",
                                 spacing=10,
                                 size=(0, 50),
                                 size_hint=(1, None))
        chat_input = TextInput(size_hint=(0.8, 1))
        input_button = Button(size_hint=(0.2, 1),
                              text="Send")
        input_layout.add_widget(chat_input)
        input_layout.add_widget(input_button)
        chat_layout.add_widget(chat_panel)
        chat_layout.add_widget(input_layout)
        root.add_widget(chat_layout)
        return root

if __name__ == "__main__":
    VpnApp().run()
