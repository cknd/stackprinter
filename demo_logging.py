"""
Custom exception formatter example
based on https://docs.python.org/3/howto/logging-cookbook.html#customized-exception-formatting

The goal is to add detailed traces to standard `logging` calls, e.g.

    try:
        something()
    except:
        logger.exception('The front fell off.')

"""

import logging


# =================== Setup ======================= #
import stackprinter

class VerboseExceptionFormatter(logging.Formatter):
    def formatException(self, exc_info):
        msg = stackprinter.format(exc_info)
        msg_indented = '    ' + '\n    '.join(msg.split('\n')).strip()
        return msg_indented

def configure_logger(logger_name=None):
    fmt = '%(asctime)s %(levelname)s: %(message)s'
    formatter = VerboseExceptionFormatter(fmt)

    # handler = logging.FileHandler('log.txt')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(logger_name)
    logger.addHandler(handler)


logger_name = "somelogger" # or leave None to just use the root logger
configure_logger(logger_name)


# =================== Test ======================= #

logger = logging.getLogger(logger_name)

def dangerous_function(blub):
    return sorted(blub, key=lambda xs: sum(xs))

try:
    somelist = [[1,2], [3,4]]
    anotherlist = [['5', 6]]
    dangerous_function(somelist + anotherlist)
except:
    logger.exception('My hovercraft is full of eels.')
    # Or equivalently:
    # logger.error('My hovercraft is full of eels.', exc_info=True)


