if __name__ == '__main__':

    from stackprinter import TracePrinter, trace
    import time
    import sys
    import numpy as np
    import stackprinter


    class whatever():
        # @trace(style='color')#, blacklist=[r'site-packages/numpy'])
        def ahoi(self):
            return some_function('')

    blub = '123'
    somelist = [1,2,3,np.zeros((23,42)), np.ones((42,23))]
    outer_scope_thing = {'various': 'things',
                         123: 'in a dict',
                         'and': np.ones((42,23)),
                         'in a list': somelist}

    def deco(f):
        bla = 1234
        def closure(*args, **kwargs):
            kwargs['things'] = bla
            return f(*args, **kwargs)

        return closure

    @deco
    def a_broken_function(thing,
                          various=None,
                          other=None,
                          things=None):
        """
        some very long
        doc string
        """
        bla = """ another triple quoted string """
        X = np.zeros((10,10))
        X[0,0] = 1
        boing = outer_scope_thing['and']
        foo = somelist
        do_something = lambda val: another_broken_function(val + outer_scope_thing['and'] + boing)
        for k in X:
            if np.sum(k) != 0:
                return [[do_something(val) for val in row] for row in X]

    def some_function(boing, zap='!'):
        thing = boing + zap
        a_broken_function(thing)

    def another_broken_function(val):
        if np.sum(val) != 42:
            bla = val.T.\
                  T.T.\
                  T

            # here is a comment \
            # that has backslashes \
            # for some reason
            ahoi = "here is a "\
                   "multi line "\
                   "string"
            # np.reshape(bla, 9000)
            boing = np.\
                    random.rand(*bla.T.\
                            T.T)
            raise Exception('something happened')

    try:
        whatever().ahoi()
    except:
        stackprinter.show(style='color', reverse=False, suppressed_paths=[r"lib/python.*/site-packages/numpy"])