"""
Various convnenience methods to walk stacks and concatenate formatted frames
"""
import types
import traceback

import stackprinter.extraction as ex
import stackprinter.colorschemes as colorschemes
from stackprinter.utils import match, get_ansi_tpl
from stackprinter.frame_formatting import FrameFormatter, ColorfulFrameFormatter


def get_formatter(style, **kwargs):
    if style in ['plaintext', 'plain']:
        return FrameFormatter(**kwargs)
    else:
        return ColorfulFrameFormatter(style, **kwargs)


def format_summary(frames, style='plaintext', source_lines=1, reverse=False,
                   **kwargs):
    """
    Render a list of frames with 1 line of source context, no variable values.

    keyword args like stackprinter.format()
    """
    min_src_lines = 0 if source_lines == 0 else 1
    minimal_formatter = get_formatter(style=style,
                                      source_lines=min_src_lines,
                                      show_signature=False,
                                      show_vals=False)

    frame_msgs = [minimal_formatter(frame) for frame in frames]
    if reverse:
        frame_msgs = reversed(frame_msgs)

    return ''.join(frame_msgs)


def format_stack(frames, style='plaintext', source_lines=5,
                 show_signature=True, show_vals='like_source',
                 truncate_vals=500, line_wrap=60, reverse=False,
                 suppressed_paths=None, suppressed_vars=[]):
    """
    Render a list of frames (or FrameInfo tuples)

    keyword args like stackprinter.format()
    """


    min_src_lines = 0 if source_lines == 0 else 1

    minimal_formatter = get_formatter(style=style,
                                      source_lines=min_src_lines,
                                      show_signature=False,
                                      show_vals=False)

    reduced_formatter = get_formatter(style=style,
                                      source_lines=min_src_lines,
                                      show_signature=show_signature,
                                      show_vals=show_vals,
                                      truncate_vals=truncate_vals,
                                      line_wrap=line_wrap,
                                      suppressed_paths=suppressed_paths,
                                      suppressed_vars=suppressed_vars)

    verbose_formatter = get_formatter(style=style,
                                      source_lines=source_lines,
                                      show_signature=show_signature,
                                      show_vals=show_vals,
                                      truncate_vals=truncate_vals,
                                      line_wrap=line_wrap,
                                      suppressed_paths=suppressed_paths,
                                      suppressed_vars=suppressed_vars)

    frame_msgs = []
    parent_is_boring = True
    for frame in frames:
        fi = ex.get_info(frame, suppressed_vars=suppressed_vars)
        is_boring = match(fi.filename, suppressed_paths)
        if is_boring:
            if parent_is_boring:
                formatter = minimal_formatter
            else:
                formatter = reduced_formatter
        else:
            formatter = verbose_formatter

        parent_is_boring = is_boring
        frame_msgs.append(formatter(fi))

    if reverse:
        frame_msgs = reversed(frame_msgs)

    return ''.join(frame_msgs)


def format_stack_from_frame(fr, add_summary=False, **kwargs):
    """
    Render a frame and its parents


    keyword args like stackprinter.format()

    """
    stack = []
    while fr is not None:
        stack.append(fr)
        fr = fr.f_back
    stack = reversed(stack)

    return format_stack(stack, **kwargs)


def format_exc_info(etype, evalue, tb, style='plaintext', add_summary='auto',
                    reverse=False, suppressed_exceptions=[KeyboardInterrupt],
                    suppressed_vars=[], **kwargs):
    """
    Format an exception traceback, including the exception message

    see stackprinter.format() for docs about the keyword arguments
    """
    if etype is None:
        etype = type(None)

    if etype.__name__ == 'ExceptionGroup':
        # Exception groups (new in py 3.11) aren't supported so far,
        # but at least we fall back on the default message.
        return ''.join(traceback.format_exception(etype, evalue, tb))

    msg = ''
    try:
        # First, recursively format any chained exceptions (exceptions
        # during whose handling the given one happened).
        # TODO: refactor this whole messy function to return a
        # more... structured datastructure before assembling a string,
        # so that e.g. a summary of the whole chain can be shown at
        # the end.
        context = getattr(evalue, '__context__', None)
        cause = getattr(evalue, '__cause__', None)
        suppress_context = getattr(evalue, '__suppress_context__', False)
        if cause:
            chained_exc = cause
            chain_hint = ("\n\nThe above exception was the direct cause "
                          "of the following exception:\n\n")
        elif context and not suppress_context:
            chained_exc = context
            chain_hint = ("\n\nWhile handling the above exception, "
                          "another exception occurred:\n\n")
        else:
            chained_exc = None

        if chained_exc:
            msg += format_exc_info(chained_exc.__class__,
                                   chained_exc,
                                   chained_exc.__traceback__,
                                   style=style,
                                   add_summary=add_summary,
                                   reverse=reverse,
                                   suppressed_vars=suppressed_vars,
                                   **kwargs)

            if style == 'plaintext':
                msg +=  chain_hint
            else:
                sc = getattr(colorschemes, style)
                clr = get_ansi_tpl(*sc.colors['exception_type'])
                msg += clr % chain_hint

        # Now, actually do some formatting:
        parts = []
        if tb:
            frameinfos = [ex.get_info(tb_, suppressed_vars=suppressed_vars)
                          for tb_ in _walk_traceback(tb)]
            if (suppressed_exceptions and
                issubclass(etype, tuple(suppressed_exceptions))):
                summary = format_summary(frameinfos, style=style,
                                         reverse=reverse, **kwargs)
                parts = [summary]
            else:
                whole_stack = format_stack(frameinfos, style=style,
                                           reverse=reverse, **kwargs)
                parts.append(whole_stack)

                if add_summary == 'auto':
                    add_summary = whole_stack.count('\n') > 50

                if add_summary:
                    summary = format_summary(frameinfos, style=style,
                                             reverse=reverse, **kwargs)
                    summary += '\n'
                    parts.append('---- (full traceback below) ----\n\n' if reverse else
                                 '---- (full traceback above) ----\n')
                    parts.append(summary)

        exc = format_exception_message(etype, evalue, style=style)
        parts.append('\n\n' if reverse else '')
        parts.append(exc)

        if reverse:
            parts = reversed(parts)

        msg += ''.join(parts)

    except Exception as exc:
        import os
        if 'PY_STACKPRINTER_DEBUG' in os.environ:
            raise

        our_tb = traceback.format_exception(exc.__class__,
                                            exc,
                                            exc.__traceback__,
                                            chain=False)
        where = getattr(exc, 'where', None)
        context = " while formatting " + str(where) if where else ''
        msg = 'Stackprinter failed%s:\n%s\n' % (context, ''.join(our_tb[-2:]))
        msg += 'So here is your original traceback at least:\n\n'
        msg += ''.join(traceback.format_exception(etype, evalue, tb))


    return msg


def format_exception_message(etype, evalue, tb=None, style='plaintext'):
    type_str = etype.__name__
    val_str = str(evalue)

    if etype == SyntaxError and evalue.text:
        val_str += '\n    %s\n   %s^' % (evalue.text.rstrip(), ' '*evalue.offset)

    if val_str:
        type_str += ": "

    if style == 'plaintext':
        return type_str + val_str
    else:
        sc = getattr(colorschemes, style)

        clr_head = get_ansi_tpl(*sc.colors['exception_type'])
        clr_msg = get_ansi_tpl(*sc.colors['exception_msg'])

        return clr_head % type_str + clr_msg % val_str


def _walk_traceback(tb):
    """
    Follow a chain of traceback objects outwards
    """
    while tb:
        yield tb
        tb = tb.tb_next
