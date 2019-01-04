"""
Various convnenience methods to walk stacks and concatenate formatted frames
"""
import types
import traceback

import stackprinter.extraction as ex
from stackprinter.utils import match, get_ansi_tpl
from stackprinter.frame_formatting import FrameFormatter, ColorfulFrameFormatter

def get_formatter_type(style):
    if style == 'plaintext':
        return FrameFormatter
    elif style ==  'color':
        return ColorfulFrameFormatter
    else:
        raise ValueError("Expected style 'plaintext' or 'color', got %r" % style)


def inspect_frames(frames):
    for fi in frames:
        if isinstance(fi, ex.FrameInfo):
            yield fi
        elif isinstance(fi, types.FrameType):
            yield ex.get_info(fi)
        else:
            raise ValueError("Expected a frame or a FrameInfo tuple, got %r" % fi)


def format_summary(frames, style='plaintext', source_lines=1, reverse=False,
                   **kwargs):
    """
    Render a list of frames with 1 line of source context, no variable values.

    keyword args like stackprinter.format()
    """
    Formatter = get_formatter_type(style)
    min_src_lines = 0 if source_lines == 0 else 1
    minimal_formatter = Formatter(source_lines=min_src_lines,
                                  show_signature=False,
                                  show_vals=False)

    frame_msgs = [minimal_formatter(fi) for fi in inspect_frames(frames)]
    if reverse:
        frame_msgs = reversed(frame_msgs)

    return ''.join(frame_msgs)


def format_stack(frames, style='plaintext', source_lines=5,
                 show_signature=True, show_vals='like_source',
                 truncate_vals=500, reverse=False, suppressed_paths=None):
    """
    Render a list of frames (or FrameInfo tuples)

    keyword args like stackprinter.format()
    """

    Formatter = get_formatter_type(style)

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
    for fi in inspect_frames(frames):
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


def format_stack_from_frame(fr, add_summary=False, **kwargs):
    """
    Render a frame and its parents


    keyword args like stackprinter.format()

    """
    stack = []
    while fr is not None:
        stack.append(ex.get_info(fr))
        fr = fr.f_back
    stack = reversed(stack)

    return format_stack(stack, **kwargs)


def format_exc_info(etype, evalue, tb, style='plaintext', add_summary=True,
                    reverse=False, **kwargs):
    """
    Format an exception traceback, including the exception message

    keyword args like stackprinter.format()
    """
    try:
        frameinfos = [ex.get_info(tb_) for tb_ in _walk_traceback(tb)]
        msgs = []
        stack = format_stack(frameinfos, style=style, reverse=reverse, **kwargs)
        msgs.append(stack)

        if add_summary:
            summ = format_summary(frameinfos, style=style, reverse=reverse, **kwargs)
            summ += '\n'
            msgs.append('------\n')
            msgs.append(summ)

        exc = format_exception_message(etype, evalue, style=style)
        msgs.append('\n\n' if reverse else '')
        msgs.append(exc)

        if reverse:
            msgs = reversed(msgs)

        msg = ''.join(msgs)

    except Exception as exc:
        raise
        our_tb = traceback.format_exception(exc.__class__,
                                            exc,
                                            exc.__traceback__,
                                            chain=False)

        msg = 'Stackprinter failed:\n%s' % ''.join(our_tb[-2:])
        msg += 'So here is the original traceback at least:\n\n'
        msg += ''.join(traceback.format_exception(etype, evalue, tb))

    return msg


def format_exception_message(etype, evalue, tb=None, style='plaintext'):
    type_str = etype.__name__
    val_str = str(evalue)

    if val_str:
        type_str += ": "

    if style == 'plaintext':
        return type_str + val_str
    elif style == 'color':
        bold = get_ansi_tpl(0, 1, 1, bold=True)
        normal = get_ansi_tpl(0, 1, 1, bold=True)
        return bold % type_str + normal % val_str
    else:
        raise ValueError("Expected style 'color' or 'plaintext', got %r" % style)


def _walk_traceback(tb):
    """
    Follow a chain of traceback objects outwards
    """
    while tb:
        yield tb
        tb = tb.tb_next
