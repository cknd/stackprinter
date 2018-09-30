from formatting import format, excepthook



if __name__ == '__main__':
    import sys
    import time
    # from tracebacks2 import format
    import numpy as np
    # sys.excepthook = excepthook

    scopidoped = None

    def a_broken_function(thing, otherthing=1234):
        # very long function
        # with many lines
        # and various weird variables
        X = np.zeros((4,5))
        Y = np.array(0)
        do_something = lambda val: another_broken_function(val)
        scoped = scopidoped
        # np.reshape(X,9000)
        # np.linalg.norm.nonexistant_attribute()
        listcomp = [[do_something(val) for val in row] for row in X]
        X[0] = len(thing)
        for k in X:
            if np.sum(k) != 0:
                raise Exception('something happened')
                # more code:
                zup = 123

    def some_function(boing, zap='!'):
        thing = boing + zap
        a_broken_function(thing)


    def another_broken_function(val):
        if val != 42:
            raise Exception('ahoi!')

    # some_function("hello")
    try:
        some_function("hello")
    except:
        stuff = sys.exc_info()
        scopidoped = 'gotcha'
        tb_string = format(*stuff)
        print(tb_string)
