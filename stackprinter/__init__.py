import sys
import types
import warnings
from threading import Thread
import stackprinter.formatting as fmt


def show(thing=None, file=sys.stderr, **kwargs):
    """
    TODO doctsring with all kwargs

    """
    print(format(thing, stacklevel=1, **kwargs), file=file)


def format(thing=None, stacklevel=0, **kwargs):
    """
    TODO doctsring with all kwargs

    """
    if thing is None:
        thing = sys.exc_info()
        if thing == (None, None, None):
            warnings.warn("Tried to show the last exception but didn't find any",
                          stacklevel=2 + stacklevel)
            return ''

    if isinstance(thing, types.FrameType):
        return fmt.format_stack_from_frame(thing, **kwargs)
    elif isinstance(thing, Thread):
        return _format_thread(thing, **kwargs)
    elif isinstance(thing, Exception):
        return _format_exception(thing, **kwargs)
    elif _is_exc_info(thing):
        return fmt.format_exc_info(*thing, **kwargs)
    else:
        raise ValueError("Can't format %s. "\
                         "Expected an exception instance, sys.exc_info() tuple,"\
                         "a frame or a thread object." % repr(thing))

def format_stack(**kwargs):
    return format(sys._getframe(1), **kwargs)

def show_stack(**kwargs):
    show(sys._getframe(1), **kwargs)


def _is_exc_info(thing):
    if not isinstance(thing, tuple) or len(thing) != 3:
        return False

    a, b, c = thing

    return (isinstance(a, type) and BaseException in a.mro() and
            isinstance(b, BaseException) and
            isinstance(c, types.TracebackType))


def _format_exception(exc, **kwargs):
    etype = exc.__class__
    tb = exc.__traceback__
    return fmt.format_exc_info(etype, exc, tb, **kwargs)


def _format_thread(thread, **kwargs):
    try:
        fr = sys._current_frames()[thread.ident]
    except KeyError:
        return "%r: no frames found" % thread
    else:
        if 'suppressed_paths' not in kwargs:
            kwargs['suppressed_paths'] = []
        kwargs['suppressed_paths'] += [r"lib/python.*/threading\.py"]

        msg = "%r\n\n" % thread
        msg += _add_indent(fmt.format_stack_from_frame(fr, **kwargs))
        return msg


def _add_indent(string):
    return '    ' + '\n    '.join(string.split('\n')).strip()


def set_excepthook(**kwargs):
    if _is_running_in_ipython():
        warnings.warn("excepthooks have no effect when running in Ipython, "
                      "since it handles all exceptions internally "
                      "(and also overrides any hook we'd set by its own). "
                      "Capture exceptions manually to print tracebacks for them.",
                      stacklevel=2)
        return

    def hook(*args):
        show(args, **kwargs)

    sys.excepthook = hook


def remove_exceptook():
    sys.excepthook = sys.__excepthook__


def _is_running_in_ipython():
    fr = sys._getframe(1)
    while fr.f_back:
        if fr.f_code.co_name == 'start_ipython':
            return True
        fr = fr.f_back
    return False

