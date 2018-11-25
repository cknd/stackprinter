import extraction as ex
import source_inspection as sc
from collections import OrderedDict
from prettyprinting import format_value
from utils import inspect_callable

import colorsys
import random
import types

def trim_source(source_map, context):
    """
    get part of a source listing, with extraneous indentation removed

    """
    indent_type = None
    min_indent = 9000
    for ln in context:
        (snippet0, *meta0), *remaining_line = source_map[ln]

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

    return trimmed_source_map


def select_scope(fi, source_context, show_vals, show_signature, filter=None):
    """
    decide which lines of code and which variables will be visible
    """
    source_lines = []
    minl, maxl = 0, 0
    if len(fi.source_map) > 0:
        minl, maxl = min(fi.source_map), max(fi.source_map)
        lineno = fi.lineno

        if source_context == 0:
            source_lines = []
        elif source_context == 1:
            source_lines = [lineno]
        elif source_context == 'all':
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
        if show_vals == 'all':
            val_lines = range(minl, maxl)
        elif show_vals == 'like_source':
            val_lines = source_lines
        elif show_vals == 'line':
            val_lines = [lineno]

        # TODO refactor the whole blacklistling mechanism below

        def hidden(name):
            value = fi.assignments[name]
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


class FrameFormatter():
    headline_tpl = "File %s, line %s, in %s\n"
    sourceline_tpl = "    %-3s %s"
    marked_sourceline_tpl = "--> %-3s %s"
    elipsis_tpl = " (...)\n"
    sep_vars = "    %s\n" % ('.' * 50)
    sep_source_below = ""
    var_indent = 8 #"        "
    val_tpl = ' ' * var_indent + "%s = %s\n"

    def __init__(self, source_context=5, show_signature=True,
                 show_vals='like_source', truncate_vals=500):
        """
        TODO


        Params
        ---
        source_context: int or 'all'
            Selects how much source code will be shown.
            0: Don't include a source listing.
            n > 0: Show n lines of code.
            string 'all': Show the whole scope of the frame.

        show_signature: bool
            Always include the function header in the source code listing.

        show_vals: str or None
            Selects which variable assignments will be shown.
            'line': Show only the variables on the highlighted line.
            'like_source': Show those visible in the source listing (default).
            'all': Show every variable in the scope of the frame.
            None: Don't show any variable assignments.

        truncate_vals: int
            Maximum number of characters to be used for each variable value
        """


        if not (isinstance(source_context, int) or source_context == 'all'):
            raise ValueError("source_context must be an integer or 'all', "
                             "was %s" % source_context)

        valid_gv = ['all', 'like_source', 'line', None]
        if show_vals not in valid_gv:
            raise ValueError("show_vals must be one of "
                             "%s, was %s" % (str(valid_gv), show_vals))

        self.source_context = source_context
        self.show_signature = show_signature
        self.show_vals = show_vals
        self.truncate_vals = truncate_vals

    def __call__(self, frame):
        """
        Render a single stack frame or traceback entry


        Params
        ----

        frame: Frame object, Traceback object (or FrameInfo tuple)
            The frame or traceback entry to be formatted.

            The only difference between passing a frame or a traceback object is
            which line gets highlighted in the source listing: For a frame, it's
            the currently executed line; for a traceback, it's the line where an
            error occured. (technically: `frame.f_lineno` vs. `tb.tb_lineno`)

            The third option is interesting only if you're planning to format
            one frame multiple different ways. It is a little faster to format a
            pre-chewed frame than a normal frame object, since the whole process
            contains many non-formatting-specific steps like "finding the source
            code", "finding all the variables" etc. So, this method also accepts
            the raw results from `extraction.get_info()`, of type FrameInfo. In
            that case, it will just assemble some strings, no more chewing.
        """
        accepted_types = (types.FrameType, types.TracebackType, ex.FrameInfo)
        if not isinstance(frame, accepted_types):
            raise ValueError("Expected one of these types: "
                             "%s. Got %r" % (accepted_types, frame))

        if isinstance(frame, ex.FrameInfo):
            finfo = frame
        else:
            finfo = ex.get_info(frame)

        msg = self._format_frame(finfo, self.source_context, self.show_vals,
                                 self.show_signature, self.truncate_vals)

        return msg

    def _format_frame(self, fi, source_context, show_vals,
                      show_signature, truncate_vals):
        msg = self.headline_tpl % (fi.filename, fi.lineno, fi.function)
        source_map, assignments = select_scope(fi, source_context,
                                               show_vals, show_signature)

        if source_map:
            lines = self._format_source(source_map)
            msg += self._format_listing(lines, fi.lineno)

        msg += self._format_assignments(assignments, truncate_vals)
        return msg

    def _format_source(self, source_map):
        lines = OrderedDict()
        for ln in sorted(source_map):
            lines[ln] = ''.join(st for st, _, _ in source_map[ln])
        return lines

    def _format_listing(self, lines, lineno):
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

    def _format_assignments(self, assignments, truncate=500):
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


