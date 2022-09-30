import types
import os

from collections import OrderedDict
import stackprinter.extraction as ex
import stackprinter.source_inspection as sc
import stackprinter.colorschemes as colorschemes

from stackprinter.prettyprinting import format_value
from stackprinter.utils import inspect_callable, match, trim_source, get_ansi_tpl

class FrameFormatter():
    headline_tpl = 'File "%s", line %s, in %s\n'
    sourceline_tpl = "    %-3s  %s"
    single_sourceline_tpl = "    %s"
    marked_sourceline_tpl = "--> %-3s  %s"
    elipsis_tpl = " (...)\n"
    var_indent = 5
    sep_vars = "%s%s" % ((' ') * 4, ('.' * 50))
    sep_source_below = ""

    val_tpl = ' ' * var_indent + "%s = %s\n"

    def __init__(self, source_lines=5, source_lines_after=1,
                 show_signature=True, show_vals='like_source',
                 truncate_vals=500, line_wrap: int = 60,
                 suppressed_paths=None, suppressed_vars=None):
        """
        Formatter for single frames.

        This is essentially a partially applied function -- supply config args
        to this constructor, then _call_ the resulting object with a frame.


        Params
        ---
        source_lines: int or 'all'. (default: 5 lines)
            Select how much source code context will be shown.
            int 0: Don't include a source listing.
            int n > 0: Show n lines of code.
            string 'all': Show the whole scope of the frame.

        source_lines_after: int
            nr of lines to show after the highlighted one

        show_signature: bool (default True)
            Always include the function header in the source code listing.

        show_vals: str or None (default 'like_source')
            Select which variable values will be shown.
            'line': Show only the variables on the highlighted line.
            'like_source': Show those visible in the source listing (default).
            'all': Show every variable in the scope of the frame.
            None: Don't show any variable values.

        truncate_vals: int (default 500)
            Maximum number of characters to be used for each variable value

        line_wrap: int (default 60)
            insert linebreaks after this nr of characters, use 0 to never insert
            a linebreak

        suppressed_paths: list of regex patterns
            Set less verbose formatting for frames whose code lives in certain paths
            (e.g. library code). Files whose path matches any of the given regex
            patterns will be considered boring. The first call to boring code is
            rendered with fewer code lines (but with argument values still visible),
            while deeper calls within boring code get a single line and no variable
            values.

            Example: To hide numpy internals from the traceback, set
            `suppressed_paths=[r"lib/python.*/site-packages/numpy"]`
        """


        if not (isinstance(source_lines, int) or source_lines == 'all'):
            raise ValueError("source_lines must be an integer or 'all', "
                             "was %r" % source_lines)

        valid_gv = ['all', 'like_source', 'line', None, False]
        if show_vals not in valid_gv:
            raise ValueError("show_vals must be one of "
                             "%s, was %r" % (str(valid_gv), show_vals))

        self.lines = source_lines
        self.lines_after = source_lines_after
        self.show_signature = show_signature
        self.show_vals = show_vals
        self.truncate_vals = truncate_vals
        self.line_wrap = line_wrap
        self.suppressed_paths = suppressed_paths
        self.suppressed_vars = suppressed_vars

    def __call__(self, frame, lineno=None):
        """
        Render a single stack frame or traceback entry


        Params
        ----

        frame: Frame object, Traceback object (or FrameInfo tuple)
            The frame or traceback entry to be formatted.

            The only difference between passing a frame or a traceback object is
            which line gets highlighted in the source listing: For a frame, it's
            the currently executed line; for a traceback, it's the line where an
            error occurred. (technically: `frame.f_lineno` vs. `tb.tb_lineno`)

            The third option is interesting only if you're planning to format
            one frame multiple different ways: It is a little faster to format a
            pre-chewed verion of the frame, since non-formatting-specific steps
            like "finding the source code", "finding all the variables" etc only
            need to be done once per frame. So, this method also accepts the raw
            results of `extraction.get_info()` of type FrameInfo. In that case,
            this method will really just do formatting, no more chewing.

        lineno: int
            override which line gets highlighted
        """
        accepted_types = (types.FrameType, types.TracebackType, ex.FrameInfo)
        if not isinstance(frame, accepted_types):
            raise ValueError("Expected one of these types: "
                             "%s. Got %r" % (accepted_types, frame))

        try:
            finfo = ex.get_info(frame, lineno, self.suppressed_vars)

            return self._format_frame(finfo)
        except Exception as exc:
            # If we crash, annotate the exception with the thing
            # we were trying to format, for debug/logging purposes.
            exc.where = frame
            raise

    def _format_frame(self, fi):
        msg = self.headline_tpl % (fi.filename, fi.lineno, fi.function)

        source_map, assignments = self.select_scope(fi)

        if source_map:
            source_lines = self._format_source(source_map)
            msg += self._format_listing(source_lines, fi.lineno)
        if assignments:
            msg += self._format_assignments(assignments)
        elif self.lines == 'all' or self.lines > 1 or self.show_signature:
            msg += '\n'

        return msg

    def _format_source(self, source_map):
        lines = OrderedDict()
        for ln in sorted(source_map):
            lines[ln] = ''.join(st for st, _, in source_map[ln])
        return lines

    def _format_listing(self, lines, lineno):
        ln_prev = None
        msg = ""
        n_lines = len(lines)
        for ln in sorted(lines):
            line = lines[ln]
            if ln_prev and ln_prev != ln - 1:
                msg += self.elipsis_tpl
            ln_prev = ln

            if n_lines > 1:
                if ln == lineno:
                    tpl = self.marked_sourceline_tpl
                else:
                    tpl = self.sourceline_tpl
                msg += tpl % (ln, line)
            else:
                msg += self.single_sourceline_tpl % line

        msg += self.sep_source_below
        return msg

    def _format_assignments(self, assignments):
        msgs = []
        for name, value in assignments.items():
            val_str = format_value(value,
                                   indent=len(name) + self.var_indent + 3,
                                   truncation=self.truncate_vals,
                                   wrap=self.line_wrap)
            assign_str = self.val_tpl % (name, val_str)
            msgs.append(assign_str)
        if len(msgs) > 0:
            return self.sep_vars + '\n' + ''.join(msgs) + self.sep_vars + '\n\n'
        else:
            return ''

    def select_scope(self, fi):
        """
        decide which lines of code and which variables will be visible
        """
        source_lines = []
        minl, maxl = 0, 0
        if len(fi.source_map) > 0:
            minl, maxl = min(fi.source_map), max(fi.source_map)
            lineno = fi.lineno

            if self.lines == 0:
                source_lines = []
            elif self.lines == 1:
                source_lines = [lineno]
            elif self.lines == 'all':
                source_lines = range(minl, maxl + 1)
            elif self.lines > 1 or self.lines_after > 0:
                start = max(lineno - (self.lines - 1), 0)
                stop = lineno + self.lines_after
                start = max(start, minl)
                stop = min(stop, maxl)
                source_lines = list(range(start, stop + 1))

            if source_lines and self.show_signature:
                source_lines = sorted(set(source_lines) | set(fi.head_lns))

        if source_lines:
            # Report a bit more info about a weird class of bug
            # that I can't reproduce locally.
            if not set(source_lines).issubset(fi.source_map.keys()):
                debug_vals = [source_lines, fi.head_lns, fi.source_map.keys()]
                info = ', '.join(str(p) for p in debug_vals)
                raise Exception("Picked an invalid source context: %s" % info)
            trimmed_source_map = trim_source(fi.source_map, source_lines)
        else:
            trimmed_source_map = {}

        if self.show_vals:
            if self.show_vals == 'all':
                val_lines = range(minl, maxl)
            elif self.show_vals == 'like_source':
                val_lines = source_lines
            elif self.show_vals == 'line':
                val_lines = [lineno] if source_lines else []

            # TODO refactor the whole blacklistling mechanism below:

            def hide(name):
                value = fi.assignments[name]
                if callable(value):
                    qualified_name, path, *_ = inspect_callable(value)
                    is_builtin = value.__class__.__name__ == 'builtin_function_or_method'
                    is_boring = is_builtin or (qualified_name == name) or (path is None)
                    is_suppressed = match(path, self.suppressed_paths)
                    return is_boring or is_suppressed
                return False

            visible_vars = (name for ln in val_lines
                            for name in fi.line2names[ln]
                            if name in fi.assignments)

            visible_assignments = OrderedDict([(n, fi.assignments[n])
                                               for n in visible_vars
                                               if not hide(n)])
        else:
            visible_assignments = {}

        return trimmed_source_map, visible_assignments


