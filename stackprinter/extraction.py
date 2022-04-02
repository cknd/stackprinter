import types
import inspect
from collections import OrderedDict, namedtuple
from stackprinter.source_inspection import annotate
from stackprinter.utils import match

NON_FUNCTION_SCOPES =  ['<module>', '<lambda>', '<listcomp>']

_FrameInfo = namedtuple('_FrameInfo',
                        ['filename', 'function', 'lineno', 'source_map',
                         'head_lns', 'line2names', 'name2lines', 'assignments'])

class FrameInfo(_FrameInfo):
    # give this namedtuple type a friendlier string representation
    def __str__(self):
        return ("<FrameInfo %s, line %s, scope %s>" %
                (self.filename, self.lineno, self.function))


def get_info(tb_or_frame, lineno=None, suppressed_vars=[]):
    """
    Get a frame representation that's easy to format


    Params
    ---
    tb: Traceback object or Frame object

    lineno: int (optional)
        Override which source line is treated as the important one. For trace-
        back objects this defaults to the last executed line (tb.tb_lineno).
        For frame objects, it defaults the currently executed one (fr.f_lineno).


    Returns
    ---
    FrameInfo, a named tuple with the following fields:

         filename: Path of the executed source file

         function: Name of the scope

         lineno: Highlighted line (last executed line)

         source_map: OrderedDict
            Maps line numbers to a list of tokens. Each token is a (string, type)
            tuple. Concatenating the first elements of all tokens of all lines
            restores the original source, weird whitespaces/indentations and all
            (in contrast to python's built-in `tokenize`). However, multiline
            statements (those with a trailing backslash) are secretly collapsed
            into their first line.

         head_lns: (int, int) or (None, None)
            Line numbers of the beginning and end of the function header

         line2names: dict
            Maps each line number to a list of variables names that occur there

         name2lines: dict
            Maps each variable name to a list of line numbers where it occurs

         assignments: OrderedDict
            Holds current values of all variables that occur in the source and
            are found in the given frame's locals or globals. Attribute lookups
            with dot notation are treated as one variable, so if `self.foo.zup`
            occurs in the source, this dict will get a key 'self.foo.zup' that
            holds the fully resolved value.
            (TODO: it would be easy to return the whole attribute lookup chain,
            so maybe just do that & let formatting decide which parts to show?)
            (TODO: Support []-lookups just like . lookups)
    """

    if isinstance(tb_or_frame, FrameInfo):
        return tb_or_frame

    if isinstance(tb_or_frame, types.TracebackType):
        tb = tb_or_frame
        lineno = tb.tb_lineno if lineno is None else lineno
        frame = tb.tb_frame
    elif isinstance(tb_or_frame, types.FrameType):
        frame = tb_or_frame
        lineno = frame.f_lineno if lineno is None else lineno
    else:
        raise ValueError('Cant inspect this: ' + repr(tb_or_frame))

    filename = inspect.getsourcefile(frame) or inspect.getfile(frame)
    function = frame.f_code.co_name

    try:
        source, startline = get_source(frame)
        # this can be slow (tens of ms) the first time it is called, since
        # inspect.get_source internally calls inspect.getmodule, for no
        # other purpose than updating the linecache. seems like a bad tradeoff
        # for our case, but this is not the time & place to fork `inspect`.
    except:
        source = []
        startline = lineno

    source_map, line2names, name2lines, head_lns, lineno = annotate(source, startline, lineno)

    if function in NON_FUNCTION_SCOPES:
        head_lns = []

    names = name2lines.keys()
    assignments = get_vars(names, frame.f_locals, frame.f_globals, suppressed_vars)

    finfo =  FrameInfo(filename, function, lineno, source_map, head_lns,
                       line2names, name2lines, assignments)
    return finfo


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

    # TODO find out what's faster: Allowing inspect's getsourcelines
    # to tokenize the whole file to find the surrounding code block,
    # or getting the whole file quickly via linecache & feeding all
    # of it to our own instance of tokenize, then clipping to
    # desired context afterwards.

    if frame.f_code.co_name in NON_FUNCTION_SCOPES:
        lines, _ = inspect.findsource(frame)
        startline = 1
    else:
        lines, startline = inspect.getsourcelines(frame)

    return lines, startline


def get_vars(names, loc, glob, suppressed_vars):
    assignments = []
    for name in names:
        if match(name, suppressed_vars):
            assignments.append((name, CensoredVariable()))
        else:
            try:
                val = lookup(name, loc, glob)
            except LookupError:
                pass
            else:
                assignments.append((name, val))
    return OrderedDict(assignments)


def lookup(name, scopeA, scopeB):
    basename, *attr_path = name.split('.')
    if basename in scopeA:
        val = scopeA[basename]
    elif basename in scopeB:
        val = scopeB[basename]
    else:
        # not all names in the source file will be
        # defined (yet) when we get to see the frame
        raise LookupError(basename)

    for k, attr in enumerate(attr_path):
        try:
            val = getattr(val, attr)
        except Exception as e:
            # return a special value in case of lookup errors
            # (note: getattr can raise anything, e.g. if a complex
            # @property fails).
            return UnresolvedAttribute(basename, attr_path, k, val,
                                       e.__class__.__name__, str(e))
    return val


class CensoredVariable():
    def __repr__(self):
        return "*****"

class UnresolvedAttribute():
    """
    Container value for failed dot attribute lookups
    """
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
