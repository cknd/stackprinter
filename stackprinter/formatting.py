import colorsys
import random
import types
import traceback
import os

from collections import OrderedDict
import stackprinter.extraction as ex
import stackprinter.source_inspection as sc
from stackprinter.prettyprinting import format_value
from stackprinter.utils import inspect_callable, match


def failsafe(formatter_func, debug=True):
    """
    Recover the built-in traceback if we fall on our face while formatting
    """
    def failsafe_formatter(etype, evalue, tb, *args, **kwargs):
        try:
            msg = formatter_func(etype, evalue, tb, **kwargs)
        except Exception as exc:
            if debug:
                raise
            our_tb = traceback.format_exception(exc.__class__,
                                                exc,
                                                exc.__traceback__,
                                                chain=False)

            msg = 'Stackprinter failed:\n%s' % ''.join(our_tb[-2:])
            msg += 'So here is the original traceback at least:\n\n'
            msg += ''.join(traceback.format_exception(etype, evalue, tb))

        return msg

    return failsafe_formatter


@failsafe
def format_exc_info(etype, evalue, tb, mode='plaintext',
                    add_summary=True, reverse=False, **kwargs):

    frameinfos = [ex.get_info(fr) for fr in ex.walk_traceback(tb)]
    # TODO decouple frameinfo-getting from actual formatting, by packing
    # more of the below to respective methods (to facilitate formatting the
    # same stack multiple different ways)


    # TODO what is this for?
    if mode in ['color', 'html']:
        fmt_mode = 'color'
    else:
        fmt_mode = 'plaintext'


    # TODO move summary generation to format_stack (so threads can also use it, and)
    # so multiple format passes over one set of frameinfos is easier to achieve


    stack_msg = format_stack(frameinfos, mode=fmt_mode, reverse=reverse, **kwargs)
    exc_msg = format_exception_message(etype, evalue, mode=fmt_mode)
    if add_summary:
        minimal_kwargs = kwargs.copy()
        minimal_kwargs['source_lines'] = 1
        minimal_kwargs['show_vals'] = False
        minimal_kwargs['show_signature'] = False
        summary_msg = format_stack(frameinfos, mode=fmt_mode, reverse=reverse, **minimal_kwargs)
    else:
        summary_msg = ''

    if reverse:
        # TODO do join over list instead
        msg = exc_msg + '\n\n' + summary_msg + '\n\n' + stack_msg
    else:
        msg = stack_msg + '\n' + summary_msg + '\n' + exc_msg

    if mode == 'html':
        from ansi2html import Ansi2HTMLConverter
        conv = Ansi2HTMLConverter()
        msg = conv.convert(msg)

    return msg


def format_exception_message(etype, evalue, tb=None, mode='plaintext'):
    type_str = etype.__name__
    val_str = str(evalue)
    if val_str:
        type_str += ": "

    if mode == 'plaintext':
        return type_str + val_str
    elif mode == 'color':
        bold = get_ansi_tpl(0, 1, 1, bold=True)
        normal = get_ansi_tpl(0, 1, 1, bold=True)
        return bold % type_str + normal % val_str
    else:
        raise ValueError("Expected mode 'color' or 'plaintext'")


def format_stack(frames, mode='plaintext', source_lines=5,
                 show_signature=True, show_vals='like_source',
                 truncate_vals=500, reverse=False, suppressed_paths=None):


    if mode == 'plaintext':
        Formatter = FrameFormatter
    elif mode in ['color', 'html']:
        Formatter = ColoredFrameFormatter
    else:
        raise ValueError("Expected mode 'plaintext' or 'color', got %r" % mode)

    min_src_lines = 0 if source_lines == 0 else 1

    minimal_formatter = Formatter(source_lines=min_src_lines,
                                  show_signature=False,
                                  show_vals=False)

    reduced_formatter = Formatter(source_lines=min_src_lines,
                                  show_signature=show_signature,
                                  show_vals=show_vals,
                                  truncate_vals=truncate_vals,
                                  suppressed_paths=suppressed_paths)

    verbose_formatter = Formatter(source_lines=source_lines,
                                  show_signature=show_signature,
                                  show_vals=show_vals,
                                  truncate_vals=truncate_vals,
                                  suppressed_paths=suppressed_paths)

    frame_msgs = []
    is_boring = False
    parent_is_boring = True
    for fi in frames:
        if isinstance(fi, types.FrameType):
            fi = ex.get_info(fi)
        elif not isinstance(fi, ex.FrameInfo):
            raise ValueError("Expected a frame or a FrameInfo tuple, got %r" % fi)

        is_boring = match(fi.filename, suppressed_paths)
        if is_boring:
            if parent_is_boring:
                frame_msgs.append(minimal_formatter(fi))
            else:
                frame_msgs.append(reduced_formatter(fi))
            parent_is_boring = True

        else:
            frame_msgs.append(verbose_formatter(fi))
            parent_is_boring = False

    if reverse:
        frame_msgs = reversed(frame_msgs)

    return ''.join(frame_msgs)



