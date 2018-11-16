import sys
import traceback
import extraction as ex
import source_inspection as sc
from collections import OrderedDict
from prettyprinting import format_value
from utils import inspect_callable

import colorsys
import random



def trim_source(source_map, context):
    # print('UNPROCESSED:')
    # print_sm(source_map)
    # print('--\n\n')
    indent_type = None
    min_indent = 9000
    for ln in context:
        (snippet0, *meta0), *remaining_line = source_map[ln]

        # printline(source_map[ln], ln)

        if snippet0.startswith('\t'):
            if indent_type == ' ':
                raise Exception('expected tabs')  # TODO remove
                # Mixed tabs and spaces - not trimming whitespace.
                return source_map
            else:
                indent_type = '\t'
        elif snippet0.startswith(' '):
            if indent_type == '\t':
                # Mixed tabs and spaces - not trimming whitespace.
                raise Exception('expected spaces') # TODO remove
                return source_map
            else:
                indent_type = ' '
        elif snippet0.startswith('\n'):
            continue

        n_nonwhite = len(snippet0.lstrip(' \t'))
        indent = len(snippet0) - n_nonwhite
        # import pdb; pdb.set_trace()
        min_indent = min(indent, min_indent)

    trimmed_source_map = OrderedDict()
    for ln in context:
        (snippet0, *meta0), *remaining_line = source_map[ln]
        if not snippet0.startswith('\n'):
            snippet0 = snippet0[min_indent:]
        trimmed_source_map[ln] = [[snippet0] + meta0] + remaining_line

    # print('PROCESSED')
    # print_sm(trimmed_source_map)
    # import pdb; pdb.set_trace()


    return trimmed_source_map


# todo remove these - they're just for debug
def printline(regions, ln=None,  **kw):
    print("%s: %s" % (ln, ' '.join(repr(tup[0]) for tup in regions)), **kw)

def print_sm(source_map):
    for ln in source_map:
        printline(source_map[ln], ln)


def select_scope(fi, source_context, show_vals, show_signature, filter=None):
    source_lines = []
    minl, maxl = 0, 0
    if len(fi.source_map) > 0:
        minl, maxl = min(fi.source_map), max(fi.source_map)
        lineno = fi.lineno

        if source_context == 0:
            source_lines = []
        elif source_context == 1:
            source_lines = [lineno]
        elif source_context == 'frame':
            source_lines = range(minl, maxl)
        elif source_context > 1:
            start = max(lineno - (source_context - 1), 0)
            stop = lineno + 1
            start = max(start, minl)
            stop = min(stop, maxl)
            source_lines = list(range(start, stop+1))
            if show_signature:
                source_lines = sorted(set(source_lines) | set(fi.head_lns))

    if source_lines:
        trimmed_source_map = trim_source(fi.source_map, source_lines)
    else:
        trimmed_source_map = {}

    if show_vals:
        if show_vals == 'frame':
            val_lines = range(minl, maxl)
        elif show_vals == 'context':
            val_lines = source_lines
        elif show_vals == 'line':
            val_lines = [lineno]


        def hidden(name):
            # todo replace by boolean filter function (name, value) -> bool passed as argument

            value = fi.assignments[name]
            # print(repr(value))
            # import pdb; pdb.set_trace()

            # TODO allow hiding functions & modules whose code lives
            # in the verbosity_blacklist (e.g. site-packages)
            if callable(value):
                qualified_name = inspect_callable(value)[0]
                is_boring = (qualified_name == name)
                return is_boring
            return False


        visible_vars = (name for ln in val_lines
                                for name in fi.line2names[ln]
                                    if name in fi.assignments)

        visible_assignments = OrderedDict([(n, fi.assignments[n])
                                           for n in visible_vars
                                               if not hidden(n)])
    else:
        visible_assignments = {}


    return trimmed_source_map, visible_assignments


## TODO decide whether anything that doesn't use self needs to be in the class