class ColoredVariablesFormatter(FrameFormatter):

    highlight_val = 1.
    default_val = 0.5

    def __init__(self, *args, **kwargs):
        self.rng = random.Random()
        bright = self._get_ansi_tpl(0, 0, 1., True)
        medium = self._get_ansi_tpl(0, 0, 0.7, True)
        darker = self._get_ansi_tpl(0, 0, 0.4, False)
        dark = self._get_ansi_tpl(0, 0, 0.1, True)
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

        colormap = self._pick_colors(source_map, assignments, fi.lineno)

        if source_map:  # TODO is this if necessary? what happens below with an empty sourcemap?
            lines = self._format_source(source_map, colormap, fi.lineno)
            msg += self._format_listing(lines, fi.lineno)

        msg += self._format_assignments(assignments, colormap, truncate)
        return msg

    def _format_source(self, source_map, colormap, lineno):
        bold_tp =     self._get_ansi_tpl(0.,0.,1., True)
        default_tpl = self._get_ansi_tpl(0.,0.,0.7, False)
        comment_tpl = self._get_ansi_tpl(0.,0.,0.2, False)

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
                        var_tpl = self._get_ansi_tpl(hue, sat, val, bold)
                        line += var_tpl % snippet
                elif ttype == sc.CALL:
                    line += bold_tp % snippet
                elif ttype == sc.COMMENT:
                    line += comment_tpl % snippet
                else:
                    line += default_tpl % snippet
            source_lines[ln] = line

        return source_lines

    def _format_assignments(self, assignments, colormap, truncate=500):
        msgs = []
        for name, value in assignments.items():
            val_str = format_value(value,
                                   indent=len(name) + self.var_indent + 3,
                                   truncate=truncate)
            assign_str = self.val_tpl % (name, val_str)
            clr_str = self._get_ansi_tpl(*colormap[name]) % assign_str
            msgs.append(clr_str)

        if len(msgs) > 0:
            return self.sep_vars + ''.join(msgs) + self.sep_vars + '\n'
        else:
            return ''

    # TODO move these methods out of the class; move the whole thing
    # to a separate module
    def _pick_colors(self, source_map, assignments, lineno):
        # TODO refactor: pick a hash for each name across frames, _then_ color.
        # Currently, colors are consistent across frames purely because the
        # map from hashes to colors is bijective. If colors were picked after
        # all hashes are known, it would be possible to avoiding color clashes
        # (by solving a little constraint satisfaction problem or something).
        # It would mean formatters would work on several frames at once, though.
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

    def _get_ansi_tpl(self, hue, sat, val, bold=False):
        r, g, b = colorsys.hsv_to_rgb(hue, sat, val)
        r = int(round(r*5))
        g = int(round(g*5))
        b = int(round(b*5))
        point = 16 + 36 * r + 6 * g + b
        bold_tp = '1;' if bold else ''
        code_tpl = ('\u001b[%s38;5;%dm' % (bold_tp, point)) + '%s\u001b[0m'
        return code_tpl