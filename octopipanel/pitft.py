import os

from kivy.logger import Logger


class PiTFT:
    """
    A class for controlling the Adafruit PiTFT
    """

    def __init__(self, fake=False):
        self.fake = fake

    def init(self):
        if self.fake:
            Logger.info('PITFT: init')
        else:
            os.system("echo 252 > /sys/class/gpio/export")
            os.system("echo 'out' > /sys/class/gpio/gpio252/direction")
            os.system("echo '1' > /sys/class/gpio/gpio252/value")
            os.system("echo pwm > /sys/class/rpi-pwm/pwm0/mode")
            os.system("echo '1000' > /sys/class/rpi-pwm/pwm0/frequency")
            os.system("echo '90' > /sys/class/rpi-pwm/pwm0/duty")

    def enable_backlight(self):
        """
        Enables the PiTFT backlight
        """
        if self.fake:
            Logger.info('PITFT: enable backlight')
        else:
            os.system("echo '1' > /sys/class/gpio/gpio252/value")
            os.system("echo '90' > /sys/class/rpi-pwm/pwm0/duty")

    def disable_backlight(self):
        """
        Disables the PiTFT backlight
        """
        if self.fake:
            Logger.info('PITFT: disable backlight')
        else:
            os.system("echo '0' > /sys/class/gpio/gpio252/value")
            os.system("echo '1' > /sys/class/rpi-pwm/pwm0/duty")
