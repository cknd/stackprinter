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

def show_stack(thread):
    try:
        fr = sys._current_frames()[thread.ident]
    except KeyError:
        print('cant print stack, thread doesnt exist')
        return


    stack = [fr]
    while fr.f_back is not None:
        fr = fr.f_back
        stack.append(fr)

    print(thread, '\n')
    # formatter = formatting.ColoredVariablesFormatter()
    formatter = formatting.FrameFormatter()
    for fr in reversed(stack):
        if 'threading.py' in fr.f_code.co_filename:
            continue
        finfo = extraction.inspect_frame(fr)
        msg = formatter.format_frame(finfo, source_context=7)
        print('    ' + '\n    '.join(msg.split('\n')))



while True:
    print(chr(27) + "[2J") # clear screen
    show_stack(thr)
    time.sleep(0.1)