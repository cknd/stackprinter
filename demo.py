if __name__ == '__main__':

    from traceprinter import TracePrinter
    # tp = TracePrinter(style='color'); tp.enable()
    import time
    import sys
    import numpy as np
    import stackprinter
    from traceprinter import trace

    class whatever():
        # @trace(style='color')#, blacklist=[r'site-packages/numpy'])
        def ahoi(self):
            # raise Exception()
            return some_function('')

    blub = '123'
    somelist = [1,2,3,np.zeros((23,42)), np.ones((42,23))]
    outer_scope_thing = {'various': 'excellent',
                         123: 'things',
                         'in': np.ones((42,23)),
                         'a list': somelist}

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
        boing = outer_scope_thing['in']
        foo = somelist
        do_something = lambda val: another_broken_function(val + outer_scope_thing['in'] + boing)
        for k in X:
            if np.sum(k) != 0:
                # raise Exception()
                hiho = locals()
                listcomp = [[do_something(val) for val in row] for row in X]

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

            # stackprinter.show_stack(style='color')
            np.reshape(bla, 9000)
            boing = np.\
                    random.rand(*bla.T.\
                            T.T)
            raise Exception('something happened')




    try:
        wha = whatever()
        wha.ahoi()
    except:
        pass
        stackprinter.show(style='color', source_lines=5, reverse=False, truncate_vals=500, suppressed_paths=["site-packages"])
