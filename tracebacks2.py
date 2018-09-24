from formatting import format, excepthook



if __name__ == '__main__':
    import sys
    # from tracebacks2 import format
    import numpy as np


    outer_scope_thing = ".oOo."

    def a_broken_function(thing, otherthing=1234):
        # very long function
        # with many lines
        # and various weird variables
        X = np.zeros((5,5))
        Y = np.array(0)
        scoped = outer_scope_thing
        # np.reshape(X,9000)
        np.linalg.norm.broken_attribute_lookup()
        X[0] = len(thing)
        for k in X:
            if np.sum(k) != 0:
                raise Exception('something happened')
                # more code:
                zup = 123

    def some_function(boing, zap='!'):
        thing = boing + zap
        a_broken_function(thing)

    # some_function("hello")
    try:
        some_function("hello")
    except:
        tb_string = format(*sys.exc_info())
        print(tb_string)

