import sys
import time
from threading import Thread
import extraction
import formatting

def forever():
    x = 0
    while True:
        x += 1
        if x % 2 == 0:
            do_something()
        else:
            do_something_else()

def do_something():
    """ a function """
    time.sleep(0.5)

def do_something_else():
    """ some other function """
    time.sleep(0.5)


thr = Thread(name='boing', target=forever, daemon=True)

thr.start()


def add_indent(string):
    return '    ' + '\n    '.join(string.split('\n')).strip()

def show_stack(thread, suppress=['threading.py']):
    try:
        fr = sys._current_frames()[thread.ident]
    except KeyError:
        return "%r: no active frames found" % thread

    stack = [fr]
    while fr.f_back is not None:
        fr = fr.f_back
        stack.append(fr)

    msg = "%r\n\n" % thread
    formatter = formatting.ColoredFrameFormatter(source_context=7)
    # formatter = formatting.FrameFormatter(source_context=7)
    for fr in reversed(stack):
        if any(pt in fr.f_code.co_filename for pt in suppress):
            co = fr.f_code
            frame_msg = "File %s, line %s, in %s\n" % (co.co_filename, fr.f_lineno, co.co_name)
        else:
            finfo = extraction.get_info(fr)
            frame_msg = formatter(finfo)
        msg += add_indent(frame_msg) + '\n'
    return msg


while True:
    print(chr(27) + "[2J") # clear screen
    print(show_stack(thr))
    time.sleep(0.1)