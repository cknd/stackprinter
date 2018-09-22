import sys
import inspect
import traceback
import tokenize
from keyword import kwlist
from collections import deque, defaultdict
from io import BytesIO
from extraction import walk_tb, FrameInfo


class FrameFormatter():
    headline_tpl = "File %s, line %s in %s\n"
    sourceline_tpl = "%s%-4s %s"
    vars_separator = "    %s\n" % ('.' * 50)
    var_indent = "        "
    assignment_tpl = var_indent + "%s = %s\n"

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
        self._validate(source_context, show_vals)
        self.source_context = source_context
        self.show_vals = show_vals
        self.show_signature = show_signature
        self.truncate_vals = int(truncate_vals)

    def _validate(self, source_context, show_vals):
        if not (isinstance(source_context, int) or source_context == 'frame'):
            raise ValueError("source_context must be an integer or 'frame'.")

        valid_gv = ['frame', 'context', 'line', False]
        if show_vals not in valid_gv:
            raise ValueError("show_vals must be one of %s" % str(valid_gv))

    def show_frame(self, fi):
        if not isinstance(fi, FrameInfo):
            raise ValueError("Expected a FrameInfo tuple. "\
                            "extraction.inspect_tb() makes those.")

        msg = self.headline_tpl % (fi.filename, fi.lineno, fi.function)
        first_ln, last_ln = fi.source[0][0], fi.source[-1][0]
        lines_shown = self.select_visible_lines(first_ln, last_ln, fi.lineno,
                                                fi.function == '<module>')

        if lines_shown:
            msg += self.format_source(fi.source, lines_shown, fi.lineno, fi.name_map)

        if self.show_vals:
            if self.show_vals == 'frame':
                val_lines = range(first_ln, last_ln)
            elif self.show_vals == 'context':
                val_lines = lines_shown
            elif self.show_vals == 'line':
                val_lines = [lineno]
            msg += self.vars_separator
            msg += self.format_vars(fi.assignments, val_lines, fi.name_map)
            msg += self.vars_separator
            msg += '\n'
        return msg

    def select_visible_lines(self, minl, maxl, lineno, is_module=False):
        if self.source_context == 'frame':
            return range(minl, maxl)
        elif self.source_context == 0:
            return []
        elif self.source_context == 1:
            return [lineno]
        elif self.source_context > 1:
            # import pdb; pdb.set_trace()
            start = max(lineno - (self.source_context - 1), 0)
            stop = lineno + 1
            start = max(start, minl)
            stop = min(stop, maxl)
            lines_shown = list(range(start, stop+1))
            if self.show_signature and not is_module and start > minl:
                lines_shown = [minl] + lines_shown
                # TODO do the right thing for multiline signatures
            return lines_shown

    def format_source(self, source_lines, lines_shown, lineno, name_map=None):
        source_lines = self.highlight(source_lines, name_map)
        source_map = dict(source_lines)
        msg = ""
        ln_prev = None
        n_visible = len(lines_shown)
        for ln in lines_shown:
            if ln_prev and ln_prev != ln - 1:
                msg += "(...)\n"
            ln_prev = ln
            do_marker = (ln == lineno and n_visible > 1)
            marker = '--> ' if do_marker else '    '
            msg += self.sourceline_tpl % (marker, ln, source_map[ln])
        return msg

    def highlight(self, source_lines, name_map):
        # do syntax highlighing, or color the names in a color cycle based on
        # order of appearance (synchronized with colors in vars below)
        return source_lines

    def format_vars(self, assignments, visible_lines, name_map=None):

        visible_lines = set(visible_lines)

        msg = ''
        # msg += 'visible lines: %s\n' % visible_lines
        for name, value in assignments:
            occurrences = name_map[name]
            startlines, _, endlines, _ = zip(*occurrences)
            occurrences = set(startlines) | set(endlines)
            if occurrences.intersection(visible_lines):
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
                        val_str = "<error calling __str__>"

                if self.truncate_vals and len(val_str) > (self.truncate_vals+3):
                    val_str = "%s..." % val_str[:self.truncate_vals]

                indented_newline = '\n' + self.var_indent + (' ' * (len(name) + 2))
                val_str = val_str.replace('\n', indented_newline)
                msg += self.assignment_tpl % (name, val_str)
        return msg


class InsanelyVerboseFormatter(FrameFormatter):
    # header, source and vals for the whole frame
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
    # header, 1 line of source, no vals
    def __init__(self):
        super().__init__(source_context=1, show_vals=False)

# class ColorTB(StringTB):
#     header_tpl = "%s... "  #TODO colored version

# class PickleTB(TTCore):
#     pass



def format_tb(frameinfos, formatter=None, reverse_order=False):
    if formatter is None:
        formatter = VerboseFormatter()
    if not isinstance(frameinfos, list):
        frameinfos = [frameinfos]
    tb_strings = [formatter.show_frame(fi) for fi in frameinfos]
    if reverse_order:
        tb_strings = reversed(tb_strings)
    return "\n\n".join(tb_strings)


def format_summary(frameinfos, message='', reverse_order=False):
    msg_inner = format_tb(frameinfos[-1], TerseFormatter(), reverse_order)
    msg_outer = format_tb(frameinfos[:-1], MinimalFormatter(), reverse_order)
    msg = [msg_outer, msg_inner, message]
    if reverse_order:
        msg = reversed(msg)
    return "\n".join(msg)


def format(etype, evalue, tb, show_full=True, show_summary=True,
           reverse_order=False, **formatter_kwargs):

    frameinfos = list(walk_tb(tb))
    exception_msg = ' '.join(traceback.format_exception_only(etype, evalue))

    if show_summary:
        msg = format_summary(frameinfos, exception_msg, reverse_order)
    else:
        msg = ''

    if show_full:
        if show_summary:
            msg += "\n\n========== Full traceback: ==========\n\n"
        formatter = VerboseFormatter(**formatter_kwargs)
        msg = format_tb(frameinfos, formatter, reverse_order)
        msg += exception_msg

    return msg


def excepthook(etype, evalue, tb, **kwargs):
    tb_message = format(etype, evalue, tb, **kwargs)
    print(tb_message, file=sys.stderr)


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