class FrameFormatter():
    headline_tpl = "File %s, line %s, in %s\n"
    sourceline_tpl = "    %-3s %s"
    marked_sourceline_tpl = "--> %-3s %s"
    elipsis_tpl = " (...)\n"
    sep_vars = "    %s\n" % ('.' * 50)
    sep_source_below = ""
    var_indent = 8 #"        "
    val_tpl = ' ' * var_indent + "%s = %s\n"

    def __init__(self,
                # source_context=5, show_signature=True,
                #  show_vals='context', truncate_vals=500
                 ):
        """
        Params
        ---

        source_context : int or 'frame'
            nr of source lines around the last executed line to show:
            0: don't show any source lines
            1: only show the final executed line of each frame (the '-->' line)
            >1: show several lines around the final line
            'frame': show the complete source of each frame

        show_vals : string 'frame' | 'context' | 'line' | False
            Selects which variable assignments to show:
            'frame': show values of all variables in each frame's source
            'context': ...only those in the source context (as chosen above)
            'line': ...only those in the final line of each frame ('-->')
            None|False: don't retrieve any variable values.

        show_signature : bool
            only if source_context > 1: always show the first source line,
            (unless the frame is at the module top level).

        summary_above : bool
            TODO

        truncate_vals : int or False
            cut string representations of variable values to this maximum length

        """
        # self._validate_args(source_context, show_vals)
        # self.source_context = source_context
        # self.show_vals = show_vals
        # self.show_signature = show_signature
        # self.truncate_vals = int(truncate_vals)
        self.colormap = {}


    def _validate_args(self, fi, source_context, show_vals):
        if not isinstance(fi, ex.FrameInfo):
            raise ValueError("Expected a FrameInfo tuple, got %s" % fi)

        if not (isinstance(source_context, int) or source_context == 'frame'):
            raise ValueError("source_context must be an integer or 'frame'"
                             ", was %s" % source_context)

        valid_gv = ['frame', 'context', 'line', False]
        if show_vals not in valid_gv:
            raise ValueError("show_vals must be one of "
                             "%s, was %s" % (str(valid_gv), show_vals))


    def format_frame(self, fi, source_context=5, show_vals='context',
                     show_signature=True, truncate_vals=500):
        """ TODO """
        self._validate_args(fi, source_context, show_vals)
        return self._format_frame(fi, source_context, show_vals,
                                  show_signature, truncate_vals)


    def _format_frame(self, fi, source_context, show_vals,
                      show_signature, truncate_vals):
        msg = self.headline_tpl % (fi.filename, fi.lineno, fi.function)
        source_map, assignments = select_scope(fi, source_context,
                                               show_vals, show_signature)

        if source_map:
            lines = self.format_source(source_map)
            msg += self.format_listing(lines, fi.lineno)

        msg += self.format_assignments(assignments, truncate_vals)
        return msg

    def format_source(self, source_map):
        lines = OrderedDict()
        for ln in sorted(source_map):
            lines[ln] = ''.join(st for st, _, _ in source_map[ln])
        return lines

    def format_listing(self, lines, lineno):
        ln_prev = None
        msg = ""
        for ln in sorted(lines):
            line = lines[ln]
            if ln_prev and ln_prev != ln - 1:
                msg += self.elipsis_tpl
            ln_prev = ln

            if ln == lineno:
                tpl = self.marked_sourceline_tpl
            else:
                tpl = self.sourceline_tpl
            msg += tpl % (ln, line)

        msg += self.sep_source_below
        return msg

    def format_assignments(self, assignments, truncate=500):
        msgs = []
        for name, value in assignments.items():
            val_str = format_value(value,
                                   indent=len(name) + self.var_indent + 3,
                                   truncate=truncate)
            assign_str = self.val_tpl % (name, val_str)
            msgs.append(assign_str)
        if len(msgs) > 0:
            return self.sep_vars + ''.join(msgs) + self.sep_vars + '\n'
        else:
            return ''



# class InsanelyVerboseFormatter(FrameFormatter):
#     def __init__(self):
#         super().__init__(source_context='frame', truncate_vals=10000)

# class VerboseFormatter(FrameFormatter):
#     # header, 5 lines of source, vals for these lines
#     def __init__(self):
#         super().__init__(source_context=5, truncate_vals=500)

# class TerseFormatter(FrameFormatter):
#     # header, 1 line of source, vals for that one line
#     def __init__(self):
#         super().__init__(source_context=1, truncate_vals=70)

# class MinimalFormatter(FrameFormatter):
#     def __init__(self):
#         super().__init__(source_context=1, show_vals=False)


