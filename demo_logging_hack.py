import logging
import stackprinter

def patch_logging(**kwargs):
    """
    Replace `formatException` on every log handler / formatter we can find

    **kwargs are those of stackprinter.format

    """
    # this is based on https://github.com/Qix-/better-exceptions/blob/master/better_exceptions/log.py

    def format_exc(exc_info):
        msg = stackprinter.format(exc_info, **kwargs)
        msg_indented = '    ' + '\n    '.join(msg.split('\n')).strip()
        return msg_indented

    if hasattr(logging, '_defaultFormatter'):
        logging._defaultFormatter.formatException = format_exc

    handlers = [handler_ref() for handler_ref in logging._handlerList]

    is_patchable = lambda handler: handler.formatter is not None

    patchable_handlers = filter(is_patchable, handlers)

    for hd in patchable_handlers:
        hd.formatter.formatException = format_exc

# option A: use the root loger:
logger = logging.getLogger()

# # option B: use a custom one:
# logging.basicConfig()
# logger = logging.getLogger('some logger')

patch_logging(style='darkbg')

#### test:

def dangerous_function(blub):
    return sorted(blub, key=sum)

try:
    somelist = [[1,2], [3,4]]
    anotherlist = [['5', 6]]
    dangerous_function(somelist + anotherlist)
except:
    logger.exception('the front fell off.')
