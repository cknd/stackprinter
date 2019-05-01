"""
custom exception formatting without patching stuff

based on https://docs.python.org/3/howto/logging-cookbook.html#customized-exception-formatting
"""
import logging
import stackprinter


class VerboseExceptionFormatter(logging.Formatter):
    def formatException(self, exc_info):
        msg = stackprinter.format(exc_info, style='darkbg')
        msg_indented = '    ' + '\n    '.join(msg.split('\n')).strip()
        return msg_indented

def configure_logging(logger_name=None):
    handler = logging.StreamHandler()  # or e.g. FileHandler('output.txt', 'w')
    formatter = VerboseExceptionFormatter('%(asctime)s %(levelname)s: %(message)s', '%d/%m/%Y %H:%M:%S')
    handler.setFormatter(formatter)

    logger = logging.getLogger(logger_name)
    logger.addHandler(handler)  # masks the default handler (which remains unchanged)
    logger.setLevel(logging.DEBUG)


# option A: use root loger:
loggername = None

# # option B: make custom logger:
# loggername = 'somelogger'  # custom logger

configure_logging(loggername)
logger = logging.getLogger(loggername)

#### test:
def dangerous_function(blub):
    return sorted(blub, key=lambda xs: sum(xs))

try:
    somelist = [[1,2], [3,4]]
    anotherlist = [['5', 6]]
    dangerous_function(somelist + anotherlist)
except:
    logger.exception('the front fell off.')


