import os

class PiTFT:
    def __init__(self, fake=False):
        self.fake = fake

    def init(self):
        if fake:
            print ('init')
        else:
            os.system("echo 252 > /sys/class/gpio/export")
            os.system("echo 'out' > /sys/class/gpio/gpio252/direction")
            os.system("echo '1' > /sys/class/gpio/gpio252/value")
            os.system("echo pwm > /sys/class/rpi-pwm/pwm0/mode")
            os.system("echo '1000' > /sys/class/rpi-pwm/pwm0/frequency")
            os.system("echo '90' > /sys/class/rpi-pwm/pwm0/duty")

    def enable_backlight(self):
        if self.fake:
            print('enable backlight')
        else:
            os.system("echo '1' > /sys/class/gpio/gpio252/value")
            os.system("echo '90' > /sys/class/rpi-pwm/pwm0/duty")

    def disable_backlight(self):
        if self.fake:
            print('disable backlight')
        else:
            os.system("echo '0' > /sys/class/gpio/gpio252/value")
            os.system("echo '1' > /sys/class/rpi-pwm/pwm0/duty")
