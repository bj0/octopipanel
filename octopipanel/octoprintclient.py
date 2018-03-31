from __future__ import print_function

import json

import requests
from kivy.logger import Logger


# todo return auth errors?
class OctoPrintClient(object):
    """
    Client connection to an OctoPrint server.
    """

    def __init__(self, base_url, api_key, fake=False):
        """

        :param base_url: REST URL for octoprint server
        :param api_key: API key for octoprint server
        :param fake: use fake data instead of touching server
        """
        self.fake = fake
        self.base_url = base_url
        self.api_key = api_key

        Logger.info('OctoPrint: using new connection: url={}, key={}'.format(
            base_url, api_key
        ))

        # specific api paths
        self.addkey = '?apikey={0}'.format(self.api_key)
        self.apiurl_printhead = '{0}/api/printer/printhead'.format(
            self.base_url)
        self.apiurl_tool = '{0}/api/printer/tool'.format(self.base_url)
        self.apiurl_bed = '{0}/api/printer/bed'.format(self.base_url)
        self.apiurl_job = '{0}/api/job'.format(self.base_url)
        self.apiurl_status = '{0}/api/printer?apikey={1}'.format(
            self.base_url, self.api_key)
        self.apiurl_connection = '{0}/api/connection'.format(self.base_url)
        self.apiurl_system = '{0}/api/system/commands'.format(self.base_url)

    def get_status(self):
        if not self.fake:
            return _get(self.apiurl_status)
        else:
            return fake_status

    def get_job(self):
        if not self.fake:
            return _get(self.apiurl_job + self.addkey)
        else:
            return fake_job

    def get_connection(self):
        if not self.fake:
            return _get(self.apiurl_connection + self.addkey)
        else:
            return fake_connection

    def send_command(self, url, data):
        headers = {
            'content-type': 'application/json',
            'X-Api-Key': self.api_key}
        data = json.dumps(data)
        print('sending:', headers, data)
        if not self.fake:
            return requests.post(url, data=data, headers=headers)

    def home_x(self):
        self.home_axes('x')

    def home_y(self):
        self.home_axes('y')

    def home_z(self):
        self.home_axes('z')

    def home_axes(self, axes):
        if isinstance(axes, str):
            axes = [axes]

        data = dict(command='home', axes=axes)
        self.send_command(self.apiurl_printhead, data)

    def move_z(self, dist=5):
        data = dict(command='jog', z=dist)
        self.send_command(self.apiurl_printhead, data)

    def move_x(self, dist=10):
        data = dict(command='jog', x=dist)
        self.send_command(self.apiurl_printhead, data)

    def move_y(self, dist=10):
        data = dict(command='jog', y=dist)
        self.send_command(self.apiurl_printhead, data)

    def extrude(self, dist=5):
        data = dict(command='extrude', amount=dist)
        self.send_command(self.apiurl_tool, data)

    def set_bed(self, temp=0):
        data = dict(command='target', target=temp)
        self.send_command(self.apiurl_bed, data)

    def set_hotend(self, temp=0):
        data = dict(command='target', targets=dict(tool0=temp))
        self.send_command(self.apiurl_tool, data)

    def start_print(self):
        # todo: prompt?
        data = dict(command='start')
        self.send_command(self.apiurl_job, data)

    def abort_print(self):
        data = dict(command='cancel')
        self.send_command(self.apiurl_job, data)

    def pause_print(self):
        data = dict(command='pause')
        self.send_command(self.apiurl_job, data)

    def shutdown(self):
        self.send_command(self.apiurl_system + '/core/shutdown', None)

    def restart(self):
        self.send_command(self.apiurl_system + '/core/restart', None)

    def reboot(self):
        self.send_command(self.apiurl_system + '/core/reboot', None)


def _get(url):
    try:
        req = requests.get(url)
        if req.status_code == 200:
            return req.text
        else:
            Logger.warn('OctoPrint: got response: {}'.format(req.status_code))
    except requests.exceptions.ConnectionError as e:
        Logger.error('OctoPrint: Connection Error ({}): {}'.format(e.errno, e.strerror))

    return None


fake_status = '''{
  "temps": {
    "bed": {
      "actual": 69.8,
      "target": 70.0,
      "offset": 0
    },
    "tool0": {
      "actual": 190.4,
      "target": 190.0,
      "offset": 0
    }
  },
  "state": {
    "text": "Operational",
    "flags": {
      "operational": true,
      "paused": false,
      "printing": true,
      "sdReady": true,
      "error": false,
      "ready": true,
      "closedOrError": false
    }
  }
}'''

fake_job = '''{
  "progress": {
    "completion": 13.193011455652211,
    "printTime": 6485,
    "filepos": 2481573,
    "printTimeLeft": 42672
  },
  "job": {
    "estimatedPrintTime": 51526.62242401473,
    "filament": {
      "tool0": {
        "volume": 117.33561505345112,
        "length": 48782.480030000464
      }
    },
    "file": {
      "origin": "local",
      "date": 1426041569,
      "name": "NESTED_BIRD_HOUSE.gcode",
      "size": 18809754
    }
  },
  "state": "Printing"
}'''

fake_connection = '''{
  "current": {
    "baudrate": 115200,
    "state": "Printing",
    "port": "/dev/ttyACM0"
  },
  "options": {
    "portPreference": null,
    "autoconnect": false,
    "baudrates": [
      250000,
      230400,
      115200,
      57600,
      38400,
      19200,
      9600
    ],
    "ports": [
      "/dev/ttyACM0",
      "/dev/ttyAMA0"
    ],
    "baudratePreference": null
  }
}'''

if __name__ == '__main__':
    from octopipanel import OctoPiPanelApp

    from kivy.config import ConfigParser

    app = OctoPiPanelApp()
    path = app.get_application_config()

    print('config path: ', path)
    config = ConfigParser('pre-load')
    config.read(path)
    api_key = config.get('server', 'api-key')
    url = config.getdefault('server', 'url', 'http://octopi.local')
    print('using url:', url)
    print('using api-key:', api_key)

    c = OctoPrintClient(url, api_key)
    print('stat:', c.get_status())
    print('con:', c.get_connection())
    print('job:', c.get_job())
