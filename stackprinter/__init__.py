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
    r"""
    Render the traceback of an exception or a frame's call stack


    Call this without arguments inside an `except` block to get a traceback for
    the currently handled exception:
        ```
        try:
            something()
        except:
            logger.err(stackprinter.format(**kwargs))
        ```

    Explicitly pass an exception (or a triple as returned by `sys.exc_info()`)
    to handle that particular exception anywhere, also outside an except block.
        ```
        try:
            something()
        except Exception as e:
            last_exc = e

        if last_exc:
            logger.err(stackprinter.format(last_exc, **kwargs))
        ```

    Pass a frame object to see the call stack leading up to that frame:
        ```
        stack = stackprinter.format(sys._getframe(2), **kwargs))
        ```

    Pass a thread object to see its current call stack:
        ```
        thread = threading.Thread(target=something)
        thread.start()
        # (...)
        stack = stackprinter.format(thread, **kwargs))
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
    thing: (optional) exception, sys.exc_info() tuple, frame or thread
        What to format. Defaults to the currently handled exception or current
        stack frame.

    style: string
        'plaintext' (default): Output just text

        'darkbg', 'darkbg2', 'darkbg3', 'lightbg', 'lightbg2', 'lightbg3':
            Enable colors, for use in terminals that support 256 ansi
            colors or in jupyter notebooks (or even with `ansi2html`)

    source_lines: int or 'all'
        Select how much source code context will be shown.
        int 0: Don't include a source listing.
        int n > 0: Show n lines of code. (default: 5)
        string 'all': Show the whole scope of the frame.

    show_signature: bool (default True)
        Always include the function header in the source code listing.

    show_vals: str or None
        Select which variable values will be shown.
        'line': Show only the variables on the highlighted line.
        'like_source' (default): Show only those visible in the source listing
        'all': Show every variable in the scope of the frame.
        None: Don't show any variable values.

    truncate_vals: int
        Maximum number of characters to be used for each variable value.
        Default: 500

    line_wrap: int (default 60)
        Limit how many columns are available to print each variable
        (excluding its name). Set to 0 or False to disable wrapping.

    suppressed_paths: list of regex patterns
        Set less verbose formatting for frames whose code lives in certain paths
        (e.g. library code). Files whose path matches any of the given regex
        patterns will be considered boring. The first call to boring code is
        rendered with fewer code lines (but with argument values still visible),
        while deeper calls within boring code get a single line and no variable
        values.

        Example: To hide numpy internals from the traceback, set
        `suppressed_paths=[r"lib/python.*/site-packages/numpy"]`
        or
        `suppressed_paths=[re.compile(r"lib/python.*/site-packages/numpy")]`

    suppressed_exceptions: list of exception classes
        Show less verbose formatting for exceptions in this list.
        By default, this list is `[KeyboardInterrupt]`. Set to `[]`
        to force verbose formatting even on a keyboard interrupt.

    suppressed_vars: list of regex patterns
        Don't show the content of variables whose name matches any of the given
        patterns.
        Internally, this doesn't just filter the output, but stackprinter won't
        even try to access these values at all. So this can also be used as a
        workaround for rare issues around dynamic attribute lookups.

        Example:
        `suppressed_vars=[r".*password.*",  r"certainobject\.certainproperty"]`

    reverse: bool
        List the innermost frame first.

    add_summary: True, False, 'auto'
        Append a compact list of involved files and source lines, similar
        to the built-in traceback message.
        'auto' (default): do that if the main traceback is longer than 50 lines.

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
def show(thing=None, file='stderr', **kwargs):
    """
    Print the traceback of an exception or a frame's call stack

    Params
    ---
    file: 'stderr', 'stdout' or file-like object
        defaults to stderr

    **kwargs:
        See `format`
    """

    # First, to handle a very rare edge case:
    # Apparently there are environments where sys.stdout and stderr
    # are None (like the pythonw.exe GUI https://stackoverflow.com/a/30313091).
    # In those cases, it's not clear where our output should go unless the user
    # specifies their own file for output. So I'll make a pragmatic assumption:
    # If `show` is called with the default 'stderr' argument but we are in an
    # environment where that stream doesn't exist, we're most likely running as
    # part of a library that's imported in someone's GUI project and there just
    # isn't any error logging (if there was, the user would've given us a file).
    # So the least annoying behavior for us is to return silently, not crashing.
    if file == 'stderr' and sys.stderr is None:
        return

    if file == 'stderr':
        file = sys.stderr
    elif file == 'stdout':
        file = sys.stdout

    print(format(thing, **kwargs), file=file)



def format_current_stack(**kwargs):
    """ Render the current thread's call stack.

    Params
    --
    **kwargs:
        See `format`
    """
    return format(sys._getframe(1), **kwargs)

def show_current_stack(**kwargs):
    """ Print the current thread's call stack.

    Params
    --
    **kwargs:
        See `show`
    """
    show(sys._getframe(1), **kwargs)




def format_current_exception(**kwargs):
    """
    Render a traceback for the currently handled exception.

    Params
    --
    **kwargs:
        See `format`
    """
    return format(sys.exc_info(), **kwargs)

def show_current_exception(file=sys.stderr, **kwargs):
    """
    Print a traceback for the currently handled exception.

    Params
    --
    **kwargs:
        See `show`
    """
    if file is None:
        return # see explanation in `show()`
    print(format_current_exception(**kwargs), file=file)



def set_excepthook(**kwargs):
    """
    Set sys.excepthook to print a detailed traceback for any uncaught exception.

    See `format()` for available kwargs.

    Examples:
    ----

    Print to stdout instead of stderr:
    ```
    set_excepthook(file='stdout')
    ```

    Enable color output:
    ```
    set_excepthook(style='darkbg') # or e.g. 'lightbg' (for more options see `format`)
    ```

    If running under Ipython, this will, with a heavy heart, attempt to monkey
    patch Ipython's traceback printer (which handles all exceptions internally,
    thus bypassing the system excepthook). You can decide whether this sounds
    like a sane idea.

    To undo, call `remove_excepthook`.

    Params
    --
    **kwargs:
        See `show` and `format`
    """
    if _is_running_in_ipython():
        _patch_ipython_excepthook(**kwargs)
    else:
        def hook(*args):
            show(args, **kwargs)

        sys.excepthook = hook


def remove_excepthook():
    """ Reinstate the default excepthook """
    if _is_running_in_ipython():
        _unpatch_ipython_excepthook()
    sys.excepthook = sys.__excepthook__


def _is_running_in_ipython():
    try:
        return __IPYTHON__
    except NameError:
        return False


ipy_tb = None

def _patch_ipython_excepthook(**kwargs):
    """ Replace ipython's built-in traceback printer, excellent though it is"""
    global ipy_tb

    blacklist = kwargs.get('suppressed_paths', [])
    blacklist.append('site-packages/IPython/')
    kwargs['suppressed_paths'] = blacklist

    if 'file' in kwargs:
        del kwargs['file']

    def format_tb(*exc_tuple, **__):
        unstructured_tb = format(exc_tuple, **kwargs)
        structured_tb = [unstructured_tb]  # \*coughs*
        return structured_tb

    import IPython
    shell = IPython.get_ipython()
    if ipy_tb is None:
        ipy_tb = shell.InteractiveTB.structured_traceback
    shell.InteractiveTB.structured_traceback = format_tb


def _unpatch_ipython_excepthook():
    """ restore proper order in Ipython """
    import IPython
    shell = IPython.get_ipython()
    if ipy_tb is not None:
        shell.InteractiveTB.structured_traceback = ipy_tb


def _is_exc_info(thing):
    if not isinstance(thing, tuple) or len(thing) != 3:
        return False
    a, b, c = thing
    return ((a is None or (isinstance(a, type) and BaseException in a.mro())) and
            (b is None or (isinstance(b, BaseException))))

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
