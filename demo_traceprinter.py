from stackprinter import trace, TracePrinter
import numpy as np

# @trace(style='color')
def dosomething(x):
    y = dosomethingelse(x)
    return y

def dosomethingelse(y):
    a = 2*y
    b = doYetAnotherThing(y)
    # raise Exception('ahoi')
    return b

def doYetAnotherThing(z):
    a = z
    b = {'a': np.ones(1)}
    zup = np.ones(0)
    return zup



tp = TracePrinter(style='color', suppressed_paths=[r"lib/python.*/site-packages/numpy"])
tp.enable()
a = np.ones(123)
dosomething(a)
tp.disable()