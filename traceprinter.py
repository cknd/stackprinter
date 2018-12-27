import sys
import inspect

from stackprinter import formatting as fmt
from stackprinter import prettyprinting as ppr
from stackprinter.utils import match


def trace(*args, blacklist=[], **formatter_kwargs):
    traceprinter = TracePrinter(blacklist=blacklist,
                                **formatter_kwargs)

    def deco(f):
        def wrapped_for_trace_printing(*args, **kwargs):
            traceprinter.enable()
            result = f(*args, **kwargs)
            traceprinter.disable()
            return result
        return wrapped_for_trace_printing

    if args:
        return deco(args[0])
    else:
        return deco


class TracePrinter():
    def __init__(self,
                 blacklist=[],
                 depth_limit=20,
                 print_function=sys.stderr.write,
                 stop_on_exception=True,
                 **formatter_kwargs):

        self.fmt = _get_formatter(**formatter_kwargs)
        self.fmt_color_mode = formatter_kwargs.get('mode', None)
        assert isinstance(blacklist, list)
        self.blacklist = [__file__] + blacklist
        self.emit = print_function
        self.depth_limit = depth_limit
        self.stop_on_exception = stop_on_exception

    def enable(self, force=False):
        self.starting_depth = _count_stack(sys._getframe()) - 1
        self.trace_before = sys.gettrace()
        if (self.trace_before is not None) and not force:
            raise Exception("There is already a trace function registered: %r" % self.trace_before)
        sys.settrace(self.trace)
        self.previous_frame = None

    def disable(self):
        sys.settrace(self.trace_before)
        del self.previous_frame

    def trace(self, frame, event, arg):
        try:
            depth = _count_stack(frame) - self.starting_depth
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
                exc_str = fmt.format_exception_message(*arg, mode=self.fmt_color_mode)
                self.show(frame, note=exc_str)
                if self.stop_on_exception:
                    self.disable()
                return None

            return self.trace
        except Exception as e:
            import stackprinter
            stackprinter.show(e)

    def show(self, frame, note=''):
        if frame is None:
            return

        depth = _count_stack(frame) - self.starting_depth
        filepath = inspect.getsourcefile(frame) or inspect.getfile(frame)

        if match(filepath, self.blacklist):
            return

        our_callsite = frame.f_back
        callsite_of_previous_frame = getattr(self.previous_frame, 'f_back', -1)
        if self.previous_frame is our_callsite and our_callsite is not None:
            # we're a child frame
            self.emit(add_indent(' └──┐\n', depth - 1))
        if frame is callsite_of_previous_frame:
            # we're a parent frame
            self.emit(add_indent('┌──────┘\n', depth))

        frame_str = self.fmt(frame)
        self.emit(add_indent(frame_str, depth))
        self.emit(add_indent(note, depth))
        self.previous_frame = frame



def add_indent(string, depth=1, max_depth=5):
    depth = max(depth, 0)

    if depth > max_depth:
        indent = '%s   ' % depth + '    ' * (depth % max_depth)
    else:
        indent = '    ' * depth

    lines = [indent + line + '\n' for line in string.splitlines()]
    indented = ''.join(lines)
    return indented

# def add_indent(string, depth=1, max_depth=10):
#     depth = max(depth, 0)

#     if depth > max_depth:
#         indent = 'd %s' % depth + '    ' * (depth % max_depth)
#     else:
#         indent = '    ' * depth

#     nl_indented = '\n' + indent
#     return string.replace('\n', nl_indented)

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