class ColoredVariablesFormatter(FrameFormatter):

    highlight_val = 1.
    default_val = 0.5

    def __init__(self, *args, **kwargs):
        self.rng = random.Random()
        bright = self.get_ansi_tpl(0, 0, 1., True)
        medium = self.get_ansi_tpl(0, 0, 0.7, True)
        darker = self.get_ansi_tpl(0, 0, 0.4, False)
        dark = self.get_ansi_tpl(0, 0, 0.1, True)
        self.headline_tpl = bright % super().headline_tpl
        self.sourceline_tpl = dark % super().sourceline_tpl
        self.marked_sourceline_tpl = medium % super().marked_sourceline_tpl
        self.elipsis_tpl = darker % super().elipsis_tpl
        self.sep_vars = darker % super().sep_vars
        super().__init__(*args, **kwargs)

    def _format_frame(self, fi, source_context, show_vals,
                      show_signature, truncate):
        msg = self.headline_tpl % (fi.filename, fi.lineno, fi.function)
        source_map, assignments = select_scope(fi, source_context,
                                               show_vals, show_signature)

        colormap = self.pick_colors(source_map, assignments, fi.lineno)

        if source_map:  # TODO is this if necessary? what happens below with an empty sourcemap?
            lines = self.format_source(source_map, colormap, fi.lineno)
            msg += self.format_listing(lines, fi.lineno)

        msg += self.format_assignments(assignments, colormap, truncate)
        return msg

    def pick_colors(self, source_map, assignments, lineno):
        # TODO refactor: pick a hash for each name across frames, _then_ color.
        # This allows an arbitrary color picking rule (no just the seed based one),
        # which in turn allows an explicit solution to avoid color clashes within
        # a frame. This will end up being a small constraint satisfaction problem..
        colormap = {}
        for ln in source_map:
            highlight = (ln == lineno)
            for name, ttype, string in source_map[ln]:
                if ttype == sc.VAR and name in assignments:
                    value = assignments[name]
                    clr = self._pick_color(name, value, highlight)
                    colormap[name] = clr
        return colormap

    def _pick_color(self, name, val, highlight=False, mode='id'):
        if mode == 'formatted':
            seed = format_value(val)
        elif mode == 'repr':
            seed = repr(val)
        elif mode == 'id':
            seed = id(val)
        elif mode == 'name':
            seed = name
        else:
            raise ValueError('Unkwnown color mode: %s' % mode)

        self.rng.seed(seed)
        hue = self.rng.uniform(-0.05,0.66)
        if hue < 0:
            hue = hue + 1
        sat = 1.
        val = self.highlight_val if highlight else self.default_val
        return (hue, sat, val, highlight)

    def get_ansi_tpl(self, hue, sat, val, bold=False):
        r, g, b = colorsys.hsv_to_rgb(hue, sat, val)
        r = int(round(r*5))
        g = int(round(g*5))
        b = int(round(b*5))
        point = 16 + 36 * r + 6 * g + b
        bold_tp = '1;' if bold else ''
        code_tpl = ('\u001b[%s38;5;%dm' % (bold_tp, point)) + '%s\u001b[0m'
        return code_tpl

    def format_source(self, source_map, colormap, lineno):
        bold_tp =     self.get_ansi_tpl(0.,0.,1., True)
        default_tpl = self.get_ansi_tpl(0.,0.,0.7, False)
        comment_tpl = self.get_ansi_tpl(0.,0.,0.2, False)

        source_lines = OrderedDict()
        for ln in source_map:
            line = ''
            for snippet, ttype, _ in source_map[ln]:
                if ttype in [sc.KEYWORD, sc.OP]:
                    line += bold_tp % snippet
                elif ttype == sc.VAR:
                    if snippet not in colormap:
                        line += default_tpl % snippet
                    else:
                        hue, sat, val, bold = colormap[snippet]
                        val = self.highlight_val if (ln == lineno) else self.default_val
                        var_tpl = self.get_ansi_tpl(hue, sat, val, bold)
                        line += var_tpl % snippet
                elif ttype == sc.CALL:
                    line += bold_tp % snippet
                elif ttype == sc.COMMENT:
                    line += comment_tpl % snippet
                else:
                    line += default_tpl % snippet
            source_lines[ln] = line

        return source_lines

    def format_assignments(self, assignments, colormap, truncate=500):
        msgs = []
        for name, value in assignments.items():
            val_str = format_value(value,
                                   indent=len(name) + self.var_indent + 3,
                                   truncate=truncate)
            assign_str = self.val_tpl % (name, val_str)
            clr_str = self.get_ansi_tpl(*colormap[name]) % assign_str
            msgs.append(clr_str)

        if len(msgs) > 0:
            return self.sep_vars + ''.join(msgs) + self.sep_vars + '\n'
        else:
            return ''


def format_tb(frameinfos, formatter=None, reverse_order=False):
    if formatter is None:
        formatter = FrameFormatter()

    if not isinstance(frameinfos, list):
        frameinfos = [frameinfos]

    tb_strings = []
    for fi in frameinfos:
        if False: #'site-packages' in fi.filename:
            tb_strings.append(formatter.format_frame(fi, source_context=1, show_vals=False, show_signature=False))
        else:
            tb_strings.append(formatter.format_frame(fi, source_context=15))

    if reverse_order:
        tb_strings = reversed(tb_strings)
    return "".join(tb_strings)


# def format_summary(frameinfos, reverse_order=False):
#     msg_inner = format_tb(frameinfos[-1], TerseFormatter(), reverse_order)
#     msg_outer = format_tb(frameinfos[:-1], MinimalFormatter(), reverse_order)
#     msg = [msg_outer, msg_inner]
#     if reverse_order:
#         msg = reversed(msg)
#     return "".join(msg)


def format(etype, evalue, tb, show_full=True, show_summary=False,
           reverse_order=False, **formatter_kwargs):
    import time
    tice = time.perf_counter()
    frameinfos = list(ex.walk_tb(tb))
    tooke = time.perf_counter() - tice


    import time; tic = time.perf_counter()
    exception_msg = ' '.join(traceback.format_exception_only(etype, evalue))

    if show_summary:
        msg = format_summary(frameinfos, reverse_order)
        msg += exception_msg

    else:
        msg = ''

    if show_full:
        if show_summary:
            msg += "\n\n========== Full traceback: ==========\n"
        # formatter = FrameFormatter(**formatter_kwargs)
        formatter = ColoredVariablesFormatter(**formatter_kwargs)
        msg += format_tb(frameinfos, formatter, reverse_order)
        msg += exception_msg

    msg += 'extraction took %s\n' % (tooke*1000)
    msg += 'formating took %s' % ((time.perf_counter() - tic) * 1000)
    return msg


def excepthook(etype, evalue, tb, **kwargs):
    tb_message = format(etype, evalue, tb, **kwargs)
    print(tb_message, file=sys.stderr)
