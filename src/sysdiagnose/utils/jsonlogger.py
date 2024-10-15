from pythonjsonlogger import jsonlogger
from datetime import datetime


class SysdiagnoseJsonFormatter(jsonlogger.JsonFormatter):
    '''Custom JSON logger formatter '''
    # https://stackoverflow.com/questions/50873446/python-logger-output-dates-in-is8601-format
    def formatTime(self, record, datefmt=None):
        return datetime.fromtimestamp(record.created).astimezone().isoformat(timespec='microseconds')
