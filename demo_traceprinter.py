from traceprinter import trace

@trace(mode='color')
def dosomething(x):
    y = dosomethingelse(x)
    return y

def dosomethingelse(y):
    return doYetAnotherThing(y)

def doYetAnotherThing(z):
    import numpy as np
    z = np.eye(3)
    raise Exception('ahoi')

dosomething(5)