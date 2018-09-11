import sys
import inspect
import tokenize
from collections import deque, defaultdict
from keyword import kwlist
from io import BytesIO

class UndefinedName(KeyError):
    pass


class TTCore():

    def __init__(self, source_context=5, get_vals='context',
                 show_signature=True):
        """
        Params
        ---

        source_context : int or 'frame'
            nr of source lines around the last executed line to show
            0: don't get any source lines
            1: only get the final executed line
            >1: get several lines around the final line
            'frame': get the complete source of each frame

        get_vals : string 'frame' | 'context' | 'line' | None
            Selects which variable assignments to retrieve.
            'frame': get values of all names in the source of the frame.
            'context': ...only for names visible in the chosen source context
            'line': ...only for names in the last executed line ('-->')
            None|False: don't retrieve any variable values.

        show_signature : bool
            only if source_context > 1: always include the first line of code,
            (unless the frame is at the module top level).
        """

        self.n_context = source_context
        self.get_vals = get_vals
        self.show_signature = show_signature

    def walk_tb(self, tb):
        """
        Follow the call stack to the bottom, grab source lines & variable values


        Params
        ---
        tb: traceback object

        Yields
        ---
        For each frame on the way to the bottom,

        filename: str
            path to source file

        function: str
            which scope we're in

        lineno: int
            nr of the last executed line

        source_lines: list of tuples (line nr, source line)

        assignments: list of tuples (name, value)

        """
        while tb:
            frame = tb.tb_frame
            lineno = tb.tb_lineno
            finfo = inspect.getframeinfo(frame)
            filename, function = finfo.filename, finfo.function
            source, startline = get_source(frame)

            if self.n_context == 'frame':
                visible_lines = range(startline, startline+len(source))
            elif self.n_context == 0:
                visible_lines = []
            elif self.n_context == 1:
                visible_lines = [lineno]
            elif self.n_context > 1:
                start = max(lineno - (self.n_context - 1), 0)
                stop = lineno + 1
                visible_lines = list(range(start, stop+1))
                if show_signature and name != '<module>' and start > startline:
                    # TODO do the right thing for multiline signatures
                    visible_lines = [startline] + visible_lines
            else:
                raise ValueError('cant read self.n_context=%s' % self.n_context)

            assignments = []
            if get_vals:
                if get_vals == 'frame':
                    val_lines = range(startline, startline+len(source))
                elif get_vals == 'context':
                    val_lines = visible_lines
                elif get_vals == 'line':
                    val_lines = [lineno]

                names_in_line = get_name_map(source, startline, val_lines)
                for lno in val_lines:
                    for name in names_in_line[lno]:
                        try:
                            val = lookup(name, frame.f_locals, frame.f_globals)
                        except Exception as e:
                            print(name, e.__class__.__name__, e)
                            pass
                        else:
                            assignments.append((name, val))

            source_pr = self.process_source(source)
            source_lines = [(lno, source_pr[lno]) for lno in visible_lines]

            yield (filename, function, lineno, source_lines, assignments)
            tb = tb.tb_next

    def process_source(self, source_lines):
        # Override in subclasses that need to see & modify the complete source
        # of the frame, e.g. to implement syntax highlighting.
        return source_lines


class StringTB(TTCore):
    headline_tpl = "File %s, line %s in %s\n"
    sourceline_tpl = "%s%-3s %s"
    vars_separator = "    %s\n" % ('.' * 50)
    var_indent =     "\n        "
    assignment_tpl = var_indent + "%s = %s\n"

    def __init__(self, source_context=5, get_vals='context', show_signature=True):

    def excepthook(*args):
        tb_string = self.format(*args)
        print(tb_string, file=sys.stderr)


    def format(etype, evalue, tb, summary_above=False):
        exc_str = ' '.join(traceback.format_exception_only(etype, evalue))
        frame_strings = self.get_frame_strings(tb, source_context,
                                               get_vals, show_signature)

        msg = ''
        if summary_above:
            lastframe = tb_strings[-1]
            msg = "%s\n%s\n" % (exc_str, lastframe)
        msg +=  "============= Full traceback: ===========\n\n"
        msg += "\n\n".join(tb_strings)
        msg += exc_str


    def get_frame_strings(etype, evalue, tb, *args, **kwargs):
        frame_strings = []
        frame_infos = walk_tb(tb, *args, **kwargs)
        for fname, function, lineno, source_lines, assignments in frame_infos:
            msg = ""
            msg += self.headline_tpl % (fname, lineno, function)
            msg += self.format_source(source_lines, lineno)

            msg += self.vars_separator
            msg += self.format_vars(assignments)
            msg += self.vars_separator

            msg += '\n'
            frame_strings.append(msg)

        return frame_strings


    def format_source(self, source_lines, lineno):
        msg = ""
        ln_prev = None
        for ln, line in source_lines:
            if ln_prev and ln_prev != ln + 1:
                msg += "(...)\n"
            ln_prev = ln
            marker = '--> ' if ln == lineno else '    '
            msg += self.sourceline_tpl % (marker, ln, line)
        return msg

    def format_vars(self, assignments, truncate=500, truncate__=True):
        for name, value in assignments:
            if isinstance(value, str):
                val_str = value
            elif hasattr(value, '__repr__'):
                try:
                    val_str = value.__repr__()
                except:
                    val_str = "<error calling __repr__>"
            else:
                try:
                    val_str = str(value)
                except:
                    val_str = "<error calling str>"

            if truncate and len(val_str) > truncate:
                val_str = "%s..." % val_str[:truncate]
            if truncate__ and name.startswith('__') and len(val_str) > 50:
                val_str = "%s..." % val_str[:50]

            # ad hoc trickery to match up multiline reprs on the = sign
            indented_newline = '\n' + self.var_indent + (' ' * (len(name) + 2))
            val_str = val_str.replace('\n', indented_newline)

            msg += self.assignment_tpl % (name, val_str)
        return msg



class ColorTB(StringTB):
    header_tpl = "%s "  #colored version

    def process_source(self, source_lines):
        # do syntax highlighting
        pass


class PickleTB(TBFormat):
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


def get_name_map(source, line_offset=0, lines_whitelist=None, last_only=True):
    """
    get a mapping from line number to the names present in that line
    """
    names_table = get_names_table(source)

    name2lines = defaultdict(list)
    for name, sline, eline in names_table:
        sline += line_offset
        eline += line_offset
        name2lines[name].extend(list(range(sline, eline+1)))

    line2names = defaultdict(list)
    for name, line_nrs in name2lines.items():
        if last_only:
            line_nrs = [max(line_nrs)]
        for lnr in line_nrs:
            if lines_whitelist and lnr not in lines_whitelist:
                continue
            line2names[lnr].append(name)

    return line2names


def lookup(name, scopeA, scopeB):
    name, *attr_path = name.split('.')

    if name in scopeA:
        val = scopeA[name]
    elif name in scopeB:
        val = scopeB[name]
    else:
        # not all names in the source file will be
        # defined (yet) when we get to see the frame
        raise UndefinedName(name)

    for attr in attr_path:
        val = getattr(val, attr)

    return val


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

