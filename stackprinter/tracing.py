import sys
import inspect

from stackprinter.frame_formatting import FrameFormatter, ColorfulFrameFormatter
from stackprinter.formatting import format_exception_message
from stackprinter import prettyprinting as ppr
from stackprinter.utils import match


def trace(*args, suppressed_paths=[], **formatter_kwargs):
    """ get a decorator """
    traceprinter = TracePrinter(suppressed_paths=suppressed_paths,
                                **kwargs)

    def deco(f):
        def wrapper(*args, **kwargs):
            traceprinter.enable(current_depth=count_stack(sys._getframe()) + 1)
            result = f(*args, **kwargs)
            traceprinter.disable()
            return result
        return wrapper

    if args:
        return deco(args[0])
    else:
        return deco


class TracePrinter():
    def __init__(self,
                 suppressed_paths=[],
                 depth_limit=20,
                 print_function=sys.stderr.write,
                 stop_on_exception=True,
                 reverse=False,
                 **formatter_kwargs):

        self.fmt = get_frame_formatter(**formatter_kwargs)
        self.fmt_style = formatter_kwargs.get('style', None)
        assert isinstance(suppressed_paths, list)
        self.suppressed_paths = suppressed_paths
        self.emit = print_function
        self.depth_limit = depth_limit
        self.stop_on_exception = stop_on_exception

    def enable(self, force=False, current_depth=None):
        if current_depth is None:
            current_depth = count_stack(sys._getframe(1))
        self.starting_depth = current_depth
        self.previous_frame = None
        self.trace_before = sys.gettrace()
        if (self.trace_before is not None) and not force:
            raise Exception("There is already a trace function registered: %r" % self.trace_before)
        sys.settrace(self.trace)

    def disable(self):
        sys.settrace(self.trace_before)
        try:
            del self.previous_frame
        except AttributeError:
            pass

    def trace(self, frame, event, arg):
        depth = count_stack(frame) - self.starting_depth
        if depth >= self.depth_limit:
            return None

        if 'call' in event:
            callsite = frame.f_back
            self.show(callsite)
            self.show(frame)
        elif 'return' in event:
            val_str = ppr.format_value(arg, indent=11, truncation=1000)
            ret_str = '    Return %s\n' % val_str
            self.show(frame, note=ret_str)
        elif event == 'exception':
            exc_str = format_exception_message(*arg, style=self.fmt_style)
            self.show(frame, note=exc_str)
            if self.stop_on_exception:
                self.disable()
            return None

        return self.trace

    def show(self, frame, note=''):
        if frame is None:
            return

        filepath = inspect.getsourcefile(frame) or inspect.getfile(frame)
        if match(filepath, __file__):
            return
        elif match(filepath, self.suppressed_paths):
            line_info = (filepath, frame.f_lineno, frame.f_code.co_name)
            frame_str = 'File %s, line %s, in %s\n' % line_info
            if len(note) > 123:
                note == note[:120] + '...'
        else:
            frame_str = self.fmt(frame)

        depth = count_stack(frame) - self.starting_depth
        our_callsite = frame.f_back
        callsite_of_previous_frame = getattr(self.previous_frame, 'f_back', -1)
        if self.previous_frame is our_callsite and our_callsite is not None:
            # we're a child frame
            self.emit(add_indent(' └──┐\n', depth - 1))
        if frame is callsite_of_previous_frame:
            # we're a parent frame
            self.emit(add_indent('┌──────┘\n', depth))


        frame_str += note
        self.emit(add_indent(frame_str, depth))
        self.previous_frame = frame


def add_indent(string, depth=1, max_depth=10):
    depth = max(depth, 0)

    if depth > max_depth:
        indent = '%s   ' % depth + '    ' * (depth % max_depth)
    else:
        indent = '    ' * depth

    lines = [indent + line + '\n' for line in string.splitlines()]
    indented = ''.join(lines)
    return indented


def get_frame_formatter(style='plaintext', **kwargs):
    if style == 'plaintext':
        Formatter = FrameFormatter
    elif style == 'color':
        Formatter = ColorfulFrameFormatter
    return Formatter(**kwargs)


def count_stack(frame):
    depth = 1
    fr = frame
    while fr.f_back:
        fr = fr.f_back
        depth += 1
    return depth