class FrameFormatter():
    headline_tpl = "File %s, line %s, in %s\n"
    sourceline_tpl = "    %-3s   %s"
    single_sourceline_tpl = "   %s"
    marked_sourceline_tpl = "--> %-3s   %s"
    elipsis_tpl = " (...)\n"
    var_indent = 5
    sep_vars = "%s%s\n" % ((' ') * 4, ('.' * 50))
    sep_source_below = ""

    val_tpl = ' ' * var_indent + "%s = %s\n"

    def __init__(self, source_lines=5, source_lines_after=1,
                 show_signature=True, show_vals='like_source', truncate_vals=500,
                 suppressed_paths=None):
        """
        TODO


        Params
        ---
        source_lines: int or 'all'
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
            error occured. (technically: `frame.f_lineno` vs. `tb.tb_lineno`)

            The third option is interesting only if you're planning to format
            one frame multiple different ways. It is a little faster to format a
            pre-chewed frame than a normal frame object, since the whole process
            contains many non-formatting-specific steps like "finding the source
            code", "finding all the variables" etc. So, this method also accepts
            the raw results from `extraction.get_info()`, of type FrameInfo. In
            that case, it will just assemble some strings, no more chewing.

        lineno: TODO
        """
        accepted_types = (types.FrameType, types.TracebackType, ex.FrameInfo)
        if not isinstance(frame, accepted_types):
            raise ValueError("Expected one of these types: "
                             "%s. Got %r" % (accepted_types, frame))

        if isinstance(frame, ex.FrameInfo):
            finfo = frame
        else:
            finfo = ex.get_info(frame, lineno)

        msg = self._format_frame(finfo, self.lines, self.lines_after, self.show_vals,
                                 self.show_signature, self.truncate_vals,
                                 self.suppressed_paths)
        return msg

    def _format_frame(self, fi, lines, lines_after, show_vals,
                      show_signature, truncate_vals, suppressed_paths):
        msg = self.headline_tpl % (fi.filename, fi.lineno, fi.function)

        source_map, assignments = select_scope(fi, lines, lines_after,
                                               show_vals, show_signature,
                                               suppressed_paths)


        if source_map:
            lines = self._format_source(source_map)
            msg += self._format_listing(lines, fi.lineno)

        msg += self._format_assignments(assignments, truncate_vals)
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

    def _format_assignments(self, assignments, truncation=500):
        msgs = []
        for name, value in assignments.items():
            val_str = format_value(value,
                                   indent=len(name) + self.var_indent + 3,
                                   truncation=truncation)
            assign_str = self.val_tpl % (name, val_str)
            msgs.append(assign_str)
        if len(msgs) > 0:
            return self.sep_vars + ''.join(msgs) + self.sep_vars + '\n'
        else:
            return ''


