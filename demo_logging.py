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
        lines = msg.split('\n')
        lines_indented = ["  ┆ " + line + "\n" for line in lines]
        msg_indented = "".join(lines_indented)
        return msg_indented

def configure_logger(logger_name=None):
    fmt = '%(asctime)s %(levelname)s: %(message)s'
    formatter = VerboseExceptionFormatter(fmt)


    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    # # Add more, like
    # handler = logging.FileHandler('log.txt')
    # ...

    logger = logging.getLogger(logger_name)
    logger.addHandler(handler)


configure_logger("some_logger")


# =================== Use ======================= #
print("\n\n")
logger = logging.getLogger("some_logger")

def dangerous_function(something):
    return something + 1

try:
    nothing = {}
    dangerous_function(nothing.get("something"))
except:
    logger.exception('My hovercraft is full of eels.')
    # Or equivalently:
    # logger.error('My hovercraft is full of eels.', exc_info=True)


