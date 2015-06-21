# coding=utf-8
from __future__ import absolute_import
import kivy
kivy.require('1.8.0')
from kivy.config import Config

from ConfigParser import RawConfigParser

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.garden.graph import Graph, MeshLinePlot
from kivy.utils import get_color_from_hex as rgb
from kivy import resources

import requests
import json
import platform

from collections import deque
import os

from octoprintclient import OctoPrintClient

read_only = True
DEBUG = False
HW = (not DEBUG) and False
isLinux = platform.system() == 'Linux'

# this is needed so kv files can find images
resources.resource_add_path(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'res'
    ))
# and this one is for loading kv files
resources.resource_add_path(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'kv'
    ))


def enable_backlight():
    if not HW or not isLinux:
        print 'enable backlight'
    else:
        os.system("echo '1' > /sys/class/gpio/gpio252/value")
        os.system("echo '90' > /sys/class/rpi-pwm/pwm0/duty")

def disable_backlight():
    if not HW or not isLinux:
        print 'disable backlight'
    else:
        os.system("echo '0' > /sys/class/gpio/gpio252/value")
        os.system("echo '1' > /sys/class/rpi-pwm/pwm0/duty")



class OctoPiPanelApp(App):
    hotend_temp = NumericProperty(0.0)
    hotend_temp_target = NumericProperty(0.0)
    bed_temp = NumericProperty(0.0)
    bed_temp_target = NumericProperty(0.0)
    hot_hotend = BooleanProperty(False)
    hot_bed = BooleanProperty(False)
    paused = BooleanProperty(False)
    printing = BooleanProperty(False)
    job_loaded = BooleanProperty(False)
    job_completion = NumericProperty(0.0, allownone=True)
    z_height = NumericProperty(0.0)
    file_name = StringProperty('Nothing')

    z_move_amount = NumericProperty(1)
    z_moves = [0.1, 1, 5]
    xy_move_amount = NumericProperty(10)
    xy_moves = [1, 10, 100]

    print_time = NumericProperty(0.0, allownone=True)
    print_time_left = NumericProperty(0.0, allownone=True)

    nozzle_status = StringProperty()
    bed_status = StringProperty()
    z_status = StringProperty()
    buf_status = StringProperty()
    mul_status = StringProperty()
    flow_status = StringProperty()
    status = StringProperty()


    def __init__(self, *args, **kwargs):
        from . import config

        win_width = kwargs.get('window_width') or config.window_width
        win_height = kwargs.get('window_height') or config.window_height

        Config.set('graphics', 'width', win_width)
        Config.set('graphics', 'height', win_height)

        self.updatetime = kwargs.get('update_time') or config.update_time
        self.backlightofftime = kwargs.get('backlight_timeout') or config.backlight_timeout

        self.octoprint = OctoPrintClient(
            kwargs.get('base_url') or config.base_url,
            kwargs.get('api_key') or config.api_key,
            DEBUG )

        self.hotend_temps = deque([0]*100)
        self.bed_temps = deque([0]*100)

        super(OctoPiPanelApp, self).__init__(*args, **kwargs)

    def update(self, dt):
#        print 'up',dt,Clock.get_time()
        self.get_state()

        # Is it time to turn of the backlight?
        if self.backlightofftime > 0 and isLinux:
            if Clock.get_time() - self.bglight_ticks > self.backlightofftime:
                # disable the backlight
                disable_backlight()

                self.bglight_ticks = Clock.get_time()
                self.bglight_on = False

    def get_state(self):
        try:
            req = self.octoprint.get_status()
#            print 'stat:',req

            if req:
                state = json.loads(req)

                # Set status flags
                temp_key = 'temps' if 'temps' in state else 'temperature'
                tempstate = state.get(temp_key, None)
                if 'temps' in tempstate:
                    tempstate = tempstate.get('temps', None)

                if tempstate:
                    self.hotend_temp = (tempstate
                                        .get('tool0', state)
                                        .get('actual', 0.0))
                    self.bed_temp = (tempstate
                                        .get('bed', state)
                                        .get('actual', 0.0))
                    self.hotend_temp_target = (tempstate
                                        .get('tool0', state)
                                        .get('target', 0.0))
                    self.bed_temp_target = (tempstate
                                        .get('bed', state)
                                        .get('target', 0.0))


                    if self.hotend_temp_target > 0.0:
                        self.hot_hotend = True
                    else:
                        self.hot_hotend = False

                    if self.bed_temp_target > 0.0:
                        self.hot_bed = True
                    else:
                        self.hot_bed = False


            # Get info about current job
            req = self.octoprint.get_job()
