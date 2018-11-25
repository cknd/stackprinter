import tokenize
from keyword import kwlist
from collections import defaultdict
from io import BytesIO


# TODO use ints after debugging is finished
# TODO move to separate module so both here and formatting can import * them
VAR = 'VAR'
KEYWORD = 'KW'
CALL = 'CALL'
OP = 'OP'
RAW = 'RAW'  # TODO rename to 'other' or something
COMMENT = 'COMMENT'


def _tokenize(source_lines):
    """
    Split a list of source lines into tokens

    TODO


    """

    tokenizer = tokenize.generate_tokens(iter(source_lines).__next__)
    # Dragons! This is a trick used in the `inspect` standard lib module,
    # which uses the undocumented generate_tokens() instead of the official
    # tokenize(), since that doesn't accept strings, only `readline`s.
    # So the official route would be to repackage our strings like this... :/
    #   source = "".join(source_lines)
    #   source_bytes = BytesIO(source.encode('utf-8')).readline
    #   tokenizer = tokenize.tokenize(source_bytes)


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
                # if was_name:# and not was_dot_continuation:
                #     # the name we just found is a call or a definition
                #     # TODO why again are we interested in this? only to omit
                #     # the function signature in our list of names? but
                #     # that's not even what this catches. if we found the signature
                #     # properly, we could filter it explicitely
                #     tokens[-1][0] = CALL
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



def join_broken_lines(source_lines):
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



def annotate(source_lines, line_offset=0, lineno=0, min_line=0, max_line=1e9):
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
    source_lines, lineno_corrections = join_broken_lines(source_lines)
    lineno += lineno_corrections[lineno - line_offset]

    max_line_relative = min(len(source_lines), max_line-line_offset)
    tokens, head_s, head_e = _tokenize(source_lines[:max_line_relative])

    tokens_by_line = defaultdict(list)
    name2lines = defaultdict(list)
    line2names = defaultdict(list)
    for ttype, string, (sline, scol), (eline, ecol) in tokens:
        ln = sline + line_offset
        # if sline != eline:
        #     # TODO fix multiline dot continuations. mostly a formatting issue. if all else fails, just display the value without source highlighting.
        #     print('skipping multiline token', string)
        #     continue
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

    return source_map, line2names, name2lines, head_lines, lineno
