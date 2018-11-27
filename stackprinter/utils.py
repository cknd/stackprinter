import inspect
import os
import re

def match(string, patterns):
    if not isinstance(string, str):
        return False
    if isinstance(patterns, str):
        patterns = []
    elif patterns is None:
        return False
    return any([bool(re.search(p, string)) for p in patterns])

def inspect_callable(f):
    # print(repr(f))
    # import pdb; pdb.set_trace()


    # TODO cleanup / refactor

    owner = getattr(f, '__self__', None)

    if inspect.ismethod(f):
        f = f.__func__

    if inspect.isfunction(f):
        code = f.__code__
    else:
        return None, None, None, None

    try:
        qname = f.__qualname__
    except AttributeError:
        qname = None

    filepath = code.co_filename
    ln = code.co_firstlineno
    return qname, filepath, owner, ln



