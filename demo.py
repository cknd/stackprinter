import numpy as np
import stackprinter

# tp = stackprinter.TracePrinter(style='color', stop_on_exception=False, suppressed_paths=[r"lib/python.*/"])
# tp.enable()

def a_broken_function(blub):
    for k in blub:
        another_broken_function(k)

def another_broken_function(k):
    if np.any(k):
        raise Exception('something happened')


try:
    somelist = [0, 0, np.zeros((23,42)), np.ones((42,23))]
    a_broken_function(somelist)
except:
    # tp.disable()
    pass
    stackprinter.show(style='color')
    raise
# stackprinter.show(style='plaintext')