class ColorfulFrameFormatter(FrameFormatter):

    def __init__(self, style='darkbg', **kwargs):
        """
        See FrameFormatter - this just adds some ANSI color codes here and there
        """
        self.colors = getattr(colorschemes, style)()

        highlight = self.tpl('highlight')
        header = self.tpl('header')
        arrow_lineno = self.tpl('arrow_lineno')
        dots = self.tpl('dots')
        lineno = self.tpl('lineno')

        self.headline_tpl = header % 'File "%s%s' + highlight % '%s' + header % '", line %s, in %s\n'
        self.sourceline_tpl = lineno % super().sourceline_tpl
        self.marked_sourceline_tpl = arrow_lineno % super().marked_sourceline_tpl
        self.elipsis_tpl = dots % super().elipsis_tpl
        self.sep_vars = dots % super().sep_vars

        super().__init__(**kwargs)

    def tpl(self, name):
        return get_ansi_tpl(*self.colors[name])

    def _format_frame(self, fi):
        basepath, filename = os.path.split(fi.filename)
        sep = os.sep if basepath else ''
        msg = self.headline_tpl % (basepath, sep, filename, fi.lineno, fi.function)
        source_map, assignments = self.select_scope(fi)

        colormap = self._pick_colors(source_map, fi.name2lines, assignments, fi.lineno)

        if source_map:
            source_lines = self._format_source(source_map, colormap, fi.lineno)
            msg += self._format_listing(source_lines, fi.lineno)

        if assignments:
            msg += self._format_assignments(assignments, colormap)
        elif self.lines == 'all' or self.lines > 1 or self.show_signature:
            msg += '\n'

        return msg

    def _format_source(self, source_map, colormap, lineno):
        bold_tp = self.tpl('source_bold')
        default_tpl = self.tpl('source_default')
        comment_tpl = self.tpl('source_comment')

        source_lines = OrderedDict()
        for ln in source_map:
            line = ''
            for snippet, ttype in source_map[ln]:
                if ttype in [sc.KEYWORD, sc.OP]:
                    line += bold_tp % snippet
                elif ttype == sc.VAR:
                    if snippet not in colormap:
                        line += default_tpl % snippet
                    else:
                        hue, sat, val, bold = colormap[snippet]
                        var_tpl = get_ansi_tpl(hue, sat, val, bold)
                        line += var_tpl % snippet
                elif ttype == sc.CALL:
                    line += bold_tp % snippet
                elif ttype == sc.COMMENT:
                    line += comment_tpl % snippet
                else:
                    line += default_tpl % snippet
            source_lines[ln] = line

        return source_lines

    def _format_assignments(self, assignments, colormap):
        msgs = []
        for name, value in assignments.items():
            val_str = format_value(value,
                                   indent=len(name) + self.var_indent + 3,
                                   truncation=self.truncate_vals,
                                   wrap=self.line_wrap)
            assign_str = self.val_tpl % (name, val_str)
            hue, sat, val, bold = colormap.get(name, self.colors['var_invisible'])
            clr_str = get_ansi_tpl(hue, sat, val, bold) % assign_str
            msgs.append(clr_str)
        if len(msgs) > 0:
            return self.sep_vars + '\n' + ''.join(msgs) + self.sep_vars + '\n\n'
        else:
            return ''

    def _pick_colors(self, source_map, name2lines, assignments, lineno):
        # TODO refactor: pick a hash for each name across frames, _then_ color.
        # Currently, colors are consistent across frames purely because there's
        # a fixed map from hashes to colors. It's not bijective though. If colors
        # were picked after hashing across all frames, that could be fixed.
        colormap = {}
        for line in source_map.values():
            for name, ttype in line:
                if name not in colormap and ttype == sc.VAR and name in assignments:
                    value = assignments[name]
                    highlight = lineno in name2lines[name]
                    colormap[name] = self._pick_color(name, value, highlight)
        return colormap

    def _pick_color(self, name, val, highlight=False, method='id'):
        if method == 'formatted':
            seed = format_value(val)
        elif method == 'repr':
            seed = repr(val)
        elif method == 'id':
            seed = id(val)
        elif method == 'name':
            seed = name
        else:
            raise ValueError('%r' % method)

        return self.colors.get_random(seed, highlight)




