from kivy.clock import Clock
from kivy.properties import NumericProperty, StringProperty, BooleanProperty
from kivy.uix.screenmanager import Screen

from octopipanel.printerstate import PrinterState


class PrintScreen(Screen):
    interval = NumericProperty(5)

    job_loaded = BooleanProperty(False)
    job_completion = NumericProperty(0.0, allownone=True)
    print_time = NumericProperty(0.0, allownone=True)
    print_time_left = NumericProperty(0.0, allownone=True)
    file_name = StringProperty('Nothing')

    def __init__(self, **kw):
        super(PrintScreen, self).__init__(**kw)
        self.octoprint = None

    def init(self, octoprint):
        self.octoprint = octoprint

    def on_enter(self, *args):
        if self.octoprint is not None:
            self.update()
        Clock.schedule_interval(self.update, self.interval)

    def on_leave(self, *args):
        Clock.unschedule(self.update)

    def update(self, *_):
        job = self.octoprint.get_job()
        connection = self.octoprint.get_connection()

        if job:
            state = PrinterState.parse(job=job, connection=connection)
            self.job_loaded = state.job_loaded
            self.job_completion = state.completion
            self.print_time = state.print_time
            self.print_time_left = state.print_time_left
            self.file_name = state.file_name

            print('job update: ', state)
