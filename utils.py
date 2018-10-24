import inspect
import os

def inspect_callable(f):
    # print(repr(f))
    # import pdb; pdb.set_trace()


    # TODO cleanup / refactor

    owner = None
    if inspect.ismethod(f):
        owner = getattr(f, '__self__', None)
        f = f.__func__

    if inspect.isfunction(f):
        code = f.__code__
        # if owner is None:
        #     owner = getattr(f, '__self__', None)
    else:
        try:
            fname = f.__qualname__
        except AttributeError:
            return None, None, None, None
        else:
            return fname, None, None, None

    filepath = code.co_filename
    ln = code.co_firstlineno
    filename = os.path.basename(filepath)
    return f.__qualname__, filename, ln, owner



