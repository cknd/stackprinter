# TODO / Idea: Support [] lookups just like . lookups
import types
import inspect
from source_inspection import annotate
from collections import OrderedDict, namedtuple

FrameInfo = namedtuple('FrameInfo',
                       ['filename', 'function', 'lineno', 'source_map',
                        'head_lns', 'line2names', 'name2lines', 'assignments'])


NON_FUNCTION_SCOPES =  ['<module>', '<lambda>', '<listcomp>']


def get_source(frame):
    """
    get source lines for this frame

    Params
    ---
    frame : frame object

    Returns
    ---
    lines : list of str

    startline : int
        location of lines[0] in the original source file
    """

    # import pdb; pdb.set_trace()


    # TODO use a raw linecache method that doesnt secretely tokenize
    # the whole source just to find the interesting block, as inspect does

    if frame.f_code.co_name in NON_FUNCTION_SCOPES:
        # import time; tic = time.perf_counter()
        lines, _ = inspect.findsource(frame)
        # print(frame.f_code.co_name, (time.perf_counter() - tic) * 1000)
        startline = 1
    else:
        lines, startline = inspect.getsourcelines(frame)

    # lc_lines = linecache.getlines(frame.f_code.co_filename)

    # find where in the linecache lines the lines from inspect show up
    # idxs = []
    # for line in lines:
    #     idxs.append(lc_lines.index(line))

    # lcl_filtered = [lc_lines[i] for i in idxs]
    # print(lcl_filtered == lines)
    # import pdb; pdb.set_trace()
    return lines, startline



def walk_tb(tb):
    """
    Follow the call stack, collecting source lines & variable values


    Params
    ---
    tb: traceback object

    Yields
    ---

    TODO
    """
    while tb:
        yield inspect_frame(tb)
        tb = tb.tb_next


def inspect_frame(tb):
    """
    # all the line nrs in all returned structures are true (absolute) nrs
    """
    if isinstance(tb, types.TracebackType):
        lineno = tb.tb_lineno
        frame = tb.tb_frame
    elif isinstance(tb, types.FrameType):
        frame = tb
        lineno = frame.f_lineno
    else:
        raise ValueError('Cant inspect this: ' + repr(tb))

    filename = inspect.getsourcefile(frame) or inspect.getfile(frame)
    function = frame.f_code.co_name

    # import linecache
    # import re
    # source = linecache.getlines(filename)
    # lnum = tb.tb_frame.f_code.co_firstlineno

    # # from inspect
    # lines = source
    # lnum = tb.tb_frame.f_code.co_firstlineno - 1
    # pat = re.compile(r'^(\s*def\s)|(\s*async\s+def\s)|(.*(?<!\w)lambda(:|\s))|^(\s*@)')
    # while lnum > 0:
    #     if pat.match(lines[lnum]): break
    #     lnum = lnum - 1
    # ...
    # startline = lnum

    import time; tic = time.perf_counter()
    try:
        source, startline = get_source(frame)  # can be slow for modules the first time, because getmodule, which seems to do nothing except update the line cache
    except:
        source = ["# no source code found\n"]
        startline = lineno

    print((time.perf_counter() - tic) * 1000)

    source_map, line2names, name2lines, head_lns, lineno = annotate(source, startline, lineno)

    if function in NON_FUNCTION_SCOPES:
        head_lns = []

    names = name2lines.keys()
    assignments = get_vars(names, frame.f_locals, frame.f_globals)

    finfo =  FrameInfo(filename, function, lineno, source_map, head_lns,
                       line2names, name2lines, assignments)


    return finfo



def get_vars(names, loc, glob):
    assignments = []
    for name in names:
        try:
            val = lookup(name, loc, glob)
        except UndefinedName:
            pass
        else:
            assignments.append((name, val))
    return OrderedDict(assignments)


class UndefinedName(KeyError):
    pass

class UnresolvedAttribute():
    def __init__(self, basename, attr_path, failure_idx, value,
                exc_type, exc_str):
        self.basename = basename
        self.attr_path = attr_path
        self.first_failed = attr_path[failure_idx]
        self.failure_idx = failure_idx
        self.last_resolvable_value = value
        self.exc_type = exc_type
        self.exc_str = exc_str

    @property
    def last_resolvable_name(self):
        return self.basename + '.'.join([''] + self.attr_path[:self.failure_idx])


def lookup(name, scopeA, scopeB):
    basename, *attr_path = name.split('.')
    if basename in scopeA:
        val = scopeA[basename]
    elif basename in scopeB:
        val = scopeB[basename]
    else:
        # not all names in the source file will be
        # defined (yet) when we get to see the frame
        raise UndefinedName(basename)

    for k, attr in enumerate(attr_path):
        try:
            val = getattr(val, attr)
        except Exception as e:
            return UnresolvedAttribute(basename, attr_path, k, val,
                                       e.__class__.__name__, str(e))


    return val
