import sys
import types
from threading import Thread

import stackprinter.formatting as fmt


def show(thing, stream=None, **kwargs):
    """
    TODO doctsring with all kwargs

    """
    print(format(thing, **kwargs), stream=stream)


def format(thing, **kwargs):
    """
    TODO doctsring with all kwargs

    """
    if isinstance(thing, Thread):
        return format_thread(thing, **kwargs)
    elif isinstance(thing, Exception):
        return format_exception(thing, **kwargs)
    elif _is_exc_info(thing):
        return fmt.format_exc_info(*thing, **kwargs)
    else:
        raise ValueError("Can't format `%r`. "\
                         "Expected an exception instance, sys.exc_info() tuple"\
                         " or thread object." % thing)


def format_exception(exc, **kwargs):
    etype = exc.__class__
    tb = exc.__traceback__
    fmt.format_exc_info(etype, exc, tb, **kwargs)

def format_thread(thread, **kwargs):
    try:
        fr = sys._current_frames()[thread.ident]
    except KeyError:
        msg = "%r: no active frames found" % thread

    stack = [fr]
    while fr.f_back is not None:
        fr = fr.f_back
        stack.append(fr)

    stack = reversed(stack)

    msg = "%r\n\n" % thread

    msg += _add_indent(fmt.format_stack(stack, **kwargs))

    return msg




# def set_excepthook(**kwargs):

#     def excepthook(etype, evalue, tb, file=sys.stderr, **kwargs):
#         message = format(etype, evalue, tb, **kwargs)
#         print(message, file=file)

#     sys.excepthook = excepthook

# def reset_exceptook():
#     sys.excepthook = sys.__excepthook__


def _is_exc_info(thing):
    if not isinstance(thing, tuple) or len(thing) != 3:
        return False

    a, b, c = thing

    return (isinstance(a, type) and BaseException in a.mro() and
            isinstance(b, Exception) and
            isinstance(c, types.TracebackType))


def _add_indent(string):
    return '    ' + '\n    '.join(string.split('\n')).strip()
