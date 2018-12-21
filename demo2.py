if __name__ == '__main__':
    import time
    import sys
    import numpy as np
    from stackprinter import format


    def bump():
        somelist = [1,2,3,np.zeros((23,42)), np.ones((42,23)), 4,5,6,7,8,9,10,11,12,13,14,15,16,17]
        somedict = {'various': 'excellent',
                             123: 'things',
                             'in': np.ones((42,23)),
                             'a list': somelist}
        sometuple = (1,2, somedict, np.ones((32,64)))
        somedict['recursion'] = somedict
        raise Exception()


    try:
        bump()
    except:
        stuff = sys.exc_info()
        scopidoped = 'gotcha'
        tic = time.perf_counter()

        msg = format(stuff, mode='color', source_lines='all', reverse=False, truncate_vals=1000, suppressed_paths=["site-packages"])

        took = time.perf_counter() - tic
        print(msg)
        print('took', took * 1000)
