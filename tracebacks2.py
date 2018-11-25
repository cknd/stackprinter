# import sys
# import traceback
# from formatting import FrameFormatter, ColoredFrameFormatter
# import extraction as ex


# # TODO:
# # verbosity blacklisting not only by folder but also by
# # exception type -- KeyboardInterrupt probable never
# # warrants a full stack inspection


# def failsafe(formatter_func):
#     """
#     Recover the built-in traceback if we fall on our face while formatting
#     """
#     def failsafe_formatter(etype, evalue, tb, *args, **kwargs):
#         try:
#             msg = formatter_func(etype, evalue, tb, **kwargs)
#         except Exception as exc:
#             our_tb = traceback.format_exception(exc.__class__,
#                                                 exc,
#                                                 exc.__traceback__,
#                                                 chain=False)

#             msg = 'Stackprinter failed:\n%s' % ''.join(our_tb[-2:])
#             msg += 'So here is the original traceback at least:\n\n'
#             msg += ''.join(traceback.format_exception(etype, evalue, tb))

#         return msg

#     return failsafe_formatter


# # def format_summary(frameinfos, reverse_order=False):
# #     msg_inner = format_tb(frameinfos[-1], TerseFormatter(), reverse_order)
# #     msg_outer = format_tb(frameinfos[:-1], MinimalFormatter(), reverse_order)
# #     msg = [msg_outer, msg_inner]
# #     if reverse_order:
# #         msg = reversed(msg)
# #     return "".join(msg)

# @failsafe
# def format(etype, evalue, tb, show_full=True, show_summary=False,
#            reverse_order=False, **formatter_kwargs):
#     import time
#     tice = time.perf_counter()
#     frames = list(ex.walk_traceback(tb))
#     frameinfos = [ex.get_info(fr) for fr in frames]
#     tooke = time.perf_counter() - tice


#     import time; tic = time.perf_counter()
#     exception_msg = ' '.join(traceback.format_exception_only(etype, evalue))

#     if show_summary:
#         msg = format_summary(frameinfos, reverse_order)
#         msg += exception_msg

#     else:
#         msg = ''

#     if show_full:
#         if show_summary:
#             msg += "\n\n========== Full traceback: ==========\n"
#         # formatter = FrameFormatter(**formatter_kwargs)
#         formatter = ColoredFrameFormatter(**formatter_kwargs)
#         msg += format_tb(frameinfos, formatter, reverse_order)
#         msg += exception_msg

#     msg += 'extraction took %s\n' % (tooke*1000)
#     msg += 'formating took %s' % ((time.perf_counter() - tic) * 1000)
#     return msg




# def format_tb(frameinfos, formatter=None, reverse_order=False):
#     if formatter is None:
#         formatter = FrameFormatter()

#     if not isinstance(frameinfos, list):
#         frameinfos = [frameinfos]

#     tb_strings = []
#     for fi in frameinfos:
#         tb_strings.append(formatter(fi))

#     if reverse_order:
#         tb_strings = reversed(tb_strings)

#     return "".join(tb_strings)


if __name__ == '__main__':
    import time
    # from tracebacks2 import format
    import numpy as np
    sys.excepthook = excepthook

    class whatever():
        def ahoi(self):
            # raise Exception()
            return some_function('')

    outer_scope_thing = {'various': 'excellent',
                         123: 'things',
                         'in': np.ones((42,23))}

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
        X = np.zeros((len(thing), len(outer_scope_thing)))
        X[0,0] = 1
        boing = outer_scope_thing['in']
        do_something = lambda val: another_broken_function(val + outer_scope_thing['in'] + boing)
        for k in X:
            if np.sum(k) != 0:
                # raise Exception()
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

            boing = np.\
                    random.rand(*bla.T.\
                            T.T)
            raise Exception('something happened')


    # some_function("hello")
    # wha = whatever()
    # wha.ahoi()
    try:
        wha = whatever()
        wha.ahoi()
    except:
        stuff = sys.exc_info()
        scopidoped = 'gotcha'
        tic = time.perf_counter()

        msg = format(*stuff)

        took = time.perf_counter() - tic
        print(msg)
        print('took', took * 1000)
