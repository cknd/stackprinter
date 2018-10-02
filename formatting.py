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


## TODO decide whether anything that doesn't use self needs to be in the class


class FrameFormatter():
    headline_tpl = "File %s, line %s, in %s\n"
    sourceline_tpl = "    %-3s %s"
    marked_sourceline_tpl = "--> %-3s %s"

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

        msg = self.headline_tpl % (fi.filename, fi.lineno, fi.function)
        source_context, val_context = self.select_visible_lines(fi)

        if source_context:
            source_lines = self.format_source(fi.source_map, source_context, fi.lineno)
            msg += self.format_listing(source_lines, fi.lineno, source_context)

        if val_context:
            visible_names = set(name for ln in val_context
                                        for name in fi.line2names[ln])
            msg += self.sep_vars
            msg += self.format_vars(fi.assignments, visible_names)
            msg += self.sep_vars
            msg += '\n'

        return msg

    def select_visible_lines(self, fi):
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

        # for ln in source_lines:
        #     print(ln, ''.join(ch[0] for ch in fi.source_map[ln]), end='')
        # print('---', fi.lineno)
        # import pdb; pdb.set_trace()

        if self.show_vals:
            if self.show_vals == 'frame':
                val_lines = range(minl, maxl)
            elif self.show_vals == 'context':
                val_lines = source_lines
            elif self.show_vals == 'line':
                val_lines = [lineno]
        else:
            val_lines = []
        return source_lines, val_lines

    def format_source(self, source_map, context, lineno):
        source_lines = OrderedDict()
        for ln in context:
            line = ''.join(snippet for snippet, ttype, _ in source_map[ln])
            source_lines[ln] = line
        return source_lines

    def format_listing(self, source_lines, lineno, context):
        lines = [source_lines[ln] for ln in context]
        lines = self.trim_whitespace(lines)

        n_context = len(context)
        ln_prev = None
        msg = ""

        for ln, line in zip(context, lines):
            if ln_prev and ln_prev != ln - 1:
                msg += "(...)\n"
            ln_prev = ln
            if n_context > 1:
                if ln == lineno:
                    tpl = self.marked_sourceline_tpl
                else:
                    tpl = self.sourceline_tpl
                msg += tpl % (ln, line)
            else:
                msg = '   ' + line

        msg += self.sep_source_below
        return msg

    def format_vars(self, assignments, visible_names):
        msgs = []
        for name, value in assignments.items():
            if name in visible_names:
                msgs.append(self.format_assignment(name, value))
        msg = ''.join(msgs)
        return msg

    def format_assignment(self, name, value):
        val_str = self.format_value(name, value)
        return self.val_tpl % (name, val_str)

    def format_value(self, name, value):
        indent = len(name) + 3


        if isinstance(value, UnresolvedAttribute):
            reason = "# %s: '%s'" % (value.exc_type, value.first_failed)
            val_tpl = reason + "\n%s = %s"
            lastval_str = self.format_value('   ', value.last_resolvable_value)
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
            shape_str = "x".join(str(d) for d in arr.shape)
            if len(shape_str) < 10:
                prefix = shape_str + " array("
                msg = prefix
            else:
                prefix = ""
                msg = shape_str + " array(\n"
        else:
            msg = prefix = "array("

        suffix = ')'
        msg += np.array2string(arr, max_line_width=70, separator=',',
                               prefix=prefix, suffix=suffix)
        msg += suffix
        return msg

    def trim_whitespace(self, lines):
        # TODO move to utils
        min_padding = 9000
        for line in lines:
            line = line.replace('\t', '    ')
            n_nonwhite = len(line.lstrip())
            if n_nonwhite > 0:
                leading_spaces = len(line) - n_nonwhite
                min_padding = min(leading_spaces, min_padding)
        pad = ' ' * min_padding
        return [line.replace(pad, '', 1) for line in lines]


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

    def __init__(self, *args, **kwargs):
        self.rng = random.Random()
        main_tpl_b = self.get_ansi_tpl(0.35, 0., 1., True)
        main_tpl_n = self.get_ansi_tpl(0.35, 0., 0.5, False)
        self.headline_tpl = main_tpl_b % super().headline_tpl
        self.sourceline_tpl = main_tpl_n % super().sourceline_tpl
        self.marked_sourceline_tpl = main_tpl_b % super().marked_sourceline_tpl
        self.sep_vars = main_tpl_n % super().sep_vars
        super().__init__(*args, **kwargs)

    def pick_color(self, name):
        self.rng.seed(name)
        hue = self.rng.uniform(0,1.)
        sat = 1.0
        val = 1.0
        return (hue, sat, val)

    def get_ansi_tpl(self, hue, sat, val, bold=False):
        r, g, b = colorsys.hsv_to_rgb(hue, sat, val)
        r = int(round(r*5))
        g = int(round(g*5))
        b = int(round(b*5))
        point = 16 + 36 * r + 6 * g + b
        bold_tp = '1;' if bold else ''
        code_tpl = ('\u001b[%s38;5;%dm' % (bold_tp, point)) + '%s\u001b[0m'
        return code_tpl

    # def get_ansi_color_tpl(self, name, highlight):
    #     if name in kwlist:
    #         hue, sat, val = 0., 0., 1.
    #         bold = True
    #     else:
    #         hue, sat, val = self.colormap[name]
    #         bold = False
    #         if highlight:
    #             bold = True
    #         else:
    #             val = 0.2

    #     return self.get_ansi_tpl(hue, sat, val, bold)

    def format_source(self, source_map, context, lineno):
        bold_tp = self.get_ansi_tpl(0.,0.,0.8, True)
        default_tpl = self.get_ansi_tpl(0.,0.,0.8, False)
        comment_tpl = self.get_ansi_tpl(0.,0.,0.4, False)

        source_lines = OrderedDict()
        colormap = {}
        for ln in context:
            mark = (ln == lineno)
            line = ''
            for snippet, ttype, _ in source_map[ln]:
                if ttype in [ex.KEYWORD, ex.OP]:
                    line += bold_tp % snippet
                elif ttype == ex.VAR:
                    if snippet not in colormap:
                        colormap[snippet] = self.pick_color(snippet)
                    hue, sat, val = colormap[snippet]
                    val = val if mark else 0.5
                    var_tpl = self.get_ansi_tpl(hue, sat, val)
                    line += var_tpl % snippet
                elif ttype == ex.COMMENT:
                    line += comment_tpl % snippet
                else:
                    line += default_tpl % snippet
            source_lines[ln] = line
        self.colormap = colormap
        return source_lines

    # def process_source(self, fi, context):
    #     self.colormap = {name: self.pick_color(name) for name in fi.name2lines if name not in kwlist}
    #     colored_source_map = self.color_names_in_source(fi.source_map, fi.name_map, fi.lineno)

    #     return colored_source_map

    # def color_names_in_source(self, source_map, line2names, lineno):

    #     colored_source_map = OrderedDict()
    #     for ln, line in source_map.items():
    #         highlight = (ln == lineno)
    #         col_offset = 0
    #         plan = sorted(line2names[ln], key=lambda oc: oc[1])
    #         for (name, scol, ecol) in plan:
    #             scol += col_offset
    #             ecol += col_offset
    #             before = line[:scol]
    #             after = line[ecol:]

    #             color_tpl = self.get_ansi_color_tpl(name, highlight)
    #             colored_name = color_tpl % name
    #             line = before + (colored_name) + after
    #             col_offset += len(colored_name) - len(name)

    #         colored_source_map[ln] = line
    #     return colored_source_map


    # def format_assignment(self, name, value, occurrences, lineno):
    #     color = self.get_ansi_color_tpl(name, (lineno in occurrences))
    #     val_str = self.format_value(name, value)
    #     return self.val_tpl % (color % name, color % val_str)


def format_tb(frameinfos, formatter=None, terse_formatter=None, reverse_order=False):
    if formatter is None:
        formatter = VerboseFormatter()
    if terse_formatter is None:
        terse_formatter = formatter
    if not isinstance(frameinfos, list):
        frameinfos = [frameinfos]

    tb_strings = []
    for fi in frameinfos:
        if 'site-packages' in fi.filename:
            tb_strings.append(terse_formatter.format_frame(fi))
        else:
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

    frameinfos = list(walk_tb(tb))
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
    return msg


def excepthook(etype, evalue, tb, **kwargs):
    tb_message = format(etype, evalue, tb, **kwargs)
    print(tb_message, file=sys.stderr)
