import os
import re
import inspect
from collections import OrderedDict

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


def trim_source(source_map, context):
    """
    get part of a source listing, with extraneous indentation removed

    """
    indent_type = None
    min_indent = 9000
    for ln in context:
        (snippet0, *meta0), *remaining_line = source_map[ln]

        if snippet0.startswith('\t'):
            if indent_type == ' ':
                # Mixed tabs and spaces - not trimming whitespace.
                return source_map
            else:
                indent_type = '\t'
        elif snippet0.startswith(' '):
            if indent_type == '\t':
                # Mixed tabs and spaces - not trimming whitespace.
                return source_map
            else:
                indent_type = ' '
        elif snippet0.startswith('\n'):
            continue

        n_nonwhite = len(snippet0.lstrip(' \t'))
        indent = len(snippet0) - n_nonwhite
        min_indent = min(indent, min_indent)

    trimmed_source_map = OrderedDict()
    for ln in context:
        (snippet0, *meta0), *remaining_line = source_map[ln]
        if not snippet0.startswith('\n'):
            snippet0 = snippet0[min_indent:]
        trimmed_source_map[ln] = [[snippet0] + meta0] + remaining_line

    return trimmed_source_map