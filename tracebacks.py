import sys
import traceback
import inspect


def printlocals(frame, truncate=500, truncate__=True):
    sep = '.' * 50
    msg = '    %s\n' % sep
    for name, value in sorted(frame.f_locals.items()):
        if hasattr(value, '__repr__'):
            try:
                val_str = value.__repr__()
            except:
                val_str = "<error calling __repr__>"
        else:
            try:
                val_str = str(value)
            except:
                val_str = "<error calling str()>"

        if truncate and len(val_str) > truncate:
            val_str = "%s..." % val_str[:truncate]
        if truncate__ and name.startswith('__') and len(val_str) > 50:
            val_str = "%s..." % val_str[:50]
        val_str = val_str.replace('\n', '\n        %s' % (' ' * (len(name) + 2)))

        msg += "       %s = %s\n" % (name, val_str)

    msg += '    %s' % sep
    return msg


def get_lines(frame):
    """
    get source for this frame

    Params
    ---
    frame : frame object

    Returns
    ---
    lines : list of str

    startline : int
        line number of lines[0] in the original source file
    """
    if frame.f_code.co_name == '<module>':
        lines, _ = inspect.findsource(frame)
        startline = 1
    else:
        lines, startline = inspect.getsourcelines(frame)

    return lines, startline


def format_line(line, line_idx, lineno=None):
    if lineno is not None and line_idx == lineno:
        msg = "--> %-3s %s" % (line_idx, line)
    else:
        msg = "    %-3s %s" % (line_idx, line)
    return msg


def get_source_lines(frame, lineno, context=5, always_show_signature=True):
    try:
        lines, startline = get_lines(frame)
    except:
        return ''

    name = frame.f_code.co_name
    start = max(lineno - context, 0)
    stop = lineno + 1
    source_str = ''
    if start > startline and always_show_signature and name != '<module>':
        source_str += format_line(lines[0], startline)
        source_str += '       (...)\n'

    for ln, line in enumerate(lines):
        line_idx = ln + startline
        if line_idx >= start and line_idx <= stop:
            source_str += format_line(line, line_idx, lineno)
    return source_str


def tb2string(tb, ):
    frame_strings = []
    while tb:
        frame = tb.tb_frame
        lineno = tb.tb_lineno
        frameinfo = inspect.getframeinfo(frame)
        msg = "File %s, line %s in %s\n" % (frameinfo.filename, lineno, frameinfo.function)

        source_str = get_source_lines(frame, lineno)
        if source_str:
            msg += source_str
            msg += printlocals(frame)


        frame_strings.append(msg)
        tb = tb.tb_next

    return '\n\n\n'.join(frame_strings)


def format_traceback(tb, etype=None, evalue=None):
    msg = tb2string(tb)
    if etype is not None and evalue is not None:
        exc_str = ' '.join(traceback.format_exception_only(etype, evalue))
        msg += '\n' + exc_str
    return msg



if __name__ == '__main__':
    import numpy as np

    def a_broken_function(thing, otherthing=1234):
        # very long function
        # with many lines
        # and various weird variables
        X = np.zeros((5, 5))
        X[0] = len(thing)
        for k in X:
            if np.sum(k) != 0:
                raise Exception('something happened')
                # more code:
                zup = 123

    def some_function(boing, zap='!'):
        thing = boing + zap
        a_broken_function(thing)

    # some_function("hello")
    try:
        some_function("hello")
    except:
        etype, exc, tb = sys.exc_info()
        print(format_traceback(tb, etype, exc))




