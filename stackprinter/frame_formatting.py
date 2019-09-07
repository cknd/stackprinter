import types
import os

from collections import OrderedDict
from keyword import kwlist
import token as token_module

import stackprinter.extraction as ex
import stackprinter.colorschemes as colorschemes

from stackprinter.prettyprinting import format_value
from stackprinter.utils import inspect_callable, match, trim_source, get_ansi_tpl, ansi_color, ansi_reset
import stack_data


class FrameFormatter():
    headline_tpl = 'File "%s", line %s, in %s\n'
    sourceline_tpl = "    %-3s  "
    single_sourceline_tpl = "    "
    marked_sourceline_tpl = "--> %-3s  "
    elipsis_tpl = " (...)\n"
    var_indent = 5
    sep_vars = "%s%s" % ((' ') * 4, ('.' * 50))
    sep_source_below = ""

    val_tpl = ' ' * var_indent + "%s = %s\n"

    def __init__(self, source_lines=5, source_lines_after=1,
                 show_signature=True, show_vals='like_source', truncate_vals=500,
                 suppressed_paths=None):
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
        self.suppressed_paths = suppressed_paths  # already compile regexes and make a `match` callable?

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
            finfo = ex.get_info(frame)

            return self._format_frame(finfo)
        except Exception as exc:
            # If we crash, annotate the exception with the thing
            # we were trying to format, for debug/logging purposes.
            exc.where = frame
            raise

    def _format_frame(self, fi):
        msg = self.headline_tpl % (fi.code.co_filename, fi.lineno, fi.executing.code_qualname())

        variables = self.variables(fi)
        if 1:
            msg += self._format_listing(fi.lines)

        if variables:
            msg += self._format_assignments(variables)
        elif self.lines == 'all' or self.lines > 1 or self.show_signature:
            msg += '\n'

        return msg

    def _format_listing(self, lines, colormap=None, variables=()):
        if colormap:
            bold_code = ansi_color(*self.colors['source_bold'])
            comment_code = ansi_color(*self.colors['source_comment'])

        msg = ""
        n_lines = len(lines)
        variables = set(variables)
        for line in lines:
            if line is stack_data.LINE_GAP:
                msg += self.elipsis_tpl
                continue

            if colormap:
                def convert_variable_range(r):
                    var = r.data[0]
                    if var in colormap:
                        return ansi_color(*colormap[var]), ansi_reset

                def convert_token_range(r):
                    typ = r.data.type
                    if typ == token_module.OP or typ == token_module.NAME and r.data.string in kwlist:
                        return bold_code, ansi_reset

                    if typ == token_module.COMMENT:
                        return comment_code, ansi_reset

                variable_ranges = [
                    rang
                    for rang in line.variable_ranges
                    if rang.data[0] in variables
                ]

                markers = (
                        stack_data.markers_from_ranges(variable_ranges, convert_variable_range) +
                        stack_data.markers_from_ranges(line.token_ranges, convert_token_range)
                )
            else:
                markers = []

            text = line.render_with_markers(markers) + "\n"

            if n_lines > 1:
                if line.is_current:
                    tpl = self.marked_sourceline_tpl
                else:
                    tpl = self.sourceline_tpl
                msg += tpl % line.lineno + text
            else:
                msg += self.single_sourceline_tpl + text

        msg += self.sep_source_below
        return msg

    def _format_assignments(self, variables, colormap=None):
        msgs = []
        for variable in variables:
            val_str = format_value(variable.value,
                                   indent=len(variable.name) + self.var_indent + 3,
                                   truncation=self.truncate_vals)
            assign_str = self.val_tpl % (variable.name, val_str)
            if colormap:
                hue, sat, val, bold = colormap.get(variable, self.colors['var_invisible'])
                assign_str = get_ansi_tpl(hue, sat, val, bold) % assign_str
            msgs.append(assign_str)
        if len(msgs) > 0:
            return self.sep_vars + '\n' + ''.join(msgs) + self.sep_vars + '\n\n'
        else:
            return ''

    def variables(self, frame_info):
        if not self.show_vals:
            return []

        if self.show_vals == 'all':
            variables = frame_info.variables
        elif self.show_vals == 'like_source':
            variables = frame_info.variables_in_lines
        elif self.show_vals == 'line':
            variables = frame_info.variables_in_executing_piece
        else:
            raise ValueError("Unknown option " + self.show_vals)

        variables = sorted(
            [
                variable
                for variable in variables
                if not self.hide_variable(variable.name, variable.value)
            ],
            key=lambda var: min(node.first_token.start for node in var.nodes)
        )

        return variables

    def hide_variable(self, name, value):
        if not callable(value):
            return False

        qualified_name, path, *_ = inspect_callable(value)

        is_builtin = value.__class__.__name__ == 'builtin_function_or_method'
        is_boring = is_builtin or qualified_name == name
        if is_boring:
            return True

        is_suppressed = match(path, self.suppressed_paths)
        if is_suppressed:
            return True


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
        basepath, filename = os.path.split(fi.code.co_filename)
        sep = os.sep if basepath else ''
        msg = self.headline_tpl % (basepath, sep, filename, fi.lineno, fi.executing.code_qualname())

        colormap = self._pick_colors(fi.variables)

        variables = self.variables(fi)
        if 1:
            msg += self._format_listing(fi.lines, colormap, variables)

        if variables:
            msg += self._format_assignments(variables, colormap)
        elif self.lines == 'all' or self.lines > 1 or self.show_signature:
            msg += '\n'

        return msg

    def _pick_colors(self, variables):
        # TODO refactor: pick a hash for each name across frames, _then_ color.
        # Currently, colors are consistent across frames purely because there's
        # a fixed map from hashes to colors. It's not bijective though. If colors
        # were picked after hashing across all frames, that could be fixed.
        return {
            variable: self._pick_color(
                variable.name,
                variable.value,
                highlight=False,  # TODO
            )
            for variable in variables
        }

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




