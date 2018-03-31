import os

from kivy import resources
from kivy.config import Config

import octopipanel.config as cfg
from octopipanel import utils
from .oppapp import OctoPiPanelApp


def main():
    if cfg.PITFT and utils.rpi_version() is None:
        print('not on RPi')
        cfg.PITFT = False

    # set window size
    Config.set('graphics', 'width', cfg.window_width)
    Config.set('graphics', 'height', cfg.window_height)

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

    # run app
    OctoPiPanelApp().run()
