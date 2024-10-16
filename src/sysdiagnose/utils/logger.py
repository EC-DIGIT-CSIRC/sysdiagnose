import logging
from pythonjsonlogger import jsonlogger
from datetime import datetime

logger = logging.getLogger('sysdiagnose')
# By default, we want to have the possibility to log almost everything.
logger.setLevel(logging.INFO)

class SysdiagnoseJsonFormatter(jsonlogger.JsonFormatter):
    '''Custom JSON logger formatter '''
    # https://stackoverflow.com/questions/50873446/python-logger-output-dates-in-is8601-format
    def formatTime(self, record, datefmt=None):
        return datetime.fromtimestamp(record.created).astimezone().isoformat(timespec='microseconds')


def get_console_handler(level: str) -> logging.StreamHandler:
    '''
    Creates a logging stream handler.

    Args:
        level: Logging level. https://docs.python.org/3/library/logging.html#logging-levels
    '''
    # Format
    fmt_console = logging.Formatter('[%(levelname)s] [%(module)s] %(message)s')
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(fmt_console)

    return ch

def get_json_handler(filename: str, level: int = logging.INFO) -> logging.FileHandler:
    '''
    Creates a logging JSON format file handler.

    Args:
        filename: Filename where to log.
        level: Logging level. By default to INFO. https://docs.python.org/3/library/logging.html#logging-levels
    '''
    fmt_json = SysdiagnoseJsonFormatter(
        fmt='%(asctime)s %(levelname)s %(module)s %(message)s',
        rename_fields={'asctime': 'timestamp'})
    # File handler
    fh = logging.FileHandler(filename)
    fh.setLevel(level)
    fh.setFormatter(fmt_json)

    return fh
