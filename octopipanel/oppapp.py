# coding=utf-8
from __future__ import absolute_import
from __future__ import print_function

from kivy import resources
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.properties import ConfigParserProperty

import octopipanel.config as cfg
from .octoprintclient import OctoPrintClient
from .pitft import PiTFT


class OctoPiPanelApp(App):
    backlight_timeout = ConfigParserProperty(0, 'pitft', 'backlight_timeout', 'app', val_type=int)

    def __init__(self, **kwargs):
        super(OctoPiPanelApp, self).__init__(**kwargs)

        self.interval = 1

        # backlight
        self.backlight_idle = Clock.get_boottime()
        self.backlight_on = True

        self.octoprint = None

        self.pitft = PiTFT(fake=not cfg.PITFT)

        # settings are in app path
        resources.resource_add_path(self.directory)

    def update(self, _):
        # Is it time to turn of the backlight?
        if self.backlight_timeout > 0:
            if (Clock.get_boottime() - self.backlight_idle > self.backlight_timeout
                    and self.backlight_on):
                # disable the backlight
                self.pitft.disable_backlight()

                self.backlight_idle = Clock.get_boottime()
                self.backlight_on = False

    def stop(self):
        Clock.unschedule(self.update)

        """ Clean up """
        # enable the backlight before quiting
        self.pitft.enable_backlight()

        # OctoPiPanel is going down.
        Logger.info("OctoPiPanel is going down.")

        super(OctoPiPanelApp, self).stop()

    def on_config_change(self, config, section, key, value):
        if section == 'server':
            self.octoprint = OctoPrintClient(
                self.config.get('server', 'url'),
                self.config.get('server', 'api-key'),
                cfg.FAKE)

    def build_config(self, config):
        config.setdefaults('pitft', {
            'backlight_timeout': 30,
        })
        config.setdefaults('server', {
            'url': 'http://octopi.local',
            'api-key': '<api key here>',
            'job_interval': 5,
            'status_interval': 2
        })

    def build_settings(self, settings):
        settings.add_json_panel('OPP', self.config, resources.resource_find('app_settings.json'))

    def build(self):
        """
        Kivy App entry point.
        :return:
        """

        # window title
        self.title = 'OctoPi Panel'

        # todo: font

        self.octoprint = OctoPrintClient(
            self.config.get('server', 'url'),
            self.config.get('server', 'api-key'),
            cfg.FAKE)

        # I couldnt seem to get at pin 252 for the backlight using the usual method,
        # but this seems to work
        self.pitft.init()

        root = Builder.load_file('octopipanel.kv')

        root.ids.print.init(self.octoprint)
        root.ids.status.init(self.octoprint)

        Logger.info('OctoPiPanel initiated')

        # start updates
        Clock.schedule_interval(self.update, self.interval)

        # handle re-enabling backlight on click and refreshing timer
        def wakeup(*_):
            self.backlight_idle = Clock.get_boottime()
            if not self.backlight_on:
                print('turn back on!')
                self.pitft.enable_backlight()
                self.backlight_on = True

        root.bind(on_touch_down=wakeup)

        return root

    def reboot(self):
        self.stop()
        if not cfg.FAKE:
            self.octoprint.reboot()
            # os.system('reboot')

    def shutdown(self):
        self.stop()
        if not cfg.FAKE:
            self.octoprint.shutdown()
            # os.system('shutdown -h 0')

    def restart(self):
        if not cfg.FAKE:
            self.octoprint.restart()