#            print 'job:',req

            if req:
                jobState = json.loads(req)

            req = self.octoprint.get_connection()
#            print 'conn:',req

            if req:
                connState = json.loads(req)

                #print self.apiurl_job + self.addkey

                self.job_completion = jobState['progress']['completion'] # In procent
                self.print_time = jobState['progress']['printTime']
                self.print_time_left = jobState['progress']['printTimeLeft']
                #self.Height = state['currentZ']
                self.file_name = jobState['job']['file']['name']
                self.job_loaded = connState['current']['state'] == "Operational" \
                    and (jobState['job']['file']['name'] != "") \
                    or (jobState['job']['file']['name'] != None)

                # Save temperatures to lists
                self.hotend_temps.popleft()
                self.hotend_temps.append(self.hotend_temp)
                self.bed_temps.popleft()
                self.bed_temps.append(self.bed_temp)

                self.update_plot()

                print self.hotend_temp
                #print self.BedTempList

                self.paused = state['state']['flags']['paused']
                self.printing = state['state']['flags']['printing']


        except requests.exceptions.ConnectionError as e:
            print "Connection Error ({0}): {1}".format(e.errno, e.strerror)


    def stop(self):
        Clock.unschedule(self.update)

        """ Clean up """
        # enable the backlight before quiting
        enable_backlight()

        # OctoPiPanel is going down.
        print "OctoPiPanel is going down."

        super(OctoPiPanelApp, self).stop()

    def build(self):

        # window title
        self.title = 'OctoPi Panel'

        # todo: font

        # backlight
        self.bglight_ticks = Clock.get_time()
        self.bglight_on = True

        # I couldnt seem to get at pin 252 for the backlight using the usual method,
        # but this seems to work
        if HW and isLinux:
            os.system("echo 252 > /sys/class/gpio/export")
            os.system("echo 'out' > /sys/class/gpio/gpio252/direction")
            os.system("echo '1' > /sys/class/gpio/gpio252/value")
            os.system("echo pwm > /sys/class/rpi-pwm/pwm0/mode")
            os.system("echo '1000' > /sys/class/rpi-pwm/pwm0/frequency")
            os.system("echo '90' > /sys/class/rpi-pwm/pwm0/duty")

        print 'OctoPiPanel initiated'

        # start updates
        Clock.schedule_interval(self.update, self.updatetime)

        self.status = "Ready."
        for file in ['statusscreen.kv','controlscreen.kv','systemscreen.kv',
                        'printscreen.kv','octopipanel.kv']:
            # path = os.path.dirname(os.path.realpath(__file__))
            # root = Builder.load_file(os.path.join(path,'kv',file))
            root = Builder.load_file(file)

        # use kivy garden's graph widget
        graph = Graph(xlabel='', ylabel='°C', x_ticks_minor=5, x_ticks_major=25,
            y_ticks_minor=0, y_ticks_major=50, y_grid_label=True,
            x_grid_label=False, padding=5, y_grid=True,
            xmax=len(self.hotend_temps), ymax=230,
            label_options={'color': rgb('000000')})
        self.hotend_plot = MeshLinePlot(color=[1,0,0,1])
        self.bed_plot = MeshLinePlot(color=[0,0,1,1])
        graph.add_plot(self.hotend_plot)
        graph.add_plot(self.bed_plot)

        root.ids.stat.ids.plot.add_widget(graph)
        self.graph = graph
        self.update_plot()

        # handle re-enabling backlight on click and refreshing timer
        def do_bglight(*x):
            self.bglight_ticks = Clock.get_time()
            if self.bglight_on:
                BoxLayout.on_touch_down(root, *x)
            else:
                print 'turn back on!'
                enable_backlight()
                self.bglight_on = True

        root.on_touch_down = do_bglight

        return root

    def update_plot(self):
        x = range(len(self.hotend_temps))
        self.hotend_plot.points = zip(x, self.hotend_temps)
        self.bed_plot.points = zip(x, self.bed_temps)
        # adjust plot bounds
        self.graph.ymin = min(0, min(min(self.hotend_temps),min(self.bed_temps))-10)
        self.graph.ymax = max(100, max(max(self.hotend_temps),max(self.bed_temps))+10)


    def reboot(self):
        self.stop()
        if HW and isLinux:
            os.system('reboot')

    def shutdown(self):
        self.stop()
        if HW and isLinux:
            os.system('shutdown -h 0')

    def restart(self):
        #TODO
        print 'todo: restart'


if __name__ == '__main__':
    OctoPiPanelApp().run()
