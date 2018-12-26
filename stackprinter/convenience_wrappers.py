import sys
import types
from threading import Thread

import stackprinter.formatting as fmt
import stackprinter.extraction as ex

def show(thing=None, stream=None, **kwargs):
    """
    TODO doctsring with all kwargs

    """
    if thing is None:
        thing = sys._getframe(1)
    print(format(thing, **kwargs), file=stream)


def format(thing=None, **kwargs):
    """
    TODO doctsring with all kwargs

    """
    if thing is None:
        thing = sys._getframe(1)

    if isinstance(thing, types.FrameType):
        return format_stack_from_frame(thing, **kwargs)
    elif isinstance(thing, Thread):
        return format_thread(thing, **kwargs)
    elif isinstance(thing, Exception):
        return format_exception(thing, **kwargs)
    elif _is_exc_info(thing):
        return fmt.format_exc_info(*thing, **kwargs)
    else:
        raise ValueError("Can't format %s. "\
                         "Expected an exception, sys.exc_info() tuple"\
                         " or thread object." % repr(thing))


def format_exception(exc, **kwargs):
    etype = exc.__class__
    tb = exc.__traceback__
    fmt.format_exc_info(etype, exc, tb, **kwargs)


def format_thread(thread, **kwargs):
    try:
        fr = sys._current_frames()[thread.ident]
    except KeyError:
        msg = "%r: no active frames found" % thread

    if 'suppressed_paths' not in kwargs:
        kwargs['suppressed_paths'] = []
    kwargs['suppressed_paths'] += [r"lib/python.*/threading\.py"]

    msg = "%r\n\n" % thread
    msg += _add_indent(format_stack_from_frame(fr, **kwargs))
    return msg


def format_stack_from_frame(fr, **kwargs):
    stack = []
    while fr.f_back is not None:
        stack.append(ex.get_info(fr))
        fr = fr.f_back

    stack = reversed(stack)

    return fmt.format_stack(stack, **kwargs)





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
            isinstance(b, BaseException) and
            isinstance(c, types.TracebackType))


def _add_indent(string):
    return '    ' + '\n    '.join(string.split('\n')).strip()