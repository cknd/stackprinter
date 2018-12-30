import types
import traceback

import stackprinter.extraction as ex
from stackprinter.utils import match, get_ansi_tpl
from stackprinter.frame_formatting import FrameFormatter, ColorfulFrameFormatter


def format_stack(frames, style='plaintext', source_lines=5,
                 show_signature=True, show_vals='like_source',
                 truncate_vals=500, reverse=False, suppressed_paths=None):


    if style == 'plaintext':
        Formatter = FrameFormatter
    elif style in ['color', 'html']:
        Formatter = ColorfulFrameFormatter
    else:
        raise ValueError("Expected style 'plaintext' or 'color', got %r" % style)

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


def format_stack_from_frame(fr, **kwargs):
    stack = []
    while fr is not None:
        stack.append(ex.get_info(fr))
        fr = fr.f_back

    stack = reversed(stack)

    return format_stack(stack, **kwargs)


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
def format_exc_info(etype, evalue, tb, style='plaintext',
                    add_summary=True, reverse=False, **kwargs):

    frameinfos = [ex.get_info(fr) for fr in ex.walk_traceback(tb)]
    # TODO decouple frameinfo-getting from actual formatting, by packing
    # more of the below to respective methods (to facilitate formatting the
    # same stack multiple different ways)


    # TODO what is this for?
    if style in ['color', 'html']:
        fmt_style = 'color'
    else:
        fmt_style = 'plaintext'


    # TODO move summary generation to format_stack (so thread-formatting can also use it, and)
    # so multiple format passes over one set of frameinfos is easier


    stack_msg = format_stack(frameinfos, style=fmt_style, reverse=reverse, **kwargs)
    exc_msg = format_exception_message(etype, evalue, style=fmt_style)
    if add_summary:
        minimal_kwargs = kwargs.copy()
        minimal_kwargs['source_lines'] = 1
        minimal_kwargs['show_vals'] = False
        minimal_kwargs['show_signature'] = False
        summary_msg = format_stack(frameinfos, style=fmt_style, reverse=reverse, **minimal_kwargs)
    else:
        summary_msg = ''

    if reverse:
        # TODO do join over list instead
        msg = exc_msg + '\n\n' + summary_msg + '\n\n' + stack_msg
    else:
        msg = stack_msg + '\n' + summary_msg + '\n' + exc_msg

    if style == 'html':
        from ansi2html import Ansi2HTMLConverter
        conv = Ansi2HTMLConverter()
        msg = conv.convert(msg)

    return msg


def format_exception_message(etype, evalue, tb=None, style=None):
    type_str = etype.__name__
    val_str = str(evalue)
    if val_str:
        type_str += ": "

    if style is None:
        style = 'plaintext'

    if style == 'plaintext':
        return type_str + val_str
    elif style == 'color':
        bold = get_ansi_tpl(0, 1, 1, bold=True)
        normal = get_ansi_tpl(0, 1, 1, bold=True)
        return bold % type_str + normal % val_str
    else:
        raise ValueError("Expected style 'color' or 'plaintext'")


