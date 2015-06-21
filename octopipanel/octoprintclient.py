import requests
import json


class OctoPrintClient(object):
    def __init__(self, base_url, api_key, debug=False):
        self.debug = debug        
        self.base_url = base_url
        self.api_key = api_key
        
        self.addkey = '?apikey={0}'.format(self.api_key)
        self.apiurl_printhead = '{0}/api/printer/printhead'.format(
            self.base_url)
        self.apiurl_tool = '{0}/api/printer/tool'.format(self.base_url)
        self.apiurl_bed = '{0}/api/printer/bed'.format(self.base_url)
        self.apiurl_job = '{0}/api/job'.format(self.base_url)
        self.apiurl_status = '{0}/api/printer?apikey={1}'.format(
            self.base_url, self.api_key)
        self.apiurl_connection = '{0}/api/connection'.format(self.base_url)

    def get_status(self):
        if not self.debug:
            req = requests.get(self.apiurl_status)
            return req.text if req.status_code == 200 else None
        else:
            return fake_status

    def get_job(self):
        if not self.debug:
            req = requests.get(self.apiurl_job+self.addkey)
            return req.text if req.status_code == 200 else None
        else:
            return fake_job

    def get_connection(self):
        if not self.debug:
            req = requests.get(self.apiurl_connection+self.addkey)
            return req.text if req.status_code == 200 else None
        else:
            return fake_connection
            
    def send_command(self, url, data):
        headers = { 'content-type': 'application/json', 'X-Api-Key': self.api_key }
        data = json.dumps(data)
        print 'sending:',headers, data
        if not self.debug:
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
    c = OctoPrintClient('http://localhost:5000', '65AA3D33EBFE404184DE8A0695A9E312')
    print 'stat:',c.get_status()
    print 'con:',c.get_connection()
    print 'job:',c.get_job()
