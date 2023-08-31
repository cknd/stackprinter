import re
import inspect
from collections import OrderedDict


def match(string, patterns):
    if patterns is None or not isinstance(string, str):
        return False
    if isinstance(patterns, str):
        patterns = [patterns]

    return any(map(lambda p: re.search(p, string), patterns))


def inspect_callable(f):
    """
    Find out to which object & file a function belongs
    """
    # TODO cleanup

    owner = getattr(f, '__self__', None)

    if inspect.ismethod(f):
        f = f.__func__

    if inspect.isfunction(f):
        code = f.__code__
    # elif isinstance(f, types.BuiltinFunctionType):
    # ?
    else:
        return None, None, None, None

    qname = getattr(f, '__qualname__', None)

    # under pypy, builtin code object (like: [].append.__func__.__code__)
    # have no co_filename and co_firstlineno
    filepath = getattr(code, 'co_filename', None)
    ln = getattr(code, 'co_firstlineno', None)

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
