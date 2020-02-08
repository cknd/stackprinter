from stack_data import FrameInfo, Options


def get_info(tb_or_frame):
    if isinstance(tb_or_frame, FrameInfo):
        return tb_or_frame

    return FrameInfo(tb_or_frame, Options(include_signature=True))