class ColoredFrameFormatter(FrameFormatter):

    def __init__(self, *args, **kwargs):
        self.rng = random.Random()
        highlight = get_ansi_tpl(0., 1., 1., True)
        bright = get_ansi_tpl(0, 0, 1., True)
        medium = get_ansi_tpl(0, 0, 0.8, True)
        darker = get_ansi_tpl(0, 0, 0.4, False)
        dark = get_ansi_tpl(0, 0, 0.2, True)

        self.headline_tpl = bright % "File %s%s" + highlight % "%s" + bright % ", line %s, in %s\n"
        self.sourceline_tpl = dark % super().sourceline_tpl
        self.marked_sourceline_tpl = medium % super().marked_sourceline_tpl
        self.elipsis_tpl = darker % super().elipsis_tpl
        self.sep_vars = darker % super().sep_vars
        super().__init__(*args, **kwargs)

    def _format_frame(self, fi, lines, lines_after, show_vals,
                      show_signature, truncation, suppressed_paths):
        basepath, filename = os.path.split(fi.filename)
        sep = os.sep if basepath else ''
        msg = self.headline_tpl % (basepath, sep, filename, fi.lineno, fi.function)
        source_map, assignments = select_scope(fi, lines, lines_after,
                                               show_vals, show_signature,
                                               suppressed_paths)

        colormap = self._pick_colors(source_map, fi.name2lines, assignments, fi.lineno)

        if source_map:  # TODO is this if necessary? what happens below with an empty sourcemap?
            lines = self._format_source(source_map, colormap, fi.lineno)
            msg += self._format_listing(lines, fi.lineno)

        msg += self._format_assignments(assignments, colormap, truncation)


        # msg += '\n\ncolormap:\n%s' % '\n'.join(str(kv) for kv in colormap.items())

        # msg += 'fi.lineno: %s\n' % fi.lineno
        # for ln in source_map:
        #     msg += '%s: %s\n' % (ln, ln == fi.lineno)
        # msg += '\n\nsource_map:\n%s' % '\n'.join(str(kv) for kv in source_map.items())
        # msg += '\n\nassignments:\n%s' % '\n'.join(str(kv) for kv in assignments.items())
        return msg

    def _format_source(self, source_map, colormap, lineno):
        bold_tp =     get_ansi_tpl(0.,0.,0.8, True)
        default_tpl = get_ansi_tpl(0.,0.,0.8, False)
        comment_tpl = get_ansi_tpl(0.,0.,0.2, False)

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

    def _format_assignments(self, assignments, colormap, truncation=500):
        msgs = []
        for name, value in assignments.items():
            val_str = format_value(value,
                                   indent=len(name) + self.var_indent + 3,
                                   truncation=truncation)
            assign_str = self.val_tpl % (name, val_str)
            clr_str = get_ansi_tpl(*colormap[name]) % assign_str

            msgs.append(clr_str)

        if len(msgs) > 0:
            return self.sep_vars + ''.join(msgs) + self.sep_vars + '\n'
        else:
            return ''

    def _pick_colors(self, source_map, name2lines, assignments, lineno):
        # TODO refactor: pick a hash for each name across frames, _then_ color.
        # Currently, colors are consistent across frames purely because the
        # map from hashes to colors is bijective. If colors were picked after
        # all hashes are known, it would be possible to avoiding color clashes
        # (by solving a little constraint satisfaction problem or something).
        # single-frame usage should continue to be supported though.
        colormap = {}
        for line in source_map.values():
            for name, ttype in line:
                if name not in colormap and ttype == sc.VAR and name in assignments:
                    value = assignments[name]
                    highlight = lineno in name2lines[name]
                    colormap[name] = self._pick_color(name, value, highlight)
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
        hue = self.rng.uniform(0.05,0.7)
        # if hue < 0:
        #     hue = hue + 1
        sat = 1. if highlight else 1.
        val = 1. if highlight else 0.3
        bold = highlight
        return (hue, sat, val, bold)


def get_ansi_tpl(hue, sat, val, bold=False):
    r_, g_, b_ = colorsys.hsv_to_rgb(hue, sat, val)
    r = int(round(r_*5))
    g = int(round(g_*5))
    b = int(round(b_*5))
    point = 16 + 36 * r + 6 * g + b
    # print(r,g,b,point)
    # import pdb; pdb.set_trace()

    bold_tp = '1;' if bold else ''
    code_tpl = ('\u001b[%s38;5;%dm' % (bold_tp, point)) + '%s\u001b[0m'
    return code_tpl


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
                # Mixed tabs and spaces - not trimming whitespace.
                return source_map
            else:
                indent_type = '\t'
        elif snippet0.startswith(' '):
            if indent_type == '\t':
                # Mixed tabs and spaces - not trimming whitespace.
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


def select_scope(fi, lines, lines_after, show_vals, show_signature, suppressed_paths=None):
    """
    decide which lines of code and which variables will be visible
    """
    source_lines = []
    minl, maxl = 0, 0
    if len(fi.source_map) > 0:
        minl, maxl = min(fi.source_map), max(fi.source_map)
        lineno = fi.lineno

        if lines == 0:
            source_lines = []
        elif lines == 1:
            source_lines = [lineno]
        elif lines == 'all':
            source_lines = range(minl, maxl+1)
        elif lines > 1 or lines_after > 0:
            start = max(lineno - (lines - 1), 0)
            stop = lineno + lines_after
            start = max(start, minl)
            stop = min(stop, maxl)
            source_lines = list(range(start, stop+1))

        if source_lines and show_signature:
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

        # TODO refactor the whole blacklistling mechanism below:

        def hide(name):
            value = fi.assignments[name]
            if callable(value):
                qualified_name, path, *_ = inspect_callable(value)
                is_builtin = value.__class__.__name__ == 'builtin_function_or_method'
                is_boring = is_builtin or (qualified_name == name)
                is_suppressed = match(path, suppressed_paths)
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