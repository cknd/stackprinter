import sys
import time
from threading import Thread
from stackprinter import format

def forever():
    x = 0
    while True:
        x += 1
        y = x % 2
        if y == 0:
            assert y == 0
            dosomething(x)
        else:
            assert y != 0
            dosomethingelse(x)


def dosomething(x):
    time.sleep(1./x)


def dosomethingelse(x):
    time.sleep(1./x)


thr = Thread(name='boing', target=forever, daemon=True)

thr.start()


while True:
    print(chr(27) + "[2J") # clear screen
    print(format(thr, style='color', source_lines='all'))
    time.sleep(2)