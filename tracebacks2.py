import sys
import inspect
import tokenize
from collections import deque
from keyword import kwlist
from io import BytesIO

class UndefinedName(KeyError):
    pass

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
        line number of lines[0] in the original source file
    """
    if frame.f_code.co_name == '<module>':
        # TODO see if this is still necessary
        lines, _ = inspect.findsource(frame)
        startline = 1
    else:
        lines, startline = inspect.getsourcelines(frame)

    return lines, startline


def get_names_table(source):
    """
    get all the names in the given piece of source code, along
    with each line number where that name occurs (a name can occur
    more than one line even if appears only once in the code if
    it's writen as a multiline continuation)

    ...line idxs start with 0, i.e. they're relative to the given
    piece of code
    """
    if isinstance(source, list):
        source = "".join(source)

    # tokenize insists on reading from a byte buffer/file,
    # but we already have our source as a very nice string.
    # so we'll just have to pack it up again.
    source_bytes = BytesIO(source.encode('utf-8')).readline
    tokens = tokenize.tokenize(source_bytes)

    names_found = []
    dot_continuation = False
    was_name = False

    for ttype, token, (sline, scol), (eline, ecol), line in tokens:
        if ttype == tokenize.NAME and token not in kwlist:
            if not dot_continuation:
                names_found.append((token, sline, eline))
            else:
                # this name is part of an attribute lookup,
                # which we want to treat as one long name.
                prev = names_found[-1]
                full_name = prev[0] + "." + token
                names_found[-1] = (full_name, prev[1], max(prev[2], eline))
                dot_continuation = False
            was_name = True
        else:
            if token == '.' and was_name:
                dot_continuation = True
            elif token == '(' and was_name:
                # forget the name we just found because
                # it's a function definition / call
                names_found = names_found[:-1]
            was_name = False

    return names_found


def get_names_per_line(source, line_offset=0):
    """
    get a mapping from line number to the names present in that line
    """
    names_table = get_names_table(source)

    name2lines = {}
    for name, sline, eline in names_table:
        if name not in name2lines:
            name2lines[name] = []
        name2lines[name].extend(list(range(sline, eline+1)))

    line2names = {}
    for name, lines in name2lines.items():
        last_occurence = max(lines)
        if last_occurence not in line2names:
            line2names[last_occurence] = []
        line2names[last_occurence].append(name)

    # import pdb; pdb.set_trace()


    # names_locations = {}
    # for name, sline, eline in names_table:
    #     for idx in range(sline+line_offset, 1+eline+line_offset):
    #         if idx not in names_locations:
    #             names_locations[idx] = []
    #         names_locations[idx].append(name)

    # # prune the name list, keeping only the last occurance of each var and
    # # keeping their order.

    # endline = line_offset + len(source)
    # pruned_names = deque()
    # pruned_locs = deque()
    # for line_idx in range(endline, line_offset, -1):
    #     for name in names_locations.get(line_idx, []):
    #         if name not in pruned_names:
    #             pruned_names.appendleft(name)
    #             pruned_locs.appendleft(line_idx)
    # # import pdb; pdb.set_trace()
    # name_lookup = dict(zip(pruned_locs, pruned_names))
    return line2names


def lookup(name, f_locals, f_globals):
    name, *attr_path = name.split('.')

    if name in f_locals:
        val = f_locals[name]
    elif name in f_globals:
        val = f_globals[name]
    else:
        # not all names in the source file will be
        # defined (yet) when we get to see the frame
        raise UndefinedName(name)

    for attr in attr_path:
        val = getattr(val, attr)

    return val


def walk_tb(tb, skip=0):

    while tb:
        frame = tb.tb_frame
        lineno = tb.tb_lineno
        finfo = inspect.getframeinfo(frame)
        filename, function = finfo.filename, finfo.function
        source, startline = get_source(frame)

        line2names = get_names_per_line(source, startline)
        values = {}
        for line in range(len(source)):
            for name in line2names:
                assert name not in values
                try:
                    values[name] = lookup(name, frame.f_locals, frame.f_globals)
                except:
                    pass

        print(filename, function, source, startline, values)
        import pdb; pdb.set_trace()

        # yield (filename, function, source, startline, names_lines, values)

        # for lineidx, line in enumerate(source):
        #     lineidx += startline
        #     print(lineidx, ':    ', line, end='')
        # print('.......')
        # for lineidx, line in enumerate(source):
        #     lineidx += startline
        #     if lineidx in names:
        #         print('//', lineidx, ':    ', names[lineidx])



        # ######
        # names_in_line = get_names_per_line(source, line_offset=startline)

        # source_lines_shown =
        # []
        # if include_signature:
        #     source_lines_shown = [startline]

        # source_lines_shown.extend(range(lineno-))

        # for each line we want to show:
        #   get the names that occur
        #

        # plan:
        # - get tokens & their line nr for all source lines, maybe even deal with dotted variables
        # - find out which line nrs are in the current frame (I think `inspect` on a frame already delivers only those lines)
        #   - maybe add an option to print only the vars in the printed context lines (including function header)
        # - query locals and globals for the values, print them in order of appearance
        # do chained getattrs for dotted variables. no evals in this code!
        # - somehow visually mark the variables that are at the -->-line

        tb = tb.tb_next



def format_source():
    pass

def format_vars():
    pass

def format_frame(filename, function, source, startline, names_lines, values):
    pass


def format(etype, evalue, tb):
    frame_strs = [format_frame(*f) for f in walk_tb(tb)]



def excepthook(*args):
    tb_string = format(*args)
    print(tb_string, file=sys.stderr)



if __name__ == '__main__':
    import sys
    # from tracebacks2 import format
    import numpy as np


    outer_scope_thing = ".oOo."

    def a_broken_function(thing, otherthing=1234):
        # very long function
        # with many lines
        # and various weird variables
        X = np.zeros((5, 5))
        scoped = outer_scope_thing
        np.reshape(X,9000)
        X[0] = len(thing)
        for k in X:
            if np.sum(k) != 0:
                raise Exception('something happened')
                # more code:
                zup = 123

    def some_function(boing, zap='!'):
        thing = boing + zap
        a_broken_function(thing)

    # some_function("hello")
    try:
        some_function("hello")
    except:
        tb_string = format(*sys.exc_info())
        # print(tb_string)

