import inspect
import tokenize
from keyword import kwlist
from collections import defaultdict, OrderedDict, namedtuple
from io import BytesIO
from typing import Dict, Tuple, List

FrameInfo = namedtuple('FrameInfo',
                       ['filename', 'function', 'lineno', 'source_map',
                        'head_lns', 'line2names', 'name2lines', 'assignments'])


NON_FUNCTION_SCOPES =  ['<module>', '<lambda>', '<listcomp>']

# TODO use ints after debugging is finished
# TODO move to top level module so both here and formatting can use them
VAR = 'VAR'
KEYWORD = 'KW'
CALL = 'CALL'
OP = 'OP'
RAW = 'RAW'
COMMENT = 'COMMENT'


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
        yield inspect_tb(tb)
        tb = tb.tb_next


def inspect_tb(tb):
    """
    # all the line nrs in all returned structures are true (absolute) nrs
    """
    frame = tb.tb_frame
    lineno = tb.tb_lineno
    finfo = inspect.getframeinfo(frame)
    filename, function = finfo.filename, finfo.function
    source, startline = get_source(frame)

    source_map, line2names, name2lines, head_lns = annotate(source, startline)

    if function in NON_FUNCTION_SCOPES:
        head_lns = []

    names = name2lines.keys()
    assignments = get_vars(names, frame.f_locals, frame.f_globals)

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
    if frame.f_code.co_name in NON_FUNCTION_SCOPES:
        lines, _ = inspect.findsource(frame)
        startline = 1
    else:
        lines, startline = inspect.getsourcelines(frame)
    return lines, startline




def annotate(source_lines, line_offset=0, min_line=0, max_line=1e9):
    """

    ## goal: split each line into a list of tokens source that is
    ## however char-for-char identical to the original, with weird
    ## whitespaces and all.

    # while we're at it, we also find out where in the source the first
    # `def ... ()` statement is and where its closing bracket ends.
    # for frames

    Returns
    ----

    source_map: dict
        maps line number -> list of tokens

    name_map: dict
        maps line number -> list of variable names on that line

    head_lines: list of int


    """
    max_line_relative = min(len(source_lines), max_line-line_offset)
    tokens, head_s, head_e = _tokenize(source_lines[:max_line_relative])

    tokens_by_line = defaultdict(list)
    name2lines = defaultdict(list)
    line2names = defaultdict(list)
    for ttype, string, (sline, scol), (eline, ecol) in tokens:
        ln = sline + line_offset
        tokens_by_line[ln].append((ttype, scol, ecol, string))  ## TODO remove string here, only useful for debugging / asserting
        if ttype == VAR:
            name2lines[string].append(ln)
            line2names[ln].append(string)

    source_map = {}
    for ln, line in enumerate(source_lines):
        ln = ln + line_offset
        regions = []
        col = 0
        # import pdb; pdb.set_trace()
        for ttype, tok_start, tok_end, string in tokens_by_line[ln]:
            if tok_start > col:
                snippet = line[col:tok_start]
                regions.append((snippet, RAW, ''))  ## TODO remove string here, only useful for debugging / asserting
                col = tok_start
            snippet = line[tok_start:tok_end]
            assert snippet == string
            regions.append((snippet, ttype, string))  ## TODO remove string here, only useful for debugging / asserting
            col = tok_end

        if col < len(line):
            snippet = line[col:]
            regions.append((snippet, RAW, ''))  ## TODO remove string here, only useful for debugging / asserting

        source_map[ln] = regions

    if head_s is not None and head_e is not None:
        head_lines = list(range(head_s + line_offset, 1 + head_e + line_offset))
    else:
        head_lines = []

    return source_map, line2names, name2lines, head_lines


def _tokenize(source_lines):
    source = "".join(source_lines)

    # tokenize insists on reading from a byte buffer/file, but we
    # already have our source as a very nice string, thank you.
    # So we pack it up again:
    source_bytes = BytesIO(source.encode('utf-8')).readline
    tokenizer = tokenize.tokenize(source_bytes)

    dot_continuation = False
    was_dot_continuation = False
    was_name = False

    head_s = None
    head_e = None
    open_parens = 0
    tokens = []

    for ttype, string, (sline, scol), (eline, ecol), line in tokenizer:
        sline -= 1  # deal in line idxs, counting from 0
        eline -= 1
        if ttype != tokenize.STRING:
            assert sline == eline, "TODO... wait, what, there are multiline tokens other than strings?"

        if ttype == tokenize.NAME:
            if string in kwlist:
                tokens.append([KEYWORD, string, (sline, scol), (eline, ecol)])
                # while we're here, note the start of the call signature
                if head_s is None and string == 'def':
                    head_s = sline

            elif not dot_continuation:
                tokens.append([VAR, string, (sline, scol), (eline, ecol)])
                was_dot_continuation = False
            else:
                # this name seems to be part of an attribute lookup,
                # which we want to treat as one long name.
                prev = tokens[-1]
                extended_name = prev[1] + "." + string
                old_eline, old_ecol = prev[3]
                end_line = max(old_eline, eline)
                end_col = max(old_ecol, ecol)
                tokens[-1] = [VAR, extended_name, prev[2], (end_line, end_col)]
                dot_continuation = False
                was_dot_continuation = True
            was_name = True
        else:
            if string == '.' and was_name:
                dot_continuation = True
                continue
            elif string == '(':
                open_parens += 1
                if was_name:# and not was_dot_continuation:
                    # the name we just found is a call or a definition
                    # TODO why again are we interested in this? only to omit
                    # the function signature in our list of names? but
                    # that's not even what this catches. if we found the signature
                    # properly, we could filter there.
                    tokens[-1][0] = CALL
            elif string == ')':
                # while we're here, note the end of the call signature.
                # the parens counting is necessary because default keyword
                # args can contain '(', ')', e.g. in object instantiations.
                open_parens -= 1
                if head_e is None and open_parens == 0 and head_s is not None:
                    head_e = sline

            if ttype == tokenize.OP:
                tokens.append([OP, string, (sline, scol), (eline, ecol)])
            if ttype == tokenize.COMMENT:
                tokens.append([COMMENT, string, (sline, scol), (eline, ecol)])

            was_name = False

    return tokens, head_s, head_e

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
