import sys
import inspect

from stackprinter import formatting as fmt
from stackprinter import prettyprinting as ppr
from stackprinter.utils import match

# import random
# rng = random.Random()
# def colorid(obj):
#     if obj is None:
#         return 'None'
#     seed = id(obj)
#     rng.seed(seed)
#     hue = rng.uniform(0.05,0.7)
#     # if hue < 0:
#     #     hue = hue + 1
#     sat = 1.
#     val = 1.
#     return fmt.get_ansi_tpl(hue, sat, val) % id(obj)


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
    def __init__(self, blacklist=[], **formatter_kwargs):

        self.fmt = _get_formatter(**formatter_kwargs)
        self.fmt_color_mode = formatter_kwargs.get('mode', None)
        assert isinstance(blacklist, list)
        self.blacklist = [__file__] + blacklist

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

    def show(self, frame, note=''):
        depth = _count_stack(frame) - self.starting_depth
        our_callsite = frame.f_back
        callsite_of_previous_frame = getattr(self.previous_frame, 'f_back', -1)
        if self.previous_frame is our_callsite and our_callsite is not None:
            # we're a child frame
            self.emit(' └──┐\n', depth - 1)
        if frame is callsite_of_previous_frame:
            # we're a parent frame
            self.emit('┌──────┘\n', depth)

        frame_str = self.fmt(frame) + '\n'
        self.emit(frame_str, depth)
        self.emit(note, depth)
        self.previous_frame = frame

    def trace(self, frame, event, arg):
        filepath = inspect.getsourcefile(frame) or inspect.getfile(frame)
        # self.emit("%s, %s <- %s <- %s, prev: %s <- %s <- %s" % (event, colorid(frame), colorid(frame.f_back),colorid(getattr(frame.f_back,'f_back')), colorid(self.previous_frame), colorid(getattr(self.previous_frame,'f_back', None)), colorid(getattr(getattr(self.previous_frame,'f_back', None),'f_back', None))), depth)

        if match(filepath, self.blacklist):
            return self.trace

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
            self.disable()
            return None

        # self.previous_frame = frame

        return self.trace


    # def trace(self, frame, event, arg):
    #     depth = _count_stack(frame) - self.starting_depth
    #     filepath = inspect.getsourcefile(frame) or inspect.getfile(frame)
    #     # self.emit("%s, %s <- %s <- %s, prev: %s <- %s <- %s" % (event, colorid(frame), colorid(frame.f_back),colorid(getattr(frame.f_back,'f_back')), colorid(self.previous_frame), colorid(getattr(self.previous_frame,'f_back', None)), colorid(getattr(getattr(self.previous_frame,'f_back', None),'f_back', None))), depth)

    #     if match(filepath, self.blacklist):
    #         return self.trace

    #     # if self.previous_frame and frame is self.previous_frame.f_back:
    #     #     self.emit('┌──────┘\n', depth)
    #     #     self.previous_frame = None

    #     if event == 'exception':
    #         frame_str = self.fmt(frame)
    #         self.emit(frame_str, depth)
    #         exc_str = fmt.format_exception_message(*arg, mode=self.fmt_color_mode)
    #         self.emit(exc_str + '\n', depth)
    #         self.disable()
    #         return None

    #     elif event == 'line':
    #         pass

    #     elif event in ['call', 'c_call']:
    #         our_callsite = frame.f_back
    #         callsite_of_previous_frame = getattr(self.previous_frame, 'f_back', -1)
    #         if callsite_of_previous_frame is our_callsite:
    #             callsite_str = '┌──────┘\n'
    #         else:
    #             callsite_str = ''
    #         callsite_str += self.fmt(our_callsite)
    #         callsite_str += '\n └──┐'
    #         self.emit(callsite_str, depth - 1)

    #         # if (self.previous_frame is frame.f_back) or self.always_show_call_site:

    #         #     # ??
    #         #     if frame.f_back is getattr(self.previous_frame, 'f_back', 0):
    #         #         self.emit('┌──────┘\n', depth - 1)
    #         #     # ??

    #         #     callsite_str = self.fmt(frame.f_back)
    #         #     self.emit(callsite_str, depth - 1)
    #         #     self.emit('\n └──┐', depth - 1)

    #         frame_str = self.fmt(frame)
    #         self.emit(frame_str, depth)

    #     elif event in ['return', 'c_return']:
    #         frame_str = self.fmt(frame)
    #         self.emit(frame_str, depth)
    #         val_str = ppr.format_value(arg, indent=11, truncation=1000)
    #         ret_str = '    Return %s' % val_str
    #         self.emit(ret_str, depth)

    #     self.previous_frame = frame

    #     return self.trace

    def emit(self, string, indent_depth=0):
        # sys.stdout.flush()
        indented = _add_indent(string, indent_depth)
        # sys.stdout.write(string)
        sys.stdout.write(indented)
        sys.stdout.flush()


def _add_indent(string, depth=1, max_depth=10):
    depth = max(depth, 0)

    if depth > max_depth:
        indent = 'd %s' % depth + '    ' * max_depth
    else:
        indent = '    ' * depth

    lines = [indent + line + '\n' for line in string.splitlines()]
    indented = ''.join(lines)
    return indented

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
