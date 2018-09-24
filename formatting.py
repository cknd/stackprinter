import sys
import traceback
from keyword import kwlist
from collections import deque, defaultdict, OrderedDict
from io import BytesIO
from extraction import walk_tb, FrameInfo, UnresolvedAttribute
try:
    import numpy as np
except ImportError:
    np = False


import colorsys
import random



class FrameFormatter():
    headline_tpl = "\n\nFile %s in %s Line %s\n"
    sourceline_tpl = "%s%-3s %s"
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

        msg = self.headline_tpl % (fi.filename, fi.function, fi.lineno)
        source_context, val_context = self.select_visible_lines(fi)

        source_map = self.process_source(fi, source_context)

        if source_context:
            msg += self.format_source(source_map, fi.lineno, source_context)

        if val_context:
            visible_occurences = {}
            for name, locations in fi.name_map.items():
                startlines, _, endlines, _ = zip(*locations)
                occurrences = set(startlines) | set(endlines)
                visible_occurences[name] = occurrences.intersection(val_context)

            msg += self.sep_vars
            msg += self.format_vars(fi.assignments, visible_occurences, fi.lineno)
            msg += self.sep_vars

        return msg

    def select_visible_lines(self, fi):
        minl, maxl = min(fi.source_map), max(fi.source_map)
        lineno = fi.lineno
        is_module = (fi.function == '<module>')

        if self.source_context == 'frame':
            source_lines = range(minl, maxl)
        elif self.source_context == 0:
            source_lines = []
        elif self.source_context == 1:
            source_lines = [lineno]
        elif self.source_context > 1:
            start = max(lineno - (self.source_context - 1), 0)
            stop = lineno + 1
            start = max(start, minl)
            stop = min(stop, maxl)
            source_lines = list(range(start, stop+1))
            if self.show_signature and not is_module and start > minl:
                source_lines = [minl] + source_lines
                # TODO do the right thing for multiline signatures
            source_lines = source_lines

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

    def process_source(self, fi, context):
        # override to add syntax coloring etc
        return fi.source_map

    def format_source(self, source_map, lineno, context):
        lines = [source_map[ln] for ln in context]
        lines = self.trim_whitespace(lines)

        msg = ""
        ln_prev = None
        n_context = len(context)
        for ln, line in zip(context, lines):
            if ln_prev and ln_prev != ln - 1:
                msg += "(...)\n"
            ln_prev = ln
            if n_context > 1:
                if ln == lineno:
                    marker = '--> '
                else:
                    marker = '    '
            else:
                marker = ''
            msg += self.sourceline_tpl % (marker, ln, line)
        msg += self.sep_source_below
        return msg

    def format_vars(self, assignments, visible_occurences, lineno):
        msgs = []
        for name, value in assignments.items():
            occurences = visible_occurences[name]
            if occurences:
                value = assignments[name]
                msgs.append(self.format_assignment(name, value,
                                                   occurences, lineno))
        msg = ''.join(msgs)
        return msg

    def format_assignment(self, name, value, occurences, lineno):
        val_str = self.format_value(name, value)
        return self.val_tpl % (name, val_str)

    def format_value(self, name, value):
        if isinstance(value, str):
            val_str = value

        elif isinstance(value, UnresolvedAttribute):
            val_tpl= "# Attribute doesn't exist. Base was: \n%s = %s"
            lastval_str = self.format_value('   ', value.last_resolvable_value)
            val_str = val_tpl % (value.last_resolvable_name, lastval_str)

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

        nl_indented = '\n' + self.var_indent + (' ' * (len(name) + 3))
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
    headline_tpl = "File %s in %s Line %s\n"
    def __init__(self):
        super().__init__(source_context=1, truncate_vals=70)

class MinimalFormatter(FrameFormatter):
    headline_tpl = "File %s in %s Line %s\n"
    def __init__(self):
        super().__init__(source_context=1, show_vals=False)


class ColoredVariablesFormatter(FrameFormatter):
    def __init__(self, *args, **kwargs):
        self.rng = random.Random()
        super().__init__(*args, **kwargs)

    def pick_color(self, name):
        self.rng.seed(name)
        hue = self.rng.random()
        sat = 1.0
        val = 1.0
        return (hue, sat, val)

    def get_ansi_color_tpl(self, hue=1., sat=1., val=1.):
        r, g, b = colorsys.hsv_to_rgb(hue, sat, val)
        r = int(round(r*5))
        g = int(round(g*5))
        b = int(round(b*5))
        point = 16 + 36 * r + 6 * g + b
        code_tpl = ('\u001b[38;5;%dm' % point) + '%s\u001b[0m'
        return code_tpl

    def process_source(self, fi, context):
        self.colormap = {name: self.pick_color(name) for name in fi.name_map}
        return fi.source_map


    def format_assignment(self, name, value, occurrences, lineno):
        hue, sat, val = self.colormap[name]
        if lineno in occurrences:
            sat = 1.
            val = 1.
        else:
            sat = 0.5
            val = 0.5
        color = self.get_ansi_color_tpl(hue, sat, val)
        val_str = self.format_value(name, value)
        return self.val_tpl % (color % name, color % val_str)



def format_tb(frameinfos, formatter=None, reverse_order=False):
    if formatter is None:
        formatter = VerboseFormatter()
    if not isinstance(frameinfos, list):
        frameinfos = [frameinfos]
    tb_strings = [formatter.format_frame(fi) for fi in frameinfos]
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
        formatter = VerboseFormatter(**formatter_kwargs)
        # formatter = ColoredVariablesFormatter(**formatter_kwargs)

        msg += format_tb(frameinfos, formatter, reverse_order)
        msg += exception_msg
    return msg


def excepthook(etype, evalue, tb, **kwargs):
    tb_message = format(etype, evalue, tb, **kwargs)
    print(tb_message, file=sys.stderr)
