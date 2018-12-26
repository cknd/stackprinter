import sys
import inspect

from stackprinter import formatting as fmt
from stackprinter import prettyprinting as ppr
from stackprinter.utils import match


class TracePrinter():
    def __init__(self, blacklist=[], **formatter_kwargs):
        self.fmt = _get_formatter(**formatter_kwargs)
        self.fmt_color_mode = formatter_kwargs.get('mode', None)
        self.last_executed_line = None
        assert isinstance(blacklist, list)
        self.blacklist = [__file__] + blacklist

    def enable(self, force=False):
        self.starting_depth = _count_stack(sys._getframe())
        self.trace_before = sys.gettrace()
        if (self.trace_before is not None) and not force:
            raise Exception("There is already a trace function registered: %r" % self.trace_before)
        sys.settrace(self.trace)

    def disable(self):
        sys.settrace(self.trace_before)
        self.last_executed_line = None

    def trace(self, frame, event, arg):
        depth = _count_stack(frame) - self.starting_depth
        filepath = inspect.getsourcefile(frame) or inspect.getfile(frame)

        if match(filepath, self.blacklist):
            return self.trace

        if event == 'exception':
            frame_str = self.fmt(frame)
            self.emit(frame_str, depth)
            exc_str = fmt.format_exception_message(*arg, mode=self.fmt_color_mode)
            self.emit(exc_str, depth)
            self.emit('\n')
            self.disable()
            return None
        elif event == 'line':
            self.last_executed_line = frame
        else:
            if event == 'call' and self.last_executed_line == frame.f_back:
                callsite = self.last_executed_line
                callsite_str = self.fmt(callsite)
                self.emit(callsite_str, depth-1)
                self.last_executed_line = None

            frame_str = self.fmt(frame)
            if event == 'return':
                val_str = ppr.format_value(arg, indent=11, truncation=1000)
                frame_str += '<== Return %s' % val_str

            self.emit(frame_str, depth)

        return self.trace

    def emit(self, string, indent_depth=0):
        indented = _add_indent(string, indent_depth)
        print(indented)

    def __del__(self):
        del self.last_executed_line

def _add_indent(string, depth=1, max_depth=10):
    depth = max(depth, 0)
    if depth > max_depth:
        indent = 'depth %s' % depth + '    ' * max_depth
    else:
        indent = '    ' * depth
    return indent + ('\n' + indent).join(string.split('\n')).strip()

def _get_formatter(mode='plaintext', **kwargs):
    if mode == 'plaintext':
        Formatter = fmt.FrameFormatter
    elif mode in ['color', 'html']:
        Formatter = fmt.ColoredFrameFormatter
    return Formatter(**kwargs)

def _count_stack(frame):
    depth = 1
    fr = frame
    while fr.f_back:
        fr = fr.f_back
        depth += 1
    return depth


def trace(blacklist=[], **formatter_kwargs):
    traceprinter = TracePrinter(blacklist=blacklist, **formatter_kwargs)

    def deco(f):
        def wrapped_for_trace_printing(*args, **kwargs):
            traceprinter.enable()
            result = f(*args, **kwargs)
            traceprinter.disable()
            return result
        return wrapped_for_trace_printing
    return deco

