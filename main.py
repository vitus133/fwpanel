from kivy.app import App
from kivy.clock import Clock
import datetime
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from router import Router
from kivy.logger import Logger
from multiprocessing import Process, Queue


def send_router_command(router, command_seq):
    router.do_seq(command_seq)




class FwPanelLayout(BoxLayout):
    time_prop = ObjectProperty(None)


class FwPanelApp(App):
    def build_config(self, config):
        config.setdefaults('ROUTER', {
            'ip': '192.168.132.1',
            'key_file': 'id_rsa',
            'user': 'admin'
        })


    def update_time(self, nap):
        now = datetime.datetime.now()
        self.root.time_prop.text = now.strftime('[b]%H[/b]:%M:%S')
        if not q.empty():
            resp = q.get()
            self.parsers[resp['command']](resp)


    def on_start(self):
        self.parsers = {
            'connect': self.connect_rsp,
            'disconnect': self.disconnect_rsp,
            'drop_kids_packets': self.drop_kids_packets_rsp,
            'drop_tv_packets': self.drop_tv_packets_rsp,
            'allow_kids_packets': self.allow_kids_packets_rsp,
            'allow_tv_packets': self.allow_tv_packets_rsp,
            'show_firewall': self.show_firewall_rsp
        }
        Logger.setLevel('INFO')
        Logger.info('Kivy App: Starting')
        self.update_time(0)
        Clock.schedule_interval(self.update_time, 0.2)
        self.root.ids.connect.state = 'down'
        self.connect()
        self.router = Router(self.config['ROUTER'], q)
        command_sequence = ('connect', 'show_firewall', 'disconnect')
        p = Process(target=send_router_command, args=(self.router, command_sequence,))
        p.start()


    def connect_rsp(self, resp):
        Logger.info(f'Kivy App: Connect response: {resp}')
        if 'Success' == resp['status']:
            self.root.ids.connect.text = 'In progress, please wait...'
        else:
            self.root.ids.connect.text = 'Failed to connect, {msg}'.format(msg=resp['message'])

    def disconnect_rsp(self, resp):
        Logger.info(f'Kivy App: Disconnect response: {resp}')
        self.root.ids.sw1.disabled = False
        self.root.ids.sw2.disabled = False
        if 'Success' != resp['status']:
           self.root.ids.connect.text = 'Failure during disconnect, {msg}'.format(msg=resp['message'])

    def drop_kids_packets_rsp(self, resp):
        if 'Success' == resp['status']:
            self.root.ids.connect.text = 'KIds internet off'

    def drop_tv_packets_rsp(self, resp):
        if 'Success' == resp['status']:
            self.root.ids.connect.text = 'TV internet off'


    def allow_kids_packets_rsp(self, resp):
        if 'Success' == resp['status']:
            self.root.ids.connect.text = 'KIds internet on'


    def allow_tv_packets_rsp(self, resp):
        if 'Success' == resp['status']:
            self.root.ids.connect.text = 'TV internet on'


    def show_firewall_rsp(self, resp):
        Logger.info(f'Kivy App: Show firewall response: {resp}')
        if 'Success' == resp['status']:
            self.filter_state = {}
            self.filter_state['kids'] = resp['message']['kids'] == 'enabled'
            self.filter_state['tv'] = resp['message']['tv'] == 'enabled'

            self.root.ids.sw1.active = self.filter_state['kids']
            self.root.ids.sw2.active =self.filter_state['tv']
            self.root.ids.connect.text = "Ready"


    def connect(self):
        state = self.root.ids.connect.state
        if state is 'down':
            self.root.ids.connect.text = 'Connecting...'
            self.root.ids.connect.disabled = True
        else:
            if state is 'normal':
                self.root.ids.connect.text = 'Connect'

    def toggle_kids(self):
        Logger.info('Kivy App: Toggle kids, stored {stored}, switch {switch}'.format(
            stored=self.filter_state['kids'],
            switch=self.root.ids.sw1.active
        ))
        if self.filter_state['kids'] != self.root.ids.sw1.active:
            self.root.ids.sw1.disabled = True
            self.root.ids.sw2.disabled = True
            if  self.root.ids.sw1.active == False:
                Logger.info(f'Kivy App: Disabling kids Internet')
                command_sequence = ('connect', 'drop_kids_packets', 'disconnect')
                self.filter_state['kids'] = False
                p = Process(target=send_router_command, args=(self.router, command_sequence,))
                p.start()
            else:
                Logger.info(f'Kivy App: Enabling kids Internet')
                command_sequence = ('connect', 'allow_kids_packets', 'disconnect')
                self.filter_state['kids'] = True
                p = Process(target=send_router_command, args=(self.router, command_sequence,))
                p.start()



    def toggle_tv(self):
        Logger.info('Kivy App: Toggle TV, stored {stored}, switch {switch}'.format(
            stored=self.filter_state['tv'],
            switch=self.root.ids.sw2.active
        ))
        if self.filter_state['tv'] != self.root.ids.sw2.active:
            self.root.ids.sw1.disabled = True
            self.root.ids.sw2.disabled = True
            if  self.root.ids.sw2.active == False:
                Logger.info(f'Kivy App: Disabling TV Internet')
                self.filter_state['tv'] = False
                p = Process(target=send_router_command, args=(self.router, ('connect', 'drop_tv_packets', 'disconnect'),))
                p.start()
            else:
                Logger.info(f'Kivy App: Enabling TV Internet')
                self.filter_state['tv'] = True
                p = Process(target=send_router_command, args=(self.router, ('connect', 'allow_tv_packets', 'disconnect'),))
                p.start()



if __name__ == '__main__':
    from kivy.core.text import LabelBase
    from kivy.core.window import Window
    from kivy.utils import get_color_from_hex

    Window.clearcolor = get_color_from_hex('#101216')
    LabelBase.register(name='Roboto',
                       fn_regular='Roboto-Thin.ttf',
                       fn_bold='Roboto-Medium.ttf')
    q = Queue()
    FwPanelApp().run()
