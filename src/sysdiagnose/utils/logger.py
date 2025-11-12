import logging
from pythonjsonlogger import json
from datetime import datetime

logger = logging.getLogger('sysdiagnose')
# By default, we want to have the possibility to log everything.
logger.setLevel(logging.DEBUG)


class SysdiagnoseJsonFormatter(json.JsonFormatter):
    '''Custom JSON logger formatter '''
    # https://stackoverflow.com/questions/50873446/python-logger-output-dates-in-is8601-format
    def formatTime(self, record, datefmt=None):
        return datetime.fromtimestamp(record.created).astimezone().isoformat(timespec='microseconds')


def set_console_logging(level: str) -> None:
    '''
    Sets a logging stream handler.

    Args:
        level: Logging level. https://docs.python.org/3/library/logging.html#logging-levels
    '''
    # Format
    fmt_console = logging.Formatter('[%(levelname)s] [%(module)s] %(message)s')
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(fmt_console)

    logger.addHandler(ch)


def set_json_logging(filename: str, level: int = logging.DEBUG) -> None:
    '''
    Creates or updates a logging JSON format file handler.

    Args:
        filename: Filename where to log.
        level: Logging level. By default to DEBUG. https://docs.python.org/3/library/logging.html#logging-levels
    '''
    updated = False
    for h in logger.handlers:
        # https://stackoverflow.com/questions/13839554/how-to-change-filehandle-with-python-logging-on-the-fly-with-different-classes-a
        if isinstance(h, logging.FileHandler):
            h.close()
            h.setStream(open(filename, 'w'))
            updated = True

    if not updated:
        fmt_json = SysdiagnoseJsonFormatter(
            fmt='%(created)f %(asctime)s %(levelname)s %(module)s %(message)s',
            rename_fields={'asctime': 'datetime', 'created': 'timestamp'})
        # File handler
        fh = logging.FileHandler(filename=filename, mode='w')
        fh.setLevel(level)
        fh.setFormatter(fmt_json)

        logger.addHandler(fh)
