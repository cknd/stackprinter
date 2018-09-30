from formatting import format, excepthook



if __name__ == '__main__':
    import sys
    import time
    # from tracebacks2 import format
    import numpy as np
    # sys.excepthook = excepthook


    outer_scope_thing = 4

    def a_broken_function(thing,
                          various=None,
                          other=None,
                          things=None):

        X = np.zeros((len(thing), outer_scope_thing))
        X[0,0] = 1
        do_something = lambda val: another_broken_function(val + outer_scope_thing)
        for k in X:
            if np.sum(k) != 0:
                listcomp = [[do_something(val) for val in row] for row in X]

    def some_function(boing, zap='!'):
        thing = boing + zap
        a_broken_function(thing)


    def another_broken_function(val):
        if val != 42:
            raise Exception('something happened')
            # np.reshape([1,2,3], 9000)
            # val.nonexistant_attribute()

    # some_function("hello")
    try:
        some_function("hello")
    except:
        stuff = sys.exc_info()
        scopidoped = 'gotcha'
        tb_string = format(*stuff)
        print(tb_string)
