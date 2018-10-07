import sys
import traceback
from keyword import kwlist
from collections import deque, defaultdict, OrderedDict
from io import BytesIO
from extraction import walk_tb, FrameInfo, UnresolvedAttribute
import extraction as ex
try:
    import numpy as np
except ImportError:
    np = False


import colorsys
import random


def printline(regions, ln=None,  **kw):

    print("%s: %s" % (ln, ' '.join(repr(tup[0]) for tup in regions)), **kw)

def print_sm(source_map):
    for ln in source_map:
        printline(source_map[ln], ln)


## TODO decide whether anything that doesn't use self needs to be in the class


class FrameFormatter():
    headline_tpl = "File %s, line %s, in %s\n"
    sourceline_tpl = "    %-3s %s"
    marked_sourceline_tpl = "--> %-3s %s"
    elipsis_tpl = " (...)\n"
    sep_vars = "    %s\n" % ('.' * 50)
    sep_source_below = ""
    var_indent = "        "
    val_tpl = var_indent + "%s = %s\n"

    def __init__(self, source_context=5, show_signature=True,
                 show_vals='context', truncate_vals=500):
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
        self._validate_args(source_context, show_vals)
        self.source_context = source_context
        self.show_vals = show_vals
        self.show_signature = show_signature
        self.truncate_vals = int(truncate_vals)
        self.colormap = {}

    def _validate_args(self, source_context, show_vals):
        if not (isinstance(source_context, int) or source_context == 'frame'):
            raise ValueError("source_context must be an integer or 'frame'.")

        valid_gv = ['frame', 'context', 'line', False]
        if show_vals not in valid_gv:
            raise ValueError("show_vals must be one of %s" % str(valid_gv))

    def format_frame(self, fi):
        if not isinstance(fi, FrameInfo):
            raise ValueError("Expected a FrameInfo tuple. "\
                             "extraction.inspect_tb() makes those.")

        return self._format_frame(fi)

    def _format_frame(self, fi):
        msg = self.headline_tpl % (fi.filename, fi.lineno, fi.function)
        source_map, assignments = self.select_scope(fi)

        if source_map:
            lines = self.format_source(source_map)
            msg += self.format_listing(lines, fi.lineno)

        if assignments:
            msg += self.format_assignments(assignments)
        return msg

    def select_scope(self, fi):
        minl, maxl = min(fi.source_map), max(fi.source_map)
        lineno = fi.lineno

        if self.source_context == 0:
            source_lines = []
        elif self.source_context == 1:
            source_lines = [lineno]
        elif self.source_context == 'frame':
            source_lines = range(minl, maxl)
        elif self.source_context > 1:
            start = max(lineno - (self.source_context - 1), 0)
            stop = lineno + 1
            start = max(start, minl)
            stop = min(stop, maxl)
            source_lines = list(range(start, stop+1))
            if self.show_signature:
                source_lines = sorted(set(source_lines) | set(fi.head_lns))
                # import pdb; pdb.set_trace()

        if source_lines:
            trimmed_source_map = self.trim_source(fi.source_map, source_lines)
        else:
            trimmed_source_map = {}

        if self.show_vals:
            if self.show_vals == 'frame':
                val_lines = range(minl, maxl)
            elif self.show_vals == 'context':
                val_lines = source_lines
            elif self.show_vals == 'line':
                val_lines = [lineno]

            visible_vars = (name for ln in val_lines
                                    for name in fi.line2names[ln]
                                        if name in fi.assignments)

            visible_assignments = OrderedDict([(n, fi.assignments[n])
                                               for n in visible_vars])
        else:
            visible_assignments = {}


        return trimmed_source_map, visible_assignments

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

    def format_assignments(self, assignments):
        msgs = []
        for name, value in assignments.items():
            val_str = self.format_value(value, indent=len(name) + 3)
            assign_str = self.val_tpl % (name, val_str)
            msgs.append(assign_str)
        msg = self.sep_vars + ''.join(msgs) + self.sep_vars + '\n'
        return msg

    def format_value(self, value, indent=0):
        if isinstance(value, UnresolvedAttribute):
            reason = "# %s: '%s'" % (value.exc_type, value.first_failed)
            val_tpl = reason + "\n%s = %s"
            lastval_str = self.format_value(value.last_resolvable_value, 3)
            val_str = val_tpl % (value.last_resolvable_name, lastval_str)
            indent = 0

        elif np and isinstance(value, np.ndarray):
            val_str = self.format_array(value)

        elif hasattr(value, '__repr__'):
            try:
                val_str = repr(value)
            except:
                val_str = "<error calling __repr__>"
        else:
            try:
                val_str = str(value)
            except:
                val_str = "<error calling __str__>"

        if self.truncate_vals and len(val_str) > (self.truncate_vals+3):
            val_str = "%s..." % val_str[:self.truncate_vals]

        nl_indented = '\n' + self.var_indent + (' ' * (indent))
        val_str = val_str.replace('\n', nl_indented)
        return val_str

    def format_array(self, arr):
        if arr.ndim >= 1:
            shape_str = repr(arr.shape)
            # shape_str = "x".join(str(d) for d in arr.shape)
            if len(shape_str) < 10:
                prefix = "%s array(" % shape_str
                msg = prefix
            else:
                prefix = ""
                msg = "%s array(\n" % shape_str
        else:
            msg = prefix = "array("

        suffix = ')'
        msg += np.array2string(arr, max_line_width=70, separator=',',
                               prefix=prefix, suffix=suffix)
        msg += suffix
        return msg



    def trim_source(self, source_map, context):
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


