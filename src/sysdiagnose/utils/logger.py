import logging
import logging.handlers
from pythonjsonlogger import jsonlogger
from datetime import datetime

# 3MB max
MAX_BYTES = 3*1024*1024
MAX_LOGFILES = 1

logger = logging.getLogger('sysdiagnose')
# By default, we want to have the possibility to log everything.
logger.setLevel(logging.DEBUG)


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


def get_json_handler(filename: str, level: int = logging.DEBUG) -> logging.FileHandler:
    '''
    Creates a logging JSON format file handler.

    Args:
        filename: Filename where to log.
        level: Logging level. By default to DEBUG. https://docs.python.org/3/library/logging.html#logging-levels
    '''
    fmt_json = SysdiagnoseJsonFormatter(
        fmt='%(created)f %(asctime)s %(levelname)s %(module)s %(message)s',
        rename_fields={'asctime': 'datetime', 'created': 'timestamp'})
    # File handler
    fh = logging.handlers.RotatingFileHandler(filename=filename, maxBytes=MAX_BYTES, backupCount=MAX_LOGFILES)
    fh.setLevel(level)
    fh.setFormatter(fmt_json)

    return fh
