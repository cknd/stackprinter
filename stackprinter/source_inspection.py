import tokenize
import warnings
from keyword import kwlist
from collections import defaultdict

RAW = 'RAW'
COMMENT = 'COMM'
VAR = 'VAR'
KEYWORD = 'KW'
CALL = 'CALL'
OP = 'OP'


def annotate(source_lines, line_offset=0, lineno=0, max_line=2**15):
    """
    Find out where in a piece of code which variables live.

    This tokenizes the source, maps out where the variables occur, and, weirdly,
    collapses any multiline continuations (i.e. lines ending with a backslash).


    Params
    ---
    line_offset: int
        line number of the first element of source_lines in the original file

    lineno: int
        A line number you're especially interested in. If this line moves around
        while treating multiline statements, the corrected nr will be returned.
        Otherwise, the given nr will be returned.

    max_line: int
        Stop analysing after this many lines

    Returns
    ---
     source_map: OrderedDict
        Maps line numbers to a list of tokens. Each token is a (string, TYPE)
        tuple. Concatenating the first elements of all tokens of all lines
        restores the original source, weird whitespaces/indentations and all
        (in contrast to python's built-in `tokenize`). However, multiline
        statements (those with a trailing backslash) are secretly collapsed
        into their first line.

     line2names: dict
        Maps each line number to a list of variables names that occur there

     name2lines: dict
        Maps each variable name to a list of line numbers where it occurs

     head_lns: (int, int) or (None, None)
        Line numbers of the beginning and end of the function header

     lineno: int
        identical to the supplied argument lineno, unless that line had to be
        moved when collapsing a backslash-continued multiline statement.
    """
    if not source_lines:
        return {}, {}, {}, [], lineno

    assert isinstance(line_offset, int)
    assert isinstance(lineno, int)
    assert isinstance(max_line, int)

    source_lines, lineno_corrections = join_broken_lines(source_lines)
    lineno += lineno_corrections[lineno - line_offset]

    max_line_relative = min(len(source_lines), max_line-line_offset)
    tokens, head_s, head_e = _tokenize(source_lines[:max_line_relative])

    tokens_by_line = defaultdict(list)
    name2lines = defaultdict(list)
    line2names = defaultdict(list)
    for ttype, string, (sline, scol), (eline, ecol) in tokens:
        ln = sline + line_offset
        tokens_by_line[ln].append((ttype, scol, ecol, string))
        if ttype == VAR:
            name2lines[string].append(ln)
            line2names[ln].append(string)

    source_map = {}
    for ln, line in enumerate(source_lines):
        ln = ln + line_offset
        regions = []
        col = 0
        for ttype, tok_start, tok_end, string in tokens_by_line[ln]:
            if tok_start > col:
                snippet = line[col:tok_start]
                regions.append((snippet, RAW))
                col = tok_start
            snippet = line[tok_start:tok_end]
            if snippet != string:
                msg = ("Token %r doesn't match raw source %r"
                       " in line %s: %r" % (string, snippet, ln, line))
                warnings.warn(msg)
            regions.append((snippet, ttype))
            col = tok_end

        if col < len(line):
            snippet = line[col:]
            regions.append((snippet, RAW))

        source_map[ln] = regions

    if head_s is not None and head_e is not None:
        head_lines = list(range(head_s + line_offset, 1 + head_e + line_offset))
    else:
        head_lines = []

    return source_map, line2names, name2lines, head_lines, lineno


def _tokenize(source_lines):
    """
    Split a list of source lines into tokens

    Params
    ---
    source_lines: list of str

    Returns
    ---

    list of tokens, each a list of this format:
        [TOKENTYPE, 'string', (startline, startcolumn), (endline, endcol)]

    """

    tokenizer = tokenize.generate_tokens(iter(source_lines).__next__)
    # Dragons! This is a trick from the `inspect` standard lib module: Using the
    # undocumented method generate_tokens() instead of the official tokenize(),
    # since the latter doesn't accept strings (only `readline()`s). The official
    # way would be to repackage our list of strings, something like this.. :(
    #   source = "".join(source_lines)
    #   source_bytes = BytesIO(source.encode('utf-8')).readline
    #   tokenizer = tokenize.tokenize(source_bytes)

    tokens = []

    dot_continuation = False
    was_name = False
    open_parens = 0

    head_s = None
    head_e = None
    name_end = -2
    for ttype, string, (sline, scol), (eline, ecol), line in tokenizer:
        sline -= 1  # we deal in line indices counting from 0
        eline -= 1
        if ttype != tokenize.STRING:
            assert sline == eline, "Can't accept non-string multiline tokens"

        if ttype == tokenize.NAME:
            if string in kwlist:
                tokens.append([KEYWORD, string, (sline, scol), (eline, ecol)])
                if head_s is None and string == 'def':
                    # while we're here, note the start of the call signature
                    head_s = sline

            elif not dot_continuation:
                tokens.append([VAR, string, (sline, scol), (eline, ecol)])
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
            was_name = True
            name_end = ecol - 1
        else:
            if string == '.' and was_name and scol == name_end + 1:
                dot_continuation = True
                continue
            elif string == '(':
                open_parens += 1
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
            name_end = -2

    # TODO: proper handling of keyword argument assignments: left hand sides
    # should be treated as variables _only_ in the header of the current
    # function, and outside of calls, but not when calling other functions...
    # this is getting silly.
    return tokens, head_s, head_e


def join_broken_lines(source_lines):
    """
    Collapse backslash-continued lines into the first (upper) line
    """

    # TODO meditate whether this is a good idea

    n_lines = len(source_lines)
    unbroken_lines = []
    k = 0
    lineno_corrections = defaultdict(lambda: 0)
    while k < n_lines:
        line = source_lines[k]

        gobbled_lines = []
        while (line.endswith('\\\n')
               and k + 1 < n_lines
               and line.lstrip()[0] != '#'):
            k_continued = k
            k += 1
            nextline = source_lines[k]
            nextline_stripped = nextline.lstrip()
            line = line[:-2] + nextline_stripped

            indent = ''
            n_raw, n_stripped = len(nextline), len(nextline_stripped)
            if n_raw != n_stripped:
                white_char = nextline[0]
                fudge = 3 if white_char == ' ' else 0
                indent = white_char * max(0, (n_raw - n_stripped - fudge))

            gobbled_lines.append(indent + "\n" )
            lineno_corrections[k] = k_continued - k

        unbroken_lines.append(line)
        unbroken_lines.extend(gobbled_lines)
        k += 1

    return unbroken_lines, lineno_corrections


