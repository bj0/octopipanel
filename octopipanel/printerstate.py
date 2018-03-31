import json

import attr


@attr.s(slots=True)
class PrinterState(object):
    paused = attr.ib(False)
    printing = attr.ib(False)

    has_temp = attr.ib(False)
    hotend_temp = attr.ib(0.0)
    bed_temp = attr.ib(0.0)
    hotend_temp_target = attr.ib(0.0)
    bed_temp_target = attr.ib(0.0)

    completion = attr.ib(0.0)
    print_time = attr.ib(0.0)
    print_time_left = attr.ib(0.0)
    file_name = attr.ib(None)
    job_loaded = attr.ib(False)

    @classmethod
    def parse(cls, status=None, job=None, connection=None):
        val = cls()
        if status:
            status = json.loads(status)

            val.paused = status['state']['flags']['paused']
            val.printing = status['state']['flags']['printing']

            # Set status flags
            temp_key = 'temps' if 'temps' in status else 'temperature'
            temp_state = status.get(temp_key, None)
            if 'temps' in temp_state:
                temp_state = temp_state.get('temps', None)

            if temp_state:
                val.has_temp = True
                val.hotend_temp = (temp_state
                                   .get('tool0', status)
                                   .get('actual', 0.0))
                val.bed_temp = (temp_state
                                .get('bed', status)
                                .get('actual', 0.0))
                val.hotend_temp_target = (temp_state
                                          .get('tool0', status)
                                          .get('target', 0.0))
                val.bed_temp_target = (temp_state
                                       .get('bed', status)
                                       .get('target', 0.0))

        if job:
            job = json.loads(job)

            val.completion = job[
                'progress']['completion']  # In procent
            val.print_time = job['progress']['printTime']
            val.print_time_left = job['progress']['printTimeLeft']
            # val.Height = state['currentZ']
            val.file_name = job['job']['file']['name']

        if connection and job:
            connection = json.loads(connection)
            val.job_loaded = (connection['current']['state'] == "Operational"
                              and (job['job']['file']['name'] != "")
                              or (job['job']['file']['name'] is not None))

        return val