class InsanelyVerboseFormatter(FrameFormatter):
    def __init__(self):
        super().__init__(source_context='frame', truncate_vals=10000)

class VerboseFormatter(FrameFormatter):
    # header, 5 lines of source, vals for these lines
    def __init__(self):
        super().__init__(source_context=5, truncate_vals=500)

class TerseFormatter(FrameFormatter):
    # header, 1 line of source, vals for that one line
    def __init__(self):
        super().__init__(source_context=1, truncate_vals=70)

class MinimalFormatter(FrameFormatter):
    def __init__(self):
        super().__init__(source_context=1, show_vals=False)


class ColoredVariablesFormatter(FrameFormatter):

    highlight_val = 1.
    default_val = 0.6

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

    def _format_frame(self, fi):
        msg = self.headline_tpl % (fi.filename, fi.lineno, fi.function)
        source_map, assignments = self.select_scope(fi)

        colormap = self.pick_colors(source_map, assignments, fi.lineno)

        if source_map:  # TODO is this if necessary? what happens below with an empty sourcemap?
            lines = self.format_source(source_map, colormap, fi.lineno)
            msg += self.format_listing(lines, fi.lineno)

        msg += self.format_assignments(assignments, colormap)
        return msg

    def pick_colors(self, source_map, assignments, lineno):
        colormap = {}
        for ln in source_map:
            highlight = (ln == lineno)
            for name, ttype, _ in source_map[ln]:
                if ttype == ex.VAR and name in assignments:
                    clr = self._pick_color(name, assignments[name], highlight)
                    colormap[name] = clr
        return colormap

    def _pick_color(self, name, val, highlight=False, mode='repr'):
        if mode == 'repr':
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
                if ttype in [ex.KEYWORD, ex.OP]:
                    line += bold_tp % snippet
                elif ttype == ex.VAR:
                    if snippet not in colormap:
                        line += default_tpl % snippet
                    else:
                        hue, sat, val, bold = colormap[snippet]
                        val = self.highlight_val if (ln == lineno) else self.default_val
                        var_tpl = self.get_ansi_tpl(hue, sat, val, bold)
                        line += var_tpl % snippet
                elif ttype == ex.CALL:
                    line += bold_tp % snippet
                elif ttype == ex.COMMENT:
                    line += comment_tpl % snippet
                else:
                    line += default_tpl % snippet
            source_lines[ln] = line

        return source_lines

    def format_assignments(self, assignments, colormap):
        msgs = []
        for name, value in assignments.items():
            val_str = self.format_value(value, indent=len(name) + 3)
            assign_str = self.val_tpl % (name, val_str)
            clr_str = self.get_ansi_tpl(*colormap[name]) % assign_str
            msgs.append(clr_str)
        msg = self.sep_vars + ''.join(msgs) + self.sep_vars + '\n'
        return msg


def format_tb(frameinfos, formatter=None, terse_formatter=None, reverse_order=False):
    if formatter is None:
        formatter = VerboseFormatter()
    if terse_formatter is None:
        terse_formatter = formatter
    if not isinstance(frameinfos, list):
        frameinfos = [frameinfos]

    tb_strings = []
    for fi in frameinfos:
        # if 'site-packages' in fi.filename:
        #     tb_strings.append(terse_formatter.format_frame(fi))
        # else:
        #     tb_strings.append(formatter.format_frame(fi))

        tb_strings.append(formatter.format_frame(fi))

    if reverse_order:
        tb_strings = reversed(tb_strings)
    return "".join(tb_strings)


def format_summary(frameinfos, reverse_order=False):
    msg_inner = format_tb(frameinfos[-1], TerseFormatter(), reverse_order)
    msg_outer = format_tb(frameinfos[:-1], MinimalFormatter(), reverse_order)
    msg = [msg_outer, msg_inner]
    if reverse_order:
        msg = reversed(msg)
    return "".join(msg)


def format(etype, evalue, tb, show_full=True, show_summary=False,
           reverse_order=False, **formatter_kwargs):
    import time
    tic = time.perf_counter()
    frameinfos = list(walk_tb(tb))
    took = time.perf_counter() - tic
    timermsg = 'extraction took %s' % took*1000
    exception_msg = ' '.join(traceback.format_exception_only(etype, evalue))

    if show_summary:
        msg = format_summary(frameinfos, reverse_order)
        msg += exception_msg

    else:
        msg = ''

    if show_full:
        if show_summary:
            msg += "\n\n========== Full traceback: ==========\n"
        # formatter = VerboseFormatter(**formatter_kwargs)
        formatter = ColoredVariablesFormatter(**formatter_kwargs)
        terse_formatter = MinimalFormatter(**formatter_kwargs)

        msg += format_tb(frameinfos, formatter, terse_formatter, reverse_order)
        msg += exception_msg

    msg += 'extraction took %s' % (took*1000)
    return msg


def excepthook(etype, evalue, tb, **kwargs):
    tb_message = format(etype, evalue, tb, **kwargs)
    print(tb_message, file=sys.stderr)
