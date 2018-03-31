from collections import deque

from kivy.clock import Clock
from kivy.garden.graph import Graph, MeshLinePlot
from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivy.uix.screenmanager import Screen
from kivy.utils import get_color_from_hex as rgb

from octopipanel.printerstate import PrinterState


class StatusScreen(Screen):
    interval = NumericProperty(1)

    paused = BooleanProperty(False)
    printing = BooleanProperty(False)
    hotend_temp = NumericProperty(0.0)
    hotend_temp_target = NumericProperty(0.0)
    bed_temp = NumericProperty(0.0)
    bed_temp_target = NumericProperty(0.0)
    hot_hotend = BooleanProperty(False)
    hot_bed = BooleanProperty(False)
    z_height = NumericProperty(0.0)
    status = StringProperty()

    def __init__(self, **kwargs):
        super(StatusScreen, self).__init__(**kwargs)

        self.hotend_temps = deque([0] * 100)
        self.bed_temps = deque([0] * 100)
        self.octoprint = None

    def init(self, octoprint):
        self.octoprint = octoprint
        # use kivy garden's graph widget
        graph = Graph(xlabel='', ylabel='°C', x_ticks_minor=5, x_ticks_major=25,
                      y_ticks_minor=0, y_ticks_major=50, y_grid_label=True,
                      x_grid_label=False, padding=5, y_grid=True,
                      xmax=len(self.hotend_temps), ymax=230,
                      _with_stencilbuffer=False,  # or it does not work in ScreenManager
                      label_options={'color': rgb('000000')})
        self.hotend_plot = MeshLinePlot(color=[1, 0, 0, 1])
        self.bed_plot = MeshLinePlot(color=[0, 0, 1, 1])
        graph.add_plot(self.hotend_plot)
        graph.add_plot(self.bed_plot)

        self.ids.plot.add_widget(graph)
        self.graph = graph
        self.update_plot()

        self.status = "Ready."

    def on_enter(self, *args):
        if self.octoprint is not None:
            self.update()
        Clock.schedule_interval(self.update, self.interval)

    def on_leave(self, *args):
        Clock.unschedule(self.update)

    def update(self, *_):
        status = self.octoprint.get_status()

        if status:
            state = PrinterState.parse(status=status)

            self.paused = state.paused
            self.printing = state.printing

            # Set status flags
            if state.has_temp:
                self.hotend_temp = state.hotend_temp
                self.bed_temp = state.bed_temp
                self.hotend_temp_target = state.hotend_temp_target
                self.bed_temp_target = state.bed_temp_target

                if self.hotend_temp_target > 0.0:
                    self.hot_hotend = True
                else:
                    self.hot_hotend = False

                if self.bed_temp_target > 0.0:
                    self.hot_bed = True
                else:
                    self.hot_bed = False

                # Save temperatures to lists
                self.hotend_temps.popleft()
                self.hotend_temps.append(self.hotend_temp)
                self.bed_temps.popleft()
                self.bed_temps.append(self.bed_temp)

                self.update_plot()

    def update_plot(self):
        x = range(len(self.hotend_temps))
        self.hotend_plot.points = zip(x, self.hotend_temps)
        self.bed_plot.points = zip(x, self.bed_temps)

        # adjust plot bounds
        self.graph.ymin = min(
            0, min(min(self.hotend_temps), min(self.bed_temps)) - 10)
        self.graph.ymax = max(
            100, max(max(self.hotend_temps), max(self.bed_temps)) + 10)
