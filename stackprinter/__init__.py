import sys
import types
import warnings
from threading import Thread
from functools import wraps

import stackprinter.formatting as fmt
from stackprinter.tracing import TracePrinter, trace


def _guess_thing(f):
    """ default to the current exception or current stack frame"""

    # the only reason this happens up here is to keep sys._getframe at the same
    # call depth relative to an invocation of `show` or `format`, even when
    # `format` is called _by_ `show`.
    @wraps(f)
    def show_or_format(thing=None, *args, **kwargs):
        if thing is None:
            thing = sys.exc_info()
            if thing == (None, None, None):
                thing = sys._getframe(1)
        return f(thing, *args, **kwargs)
    return show_or_format


@_guess_thing
def format(thing=None, **kwargs):
    """
    Render a call stack or the traceback of an exception.


    Call this with no argument inside an `except` block to get a traceback for
    the currently handled exception:
        ```
        try:
            something()
        except:
            traceback_message = stackprinter.format(**kwargs)
        ```

    Explicitely pass an exception (or a triple as returned by `sys.exc_info()`)
    to handle that particular exception anywhere, also outside an except block.
        ```
        try:
            something()
        except Exception as e:
            last_exc = e

        if last_exc:
            traceback_message = stackprinter.format(last_exc, **kwargs)
        ```

    Pass a frame object to see the call stack leading up to that frame:
        ```
        stack = stackprinter.format(sys._getframe(0), **kwargs))
        ```

    Two other ways to see the current call stack:
        ```
        # this works anywhere outside exception handling blocks:
        stack = stackprinter.format(**kwargs)

        # (this works anywhere:)
        stack = stackprinter.format_current_stack(**kwargs)
        ```

    Pass a thread object to see its current call stack:
        ```
        thread = threading.Thread(target=something)
        thread.start()
        while True:
            msg = stackprinter.format(thread, **kwargs))
            print(msg)
            time.sleep(0.1)
        ```

    Note:
    This displays variable values as they are _at the time of formatting_. In
    multi-threaded programs, variables can change while we're busy walking
    the stack & printing them. So, if nothing seems to make sense, consider that
    your exception and the traceback messages are from slightly different times.
    Sadly, there is no responsible way to freeze all other threads as soon
    as we want to inspect some thread's call stack (...or is there?)


    Params
    ---
    thing: (optional) exception, sys.exc_info() tuple, frame or thread object
        What to format. Defaults to the currently handled exception or current
        stack frame.

    style: string 'color' or 'plaintext' (default: 'plaintext')
        'color': Insert ANSI colored semantic highlights, for use in terminals
                 that support 256 colors (or with something like the `ansi2html`
                 package, to create colorful log files). There is only one color
                 scheme and it assumes a dark background.
        'plaintext': Just text.

    source_lines: int or 'all'. (default: 5 lines)
        Select how much source code context will be shown.
        int 0: Don't include a source listing.
        int n > 0: Show n lines of code.
        string 'all': Show the whole scope of the frame.

    show_signature: bool (default True)
        Always include the function header in the source code listing.

    show_vals: str or None (default 'like_source')
        Select which variable values will be shown.
        'line': Show only the variables on the highlighted line.
        'like_source': Show those visible in the source listing (default).
        'all': Show every variable in the scope of the frame.
        None: Don't show any variable values.

    truncate_vals: int (default 500)
        Maximum number of characters to be used for each variable value

    suppressed_paths: list of regex patterns
        Set less verbose formatting for frames whose code lives in certain paths
        (e.g. library code). Files whose path matches any of the given regex
        patterns will be considered boring. The first call to boring code is
        rendered with fewer code lines (but with argument values still visible),
        while deeper calls within boring code get a single line and no variable
        values.

        Example: To hide numpy internals from the traceback, set
        `suppressed_paths=[r"lib/python.*/site-packages/numpy"]`

    reverse: bool (default False)
        List the innermost frame first

    add_summary: bool (default: True)
        Append a short list of all involved paths and source lines, similar
        to the built-in traceback message.

    """
    if isinstance(thing, types.FrameType):
        return fmt.format_stack_from_frame(thing, **kwargs)
    elif isinstance(thing, Thread):
        return format_thread(thing, **kwargs)
    elif isinstance(thing, Exception):
        exc_info = (thing.__class__, thing, thing.__traceback__)
        return format(exc_info, **kwargs)
    elif _is_exc_info(thing):
        return fmt.format_exc_info(*thing, **kwargs)
    else:
        raise ValueError("Can't format %s. "\
                         "Expected an exception instance, sys.exc_info() tuple,"\
                         "a frame or a thread object." % repr(thing))


@_guess_thing
def show(thing=None, file=sys.stderr, **kwargs):
    """
    Print a stack trace or the traceback message for an exception.

    See `format` for full docs. This function is identical to `format` except
    that it directly prints the result to `file`, defaulting to sys.stderr
    """
    print(format(thing, **kwargs), file=file)



def format_current_stack(**kwargs):
    """ Render the current thread's call stack. Arguments like format() """
    return format(sys._getframe(1), **kwargs)

def show_current_stack(**kwargs):
    """ Print the current thread's call stack. Arguments like show() """
    show(sys._getframe(1), **kwargs)




def format_current_exception(**kwargs):
    """
    Render a traceback for the currently handled exception.

    kwargs like format()
    """
    return format(sys.exc_info(), **kwargs)

def show_current_exception(file=sys.stderr, **kwargs):
    """
    Print a traceback for the currently handled exception.

    kwargs like show()
    """
    print(format_current_exception(**kwargs), file=file)



def set_excepthook(**kwargs):
    """
    Set sys.excepthook to print a detailed traceback for any uncaught exception.

    This doesn't work in IPython, since Ipython handles exceptions internally
    i.e. the interpreter never sees an uncaught exception (and Ipython resets
    the excepthook for its own purposes, anyway).

    kwargs like show()
    """
    if _is_running_in_ipython():
        warnings.warn("Excepthooks have no effect when running under Ipython - "
                      "capture exceptions manually to print tracebacks for them.",
                      stacklevel=2)
        return
    else:
        def hook(*args):
            show(args, **kwargs)

        sys.excepthook = hook

def remove_exceptook():
    """ Reinstate the default excepthook """
    sys.excepthook = sys.__excepthook__



def format_thread(thread, add_summary=False, **kwargs):
    try:
        fr = sys._current_frames()[thread.ident]
    except KeyError:
        return "%r: no frames found" % thread
    else:
        if 'suppressed_paths' not in kwargs:
            kwargs['suppressed_paths'] = []
        kwargs['suppressed_paths'] += [r"lib/python.*/threading\.py"]

        msg = fmt.format_stack_from_frame(fr, **kwargs)
        msg_indented = '    ' + '\n    '.join(msg.split('\n')).strip()
        return "%r\n\n%s" % (thread, msg_indented)


def _is_exc_info(thing):
    if not isinstance(thing, tuple) or len(thing) != 3:
        return False
    a, b, c = thing
    return (isinstance(a, type) and BaseException in a.mro() and
            isinstance(b, BaseException) and
            isinstance(c, types.TracebackType))


def _is_running_in_ipython():
    fr = sys._getframe(1)
    while fr.f_back:
        if fr.f_code.co_name == 'start_ipython':
            return True
        fr = fr.f_back
    return False

